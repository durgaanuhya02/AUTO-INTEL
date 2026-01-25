import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import openai
from scipy.stats import pearsonr

from .base_agent import BaseAgent
from backend.models.schemas import AgentType, AgentMessage

class AnalystAgent(BaseAgent):
    def __init__(self, redis_client, db_session, openai_client):
        super().__init__(AgentType.ANALYST, redis_client)
        self.db_session = db_session
        self.openai_client = openai_client
        self.correlation_matrix = {}
        self.analysis_history = []
        self.pending_anomalies = []
    
    async def initialize(self):
        """Initialize the analyst agent"""
        await self.update_status("initializing", "Setting up analysis models")
        await self._load_correlation_data()
        await self.update_status("active", "Ready for analysis")
        self.logger.info("Analyst agent initialized successfully")
    
    async def process(self):
        """Main processing loop - analyze pending anomalies and correlations"""
        await self.update_status("processing", "Analyzing correlations and root causes")
        
        try:
            # Process pending anomalies
            if self.pending_anomalies:
                for anomaly in self.pending_anomalies:
                    analysis = await self._perform_root_cause_analysis(anomaly)
                    if analysis:
                        await self.send_message(
                            AgentType.SIMULATION,
                            "analysis_complete",
                            analysis
                        )
                
                self.pending_anomalies.clear()
            
            # Perform periodic correlation analysis
            await self._update_correlations()
            
            # Generate insights
            insights = await self._generate_insights()
            if insights:
                await self.send_message(
                    None,  # Broadcast
                    "insights_generated",
                    {"insights": insights, "timestamp": datetime.utcnow().isoformat()}
                )
            
            await self.update_status("active", "Analysis complete", {
                "last_analysis": datetime.utcnow().isoformat(),
                "correlations_updated": len(self.correlation_matrix),
                "insights_generated": len(insights) if insights else 0
            })
            
        except Exception as e:
            self.logger.error(f"Error in analyst processing: {e}")
            await self.update_status("error", f"Analysis error: {str(e)}")
    
    async def handle_message(self, message: AgentMessage):
        """Handle messages from other agents"""
        await super().handle_message(message)
        
        if message.message_type == "anomaly_detected":
            self.pending_anomalies.append(message.content)
            await self.update_status("processing", f"Analyzing anomaly: {message.content.get('metric_type')}")
        
        elif message.message_type == "metrics_update":
            # Store metrics for correlation analysis
            await self._store_metrics_for_analysis(message.content["metrics"])
    
    async def _perform_root_cause_analysis(self, anomaly: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Perform root cause analysis for detected anomalies"""
        metric_type = anomaly["metric_type"]
        current_value = anomaly["current_value"]
        
        # Get historical data and correlations
        correlations = await self._get_correlations_for_metric(metric_type)
        historical_context = await self._get_historical_context(metric_type)
        
        # Use AI to analyze the root cause
        analysis_prompt = f"""
        Analyze this business metric anomaly:
        
        Metric: {metric_type}
        Current Value: {current_value}
        Expected Value: {anomaly.get('expected_value', 'N/A')}
        Severity: {anomaly.get('severity', 'Unknown')}
        
        Correlations with other metrics:
        {correlations}
        
        Historical Context:
        {historical_context}
        
        Provide a root cause analysis including:
        1. Most likely causes (ranked by probability)
        2. Contributing factors
        3. Business impact assessment
        4. Recommended investigation areas
        
        Format as JSON with keys: likely_causes, contributing_factors, business_impact, recommendations
        """
        
        try:
            response = await self._call_openai(analysis_prompt)
            analysis_result = {
                "anomaly": anomaly,
                "root_cause_analysis": response,
                "correlations": correlations,
                "confidence_score": self._calculate_analysis_confidence(anomaly, correlations),
                "timestamp": datetime.utcnow().isoformat(),
                "analyst_agent_id": str(id(self))
            }
            
            # Store analysis for future reference
            self.analysis_history.append(analysis_result)
            if len(self.analysis_history) > 50:
                self.analysis_history = self.analysis_history[-50:]
            
            self.logger.info(f"Root cause analysis completed for {metric_type}")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Error in root cause analysis: {e}")
            return None
    
    async def _get_correlations_for_metric(self, metric_type: str) -> Dict[str, float]:
        """Get correlations between the given metric and other metrics"""
        correlations = {}
        
        if metric_type in self.correlation_matrix:
            correlations = self.correlation_matrix[metric_type].copy()
            # Sort by absolute correlation strength
            correlations = dict(sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True))
        
        return correlations
    
    async def _get_historical_context(self, metric_type: str) -> str:
        """Get historical context for the metric"""
        # Get recent metric history
        metric_history = await self.get_data(f"metric_history_{metric_type}")
        
        if not metric_history:
            return "No historical data available"
        
        recent_values = metric_history[-10:] if len(metric_history) >= 10 else metric_history
        
        context = f"""
        Recent {metric_type} values: {recent_values}
        Average: {np.mean(recent_values):.2f}
        Trend: {'Increasing' if recent_values[-1] > recent_values[0] else 'Decreasing'}
        Volatility: {np.std(recent_values):.2f}
        """
        
        return context
    
    async def _update_correlations(self):
        """Update correlation matrix between different metrics"""
        try:
            # Get recent metrics data
            metrics_data = {}
            metric_types = ["revenue", "orders", "churn_risk", "delivery_delay", "customer_satisfaction"]
            
            for metric_type in metric_types:
                history = await self.get_data(f"metric_history_{metric_type}")
                if history and len(history) > 10:
                    metrics_data[metric_type] = history[-30:]  # Last 30 data points
            
            # Calculate correlations
            if len(metrics_data) >= 2:
                for metric1 in metrics_data:
                    if metric1 not in self.correlation_matrix:
                        self.correlation_matrix[metric1] = {}
                    
                    for metric2 in metrics_data:
                        if metric1 != metric2:
                            try:
                                # Ensure same length
                                min_len = min(len(metrics_data[metric1]), len(metrics_data[metric2]))
                                data1 = metrics_data[metric1][-min_len:]
                                data2 = metrics_data[metric2][-min_len:]
                                
                                correlation, p_value = pearsonr(data1, data2)
                                if not np.isnan(correlation):
                                    self.correlation_matrix[metric1][metric2] = correlation
                            except Exception as e:
                                self.logger.warning(f"Error calculating correlation between {metric1} and {metric2}: {e}")
            
            self.logger.info("Correlation matrix updated")
            
        except Exception as e:
            self.logger.error(f"Error updating correlations: {e}")
    
    async def _generate_insights(self) -> List[Dict[str, Any]]:
        """Generate business insights from analysis"""
        insights = []
        
        try:
            # Analyze correlation patterns
            strong_correlations = []
            for metric1, correlations in self.correlation_matrix.items():
                for metric2, correlation in correlations.items():
                    if abs(correlation) > 0.7:  # Strong correlation
                        strong_correlations.append({
                            "metric1": metric1,
                            "metric2": metric2,
                            "correlation": correlation,
                            "strength": "strong" if abs(correlation) > 0.8 else "moderate"
                        })
            
            if strong_correlations:
                insights.append({
                    "type": "correlation_insight",
                    "title": "Strong Metric Correlations Detected",
                    "description": f"Found {len(strong_correlations)} strong correlations between metrics",
                    "details": strong_correlations,
                    "actionable": True,
                    "priority": "medium"
                })
            
            # Analyze recent analysis patterns
            if len(self.analysis_history) >= 3:
                recent_analyses = self.analysis_history[-5:]
                common_causes = {}
                
                for analysis in recent_analyses:
                    if "root_cause_analysis" in analysis:
                        # Extract likely causes (this would be more sophisticated in practice)
                        causes = analysis["root_cause_analysis"].get("likely_causes", [])
                        for cause in causes:
                            if isinstance(cause, str):
                                common_causes[cause] = common_causes.get(cause, 0) + 1
                
                if common_causes:
                    most_common = max(common_causes.items(), key=lambda x: x[1])
                    if most_common[1] >= 2:
                        insights.append({
                            "type": "pattern_insight",
                            "title": "Recurring Issue Pattern",
                            "description": f"'{most_common[0]}' appears in multiple recent analyses",
                            "frequency": most_common[1],
                            "actionable": True,
                            "priority": "high"
                        })
            
        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")
        
        return insights
    
    async def _store_metrics_for_analysis(self, metrics: Dict[str, float]):
        """Store metrics data for correlation analysis"""
        for metric_type, value in metrics.items():
            # Get existing history
            history = await self.get_data(f"metric_history_{metric_type}") or []
            
            # Add new value
            history.append(value)
            
            # Keep last 100 values
            if len(history) > 100:
                history = history[-100:]
            
            # Store updated history
            await self.store_data(f"metric_history_{metric_type}", history, 3600)
    
    async def _calculate_analysis_confidence(self, anomaly: Dict[str, Any], correlations: Dict[str, float]) -> float:
        """Calculate confidence score for the analysis"""
        base_confidence = 0.5
        
        # Increase confidence based on correlation strength
        if correlations:
            max_correlation = max(abs(corr) for corr in correlations.values())
            base_confidence += min(0.3, max_correlation * 0.3)
        
        # Increase confidence based on anomaly severity
        severity = anomaly.get("severity", "low")
        severity_boost = {"low": 0.0, "medium": 0.1, "high": 0.2, "critical": 0.3}
        base_confidence += severity_boost.get(severity, 0.0)
        
        # Increase confidence based on historical data availability
        if len(self.analysis_history) > 5:
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    async def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI API for analysis"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a business analyst AI. Provide structured, actionable analysis in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            
            # Try to parse as JSON, fallback to structured text
            try:
                import json
                return json.loads(content)
            except:
                return {"analysis": content, "format": "text"}
                
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            return {"error": str(e), "analysis": "AI analysis unavailable"}
    
    async def _load_correlation_data(self):
        """Load initial correlation data"""
        # Initialize with some baseline correlations for demo
        self.correlation_matrix = {
            "revenue": {"orders": 0.85, "customer_satisfaction": 0.72, "delivery_delay": -0.45},
            "orders": {"revenue": 0.85, "churn_risk": -0.38, "delivery_delay": 0.23},
            "churn_risk": {"customer_satisfaction": -0.67, "delivery_delay": 0.54},
            "delivery_delay": {"customer_satisfaction": -0.58, "revenue": -0.45},
            "customer_satisfaction": {"revenue": 0.72, "churn_risk": -0.67}
        }