"""
Input validation utilities
"""
import re
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, validator, ValidationError

class MetricValidation:
    """Validation utilities for metrics"""
    
    @staticmethod
    def validate_metric_value(value: float, metric_type: str) -> bool:
        """Validate metric value based on type"""
        if not isinstance(value, (int, float)):
            return False
        
        # Type-specific validation
        if metric_type == "revenue" and value < 0:
            return False
        elif metric_type == "orders" and (value < 0 or value != int(value)):
            return False
        elif metric_type == "churn_risk" and not (0 <= value <= 1):
            return False
        elif metric_type == "customer_satisfaction" and not (0 <= value <= 5):
            return False
        elif metric_type == "delivery_delay" and value < 0:
            return False
        
        return True
    
    @staticmethod
    def validate_timestamp(timestamp: datetime) -> bool:
        """Validate timestamp is reasonable"""
        now = datetime.utcnow()
        # Allow timestamps from 1 year ago to 1 hour in the future
        min_time = now - timedelta(days=365)
        max_time = now + timedelta(hours=1)
        
        return min_time <= timestamp <= max_time

class DecisionValidation:
    """Validation utilities for decisions"""
    
    @staticmethod
    def validate_confidence_score(score: float) -> bool:
        """Validate confidence score is between 0 and 1"""
        return isinstance(score, (int, float)) and 0 <= score <= 1
    
    @staticmethod
    def validate_financial_impact(impact: float) -> bool:
        """Validate financial impact is reasonable"""
        # Allow negative (costs) and positive (revenue) impacts
        # But limit to reasonable range
        return isinstance(impact, (int, float)) and -1_000_000 <= impact <= 1_000_000
    
    @staticmethod
    def validate_scenario(scenario: Dict[str, Any]) -> bool:
        """Validate decision scenario structure"""
        required_fields = ["name", "description", "confidence_score", "risk_score"]
        
        if not all(field in scenario for field in required_fields):
            return False
        
        if not DecisionValidation.validate_confidence_score(scenario["confidence_score"]):
            return False
        
        if not DecisionValidation.validate_confidence_score(scenario["risk_score"]):
            return False
        
        return True

class AlertValidation:
    """Validation utilities for alerts"""
    
    VALID_SEVERITIES = ["low", "medium", "high", "critical"]
    VALID_METRIC_TYPES = ["revenue", "orders", "churn_risk", "delivery_delay", "customer_satisfaction"]
    VALID_AGENT_TYPES = ["observer", "analyst", "simulation", "decision", "governance"]
    
    @staticmethod
    def validate_severity(severity: str) -> bool:
        """Validate alert severity"""
        return severity.lower() in AlertValidation.VALID_SEVERITIES
    
    @staticmethod
    def validate_metric_type(metric_type: str) -> bool:
        """Validate metric type"""
        return metric_type.lower() in AlertValidation.VALID_METRIC_TYPES
    
    @staticmethod
    def validate_agent_type(agent_type: str) -> bool:
        """Validate agent type"""
        return agent_type.lower() in AlertValidation.VALID_AGENT_TYPES

class InputSanitizer:
    """Input sanitization utilities"""
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if not isinstance(input_str, str):
            return ""
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', input_str)
        
        # Limit length
        sanitized = sanitized[:max_length]
        
        # Strip whitespace
        return sanitized.strip()
    
    @staticmethod
    def sanitize_dict(input_dict: Dict[str, Any], max_depth: int = 3) -> Dict[str, Any]:
        """Sanitize dictionary input"""
        if not isinstance(input_dict, dict) or max_depth <= 0:
            return {}
        
        sanitized = {}
        for key, value in input_dict.items():
            # Sanitize key
            clean_key = InputSanitizer.sanitize_string(str(key), 100)
            if not clean_key:
                continue
            
            # Sanitize value based on type
            if isinstance(value, str):
                sanitized[clean_key] = InputSanitizer.sanitize_string(value)
            elif isinstance(value, (int, float, bool)):
                sanitized[clean_key] = value
            elif isinstance(value, dict):
                sanitized[clean_key] = InputSanitizer.sanitize_dict(value, max_depth - 1)
            elif isinstance(value, list):
                sanitized[clean_key] = [
                    InputSanitizer.sanitize_string(str(item)) if isinstance(item, str) else item
                    for item in value[:100]  # Limit list size
                    if isinstance(item, (str, int, float, bool))
                ]
        
        return sanitized

class BusinessRuleValidator:
    """Business rule validation"""
    
    @staticmethod
    def validate_approval_threshold(financial_impact: float, confidence_score: float) -> bool:
        """Validate if decision requires approval based on business rules"""
        # High impact decisions always require approval
        if abs(financial_impact) > 10000:
            return True
        
        # Low confidence decisions require approval
        if confidence_score < 0.7:
            return True
        
        # Medium impact with medium confidence requires approval
        if abs(financial_impact) > 5000 and confidence_score < 0.8:
            return True
        
        return False
    
    @staticmethod
    def validate_metric_thresholds(metric_type: str, value: float) -> Optional[str]:
        """Validate if metric value exceeds business thresholds"""
        thresholds = {
            "revenue": {"min": 0, "warning": 50000, "critical": 100000},
            "orders": {"min": 0, "warning": 100, "critical": 500},
            "churn_risk": {"min": 0, "max": 1, "warning": 0.15, "critical": 0.25},
            "customer_satisfaction": {"min": 0, "max": 5, "warning": 3.5, "critical": 3.0},
            "delivery_delay": {"min": 0, "warning": 3.0, "critical": 5.0},
        }
        
        if metric_type not in thresholds:
            return None
        
        threshold = thresholds[metric_type]
        
        # Check bounds
        if "min" in threshold and value < threshold["min"]:
            return "critical"
        if "max" in threshold and value > threshold["max"]:
            return "critical"
        
        # Check warning/critical levels
        if metric_type in ["revenue", "orders"]:
            # Higher is better
            if value < threshold["critical"]:
                return "critical"
            elif value < threshold["warning"]:
                return "warning"
        else:
            # Lower is better
            if value > threshold["critical"]:
                return "critical"
            elif value > threshold["warning"]:
                return "warning"
        
        return None