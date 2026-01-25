"""
Enhanced logging middleware with request tracking
"""
import time
import uuid
import json
import logging
from typing import Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("api_requests")

class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request
        await self._log_request(request, request_id)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            await self._log_response(request, response, request_id, duration)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            await self._log_error(request, e, request_id, duration)
            raise

    async def _log_request(self, request: Request, request_id: str):
        """Log incoming request"""
        client_ip = self._get_client_ip(request)
        
        log_data = {
            "event": "request_started",
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent", ""),
            "content_type": request.headers.get("content-type", ""),
            "content_length": request.headers.get("content-length", 0),
        }
        
        logger.info(json.dumps(log_data))

    async def _log_response(self, request: Request, response: Response, request_id: str, duration: float):
        """Log response"""
        client_ip = self._get_client_ip(request)
        
        log_data = {
            "event": "request_completed",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": client_ip,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "response_size": len(response.body) if hasattr(response, 'body') else 0,
        }
        
        # Log level based on status code
        if response.status_code >= 500:
            logger.error(json.dumps(log_data))
        elif response.status_code >= 400:
            logger.warning(json.dumps(log_data))
        else:
            logger.info(json.dumps(log_data))

    async def _log_error(self, request: Request, error: Exception, request_id: str, duration: float):
        """Log error"""
        client_ip = self._get_client_ip(request)
        
        log_data = {
            "event": "request_error",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": client_ip,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "duration_ms": round(duration * 1000, 2),
        }
        
        logger.error(json.dumps(log_data))

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

class PerformanceLogger:
    """Performance monitoring and logging"""
    
    @staticmethod
    def log_slow_query(query_name: str, duration: float, threshold: float = 1.0):
        """Log slow database queries"""
        if duration > threshold:
            log_data = {
                "event": "slow_query",
                "query_name": query_name,
                "duration_ms": round(duration * 1000, 2),
                "threshold_ms": round(threshold * 1000, 2),
            }
            logger.warning(json.dumps(log_data))
    
    @staticmethod
    def log_agent_performance(agent_name: str, task: str, duration: float, success: bool):
        """Log agent performance metrics"""
        log_data = {
            "event": "agent_performance",
            "agent_name": agent_name,
            "task": task,
            "duration_ms": round(duration * 1000, 2),
            "success": success,
        }
        logger.info(json.dumps(log_data))
    
    @staticmethod
    def log_system_metrics(metrics: Dict[str, Any]):
        """Log system performance metrics"""
        log_data = {
            "event": "system_metrics",
            **metrics
        }
        logger.info(json.dumps(log_data))