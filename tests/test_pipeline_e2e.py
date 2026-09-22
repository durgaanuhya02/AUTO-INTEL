"""End-to-end tests for Observer -> Analyst -> Simulation -> Decision -> Governance.

Agents talk over real Redis pub/sub (fakeredis implements the same protocol), so these
tests exercise message serialization and delivery, not just method calls.
"""
import asyncio
import json

import pytest

from backend.models.schemas import AgentType
from tests.conftest import until, anomaly


async def run_stage(agent, pending_attr):
    """Wait for pub/sub delivery into the agent's inbox, then run one processing cycle."""
    await until(lambda: getattr(agent, pending_attr))
    await agent.process()


async def drive_pipeline(p, issue):
    await p["observer"].send_message(AgentType.ANALYST, "anomaly_detected", issue)
    await run_stage(p["analyst"], "pending_anomalies")
    await run_stage(p["simulation"], "pending_analyses")
    await run_stage(p["decision"], "pending_scenarios")
    await run_stage(p["governance"], "pending_decisions")


async def governance_log(redis):
    return [json.loads(e) for e in await redis.lrange("governance_log", 0, -1)]


async def test_critical_metric_anomaly_flows_to_human_approval(pipeline, redis, spy, business_hours):
    await drive_pipeline(pipeline, anomaly("revenue", current=6000.0, expected=15000.0))

    entries = await governance_log(redis)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["action"] == "request_human_approval"
    assert entry["final_status"] == "pending"
    assert entry["decision_id"] != "pending", "decisions must carry a real id for approvals to reference"
    assert 0.0 <= entry["confidence_score"] <= 1.0

    queue = [json.loads(e) for e in await redis.lrange("approval_queue", 0, -1)]
    assert len(queue) == 1
    assert queue[0]["decision"]["id"] == entry["decision_id"]
    assert any(v["rule"] == "critical_metrics" for v in queue[0]["policy_violations"])

    await until(lambda: "approval_requested" in spy.types())


async def test_low_risk_non_critical_anomaly_is_auto_approved_and_executed(pipeline, redis, spy, business_hours):
    await drive_pipeline(pipeline, anomaly("orders", current=60, expected=150))

    (entry,) = await governance_log(redis)
    assert entry["action"] == "auto_approve", entry["policy_result"]
    assert entry["final_status"] == "approved"
    assert await redis.llen("approval_queue") == 0

    await until(lambda: "decision_approved" in spy.types())
    execution = await redis.get(f"execution:{entry['decision_id']}")
    assert execution is not None, "auto-approved decisions must trigger an execution record"
    assert json.loads(execution)["status"] == "executing"


@pytest.mark.parametrize("name", ["Price Optimization", "Logistics Optimization", "price_optimization"])
async def test_restricted_scenarios_require_approval_regardless_of_name_formatting(pipeline, business_hours, name):
    """Scenario names are human-readable ('Price Optimization'); the policy keys use underscores."""
    decision = {
        "title": "t", "recommended_scenario": name, "financial_impact": 100.0,
        "confidence_score": 0.95, "requires_approval": False,
        "scenarios": [{"name": name, "risk_score": 0.1}],
    }
    result = await pipeline["governance"]._apply_policy_rules(decision, {"anomaly": anomaly("orders")})
    assert result["requires_approval"] is True
    assert any(v["rule"] == "restricted_scenarios" for v in result["violations"])

    from backend.models.schemas import DecisionScenario
    scenario = DecisionScenario(name=name, description="", parameters={}, predicted_outcome={},
                                confidence_score=0.95, risk_score=0.1)
    assert await pipeline["decision"]._requires_approval(scenario, 100.0) is True


async def test_after_hours_decisions_require_approval(pipeline, redis, after_hours):
    await drive_pipeline(pipeline, anomaly("orders", current=60, expected=150))

    (entry,) = await governance_log(redis)
    assert entry["action"] == "request_human_approval"
    assert any(v["rule"] == "business_hours_only" for v in entry["policy_result"]["violations"])


async def test_human_approval_response_is_broadcast(pipeline, redis, spy, business_hours):
    await drive_pipeline(pipeline, anomaly("revenue"))
    (entry,) = await governance_log(redis)

    await pipeline["observer"].send_message(
        AgentType.GOVERNANCE,
        "human_approval",
        {"decision_id": entry["decision_id"], "approved": True, "approver": "ops@example.com"},
    )
    await until(lambda: "decision_approved" in spy.types())
    approved = next(m for m in spy.messages if m["message_type"] == "decision_approved")
    assert approved["content"]["decision_id"] == entry["decision_id"]
    assert approved["content"]["human_approved"] is True


async def test_human_rejection_is_broadcast_and_dequeued(pipeline, redis, spy, business_hours):
    await drive_pipeline(pipeline, anomaly("revenue"))
    (entry,) = await governance_log(redis)

    await pipeline["observer"].send_message(
        AgentType.GOVERNANCE,
        "human_approval",
        {"decision_id": entry["decision_id"], "approved": False, "approver": "ops", "comments": "too risky"},
    )
    await until(lambda: "decision_rejected" in spy.types())
    rejected = next(m for m in spy.messages if m["message_type"] == "decision_rejected")
    assert rejected["content"]["reason"] == "too risky"
    assert await redis.llen("approval_queue") == 0
    assert await redis.get(f"execution:{entry['decision_id']}") is None


