import numpy as np
from typing import Dict, Any, List
from datetime import datetime
import json
import time

from .base_agent import BaseAgent
from backend.models.schemas import AgentType, MetricType, AlertSeverity
from backend.services.anomaly_detection import MultivariateAnomalyDetector, aligned_history
from backend.services.olist_metrics import METRICS, daily_metrics

# Trailing window (days) the detector is fitted on, and how many past values are kept per metric.
DETECTION_WINDOW = 60
HISTORY_LIMIT = 120
# Detector settings, selected on the 2017 validation split by evaluation/run_anomaly.py
# (best validation F1: weekday-adjusted hybrid, contamination 0.15, |z| > 3.5).
DETECTOR_CONFIG = {"contamination": 0.15, "z_threshold": 3.5, "seasonal_period": 7,
                   "seasonal_cycles": 4}
# The replay starts once the warm-up history covers the window plus the weekday baseline.
REPLAY_START = DETECTION_WINDOW + DETECTOR_CONFIG["seasonal_period"] * DETECTOR_CONFIG["seasonal_cycles"]


def baseline_metrics() -> Dict[str, float]:
    """Typical day in the Olist data (median of each daily metric)."""
    return daily_metrics().median().to_dict()


class ObserverAgent(BaseAgent):
    """Replays the Olist daily metrics one day per cycle and flags anomalous days.

    Detection is a hybrid multivariate Isolation Forest + per-metric z-score over the trailing
    DETECTION_WINDOW days of weekday-adjusted values; each anomaly is attributed to the metric that
    deviates most so it can be routed to metric-specific analysis and scenarios. Hard thresholds on
    the raw values are checked independently.
    """

    def __init__(self, redis_client, db_session):
        super().__init__(AgentType.OBSERVER, redis_client)
        self.db_session = db_session
        # A condition that persists must not raise a fresh alert (and a fresh decision) every cycle.
        self.alert_cooldown_seconds = 900
        self._last_alert_at: Dict[str, float] = {}
        self._now = time.monotonic
        self.detector = MultivariateAnomalyDetector(METRICS, random_state=42, **DETECTOR_CONFIG)
        self.metric_history: Dict[str, List[float]] = {}
        self._feed = daily_metrics()
        self._cursor = REPLAY_START
        self.thresholds = self._thresholds_from_data()

    def _thresholds_from_data(self) -> Dict[str, Dict[str, float]]:
        """Hard business limits, scaled from the median day rather than hand-picked constants."""
        median = self._feed.median()
        return {
            MetricType.REVENUE: {"min": 0.25 * median["revenue"], "max": 5 * median["revenue"]},
            MetricType.ORDERS: {"min": 0.25 * median["orders"], "max": 5 * median["orders"]},
            MetricType.CUSTOMER_SATISFACTION: {"min": 3.0, "max": 5.0},
            MetricType.DELIVERY_DELAY: {"min": 0.0, "max": 2 * median["delivery_delay"]},
            MetricType.CHURN_RISK: {"min": 0.0, "max": 0.3},
        }

    async def initialize(self):
        """Initialize the observer agent"""
        await self.update_status("initializing", "Loading historical data")
        await self._load_historical_data()
        await self.update_status("active", "Monitoring metrics")
        self.logger.info("Observer agent initialized successfully")

    async def process(self):
        """Main processing loop - monitor metrics and detect anomalies"""
        await self.update_status("processing", "Analyzing current metrics")

        try:
            # Get latest metrics
            current_metrics = await self._get_current_metrics()

            # Check for anomalies
            anomalies = await self._detect_anomalies(current_metrics)

            # Check threshold violations
            threshold_violations = await self._check_thresholds(current_metrics)

            # Generate alerts for anomalies and violations
            # Hard threshold violations first: when both detectors fire for one metric they describe
            # the same problem, and the violation is the more actionable one (it names the limit).
            all_issues = [i for i in threshold_violations + anomalies if self._should_alert(i)]
            for issue in all_issues:
                await self._create_alert(issue)
                await self.send_message(
                    AgentType.ANALYST,
                    "anomaly_detected",
                    issue
                )

            # Update metrics history
            await self._update_metric_history(current_metrics)

            # Send status update to other agents
            await self.send_message(
                None,  # Broadcast
                "metrics_update",
                {
                    "metrics": current_metrics,
                    "anomalies_count": len(anomalies),
                    "violations_count": len(threshold_violations),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            await self.update_status("active", "Monitoring metrics", {
                "last_check": datetime.utcnow().isoformat(),
                "anomalies_detected": len(anomalies),
                "threshold_violations": len(threshold_violations)
            })

        except Exception as e:
            self.logger.error(f"Error in observer processing: {e}")
            await self.update_status("error", f"Processing error: {str(e)}")

    async def _get_current_metrics(self) -> Dict[str, float]:
        """Next day of the Olist replay. Wraps to the first post-warm-up day at the end of the data."""
        if self._cursor >= len(self._feed):
            self._cursor = REPLAY_START
        day = self._feed.index[self._cursor]
        current_metrics = {m: float(v) for m, v in self._feed.iloc[self._cursor].items()}
        self._cursor += 1

        await self.store_data("current_metrics", {**current_metrics, "date": day.date().isoformat()}, 300)

        return current_metrics

    def _should_alert(self, issue: Dict[str, Any]) -> bool:
        """One alert per metric per cooldown window, however many detectors fire or cycles pass."""
        key = str(issue["metric_type"])
        now = self._now()
        last = self._last_alert_at.get(key)
        if last is not None and now - last < self.alert_cooldown_seconds:
            return False
        self._last_alert_at[key] = now
        return True

    def _judgeable_metrics(self, current_metrics: Dict[str, float]) -> List[str]:
        """Metrics with enough, non-constant history to be scored."""
        needed = self.detector.lookback + self.detector.min_history
        judgeable = []
        for name in current_metrics:
            history = self.metric_history.get(name, [])
            if len(history) >= needed and np.std(history[-DETECTION_WINDOW:]) > 0:
                judgeable.append(name)
        return judgeable

    async def _detect_anomalies(self, current_metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """Score today's metric vector against the trailing window (see ObserverAgent).

        Returns at most one anomaly per day, attributed to the metric with the largest |z|.
        """
        metrics = self._judgeable_metrics(current_metrics)
        if not metrics:
            return []

        detector = MultivariateAnomalyDetector(metrics, random_state=self.detector.random_state,
                                               **DETECTOR_CONFIG)
        history = aligned_history(self.metric_history, metrics, DETECTION_WINDOW + detector.lookback)
        detection = detector.detect(history, np.array([current_metrics[m] for m in metrics]))
        if detection is None or not detection.is_anomaly:
            return []

        metric = detection.metric
        value, expected = current_metrics[metric], detection.expected[metric]
        return [{
            "metric_type": metric,
            "current_value": value,
            "expected_value": expected,
            "z_score": abs(detection.z_scores[metric]),
            "anomaly_score": detection.score,
            "z_scores": detection.z_scores,
            "severity": AlertSeverity(detection.severity),
            "description": f"{metric} anomaly detected: {value:.2f} (expected ~{expected:.2f})"
        }]

    async def _check_thresholds(self, current_metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """Check if metrics violate predefined thresholds"""
        violations = []

        for metric_name, value in current_metrics.items():
            if metric_name in self.thresholds:
                threshold = self.thresholds[metric_name]

                if value < threshold["min"]:
                    violations.append({
                        "metric_type": metric_name,
                        "current_value": value,
                        "threshold_value": threshold["min"],
                        "violation_type": "below_minimum",
                        "severity": AlertSeverity.HIGH,
                        "description": f"{metric_name} below minimum threshold: {value:.2f} < {threshold['min']}"
                    })
                elif value > threshold["max"]:
                    violations.append({
                        "metric_type": metric_name,
                        "current_value": value,
                        "threshold_value": threshold["max"],
                        "violation_type": "above_maximum",
                        "severity": AlertSeverity.MEDIUM,
                        "description": f"{metric_name} above maximum threshold: {value:.2f} > {threshold['max']}"
                    })

        return violations

    async def _create_alert(self, issue: Dict[str, Any]):
        """Create an alert in the database"""
        # In a real system, this would create a database record
        alert_data = {
            "title": f"Metric Alert: {issue['metric_type']}",
            "description": issue["description"],
            "severity": issue["severity"],
            "metric_type": issue["metric_type"],
            "current_value": issue["current_value"],
            "threshold_value": issue.get("threshold_value"),
            "agent_type": self.agent_type,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Store in Redis for polling clients and publish for real-time (WebSocket) clients
        payload = json.dumps(alert_data, default=str)
        await self.redis_client.lpush("alerts", payload)
        await self.redis_client.ltrim("alerts", 0, 99)  # Keep last 100 alerts
        await self.redis_client.publish("alerts", payload)

        self.logger.warning(f"Alert created: {issue['description']}")

    async def _load_historical_data(self):
        """Seed the history with the Olist days that precede the replay start."""
        warmup = self._feed.iloc[:self._cursor]
        self.metric_history = {m: warmup[m].astype(float).tolist() for m in METRICS}

    async def _update_metric_history(self, current_metrics: Dict[str, float]):
        """Update the rolling history of metrics"""
        for metric_name, value in current_metrics.items():
            if metric_name not in self.metric_history:
                self.metric_history[metric_name] = []

            self.metric_history[metric_name].append(value)

            if len(self.metric_history[metric_name]) > HISTORY_LIMIT:
                self.metric_history[metric_name] = self.metric_history[metric_name][-HISTORY_LIMIT:]