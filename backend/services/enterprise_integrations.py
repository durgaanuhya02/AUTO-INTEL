import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import AsyncSessionLocal, get_redis
from ..core.config import settings

class EnterpriseIntegrations:
    """
    Enterprise-grade integrations for real-world business systems.
    Supports major platforms: Salesforce, SAP, Oracle, Microsoft Dynamics, etc.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("enterprise_integrations")
        self.redis_client = None
        self.integrations = {}
        self.active_connections = {}
    
    async def initialize(self):
        """Initialize enterprise integrations"""
        self.redis_client = await get_redis()
        await self._setup_integrations()
        self.logger.info("Enterprise integrations initialized")
    
    async def _setup_integrations(self):
        """Setup enterprise system integrations"""
        self.integrations = {
            "salesforce": {
                "enabled": True,
                "base_url": "https://your-domain.salesforce.com",
                "auth_type": "oauth2",
                "endpoints": {
                    "opportunities": "/services/data/v58.0/query/?q=SELECT+Id,Amount,StageName,CloseDate+FROM+Opportunity",
                    "accounts": "/services/data/v58.0/query/?q=SELECT+Id,Name,AnnualRevenue+FROM+Account",
                    "leads": "/services/data/v58.0/query/?q=SELECT+Id,Status,Rating+FROM+Lead"
                }
            },
            "sap": {
                "enabled": True,
                "base_url": "https://your-sap-system.com:8000",
                "auth_type": "basic",
                "endpoints": {
                    "sales_orders": "/sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrder",
                    "customers": "/sap/opu/odata/sap/API_BUSINESS_PARTNER/A_Customer",
                    "materials": "/sap/opu/odata/sap/API_MATERIAL_SRV/A_Product"
                }
            },
            "dynamics365": {
                "enabled": True,
                "base_url": "https://your-org.crm.dynamics.com",
                "auth_type": "oauth2",
                "endpoints": {
                    "opportunities": "/api/data/v9.2/opportunities",
                    "accounts": "/api/data/v9.2/accounts",
                    "contacts": "/api/data/v9.2/contacts"
                }
            },
            "oracle_erp": {
                "enabled": True,
                "base_url": "https://your-oracle-cloud.oraclecloud.com",
                "auth_type": "oauth2",
                "endpoints": {
                    "invoices": "/fscmRestApi/resources/11.13.18.05/receivablesInvoices",
                    "customers": "/fscmRestApi/resources/11.13.18.05/customers",
                    "orders": "/fscmRestApi/resources/11.13.18.05/orders"
                }
            },
            "hubspot": {
                "enabled": True,
                "base_url": "https://api.hubapi.com",
                "auth_type": "api_key",
                "endpoints": {
                    "deals": "/crm/v3/objects/deals",
                    "companies": "/crm/v3/objects/companies",
                    "contacts": "/crm/v3/objects/contacts"
                }
            }
        }
    
    async def start_enterprise_sync(self):
        """Start syncing data from all enterprise systems"""
        self.logger.info("Starting enterprise data synchronization...")
        
        tasks = []
        for system_name, config in self.integrations.items():
            if config.get("enabled", False):
                task = asyncio.create_task(self._sync_system_data(system_name, config))
                tasks.append(task)
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Error in enterprise sync: {e}")
    
    async def _sync_system_data(self, system_name: str, config: Dict[str, Any]):
        """Sync data from a specific enterprise system"""
        sync_interval = 300  # 5 minutes for enterprise systems
        
        while True:
            try:
                await self._fetch_system_data(system_name, config)
                await asyncio.sleep(sync_interval)
            except Exception as e:
                self.logger.error(f"Error syncing {system_name}: {e}")
                await asyncio.sleep(sync_interval * 2)
    
    async def _fetch_system_data(self, system_name: str, config: Dict[str, Any]):
        """Fetch data from enterprise system"""
        auth_headers = await self._get_auth_headers(system_name, config)
        
        for endpoint_name, endpoint_url in config["endpoints"].items():
            try:
                full_url = config["base_url"] + endpoint_url
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(full_url, headers=auth_headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            await self._process_enterprise_data(system_name, endpoint_name, data)
                        else:
                            self.logger.warning(f"Failed to fetch {system_name}/{endpoint_name}: {response.status}")
            
            except Exception as e:
                self.logger.error(f"Error fetching {system_name}/{endpoint_name}: {e}")
    
    async def _get_auth_headers(self, system_name: str, config: Dict[str, Any]) -> Dict[str, str]:
        """Get authentication headers for enterprise system"""
        auth_type = config.get("auth_type", "api_key")
        
        if auth_type == "oauth2":
            # In production, implement proper OAuth2 flow
            token = await self._get_oauth_token(system_name)
            return {"Authorization": f"Bearer {token}"}
        
        elif auth_type == "basic":
            # In production, use secure credential storage
            return {"Authorization": "Basic your_encoded_credentials"}
        
        elif auth_type == "api_key":
            # In production, use secure API key storage
            return {"Authorization": f"Bearer your_api_key"}
        
        return {}
    
    async def _get_oauth_token(self, system_name: str) -> str:
        """Get OAuth token for system (implement proper OAuth flow)"""
        # In production, implement proper OAuth2 token management
        # with refresh tokens, token caching, etc.
        cached_token = await self.redis_client.get(f"oauth_token:{system_name}")
        
        if cached_token:
            return cached_token.decode()
        
        # Implement OAuth token refresh logic here
        return "your_oauth_token"
    
    async def _process_enterprise_data(self, system_name: str, endpoint_name: str, data: Dict[str, Any]):
        """Process data from enterprise systems and convert to business metrics"""
        
        if system_name == "salesforce":
            await self._process_salesforce_data(endpoint_name, data)
        elif system_name == "sap":
            await self._process_sap_data(endpoint_name, data)
        elif system_name == "dynamics365":
            await self._process_dynamics_data(endpoint_name, data)
        elif system_name == "oracle_erp":
            await self._process_oracle_data(endpoint_name, data)
        elif system_name == "hubspot":
            await self._process_hubspot_data(endpoint_name, data)
    
    async def _process_salesforce_data(self, endpoint_name: str, data: Dict[str, Any]):
        """Process Salesforce data"""
        records = data.get("records", [])
        
        if endpoint_name == "opportunities" and records:
            # Calculate pipeline metrics
            total_pipeline = sum(float(r.get("Amount", 0)) for r in records if r.get("Amount"))
            won_opportunities = [r for r in records if r.get("StageName") == "Closed Won"]
            won_revenue = sum(float(r.get("Amount", 0)) for r in won_opportunities)
            
            metrics = [
                {
                    "metric_type": "sales_pipeline",
                    "value": total_pipeline,
                    "timestamp": datetime.utcnow(),
                    "metadata": {"source": "salesforce", "opportunity_count": len(records)}
                },
                {
                    "metric_type": "won_revenue",
                    "value": won_revenue,
                    "timestamp": datetime.utcnow(),
                    "metadata": {"source": "salesforce", "won_count": len(won_opportunities)}
                }
            ]
            
            await self._store_enterprise_metrics(metrics)
    
    async def _process_sap_data(self, endpoint_name: str, data: Dict[str, Any]):
        """Process SAP data"""
        if endpoint_name == "sales_orders":
            orders = data.get("d", {}).get("results", [])
            
            if orders:
                total_order_value = sum(float(order.get("NetAmount", 0)) for order in orders)
                
                metrics = [
                    {
                        "metric_type": "sap_orders_value",
                        "value": total_order_value,
                        "timestamp": datetime.utcnow(),
                        "metadata": {"source": "sap", "order_count": len(orders)}
                    }
                ]
                
                await self._store_enterprise_metrics(metrics)
    
    async def _process_dynamics_data(self, endpoint_name: str, data: Dict[str, Any]):
        """Process Microsoft Dynamics 365 data"""
        records = data.get("value", [])
        
        if endpoint_name == "opportunities" and records:
            total_revenue = sum(float(r.get("estimatedvalue", 0)) for r in records if r.get("estimatedvalue"))
            
            metrics = [
                {
                    "metric_type": "dynamics_pipeline",
                    "value": total_revenue,
                    "timestamp": datetime.utcnow(),
                    "metadata": {"source": "dynamics365", "opportunity_count": len(records)}
                }
            ]
            
            await self._store_enterprise_metrics(metrics)
    
    async def _process_oracle_data(self, endpoint_name: str, data: Dict[str, Any]):
        """Process Oracle ERP data"""
        items = data.get("items", [])
        
        if endpoint_name == "invoices" and items:
            total_invoice_amount = sum(float(item.get("InvoiceAmount", 0)) for item in items)
            
            metrics = [
                {
                    "metric_type": "oracle_invoices",
                    "value": total_invoice_amount,
                    "timestamp": datetime.utcnow(),
                    "metadata": {"source": "oracle_erp", "invoice_count": len(items)}
                }
            ]
            
            await self._store_enterprise_metrics(metrics)
    
    async def _process_hubspot_data(self, endpoint_name: str, data: Dict[str, Any]):
        """Process HubSpot data"""
        results = data.get("results", [])
        
        if endpoint_name == "deals" and results:
            total_deal_value = sum(float(r.get("properties", {}).get("amount", 0)) for r in results)
            
            metrics = [
                {
                    "metric_type": "hubspot_deals",
                    "value": total_deal_value,
                    "timestamp": datetime.utcnow(),
                    "metadata": {"source": "hubspot", "deal_count": len(results)}
                }
            ]
            
            await self._store_enterprise_metrics(metrics)
    
    async def _store_enterprise_metrics(self, metrics: List[Dict[str, Any]]):
        """Store enterprise metrics and trigger agent processing"""
        try:
            # Store in database
            from ..models.database_models import Metric
            
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
            
            # Publish to Redis for real-time processing
            for metric_data in metrics:
                await self.redis_client.publish(
                    "enterprise_metrics",
                    json.dumps({
                        "type": "enterprise_metric",
                        "metric_type": metric_data["metric_type"],
                        "value": metric_data["value"],
                        "timestamp": metric_data["timestamp"].isoformat(),
                        "metadata": metric_data.get("metadata", {})
                    }, default=str)
                )
            
            self.logger.info(f"Stored {len(metrics)} enterprise metrics")
            
        except Exception as e:
            self.logger.error(f"Error storing enterprise metrics: {e}")
    
    async def setup_custom_integration(self, integration_config: Dict[str, Any]):
        """Setup a custom enterprise integration"""
        system_name = integration_config.get("name")
        
        if not system_name:
            raise ValueError("Integration name is required")
        
        self.integrations[system_name] = integration_config
        
        # Start syncing from the new integration
        if integration_config.get("enabled", False):
            asyncio.create_task(self._sync_system_data(system_name, integration_config))
        
        self.logger.info(f"Custom integration '{system_name}' setup complete")
    
    async def get_integration_status(self) -> Dict[str, Any]:
        """Get status of all enterprise integrations"""
        status = {}
        
        for system_name, config in self.integrations.items():
            # Check if system is reachable
            try:
                auth_headers = await self._get_auth_headers(system_name, config)
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        config["base_url"],
                        headers=auth_headers,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        status[system_name] = {
                            "enabled": config.get("enabled", False),
                            "status": "connected" if response.status < 400 else "error",
                            "last_check": datetime.utcnow().isoformat()
                        }
            except Exception as e:
                status[system_name] = {
                    "enabled": config.get("enabled", False),
                    "status": "disconnected",
                    "error": str(e),
                    "last_check": datetime.utcnow().isoformat()
                }
        
        return status

# Global instance
enterprise_integrations = EnterpriseIntegrations()