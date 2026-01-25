#!/usr/bin/env python3
"""
Enhanced Decision Agent - Action Logic and Scenario Ranking
Converts insights into actionable decisions with confidence scoring
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import json
import uuid

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

@dataclass
class DecisionAction:
    """Decision action with execution details"""
    action_id: str
    action_type: str
    title: str
    description: str
    parameters: Dict[str, Any]
    expected_outcome: Dict[str, float]
    confidence_score: float
    risk_level: str
    implementation_cost: float
    time_to_execute: int  # hours
    success_probability: float

@dataclass
class DecisionResult:
    """Final decision result with ranking and reasoning"""
    decision_id: str
    selected_scenario: Dict[str, Any]
    alternative_scenarios: List[Dict[str, Any]]
    decision_reasoning: str
    confidence_level: float
    risk_assessment: Dict[str, Any]
    financial_impact: float
    requires_approval: bool
    execution_plan: List[Dict[str, Any]]
    monitoring_metrics: List[str]

class EnhancedDecisionAgent(BaseAgent):
    """Action logic agent that converts scenarios into executable decisions"""
    
    def __init__(self):
        super().__init__("enhanced_decision_agent")
        self.decision_queue = []
        self.decision_history = []
        self.decision_criteria = {}
        self.running = False
        
        # Decision thresholds
        self.min_confidence_threshold = 0.6
        self.max_risk_threshold = 0.7
        self.min_roi_threshold = 1.2
        
    async def initialize(self):
        """Initialize the decision agent"""
        await super().initialize()
        logger.info("⚖️ Enhanced Decision Agent initialized - Ready for decision making...")
        
        # Subscribe to scenario completion events
        from backend.services.event_bus import event_bus
        await event_bus.subscribe_to_stream(
            'agents', 
            'decision_group', 
            'enhanced_decision_agent',
            self._handle_scenarios_ready
        )
        
        self.running = True
        
        # Start decision processing loop
        asyncio.create_task(self._process_decision_queue())
        
        # Initialize decision criteria
        await self._initialize_decision_criteria()
    
    async def _handle_scenarios_ready(self, event):
        """Handle scenarios ready events from simulation agent"""
        try:
            if event.event_type == 'scenarios_ready':
                decision_request = {
                    'id': event.event_id,
                    'trigger_source': event.source,
                    'simulation_report': event.data.get('simulation_report', {}),
                    'top_scenarios': event.data.get('top_scenarios', []),
                    'recommendation': event.data.get('recommendation', ''),
                    'confidence_level': event.data.get('confidence_level', 0.5),
                    'priority': 'high' if 'Critical' in event.data.get('simulation_report', {}).get('analysis_report', {}).get('business_impact', '') else 'medium',
                    'timestamp': datetime.fromisoformat(event.timestamp)
                }
                
                # Add to decision queue
                self.decision_queue.append(decision_request)
                
                # Sort by priority
                self.decision_queue.sort(
                    key=lambda x: {'high': 0, 'medium': 1, 'low': 2}.get(x['priority'], 1)
                )
                
                await self.update_status("decision_queued", 
                                       f"Queued decision for {decision_request['simulation_report'].get('metric_name', 'unknown')}")
                
                logger.info(f"⚖️ Decision queued: {decision_request['simulation_report'].get('metric_name', 'unknown')} "
                           f"(priority: {decision_request['priority']})")
        
        except Exception as e:
            logger.error(f"Error handling scenarios ready: {str(e)}")
    
    async def _process_decision_queue(self):
        """Process decision queue with action logic"""
        while self.running:
            try:
                if self.decision_queue:
                    decision_request = self.decision_queue.pop(0)
                    await self._make_decision(decision_request)
                else:
                    await asyncio.sleep(5)  # Wait for new decisions
                    
            except Exception as e:
                logger.error(f"Error processing decision queue: {str(e)}")
                await asyncio.sleep(10)
    
    async def _make_decision(self, decision_request: Dict[str, Any]):
        """Make final decision with action logic"""
        try:
            await self.update_status("deciding", 
                                   f"Making decision for {decision_request['simulation_report'].get('metric_name', 'unknown')}")
            
            logger.info(f"🎯 Starting decision making: {decision_request['simulation_report'].get('metric_name', 'unknown')}")
            
            # Rank scenarios using advanced scoring
            ranked_scenarios = await self._rank_scenarios(decision_request['top_scenarios'])
            
            # Select best scenario with confidence assessment
            selected_scenario, selection_confidence = await self._select_best_scenario(
                ranked_scenarios, decision_request
            )
            
            # Generate decision reasoning
            decision_reasoning = await self._generate_decision_reasoning(
                selected_scenario, ranked_scenarios, decision_request
            )
            
            # Assess risks and requirements
            risk_assessment = await self._assess_decision_risks(selected_scenario, decision_request)
            
            # Calculate financial impact
            financial_impact = await self._calculate_financial_impact(selected_scenario)
            
            # Determine approval requirements
            requires_approval = await self._determine_approval_requirements(
                selected_scenario, risk_assessment, financial_impact
            )
            
            # Create execution plan
            execution_plan = await self._create_execution_plan(selected_scenario)
            
            # Define monitoring metrics
            monitoring_metrics = await self._define_monitoring_metrics(
                selected_scenario, decision_request['simulation_report']
            )
            
            # Create final decision result
            decision_result = DecisionResult(
                decision_id=str(uuid.uuid4()),
                selected_scenario=selected_scenario,
                alternative_scenarios=ranked_scenarios[1:4],  # Top 3 alternatives
                decision_reasoning=decision_reasoning,
                confidence_level=selection_confidence,
                risk_assessment=risk_assessment,
                financial_impact=financial_impact,
                requires_approval=requires_approval,
                execution_plan=execution_plan,
                monitoring_metrics=monitoring_metrics
            )
            
            # Store decision for audit trail
            decision_record = {
                'decision_result': decision_result.__dict__,
                'simulation_report': decision_request['simulation_report'],
                'timestamp': datetime.now().isoformat(),
                'agent_id': self.agent_id
            }
            
            self.decision_history.append(decision_record)
            if len(self.decision_history) > 50:
                self.decision_history = self.decision_history[-50:]
            
            # Publish decision results
            await self._publish_decision_results(decision_record)
            
            # Trigger governance agent for approval
            await self._trigger_governance_agent(decision_record)
            
            await self.update_status("decision_complete", 
                                   f"Decision made for {decision_request['simulation_report'].get('metric_name', 'unknown')}")
            
            logger.info(f"✅ Decision completed: {decision_request['simulation_report'].get('metric_name', 'unknown')} "
                       f"(confidence: {selection_confidence:.2f}, approval: {requires_approval})")
        
        except Exception as e:
            logger.error(f"Error making decision: {str(e)}")
            await self.update_status("error", f"Decision failed: {str(e)}")
    
    async def _rank_scenarios(self, scenarios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank scenarios using comprehensive scoring algorithm"""
        try:
            scored_scenarios = []
            
            for scenario in scenarios:
                # Extract scenario data
                scenario_data = scenario.get('scenario', {})
                projected_metrics = scenario.get('projected_metrics', {})
                roi_estimate = scenario.get('roi_estimate', 0)
                risk_assessment = scenario.get('risk_assessment', {})
                implementation_complexity = scenario.get('implementation_complexity', 'medium')
                
                # Calculate comprehensive score
                score_components = await self._calculate_scenario_score(
                    scenario_data, projected_metrics, roi_estimate, 
                    risk_assessment, implementation_complexity
                )
                
                # Add scoring details to scenario
                enhanced_scenario = scenario.copy()
                enhanced_scenario['score_components'] = score_components
                enhanced_scenario['total_score'] = score_components['total_score']
                enhanced_scenario['ranking_factors'] = await self._get_ranking_factors(scenario)
                
                scored_scenarios.append(enhanced_scenario)
            
            # Sort by total score (descending)
            ranked_scenarios = sorted(scored_scenarios, 
                                    key=lambda x: x['total_score'], reverse=True)
            
            # Add ranking positions
            for i, scenario in enumerate(ranked_scenarios):
                scenario['rank'] = i + 1
            
            logger.info(f"Ranked {len(ranked_scenarios)} scenarios")
            return ranked_scenarios
            
        except Exception as e:
            logger.error(f"Error ranking scenarios: {str(e)}")
            return scenarios  # Return original if ranking fails
    
    async def _calculate_scenario_score(self, scenario_data: Dict[str, Any],
                                      projected_metrics: Dict[str, float],
                                      roi_estimate: float,
                                      risk_assessment: Dict[str, Any],
                                      implementation_complexity: str) -> Dict[str, float]:
        """Calculate comprehensive scenario score"""
        try:
            # ROI Score (0-1, higher is better)
            roi_score = min(max(roi_estimate / 3.0, 0), 1)  # Normalize to 0-1, cap at 300% ROI
            
            # Success Probability Score (already 0-1)
            success_score = scenario_data.get('success_probability', 0.5)
            
            # Risk Score (0-1, lower risk is better)
            risk_level = risk_assessment.get('risk_level', 'medium')
            risk_scores = {'low': 0.9, 'medium': 0.6, 'high': 0.3}
            risk_score = risk_scores.get(risk_level, 0.6)
            
            # Implementation Score (0-1, lower complexity is better)
            complexity_scores = {'low': 0.9, 'medium': 0.6, 'high': 0.3}
            implementation_score = complexity_scores.get(implementation_complexity, 0.6)
            
            # Time to Impact Score (0-1, faster is better)
            time_to_impact = scenario_data.get('time_to_impact', 14)
            time_score = max(0, min(1, (30 - time_to_impact) / 30))  # 30 days max
            
            # Confidence Score (from scenario)
            confidence_score = scenario_data.get('confidence_score', 0.5)
            
            # Financial Impact Score (normalized)
            implementation_cost = scenario_data.get('implementation_cost', 0)
            cost_score = max(0, min(1, (100000 - implementation_cost) / 100000))  # $100k max
            
            # Weighted combination
            weights = {
                'roi': 0.25,
                'success': 0.20,
                'risk': 0.15,
                'implementation': 0.15,
                'time': 0.10,
                'confidence': 0.10,
                'cost': 0.05
            }
            
            total_score = (
                roi_score * weights['roi'] +
                success_score * weights['success'] +
                risk_score * weights['risk'] +
                implementation_score * weights['implementation'] +
                time_score * weights['time'] +
                confidence_score * weights['confidence'] +
                cost_score * weights['cost']
            )
            
            return {
                'roi_score': roi_score,
                'success_score': success_score,
                'risk_score': risk_score,
                'implementation_score': implementation_score,
                'time_score': time_score,
                'confidence_score': confidence_score,
                'cost_score': cost_score,
                'total_score': total_score
            }
            
        except Exception as e:
            logger.error(f"Error calculating scenario score: {str(e)}")
            return {'total_score': 0.5}  # Default middle score
    
    async def _select_best_scenario(self, ranked_scenarios: List[Dict[str, Any]], 
                                  decision_request: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
        """Select best scenario with confidence assessment"""
        try:
            if not ranked_scenarios:
                raise ValueError("No scenarios available for selection")
            
            # Get top scenario
            top_scenario = ranked_scenarios[0]
            
            # Calculate selection confidence based on multiple factors
            selection_confidence = await self._calculate_selection_confidence(
                top_scenario, ranked_scenarios, decision_request
            )
            
            # Apply decision criteria filters
            meets_criteria = await self._check_decision_criteria(top_scenario)
            
            if not meets_criteria:
                # Look for alternative that meets criteria
                for scenario in ranked_scenarios[1:]:
                    if await self._check_decision_criteria(scenario):
                        logger.info(f"Selected alternative scenario due to criteria requirements")
                        return scenario, selection_confidence * 0.8  # Reduce confidence
                
                # If no scenario meets criteria, proceed with top but flag for approval
                logger.warning(f"No scenario meets all criteria, proceeding with top scenario")
                top_scenario['criteria_override'] = True
            
            return top_scenario, selection_confidence
            
        except Exception as e:
            logger.error(f"Error selecting best scenario: {str(e)}")
            # Return first scenario with low confidence as fallback
            return ranked_scenarios[0] if ranked_scenarios else {}, 0.3
    
    async def _calculate_selection_confidence(self, top_scenario: Dict[str, Any],
                                            all_scenarios: List[Dict[str, Any]],
                                            decision_request: Dict[str, Any]) -> float:
        """Calculate confidence in scenario selection"""
        try:
            base_confidence = 0.5
            
            # Boost confidence based on scenario score
            scenario_score = top_scenario.get('total_score', 0.5)
            base_confidence += scenario_score * 0.3
            
            # Boost confidence based on score gap with alternatives
            if len(all_scenarios) > 1:
                score_gap = top_scenario.get('total_score', 0) - all_scenarios[1].get('total_score', 0)
                base_confidence += min(score_gap * 0.5, 0.2)  # Max 0.2 boost
            
            # Boost confidence based on simulation confidence
            simulation_confidence = decision_request.get('confidence_level', 0.5)
            base_confidence += simulation_confidence * 0.2
            
            # Reduce confidence for high-risk scenarios
            risk_level = top_scenario.get('risk_assessment', {}).get('risk_level', 'medium')
            if risk_level == 'high':
                base_confidence -= 0.15
            elif risk_level == 'low':
                base_confidence += 0.1
            
            return min(1.0, max(0.0, base_confidence))
            
        except Exception as e:
            logger.error(f"Error calculating selection confidence: {str(e)}")
            return 0.5
    
    async def _check_decision_criteria(self, scenario: Dict[str, Any]) -> bool:
        """Check if scenario meets decision criteria"""
        try:
            scenario_data = scenario.get('scenario', {})
            
            # Check confidence threshold
            if scenario_data.get('confidence_score', 0) < self.min_confidence_threshold:
                return False
            
            # Check risk threshold
            risk_level = scenario.get('risk_assessment', {}).get('risk_level', 'medium')
            risk_values = {'low': 0.2, 'medium': 0.5, 'high': 0.8}
            if risk_values.get(risk_level, 0.5) > self.max_risk_threshold:
                return False
            
            # Check ROI threshold
            roi_estimate = scenario.get('roi_estimate', 0)
            if roi_estimate < self.min_roi_threshold:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking decision criteria: {str(e)}")
            return False
    
    async def _generate_decision_reasoning(self, selected_scenario: Dict[str, Any],
                                         all_scenarios: List[Dict[str, Any]],
                                         decision_request: Dict[str, Any]) -> str:
        """Generate natural language reasoning for the decision"""
        try:
            scenario_data = selected_scenario.get('scenario', {})
            score_components = selected_scenario.get('score_components', {})
            
            reasoning_parts = []
            
            # Context
            metric_name = decision_request['simulation_report'].get('metric_name', 'metric')
            reasoning_parts.append(f"Based on analysis of {metric_name} anomaly, ")
            
            # Selection rationale
            reasoning_parts.append(f"I recommend '{scenario_data.get('title', 'selected scenario')}' ")
            reasoning_parts.append(f"with a confidence score of {score_components.get('total_score', 0):.2f}. ")
            
            # Key strengths
            strengths = []
            if score_components.get('roi_score', 0) > 0.7:
                strengths.append("strong ROI potential")
            if score_components.get('success_score', 0) > 0.7:
                strengths.append("high success probability")
            if score_components.get('risk_score', 0) > 0.7:
                strengths.append("low risk profile")
            
            if strengths:
                reasoning_parts.append(f"This scenario offers {', '.join(strengths)}. ")
            
            # Expected outcomes
            roi_estimate = selected_scenario.get('roi_estimate', 0)
            reasoning_parts.append(f"Expected ROI is {roi_estimate:.1%} ")
            
            implementation_cost = scenario_data.get('implementation_cost', 0)
            if implementation_cost > 0:
                reasoning_parts.append(f"with implementation cost of ${implementation_cost:,.0f}. ")
            
            # Risk assessment
            risk_level = selected_scenario.get('risk_assessment', {}).get('risk_level', 'medium')
            reasoning_parts.append(f"Risk level is assessed as {risk_level}. ")
            
            # Comparison with alternatives
            if len(all_scenarios) > 1:
                alt_score = all_scenarios[1].get('total_score', 0)
                score_diff = selected_scenario.get('total_score', 0) - alt_score
                if score_diff > 0.1:
                    reasoning_parts.append(f"This option significantly outperforms alternatives by {score_diff:.2f} points. ")
                else:
                    reasoning_parts.append(f"This option marginally outperforms alternatives. ")
            
            # Implementation timeline
            time_to_impact = scenario_data.get('time_to_impact', 14)
            reasoning_parts.append(f"Expected implementation time is {time_to_impact} days.")
            
            return "".join(reasoning_parts)
            
        except Exception as e:
            logger.error(f"Error generating decision reasoning: {str(e)}")
            return "Decision made based on available scenario analysis."
    
    async def _assess_decision_risks(self, selected_scenario: Dict[str, Any],
                                   decision_request: Dict[str, Any]) -> Dict[str, Any]:
        """Assess comprehensive risks for the decision"""
        try:
            scenario_data = selected_scenario.get('scenario', {})
            
            risk_assessment = {
                'overall_risk_level': selected_scenario.get('risk_assessment', {}).get('risk_level', 'medium'),
                'financial_risk': await self._assess_financial_risk(selected_scenario),
                'operational_risk': await self._assess_operational_risk(selected_scenario),
                'market_risk': await self._assess_market_risk(selected_scenario),
                'implementation_risk': await self._assess_implementation_risk(selected_scenario),
                'mitigation_strategies': await self._generate_risk_mitigation(selected_scenario)
            }
            
            return risk_assessment
            
        except Exception as e:
            logger.error(f"Error assessing decision risks: {str(e)}")
            return {'overall_risk_level': 'medium'}
    
    async def _assess_financial_risk(self, scenario: Dict[str, Any]) -> str:
        """Assess financial risk level"""
        implementation_cost = scenario.get('scenario', {}).get('implementation_cost', 0)
        roi_estimate = scenario.get('roi_estimate', 0)
        
        if implementation_cost > 50000 and roi_estimate < 1.5:
            return "high"
        elif implementation_cost > 20000 or roi_estimate < 1.2:
            return "medium"
        else:
            return "low"
    
    async def _assess_operational_risk(self, scenario: Dict[str, Any]) -> str:
        """Assess operational risk level"""
        complexity = scenario.get('implementation_complexity', 'medium')
        scenario_type = scenario.get('scenario', {}).get('scenario_type', '')
        
        if complexity == 'high' or 'operational' in str(scenario_type).lower():
            return "high"
        elif complexity == 'medium':
            return "medium"
        else:
            return "low"
    
    async def _assess_market_risk(self, scenario: Dict[str, Any]) -> str:
        """Assess market risk level"""
        scenario_type = scenario.get('scenario', {}).get('scenario_type', '')
        
        if 'pricing' in str(scenario_type).lower() or 'marketing' in str(scenario_type).lower():
            return "medium"
        else:
            return "low"
    
    async def _assess_implementation_risk(self, scenario: Dict[str, Any]) -> str:
        """Assess implementation risk level"""
        complexity = scenario.get('implementation_complexity', 'medium')
        time_to_impact = scenario.get('scenario', {}).get('time_to_impact', 14)
        
        if complexity == 'high' or time_to_impact > 30:
            return "high"
        elif complexity == 'medium' or time_to_impact > 14:
            return "medium"
        else:
            return "low"
    
    async def _generate_risk_mitigation(self, scenario: Dict[str, Any]) -> List[str]:
        """Generate risk mitigation strategies"""
        strategies = []
        
        # Financial risk mitigation
        if await self._assess_financial_risk(scenario) in ['medium', 'high']:
            strategies.append("Implement phased rollout to minimize financial exposure")
            strategies.append("Establish clear ROI monitoring and exit criteria")
        
        # Operational risk mitigation
        if await self._assess_operational_risk(scenario) in ['medium', 'high']:
            strategies.append("Conduct pilot testing before full implementation")
            strategies.append("Ensure adequate staff training and support")
        
        # Market risk mitigation
        if await self._assess_market_risk(scenario) in ['medium', 'high']:
            strategies.append("Monitor competitor responses and market conditions")
            strategies.append("Prepare contingency plans for market changes")
        
        return strategies[:5]  # Limit to 5 strategies
    
    async def _calculate_financial_impact(self, scenario: Dict[str, Any]) -> float:
        """Calculate total financial impact"""
        try:
            implementation_cost = scenario.get('scenario', {}).get('implementation_cost', 0)
            roi_estimate = scenario.get('roi_estimate', 0)
            
            # Estimate revenue impact based on ROI
            if roi_estimate > 0:
                revenue_impact = implementation_cost * roi_estimate
                net_impact = revenue_impact - implementation_cost
            else:
                net_impact = -implementation_cost
            
            return float(net_impact)
            
        except Exception as e:
            logger.error(f"Error calculating financial impact: {str(e)}")
            return 0.0
    
    async def _determine_approval_requirements(self, scenario: Dict[str, Any],
                                             risk_assessment: Dict[str, Any],
                                             financial_impact: float) -> bool:
        """Determine if decision requires approval"""
        try:
            # High financial impact requires approval
            if abs(financial_impact) > 25000:
                return True
            
            # High risk requires approval
            if risk_assessment.get('overall_risk_level') == 'high':
                return True
            
            # Low confidence requires approval
            if scenario.get('scenario', {}).get('confidence_score', 0) < 0.7:
                return True
            
            # Criteria override requires approval
            if scenario.get('criteria_override', False):
                return True
            
            # Complex implementations require approval
            if scenario.get('implementation_complexity') == 'high':
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error determining approval requirements: {str(e)}")
            return True  # Default to requiring approval on error
    
    async def _create_execution_plan(self, scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create detailed execution plan"""
        try:
            scenario_data = scenario.get('scenario', {})
            scenario_type = scenario_data.get('scenario_type', '')
            
            execution_steps = []
            
            # Common initial steps
            execution_steps.append({
                'step': 1,
                'phase': 'preparation',
                'task': 'Finalize implementation parameters',
                'duration_hours': 4,
                'responsible': 'implementation_team',
                'dependencies': []
            })
            
            execution_steps.append({
                'step': 2,
                'phase': 'preparation',
                'task': 'Conduct stakeholder briefing',
                'duration_hours': 2,
                'responsible': 'project_manager',
                'dependencies': [1]
            })
            
            # Scenario-specific steps
            if 'pricing' in str(scenario_type).lower():
                execution_steps.extend([
                    {
                        'step': 3,
                        'phase': 'implementation',
                        'task': 'Update pricing systems',
                        'duration_hours': 8,
                        'responsible': 'technical_team',
                        'dependencies': [2]
                    },
                    {
                        'step': 4,
                        'phase': 'implementation',
                        'task': 'Deploy pricing changes',
                        'duration_hours': 4,
                        'responsible': 'operations_team',
                        'dependencies': [3]
                    }
                ])
            elif 'marketing' in str(scenario_type).lower():
                execution_steps.extend([
                    {
                        'step': 3,
                        'phase': 'implementation',
                        'task': 'Develop marketing materials',
                        'duration_hours': 16,
                        'responsible': 'marketing_team',
                        'dependencies': [2]
                    },
                    {
                        'step': 4,
                        'phase': 'implementation',
                        'task': 'Launch marketing campaign',
                        'duration_hours': 8,
                        'responsible': 'marketing_team',
                        'dependencies': [3]
                    }
                ])
            else:
                # Generic implementation steps
                execution_steps.extend([
                    {
                        'step': 3,
                        'phase': 'implementation',
                        'task': 'Execute scenario implementation',
                        'duration_hours': 12,
                        'responsible': 'implementation_team',
                        'dependencies': [2]
                    }
                ])
            
            # Common final steps
            execution_steps.append({
                'step': len(execution_steps) + 1,
                'phase': 'monitoring',
                'task': 'Begin performance monitoring',
                'duration_hours': 2,
                'responsible': 'analytics_team',
                'dependencies': [len(execution_steps)]
            })
            
            return execution_steps
            
        except Exception as e:
            logger.error(f"Error creating execution plan: {str(e)}")
            return []
    
    async def _define_monitoring_metrics(self, scenario: Dict[str, Any],
                                       simulation_report: Dict[str, Any]) -> List[str]:
        """Define metrics to monitor post-implementation"""
        try:
            metrics = []
            
            # Always monitor the original anomaly metric
            original_metric = simulation_report.get('metric_name', '')
            if original_metric:
                metrics.append(original_metric)
            
            # Add scenario-specific metrics
            scenario_type = scenario.get('scenario', {}).get('scenario_type', '')
            
            if 'pricing' in str(scenario_type).lower():
                metrics.extend(['revenue', 'order_volume', 'avg_order_value'])
            elif 'marketing' in str(scenario_type).lower():
                metrics.extend(['customer_acquisition', 'conversion_rate', 'marketing_roi'])
            elif 'operational' in str(scenario_type).lower():
                metrics.extend(['operational_efficiency', 'customer_satisfaction', 'delivery_performance'])
            elif 'inventory' in str(scenario_type).lower():
                metrics.extend(['inventory_turnover', 'stockout_rate', 'carrying_cost'])
            
            # Add financial metrics
            metrics.extend(['roi', 'implementation_cost_actual'])
            
            # Remove duplicates while preserving order
            unique_metrics = []
            seen = set()
            for metric in metrics:
                if metric not in seen:
                    seen.add(metric)
                    unique_metrics.append(metric)
            
            return unique_metrics[:10]  # Limit to 10 metrics
            
        except Exception as e:
            logger.error(f"Error defining monitoring metrics: {str(e)}")
            return ['revenue', 'customer_satisfaction', 'roi']
    
    async def _get_ranking_factors(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Get factors that influenced scenario ranking"""
        try:
            return {
                'roi_estimate': scenario.get('roi_estimate', 0),
                'success_probability': scenario.get('scenario', {}).get('success_probability', 0),
                'risk_level': scenario.get('risk_assessment', {}).get('risk_level', 'medium'),
                'implementation_complexity': scenario.get('implementation_complexity', 'medium'),
                'time_to_impact': scenario.get('scenario', {}).get('time_to_impact', 14),
                'implementation_cost': scenario.get('scenario', {}).get('implementation_cost', 0)
            }
        except Exception as e:
            logger.error(f"Error getting ranking factors: {str(e)}")
            return {}
    
    async def _initialize_decision_criteria(self):
        """Initialize decision-making criteria"""
        self.decision_criteria = {
            'min_confidence_threshold': 0.6,
            'max_risk_threshold': 0.7,
            'min_roi_threshold': 1.2,
            'max_implementation_cost': 100000,
            'max_implementation_time': 30,  # days
            'required_success_probability': 0.5
        }
        
        logger.info("Decision criteria initialized")
    
    async def _publish_decision_results(self, decision_record: Dict[str, Any]):
        """Publish decision results to event bus"""
        from backend.services.event_bus import event_bus, Event
        
        decision_event = Event(
            event_id=str(uuid.uuid4()),
            event_type='decision_made',
            source='enhanced_decision_agent',
            timestamp=datetime.now().isoformat(),
            data=decision_record
        )
        
        await event_bus.publish_event('decisions', decision_event)
        
        logger.info(f"⚖️ Published decision results for {decision_record['simulation_report'].get('metric_name', 'unknown')}")
    
    async def _trigger_governance_agent(self, decision_record: Dict[str, Any]):
        """Trigger governance agent for approval process"""
        from backend.services.event_bus import event_bus, Event
        
        governance_event = Event(
            event_id=str(uuid.uuid4()),
            event_type='approval_required' if decision_record['decision_result']['requires_approval'] else 'auto_execute',
            source='enhanced_decision_agent',
            timestamp=datetime.now().isoformat(),
            data={
                'decision_record': decision_record,
                'priority': 'high' if 'Critical' in decision_record['simulation_report'].get('business_impact', '') else 'medium'
            }
        )
        
        await event_bus.publish_event('governance', governance_event)
        
        logger.info(f"⚖️ Triggered governance agent for {decision_record['simulation_report'].get('metric_name', 'unknown')}")
    
    def stop_decision_making(self):
        """Stop the decision making process"""
        self.running = False
        logger.info("🛑 Enhanced Decision Agent stopping...")

# Global enhanced decision agent instance
enhanced_decision_agent = EnhancedDecisionAgent()