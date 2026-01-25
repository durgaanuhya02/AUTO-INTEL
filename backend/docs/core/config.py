from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    database_url: str = "postgresql://user:password@localhost:5432/agentic_ai"
    redis_url: str = "redis://localhost:6379"
    openai_api_key: Optional[str] = None
    secret_key: str = "your-secret-key-change-in-production"
    environment: str = "development"
    log_level: str = "INFO"
    
    # Agent settings
    agent_update_interval: int = 30  # seconds
    confidence_threshold: float = 0.7
    high_impact_threshold: float = 10000.0  # USD
    
    # WebSocket settings
    websocket_heartbeat: int = 30
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra fields in .env

settings = Settings()