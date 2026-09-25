"""Multivariate anomaly detection over a trailing window of business metrics.

The Observer agent and the evaluation scripts both use this class, so the detector that is measured
is the detector that runs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# The forest decides WHETHER a day is anomalous; severity is how far the attributed metric deviates.
# (IsolationForest scores saturate on small windows, so they make a poor severity scale.)
HIGH_SEVERITY_Z = 3.0


@dataclass
class Detection:
    is_anomaly: bool
    score: float                 # IsolationForest.decision_function: < 0 anomalous, lower = worse
    metric: Optional[str]        # metric that deviates most from the window (|z|), for routing
    z_scores: Dict[str, float]
    expected: Dict[str, float]   # window means, or same-weekday baselines when deseasonalised

    @property
    def severity(self) -> str:
        return "high" if abs(self.z_scores[self.metric]) > HIGH_SEVERITY_Z else "medium"


class MultivariateAnomalyDetector:
    """Fits StandardScaler + IsolationForest on the trailing window, then scores the current vector.

    Refitting per call keeps the model aligned with the recent regime (trend, seasonality) at the cost
    of one fit per cycle, which is cheap at window sizes of tens to a few hundred days.

    Isolation Forest scores saturate once a value leaves the range of the window: a single metric at
    5 sigma and at 100 sigma score the same, and with several metrics that one extreme dimension is
    often not enough to flag the day. With `z_threshold` set, a day is also anomalous when any single
    metric deviates from the window mean by more than that many standard deviations (hybrid mode).

    With `seasonal_period` set (7 for daily data), every value is first divided by the median of the
    same weekday over the previous `seasonal_cycles` weeks, so the detector sees deviations from the
    weekly pattern and recent level rather than the pattern itself. That needs
    `lookback = seasonal_period * seasonal_cycles` extra days of history.
    """

    def __init__(self, metrics: Sequence[str], contamination: float = 0.1,
                 n_estimators: int = 100, random_state: int = 42, min_history: int = 11,
                 z_threshold: Optional[float] = None, seasonal_period: Optional[int] = None,
                 seasonal_cycles: int = 4):
        self.metrics = list(metrics)
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.min_history = min_history
        self.z_threshold = z_threshold
        self.seasonal_period = seasonal_period
        self.seasonal_cycles = seasonal_cycles

    @property
    def lookback(self) -> int:
        return self.seasonal_period * self.seasonal_cycles if self.seasonal_period else 0

    def detect(self, history: np.ndarray, current: np.ndarray) -> Optional[Detection]:
        """history: (n, d) past vectors, oldest first; current: (d,). None if history is too short."""
        history = np.asarray(history, dtype=float)
        current = np.asarray(current, dtype=float)
        expected = None
        if self.seasonal_period:
            full = np.vstack([history, current])
            expected = seasonal_baseline(full, self.seasonal_period, self.seasonal_cycles)[-1]
            ratios = seasonal_ratio(full, self.seasonal_period, self.seasonal_cycles)
            history, current = ratios[:-1][self.lookback:], ratios[-1]
        if len(history) < self.min_history:
            return None

        mean, std = history.mean(axis=0), history.std(axis=0)
        z = np.divide(current - mean, std, out=np.zeros_like(mean), where=std > 0)

        scaler = StandardScaler().fit(history)
        model = IsolationForest(n_estimators=self.n_estimators, contamination=self.contamination,
                                random_state=self.random_state).fit(scaler.transform(history))
        score = float(model.decision_function(scaler.transform(current.reshape(1, -1)))[0])

        extreme = self.z_threshold is not None and float(np.max(np.abs(z))) > self.z_threshold
        return Detection(
            is_anomaly=score < 0 or extreme,
            score=score,
            metric=self.metrics[int(np.argmax(np.abs(z)))],
            z_scores={m: float(v) for m, v in zip(self.metrics, z)},
            expected={m: float(v) for m, v in zip(self.metrics, mean if expected is None else expected)},
        )


def seasonal_baseline(values: np.ndarray, period: int = 7, cycles: int = 4) -> np.ndarray:
    """Row t = median of rows t-period, t-2*period, ..., t-cycles*period (NaN for the first rows).

    Uses only earlier rows, so it is causal.
    """
    values = np.asarray(values, dtype=float)
    out = np.full_like(values, np.nan)
    lookback = period * cycles
    for t in range(lookback, len(values)):
        out[t] = np.median(values[t - lookback:t][::-1][period - 1::period], axis=0)
    return out


def seasonal_ratio(values: np.ndarray, period: int = 7, cycles: int = 4) -> np.ndarray:
    """values / seasonal_baseline(values): 1.0 means 'as usual for this weekday'."""
    baseline = seasonal_baseline(values, period, cycles)
    return np.divide(values, baseline, out=np.full_like(baseline, np.nan), where=baseline > 0)


def aligned_history(history: Dict[str, List[float]], metrics: Sequence[str],
                    window: int) -> np.ndarray:
    """Last `window` rows where every metric has a value, as an (n, len(metrics)) array."""
    n = min(len(history.get(m, [])) for m in metrics)
    n = min(n, window)
    if n == 0:
        return np.empty((0, len(metrics)))
    return np.column_stack([history[m][-n:] for m in metrics])
