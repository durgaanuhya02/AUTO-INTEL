#!/usr/bin/env python3
"""
Enhanced Simulation Agent - What-If Engine for Decision Intelligence
Generates multiple decision scenarios and scores expected outcomes
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import json
from enum import Enum

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ScenarioType(Enum):
    PRICING_ADJUSTMENT = "pricing_adjustment"
    INVENTORY_OPTIMIZATION = "inventory_optimization"
    MARKETING_CAMPAIGN = "marketing_campaign"
    OPERATIONAL_CHANGE = "operational_change"
    RESOURCE_ALLOCATION = "resource_allocation"

@dataclass
class SimulationScenario:
    """Simulation scenario definition"""
    scenario_id: str
    scenario_type: ScenarioType
    title: str
    description: str
    parameters: Dict[str, Any]
    expected_outcomes: Dict[str, float]
    confidence_score: float
    risk_level: str
    implementation_cost: float
    time_to_impact: int  # days
    success_probability: float

@dataclass
class SimulationResult:
    """Simulation result with scoring"""
    scenario: SimulationScenario
    projected_metrics: Dict[str, float]
    roi_estimate: float
    risk_assessment: Dict[str, Any]
    implementation_complexity: str
    overall_score: float
    ranking: int

class EnhancedSimulationAgent(BaseAgent):
    """What-if engine that generates and scores decision scenarios"""

    def __init__(self, ml_service=None, analytics_engine=None):
        super().__init__("enhanced_simulation_agent")
        self.simulation_queue = []
        self.scenario_templates = {}
        self.historical_outcomes = {}
        self.running = False
        self.ml_service = ml_service
        self.analytics_engine = analytics_engine

        # Initialize scenario templates
        self._initialize_scenario_templates()
        
    async def initialize(self):
        """Initialize the simulation agent"""
        await super().initialize()
        logger.info("🎯 Enhanced Simulation Agent initialized - Ready for what-if analysis...")
        
        # Subscribe to decision trigger events
        from backend.services.event_bus import event_bus
        await event_bus.subscribe_to_stream(
            'agents', 
            'simulation_group', 
            'enhanced_simulation_agent',
            self._handle_simulation_request
        )
        
        self.running = True
        
        # Start simulation processing loop
        asyncio.create_task(self._process_simulations())
    
    def _initialize_scenario_templates(self):
        """Initialize scenario templates for different business situations"""
        self.scenario_templates = {
            'revenue_decline': [
                {
                    'type': ScenarioType.PRICING_ADJUSTMENT,
                    'title': 'Price Reduction Strategy',
                    'description': 'Reduce prices by 5-15% to stimulate demand',
                    'parameters': {'price_reduction': [0.05, 0.10, 0.15]},
                    'base_success_probability': 0.7
                },
                {
                    'type': ScenarioType.MARKETING_CAMPAIGN,
                    'title': 'Aggressive Marketing Push',
                    'description': 'Increase marketing spend by 25-50%',
                    'parameters': {'marketing_increase': [0.25, 0.35, 0.50]},
                    'base_success_probability': 0.6
                },
                {
                    'type': ScenarioType.INVENTORY_OPTIMIZATION,
                    'title': 'Inventory Clearance',
                    'description': 'Clear slow-moving inventory with targeted promotions',
                    'parameters': {'discount_rate': [0.20, 0.30, 0.40]},
                    'base_success_probability': 0.8
                }
            ],
            'customer_satisfaction_low': [
                {
                    'type': ScenarioType.OPERATIONAL_CHANGE,
                    'title': 'Delivery Speed Improvement',
                    'description': 'Invest in faster delivery options',
                    'parameters': {'delivery_improvement': [0.20, 0.35, 0.50]},
                    'base_success_probability': 0.75
                },
                {
                    'type': ScenarioType.RESOURCE_ALLOCATION,
                    'title': 'Customer Service Enhancement',
                    'description': 'Increase customer service staff by 20-40%',
                    'parameters': {'staff_increase': [0.20, 0.30, 0.40]},
                    'base_success_probability': 0.65
                }
            ],
            'order_volume_drop': [
                {
                    'type': ScenarioType.MARKETING_CAMPAIGN,
                    'title': 'Customer Acquisition Campaign',
                    'description': 'Launch targeted customer acquisition campaign',
                    'parameters': {'campaign_budget': [10000, 25000, 50000]},
                    'base_success_probability': 0.6
                },
                {
                    'type': ScenarioType.PRICING_ADJUSTMENT,
                    'title': 'Competitive Pricing',
                    'description': 'Adjust pricing to match or beat competitors',
                    'parameters': {'price_adjustment': [-0.10, -0.05, 0.05]},
                    'base_success_probability': 0.7
                }
            ]
        }
    
    async def _handle_simulation_request(self, event):
        """Handle simulation requests from other agents"""
        try:
            if event.event_type == 'decision_trigger':
                analysis_report = event.data.get('analysis_report', {})
                
                simulation_request = {
                    'id': event.event_id,
                    'trigger_source': event.source,
                    'metric_name': analysis_report.get('metric_name'),
                    'analysis_report': analysis_report,
                    'priority': event.data.get('priority', 'medium'),
                    'timestamp': datetime.fromisoformat(event.timestamp)
                }
                
                # Add to simulation queue
                self.simulation_queue.append(simulation_request)
                
                # Sort by priority
                self.simulation_queue.sort(
                    key=lambda x: {'high': 0, 'medium': 1, 'low': 2}.get(x['priority'], 1)
                )
                
                await self.update_status("simulation_queued", 
                                       f"Queued simulation for {simulation_request['metric_name']}")
                
                logger.info(f"🎯 Simulation queued: {simulation_request['metric_name']} "
                           f"(priority: {simulation_request['priority']})")
        
        except Exception as e:
            logger.error(f"Error handling simulation request: {str(e)}")
    
    async def _process_simulations(self):
        """Process simulation queue"""
        while self.running:
            try:
                if self.simulation_queue:
                    simulation_request = self.simulation_queue.pop(0)
                    await self._run_simulation(simulation_request)
                else:
                    await asyncio.sleep(5)  # Wait for new simulations
                    
            except Exception as e:
                logger.error(f"Error processing simulations: {str(e)}")
                await asyncio.sleep(10)
    
    async def _run_simulation(self, simulation_request: Dict[str, Any]):
        """Run what-if simulation for the request"""
        try:
            await self.update_status("simulating", 
                                   f"Running scenarios for {simulation_request['metric_name']}")
            
            logger.info(f"🔬 Starting simulation: {simulation_request['metric_name']}")
            
            # Generate scenarios based on the problem type
            scenarios = await self._generate_scenarios(simulation_request)
            
            # Run simulations for each scenario
            simulation_results = []
            for scenario in scenarios:
                result = await self._simulate_scenario(scenario, simulation_request)
                simulation_results.append(result)
            
            # Rank scenarios by overall score
            simulation_results.sort(key=lambda x: x.overall_score, reverse=True)
            for i, result in enumerate(simulation_results):
                result.ranking = i + 1
            
            # Create simulation report
            simulation_report = {
                'simulation_id': simulation_request['id'],
                'metric_name': simulation_request['metric_name'],
                'trigger_source': simulation_request['trigger_source'],
                'timestamp': datetime.now().isoformat(),
                'scenarios_evaluated': len(simulation_results),
                'top_scenario': simulation_results[0].__dict__ if simulation_results else None,
                'all_scenarios': [result.__dict__ for result in simulation_results],
                'recommendation': await self._generate_simulation_recommendation(simulation_results),
                'confidence_level': self._calculate_simulation_confidence(simulation_results)
            }
            
            # Publish simulation results
            await self._publish_simulation_results(simulation_report)
            
            # Trigger decision agent with scenarios
            await self._trigger_decision_agent(simulation_report)
            
            await self.update_status("simulation_complete", 
                                   f"Completed simulation for {simulation_request['metric_name']}")
            
            logger.info(f"✅ Simulation completed: {simulation_request['metric_name']} "
                       f"({len(simulation_results)} scenarios evaluated)")
        
        except Exception as e:
            logger.error(f"Error running simulation: {str(e)}")
            await self.update_status("error", f"Simulation failed: {str(e)}")
    
    async def _generate_scenarios(self, simulation_request: Dict[str, Any]) -> List[SimulationScenario]:
        """Generate scenarios based on the problem type"""
        scenarios = []
        
        try:
            metric_name = simulation_request['metric_name']
            analysis_report = simulation_request['analysis_report']
            
            # Determine problem type from analysis
            problem_type = self._classify_problem(metric_name, analysis_report)
            
            # Get scenario templates for this problem type
            templates = self.scenario_templates.get(problem_type, [])
            
            scenario_id_counter = 1
            for template in templates:
                # Generate variations of each template
                for param_key, param_values in template['parameters'].items():
                    for param_value in param_values:
                        scenario = SimulationScenario(
                            scenario_id=f"{simulation_request['id']}_scenario_{scenario_id_counter}",
                            scenario_type=template['type'],
                            title=f"{template['title']} ({param_key}: {param_value})",
                            description=template['description'],
                            parameters={param_key: param_value},
                            expected_outcomes=self._calculate_expected_outcomes(
                                template['type'], {param_key: param_value}, metric_name
                            ),
                            confidence_score=template['base_success_probability'],
                            risk_level=self._assess_scenario_risk(template['type'], param_value),
                            implementation_cost=self._estimate_implementation_cost(
                                template['type'], {param_key: param_value}
                            ),
                            time_to_impact=self._estimate_time_to_impact(template['type']),
                            success_probability=template['base_success_probability']
                        )
                        
                        scenarios.append(scenario)
                        scenario_id_counter += 1
            
            logger.info(f"Generated {len(scenarios)} scenarios for {problem_type}")
            
        except Exception as e:
            logger.error(f"Error generating scenarios: {str(e)}")
        
        return scenarios
    
    def _classify_problem(self, metric_name: str, analysis_report: Dict[str, Any]) -> str:
        """Classify the problem type for scenario generation"""
        root_cause = analysis_report.get('root_cause_analysis', {})
        
        if metric_name == 'revenue':
            return 'revenue_decline'
        elif metric_name == 'customer_satisfaction':
            return 'customer_satisfaction_low'
        elif metric_name in ['orders', 'order_volume']:
            return 'order_volume_drop'
        else:
            return 'revenue_decline'  # Default fallback
    
    def _calculate_expected_outcomes(self, scenario_type: ScenarioType,
                                   parameters: Dict[str, Any],
                                   metric_name: str) -> Dict[str, float]:
        """Calculate expected outcomes for a scenario using ML predictions"""
        outcomes = {}

        try:
            # Use ML service if available
            if self.ml_service:
                return asyncio.run(self._calculate_ml_outcomes(scenario_type, parameters, metric_name))
            else:
                # Fallback to original hardcoded calculations
                return self._fallback_expected_outcomes(scenario_type, parameters, metric_name)

        except Exception as e:
            logger.error(f"Error calculating expected outcomes: {str(e)}")
            # Fallback to original hardcoded calculations
            return self._fallback_expected_outcomes(scenario_type, parameters, metric_name)

    async def _calculate_ml_outcomes(self, scenario_type: ScenarioType,
                                   parameters: Dict[str, Any],
                                   metric_name: str) -> Dict[str, float]:
        """Calculate outcomes using ML predictions"""
        outcomes = {}

        try:
            if scenario_type == ScenarioType.PRICING_ADJUSTMENT:
                # Use ML price optimization for realistic predictions
                price_change = parameters.get('price_reduction', parameters.get('price_adjustment', 0))

                # Get current market data (simplified)
                current_data = {
                    'current_price': 100.0,  # Base price
                    'competitor_price': 95.0,
                    'demand_index': 1.0,
                    'category_popularity': 0.8,
                    'seasonal_factor': 1.0,
                    'inventory_level': 0.7
                }

                # Adjust for scenario
                scenario_data = current_data.copy()
                scenario_data['current_price'] *= (1 - price_change)

                # Create DataFrame for ML prediction
                import pandas as pd
                product_df = pd.DataFrame([scenario_data])

                # Get ML prediction
                ml_result = await self.ml_service.predict_optimal_prices(product_df)

                if ml_result.prediction:
                    # Calculate revenue impact using ML-predicted optimal price
                    optimal_price = ml_result.prediction[0]
                    price_elasticity = -1.2  # From ML analysis

                    # Demand change based on price elasticity
                    demand_change = price_elasticity * price_change
                    revenue_change = (1 + price_change) * (1 + demand_change) - 1

                    outcomes['revenue_change'] = revenue_change
                    outcomes['order_volume_change'] = demand_change
                    outcomes['optimal_price'] = optimal_price
                else:
                    # Fallback
                    demand_change = -price_change * 1.2
                    revenue_change = (1 + price_change) * (1 + demand_change) - 1
                    outcomes['revenue_change'] = revenue_change
                    outcomes['order_volume_change'] = demand_change

            elif scenario_type == ScenarioType.MARKETING_CAMPAIGN:
                # Use ML demand forecasting for marketing impact
                marketing_increase = parameters.get('marketing_increase', 0)
                campaign_budget = parameters.get('campaign_budget', 0)

                if campaign_budget > 1000:
                    # Budget-based - use ML demand prediction
                    ml_result = await self.ml_service.predict_demand("top_category", days_ahead=30)

                    if ml_result.prediction:
                        # Estimate marketing ROI from ML insights
                        avg_daily_demand = sum(ml_result.prediction) / len(ml_result.prediction)
                        marketing_lift = min(marketing_increase * 0.8, 0.5)  # Cap at 50% lift
                        revenue_increase = (avg_daily_demand * 30 * marketing_lift * 100) / 100000  # Normalize
                    else:
                        revenue_increase = (campaign_budget * 3.5) / 100000  # Fallback ROI
                else:
                    # Percentage-based
                    revenue_increase = marketing_increase * 0.6

                outcomes['revenue_change'] = revenue_increase
                outcomes['customer_acquisition'] = marketing_increase * 0.8

            elif scenario_type == ScenarioType.OPERATIONAL_CHANGE:
                improvement = parameters.get('delivery_improvement', 0)

                # Use ML customer behavior prediction for satisfaction impact
                customer_features = pd.DataFrame([{
                    'days_since_last_order': 7,
                    'avg_order_value': 150,
                    'total_orders': 5,
                    'satisfaction_trend': 0.7,
                    'category_preference_score': 0.8
                }])

                ml_result = await self.ml_service.predict_customer_behavior(customer_features)

                if ml_result.prediction:
                    # Satisfaction improvement based on ML behavior prediction
                    churn_risk = ml_result.prediction[0]
                    satisfaction_improvement = improvement * (1 - churn_risk) * 0.4
                else:
                    satisfaction_improvement = improvement * 0.4

                outcomes['customer_satisfaction_change'] = satisfaction_improvement
                outcomes['retention_improvement'] = improvement * 0.3

            elif scenario_type == ScenarioType.RESOURCE_ALLOCATION:
                staff_increase = parameters.get('staff_increase', 0)

                # Similar to operational change but focused on service
                outcomes['customer_satisfaction_change'] = staff_increase * 0.5
                outcomes['operational_cost_increase'] = staff_increase * 0.8

            elif scenario_type == ScenarioType.INVENTORY_OPTIMIZATION:
                discount_rate = parameters.get('discount_rate', 0)

                # Use ML demand prediction for inventory impact
                ml_result = await self.ml_service.predict_demand("clearance_category", days_ahead=14)

                if ml_result.prediction:
                    # Inventory turnover based on predicted demand
                    avg_demand = sum(ml_result.prediction) / len(ml_result.prediction)
                    turnover_improvement = discount_rate * 2.0 * (avg_demand / 50)  # Normalized
                else:
                    turnover_improvement = discount_rate * 2.0

                outcomes['inventory_turnover'] = turnover_improvement
                outcomes['margin_impact'] = -discount_rate * 0.7

        except Exception as e:
            logger.error(f"Error in ML outcome calculation: {str(e)}")

        """Fallback hardcoded calculations when ML is unavailable"""
        outcomes = {}

        try:
            if scenario_type == ScenarioType.PRICING_ADJUSTMENT:
                price_change = parameters.get('price_reduction', parameters.get('price_adjustment', 0))

                # Price elasticity assumptions
                if metric_name == 'revenue':
                    # Assume price elasticity of demand = -1.2
                    demand_change = -price_change * 1.2
                    revenue_change = (1 + price_change) * (1 + demand_change) - 1
                    outcomes['revenue_change'] = revenue_change
                    outcomes['order_volume_change'] = demand_change

            elif scenario_type == ScenarioType.MARKETING_CAMPAIGN:
                marketing_increase = parameters.get('marketing_increase', parameters.get('campaign_budget', 0))

                if isinstance(marketing_increase, (int, float)) and marketing_increase > 1000:
                    # Budget-based calculation
                    roi_multiplier = 3.5  # Assume $3.5 return per $1 spent
                    revenue_increase = (marketing_increase * roi_multiplier) / 100000  # Normalize
                else:
                    # Percentage-based calculation
                    revenue_increase = marketing_increase * 0.6  # 60% efficiency

                outcomes['revenue_change'] = revenue_increase
                outcomes['customer_acquisition'] = marketing_increase * 0.8

            elif scenario_type == ScenarioType.OPERATIONAL_CHANGE:
                improvement = parameters.get('delivery_improvement', 0)
                outcomes['customer_satisfaction_change'] = improvement * 0.4
                outcomes['retention_improvement'] = improvement * 0.3

            elif scenario_type == ScenarioType.RESOURCE_ALLOCATION:
                staff_increase = parameters.get('staff_increase', 0)
                outcomes['customer_satisfaction_change'] = staff_increase * 0.5
                outcomes['operational_cost_increase'] = staff_increase * 0.8

            elif scenario_type == ScenarioType.INVENTORY_OPTIMIZATION:
                discount_rate = parameters.get('discount_rate', 0)
                outcomes['inventory_turnover'] = discount_rate * 2.0
                outcomes['margin_impact'] = -discount_rate * 0.7

        except Exception as e:
            logger.error(f"Error in fallback expected outcomes: {str(e)}")

        return outcomes
    
    def _assess_scenario_risk(self, scenario_type: ScenarioType, param_value: float) -> str:
        """Assess risk level of a scenario"""
        if scenario_type == ScenarioType.PRICING_ADJUSTMENT:
            if abs(param_value) > 0.15:
                return "high"
            elif abs(param_value) > 0.08:
                return "medium"
            else:
                return "low"
        
        elif scenario_type == ScenarioType.MARKETING_CAMPAIGN:
            if param_value > 0.4 or param_value > 40000:
                return "high"
            elif param_value > 0.25 or param_value > 20000:
                return "medium"
            else:
                return "low"
        
        else:
            return "medium"  # Default
    
    def _estimate_implementation_cost(self, scenario_type: ScenarioType, 
                                    parameters: Dict[str, Any]) -> float:
        """Estimate implementation cost"""
        if scenario_type == ScenarioType.PRICING_ADJUSTMENT:
            return 1000  # Low cost - just price changes
        
        elif scenario_type == ScenarioType.MARKETING_CAMPAIGN:
            budget = parameters.get('campaign_budget', 0)
            if budget > 1000:
                return budget
            else:
                marketing_increase = parameters.get('marketing_increase', 0)
                return marketing_increase * 50000  # Base marketing budget
        
        elif scenario_type == ScenarioType.OPERATIONAL_CHANGE:
            return 25000  # Medium cost for operational changes
        
        elif scenario_type == ScenarioType.RESOURCE_ALLOCATION:
            staff_increase = parameters.get('staff_increase', 0)
            return staff_increase * 60000  # Annual salary per additional staff
        
        elif scenario_type == ScenarioType.INVENTORY_OPTIMIZATION:
            return 5000  # Low cost for inventory management
        
        return 10000  # Default
    
    def _estimate_time_to_impact(self, scenario_type: ScenarioType) -> int:
        """Estimate time to see impact in days"""
        time_mapping = {
            ScenarioType.PRICING_ADJUSTMENT: 3,
            ScenarioType.MARKETING_CAMPAIGN: 14,
            ScenarioType.OPERATIONAL_CHANGE: 30,
            ScenarioType.RESOURCE_ALLOCATION: 21,
            ScenarioType.INVENTORY_OPTIMIZATION: 7
        }
        
        return time_mapping.get(scenario_type, 14)
    
    async def _simulate_scenario(self, scenario: SimulationScenario, 
                                simulation_request: Dict[str, Any]) -> SimulationResult:
        """Simulate a specific scenario and calculate results"""
        try:
            # Get current metrics as baseline
            current_metrics = await self._get_current_metrics()
            
            # Apply scenario effects
            projected_metrics = current_metrics.copy()
            
            for outcome_key, outcome_value in scenario.expected_outcomes.items():
                if outcome_key.endswith('_change'):
                    base_metric = outcome_key.replace('_change', '')
                    if base_metric in projected_metrics:
                        if outcome_value > -1:  # Avoid negative values
                            projected_metrics[base_metric] *= (1 + outcome_value)
                        else:
                            projected_metrics[base_metric] *= 0.1  # Minimum value
                
                elif outcome_key in projected_metrics:
                    projected_metrics[outcome_key] = outcome_value
            
            # Calculate ROI
            roi_estimate = self._calculate_roi(scenario, projected_metrics, current_metrics)
            
            # Risk assessment
            risk_assessment = {
                'risk_level': scenario.risk_level,
                'implementation_risk': self._assess_implementation_risk(scenario),
                'market_risk': self._assess_market_risk(scenario),
                'financial_risk': self._assess_financial_risk(scenario)
            }
            
            # Implementation complexity
            implementation_complexity = self._assess_implementation_complexity(scenario)
            
            # Overall score (weighted combination of factors)
            overall_score = self._calculate_overall_score(
                roi_estimate, scenario.success_probability, 
                risk_assessment, implementation_complexity
            )
            
            return SimulationResult(
                scenario=scenario,
                projected_metrics=projected_metrics,
                roi_estimate=roi_estimate,
                risk_assessment=risk_assessment,
                implementation_complexity=implementation_complexity,
                overall_score=overall_score,
                ranking=0  # Will be set later
            )
            
        except Exception as e:
            logger.error(f"Error simulating scenario: {str(e)}")
            # Return default result
            return SimulationResult(
                scenario=scenario,
                projected_metrics={},
                roi_estimate=0.0,
                risk_assessment={'risk_level': 'high'},
                implementation_complexity='high',
                overall_score=0.0,
                ranking=999
            )
    
    async def _get_current_metrics(self) -> Dict[str, float]:
        """Get current baseline metrics"""
        # In a real system, this would fetch from the data processor
        return {
            'revenue': 1000000.0,
            'orders': 1000,
            'customer_satisfaction': 4.2,
            'order_volume': 1000
        }
    
    def _calculate_roi(self, scenario: SimulationScenario, 
                      projected_metrics: Dict[str, float], 
                      current_metrics: Dict[str, float]) -> float:
        """Calculate ROI for the scenario"""
        try:
            # Calculate revenue impact
            current_revenue = current_metrics.get('revenue', 0)
            projected_revenue = projected_metrics.get('revenue', current_revenue)
            revenue_gain = projected_revenue - current_revenue
            
            # Calculate ROI
            if scenario.implementation_cost > 0:
                roi = (revenue_gain - scenario.implementation_cost) / scenario.implementation_cost
            else:
                roi = revenue_gain / 1000  # Avoid division by zero
            
            return roi
            
        except Exception as e:
            logger.error(f"Error calculating ROI: {str(e)}")
            return 0.0
    
    def _assess_implementation_risk(self, scenario: SimulationScenario) -> str:
        """Assess implementation risk"""
        if scenario.scenario_type == ScenarioType.PRICING_ADJUSTMENT:
            return "low"
        elif scenario.scenario_type == ScenarioType.MARKETING_CAMPAIGN:
            return "medium"
        else:
            return "high"
    
    def _assess_market_risk(self, scenario: SimulationScenario) -> str:
        """Assess market risk"""
        return "medium"  # Simplified assessment
    
    def _assess_financial_risk(self, scenario: SimulationScenario) -> str:
        """Assess financial risk"""
        if scenario.implementation_cost > 50000:
            return "high"
        elif scenario.implementation_cost > 20000:
            return "medium"
        else:
            return "low"
    
    def _assess_implementation_complexity(self, scenario: SimulationScenario) -> str:
        """Assess implementation complexity"""
        complexity_mapping = {
            ScenarioType.PRICING_ADJUSTMENT: "low",
            ScenarioType.MARKETING_CAMPAIGN: "medium",
            ScenarioType.OPERATIONAL_CHANGE: "high",
            ScenarioType.RESOURCE_ALLOCATION: "high",
            ScenarioType.INVENTORY_OPTIMIZATION: "medium"
        }
        
        return complexity_mapping.get(scenario.scenario_type, "medium")
    
    def _calculate_overall_score(self, roi: float, success_probability: float,
                               risk_assessment: Dict[str, Any], 
                               implementation_complexity: str) -> float:
        """Calculate overall scenario score"""
        try:
            # Normalize ROI (cap at 200% for scoring)
            roi_score = min(max(roi, -1.0), 2.0) / 2.0 + 0.5  # Scale to 0-1
            
            # Success probability is already 0-1
            success_score = success_probability
            
            # Risk penalty (lower is better)
            risk_levels = {'low': 0.9, 'medium': 0.7, 'high': 0.5}
            risk_score = risk_levels.get(risk_assessment.get('risk_level', 'medium'), 0.7)
            
            # Complexity penalty (lower is better)
            complexity_levels = {'low': 0.9, 'medium': 0.7, 'high': 0.5}
            complexity_score = complexity_levels.get(implementation_complexity, 0.7)
            
            # Weighted combination
            overall_score = (
                roi_score * 0.4 +           # 40% weight on ROI
                success_score * 0.3 +       # 30% weight on success probability
                risk_score * 0.2 +          # 20% weight on risk (inverted)
                complexity_score * 0.1      # 10% weight on complexity (inverted)
            )
            
            return max(0.0, min(1.0, overall_score))  # Ensure 0-1 range
            
        except Exception as e:
            logger.error(f"Error calculating overall score: {str(e)}")
            return 0.5  # Default middle score
    
    async def _generate_simulation_recommendation(self, simulation_results: List[SimulationResult]) -> str:
        """Generate recommendation based on simulation results"""
        if not simulation_results:
            return "No viable scenarios identified"
        
        top_scenario = simulation_results[0]
        
        if top_scenario.overall_score > 0.8:
            return f"Strongly recommend: {top_scenario.scenario.title} " \
                   f"(Score: {top_scenario.overall_score:.2f}, ROI: {top_scenario.roi_estimate:.1%})"
        elif top_scenario.overall_score > 0.6:
            return f"Recommend with caution: {top_scenario.scenario.title} " \
                   f"(Score: {top_scenario.overall_score:.2f}, Risk: {top_scenario.scenario.risk_level})"
        else:
            return f"Consider alternatives: Top scenario has moderate score " \
                   f"({top_scenario.overall_score:.2f}). May need more analysis."
    
    def _calculate_simulation_confidence(self, simulation_results: List[SimulationResult]) -> float:
        """Calculate overall confidence in simulation results"""
        if not simulation_results:
            return 0.0
        
        # Base confidence on top scenario score and spread of scores
        top_score = simulation_results[0].overall_score
        score_spread = max(result.overall_score for result in simulation_results) - \
                      min(result.overall_score for result in simulation_results)
        
        # Higher confidence if top score is high and there's clear differentiation
        confidence = top_score * (1 - score_spread * 0.5)
        
        return max(0.0, min(1.0, confidence))
    
    async def _publish_simulation_results(self, simulation_report: Dict[str, Any]):
        """Publish simulation results to event bus"""
        from backend.services.event_bus import event_bus, Event
        import uuid
        
        simulation_event = Event(
            event_id=str(uuid.uuid4()),
            event_type='simulation_completed',
            source='enhanced_simulation_agent',
            timestamp=datetime.now().isoformat(),
            data=simulation_report
        )
        
        await event_bus.publish_event('agents', simulation_event)
        
        logger.info(f"🎯 Published simulation results for {simulation_report['metric_name']}")
    
    async def _trigger_decision_agent(self, simulation_report: Dict[str, Any]):
        """Trigger decision agent with simulation results"""
        from backend.services.event_bus import event_bus, Event
        import uuid
        
        decision_event = Event(
            event_id=str(uuid.uuid4()),
            event_type='scenarios_ready',
            source='enhanced_simulation_agent',
            timestamp=datetime.now().isoformat(),
            data={
                'simulation_report': simulation_report,
                'top_scenarios': simulation_report['all_scenarios'][:3],  # Top 3 scenarios
                'recommendation': simulation_report['recommendation'],
                'confidence_level': simulation_report['confidence_level']
            }
        )
        
        await event_bus.publish_event('agents', decision_event)
        
        logger.info(f"🎯 Triggered decision agent with scenarios for {simulation_report['metric_name']}")
    
    def stop_simulation(self):
        """Stop the simulation processing"""
        self.running = False
        logger.info("🛑 Enhanced Simulation Agent stopping...")

# Global enhanced simulation agent instance
enhanced_simulation_agent = EnhancedSimulationAgent()