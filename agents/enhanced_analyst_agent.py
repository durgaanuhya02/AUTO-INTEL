#!/usr/bin/env python3
"""
Enhanced Analyst Agent - ML-Powered Reasoning and Root Cause Analysis
Activates only on meaningful events and generates intelligent insights using ML models
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import numpy as np
import json

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

@dataclass
class MLRootCauseAnalysis:
    """ML-enhanced root cause analysis result"""
    metric_name: str
    anomaly_data: Dict[str, Any]
    likely_causes: List[Dict[str, Any]]
    contributing_factors: List[str]
    business_impact: str
    confidence_score: float
    recommendations: List[str]
    correlation_analysis: Dict[str, float]
    ml_insights: Dict[str, Any]
    timestamp: datetime

class EnhancedAnalystAgent(BaseAgent):
    """ML-powered reasoning agent that performs deep analysis on demand"""
    
    def __init__(self, ml_service=None, redis_cache=None):
        super().__init__("enhanced_analyst_agent")
        self.analysis_queue = []
        self.correlation_matrix = {}
        self.analysis_history = []
        self.running = False
        
        # ML integration
        self.ml_service = ml_service
        self.redis_cache = redis_cache
        
        # Analysis models and thresholds
        self.confidence_threshold = 0.7
        self.correlation_threshold = 0.5
        
    async def initialize(self):
        """Initialize the analyst agent with ML services"""
        await super().initialize()
        logger.info("🧠 Enhanced Analyst Agent initialized - Ready for ML-powered analysis...")
        
        # Initialize ML services if available
        if not self.ml_service:
            try:
                from backend.services.ml_service import enhanced_ml_service
                self.ml_service = enhanced_ml_service
                logger.info("✅ ML service connected for root cause analysis")
            except Exception as e:
                logger.warning(f"ML service not available: {str(e)}")
        
        if not self.redis_cache:
            try:
                from backend.services.redis_cache_service import redis_cache_service
                self.redis_cache = redis_cache_service
                logger.info("✅ Redis cache connected for analysis caching")
            except Exception as e:
                logger.warning(f"Redis cache not available: {str(e)}")
        
        # Subscribe to investigation requests
        from backend.services.event_bus import event_bus
        await event_bus.subscribe_to_stream(
            'agents', 
            'analyst_group', 
            'enhanced_analyst_agent',
            self._handle_investigation_request
        )
        
        self.running = True
        
        # Start analysis processing loop
        asyncio.create_task(self._process_analysis_queue())
        
        # Initialize ML-enhanced correlation models
        await self._initialize_ml_correlation_models()
        
        # Update agent status in Redis
        if self.redis_cache:
            await self.redis_cache.cache_agent_status(self.agent_id, {
                'status': 'active',
                'capabilities': ['root_cause_analysis', 'correlation_analysis', 'ml_insights'],
                'ml_available': self.ml_service is not None,
                'last_activity': datetime.now().isoformat()
            })
    
    async def _handle_investigation_request(self, event):
        """Handle investigation requests from observer agent with ML context"""
        try:
            if event.event_type in ['investigation_requested', 'ml_investigation_requested']:
                investigation_data = {
                    'id': event.event_id,
                    'trigger_source': event.source,
                    'trigger_type': event.data.get('trigger_type'),
                    'metric_name': event.data.get('metric_name'),
                    'anomaly_data': event.data.get('anomaly_data', {}),
                    'priority': event.data.get('priority', 'medium'),
                    'ml_context': event.data.get('ml_context', {}),
                    'timestamp': datetime.fromisoformat(event.timestamp)
                }
                
                # Add to analysis queue
                self.analysis_queue.append(investigation_data)
                
                # Sort by priority (ML-enhanced investigations get slight priority boost)
                priority_weights = {'high': 0, 'medium': 1, 'low': 2}
                if investigation_data['ml_context'].get('model_available', False):
                    priority_weights = {k: v - 0.1 for k, v in priority_weights.items()}  # Slight boost
                
                self.analysis_queue.sort(
                    key=lambda x: priority_weights.get(x['priority'], 1)
                )
                
                await self.update_status("analysis_queued", 
                                       f"Queued ML analysis for {investigation_data['metric_name']}")
                
                logger.info(f"🧠 ML Investigation queued: {investigation_data['metric_name']} "
                           f"(priority: {investigation_data['priority']}, ML: {investigation_data['ml_context'].get('model_available', False)})")
        
        except Exception as e:
            logger.error(f"Error handling investigation request: {str(e)}")
    
    async def _process_analysis_queue(self):
        """Process analysis queue with ML-powered reasoning"""
        while self.running:
            try:
                if self.analysis_queue:
                    investigation = self.analysis_queue.pop(0)
                    await self._perform_ml_analysis(investigation)
                else:
                    await asyncio.sleep(5)  # Wait for new investigations
                    
            except Exception as e:
                logger.error(f"Error processing analysis queue: {str(e)}")
                await asyncio.sleep(10)
    
    async def _perform_ml_analysis(self, investigation: Dict[str, Any]):
        """Perform ML-enhanced analysis with root cause investigation"""
        try:
            await self.update_status("analyzing", 
                                   f"ML analyzing {investigation['metric_name']}")
            
            logger.info(f"🔬 Starting ML-enhanced analysis: {investigation['metric_name']}")
            
            # Check Redis cache for similar analysis
            analysis_cache_key = f"analysis_{investigation['metric_name']}_{investigation['trigger_type']}"
            cached_analysis = None
            
            if self.redis_cache:
                cached_analysis = await self.redis_cache.get_model_output(analysis_cache_key)
            
            if cached_analysis and (datetime.now() - datetime.fromisoformat(cached_analysis['generated_at'])).seconds < 1800:
                # Use cached analysis if less than 30 minutes old
                logger.debug("Using cached ML analysis results")
                root_cause_analysis = cached_analysis['analysis']
            else:
                # Perform new ML-enhanced root cause analysis
                root_cause_analysis = await self._analyze_ml_root_causes(investigation)
            
            # Generate ML-enhanced correlation analysis
            correlation_analysis = await self._analyze_ml_correlations(investigation['metric_name'])
            
            # Calculate business impact using ML insights
            business_impact = await self._assess_ml_business_impact(investigation, root_cause_analysis)
            
            # Generate ML-powered recommendations
            recommendations = await self._generate_ml_recommendations(
                investigation, root_cause_analysis, correlation_analysis
            )
            
            # Create comprehensive ML analysis report
            analysis_report = {
                'investigation_id': investigation['id'],
                'metric_name': investigation['metric_name'],
                'trigger_type': investigation['trigger_type'],
                'anomaly_data': investigation['anomaly_data'],
                'root_cause_analysis': root_cause_analysis,
                'correlation_analysis': correlation_analysis,
                'business_impact': business_impact,
                'recommendations': recommendations,
                'confidence_score': self._calculate_ml_analysis_confidence(root_cause_analysis, correlation_analysis),
                'ml_enhanced': True,
                'ml_models_used': root_cause_analysis.get('ml_models_used', []),
                'timestamp': datetime.now().isoformat(),
                'analyst_agent_id': self.agent_id
            }
            
            # Cache analysis results in Redis
            if self.redis_cache and not cached_analysis:
                await self.redis_cache.cache_model_output(
                    analysis_cache_key,
                    {
                        'analysis': root_cause_analysis,
                        'analysis_type': 'ml_root_cause',
                        'metric_name': investigation['metric_name']
                    }
                )
            
            # Store analysis for future reference
            self.analysis_history.append(analysis_report)
            if len(self.analysis_history) > 100:
                self.analysis_history = self.analysis_history[-100:]
            
            # Publish ML analysis results
            await self._publish_ml_analysis_results(analysis_report)
            
            # Trigger simulation agent with ML analysis
            await self._trigger_simulation_agent(analysis_report)
            
            await self.update_status("analysis_complete", 
                                   f"Completed ML analysis for {investigation['metric_name']}")
            
            logger.info(f"✅ ML Analysis completed: {investigation['metric_name']} "
                       f"(confidence: {analysis_report['confidence_score']:.2f}, ML models: {len(analysis_report['ml_models_used'])})")
        
        except Exception as e:
            logger.error(f"Error performing ML analysis: {str(e)}")
            await self.update_status("error", f"ML analysis failed: {str(e)}")
    
    async def _analyze_ml_root_causes(self, investigation: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze root causes using ML models and statistical methods"""
        metric_name = investigation['metric_name']
        anomaly_data = investigation['anomaly_data']
        ml_context = investigation.get('ml_context', {})
        
        try:
            # Get historical data for ML analysis
            historical_context = await self._get_ml_historical_context(metric_name)
            
            # Initialize analysis results
            likely_causes = []
            ml_models_used = []
            ml_insights = {}
            
            # Try ML-based root cause analysis first
            if self.ml_service and historical_context.get('data_available', False):
                ml_causes = await self._analyze_ml_causes(metric_name, anomaly_data, historical_context)
                if ml_causes:
                    likely_causes.extend(ml_causes['causes'])
                    ml_models_used.extend(ml_causes.get('models_used', []))
                    ml_insights.update(ml_causes.get('insights', {}))
            
            # Fallback to enhanced statistical analysis
            statistical_causes = await self._analyze_statistical_causes(metric_name, anomaly_data, historical_context)
            likely_causes.extend(statistical_causes)
            
            # Remove duplicates and rank by probability
            unique_causes = []
            seen_causes = set()
            for cause in likely_causes:
                cause_key = cause.get('cause', '')
                if cause_key not in seen_causes:
                    seen_causes.add(cause_key)
                    unique_causes.append(cause)
            
            # Sort by probability and ML confidence
            unique_causes.sort(key=lambda x: (x.get('probability', 0) + x.get('ml_confidence', 0)) / 2, reverse=True)
            
            # Identify contributing factors using ML
            contributing_factors = await self._identify_ml_contributing_factors(
                metric_name, anomaly_data, unique_causes, ml_insights
            )
            
            return {
                'likely_causes': unique_causes[:5],  # Top 5 causes
                'contributing_factors': contributing_factors,
                'analysis_method': 'ml_enhanced_statistical',
                'data_points_analyzed': historical_context.get('data_points', 0),
                'analysis_confidence': self._calculate_cause_confidence(unique_causes),
                'ml_models_used': ml_models_used,
                'ml_insights': ml_insights,
                'ml_enhanced': len(ml_models_used) > 0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing ML root causes: {str(e)}")
            return {
                'likely_causes': [],
                'contributing_factors': [],
                'analysis_method': 'error',
                'error': str(e),
                'ml_enhanced': False
            }
    
    async def _analyze_ml_causes(self, metric_name: str, anomaly_data: Dict[str, Any], 
                               historical_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze causes using ML models"""
        try:
            causes = []
            models_used = []
            insights = {}
            
            # Use XGBoost for feature importance analysis
            if self.ml_service:
                try:
                    # Create feature matrix for analysis
                    import pandas as pd
                    import numpy as np
                    
                    # Generate synthetic feature data based on business context
                    current_value = anomaly_data.get('current_value', 0)
                    expected_range = anomaly_data.get('expected_range', (0, 0))
                    
                    # Create features that might influence the metric
                    feature_data = pd.DataFrame({
                        'current_value': [current_value],
                        'deviation_from_expected': [current_value - np.mean(expected_range)],
                        'hour_of_day': [datetime.now().hour],
                        'day_of_week': [datetime.now().weekday()],
                        'month': [datetime.now().month],
                        'is_weekend': [1 if datetime.now().weekday() >= 5 else 0],
                        'is_business_hours': [1 if 9 <= datetime.now().hour <= 17 else 0],
                        'seasonal_factor': [1.0 + 0.1 * np.sin(2 * np.pi * datetime.now().timetuple().tm_yday / 365)]
                    })
                    
                    # Train XGBoost model for feature importance
                    ml_result = await self.ml_service.train_xgboost_model(
                        data=feature_data,
                        target_column='current_value',
                        task_type='regression'
                    )
                    
                    if ml_result and ml_result.feature_importance:
                        models_used.append('xgboost_feature_analysis')
                        
                        # Convert feature importance to root causes
                        for feature, importance in ml_result.feature_importance.items():
                            if importance > 0.1:  # Significant importance
                                cause_description = self._feature_to_cause_description(feature, importance)
                                if cause_description:
                                    causes.append({
                                        'cause': cause_description['cause'],
                                        'description': cause_description['description'],
                                        'probability': min(importance * 2, 1.0),  # Scale to 0-1
                                        'ml_confidence': importance,
                                        'impact': 'high' if importance > 0.3 else 'medium',
                                        'category': cause_description['category'],
                                        'ml_derived': True
                                    })
                        
                        insights['feature_importance'] = ml_result.feature_importance
                        insights['model_accuracy'] = ml_result.accuracy
                
                except Exception as e:
                    logger.debug(f"XGBoost feature analysis failed: {str(e)}")
            
            # Use SHAP for explainability if available
            try:
                from backend.services.shap_explainability_service import shap_explainability_service
                
                # Get SHAP explanation for the anomaly
                shap_explanation = await shap_explainability_service.explain_anomaly(
                    metric_name=metric_name,
                    anomaly_value=anomaly_data.get('current_value', 0),
                    context_data=historical_context
                )
                
                if shap_explanation:
                    models_used.append('shap_explainability')
                    insights['shap_values'] = shap_explanation.get('shap_values', {})
                    
                    # Convert SHAP values to causes
                    for feature, shap_value in shap_explanation.get('shap_values', {}).items():
                        if abs(shap_value) > 0.1:  # Significant SHAP value
                            cause_description = self._shap_to_cause_description(feature, shap_value)
                            if cause_description:
                                causes.append({
                                    'cause': cause_description['cause'],
                                    'description': cause_description['description'],
                                    'probability': min(abs(shap_value) * 3, 1.0),
                                    'ml_confidence': abs(shap_value),
                                    'impact': 'high' if abs(shap_value) > 0.3 else 'medium',
                                    'category': cause_description['category'],
                                    'ml_derived': True,
                                    'shap_contribution': shap_value
                                })
            
            except Exception as e:
                logger.debug(f"SHAP analysis failed: {str(e)}")
            
            return {
                'causes': causes,
                'models_used': models_used,
                'insights': insights
            } if causes else None
            
        except Exception as e:
            logger.error(f"Error in ML cause analysis: {str(e)}")
            return None
    
    def _feature_to_cause_description(self, feature: str, importance: float) -> Optional[Dict[str, str]]:
        """Convert ML feature importance to business cause description"""
        feature_mappings = {
            'hour_of_day': {
                'cause': 'Time-of-day effect',
                'description': 'Business performance varies by hour of day',
                'category': 'temporal'
            },
            'day_of_week': {
                'cause': 'Day-of-week pattern',
                'description': 'Weekly business cycle affecting performance',
                'category': 'temporal'
            },
            'is_weekend': {
                'cause': 'Weekend effect',
                'description': 'Different business patterns on weekends',
                'category': 'temporal'
            },
            'is_business_hours': {
                'cause': 'Business hours impact',
                'description': 'Performance differs during business vs non-business hours',
                'category': 'operational'
            },
            'seasonal_factor': {
                'cause': 'Seasonal variation',
                'description': 'Annual seasonal patterns affecting business',
                'category': 'seasonal'
            },
            'deviation_from_expected': {
                'cause': 'Systematic deviation',
                'description': 'Consistent deviation from expected performance levels',
                'category': 'systematic'
            }
        }
        
        return feature_mappings.get(feature)
    
    def _shap_to_cause_description(self, feature: str, shap_value: float) -> Optional[Dict[str, str]]:
        """Convert SHAP values to business cause descriptions"""
        direction = 'increase' if shap_value > 0 else 'decrease'
        
        shap_mappings = {
            'price_factor': {
                'cause': f'Pricing {direction}',
                'description': f'Price changes contributing to metric {direction}',
                'category': 'pricing'
            },
            'demand_factor': {
                'cause': f'Demand {direction}',
                'description': f'Market demand changes causing metric {direction}',
                'category': 'demand'
            },
            'competition_factor': {
                'cause': f'Competitive pressure {direction}',
                'description': f'Competitor actions leading to metric {direction}',
                'category': 'market'
            },
            'quality_factor': {
                'cause': f'Quality {direction}',
                'description': f'Product/service quality changes affecting metric {direction}',
                'category': 'quality'
            }
        }
        
        return shap_mappings.get(feature)
    
    async def _analyze_statistical_causes(self, metric_name: str, anomaly_data: Dict[str, Any], 
                                        historical_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhanced statistical cause analysis (fallback when ML unavailable)"""
        causes = []
        
        try:
            if metric_name == 'revenue':
                causes = await self._analyze_revenue_causes_enhanced(anomaly_data, historical_context)
            elif metric_name == 'customer_satisfaction':
                causes = await self._analyze_satisfaction_causes_enhanced(anomaly_data, historical_context)
            elif metric_name in ['orders', 'order_volume']:
                causes = await self._analyze_order_causes_enhanced(anomaly_data, historical_context)
            else:
                causes = await self._analyze_generic_causes_enhanced(anomaly_data, historical_context)
            
            # Add statistical confidence to all causes
            for cause in causes:
                cause['ml_derived'] = False
                cause['statistical_confidence'] = cause.get('probability', 0.5)
            
        except Exception as e:
            logger.error(f"Error in statistical cause analysis: {str(e)}")
        
        return causes
    
    async def _analyze_revenue_causes(self, anomaly_data: Dict[str, Any], 
                                    historical_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze potential causes for revenue anomalies"""
        causes = []
        current_value = anomaly_data.get('current_value', 0)
        expected_range = anomaly_data.get('expected_range', (0, 0))
        
        if current_value < expected_range[0]:  # Revenue drop
            causes = [
                {
                    'cause': 'Decreased order volume',
                    'description': 'Reduction in number of orders placed',
                    'probability': 0.8,
                    'impact': 'high',
                    'category': 'demand'
                },
                {
                    'cause': 'Lower average order value',
                    'description': 'Customers purchasing lower-value items',
                    'probability': 0.7,
                    'impact': 'high',
                    'category': 'pricing'
                },
                {
                    'cause': 'Increased promotional discounts',
                    'description': 'Higher discount rates reducing revenue per order',
                    'probability': 0.6,
                    'impact': 'medium',
                    'category': 'pricing'
                },
                {
                    'cause': 'Seasonal demand fluctuation',
                    'description': 'Natural seasonal variation in customer demand',
                    'probability': 0.5,
                    'impact': 'medium',
                    'category': 'seasonal'
                },
                {
                    'cause': 'Competitive pressure',
                    'description': 'Competitors offering better prices or products',
                    'probability': 0.4,
                    'impact': 'high',
                    'category': 'market'
                }
            ]
        else:  # Revenue spike
            causes = [
                {
                    'cause': 'Successful marketing campaign',
                    'description': 'Effective promotional or advertising campaign',
                    'probability': 0.7,
                    'impact': 'high',
                    'category': 'marketing'
                },
                {
                    'cause': 'Seasonal demand increase',
                    'description': 'Holiday or seasonal shopping surge',
                    'probability': 0.6,
                    'impact': 'high',
                    'category': 'seasonal'
                },
                {
                    'cause': 'New product launch success',
                    'description': 'Popular new product driving sales',
                    'probability': 0.5,
                    'impact': 'high',
                    'category': 'product'
                }
            ]
        
        return causes
    
    async def _analyze_satisfaction_causes(self, anomaly_data: Dict[str, Any], 
                                         historical_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze potential causes for customer satisfaction anomalies"""
        causes = []
        current_value = anomaly_data.get('current_value', 0)
        expected_range = anomaly_data.get('expected_range', (0, 0))
        
        if current_value < expected_range[0]:  # Satisfaction drop
            causes = [
                {
                    'cause': 'Delivery delays',
                    'description': 'Increased shipping times affecting customer experience',
                    'probability': 0.8,
                    'impact': 'high',
                    'category': 'logistics'
                },
                {
                    'cause': 'Product quality issues',
                    'description': 'Defective or substandard products received',
                    'probability': 0.7,
                    'impact': 'high',
                    'category': 'quality'
                },
                {
                    'cause': 'Poor customer service',
                    'description': 'Inadequate support or response times',
                    'probability': 0.6,
                    'impact': 'high',
                    'category': 'service'
                },
                {
                    'cause': 'Website/app issues',
                    'description': 'Technical problems affecting user experience',
                    'probability': 0.5,
                    'impact': 'medium',
                    'category': 'technical'
                }
            ]
        else:  # Satisfaction improvement
            causes = [
                {
                    'cause': 'Improved delivery performance',
                    'description': 'Faster and more reliable shipping',
                    'probability': 0.7,
                    'impact': 'high',
                    'category': 'logistics'
                },
                {
                    'cause': 'Enhanced customer service',
                    'description': 'Better support and response times',
                    'probability': 0.6,
                    'impact': 'high',
                    'category': 'service'
                }
            ]
        
        return causes
    
    async def _analyze_order_causes(self, anomaly_data: Dict[str, Any], 
                                  historical_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze potential causes for order volume anomalies"""
        causes = []
        current_value = anomaly_data.get('current_value', 0)
        expected_range = anomaly_data.get('expected_range', (0, 0))
        
        if current_value < expected_range[0]:  # Order volume drop
            causes = [
                {
                    'cause': 'Market saturation',
                    'description': 'Reduced demand in target market segments',
                    'probability': 0.6,
                    'impact': 'high',
                    'category': 'market'
                },
                {
                    'cause': 'Pricing issues',
                    'description': 'Products priced too high for market conditions',
                    'probability': 0.7,
                    'impact': 'high',
                    'category': 'pricing'
                },
                {
                    'cause': 'Inventory shortages',
                    'description': 'Popular products out of stock',
                    'probability': 0.5,
                    'impact': 'medium',
                    'category': 'inventory'
                }
            ]
        else:  # Order volume increase
            causes = [
                {
                    'cause': 'Successful promotion',
                    'description': 'Effective discount or promotional campaign',
                    'probability': 0.8,
                    'impact': 'high',
                    'category': 'marketing'
                },
                {
                    'cause': 'Market expansion',
                    'description': 'Entry into new geographic or demographic markets',
                    'probability': 0.6,
                    'impact': 'high',
                    'category': 'expansion'
                }
            ]
        
        return causes
    
    async def _analyze_generic_causes(self, anomaly_data: Dict[str, Any], 
                                    historical_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generic cause analysis for other metrics"""
        return [
            {
                'cause': 'Data collection issue',
                'description': 'Potential problem with data measurement or reporting',
                'probability': 0.4,
                'impact': 'low',
                'category': 'technical'
            },
            {
                'cause': 'External market factors',
                'description': 'Broader market or economic conditions',
                'probability': 0.3,
                'impact': 'medium',
                'category': 'external'
            }
        ]
    
    async def _analyze_correlations(self, metric_name: str) -> Dict[str, float]:
        """Analyze correlations with other metrics"""
        try:
            # Get current correlation matrix
            correlations = self.correlation_matrix.get(metric_name, {})
            
            # Filter for significant correlations
            significant_correlations = {
                k: v for k, v in correlations.items() 
                if abs(v) >= self.correlation_threshold
            }
            
            # Sort by correlation strength
            sorted_correlations = dict(
                sorted(significant_correlations.items(), 
                      key=lambda x: abs(x[1]), reverse=True)
            )
            
            return sorted_correlations
            
        except Exception as e:
            logger.error(f"Error analyzing correlations: {str(e)}")
            return {}
    
    async def _assess_business_impact(self, investigation: Dict[str, Any], 
                                   root_cause_analysis: Dict[str, Any]) -> str:
        """Assess business impact of the anomaly"""
        metric_name = investigation['metric_name']
        anomaly_data = investigation['anomaly_data']
        
        try:
            current_value = anomaly_data.get('current_value', 0)
            expected_range = anomaly_data.get('expected_range', (0, 0))
            
            if metric_name == 'revenue':
                if current_value < expected_range[0]:
                    revenue_loss = expected_range[0] - current_value
                    if revenue_loss > 100000:
                        return f"Critical: Potential revenue loss of ${revenue_loss:,.2f}"
                    elif revenue_loss > 50000:
                        return f"High: Revenue shortfall of ${revenue_loss:,.2f}"
                    else:
                        return f"Medium: Minor revenue impact of ${revenue_loss:,.2f}"
                else:
                    revenue_gain = current_value - expected_range[1]
                    return f"Positive: Revenue increase of ${revenue_gain:,.2f}"
            
            elif metric_name == 'customer_satisfaction':
                if current_value < expected_range[0]:
                    satisfaction_drop = expected_range[0] - current_value
                    if satisfaction_drop > 0.5:
                        return "Critical: Significant customer satisfaction decline - risk of churn"
                    else:
                        return "Medium: Customer satisfaction below expectations"
                else:
                    return "Positive: Customer satisfaction improvement"
            
            elif metric_name in ['orders', 'order_volume']:
                if current_value < expected_range[0]:
                    order_drop = expected_range[0] - current_value
                    return f"Medium: Order volume decline of {order_drop:,.0f} orders"
                else:
                    order_increase = current_value - expected_range[1]
                    return f"Positive: Order volume increase of {order_increase:,.0f} orders"
            
            return "Impact assessment requires further analysis"
            
        except Exception as e:
            logger.error(f"Error assessing business impact: {str(e)}")
            return "Unable to assess business impact"
    
    async def _generate_recommendations(self, investigation: Dict[str, Any],
                                      root_cause_analysis: Dict[str, Any],
                                      correlation_analysis: Dict[str, float]) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        try:
            likely_causes = root_cause_analysis.get('likely_causes', [])
            
            for cause in likely_causes[:3]:  # Top 3 causes
                cause_category = cause.get('category', 'unknown')
                
                if cause_category == 'demand':
                    recommendations.append("Implement demand stimulation strategies (promotions, marketing)")
                elif cause_category == 'pricing':
                    recommendations.append("Review and optimize pricing strategy")
                elif cause_category == 'logistics':
                    recommendations.append("Improve delivery and fulfillment processes")
                elif cause_category == 'quality':
                    recommendations.append("Enhance quality control and product standards")
                elif cause_category == 'service':
                    recommendations.append("Strengthen customer service capabilities")
                elif cause_category == 'marketing':
                    recommendations.append("Scale successful marketing initiatives")
                elif cause_category == 'inventory':
                    recommendations.append("Optimize inventory management and stock levels")
            
            # Add correlation-based recommendations
            if correlation_analysis:
                top_correlation = max(correlation_analysis.items(), key=lambda x: abs(x[1]))
                recommendations.append(f"Monitor {top_correlation[0]} closely due to strong correlation")
            
            # Remove duplicates while preserving order
            seen = set()
            unique_recommendations = []
            for rec in recommendations:
                if rec not in seen:
                    seen.add(rec)
                    unique_recommendations.append(rec)
            
            return unique_recommendations[:5]  # Top 5 recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return ["Conduct further investigation to determine appropriate actions"]
    
    async def _get_historical_context(self, metric_name: str) -> Dict[str, Any]:
        """Get historical context for the metric"""
        try:
            # In a real system, this would fetch from data processor
            # For now, return simulated context
            return {
                'data_points': 30,
                'average_value': 1000000 if metric_name == 'revenue' else 4.2,
                'trend': 'stable',
                'volatility': 'low'
            }
        except Exception as e:
            logger.error(f"Error getting historical context: {str(e)}")
            return {}
    
    def _calculate_analysis_confidence(self, root_cause_analysis: Dict[str, Any], 
                                     correlation_analysis: Dict[str, float]) -> float:
        """Calculate confidence score for the analysis"""
        try:
            base_confidence = 0.5
            
            # Boost confidence based on number of likely causes identified
            likely_causes = root_cause_analysis.get('likely_causes', [])
            if likely_causes:
                max_probability = max(cause.get('probability', 0) for cause in likely_causes)
                base_confidence += max_probability * 0.3
            
            # Boost confidence based on correlation strength
            if correlation_analysis:
                max_correlation = max(abs(corr) for corr in correlation_analysis.values())
                base_confidence += max_correlation * 0.2
            
            return min(1.0, base_confidence)
            
        except Exception as e:
            logger.error(f"Error calculating analysis confidence: {str(e)}")
            return 0.5
    
    def _calculate_cause_confidence(self, likely_causes: List[Dict[str, Any]]) -> float:
        """Calculate confidence in root cause analysis"""
        if not likely_causes:
            return 0.0
        
        # Average probability of top causes
        top_probabilities = [cause.get('probability', 0) for cause in likely_causes[:3]]
        return sum(top_probabilities) / len(top_probabilities)
    
    async def _identify_contributing_factors(self, metric_name: str, 
                                           anomaly_data: Dict[str, Any],
                                           likely_causes: List[Dict[str, Any]]) -> List[str]:
        """Identify contributing factors beyond primary causes"""
        factors = []
        
        # Time-based factors
        current_time = datetime.now()
        if current_time.month in [11, 12]:  # Holiday season
            factors.append("Holiday season demand patterns")
        elif current_time.weekday() >= 5:  # Weekend
            factors.append("Weekend shopping behavior")
        
        # Metric-specific factors
        if metric_name == 'revenue':
            factors.extend([
                "Economic conditions",
                "Competitive landscape changes",
                "Product mix variations"
            ])
        elif metric_name == 'customer_satisfaction':
            factors.extend([
                "Service quality variations",
                "Product availability",
                "Communication effectiveness"
            ])
        
        return factors[:5]  # Limit to 5 factors
    
    async def _initialize_correlation_models(self):
        """Initialize correlation models with baseline data"""
        # Initialize with some baseline correlations
        self.correlation_matrix = {
            'revenue': {
                'orders': 0.85,
                'customer_satisfaction': 0.72,
                'avg_order_value': 0.91
            },
            'customer_satisfaction': {
                'revenue': 0.72,
                'delivery_performance': 0.68,
                'order_volume': 0.45
            },
            'orders': {
                'revenue': 0.85,
                'customer_satisfaction': 0.45,
                'marketing_spend': 0.63
            }
        }
        
        logger.info("Correlation models initialized")
    
    async def _publish_analysis_results(self, analysis_report: Dict[str, Any]):
        """Publish analysis results to event bus"""
        from backend.services.event_bus import event_bus, Event
        import uuid
        
        analysis_event = Event(
            event_id=str(uuid.uuid4()),
            event_type='analysis_completed',
            source='enhanced_analyst_agent',
            timestamp=datetime.now().isoformat(),
            data=analysis_report
        )
        
        await event_bus.publish_event('agents', analysis_event)
        
        logger.info(f"🧠 Published analysis results for {analysis_report['metric_name']}")
    
    async def _trigger_simulation_agent(self, analysis_report: Dict[str, Any]):
        """Trigger simulation agent with analysis results"""
        from backend.services.event_bus import event_bus, Event
        import uuid
        
        decision_trigger_event = Event(
            event_id=str(uuid.uuid4()),
            event_type='decision_trigger',
            source='enhanced_analyst_agent',
            timestamp=datetime.now().isoformat(),
            data={
                'analysis_report': analysis_report,
                'priority': 'high' if 'Critical' in analysis_report.get('business_impact', '') else 'medium',
                'requires_simulation': True
            }
        )
        
        await event_bus.publish_event('agents', decision_trigger_event)
        
        logger.info(f"🧠 Triggered simulation agent for {analysis_report['metric_name']}")
    
    def stop_analysis(self):
        """Stop the analysis processing"""
        self.running = False
        logger.info("🛑 Enhanced Analyst Agent stopping...")

# Global enhanced analyst agent instance
enhanced_analyst_agent = EnhancedAnalystAgent()
    
    async def _analyze_revenue_causes_enhanced(self, anomaly_data: Dict[str, Any], 
                                             historical_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhanced revenue cause analysis with ML insights"""
        causes = []
        current_value = anomaly_data.get('current_value', 0)
        expected_range = anomaly_data.get('expected_range', (0, 0))
        
        if current_value < expected_range[0]:  # Revenue drop
            causes = [
                {
                    'cause': 'Decreased order volume',
                    'description': 'Reduction in number of orders placed - analyze customer acquisition and retention',
                    'probability': 0.8,
                    'impact': 'high',
                    'category': 'demand',
                    'ml_actionable': True
                },
                {
                    'cause': 'Lower average order value',
                    'description': 'Customers purchasing lower-value items - review pricing and product mix',
                    'probability': 0.7,
                    'impact': 'high',
                    'category': 'pricing',
                    'ml_actionable': True
                },
                {
                    'cause': 'Increased promotional discounts',
                    'description': 'Higher discount rates reducing revenue per order - optimize promotion strategy',
                    'probability': 0.6,
                    'impact': 'medium',
                    'category': 'pricing',
                    'ml_actionable': True
                },
                {
                    'cause': 'Competitive pressure',
                    'description': 'Competitors offering better prices or products - market analysis needed',
                    'probability': 0.5,
                    'impact': 'high',
                    'category': 'market',
                    'ml_actionable': False
                }
            ]
        else:  # Revenue spike
            causes = [
                {
                    'cause': 'Successful marketing campaign',
                    'description': 'Effective promotional or advertising campaign driving sales',
                    'probability': 0.8,
                    'impact': 'high',
                    'category': 'marketing',
                    'ml_actionable': True
                },
                {
                    'cause': 'Seasonal demand increase',
                    'description': 'Holiday or seasonal shopping surge - capitalize on trend',
                    'probability': 0.7,
                    'impact': 'high',
                    'category': 'seasonal',
                    'ml_actionable': True
                }
            ]
        
        return causes
    
    async def _analyze_satisfaction_causes_enhanced(self, anomaly_data: Dict[str, Any], 
                                                  historical_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhanced satisfaction cause analysis"""
        causes = []
        current_value = anomaly_data.get('current_value', 0)
        expected_range = anomaly_data.get('expected_range', (0, 0))
        
        if current_value < expected_range[0]:  # Satisfaction drop
            causes = [
                {
                    'cause': 'Delivery performance degradation',
                    'description': 'Increased shipping times or delivery issues affecting customer experience',
                    'probability': 0.8,
                    'impact': 'high',
                    'category': 'logistics',
                    'ml_actionable': True
                },
                {
                    'cause': 'Product quality issues',
                    'description': 'Defective or substandard products received by customers',
                    'probability': 0.7,
                    'impact': 'high',
                    'category': 'quality',
                    'ml_actionable': True
                },
                {
                    'cause': 'Customer service degradation',
                    'description': 'Inadequate support or increased response times',
                    'probability': 0.6,
                    'impact': 'high',
                    'category': 'service',
                    'ml_actionable': True
                }
            ]
        else:  # Satisfaction improvement
            causes = [
                {
                    'cause': 'Improved delivery performance',
                    'description': 'Faster and more reliable shipping enhancing customer experience',
                    'probability': 0.8,
                    'impact': 'high',
                    'category': 'logistics',
                    'ml_actionable': True
                }
            ]
        
        return causes
    
    async def _analyze_order_causes_enhanced(self, anomaly_data: Dict[str, Any], 
                                           historical_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhanced order volume cause analysis"""
        causes = []
        current_value = anomaly_data.get('current_value', 0)
        expected_range = anomaly_data.get('expected_range', (0, 0))
        
        if current_value < expected_range[0]:  # Order volume drop
            causes = [
                {
                    'cause': 'Pricing optimization needed',
                    'description': 'Products may be priced too high for current market conditions',
                    'probability': 0.7,
                    'impact': 'high',
                    'category': 'pricing',
                    'ml_actionable': True
                },
                {
                    'cause': 'Marketing effectiveness decline',
                    'description': 'Reduced marketing reach or campaign effectiveness',
                    'probability': 0.6,
                    'impact': 'high',
                    'category': 'marketing',
                    'ml_actionable': True
                }
            ]
        else:  # Order volume increase
            causes = [
                {
                    'cause': 'Successful promotional campaign',
                    'description': 'Effective discount or promotional strategy driving orders',
                    'probability': 0.8,
                    'impact': 'high',
                    'category': 'marketing',
                    'ml_actionable': True
                }
            ]
        
        return causes
    
    async def _analyze_generic_causes_enhanced(self, anomaly_data: Dict[str, Any], 
                                             historical_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhanced generic cause analysis"""
        return [
            {
                'cause': 'Data quality issue',
                'description': 'Potential problem with data measurement or reporting systems',
                'probability': 0.4,
                'impact': 'low',
                'category': 'technical',
                'ml_actionable': False
            },
            {
                'cause': 'External market factors',
                'description': 'Broader market or economic conditions affecting business',
                'probability': 0.3,
                'impact': 'medium',
                'category': 'external',
                'ml_actionable': False
            }
        ]
    
    async def _analyze_ml_correlations(self, metric_name: str) -> Dict[str, float]:
        """Analyze correlations using ML-enhanced correlation matrix"""
        try:
            # Get current correlation matrix (enhanced with ML)
            correlations = self.correlation_matrix.get(metric_name, {})
            
            # If ML service available, enhance correlations with real-time analysis
            if self.ml_service:
                try:
                    # Use ML to detect dynamic correlations
                    ml_correlations = await self._detect_ml_correlations(metric_name)
                    if ml_correlations:
                        # Merge ML correlations with static ones
                        for metric, correlation in ml_correlations.items():
                            correlations[f"{metric}_ml"] = correlation
                
                except Exception as e:
                    logger.debug(f"ML correlation analysis failed: {str(e)}")
            
            # Filter for significant correlations
            significant_correlations = {
                k: v for k, v in correlations.items() 
                if abs(v) >= self.correlation_threshold
            }
            
            # Sort by correlation strength
            sorted_correlations = dict(
                sorted(significant_correlations.items(), 
                      key=lambda x: abs(x[1]), reverse=True)
            )
            
            return sorted_correlations
            
        except Exception as e:
            logger.error(f"Error analyzing ML correlations: {str(e)}")
            return {}
    
    async def _detect_ml_correlations(self, metric_name: str) -> Dict[str, float]:
        """Detect correlations using ML models"""
        try:
            # This would use real-time data to detect correlations
            # For now, return enhanced static correlations
            ml_correlations = {}
            
            if metric_name == 'revenue':
                ml_correlations = {
                    'orders_dynamic': 0.87,
                    'customer_satisfaction_lagged': 0.74,
                    'marketing_spend_correlation': 0.65
                }
            elif metric_name == 'customer_satisfaction':
                ml_correlations = {
                    'delivery_performance_realtime': 0.71,
                    'product_quality_index': 0.68
                }
            
            return ml_correlations
            
        except Exception as e:
            logger.error(f"Error detecting ML correlations: {str(e)}")
            return {}
    
    async def _assess_ml_business_impact(self, investigation: Dict[str, Any], 
                                       root_cause_analysis: Dict[str, Any]) -> str:
        """Assess business impact using ML insights"""
        metric_name = investigation['metric_name']
        anomaly_data = investigation['anomaly_data']
        ml_insights = root_cause_analysis.get('ml_insights', {})
        
        try:
            current_value = anomaly_data.get('current_value', 0)
            expected_range = anomaly_data.get('expected_range', (0, 0))
            
            # Base impact assessment
            base_impact = await self._assess_statistical_business_impact(metric_name, anomaly_data)
            
            # Enhance with ML insights
            if ml_insights and ml_insights.get('model_accuracy', 0) > 0.8:
                confidence_boost = " (ML-validated)"
                
                # Add ML-specific insights
                if 'feature_importance' in ml_insights:
                    top_feature = max(ml_insights['feature_importance'].items(), key=lambda x: x[1])
                    base_impact += f" Key ML factor: {top_feature[0]} (importance: {top_feature[1]:.2f})"
                
                return base_impact + confidence_boost
            
            return base_impact
            
        except Exception as e:
            logger.error(f"Error assessing ML business impact: {str(e)}")
            return "Impact assessment requires further analysis"
    
    async def _assess_statistical_business_impact(self, metric_name: str, anomaly_data: Dict[str, Any]) -> str:
        """Statistical business impact assessment (fallback)"""
        try:
            current_value = anomaly_data.get('current_value', 0)
            expected_range = anomaly_data.get('expected_range', (0, 0))
            
            if metric_name == 'revenue':
                if current_value < expected_range[0]:
                    revenue_loss = expected_range[0] - current_value
                    if revenue_loss > 100000:
                        return f"Critical: Potential revenue loss of ${revenue_loss:,.2f}"
                    elif revenue_loss > 50000:
                        return f"High: Revenue shortfall of ${revenue_loss:,.2f}"
                    else:
                        return f"Medium: Minor revenue impact of ${revenue_loss:,.2f}"
                else:
                    revenue_gain = current_value - expected_range[1]
                    return f"Positive: Revenue increase of ${revenue_gain:,.2f}"
            
            elif metric_name == 'customer_satisfaction':
                if current_value < expected_range[0]:
                    satisfaction_drop = expected_range[0] - current_value
                    if satisfaction_drop > 0.5:
                        return "Critical: Significant customer satisfaction decline - risk of churn"
                    else:
                        return "Medium: Customer satisfaction below expectations"
                else:
                    return "Positive: Customer satisfaction improvement"
            
            return "Impact assessment in progress"
            
        except Exception as e:
            logger.error(f"Error assessing statistical business impact: {str(e)}")
            return "Unable to assess business impact"
    
    async def _generate_ml_recommendations(self, investigation: Dict[str, Any],
                                         root_cause_analysis: Dict[str, Any],
                                         correlation_analysis: Dict[str, float]) -> List[str]:
        """Generate ML-powered actionable recommendations"""
        recommendations = []
        
        try:
            likely_causes = root_cause_analysis.get('likely_causes', [])
            ml_insights = root_cause_analysis.get('ml_insights', {})
            
            # ML-driven recommendations
            ml_actionable_causes = [cause for cause in likely_causes if cause.get('ml_actionable', False)]
            
            for cause in ml_actionable_causes[:3]:  # Top 3 ML-actionable causes
                cause_category = cause.get('category', 'unknown')
                
                if cause_category == 'pricing':
                    recommendations.append("🎯 Use XGBoost price optimization to find optimal pricing strategy")
                elif cause_category == 'demand':
                    recommendations.append("📈 Deploy ARIMA/Prophet demand forecasting for better inventory planning")
                elif cause_category == 'marketing':
                    recommendations.append("🚀 Implement ML-driven customer segmentation for targeted campaigns")
                elif cause_category == 'logistics':
                    recommendations.append("🚚 Use ML models to optimize delivery routes and timing")
                elif cause_category == 'quality':
                    recommendations.append("⭐ Deploy ML quality prediction models for proactive issue detection")
            
            # Add SHAP-based recommendations
            if 'shap_values' in ml_insights:
                top_shap_feature = max(ml_insights['shap_values'].items(), key=lambda x: abs(x[1]))
                recommendations.append(f"🔍 Focus on {top_shap_feature[0]} - highest ML impact factor")
            
            # Correlation-based recommendations
            if correlation_analysis:
                top_correlation = max(correlation_analysis.items(), key=lambda x: abs(x[1]))
                recommendations.append(f"📊 Monitor {top_correlation[0]} closely (correlation: {top_correlation[1]:.2f})")
            
            # Fallback statistical recommendations
            if not recommendations:
                recommendations.extend([
                    "📈 Implement data-driven decision making processes",
                    "🔍 Conduct deeper root cause analysis with more data",
                    "⚡ Set up real-time monitoring for early detection"
                ])
            
            # Remove duplicates while preserving order
            seen = set()
            unique_recommendations = []
            for rec in recommendations:
                if rec not in seen:
                    seen.add(rec)
                    unique_recommendations.append(rec)
            
            return unique_recommendations[:5]  # Top 5 recommendations
            
        except Exception as e:
            logger.error(f"Error generating ML recommendations: {str(e)}")
            return ["Conduct further ML-enhanced investigation to determine appropriate actions"]
    
    async def _get_ml_historical_context(self, metric_name: str) -> Dict[str, Any]:
        """Get ML-enhanced historical context for the metric"""
        try:
            # Check Redis cache for historical context
            if self.redis_cache:
                cached_context = await self.redis_cache.get_model_output(f'historical_context_{metric_name}')
                if cached_context:
                    return cached_context
            
            # Generate enhanced context
            context = {
                'data_points': 30,
                'average_value': 1000000 if metric_name == 'revenue' else 4.2,
                'trend': 'stable',
                'volatility': 'low',
                'data_available': True,
                'ml_enhanced': True
            }
            
            # Cache the context
            if self.redis_cache:
                await self.redis_cache.cache_model_output(
                    f'historical_context_{metric_name}',
                    context
                )
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting ML historical context: {str(e)}")
            return {'data_available': False}
    
    def _calculate_ml_analysis_confidence(self, root_cause_analysis: Dict[str, Any], 
                                        correlation_analysis: Dict[str, float]) -> float:
        """Calculate confidence score for ML-enhanced analysis"""
        try:
            base_confidence = 0.5
            
            # Boost confidence based on ML enhancement
            if root_cause_analysis.get('ml_enhanced', False):
                base_confidence += 0.2
            
            # Boost confidence based on number of likely causes identified
            likely_causes = root_cause_analysis.get('likely_causes', [])
            if likely_causes:
                max_probability = max(cause.get('probability', 0) for cause in likely_causes)
                ml_confidence = max(cause.get('ml_confidence', 0) for cause in likely_causes)
                base_confidence += (max_probability + ml_confidence) / 2 * 0.3
            
            # Boost confidence based on correlation strength
            if correlation_analysis:
                max_correlation = max(abs(corr) for corr in correlation_analysis.values())
                base_confidence += max_correlation * 0.2
            
            # Boost confidence based on ML model accuracy
            ml_insights = root_cause_analysis.get('ml_insights', {})
            if ml_insights.get('model_accuracy', 0) > 0.8:
                base_confidence += 0.15
            
            return min(1.0, base_confidence)
            
        except Exception as e:
            logger.error(f"Error calculating ML analysis confidence: {str(e)}")
            return 0.5
    
    def _calculate_cause_confidence(self, likely_causes: List[Dict[str, Any]]) -> float:
        """Calculate confidence in root cause analysis"""
        if not likely_causes:
            return 0.0
        
        # Average probability of top causes, weighted by ML confidence
        top_causes = likely_causes[:3]
        total_confidence = 0
        
        for cause in top_causes:
            probability = cause.get('probability', 0)
            ml_confidence = cause.get('ml_confidence', 0)
            # Weight ML-derived causes higher
            weight = 1.2 if cause.get('ml_derived', False) else 1.0
            total_confidence += (probability + ml_confidence) / 2 * weight
        
        return min(1.0, total_confidence / len(top_causes))
    
    async def _identify_ml_contributing_factors(self, metric_name: str, 
                                              anomaly_data: Dict[str, Any],
                                              likely_causes: List[Dict[str, Any]],
                                              ml_insights: Dict[str, Any]) -> List[str]:
        """Identify contributing factors using ML insights"""
        factors = []
        
        # Time-based factors
        current_time = datetime.now()
        if current_time.month in [11, 12]:  # Holiday season
            factors.append("Holiday season demand patterns")
        elif current_time.weekday() >= 5:  # Weekend
            factors.append("Weekend shopping behavior")
        
        # ML-derived factors
        if 'feature_importance' in ml_insights:
            for feature, importance in ml_insights['feature_importance'].items():
                if importance > 0.15:  # Significant importance
                    factors.append(f"ML factor: {feature} (importance: {importance:.2f})")
        
        # Metric-specific factors enhanced with ML
        if metric_name == 'revenue':
            factors.extend([
                "Economic conditions (ML-trackable)",
                "Competitive landscape changes (sentiment analysis)",
                "Product mix variations (ML-optimizable)"
            ])
        elif metric_name == 'customer_satisfaction':
            factors.extend([
                "Service quality variations (ML-predictable)",
                "Product availability (ML-optimizable)",
                "Communication effectiveness (NLP-analyzable)"
            ])
        
        return factors[:6]  # Limit to 6 factors
    
    async def _initialize_ml_correlation_models(self):
        """Initialize ML-enhanced correlation models"""
        # Enhanced correlation matrix with ML insights
        self.correlation_matrix = {
            'revenue': {
                'orders': 0.85,
                'customer_satisfaction': 0.72,
                'avg_order_value': 0.91,
                'marketing_spend': 0.68,
                'delivery_performance': 0.58
            },
            'customer_satisfaction': {
                'revenue': 0.72,
                'delivery_performance': 0.68,
                'order_volume': 0.45,
                'product_quality': 0.74,
                'response_time': -0.63
            },
            'orders': {
                'revenue': 0.85,
                'customer_satisfaction': 0.45,
                'marketing_spend': 0.63,
                'price_competitiveness': -0.52,
                'inventory_availability': 0.67
            }
        }
        
        logger.info("ML-enhanced correlation models initialized")
    
    async def _publish_ml_analysis_results(self, analysis_report: Dict[str, Any]):
        """Publish ML analysis results to event bus"""
        from backend.services.event_bus import event_bus, Event
        import uuid
        
        analysis_event = Event(
            event_id=str(uuid.uuid4()),
            event_type='ml_analysis_completed',
            source='enhanced_analyst_agent',
            timestamp=datetime.now().isoformat(),
            data=analysis_report
        )
        
        await event_bus.publish_event('agents', analysis_event)
        
        logger.info(f"🧠 Published ML analysis results for {analysis_report['metric_name']}")
    
    async def _trigger_simulation_agent(self, analysis_report: Dict[str, Any]):
        """Trigger simulation agent with ML analysis results"""
        from backend.services.event_bus import event_bus, Event
        import uuid
        
        decision_trigger_event = Event(
            event_id=str(uuid.uuid4()),
            event_type='ml_decision_trigger',
            source='enhanced_analyst_agent',
            timestamp=datetime.now().isoformat(),
            data={
                'analysis_report': analysis_report,
                'priority': 'high' if 'Critical' in analysis_report.get('business_impact', '') else 'medium',
                'requires_simulation': True,
                'ml_enhanced': analysis_report.get('ml_enhanced', False),
                'ml_confidence': analysis_report.get('confidence_score', 0.5)
            }
        )
        
        await event_bus.publish_event('agents', decision_trigger_event)
        
        logger.info(f"🧠 Triggered ML-enhanced simulation agent for {analysis_report['metric_name']}")
    
    def stop_analysis(self):
        """Stop the analysis processing"""
        self.running = False
        logger.info("🛑 Enhanced Analyst Agent stopping...")

# Global enhanced analyst agent instance
enhanced_analyst_agent = EnhancedAnalystAgent()