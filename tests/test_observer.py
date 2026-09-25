"""Anomaly detection correctness for the Observer agent."""
import json

import numpy as np
import pytest

from agents.observer_agent import REPLAY_START
from backend.models.schemas import AgentType
from backend.services.olist_metrics import daily_metrics
from tests.conftest import until


def day(observer, **overrides):
    """A typical next day (median of the same weekday over the last 4 weeks), with overrides."""
    typical = {m: float(np.median(h[-28::7])) for m, h in observer.metric_history.items()}
    return {**typical, **overrides}


def seed_history(observer, metric, center, spread, n=60):
    rng = np.random.default_rng(0)
    observer.metric_history[metric] = list(center + rng.normal(0, spread, n))


async def test_normal_value_is_not_flagged(pipeline):
    observer = pipeline["observer"]
    seed_history(observer, "revenue", 15000, 300)
    assert await observer._detect_anomalies({"revenue": 15100.0}) == []


async def test_large_deviation_is_flagged_high_severity(pipeline):
    observer = pipeline["observer"]
    seed_history(observer, "revenue", 15000, 300)
    (found,) = await observer._detect_anomalies({"revenue": 25000.0})
    assert found["metric_type"] == "revenue"
    assert found["severity"] == "high"
    assert found["z_score"] > 3
    assert found["expected_value"] == pytest.approx(15000, rel=0.05)


async def test_moderate_deviation_is_never_high_severity(pipeline):
    """A ~2.7 sigma day may or may not be flagged (the validated detector needs |z| > 3.5 or a forest
    outlier), but it must never be escalated to HIGH."""
    observer = pipeline["observer"]
    seed_history(observer, "revenue", 15000, 300)
    mean, std = np.mean(observer.metric_history["revenue"]), np.std(observer.metric_history["revenue"])
    found = await observer._detect_anomalies({"revenue": mean + 2.7 * std})
    assert all(f["severity"] == "medium" for f in found)


async def test_flat_history_does_not_divide_by_zero(pipeline):
    observer = pipeline["observer"]
    observer.metric_history["orders"] = [150.0] * 30
    assert await observer._detect_anomalies({"orders": 900.0}) == []


async def test_too_little_history_is_not_judged(pipeline):
    observer = pipeline["observer"]
    observer.metric_history["orders"] = [150.0, 151.0, 149.0]
    assert await observer._detect_anomalies({"orders": 900.0}) == []


async def test_threshold_violations_below_min_and_above_max(pipeline):
    observer = pipeline["observer"]
    found = {v["metric_type"]: v for v in await observer._check_thresholds(
        {"revenue": 500.0, "churn_risk": 0.9, "orders": 150}
    )}
    assert found["revenue"]["violation_type"] == "below_minimum"
    assert found["churn_risk"]["violation_type"] == "above_maximum"
    assert "orders" not in found


async def test_process_alerts_and_notifies_analyst_over_pubsub(pipeline, redis, monkeypatch):
    observer, analyst = pipeline["observer"], pipeline["analyst"]

    async def metrics():
        return day(observer, revenue=500.0)

    monkeypatch.setattr(observer, "_get_current_metrics", metrics)
    await observer.process()

    await until(lambda: analyst.pending_anomalies)
    assert analyst.pending_anomalies[0]["metric_type"] == "revenue"
    assert analyst.pending_anomalies[0]["severity"] == "high"


async def test_alerts_are_stored_as_parseable_json(pipeline, redis):
    """The dashboard reads the `alerts` list; entries must be JSON, not Python reprs."""
    observer = pipeline["observer"]
    (violation,) = await observer._check_thresholds({"revenue": 500.0})
    await observer._create_alert(violation)

    (raw,) = await redis.lrange("alerts", 0, -1)
    alert = json.loads(raw)
    assert alert["severity"] == "high"
    assert alert["metric_type"] == "revenue"
    assert alert["agent_type"] == "observer"


async def test_alert_list_is_capped_at_100(pipeline, redis):
    observer = pipeline["observer"]
    (violation,) = await observer._check_thresholds({"revenue": 500.0})
    for _ in range(120):
        await observer._create_alert(violation)
    assert await redis.llen("alerts") == 100


async def test_metric_feed_replays_olist_days_in_order_and_wraps(pipeline):
    observer = pipeline["observer"]
    feed = daily_metrics()

    first = await observer._get_current_metrics()
    assert first == pytest.approx(feed.iloc[REPLAY_START].to_dict())
    second = await observer._get_current_metrics()
    assert second == pytest.approx(feed.iloc[REPLAY_START + 1].to_dict())

    for _ in range(len(feed)):  # run past the end of the data
        metrics = await observer._get_current_metrics()
        assert set(metrics) == set(feed.columns)
    assert observer._cursor <= len(feed)


async def test_warm_up_history_is_the_days_before_the_replay(pipeline):
    observer = pipeline["observer"]
    feed = daily_metrics()
    assert observer.metric_history["revenue"] == pytest.approx(
        feed["revenue"].iloc[:REPLAY_START].tolist())


async def test_multivariate_anomaly_is_attributed_to_the_deviating_metric(pipeline):
    observer = pipeline["observer"]
    typical = day(observer)
    (found,) = await observer._detect_anomalies({**typical, "delivery_delay": 40.0})
    assert found["metric_type"] == "delivery_delay"
    assert found["z_score"] > 3 and found["severity"] == "high"
    assert await observer._detect_anomalies(typical) == []


async def test_steady_state_metrics_do_not_cause_an_alert_storm(pipeline, redis, monkeypatch):
    observer = pipeline["observer"]
    for _ in range(50):
        await observer.process()
    assert await redis.llen("alerts") < 15, "healthy simulated metrics should rarely alert"


async def test_persistent_violation_alerts_once_per_cooldown(pipeline, redis, monkeypatch):
    observer = pipeline["observer"]
    clock = [1000.0]
    observer._now = lambda: clock[0]

    async def broken():
        return day(observer, revenue=500.0)

    monkeypatch.setattr(observer, "_get_current_metrics", broken)

    for _ in range(10):
        await observer.process()
        clock[0] += 30
    assert await redis.llen("alerts") == 1, "same condition must not re-alert every cycle"

    clock[0] += observer.alert_cooldown_seconds  # cooldown elapses; the condition is still true
    await observer.process()
    assert await redis.llen("alerts") == 2


async def test_different_conditions_are_not_suppressed_by_each_other(pipeline, redis, monkeypatch):
    observer = pipeline["observer"]

    async def broken():
        return day(observer, revenue=500.0, orders=5, churn_risk=0.9)

    monkeypatch.setattr(observer, "_get_current_metrics", broken)
    await observer.process()
    assert await redis.llen("alerts") == 3  # revenue low, orders low, churn high
