"""
System monitoring and health check utilities
"""
import time
import psutil
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
import redis.asyncio as redis
from ..core.database import get_redis
from ..middleware.logging import PerformanceLogger

class SystemMonitor:
    """System performance monitoring"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.slow_requests = 0
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Network (if available)
        try:
            network = psutil.net_io_counters()
            network_stats = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv,
            }
        except:
            network_stats = {}
        
        # Application metrics
        uptime = time.time() - self.start_time
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": round(uptime, 2),
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free,
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100,
                },
                "network": network_stats,
            },
            "application": {
                "request_count": self.request_count,
                "error_count": self.error_count,
                "slow_requests": self.slow_requests,
                "error_rate": (self.error_count / max(self.request_count, 1)) * 100,
            }
        }
    
    def increment_request_count(self):
        """Increment request counter"""
        self.request_count += 1
    
    def increment_error_count(self):
        """Increment error counter"""
        self.error_count += 1
    
    def increment_slow_request_count(self):
        """Increment slow request counter"""
        self.slow_requests += 1

class HealthChecker:
    """Health check utilities"""
    
    def __init__(self):
        self.checks = {}
    
    async def check_redis_health(self) -> Dict[str, Any]:
        """Check Redis connection health"""
        try:
            redis_client = await get_redis()
            start_time = time.time()
            
            # Test basic operations
            await redis_client.ping()
            await redis_client.set("health_check", "ok", ex=10)
            value = await redis_client.get("health_check")
            await redis_client.delete("health_check")
            
            latency = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "operations": ["ping", "set", "get", "delete"],
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    async def check_agent_health(self) -> Dict[str, Any]:
        """Check agent system health"""
        try:
            redis_client = await get_redis()
            agent_names = ["observer", "analyst", "simulation", "decision", "governance"]
            
            agent_statuses = {}
            healthy_agents = 0
            
            for agent_name in agent_names:
                status_data = await redis_client.get(f"agent_status:{agent_name}")
                if status_data:
                    import json
                    status = json.loads(status_data)
                    agent_statuses[agent_name] = status
                    
                    # Check if agent is healthy (active and recent activity)
                    if status.get("status") == "active":
                        last_activity = datetime.fromisoformat(status.get("last_activity", "1970-01-01"))
                        if datetime.utcnow() - last_activity < timedelta(minutes=5):
                            healthy_agents += 1
                else:
                    agent_statuses[agent_name] = {"status": "unknown"}
            
            health_percentage = (healthy_agents / len(agent_names)) * 100
            overall_status = "healthy" if health_percentage >= 80 else "degraded" if health_percentage >= 50 else "unhealthy"
            
            return {
                "status": overall_status,
                "healthy_agents": healthy_agents,
                "total_agents": len(agent_names),
                "health_percentage": round(health_percentage, 1),
                "agents": agent_statuses,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    async def check_data_freshness(self) -> Dict[str, Any]:
        """Check if data is fresh and up-to-date"""
        try:
            redis_client = await get_redis()
            
            # Check when metrics were last updated
            metrics_timestamp = await redis_client.get("last_metric_update")
            if metrics_timestamp:
                last_update = datetime.fromisoformat(metrics_timestamp.decode())
                age_minutes = (datetime.utcnow() - last_update).total_seconds() / 60
                
                status = "healthy" if age_minutes < 5 else "stale" if age_minutes < 15 else "unhealthy"
            else:
                status = "unhealthy"
                age_minutes = float('inf')
            
            return {
                "status": status,
                "last_update": metrics_timestamp.decode() if metrics_timestamp else None,
                "age_minutes": round(age_minutes, 1) if age_minutes != float('inf') else None,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run all health checks"""
        checks = await asyncio.gather(
            self.check_redis_health(),
            self.check_agent_health(),
            self.check_data_freshness(),
            return_exceptions=True
        )
        
        redis_health, agent_health, data_health = checks
        
        # Determine overall health
        component_statuses = [
            redis_health.get("status", "unhealthy"),
            agent_health.get("status", "unhealthy"),
            data_health.get("status", "unhealthy"),
        ]
        
        if all(status == "healthy" for status in component_statuses):
            overall_status = "healthy"
        elif any(status == "unhealthy" for status in component_statuses):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"
        
        return {
            "overall_status": overall_status,
            "components": {
                "redis": redis_health,
                "agents": agent_health,
                "data": data_health,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

class AlertManager:
    """System alert management"""
    
    def __init__(self):
        self.alert_thresholds = {
            "cpu_percent": 80,
            "memory_percent": 85,
            "disk_percent": 90,
            "error_rate": 5,  # percentage
            "response_time": 2000,  # milliseconds
        }
    
    async def check_system_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for system alerts based on metrics"""
        alerts = []
        
        # CPU alert
        cpu_percent = metrics.get("system", {}).get("cpu_percent", 0)
        if cpu_percent > self.alert_thresholds["cpu_percent"]:
            alerts.append({
                "type": "system_alert",
                "severity": "high" if cpu_percent > 90 else "medium",
                "title": "High CPU Usage",
                "description": f"CPU usage is {cpu_percent}%",
                "metric": "cpu_percent",
                "value": cpu_percent,
                "threshold": self.alert_thresholds["cpu_percent"],
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        # Memory alert
        memory_percent = metrics.get("system", {}).get("memory", {}).get("percent", 0)
        if memory_percent > self.alert_thresholds["memory_percent"]:
            alerts.append({
                "type": "system_alert",
                "severity": "high" if memory_percent > 95 else "medium",
                "title": "High Memory Usage",
                "description": f"Memory usage is {memory_percent}%",
                "metric": "memory_percent",
                "value": memory_percent,
                "threshold": self.alert_thresholds["memory_percent"],
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        # Disk alert
        disk_percent = metrics.get("system", {}).get("disk", {}).get("percent", 0)
        if disk_percent > self.alert_thresholds["disk_percent"]:
            alerts.append({
                "type": "system_alert",
                "severity": "critical" if disk_percent > 95 else "high",
                "title": "Low Disk Space",
                "description": f"Disk usage is {disk_percent}%",
                "metric": "disk_percent",
                "value": disk_percent,
                "threshold": self.alert_thresholds["disk_percent"],
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        # Error rate alert
        error_rate = metrics.get("application", {}).get("error_rate", 0)
        if error_rate > self.alert_thresholds["error_rate"]:
            alerts.append({
                "type": "application_alert",
                "severity": "high" if error_rate > 10 else "medium",
                "title": "High Error Rate",
                "description": f"Error rate is {error_rate}%",
                "metric": "error_rate",
                "value": error_rate,
                "threshold": self.alert_thresholds["error_rate"],
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        return alerts

# Global instances
system_monitor = SystemMonitor()
health_checker = HealthChecker()
alert_manager = AlertManager()