async def test_approval_for_unknown_decision_is_ignored(pipeline, redis, spy):
    await pipeline["observer"].send_message(
        AgentType.GOVERNANCE,
        "human_approval",
        {"decision_id": "never-queued", "approved": True, "approver": "ops"},
    )
    await asyncio.sleep(0.2)
    assert "decision_approved" not in spy.types()
    assert await redis.get("execution:never-queued") is None


async def test_second_approval_of_the_same_decision_does_nothing(pipeline, redis, spy, business_hours):
    await drive_pipeline(pipeline, anomaly("revenue"))
    (entry,) = await governance_log(redis)
    approval = {"decision_id": entry["decision_id"], "approved": True, "approver": "ops"}

    await pipeline["observer"].send_message(AgentType.GOVERNANCE, "human_approval", approval)
    await until(lambda: spy.types().count("decision_approved") == 1)
    await pipeline["observer"].send_message(AgentType.GOVERNANCE, "human_approval", approval)
    await asyncio.sleep(0.2)
    assert spy.types().count("decision_approved") == 1


async def test_every_stage_reports_status_to_redis(pipeline, redis, business_hours):
    await drive_pipeline(pipeline, anomaly("revenue"))
    for name in ("analyst", "simulation", "decision", "governance"):
        raw = await redis.get(f"agent_status:{name}")
        assert raw is not None, f"{name} never published status"
        assert json.loads(raw)["status"] == "active"


async def test_simulation_produces_comparable_scenarios(pipeline):
    scenarios = pipeline["simulation"].generate_scenarios({"anomaly": anomaly("revenue")})
    assert len(scenarios) >= 2
    for s in scenarios:
        assert 0.0 <= s.confidence_score <= 1.0
        assert 0.0 <= s.risk_score <= 1.0
        assert 0.0 <= s.predicted_outcome["probability_of_improvement"] <= 1.0
        # every scenario for a revenue drop should move revenue toward expected, not past it
        assert 6000.0 <= s.predicted_outcome["expected_value"] <= 15000.0


async def test_unknown_metric_falls_back_to_conservative_scenarios(pipeline):
    scenarios = pipeline["simulation"].generate_scenarios({"anomaly": anomaly("mystery_metric")})
    assert scenarios and all(s.risk_score <= 0.1 for s in scenarios)


async def test_financial_impact_is_the_improvement_not_the_absolute_level(pipeline):
    decision_agent = pipeline["decision"]
    scenarios = pipeline["simulation"].generate_scenarios({"anomaly": anomaly("revenue", 14000.0, 15000.0)})
    impact = await decision_agent._calculate_financial_impact(scenarios[0], anomaly("revenue", 14000.0, 15000.0))
    # a 1,000 revenue gap can never be worth ~15,000
    assert impact < 1000.0


async def _decide(pipeline, a):
    scenarios = pipeline["simulation"].generate_scenarios({"anomaly": a})
    return await pipeline["decision"]._make_decision(
        {"analysis": {"anomaly": a}, "scenarios": [s.model_dump() for s in scenarios]}
    )


async def test_decision_recommends_a_profitable_scenario_when_one_exists(pipeline):
    result = await _decide(pipeline, anomaly("revenue", 6000.0, 15000.0))
    details = result["evaluation_details"]
    assert details["meets_criteria"] is True
    assert details["net_impact"] > 0
    assert details["roi"] is None or details["roi"] >= 1.2


async def test_decision_never_auto_recommends_when_nothing_pays_off(pipeline):
    # a 100 gap: every intervention costs more than the revenue it recovers
    result = await _decide(pipeline, anomaly("revenue", 14900.0, 15000.0))
    assert result["evaluation_details"]["meets_criteria"] is False
    assert result["decision"]["requires_approval"] is True
    assert "No scenario met the decision criteria" in result["decision"]["reasoning"]


async def test_human_review_is_recorded_in_the_decision_log_and_pushed(pipeline, redis, business_hours):
    pubsub = redis.pubsub()
    await pubsub.subscribe("decisions")
    await drive_pipeline(pipeline, anomaly("revenue"))
    (entry,) = await governance_log(redis)

    await pipeline["observer"].send_message(
        AgentType.GOVERNANCE, "human_approval",
        {"decision_id": entry["decision_id"], "approved": True, "approver": "ops@example.com"},
    )
    await until(lambda: True)
    for _ in range(100):
        if await redis.llen("governance_log") == 2:
            break
        await asyncio.sleep(0.02)

    newest = json.loads((await redis.lrange("governance_log", 0, 0))[0])
    assert newest["decision_id"] == entry["decision_id"]
    assert newest["final_status"] == "approved"
    assert newest["action"] == "human_approved"
    assert newest["approver"] == "ops@example.com"
    await pubsub.aclose()


async def test_manual_trigger_measures_against_the_metric_baseline(pipeline):
    from agents.agent_orchestrator import AgentOrchestrator

    orch = AgentOrchestrator()
    orch.agents = {"analyst": pipeline["analyst"]}
    result = await orch.trigger_manual_analysis("revenue", 4200.0)
    assert result["anomaly"]["expected_value"] == 15000.0
    unknown = await orch.trigger_manual_analysis("mystery", 80.0)
    assert unknown["anomaly"]["expected_value"] == 100.0
