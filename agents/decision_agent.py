import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import json
import uuid

from .base_agent import BaseAgent
from backend.models.schemas import AgentType, AgentMessage, DecisionScenario, DecisionCreate

# Assumed value (R$, the currency of the Olist data) of one unit of improvement in each metric.
# These are tunable business assumptions, not measured values: replace with figures from finance
# before relying on them.
METRIC_UNIT_VALUE = {
    "revenue": 1.0,
    "orders": 40.0,               # average contribution margin per order
    "churn_risk": 200000.0,       # value of a full 1.0 reduction in churn probability
    "delivery_delay": 1500.0,     # per day of delay removed
    "customer_satisfaction": 8000.0,  # per rating point
}
DEFAULT_UNIT_VALUE = 100.0


class DecisionAgent(BaseAgent):
    def __init__(self, redis_client, db_session, openai_client):
        super().__init__(AgentType.DECISION, redis_client)
        self.db_session = db_session
        self.openai_client = openai_client
        self.pending_scenarios = []
        self.decision_criteria = {
            "min_confidence": 0.6,
            "max_risk": 0.7,
            "roi_threshold": 1.2
        }

    async def initialize(self):
        await self.update_status("initializing", "Loading decision models")
        await self._load_decision_criteria()
        await self.update_status("active", "Ready for decision making")
        self.logger.info("Decision agent initialized successfully")

    async def process(self):
        await self.update_status("processing", "Evaluating decisions")

        try:
            packages, self.pending_scenarios = self.pending_scenarios, []
            for scenario_package in packages:
                decision = await self._make_decision(scenario_package)
                if decision:
                    await self.send_message(
                        AgentType.GOVERNANCE,
                        "decision_ready",
                        decision
                    )

            await self.update_status("active", "Decision evaluation complete")

        except Exception as e:
            self.logger.error(f"Error in decision processing: {e}")
            await self.update_status("error", f"Decision error: {str(e)}")

    async def handle_message(self, message: AgentMessage):
        await super().handle_message(message)

        if message.message_type == "scenarios_ready":
            self.pending_scenarios.append(message.content)
            await self.update_status("processing", "Evaluating new scenarios")

    async def _make_decision(self, scenario_package: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            analysis = scenario_package["analysis"]
            scenarios = scenario_package["scenarios"]

            # Evaluate each scenario
            evaluated_scenarios = []
            for scenario_data in scenarios:
                scenario = DecisionScenario(**scenario_data)
                evaluation = await self._evaluate_scenario(scenario, analysis)
                evaluated_scenarios.append({
                    "scenario": scenario,
                    "evaluation": evaluation
                })

            # Select best scenario
            best_scenario = await self._select_best_scenario(evaluated_scenarios)

            if not best_scenario:
                return None

            # Generate decision reasoning
            reasoning = await self._generate_reasoning(best_scenario, evaluated_scenarios, analysis)

            # Calculate financial impact
            financial_impact = await self._calculate_financial_impact(best_scenario["scenario"], analysis["anomaly"])

            # Determine if approval is required
            meets_criteria = best_scenario["evaluation"]["meets_criteria"]
            requires_approval = (
                await self._requires_approval(best_scenario["scenario"], financial_impact)
                or not meets_criteria  # nothing viable: a human must decide
            )
            if not meets_criteria:
                reasoning += (
                    f" No scenario met the decision criteria (positive net value and ROI >= "
                    f"{self.decision_criteria['roi_threshold']}); this is the lowest-risk option, "
                    f"shown for human review."
                )

            decision = DecisionCreate(
                title=f"Decision for {analysis['anomaly']['metric_type']} anomaly",
                description=f"Recommended action based on {analysis['anomaly']['metric_type']} analysis",
                scenarios=[s["scenario"] for s in evaluated_scenarios],
                recommended_scenario=best_scenario["scenario"].name,
                confidence_score=best_scenario["evaluation"]["overall_score"],
                financial_impact=financial_impact,
                requires_approval=requires_approval,
                reasoning=reasoning
            )

            self.logger.info(f"Decision made: {decision.recommended_scenario} (confidence: {decision.confidence_score:.2f})")

            decision_payload = decision.model_dump()
            decision_payload["id"] = uuid.uuid4().hex

            return {
                "decision": decision_payload,
                "analysis": analysis,
                "evaluation_details": best_scenario["evaluation"]
            }

        except Exception as e:
            self.logger.error(f"Error making decision: {e}")
            return None

    async def _evaluate_scenario(self, scenario: DecisionScenario, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a scenario based on multiple criteria"""

        # Expected value score (0-1)
        expected_value = scenario.predicted_outcome.get("expected_value", 0)
        current_value = analysis["anomaly"]["current_value"]
        improvement_ratio = (expected_value - current_value) / current_value if current_value != 0 else 0
        value_score = min(1.0, max(0.0, improvement_ratio + 0.5))

        # Confidence score (already 0-1)
        confidence_score = scenario.confidence_score

        # Risk score (invert so lower risk = higher score)
        risk_score = 1.0 - scenario.risk_score

        # Probability of success
        prob_improvement = scenario.predicted_outcome.get("probability_of_improvement", 0.5)

        # Calculate weighted overall score
        weights = {
            "value": 0.3,
            "confidence": 0.25,
            "risk": 0.25,
            "probability": 0.2
        }

        overall_score = (
            weights["value"] * value_score +
            weights["confidence"] * confidence_score +
            weights["risk"] * risk_score +
            weights["probability"] * prob_improvement
        )

        # A scenario that loses money (or doesn't clear the ROI bar) is not viable, however well it scores.
        net_impact = await self._calculate_financial_impact(scenario, analysis["anomaly"])
        cost = float(scenario.parameters.get("estimated_cost", scenario.parameters.get("cost", 0.0)))
        roi = (net_impact + cost) / cost if cost > 0 else None  # None: free, so ROI is unbounded
        pays_off = net_impact > 0 and (roi is None or roi >= self.decision_criteria["roi_threshold"])

        return {
            "value_score": value_score,
            "confidence_score": confidence_score,
            "risk_score": risk_score,
            "probability_score": prob_improvement,
            "overall_score": overall_score,
            "net_impact": net_impact,
            "roi": roi,
            "meets_criteria": pays_off and self._meets_decision_criteria(scenario, overall_score)
        }

    def _meets_decision_criteria(self, scenario: DecisionScenario, overall_score: float) -> bool:
        """Check if scenario meets minimum decision criteria"""
        return (
            scenario.confidence_score >= self.decision_criteria["min_confidence"] and
            scenario.risk_score <= self.decision_criteria["max_risk"] and
            overall_score >= 0.5
        )

    async def _select_best_scenario(self, evaluated_scenarios: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Select the best scenario from evaluated options"""

        # Filter scenarios that meet criteria
        viable_scenarios = [s for s in evaluated_scenarios if s["evaluation"]["meets_criteria"]]

        if not viable_scenarios:
            # If no scenarios meet criteria, select the least risky option
            viable_scenarios = sorted(evaluated_scenarios, key=lambda s: s["scenario"].risk_score)[:1]

        if not viable_scenarios:
            return None

        # Sort by overall score
        best_scenario = max(viable_scenarios, key=lambda s: s["evaluation"]["overall_score"])

        return best_scenario

    async def _generate_reasoning(self, best_scenario: Dict[str, Any], all_scenarios: List[Dict[str, Any]], analysis: Dict[str, Any]) -> str:
        """Generate natural language reasoning for the decision"""

        scenario = best_scenario["scenario"]
        evaluation = best_scenario["evaluation"]
        anomaly = analysis["anomaly"]

        reasoning_parts = []

        # Context
        reasoning_parts.append(f"Based on the detected {anomaly['metric_type']} anomaly (current value: {anomaly['current_value']:.2f}), ")

        # Recommendation
        reasoning_parts.append(f"I recommend implementing '{scenario.name}'. ")

        # Justification
        reasoning_parts.append(f"This scenario has a confidence score of {scenario.confidence_score:.2f} and risk score of {scenario.risk_score:.2f}. ")

        # Expected outcome
        expected_value = scenario.predicted_outcome.get("expected_value", 0)
        prob_improvement = scenario.predicted_outcome.get("probability_of_improvement", 0)
        reasoning_parts.append(f"The expected outcome is {expected_value:.2f} with a {prob_improvement:.1%} probability of improvement. ")

        # Comparison with alternatives
        if len(all_scenarios) > 1:
            other_scores = [s["evaluation"]["overall_score"] for s in all_scenarios if s != best_scenario]
            if other_scores:
                avg_other_score = np.mean(other_scores)
                reasoning_parts.append(f"This option scores {evaluation['overall_score']:.2f} compared to an average of {avg_other_score:.2f} for other scenarios. ")

        # Risk assessment
        if scenario.risk_score < 0.3:
            reasoning_parts.append("The risk level is considered low. ")
        elif scenario.risk_score < 0.6:
            reasoning_parts.append("The risk level is moderate and manageable. ")
        else:
            reasoning_parts.append("While the risk is higher, the potential benefits justify the decision. ")

        return "".join(reasoning_parts)

    async def _calculate_financial_impact(self, scenario: DecisionScenario, anomaly: Dict[str, Any]) -> float:
        """Net impact (R$): value of the metric improvement the scenario delivers, minus its cost."""

        cost = float(scenario.parameters.get("estimated_cost", scenario.parameters.get("cost", 0.0)))

        current_value = float(anomaly["current_value"])
        predicted_value = float(scenario.predicted_outcome.get("expected_value", current_value))
        improvement = abs(predicted_value - current_value)

        unit_value = METRIC_UNIT_VALUE.get(str(anomaly["metric_type"]), DEFAULT_UNIT_VALUE)
        return improvement * unit_value - cost

    async def _requires_approval(self, scenario: DecisionScenario, financial_impact: float) -> bool:
        """Determine if the decision requires human approval"""

        # High financial impact requires approval
        if abs(financial_impact) > 10000:
            return True

        # Low confidence requires approval
        if scenario.confidence_score < 0.7:
            return True

        # High risk requires approval
        if scenario.risk_score > 0.6:
            return True

        # Certain scenario types always require approval
        high_impact_scenarios = ["price_optimization", "logistics_optimization"]
        normalized_name = scenario.name.lower().replace(" ", "_")
        if any(keyword in normalized_name for keyword in high_impact_scenarios):
            return True

        return False

    async def _load_decision_criteria(self):
        """Load decision-making criteria and thresholds"""
        # In production, this would load from configuration or database
        self.decision_criteria = {
            "min_confidence": 0.6,
            "max_risk": 0.7,
            "roi_threshold": 1.2,
            "max_auto_cost": 5000,
            "min_improvement_threshold": 0.05
        }

        self.logger.info("Decision criteria loaded")