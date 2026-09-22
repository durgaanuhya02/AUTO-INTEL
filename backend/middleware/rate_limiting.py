"""
Rate limiting middleware for API endpoints
"""
import time
import uuid
from typing import Dict, Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
import redis.asyncio as redis
from ..core.config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_client: Optional[redis.Redis] = None):
        super().__init__(app)
        self.redis_client = redis_client
        self.rate_limits = {
            "/api/v1/dashboard": {"requests": 60, "window": 60},  # 60 requests per minute
            "/api/v1/metrics": {"requests": 120, "window": 60},   # 120 requests per minute
            "/api/v1/agents/trigger": {"requests": 10, "window": 60},  # 10 triggers per minute
            "/api/v1/approve-decision": {"requests": 30, "window": 60},  # 30 approvals per minute
        }
        self.default_limit = {"requests": 100, "window": 60}  # Default: 100 requests per minute

    async def _resolve_redis(self):
        """Middleware must be registered before startup, so Redis is resolved on first use."""
        if self.redis_client is None:
            try:
                from ..core.database import get_redis
                self.redis_client = await get_redis()
            except Exception:
                return None
        return self.redis_client

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and WebSocket connections
        if request.url.path in ["/health", "/ws"] or request.url.path.startswith("/docs"):
            return await call_next(request)

        await self._resolve_redis()

        client_ip = self._get_client_ip(request)
        endpoint = request.url.path

        # Get rate limit for this endpoint
        limit_config = self.rate_limits.get(endpoint, self.default_limit)

        # Check rate limit
        if await self._is_rate_limited(client_ip, endpoint, limit_config):
            # HTTPException raised inside middleware is not handled by FastAPI (it would surface
            # as a 500), so build the 429 response directly.
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": str(limit_config["window"])},
                content={"detail": {
                    "error": "Rate limit exceeded",
                    "limit": limit_config["requests"],
                    "window": limit_config["window"],
                    "retry_after": limit_config["window"]
                }}
            )

        response = await call_next(request)

        # Add rate limit headers
        remaining = await self._get_remaining_requests(client_ip, endpoint, limit_config)
        response.headers["X-RateLimit-Limit"] = str(limit_config["requests"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + limit_config["window"])

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def _is_rate_limited(self, client_ip: str, endpoint: str, limit_config: Dict) -> bool:
        """Check if client has exceeded rate limit"""
        if not self.redis_client:
            return False  # Skip rate limiting if Redis is not available

        key = f"rate_limit:{client_ip}:{endpoint}"
        current_time = time.time()
        window_start = current_time - limit_config["window"]
        # Members must be unique per request: keying on the timestamp alone collapses every
        # request within the same instant into one entry and the limit is never reached.
        member = f"{current_time}:{uuid.uuid4().hex}"

        try:
            # Sliding-window log, executed atomically so concurrent requests can't all slip under the limit
            pipe = self.redis_client.pipeline(transaction=True)
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {member: current_time})
            pipe.zcard(key)
            pipe.expire(key, limit_config["window"])
            _, _, current_requests, _ = await pipe.execute()

            return current_requests > limit_config["requests"]
        except Exception:
            # If Redis fails, allow the request
            return False

    async def _get_remaining_requests(self, client_ip: str, endpoint: str, limit_config: Dict) -> int:
        """Get remaining requests for client"""
        if not self.redis_client:
            return limit_config["requests"]

        key = f"rate_limit:{client_ip}:{endpoint}"

        try:
            current_requests = await self.redis_client.zcard(key)
            return max(0, limit_config["requests"] - current_requests)
        except Exception:
            return limit_config["requests"]