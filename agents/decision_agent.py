import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import json

from .base_agent import BaseAgent
from backend.models.schemas import AgentType, AgentMessage, DecisionScenario, DecisionCreate

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
            if self.pending_scenarios:
                for scenario_package in self.pending_scenarios:
                    decision = await self._make_decision(scenario_package)
                    if decision:
                        await self.send_message(
                            AgentType.GOVERNANCE,
                            "decision_ready",
                            decision
                        )
                
                self.pending_scenarios.clear()
            
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
            financial_impact = await self._calculate_financial_impact(best_scenario["scenario"])
            
            # Determine if approval is required
            requires_approval = await self._requires_approval(best_scenario["scenario"], financial_impact)
            
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
            
            return {
                "decision": decision.model_dump(),
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
        
        return {
            "value_score": value_score,
            "confidence_score": confidence_score,
            "risk_score": risk_score,
            "probability_score": prob_improvement,
            "overall_score": overall_score,
            "meets_criteria": self._meets_decision_criteria(scenario, overall_score)
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
    
    async def _calculate_financial_impact(self, scenario: DecisionScenario) -> float:
        """Calculate estimated financial impact of the scenario"""
        
        # Extract cost from parameters
        cost = 0.0
        if "estimated_cost" in scenario.parameters:
            cost = scenario.parameters["estimated_cost"]
        elif "cost" in scenario.parameters:
            cost = scenario.parameters["cost"]
        
        # Calculate expected benefit
        expected_value = scenario.predicted_outcome.get("expected_value", 0)
        
        # For revenue scenarios, the expected value is the new revenue level
        # For cost scenarios (like delivery_delay), convert to revenue impact
        if "revenue" in scenario.name.lower() or "promotional" in scenario.name.lower():
            benefit = expected_value
        else:
            # Estimate revenue impact for non-revenue scenarios
            benefit = expected_value * 1000  # Rough conversion factor
        
        net_impact = benefit - cost
        
        return float(net_impact)
    
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
        if any(keyword in scenario.name.lower() for keyword in high_impact_scenarios):
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