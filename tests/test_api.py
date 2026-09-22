"""REST API tests against the real FastAPI app (real lifespan, fakeredis for Redis)."""
import json
import time
from unittest.mock import AsyncMock

import pytest

from tests.conftest import anomaly


def unique_anomaly(value):
    """Tag test data with a distinctive value so assertions ignore unrelated background data."""
    return anomaly("revenue", current=value, expected=15000.0)


def find_approval(client, value):
    queue = client.get("/api/v1/approval-queue").json()["pending_approvals"]
    matches = [a for a in queue if a["analysis"]["anomaly"]["current_value"] == value]
    return matches[0] if matches else None


def test_root_reports_running(app_client):
    body = app_client.get("/").json()
    assert body["status"] == "running"


@pytest.mark.parametrize("status,http", [("healthy", 200), ("degraded", 200), ("unhealthy", 503), ("critical", 503)])
def test_health_status_code_reflects_component_health(app_client, monkeypatch, status, http):
    """ECS / ALB health checks (`curl -f`) look at the HTTP status, not the body."""
    import backend.main as main

    monkeypatch.setattr(
        main.health_checker, "run_comprehensive_health_check",
        AsyncMock(return_value={"overall_status": status, "components": {}}),
    )
    response = app_client.get("/health")
    assert response.status_code == http
    assert response.json()["status"] == status


def test_health_returns_503_if_the_check_itself_fails(app_client, monkeypatch):
    import backend.main as main

    monkeypatch.setattr(main.health_checker, "run_comprehensive_health_check",
                        AsyncMock(side_effect=RuntimeError("redis down")))
    response = app_client.get("/health")
    assert response.status_code == 503
    assert response.json()["status"] == "critical"


def test_agents_status_lists_the_five_pipeline_agents(app_client):
    body = app_client.get("/api/v1/agents/status").json()
    assert set(body["agents"]) == {"observer", "analyst", "simulation", "decision", "governance"}
    assert body["redis_connected"] is True


def test_observer_alert_is_visible_via_alerts_and_dashboard(app_client, live_pipeline):
    from agents.agent_orchestrator import orchestrator

    async def raise_alert():
        observer = orchestrator.agents["observer"]
        (violation,) = await observer._check_thresholds({"revenue": 512.0})
        await observer._create_alert(violation)

    app_client.portal.call(raise_alert)

    alerts = app_client.get("/api/v1/alerts").json()["alerts"]
    assert any(a["current_value"] == 512.0 and a["severity"] == "high" for a in alerts)

    # Dashboard requires the AlertResponse contract (id + created_at) and must not silently drop it.
    dashboard = app_client.get("/api/v1/dashboard").json()
    shown = [a for a in dashboard["alerts"] if a["current_value"] == 512.0]
    assert shown, "observer alert was dropped by the dashboard endpoint"
    assert isinstance(shown[0]["id"], int) and shown[0]["created_at"]


