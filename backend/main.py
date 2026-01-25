from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
import uvicorn

from .core.config import settings
from .core.database import get_redis
from .api.routes import router
from .middleware.rate_limiting import RateLimitMiddleware
from .middleware.security import SecurityMiddleware
from .middleware.logging import LoggingMiddleware
from .utils.monitoring import system_monitor, health_checker, alert_manager
from .utils.cache import cache_manager
from agents.agent_orchestrator import orchestrator
from .services.real_time_data_ingestion import real_time_ingestion
from .services.enterprise_integrations import enterprise_integrations
from .services.advanced_analytics import advanced_analytics

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Agentic AI Business Decision System",
    description="Autonomous AI system for business decision-making with enterprise-grade features",
    version="1.0.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
)

# Add middleware (order matters!)
app.add_middleware(LoggingMiddleware)
app.add_middleware(SecurityMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"] if settings.environment == "development" 
                  else ["https://yourdomain.com"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware (add after Redis is available)
@app.on_event("startup")
async def add_rate_limiting():
    redis_client = await get_redis()
    app.add_middleware(RateLimitMiddleware, redis_client=redis_client)

# Initialize ML service on startup
@app.on_event("startup")
async def initialize_ml_service():
    """Initialize ML service and load pre-trained models"""
    try:
        from .services.ml_service import MLService
        from .services.real_time_analytics_engine import RealTimeAnalyticsEngine

        # Initialize ML service (loads pre-trained models)
        global ml_service, analytics_engine
        ml_service = MLService()
        await ml_service.initialize()

        # Initialize analytics engine
        analytics_engine = RealTimeAnalyticsEngine()
        await analytics_engine.initialize()

        logger.info("✅ ML Service and Analytics Engine initialized")

    except Exception as e:
        logger.error(f"Failed to initialize ML services: {e}")
        # Continue without ML - system will use fallbacks

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        if self.active_connections:
            message_str = json.dumps(message, default=str)
            disconnected = []
            
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_str)
                except:
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.disconnect(connection)

manager = ConnectionManager()

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            
            # Handle client messages (like manual triggers)
            try:
                message = json.loads(data)
                if message.get("type") == "trigger_analysis":
                    result = await orchestrator.trigger_manual_analysis(
                        message.get("metric_type", "revenue"),
                        message.get("current_value", 1000)
                    )
                    await websocket.send_text(json.dumps({
                        "type": "analysis_triggered",
                        "result": result
                    }))
            except json.JSONDecodeError:
                pass
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/")
async def root():
    return {
        "message": "Agentic AI Business Decision System",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    try:
        # Run comprehensive health check
        health_result = await health_checker.run_comprehensive_health_check()
        
        # Get system metrics
        system_metrics = await system_monitor.get_system_metrics()
        
        # Check for system alerts
        alerts = await alert_manager.check_system_alerts(system_metrics)
        
        return {
            "status": health_result["overall_status"],
            "timestamp": datetime.utcnow().isoformat(),
            "health_checks": health_result["components"],
            "system_metrics": system_metrics,
            "alerts": alerts,
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "critical",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/metrics/system")
async def get_system_metrics():
    """Get detailed system performance metrics"""
    try:
        import psutil
        import time
        from datetime import datetime
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        # Calculate network latency (simplified)
        start_time = time.time()
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            network_latency = (time.time() - start_time) * 1000
        except:
            network_latency = 0
        
        # Get process info
        process = psutil.Process()
        process_memory = process.memory_info()
        
        # Calculate uptime
        boot_time = psutil.boot_time()
        uptime = time.time() - boot_time
        
        # Simulate some metrics
        active_connections = len(psutil.net_connections())
        requests_per_minute = 45  # This would come from actual request tracking
        error_rate = 0.5  # This would come from error tracking
        response_time = 150  # This would come from response time tracking
        
        metrics = {
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "disk_usage": disk.percent,
            "network_latency": network_latency,
            "response_time": response_time,
            "uptime": uptime,
            "active_connections": active_connections,
            "requests_per_minute": requests_per_minute,
            "error_rate": error_rate,
            "timestamp": datetime.utcnow().isoformat(),
            "memory_total": memory.total,
            "memory_available": memory.available,
            "disk_total": disk.total,
            "disk_free": disk.free,
            "network_bytes_sent": network.bytes_sent,
            "network_bytes_recv": network.bytes_recv
        }
        
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching system metrics: {str(e)}")

# Background task to broadcast updates
async def broadcast_updates():
    """Background task to broadcast real-time updates to WebSocket clients"""
    redis_client = await get_redis()
    
    # Subscribe to Redis channels for real-time updates
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("agent:broadcast", "alerts", "decisions")
    
    async for message in pubsub.listen():
        if message["type"] == "message":
            try:
                # Parse and broadcast the message
                if message["channel"] == b"agent:broadcast":
                    data = json.loads(message["data"])
                    await manager.broadcast({
                        "type": "agent_update",
                        "data": data,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif message["channel"] == b"alerts":
                    alert_data = eval(message["data"].decode())  # Safe in controlled environment
                    await manager.broadcast({
                        "type": "new_alert",
                        "data": alert_data,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif message["channel"] == b"decisions":
                    decision_data = json.loads(message["data"])
                    await manager.broadcast({
                        "type": "new_decision",
                        "data": decision_data,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
            except Exception as e:
                logger.error(f"Error broadcasting update: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize the system on startup"""
    logger.info("Starting Agentic AI Business Decision System...")
    
    try:
        # Initialize Redis and cache
        redis_client = await get_redis()
        await redis_client.ping()
        logger.info("Redis connection established")
        
        # Initialize cache manager
        cache_manager.redis_client = redis_client
        
        # Initialize the orchestrator
        await orchestrator.initialize()
        
        # Initialize enterprise services
        await real_time_ingestion.initialize()
        await enterprise_integrations.initialize()
        await advanced_analytics.initialize()
        
        # Start all services in the background
        asyncio.create_task(orchestrator.start())
        asyncio.create_task(real_time_ingestion.start_real_time_ingestion())
        asyncio.create_task(enterprise_integrations.start_enterprise_sync())
        asyncio.create_task(advanced_analytics.start_analytics_engine())
        
        # Start the broadcast task
        asyncio.create_task(broadcast_updates())
        
        # Start system monitoring
        asyncio.create_task(monitor_system_health())
        
        logger.info("System startup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to start system: {e}")
        raise

async def monitor_system_health():
    """Background task to monitor system health"""
    while True:
        try:
            # Get system metrics
            metrics = await system_monitor.get_system_metrics()
            
            # Check for alerts
            alerts = await alert_manager.check_system_alerts(metrics)
            
            # Log alerts
            for alert in alerts:
                logger.warning(f"System Alert: {alert['title']} - {alert['description']}")
            
            # Store metrics in Redis for monitoring dashboard
            redis_client = await get_redis()
            await redis_client.set(
                "system_metrics",
                json.dumps(metrics, default=str),
                ex=300  # 5 minutes
            )
            
            # Wait 60 seconds before next check
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"Error in system health monitoring: {e}")
            await asyncio.sleep(30)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Agentic AI Business Decision System...")
    
    try:
        await orchestrator.stop()
        await real_time_ingestion.stop()
        # Enterprise integrations and analytics will stop when main loop ends
        logger.info("System shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )