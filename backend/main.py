from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
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

# Add middleware (order matters! last added = outermost). Middleware can't be added once the
# app has started, so the rate limiter resolves its Redis client lazily on first request.
app.add_middleware(LoggingMiddleware)
app.add_middleware(SecurityMiddleware)
app.add_middleware(RateLimitMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"] if settings.environment == "development"
                  else ["https://yourdomain.com"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        connections = list(self.active_connections)
        if not connections:
            return
        message_str = json.dumps(message, default=str)

        async def send(connection):
            # A stalled client must not delay delivery to everyone else.
            await asyncio.wait_for(connection.send_text(message_str), timeout=SEND_TIMEOUT_SECONDS)

        results = await asyncio.gather(*(send(c) for c in connections), return_exceptions=True)
        for connection, result in zip(connections, results):
            if isinstance(result, Exception):
                self.disconnect(connection)

UNHEALTHY_STATUSES = {"unhealthy", "critical"}
SEND_TIMEOUT_SECONDS = 5.0
manager = ConnectionManager()
KNOWN_METRICS = {"revenue", "orders", "churn_risk", "delivery_delay", "customer_satisfaction"}


def _ws_error(code: str, detail: str = "") -> str:
    return json.dumps({"type": "error", "error": code, "detail": detail})

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text(_ws_error("invalid_json"))
                continue
            if not isinstance(message, dict):
                await websocket.send_text(_ws_error("invalid_message", "expected a JSON object"))
                continue

            message_type = message.get("type")
            if message_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()}))

            elif message_type == "trigger_analysis":
                metric_type = message.get("metric_type", "revenue")
                value = message.get("current_value", 1000)
                if metric_type not in KNOWN_METRICS:
                    await websocket.send_text(_ws_error("invalid_metric_type", str(metric_type)))
                    continue
                if isinstance(value, bool) or not isinstance(value, (int, float)) or value != value or abs(value) == float("inf"):
                    await websocket.send_text(_ws_error("invalid_current_value"))
                    continue
                try:
                    result = await orchestrator.trigger_manual_analysis(metric_type, float(value))
                except Exception as e:
                    logger.error(f"trigger_analysis failed: {e}")
                    await websocket.send_text(_ws_error("trigger_failed"))
                    continue
                await websocket.send_text(json.dumps({"type": "analysis_triggered", "result": result}))

            else:
                await websocket.send_text(_ws_error("unknown_message_type", str(message_type)))

    except WebSocketDisconnect:
        pass
    finally:
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

        overall = health_result["overall_status"]
        # Load balancers and `curl -f` health checks key off the HTTP status, not the body.
        return JSONResponse(
            status_code=503 if overall in UNHEALTHY_STATUSES else 200,
            content={
                "status": overall,
                "timestamp": datetime.utcnow().isoformat(),
                "health_checks": health_result["components"],
                "system_metrics": system_metrics,
                "alerts": alerts,
                "version": "1.0.0"
            }
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "critical",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

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
                    alert_data = json.loads(message["data"])
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

background_tasks: set = set()


def spawn_supervised(name: str, factory, restart_delay: float = 5.0):
    """Run `factory()` as a background task and restart it if it raises.

    Bare asyncio.create_task() tasks are garbage-collectable and die silently on the first
    unhandled exception (e.g. a Redis blip), which is fatal for a 24/7 service.
    """
    async def runner():
        while True:
            try:
                await factory()
                return  # returned normally: the service chose to stop
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(f"Background task '{name}' crashed; restarting in {restart_delay}s")
                await asyncio.sleep(restart_delay)

    task = asyncio.create_task(runner(), name=name)
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)
    return task


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

        # Start all services in the background, restarting any that crash
        spawn_supervised("orchestrator", orchestrator.start)
        spawn_supervised("real_time_ingestion", real_time_ingestion.start_real_time_ingestion)
        spawn_supervised("enterprise_sync", enterprise_integrations.start_enterprise_sync)
        spawn_supervised("analytics_engine", advanced_analytics.start_analytics_engine)
        spawn_supervised("broadcast_updates", broadcast_updates)
        spawn_supervised("system_health", monitor_system_health)

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
        for task in list(background_tasks):
            task.cancel()
        await asyncio.gather(*background_tasks, return_exceptions=True)
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