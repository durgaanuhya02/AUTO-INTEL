"""
Continuous Monitoring Service - 24/7 Background Daemon
Autonomous metric collection and event generation for agentic AI system
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json

from .event_bus import event_bus, EventType, Event, publish_metric_update, publish_anomaly_detected
from .real_data_processor import RealDataProcessor
from .redis_cache_service import redis_cache_service

logger = logging.getLogger(__name__)

class ContinuousMonitoringService:
    """
    24/7 Background monitoring service that:
    1. Continuously polls metrics every X seconds
    2. Publishes metric updates to event bus
    3. Triggers autonomous agent reactions
    4. Maintains system health monitoring
    """
    
    def __init__(self, poll_interval: int = 30):
        self.poll_interval = poll_interval  # seconds
        self.running = False
        self.data_processor = RealDataProcessor()
        self.last_metrics: Optional[Dict[str, Any]] = None
        self.baseline_metrics: Optional[Dict[str, Any]] = None
        self.monitoring_start_time = None
        
        # Anomaly detection thresholds
        self.thresholds = {
            'revenue_change_percent': 15.0,  # Alert if revenue changes >15%
            'order_change_percent': 20.0,   # Alert if orders change >20%
            'satisfaction_threshold': 4.0,   # Alert if satisfaction <4.0
            'growth_rate_threshold': -0.05   # Alert if growth rate <-5%
        }
    
    async def initialize(self) -> bool:
        """Initialize the monitoring service"""
        try:
            # Initialize data processor
            await self.data_processor.initialize()
            
            # Get baseline metrics
            self.baseline_metrics = await self._collect_current_metrics()
            if not self.baseline_metrics:
                logger.error("❌ Failed to collect baseline metrics")
                return False
            
            logger.info("✅ Continuous monitoring service initialized")
            logger.info(f"📊 Baseline metrics: Revenue=${self.baseline_metrics.get('revenue', 0):,.2f}, Orders={self.baseline_metrics.get('orders', 0):,}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize monitoring service: {e}")
            return False
    
    async def start(self):
        """Start continuous monitoring"""
        if not await self.initialize():
            logger.error("❌ Cannot start monitoring - initialization failed")
            return
            
        self.running = True
        self.monitoring_start_time = datetime.utcnow()
        
        logger.info(f"🚀 Starting continuous monitoring (polling every {self.poll_interval}s)")
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._periodic_baseline_update())
    
    async def stop(self):
        """Stop continuous monitoring"""
        self.running = False
        logger.info("🛑 Continuous monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop - runs every poll_interval seconds"""
        while self.running:
            try:
                start_time = time.time()
                
                # Collect current metrics
                current_metrics = await self._collect_current_metrics()
                if not current_metrics:
                    logger.warning("⚠️ Failed to collect metrics, skipping cycle")
                    await asyncio.sleep(self.poll_interval)
                    continue
                
                # Publish metric update event
                await self._publish_metric_update(current_metrics)
                
                # Detect anomalies if we have previous metrics
                if self.last_metrics:
                    await self._detect_anomalies(current_metrics, self.last_metrics)
                
                # Update cache
                await self._update_cache(current_metrics)
                
                # Store current metrics for next comparison
                self.last_metrics = current_metrics
                
                # Calculate processing time
                processing_time = time.time() - start_time
                logger.debug(f"📊 Monitoring cycle completed in {processing_time:.2f}s")
                
                # Sleep for remaining time
                sleep_time = max(0, self.poll_interval - processing_time)
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(self.poll_interval)
    
    async def _collect_current_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect current business metrics"""
        try:
            # Get metrics from data processor
            metrics = await self.data_processor.get_current_metrics()
            
            if not metrics:
                return None
            
            # Add monitoring metadata
            metrics.update({
                'collection_timestamp': datetime.utcnow().isoformat(),
                'monitoring_uptime_seconds': (
                    datetime.utcnow() - self.monitoring_start_time
                ).total_seconds() if self.monitoring_start_time else 0,
                'data_freshness': 'real-time',
                'source': 'continuous_monitoring'
            })
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Error collecting metrics: {e}")
            return None
    
    async def _publish_metric_update(self, metrics: Dict[str, Any]):
        """Publish metric update to event bus"""
        try:
            correlation_id = f"monitoring_{int(time.time())}"
            
            success = await publish_metric_update(
                source_agent="continuous_monitoring",
                metrics=metrics,
                correlation_id=correlation_id
            )
            
            if success:
                logger.debug(f"📡 Published metric update (correlation: {correlation_id})")
            else:
                logger.warning("⚠️ Failed to publish metric update")
                
        except Exception as e:
            logger.error(f"❌ Error publishing metric update: {e}")
    
    async def _detect_anomalies(self, current: Dict[str, Any], previous: Dict[str, Any]):
        """Detect anomalies by comparing current vs previous metrics"""
        try:
            anomalies = []
            
            # Revenue change detection
            if 'revenue' in current and 'revenue' in previous:
                revenue_change = abs(current['revenue'] - previous['revenue']) / previous['revenue'] * 100
                if revenue_change > self.thresholds['revenue_change_percent']:
                    direction = "increase" if current['revenue'] > previous['revenue'] else "decrease"
                    anomalies.append({
                        'type': 'revenue_anomaly',
                        'severity': 'high',
                        'description': f"Revenue {direction} of {revenue_change:.1f}% detected",
                        'current_value': current['revenue'],
                        'previous_value': previous['revenue'],
                        'change_percent': revenue_change * (1 if direction == "increase" else -1)
                    })
            
            # Order volume change detection
            if 'orders' in current and 'orders' in previous:
                order_change = abs(current['orders'] - previous['orders']) / max(previous['orders'], 1) * 100
                if order_change > self.thresholds['order_change_percent']:
                    direction = "increase" if current['orders'] > previous['orders'] else "decrease"
                    anomalies.append({
                        'type': 'order_volume_anomaly',
                        'severity': 'medium',
                        'description': f"Order volume {direction} of {order_change:.1f}% detected",
                        'current_value': current['orders'],
                        'previous_value': previous['orders'],
                        'change_percent': order_change * (1 if direction == "increase" else -1)
                    })
            
            # Customer satisfaction threshold
            if 'customer_satisfaction' in current:
                if current['customer_satisfaction'] < self.thresholds['satisfaction_threshold']:
                    anomalies.append({
                        'type': 'satisfaction_anomaly',
                        'severity': 'high',
                        'description': f"Customer satisfaction below threshold: {current['customer_satisfaction']:.2f}",
                        'current_value': current['customer_satisfaction'],
                        'threshold': self.thresholds['satisfaction_threshold']
                    })
            
            # Growth rate threshold
            if 'monthly_growth' in current:
                if current['monthly_growth'] < self.thresholds['growth_rate_threshold']:
                    anomalies.append({
                        'type': 'growth_rate_anomaly',
                        'severity': 'critical',
                        'description': f"Negative growth rate detected: {current['monthly_growth']:.2%}",
                        'current_value': current['monthly_growth'],
                        'threshold': self.thresholds['growth_rate_threshold']
                    })
            
            # Publish anomalies
            for anomaly in anomalies:
                await self._publish_anomaly(anomaly)
                
        except Exception as e:
            logger.error(f"❌ Error detecting anomalies: {e}")
    
    async def _publish_anomaly(self, anomaly: Dict[str, Any]):
        """Publish anomaly detection event"""
        try:
            correlation_id = f"anomaly_{int(time.time())}"
            
            success = await publish_anomaly_detected(
                source_agent="continuous_monitoring",
                anomaly_data=anomaly,
                correlation_id=correlation_id
            )
            
            if success:
                logger.warning(f"🚨 ANOMALY DETECTED: {anomaly['description']} (correlation: {correlation_id})")
            else:
                logger.error("❌ Failed to publish anomaly event")
                
        except Exception as e:
            logger.error(f"❌ Error publishing anomaly: {e}")
    
    async def _update_cache(self, metrics: Dict[str, Any]):
        """Update Redis cache with current metrics"""
        try:
            if redis_cache_service.redis_client:
                # Store current metrics
                await redis_cache_service.set_json("current_metrics", metrics, ttl=300)
                
                # Store in time series for trends
                timestamp = int(time.time())
                await redis_cache_service.redis_client.zadd(
                    "metrics_timeseries",
                    {json.dumps(metrics): timestamp}
                )
                
                # Keep only last 1000 entries
                await redis_cache_service.redis_client.zremrangebyrank("metrics_timeseries", 0, -1001)
                
        except Exception as e:
            logger.error(f"❌ Error updating cache: {e}")
    
    async def _health_check_loop(self):
        """Monitor system health every 5 minutes"""
        while self.running:
            try:
                await asyncio.sleep(300)  # 5 minutes
                
                health_status = {
                    'monitoring_uptime': (datetime.utcnow() - self.monitoring_start_time).total_seconds(),
                    'last_metric_collection': self.last_metrics.get('collection_timestamp') if self.last_metrics else None,
                    'redis_connected': redis_cache_service.redis_client is not None,
                    'event_bus_connected': event_bus.redis_client is not None,
                    'data_processor_healthy': True  # Add actual health check
                }
                
                logger.info(f"💓 System health check: {health_status}")
                
            except Exception as e:
                logger.error(f"❌ Error in health check: {e}")
    
    async def _periodic_baseline_update(self):
        """Update baseline metrics every hour"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # 1 hour
                
                if self.last_metrics:
                    self.baseline_metrics = self.last_metrics.copy()
                    logger.info("📊 Updated baseline metrics for anomaly detection")
                    
            except Exception as e:
                logger.error(f"❌ Error updating baseline: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring service status"""
        return {
            'running': self.running,
            'poll_interval': self.poll_interval,
            'uptime_seconds': (
                datetime.utcnow() - self.monitoring_start_time
            ).total_seconds() if self.monitoring_start_time else 0,
            'last_metrics_timestamp': self.last_metrics.get('collection_timestamp') if self.last_metrics else None,
            'baseline_established': self.baseline_metrics is not None,
            'thresholds': self.thresholds
        }

# Global monitoring service instance
continuous_monitoring = ContinuousMonitoringService()