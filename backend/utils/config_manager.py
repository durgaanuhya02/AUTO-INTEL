"""
Configuration management utilities
"""
import json
from typing import Dict, Any, Optional
from datetime import datetime
import redis.asyncio as redis
from ..core.database import get_redis

class ConfigManager:
    """Centralized configuration management"""
    
    def __init__(self):
        self.config_cache = {}
        self.default_configs = {
            "agent_settings": {
                "update_interval": 30,
                "confidence_threshold": 0.7,
                "high_impact_threshold": 10000.0,
                "max_retries": 3,
                "timeout": 30,
            },
            "alert_thresholds": {
                "revenue": {"warning": 50000, "critical": 100000},
                "orders": {"warning": 100, "critical": 500},
                "churn_risk": {"warning": 0.15, "critical": 0.25},
                "customer_satisfaction": {"warning": 3.5, "critical": 3.0},
                "delivery_delay": {"warning": 3.0, "critical": 5.0},
            },
            "system_limits": {
                "max_alerts": 100,
                "max_decisions": 50,
                "max_history_points": 1000,
                "cache_ttl": 300,
            },
            "integration_settings": {
                "salesforce": {"enabled": True, "sync_interval": 300},
                "sap": {"enabled": True, "sync_interval": 600},
                "oracle": {"enabled": True, "sync_interval": 900},
                "dynamics365": {"enabled": False, "sync_interval": 300},
                "hubspot": {"enabled": False, "sync_interval": 300},
            },
            "security_settings": {
                "rate_limit_enabled": True,
                "api_key_required": False,
                "cors_origins": ["http://localhost:3000"],
                "session_timeout": 3600,
            }
        }
    
    async def get_config(self, config_key: str, default: Any = None) -> Any:
        """Get configuration value"""
        try:
            # Check cache first
            if config_key in self.config_cache:
                return self.config_cache[config_key]
            
            # Try Redis
            redis_client = await get_redis()
            config_data = await redis_client.get(f"config:{config_key}")
            
            if config_data:
                config_value = json.loads(config_data)
                self.config_cache[config_key] = config_value
                return config_value
            
            # Fall back to defaults
            if config_key in self.default_configs:
                return self.default_configs[config_key]
            
            return default
            
        except Exception:
            # Return default on any error
            return self.default_configs.get(config_key, default)
    
    async def set_config(self, config_key: str, config_value: Any, ttl: Optional[int] = None) -> bool:
        """Set configuration value"""
        try:
            redis_client = await get_redis()
            
            # Store in Redis
            if ttl:
                await redis_client.set(
                    f"config:{config_key}",
                    json.dumps(config_value, default=str),
                    ex=ttl
                )
            else:
                await redis_client.set(
                    f"config:{config_key}",
                    json.dumps(config_value, default=str)
                )
            
            # Update cache
            self.config_cache[config_key] = config_value
            
            # Log configuration change
            await self._log_config_change(config_key, config_value)
            
            return True
            
        except Exception:
            return False
    
    async def get_all_configs(self) -> Dict[str, Any]:
        """Get all configuration values"""
        all_configs = {}
        
        try:
            redis_client = await get_redis()
            
            # Get all config keys
            config_keys = await redis_client.keys("config:*")
            
            for key in config_keys:
                config_key = key.decode().replace("config:", "")
                config_data = await redis_client.get(key)
                if config_data:
                    all_configs[config_key] = json.loads(config_data)
            
            # Add defaults for missing configs
            for key, default_value in self.default_configs.items():
                if key not in all_configs:
                    all_configs[key] = default_value
            
            return all_configs
            
        except Exception:
            return self.default_configs.copy()
    
    async def reset_config(self, config_key: str) -> bool:
        """Reset configuration to default"""
        if config_key in self.default_configs:
            return await self.set_config(config_key, self.default_configs[config_key])
        return False
    
    async def validate_config(self, config_key: str, config_value: Any) -> bool:
        """Validate configuration value"""
        validators = {
            "agent_settings": self._validate_agent_settings,
            "alert_thresholds": self._validate_alert_thresholds,
            "system_limits": self._validate_system_limits,
            "integration_settings": self._validate_integration_settings,
            "security_settings": self._validate_security_settings,
        }
        
        validator = validators.get(config_key)
        if validator:
            return validator(config_value)
        
        return True  # Allow unknown configs
    
    def _validate_agent_settings(self, config: Dict[str, Any]) -> bool:
        """Validate agent settings"""
        required_fields = ["update_interval", "confidence_threshold", "high_impact_threshold"]
        
        if not all(field in config for field in required_fields):
            return False
        
        if not (1 <= config["update_interval"] <= 3600):
            return False
        
        if not (0.0 <= config["confidence_threshold"] <= 1.0):
            return False
        
        if not (0 <= config["high_impact_threshold"] <= 1000000):
            return False
        
        return True
    
    def _validate_alert_thresholds(self, config: Dict[str, Any]) -> bool:
        """Validate alert thresholds"""
        valid_metrics = ["revenue", "orders", "churn_risk", "customer_satisfaction", "delivery_delay"]
        
        for metric, thresholds in config.items():
            if metric not in valid_metrics:
                return False
            
            if not isinstance(thresholds, dict):
                return False
            
            if "warning" in thresholds and "critical" in thresholds:
                if not isinstance(thresholds["warning"], (int, float)):
                    return False
                if not isinstance(thresholds["critical"], (int, float)):
                    return False
        
        return True
    
    def _validate_system_limits(self, config: Dict[str, Any]) -> bool:
        """Validate system limits"""
        required_fields = ["max_alerts", "max_decisions", "max_history_points", "cache_ttl"]
        
        if not all(field in config for field in required_fields):
            return False
        
        for field in required_fields:
            if not isinstance(config[field], int) or config[field] < 0:
                return False
        
        return True
    
    def _validate_integration_settings(self, config: Dict[str, Any]) -> bool:
        """Validate integration settings"""
        valid_integrations = ["salesforce", "sap", "oracle", "dynamics365", "hubspot"]
        
        for integration, settings in config.items():
            if integration not in valid_integrations:
                return False
            
            if not isinstance(settings, dict):
                return False
            
            if "enabled" not in settings or not isinstance(settings["enabled"], bool):
                return False
            
            if "sync_interval" not in settings or not isinstance(settings["sync_interval"], int):
                return False
        
        return True
    
    def _validate_security_settings(self, config: Dict[str, Any]) -> bool:
        """Validate security settings"""
        required_fields = ["rate_limit_enabled", "api_key_required", "cors_origins", "session_timeout"]
        
        if not all(field in config for field in required_fields):
            return False
        
        if not isinstance(config["rate_limit_enabled"], bool):
            return False
        
        if not isinstance(config["api_key_required"], bool):
            return False
        
        if not isinstance(config["cors_origins"], list):
            return False
        
        if not isinstance(config["session_timeout"], int) or config["session_timeout"] < 60:
            return False
        
        return True
    
    async def _log_config_change(self, config_key: str, config_value: Any):
        """Log configuration changes"""
        try:
            redis_client = await get_redis()
            
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "config_key": config_key,
                "new_value": config_value,
                "source": "config_manager"
            }
            
            await redis_client.lpush(
                "config_changes",
                json.dumps(log_entry, default=str)
            )
            
            # Keep only last 100 changes
            await redis_client.ltrim("config_changes", 0, 99)
            
        except Exception:
            pass  # Don't fail on logging errors

# Global config manager instance
config_manager = ConfigManager()