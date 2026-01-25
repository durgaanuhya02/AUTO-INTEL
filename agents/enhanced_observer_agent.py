"""
Enhanced Observer Agent - Always-On Autonomous Monitoring
Subscribes to metric events and detects patterns, anomalies, and trends
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
from dataclasses import dataclass

from .base_agent import BaseAgent
from backend.services.event_bus import event_bus, EventType, Event, publish_agent_status, publish_anomaly_detected
from backend.services.redis_cache_service import redis_cache_service

logger = logging.getLogger(__name__)

@dataclass
class ObservationPattern:
    """Detected pattern in metrics"""
    pattern_type: str
    confidence: float
    description: str
    data_points: List[float]
    trend_direction: str  # 'up', 'down', 'stable', 'volatile'
    significance: str     # 'low', 'medium', 'high', 'critical'

class EnhancedObserverAgent(BaseAgent):
    """
    Always-on observer agent that:
    1. Subscribes to metric update events
    2. Maintains rolling window of metrics
    3. Detects patterns and anomalies autonomously
    4. Publishes observations to trigger other agents
    """
    
    def __init__(self):
        super().__init__("enhanced_observer", "Observer")
        self.metric_history: Dict[str, List[float]] = {}
        self.timestamp_history: List[float] = []
        self.window_size = 50  # Keep last 50 data points
        self.observation_count = 0
        self.patterns_detected = 0
        self.anomalies_detected = 0
        
        # Pattern detection parameters
        self.volatility_threshold = 0.15  # 15% coefficient of variation
        self.trend_threshold = 0.05       # 5% change for trend detection
        self.anomaly_z_score = 2.0        # Z-score threshold for anomalies
        
    async def initialize(self) -> bool:
        """Initialize the observer agent"""
        try:
            # Subscribe to metric update events
            if event_bus.redis_client:
                asyncio.create_task(event_bus.subscribe(
                    event_types=[EventType.METRIC_UPDATE],
                    consumer_name="observer_agent",
                    callback=self._handle_metric_update
                ))
            
            self.status = "active"
            self.current_task = "Monitoring metric streams for patterns and anomalies"
            
            # Publish initial status
            await self._publish_status()
            
            logger.info("✅ Enhanced Observer Agent initialized and subscribed to metric events")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Observer Agent: {e}")
            self.status = "error"
            return False
    
    async def start(self):
        """Start the observer agent"""
        if not await self.initialize():
            return
            
        self.running = True
        logger.info("🔍 Enhanced Observer Agent started - autonomous monitoring active")
        
        # Start background tasks
        asyncio.create_task(self._pattern_analysis_loop())
        asyncio.create_task(self._status_update_loop())
    
    async def stop(self):
        """Stop the observer agent"""
        self.running = False
        self.status = "stopped"
        await self._publish_status()
        logger.info("🛑 Enhanced Observer Agent stopped")
    
    async def _handle_metric_update(self, event: Event):
        """Handle incoming metric update events"""
        try:
            self.last_activity = datetime.utcnow()
            self.observation_count += 1
            
            # Extract metrics from event
            metrics = event.data.get('metrics', {})
            timestamp = event.timestamp
            
            # Update metric history
            await self._update_metric_history(metrics, timestamp)
            
            # Perform real-time analysis
            await self._analyze_metrics_realtime(metrics)
            
            # Update current task
            self.current_task = f"Processed {self.observation_count} metric updates, detected {self.patterns_detected} patterns"
            
            logger.debug(f"🔍 Observer processed metric update: {len(metrics)} metrics")
            
        except Exception as e:
            logger.error(f"❌ Error handling metric update: {e}")
    
    async def _update_metric_history(self, metrics: Dict[str, Any], timestamp: float):
        """Update rolling window of metric history"""
        try:
            # Add timestamp
            self.timestamp_history.append(timestamp)
            if len(self.timestamp_history) > self.window_size:
                self.timestamp_history.pop(0)
            
            # Update each metric's history
            for metric_name, value in metrics.items():
                if isinstance(value, (int, float)):
                    if metric_name not in self.metric_history:
                        self.metric_history[metric_name] = []
                    
                    self.metric_history[metric_name].append(float(value))
                    
                    # Maintain window size
                    if len(self.metric_history[metric_name]) > self.window_size:
                        self.metric_history[metric_name].pop(0)
            
            # Store in cache for other agents
            await self._cache_metric_history()
            
        except Exception as e:
            logger.error(f"❌ Error updating metric history: {e}")
    
    async def _analyze_metrics_realtime(self, current_metrics: Dict[str, Any]):
        """Perform real-time analysis on current metrics"""
        try:
            observations = []
            
            for metric_name, current_value in current_metrics.items():
                if not isinstance(current_value, (int, float)):
                    continue
                    
                if metric_name not in self.metric_history or len(self.metric_history[metric_name]) < 5:
                    continue
                
                history = self.metric_history[metric_name]
                
                # Detect anomalies using Z-score
                anomaly = await self._detect_anomaly(metric_name, current_value, history)
                if anomaly:
                    observations.append(anomaly)
                    self.anomalies_detected += 1
                
                # Detect trends (need at least 10 points)
                if len(history) >= 10:
                    trend = await self._detect_trend(metric_name, history)
                    if trend:
                        observations.append(trend)
                
                # Detect volatility patterns
                if len(history) >= 20:
                    volatility = await self._detect_volatility(metric_name, history)
                    if volatility:
                        observations.append(volatility)
            
            # Publish significant observations
            for observation in observations:
                if observation.significance in ['high', 'critical']:
                    await self._publish_observation(observation)
                    self.patterns_detected += 1
            
        except Exception as e:
            logger.error(f"❌ Error in real-time analysis: {e}")
    
    async def _detect_anomaly(self, metric_name: str, current_value: float, 
                            history: List[float]) -> Optional[ObservationPattern]:
        """Detect anomalies using statistical methods"""
        try:
            if len(history) < 10:
                return None
            
            # Calculate Z-score
            mean_val = np.mean(history)
            std_val = np.std(history)
            
            if std_val == 0:
                return None
            
            z_score = abs((current_value - mean_val) / std_val)
            
            if z_score > self.anomaly_z_score:
                direction = "above" if current_value > mean_val else "below"
                significance = "critical" if z_score > 3.0 else "high"
                
                return ObservationPattern(
                    pattern_type="anomaly",
                    confidence=min(0.99, z_score / 4.0),  # Cap at 99%
                    description=f"{metric_name} anomaly: {current_value:.2f} is {direction} normal range (Z-score: {z_score:.2f})",
                    data_points=[current_value],
                    trend_direction="anomalous",
                    significance=significance
                )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error detecting anomaly: {e}")
            return None
    
    async def _detect_trend(self, metric_name: str, history: List[float]) -> Optional[ObservationPattern]:
        """Detect trends using linear regression"""
        try:
            if len(history) < 10:
                return None
            
            # Simple linear regression
            x = np.arange(len(history))
            y = np.array(history)
            
            # Calculate slope
            slope = np.polyfit(x, y, 1)[0]
            
            # Calculate relative slope (percentage change per period)
            mean_val = np.mean(history)
            if mean_val == 0:
                return None
            
            relative_slope = slope / mean_val
            
            if abs(relative_slope) > self.trend_threshold:
                direction = "up" if slope > 0 else "down"
                confidence = min(0.95, abs(relative_slope) * 10)  # Scale confidence
                
                # Determine significance
                if abs(relative_slope) > 0.2:  # 20% change
                    significance = "critical"
                elif abs(relative_slope) > 0.1:  # 10% change
                    significance = "high"
                else:
                    significance = "medium"
                
                return ObservationPattern(
                    pattern_type="trend",
                    confidence=confidence,
                    description=f"{metric_name} trending {direction}: {relative_slope:.2%} change per period",
                    data_points=history[-10:],  # Last 10 points
                    trend_direction=direction,
                    significance=significance
                )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error detecting trend: {e}")
            return None
    
    async def _detect_volatility(self, metric_name: str, history: List[float]) -> Optional[ObservationPattern]:
        """Detect high volatility patterns"""
        try:
            if len(history) < 20:
                return None
            
            # Calculate coefficient of variation
            mean_val = np.mean(history)
            std_val = np.std(history)
            
            if mean_val == 0:
                return None
            
            cv = std_val / mean_val
            
            if cv > self.volatility_threshold:
                significance = "high" if cv > 0.3 else "medium"
                
                return ObservationPattern(
                    pattern_type="volatility",
                    confidence=min(0.9, cv * 2),
                    description=f"{metric_name} high volatility detected: {cv:.2%} coefficient of variation",
                    data_points=history[-20:],  # Last 20 points
                    trend_direction="volatile",
                    significance=significance
                )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error detecting volatility: {e}")
            return None
    
    async def _publish_observation(self, observation: ObservationPattern):
        """Publish significant observations as anomaly events"""
        try:
            anomaly_data = {
                'pattern_type': observation.pattern_type,
                'confidence': observation.confidence,
                'description': observation.description,
                'trend_direction': observation.trend_direction,
                'significance': observation.significance,
                'data_points_count': len(observation.data_points),
                'detected_by': 'enhanced_observer_agent',
                'detection_timestamp': datetime.utcnow().isoformat()
            }
            
            success = await publish_anomaly_detected(
                source_agent="enhanced_observer",
                anomaly_data=anomaly_data,
                correlation_id=f"observer_{int(time.time())}"
            )
            
            if success:
                logger.info(f"🔍 Observer published observation: {observation.description}")
            
        except Exception as e:
            logger.error(f"❌ Error publishing observation: {e}")
    
    async def _pattern_analysis_loop(self):
        """Background loop for deeper pattern analysis"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                # Perform cross-metric correlation analysis
                await self._analyze_correlations()
                
                # Detect seasonal patterns
                await self._detect_seasonal_patterns()
                
                # Update performance metrics
                self.performance = min(100.0, 80.0 + (self.patterns_detected / max(1, self.observation_count)) * 20)
                
            except Exception as e:
                logger.error(f"❌ Error in pattern analysis loop: {e}")
                await asyncio.sleep(60)
    
    async def _analyze_correlations(self):
        """Analyze correlations between different metrics"""
        try:
            if len(self.metric_history) < 2:
                return
            
            # Find metrics with sufficient data
            valid_metrics = {
                name: history for name, history in self.metric_history.items()
                if len(history) >= 20
            }
            
            if len(valid_metrics) < 2:
                return
            
            # Calculate correlations
            metric_names = list(valid_metrics.keys())
            for i in range(len(metric_names)):
                for j in range(i + 1, len(metric_names)):
                    metric1, metric2 = metric_names[i], metric_names[j]
                    
                    # Ensure same length
                    min_len = min(len(valid_metrics[metric1]), len(valid_metrics[metric2]))
                    data1 = valid_metrics[metric1][-min_len:]
                    data2 = valid_metrics[metric2][-min_len:]
                    
                    # Calculate correlation
                    correlation = np.corrcoef(data1, data2)[0, 1]
                    
                    # Report strong correlations
                    if abs(correlation) > 0.7:
                        correlation_type = "positive" if correlation > 0 else "negative"
                        logger.info(f"🔗 Strong {correlation_type} correlation detected: {metric1} ↔ {metric2} (r={correlation:.3f})")
            
        except Exception as e:
            logger.error(f"❌ Error analyzing correlations: {e}")
    
    async def _detect_seasonal_patterns(self):
        """Detect seasonal or cyclical patterns"""
        try:
            # This would require more sophisticated time series analysis
            # For now, just log that we're checking
            logger.debug("🔄 Checking for seasonal patterns...")
            
        except Exception as e:
            logger.error(f"❌ Error detecting seasonal patterns: {e}")
    
    async def _cache_metric_history(self):
        """Cache metric history for other agents"""
        try:
            if redis_cache_service.redis_client:
                cache_data = {
                    'metric_history': self.metric_history,
                    'timestamp_history': self.timestamp_history,
                    'window_size': self.window_size,
                    'last_update': datetime.utcnow().isoformat()
                }
                
                await redis_cache_service.set_json("observer_metric_history", cache_data, ttl=300)
                
        except Exception as e:
            logger.error(f"❌ Error caching metric history: {e}")
    
    async def _status_update_loop(self):
        """Periodically update agent status"""
        while self.running:
            try:
                await asyncio.sleep(30)  # Update every 30 seconds
                await self._publish_status()
                
            except Exception as e:
                logger.error(f"❌ Error in status update loop: {e}")
                await asyncio.sleep(30)
    
    async def _publish_status(self):
        """Publish current agent status"""
        try:
            status_data = {
                'agent_name': self.name,
                'agent_type': self.agent_type,
                'status': self.status,
                'current_task': self.current_task,
                'performance': self.performance,
                'last_activity': self.last_activity.isoformat() if self.last_activity else None,
                'uptime': (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0,
                'observations_processed': self.observation_count,
                'patterns_detected': self.patterns_detected,
                'anomalies_detected': self.anomalies_detected,
                'metrics_tracked': len(self.metric_history),
                'data_window_size': len(self.timestamp_history)
            }
            
            await publish_agent_status(
                agent_name=self.name,
                status_data=status_data,
                correlation_id=f"status_{self.name}_{int(time.time())}"
            )
            
        except Exception as e:
            logger.error(f"❌ Error publishing status: {e}")
    
    def get_insights(self) -> Dict[str, Any]:
        """Get current insights from observations"""
        return {
            'total_observations': self.observation_count,
            'patterns_detected': self.patterns_detected,
            'anomalies_detected': self.anomalies_detected,
            'metrics_tracked': len(self.metric_history),
            'detection_rate': self.patterns_detected / max(1, self.observation_count),
            'current_window_size': len(self.timestamp_history),
            'active_monitoring': self.running
        }

# Global observer agent instance
enhanced_observer_agent = EnhancedObserverAgent()