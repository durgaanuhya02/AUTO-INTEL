"""Olist metric derivation and the shared anomaly detector."""
import numpy as np
import pytest

from backend.services.anomaly_detection import (MultivariateAnomalyDetector, seasonal_baseline,
                                                seasonal_ratio)
from backend.services.olist_metrics import (METRICS, WINDOW_END, WINDOW_START, customer_rfm,
                                            daily_metrics, dataset_statistics, rfm_summary)


def test_daily_metrics_cover_the_window_without_gaps():
    frame = daily_metrics()
    assert list(frame.columns) == METRICS
    assert frame.index[0] == WINDOW_START and frame.index[-1] == WINDOW_END
    assert not frame.isna().any().any()
    assert frame["customer_satisfaction"].between(1, 5).all()


def test_black_friday_is_the_peak_revenue_day():
    frame = daily_metrics()
    assert frame["revenue"].idxmax().date().isoformat() == "2017-11-24"


def test_dataset_statistics_match_the_published_olist_counts():
    stats = dataset_statistics()
    assert stats["orders"] == 99441
    assert stats["order_items"] == 112650
    assert stats["unique_customers"] == 96096
    assert stats["revenue_brl"] == pytest.approx(13591643.70, abs=0.01)


def test_rfm_segments_partition_customers_and_revenue():
    rfm = customer_rfm()
    summary = rfm_summary(rfm)
    assert summary["customers"].sum() == len(rfm)
    assert summary["revenue"].sum() == pytest.approx(rfm["monetary"].sum())
    assert (rfm["segment"] != "").all()
    # Only repeat buyers can be Champions.
    assert rfm.loc[rfm["segment"] == "Champions", "frequency"].min() >= 2


def test_seasonal_baseline_uses_only_earlier_same_weekday_values():
    values = np.arange(40, dtype=float).reshape(-1, 1)
    baseline = seasonal_baseline(values, period=7, cycles=4)
    assert np.isnan(baseline[:28]).all()
    assert baseline[28, 0] == np.median([21, 14, 7, 0])
    values[35:] = 1e6  # the future must not leak into earlier baselines
    assert seasonal_baseline(values, 7, 4)[34, 0] == baseline[34, 0]


def test_weekday_ratio_is_one_for_a_pure_weekly_pattern():
    pattern = np.tile([100, 110, 120, 130, 140, 60, 70], 10).astype(float).reshape(-1, 1)
    ratio = seasonal_ratio(pattern, 7, 4)
    assert np.allclose(ratio[28:], 1.0)


def _normal_window(n=60, seed=0):
    rng = np.random.default_rng(seed)
    return rng.normal([20000, 150, 4.0, 12.0], [2000, 15, 0.1, 1.0], size=(n, 4))


def test_forest_alone_misses_a_single_extreme_metric_but_hybrid_catches_it():
    history = _normal_window()
    current = history.mean(axis=0)
    current[3] = 60.0  # delivery delay ~48 sigma, everything else typical
    forest = MultivariateAnomalyDetector(METRICS).detect(history, current)
    hybrid = MultivariateAnomalyDetector(METRICS, z_threshold=3.0).detect(history, current)
    assert hybrid.is_anomaly and hybrid.metric == "delivery_delay" and hybrid.severity == "high"
    assert forest.metric == "delivery_delay"
    # Documented limitation: the forest score does not grow with the size of the deviation.
    current[3] = 600.0
    assert MultivariateAnomalyDetector(METRICS).detect(history, current).score == pytest.approx(
        forest.score)


def test_typical_day_is_not_flagged():
    history = _normal_window()
    detection = MultivariateAnomalyDetector(METRICS, z_threshold=3.0).detect(
        history, history.mean(axis=0))
    assert not detection.is_anomaly


def test_seasonal_detector_needs_lookback_and_reports_weekday_baseline():
    week = [100, 110, 120, 130, 140, 60, 70]  # Mon..Sun
    pattern = np.tile(week, 21).astype(float)[:145]  # ends on a Friday, so the next day is Saturday
    rng = np.random.default_rng(1)
    history = np.column_stack([pattern * (1 + rng.normal(0, 0.02, len(pattern)))] * 4)
    detector = MultivariateAnomalyDetector(METRICS, z_threshold=3.0, seasonal_period=7)
    assert detector.lookback == 28
    assert detector.detect(history[:30], history[30]) is None  # 2 usable rows after lookback

    # A normal Saturday (60) is fine; a weekday-sized value on a Saturday is not.
    normal = detector.detect(history, np.array([60.0] * 4))
    odd = detector.detect(history, np.array([130.0] * 4))
    assert not normal.is_anomaly
    assert odd.is_anomaly
    assert odd.expected["revenue"] == pytest.approx(60.0, rel=0.05)