def test_dashboard_schema_and_agent_statuses(app_client, clean_state):
    response = app_client.get("/api/v1/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert {"current_metrics", "alerts", "recent_decisions", "agent_statuses", "trends"} <= set(body)
    assert len(body["agent_statuses"]) == 5


def test_decision_reaches_dashboard_with_a_stable_id(app_client, live_pipeline):
    live_pipeline(unique_anomaly(4301.0))

    def decisions():
        return app_client.get("/api/v1/dashboard").json()["recent_decisions"]

    first = decisions()
    assert first and first[0]["requires_approval"] is True
    time.sleep(0)  # cache is keyed by time; ids must not depend on process-salted hash()
    assert [d["id"] for d in decisions()] == [d["id"] for d in first]
    assert first[0]["id"] >= 0


def test_human_approval_end_to_end(app_client, live_pipeline, sync_redis):
    live_pipeline(unique_anomaly(4242.0))

    pending = find_approval(app_client, 4242.0)
    assert pending is not None, "revenue decisions must land in the approval queue"
    decision_id = pending["decision"]["id"]

    response = app_client.post("/api/v1/approve-decision", params={
        "decision_id": decision_id, "approved": True, "approver": "qa@example.com", "comments": "ok"})
    assert response.status_code == 200

    deadline = time.time() + 5
    while time.time() < deadline and find_approval(app_client, 4242.0):
        time.sleep(0.02)
    assert find_approval(app_client, 4242.0) is None, "approved decision must leave the queue"

    execution = sync_redis.get(f"execution:{decision_id}")
    assert execution is not None, "human-approved decisions must be executed"
    assert json.loads(execution)["status"] == "executing"


def test_human_rejection_removes_from_queue_without_executing(app_client, live_pipeline, sync_redis):
    live_pipeline(unique_anomaly(4243.0))
    decision_id = find_approval(app_client, 4243.0)["decision"]["id"]

    app_client.post("/api/v1/approve-decision", params={
        "decision_id": decision_id, "approved": False, "approver": "qa", "comments": "no"})

    deadline = time.time() + 5
    while time.time() < deadline and find_approval(app_client, 4243.0):
        time.sleep(0.02)
    assert find_approval(app_client, 4243.0) is None
    assert sync_redis.get(f"execution:{decision_id}") is None


def test_approving_an_unknown_decision_is_404(app_client, clean_state):
    response = app_client.post("/api/v1/approve-decision", params={
        "decision_id": "does-not-exist", "approved": True, "approver": "qa"})
    assert response.status_code == 404


def test_approving_twice_is_rejected(app_client, live_pipeline):
    live_pipeline(unique_anomaly(4244.0))
    decision_id = find_approval(app_client, 4244.0)["decision"]["id"]
    params = {"decision_id": decision_id, "approved": True, "approver": "qa"}

    assert app_client.post("/api/v1/approve-decision", params=params).status_code == 200
    deadline = time.time() + 5
    while time.time() < deadline and find_approval(app_client, 4244.0):
        time.sleep(0.02)
    assert app_client.post("/api/v1/approve-decision", params=params).status_code == 404


def test_missing_required_parameters_are_422(app_client, clean_state):
    assert app_client.post("/api/v1/approve-decision", params={"decision_id": "x"}).status_code == 422
    assert app_client.post("/api/v1/agents/trigger", params={"metric_type": "revenue"}).status_code == 422
    assert app_client.post("/api/v1/agents/trigger",
                           params={"metric_type": "revenue", "current_value": "abc"}).status_code == 422


def test_alerts_endpoint_skips_corrupt_entries(app_client, clean_state, sync_redis):
    sync_redis.lpush("alerts", "not json at all")
    sync_redis.lpush("alerts", json.dumps({"title": "ok", "current_value": 1.0, "severity": "low"}))
    alerts = app_client.get("/api/v1/alerts").json()["alerts"]
    assert len(alerts) == 1 and alerts[0]["title"] == "ok"


def test_alerts_endpoint_never_executes_stored_code(app_client, clean_state, sync_redis, tmp_path):
    """Regression: the endpoint used eval() on Redis contents."""
    marker = tmp_path / "pwned"
    sync_redis.lpush("alerts", f"__import__('pathlib').Path(r'{marker}').write_text('x') or {{}}")
    app_client.get("/api/v1/alerts")
    assert not marker.exists()


def test_rate_limit_returns_429_with_retry_after(app_client, clean_state):
    statuses = [
        app_client.post("/api/v1/agents/trigger", params={"metric_type": "orders", "current_value": 100}).status_code
        for _ in range(12)
    ]
    assert statuses[:10] == [200] * 10
    assert 429 in statuses[10:], "limit is 10/min for /agents/trigger"

    limited = app_client.post("/api/v1/agents/trigger", params={"metric_type": "orders", "current_value": 100})
    assert limited.status_code == 429
    assert limited.headers["retry-after"] == "60"
    assert limited.json()["detail"]["error"] == "Rate limit exceeded"


def test_rate_limit_headers_present_on_normal_responses(app_client, clean_state):
    response = app_client.get("/api/v1/alerts")
    assert response.headers["x-ratelimit-limit"] == "100"
    assert int(response.headers["x-ratelimit-remaining"]) <= 99
