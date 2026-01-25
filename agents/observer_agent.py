import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import asyncio

from .base_agent import BaseAgent
from backend.models.schemas import AgentType, MetricType, AlertSeverity, AlertCreate

class ObserverAgent(BaseAgent):
    def __init__(self, redis_client, db_session):
        super().__init__(AgentType.OBSERVER, redis_client)
        self.db_session = db_session
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.metric_history = {}
        self.thresholds = {
            MetricType.REVENUE: {"min": 1000, "max": 100000},
            MetricType.ORDERS: {"min": 10, "max": 1000},
            MetricType.CHURN_RISK: {"min": 0.0, "max": 0.3},
            MetricType.DELIVERY_DELAY: {"min": 0.0, "max": 5.0}
        }
    
    async def initialize(self):
        """Initialize the observer agent"""
        await self.update_status("initializing", "Loading historical data")
        await self._load_historical_data()
        await self._train_anomaly_detector()
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
            all_issues = anomalies + threshold_violations
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
        """Get current business metrics from the database"""
        # In a real system, this would query the database
        # For demo, we'll simulate with some realistic values
        
        # Get stored metrics or generate realistic ones
        stored_metrics = await self.get_data("current_metrics")
        if stored_metrics:
            # Add some variation to simulate real-time changes
            base_metrics = stored_metrics
        else:
            base_metrics = {
                "revenue": 15000.0,
                "orders": 150,
                "churn_risk": 0.15,
                "delivery_delay": 2.5,
                "customer_satisfaction": 4.2
            }
        
        # Add realistic variations
        current_time = datetime.utcnow()
        hour = current_time.hour
        
        # Simulate daily patterns
        daily_multiplier = 1.0 + 0.3 * np.sin(2 * np.pi * hour / 24)
        
        current_metrics = {
            "revenue": base_metrics["revenue"] * daily_multiplier * (1 + np.random.normal(0, 0.1)),
            "orders": int(base_metrics["orders"] * daily_multiplier * (1 + np.random.normal(0, 0.15))),
            "churn_risk": max(0, min(1, base_metrics["churn_risk"] * (1 + np.random.normal(0, 0.2)))),
            "delivery_delay": max(0, base_metrics["delivery_delay"] * (1 + np.random.normal(0, 0.3))),
            "customer_satisfaction": max(1, min(5, base_metrics["customer_satisfaction"] * (1 + np.random.normal(0, 0.05))))
        }
        
        # Store for next iteration
        await self.store_data("current_metrics", current_metrics, 300)
        
        return current_metrics
    
    async def _detect_anomalies(self, current_metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """Detect anomalies in current metrics using ML"""
        anomalies = []
        
        for metric_name, value in current_metrics.items():
            if metric_name in self.metric_history and len(self.metric_history[metric_name]) > 10:
                history = self.metric_history[metric_name]
                
                # Use statistical approach for anomaly detection
                mean_val = np.mean(history)
                std_val = np.std(history)
                z_score = abs((value - mean_val) / std_val) if std_val > 0 else 0
                
                if z_score > 2.5:  # 2.5 standard deviations
                    severity = AlertSeverity.HIGH if z_score > 3 else AlertSeverity.MEDIUM
                    
                    anomalies.append({
                        "metric_type": metric_name,
                        "current_value": value,
                        "expected_value": mean_val,
                        "z_score": z_score,
                        "severity": severity,
                        "description": f"{metric_name} anomaly detected: {value:.2f} (expected ~{mean_val:.2f})"
                    })
        
        return anomalies
    
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
        
        # Store in Redis for real-time access
        await self.redis_client.lpush("alerts", str(alert_data))
        await self.redis_client.ltrim("alerts", 0, 99)  # Keep last 100 alerts
        
        self.logger.warning(f"Alert created: {issue['description']}")
    
    async def _load_historical_data(self):
        """Load historical metric data for baseline establishment"""
        # Initialize with some historical data for demo
        for metric_type in ["revenue", "orders", "churn_risk", "delivery_delay", "customer_satisfaction"]:
            # Generate 30 days of historical data
            history = []
            base_value = {
                "revenue": 15000,
                "orders": 150,
                "churn_risk": 0.15,
                "delivery_delay": 2.5,
                "customer_satisfaction": 4.2
            }[metric_type]
            
            for i in range(30):
                # Add daily variation
                daily_var = 1.0 + 0.2 * np.sin(2 * np.pi * i / 7)  # Weekly pattern
                noise = np.random.normal(0, 0.1)
                value = base_value * daily_var * (1 + noise)
                history.append(max(0, value))
            
            self.metric_history[metric_type] = history
    
    async def _train_anomaly_detector(self):
        """Train the anomaly detection model on historical data"""
        if not self.metric_history:
            return
        
        # Prepare training data
        training_data = []
        for metric_values in self.metric_history.values():
            training_data.extend([[v] for v in metric_values])
        
        if len(training_data) > 10:
            training_array = np.array(training_data)
            self.scaler.fit(training_array)
            scaled_data = self.scaler.transform(training_array)
            self.anomaly_detector.fit(scaled_data)
            
            self.logger.info("Anomaly detector trained successfully")
    
    async def _update_metric_history(self, current_metrics: Dict[str, float]):
        """Update the rolling history of metrics"""
        for metric_name, value in current_metrics.items():
            if metric_name not in self.metric_history:
                self.metric_history[metric_name] = []
            
            self.metric_history[metric_name].append(value)
            
            # Keep only last 100 values
            if len(self.metric_history[metric_name]) > 100:
                self.metric_history[metric_name] = self.metric_history[metric_name][-100:]