import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List, Optional
import aiohttp
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert

from ..core.database import AsyncSessionLocal, get_redis
from ..models.database_models import Metric
from ..models.schemas import MetricType, MetricCreate
from .data_processor import data_processor

class RealTimeDataIngestion:
    """
    Real-time data ingestion service for production environments.
    Supports multiple data sources: APIs, databases, message queues, webhooks.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("data_ingestion")
        self.redis_client = None
        self.running = False
        self.data_sources = {}
        self.ingestion_stats = {
            "total_records": 0,
            "successful_ingestions": 0,
            "failed_ingestions": 0,
            "last_ingestion": None
        }
    
    async def initialize(self):
        """Initialize the data ingestion service"""
        self.redis_client = await get_redis()
        await self._setup_data_sources()
        self.logger.info("Real-time data ingestion service initialized")
    
    async def _setup_data_sources(self):
        """Setup various data sources for real-time ingestion"""
        
        # E-commerce API endpoints (replace with actual endpoints)
        self.data_sources = {
            "shopify_api": {
                "url": "https://your-store.myshopify.com/admin/api/2023-10/orders.json",
                "headers": {"X-Shopify-Access-Token": "your_token"},
                "interval": 60,  # seconds
                "metric_mappings": {
                    "total_price": "revenue",
                    "order_count": "orders"
                }
            },
            "stripe_api": {
                "url": "https://api.stripe.com/v1/charges",
                "headers": {"Authorization": "Bearer your_stripe_key"},
                "interval": 30,
                "metric_mappings": {
                    "amount": "revenue"
                }
            },
            "google_analytics": {
                "url": "https://analyticsreporting.googleapis.com/v4/reports:batchGet",
                "headers": {"Authorization": "Bearer your_ga_token"},
                "interval": 300,  # 5 minutes
                "metric_mappings": {
                    "sessions": "website_traffic",
                    "bounceRate": "bounce_rate"
                }
            },
            "customer_support": {
                "url": "https://api.zendesk.com/api/v2/tickets.json",
                "headers": {"Authorization": "Bearer your_zendesk_token"},
                "interval": 120,
                "metric_mappings": {
                    "satisfaction_score": "customer_satisfaction"
                }
            }
        }
    
    async def start_real_time_ingestion(self):
        """Start real-time data ingestion from all sources"""
        if self.running:
            self.logger.warning("Data ingestion already running")
            return
        
        self.running = True
        self.logger.info("Starting real-time data ingestion...")
        
        # Start ingestion tasks for each data source
        tasks = []
        for source_name, config in self.data_sources.items():
            task = asyncio.create_task(self._ingest_from_source(source_name, config))
            tasks.append(task)
        
        # Start webhook server for push-based data
        webhook_task = asyncio.create_task(self._start_webhook_server())
        tasks.append(webhook_task)
        
        # Start database polling for existing systems
        db_polling_task = asyncio.create_task(self._poll_existing_databases())
        tasks.append(db_polling_task)
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Error in data ingestion: {e}")
        finally:
            self.running = False
    
    async def _ingest_from_source(self, source_name: str, config: Dict[str, Any]):
        """Ingest data from a specific source"""
        interval = config.get("interval", 60)
        
        while self.running:
            try:
                await self._fetch_and_process_data(source_name, config)
                await asyncio.sleep(interval)
            except Exception as e:
                self.logger.error(f"Error ingesting from {source_name}: {e}")
                await asyncio.sleep(interval * 2)  # Back off on error
    
    async def _fetch_and_process_data(self, source_name: str, config: Dict[str, Any]):
        """Fetch and process data from a source"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    config["url"],
                    headers=config.get("headers", {})
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        await self._process_source_data(source_name, data, config)
                        self.ingestion_stats["successful_ingestions"] += 1
                    else:
                        self.logger.warning(f"Failed to fetch from {source_name}: {response.status}")
                        self.ingestion_stats["failed_ingestions"] += 1
        
        except Exception as e:
            self.logger.error(f"Error fetching from {source_name}: {e}")
            self.ingestion_stats["failed_ingestions"] += 1
    
    async def _process_source_data(self, source_name: str, data: Dict[str, Any], config: Dict[str, Any]):
        """Process data from a specific source and convert to metrics"""
        metric_mappings = config.get("metric_mappings", {})
        metrics_to_store = []
        
        # Process based on source type
        if source_name == "shopify_api":
            metrics_to_store.extend(await self._process_shopify_data(data))
        elif source_name == "stripe_api":
            metrics_to_store.extend(await self._process_stripe_data(data))
        elif source_name == "google_analytics":
            metrics_to_store.extend(await self._process_ga_data(data))
        elif source_name == "customer_support":
            metrics_to_store.extend(await self._process_support_data(data))
        
        # Store metrics in database and Redis
        if metrics_to_store:
            await self._store_metrics(metrics_to_store)
            await self._publish_real_time_updates(metrics_to_store)
    
    async def _process_shopify_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process Shopify order data"""
        metrics = []
        orders = data.get("orders", [])
        
        if orders:
            # Calculate revenue
            total_revenue = sum(float(order.get("total_price", 0)) for order in orders)
            metrics.append({
                "metric_type": "revenue",
                "value": total_revenue,
                "timestamp": datetime.utcnow(),
                "metadata": {"source": "shopify", "order_count": len(orders)}
            })
            
            # Order count
            metrics.append({
                "metric_type": "orders",
                "value": len(orders),
                "timestamp": datetime.utcnow(),
                "metadata": {"source": "shopify"}
            })
            
            # Average order value
            avg_order_value = total_revenue / len(orders) if orders else 0
            metrics.append({
                "metric_type": "avg_order_value",
                "value": avg_order_value,
                "timestamp": datetime.utcnow(),
                "metadata": {"source": "shopify"}
            })
        
        return metrics
    
    async def _process_stripe_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process Stripe payment data"""
        metrics = []
        charges = data.get("data", [])
        
        if charges:
            # Calculate revenue from successful charges
            successful_charges = [c for c in charges if c.get("status") == "succeeded"]
            total_revenue = sum(c.get("amount", 0) / 100 for c in successful_charges)  # Convert from cents
            
            metrics.append({
                "metric_type": "revenue",
                "value": total_revenue,
                "timestamp": datetime.utcnow(),
                "metadata": {"source": "stripe", "charge_count": len(successful_charges)}
            })
        
        return metrics
    
    async def _process_ga_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process Google Analytics data"""
        metrics = []
        reports = data.get("reports", [])
        
        for report in reports:
            rows = report.get("data", {}).get("rows", [])
            for row in rows:
                dimensions = row.get("dimensions", [])
                metrics_data = row.get("metrics", [{}])[0].get("values", [])
                
                # Process specific metrics based on your GA setup
                if len(metrics_data) >= 2:
                    sessions = int(metrics_data[0])
                    bounce_rate = float(metrics_data[1])
                    
                    metrics.extend([
                        {
                            "metric_type": "website_traffic",
                            "value": sessions,
                            "timestamp": datetime.utcnow(),
                            "metadata": {"source": "google_analytics"}
                        },
                        {
                            "metric_type": "bounce_rate",
                            "value": bounce_rate / 100,  # Convert to decimal
                            "timestamp": datetime.utcnow(),
                            "metadata": {"source": "google_analytics"}
                        }
                    ])
        
        return metrics
    
    async def _process_support_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process customer support data"""
        metrics = []
        tickets = data.get("tickets", [])
        
        if tickets:
            # Calculate average satisfaction score
            satisfaction_scores = [
                t.get("satisfaction_rating", {}).get("score")
                for t in tickets
                if t.get("satisfaction_rating", {}).get("score") is not None
            ]
            
            if satisfaction_scores:
                avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores)
                metrics.append({
                    "metric_type": "customer_satisfaction",
                    "value": avg_satisfaction,
                    "timestamp": datetime.utcnow(),
                    "metadata": {"source": "zendesk", "ticket_count": len(tickets)}
                })
        
        return metrics
    
    async def _store_metrics(self, metrics: List[Dict[str, Any]]):
        """Store metrics in PostgreSQL database"""
        try:
            async with AsyncSessionLocal() as session:
                for metric_data in metrics:
                    metric = Metric(
                        metric_type=metric_data["metric_type"],
                        value=metric_data["value"],
                        timestamp=metric_data["timestamp"],
                        metadata=metric_data.get("metadata", {})
                    )
                    session.add(metric)
                
                await session.commit()
                self.ingestion_stats["total_records"] += len(metrics)
                self.ingestion_stats["last_ingestion"] = datetime.utcnow()
                
        except Exception as e:
            self.logger.error(f"Error storing metrics: {e}")
    
    async def _publish_real_time_updates(self, metrics: List[Dict[str, Any]]):
        """Publish real-time updates to Redis for immediate agent processing"""
        try:
            for metric_data in metrics:
                # Store current metric value
                await self.redis_client.set(
                    f"current_metric:{metric_data['metric_type']}",
                    json.dumps({
                        "value": metric_data["value"],
                        "timestamp": metric_data["timestamp"].isoformat(),
                        "metadata": metric_data.get("metadata", {})
                    }),
                    ex=3600  # Expire after 1 hour
                )
                
                # Publish to agents
                await self.redis_client.publish(
                    "metric_updates",
                    json.dumps({
                        "type": "metric_update",
                        "metric_type": metric_data["metric_type"],
                        "value": metric_data["value"],
                        "timestamp": metric_data["timestamp"].isoformat(),
                        "metadata": metric_data.get("metadata", {})
                    }, default=str)
                )
        
        except Exception as e:
            self.logger.error(f"Error publishing real-time updates: {e}")
    
    async def _start_webhook_server(self):
        """Start webhook server for push-based data ingestion"""
        # This would typically be integrated with your FastAPI app
        # For now, we'll simulate webhook data reception
        while self.running:
            try:
                # Simulate receiving webhook data
                await asyncio.sleep(30)
                
                # In production, this would handle actual webhook payloads
                # from services like Stripe, Shopify, etc.
                
            except Exception as e:
                self.logger.error(f"Error in webhook server: {e}")
    
    async def _poll_existing_databases(self):
        """Poll existing databases for new data"""
        while self.running:
            try:
                # Poll your existing business databases
                # This is where you'd connect to your current systems
                
                # Example: Poll order database
                await self._poll_order_database()
                
                # Example: Poll customer database
                await self._poll_customer_database()
                
                await asyncio.sleep(60)  # Poll every minute
                
            except Exception as e:
                self.logger.error(f"Error polling databases: {e}")
    
    async def _poll_order_database(self):
        """Poll order database for new orders"""
        # This would connect to your existing order database
        # and extract new orders since last poll
        
        # Simulated order data
        simulated_orders = await self._simulate_order_data()
        if simulated_orders:
            await self._process_source_data("order_db", simulated_orders, {
                "metric_mappings": {"total_price": "revenue", "order_count": "orders"}
            })
    
    async def _poll_customer_database(self):
        """Poll customer database for satisfaction updates"""
        # This would connect to your customer database
        # and extract satisfaction scores, churn indicators, etc.
        pass
    
    async def _simulate_order_data(self) -> Dict[str, Any]:
        """Simulate order data for demo purposes"""
        # In production, remove this and use actual data polling
        current_hour = datetime.utcnow().hour
        
        # Simulate realistic order patterns
        base_orders = 10
        if 9 <= current_hour <= 17:  # Business hours
            order_count = base_orders + np.random.poisson(5)
        elif 18 <= current_hour <= 22:  # Evening
            order_count = base_orders + np.random.poisson(3)
        else:  # Night
            order_count = base_orders + np.random.poisson(1)
        
        orders = []
        for i in range(order_count):
            order_value = np.random.normal(75, 25)  # Average $75 order
            orders.append({
                "total_price": max(10, order_value),  # Minimum $10
                "created_at": datetime.utcnow().isoformat()
            })
        
        return {"orders": orders}
    
    async def get_ingestion_stats(self) -> Dict[str, Any]:
        """Get data ingestion statistics"""
        return {
            **self.ingestion_stats,
            "running": self.running,
            "active_sources": len(self.data_sources),
            "last_ingestion": self.ingestion_stats["last_ingestion"].isoformat() if self.ingestion_stats["last_ingestion"] else None
        }
    
    async def stop(self):
        """Stop the data ingestion service"""
        self.running = False
        self.logger.info("Data ingestion service stopped")

# Global instance
real_time_ingestion = RealTimeDataIngestion()