"""
Security middleware for the API
"""
import secrets
import hashlib
from typing import Optional
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.config import settings

security = HTTPBearer(auto_error=False)

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.api_keys = self._load_api_keys()

    def _load_api_keys(self):
        """Load API keys from environment or config"""
        # In production, load from secure storage
        return {
            "demo_key": hashlib.sha256("demo_api_key".encode()).hexdigest(),
            "admin_key": hashlib.sha256("admin_api_key".encode()).hexdigest(),
        }

    async def dispatch(self, request: Request, call_next):
        # Skip security for health checks and docs
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Skip security for WebSocket (handled separately)
        if request.url.path == "/ws":
            return await call_next(request)

        # Add security headers
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response

async def verify_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Verify API key for protected endpoints"""
    # For demo purposes, we'll be lenient
    # In production, implement proper API key validation
    if settings.environment == "development":
        return True
    
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validate API key
    provided_key = hashlib.sha256(credentials.credentials.encode()).hexdigest()
    
    # In production, check against database or secure storage
    valid_keys = [
        hashlib.sha256("demo_api_key".encode()).hexdigest(),
        hashlib.sha256("admin_api_key".encode()).hexdigest(),
    ]
    
    if provided_key not in valid_keys:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return True

def generate_api_key() -> str:
    """Generate a new API key"""
    return secrets.token_urlsafe(32)