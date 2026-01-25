#!/usr/bin/env python3
"""
Continuous Monitoring Service - Always-On Background Worker
Monitors metrics 24/7 and publishes events for agent consumption
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dataclasses import dataclass
import json

from .event_bus import event_bus
from .real_data_processor import data_processor

logger = logging.getLogger(__name__)

@dataclass
class MetricThreshold:
    """Metric threshold configuration"""
    metric_name: str
    min_value: float = None
    max_value: float = None
    change_threshold: float = None  # Percentage change threshold
    time_window: int = 300  # 5 minutes default

class ContinuousMonitoringService:
    """24/7 monitoring service that feeds the agentic system"""
    
    def __init__(self, poll_interval: int = 30):
        self.poll_interval = poll_interval
        self.running = False
        self.last_metrics = {}
        self.metric_history = {}
        
        # Define monitoring thresholds
        self.thresholds = {
            'revenue': MetricThreshold(
                metric_name='revenue',
                change_threshold=10.0,  # 10% change triggers alert
                time_window=300
            ),
            'customer_satisfaction': MetricThreshold(
                metric_name='customer_satisfaction',
                min_value=3.5,  # Below 3.5 triggers alert
                max_value=5.0,
                change_threshold=5.0
            ),
            'order_volume': MetricThreshold(
                metric_name='order_volume',
                change_threshold=15.0,  # 15% change in orders
                time_window=300
            ),
            'delivery_performance': MetricThreshold(
                metric_name='delivery_performance',
                min_value=80.0,  # Below 80% on-time delivery
                change_threshold=5.0
            )
        }
    
    async def start_monitoring(self):
        """Start the continuous monitoring loop"""
        self.running = True
        logger.info("🔄 Starting continuous monitoring service...")
        
        while self.running:
            try:
                await self._collect_and_publish_metrics()
                await asyncio.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(5)  # Brief pause on error
    
    async def _collect_and_publish_metrics(self):
        """Collect current metrics and publish events"""
        try:
            # Get current business metrics
            current_metrics = data_processor.calculate_business_metrics()
            timestamp = datetime.now()
            
            # Prepare metric data
            metrics_data = {
                'revenue': current_metrics.total_revenue,
                'customer_satisfaction': current_metrics.customer_satisfaction,
                'order_volume': current_metrics.total_orders,
                'avg_order_value': current_metrics.avg_order_value,
                'monthly_growth': current_metrics.monthly_growth,
                'delivery_performance': current_metrics.delivery_performance.get('on_time_delivery_rate', 85.0)
            }
            
            # Store in history
            self._update_metric_history(timestamp, metrics_data)
            
            # Publish individual metric events
            for metric_name, value in metrics_data.items():
                await event_bus.publish_metric_update(
                    metric_name=metric_name,
                    value=value,
                    metadata={
                        'timestamp': timestamp.isoformat(),
                        'source': 'continuous_monitoring',
                        'previous_value': self.last_metrics.get(metric_name),
                        'change_detected': self._detect_significant_change(metric_name, value)
                    }
                )
            
            # Check for threshold violations
            await self._check_thresholds(metrics_data, timestamp)
            
            # Update last metrics
            self.last_metrics = metrics_data.copy()
            
            logger.info(f"📊 Published metrics update: Revenue=${metrics_data['revenue']:,.2f}, "
                       f"Satisfaction={metrics_data['customer_satisfaction']:.2f}, "
                       f"Orders={metrics_data['order_volume']:,}")
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}")
    
    def _update_metric_history(self, timestamp: datetime, metrics: Dict[str, float]):
        """Update metric history for trend analysis"""
        timestamp_key = timestamp.isoformat()
        
        for metric_name, value in metrics.items():
            if metric_name not in self.metric_history:
                self.metric_history[metric_name] = []
            
            self.metric_history[metric_name].append({
                'timestamp': timestamp_key,
                'value': value
            })
            
            # Keep only last 24 hours of data
            cutoff_time = timestamp - timedelta(hours=24)
            self.metric_history[metric_name] = [
                entry for entry in self.metric_history[metric_name]
                if datetime.fromisoformat(entry['timestamp']) > cutoff_time
            ]
    
    def _detect_significant_change(self, metric_name: str, current_value: float) -> bool:
        """Detect if metric has changed significantly"""
        if metric_name not in self.last_metrics:
            return False
        
        previous_value = self.last_metrics[metric_name]
        if previous_value == 0:
            return current_value != 0
        
        threshold = self.thresholds.get(metric_name)
        if not threshold or not threshold.change_threshold:
            return False
        
        change_percent = abs((current_value - previous_value) / previous_value) * 100
        return change_percent >= threshold.change_threshold
    
    async def _check_thresholds(self, metrics: Dict[str, float], timestamp: datetime):
        """Check metrics against defined thresholds and trigger alerts"""
        for metric_name, value in metrics.items():
            threshold = self.thresholds.get(metric_name)
            if not threshold:
                continue
            
            alert_triggered = False
            alert_message = ""
            severity = "medium"
            
            # Check minimum threshold
            if threshold.min_value is not None and value < threshold.min_value:
                alert_triggered = True
                alert_message = f"{metric_name} below minimum threshold: {value:.2f} < {threshold.min_value}"
                severity = "high"
            
            # Check maximum threshold
            elif threshold.max_value is not None and value > threshold.max_value:
                alert_triggered = True
                alert_message = f"{metric_name} above maximum threshold: {value:.2f} > {threshold.max_value}"
                severity = "high"
            
            # Check change threshold
            elif self._detect_significant_change(metric_name, value):
                previous_value = self.last_metrics.get(metric_name, 0)
                change_percent = ((value - previous_value) / previous_value) * 100 if previous_value != 0 else 0
                alert_triggered = True
                alert_message = f"{metric_name} significant change detected: {change_percent:+.1f}%"
                severity = "medium"
            
            # Publish alert if triggered
            if alert_triggered:
                await event_bus.publish_alert(
                    alert_type="threshold_violation",
                    severity=severity,
                    message=alert_message,
                    source_data={
                        'metric_name': metric_name,
                        'current_value': value,
                        'previous_value': self.last_metrics.get(metric_name),
                        'threshold': threshold.__dict__,
                        'timestamp': timestamp.isoformat()
                    }
                )
                
                logger.warning(f"🚨 Threshold alert: {alert_message}")
    
    async def get_metric_trends(self, metric_name: str, hours: int = 1) -> List[Dict[str, Any]]:
        """Get metric trends for specified time period"""
        if metric_name not in self.metric_history:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            entry for entry in self.metric_history[metric_name]
            if datetime.fromisoformat(entry['timestamp']) > cutoff_time
        ]
    
    def stop_monitoring(self):
        """Stop the monitoring service"""
        self.running = False
        logger.info("🛑 Stopping continuous monitoring service...")
    
    async def publish_system_health(self):
        """Publish system health metrics"""
        health_data = {
            'monitoring_active': self.running,
            'last_update': datetime.now().isoformat(),
            'metrics_tracked': len(self.last_metrics),
            'history_size': sum(len(history) for history in self.metric_history.values()),
            'thresholds_configured': len(self.thresholds)
        }
        
        await event_bus.publish_metric_update(
            metric_name='system_health',
            value=1.0 if self.running else 0.0,
            metadata=health_data
        )

# Global monitoring service instance
monitoring_service = ContinuousMonitoringService()