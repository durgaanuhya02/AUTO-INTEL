from typing import Dict, Any, List
from datetime import datetime

from .base_agent import BaseAgent
from backend.models.schemas import AgentType, AgentMessage, DecisionScenario


# metric -> (direction the metric should move, candidate interventions)
# Each intervention: (name, description, lift, cost, base_confidence, risk)
# `lift` is the fraction of the gap to the expected value that the action recovers.
SCENARIO_LIBRARY: Dict[str, List[tuple]] = {
    "revenue": [
        ("Promotional Campaign", "Targeted promotions to lift short-term revenue", 0.60, 4000.0, 0.75, 0.30),
        ("Price Optimization", "Adjust pricing on high-elasticity products", 0.80, 1500.0, 0.65, 0.55),
        ("Inventory Clearance", "Clear slow-moving stock with discounts", 0.45, 800.0, 0.80, 0.20),
    ],
    "orders": [
        ("Marketing Push", "Increase paid acquisition spend", 0.65, 3500.0, 0.70, 0.35),
        ("Checkout Optimization", "Reduce checkout friction", 0.50, 1200.0, 0.80, 0.15),
    ],
    "churn_risk": [
        ("Retention Offer", "Targeted loyalty offers for at-risk customers", 0.70, 2500.0, 0.75, 0.25),
        ("Customer Success Outreach", "Proactive support outreach", 0.50, 1800.0, 0.70, 0.20),
    ],
    "delivery_delay": [
        ("Logistics Optimization", "Re-route and rebalance carrier allocation", 0.75, 6000.0, 0.65, 0.50),
        ("Express Carrier Upgrade", "Shift priority orders to faster carrier", 0.55, 2500.0, 0.80, 0.20),
    ],
    "customer_satisfaction": [
        ("Support Staffing Increase", "Add customer service capacity", 0.60, 3000.0, 0.75, 0.25),
        ("Service Recovery Credits", "Proactive credits for affected customers", 0.40, 1000.0, 0.80, 0.15),
    ],
}

DEFAULT_SCENARIOS = [
    ("Manual Investigation", "Escalate to the operations team for manual review", 0.30, 500.0, 0.80, 0.10),
    ("Monitor and Wait", "Take no action and re-evaluate next cycle", 0.10, 0.0, 0.85, 0.05),
]


class SimulationAgent(BaseAgent):
    """What-if engine: turns a root-cause analysis into scored, comparable scenarios."""

    def __init__(self, redis_client, db_session=None):
        super().__init__(AgentType.SIMULATION, redis_client)
        self.db_session = db_session
        self.pending_analyses: List[Dict[str, Any]] = []

    async def initialize(self):
        await self.update_status("active", "Ready for scenario simulation")
        self.logger.info("Simulation agent initialized successfully")

    async def process(self):
        await self.update_status("processing", "Simulating scenarios")
        try:
            analyses, self.pending_analyses = self.pending_analyses, []
            for analysis in analyses:
                try:
                    scenarios = self.generate_scenarios(analysis)
                except (KeyError, TypeError, ValueError) as e:
                    self.logger.error(f"Skipping malformed analysis: {e!r}")
                    continue
                await self.send_message(
                    AgentType.DECISION,
                    "scenarios_ready",
                    {"analysis": analysis, "scenarios": [s.model_dump() for s in scenarios]},
                )
            await self.update_status("active", "Simulation complete", {
                "last_simulation": datetime.utcnow().isoformat(),
                "analyses_simulated": len(analyses),
            })
        except Exception as e:
            self.logger.error(f"Error in simulation processing: {e}")
            await self.update_status("error", f"Simulation error: {e}")

    async def handle_message(self, message: AgentMessage):
        await super().handle_message(message)
        if message.message_type == "analysis_complete":
            self.pending_analyses.append(message.content)

    def generate_scenarios(self, analysis: Dict[str, Any]) -> List[DecisionScenario]:
        anomaly = analysis["anomaly"]
        metric = str(anomaly["metric_type"])
        current = float(anomaly["current_value"])
        expected = float(anomaly.get("expected_value", current))
        gap = expected - current

        scenarios = []
        for name, desc, lift, cost, confidence, risk in SCENARIO_LIBRARY.get(metric, DEFAULT_SCENARIOS):
            outcome = current + gap * lift
            improved = abs(outcome - expected) < abs(current - expected)
            scenarios.append(DecisionScenario(
                name=name,
                description=desc,
                parameters={"estimated_cost": cost, "target_metric": metric, "lift": lift},
                predicted_outcome={
                    "expected_value": outcome,
                    "probability_of_improvement": min(0.95, confidence * (0.5 + lift / 2)) if improved else 0.1,
                },
                confidence_score=confidence,
                risk_score=risk,
            ))
        return scenarios
