"""
Enhanced security utilities for the enterprise system
"""
import hashlib
import secrets
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SecurityValidator:
    """Enhanced security validation utilities"""
    
    # File upload security
    ALLOWED_FILE_EXTENSIONS = {'.csv', '.xlsx', '.xls', '.json'}
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    
    # Input validation patterns
    PATTERNS = {
        'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        'alphanumeric': re.compile(r'^[a-zA-Z0-9_-]+$'),
        'safe_filename': re.compile(r'^[a-zA-Z0-9._-]+$'),
        'sql_injection': re.compile(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)', re.IGNORECASE),
        'xss': re.compile(r'<script|javascript:|on\w+\s*=', re.IGNORECASE)
    }
    
    @classmethod
    def validate_file_upload(cls, filename: str, file_size: int, content_type: str = None) -> Dict[str, Any]:
        """Validate file upload security"""
        errors = []
        
        # Check file extension
        if not any(filename.lower().endswith(ext) for ext in cls.ALLOWED_FILE_EXTENSIONS):
            errors.append(f"File type not allowed. Allowed types: {', '.join(cls.ALLOWED_FILE_EXTENSIONS)}")
        
        # Check file size
        if file_size > cls.MAX_FILE_SIZE:
            errors.append(f"File too large. Maximum size: {cls.MAX_FILE_SIZE // (1024*1024)}MB")
        
        # Check filename for security
        if not cls.PATTERNS['safe_filename'].match(filename):
            errors.append("Filename contains invalid characters")
        
        # Check for suspicious patterns in filename
        suspicious_patterns = ['../', '..\\', '<', '>', '|', '&', ';']
        if any(pattern in filename for pattern in suspicious_patterns):
            errors.append("Filename contains suspicious patterns")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'sanitized_filename': cls.sanitize_filename(filename)
        }
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove path components
        filename = filename.split('/')[-1].split('\\')[-1]
        
        # Replace unsafe characters
        filename = re.sub(r'[^\w\.-]', '_', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:250] + ('.' + ext if ext else '')
        
        return filename
    
    @classmethod
    def validate_input(cls, data: Any, field_name: str, validation_type: str) -> Dict[str, Any]:
        """Validate input data against patterns"""
        if not isinstance(data, str):
            return {'valid': False, 'error': f'{field_name} must be a string'}
        
        if validation_type not in cls.PATTERNS:
            return {'valid': False, 'error': f'Unknown validation type: {validation_type}'}
        
        pattern = cls.PATTERNS[validation_type]
        
        if validation_type in ['sql_injection', 'xss']:
            # These are negative patterns (should NOT match)
            if pattern.search(data):
                return {'valid': False, 'error': f'{field_name} contains potentially malicious content'}
        else:
            # These are positive patterns (should match)
            if not pattern.match(data):
                return {'valid': False, 'error': f'{field_name} format is invalid'}
        
        return {'valid': True, 'sanitized': cls.sanitize_string(data)}
    
    @classmethod
    def sanitize_string(cls, data: str) -> str:
        """Sanitize string input"""
        if not isinstance(data, str):
            return str(data)
        
        # Remove null bytes
        data = data.replace('\x00', '')
        
        # Limit length
        if len(data) > 10000:
            data = data[:10000]
        
        # Basic HTML encoding for safety
        data = data.replace('<', '&lt;').replace('>', '&gt;')
        
        return data.strip()
    
    @classmethod
    def validate_json_structure(cls, data: Dict[str, Any], required_fields: List[str], 
                               optional_fields: List[str] = None) -> Dict[str, Any]:
        """Validate JSON structure"""
        errors = []
        optional_fields = optional_fields or []
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Check for unexpected fields
        allowed_fields = set(required_fields + optional_fields)
        unexpected_fields = set(data.keys()) - allowed_fields
        if unexpected_fields:
            errors.append(f"Unexpected fields: {', '.join(unexpected_fields)}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

class RateLimiter:
    """Enhanced rate limiting with different strategies"""
    
    def __init__(self):
        self.requests = {}  # In production, use Redis
        self.blocked_ips = {}
    
    def is_rate_limited(self, identifier: str, limit: int, window_seconds: int) -> Dict[str, Any]:
        """Check if request should be rate limited"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Clean old requests
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier] 
                if req_time > window_start
            ]
        else:
            self.requests[identifier] = []
        
        # Check if over limit
        current_requests = len(self.requests[identifier])
        
        if current_requests >= limit:
            # Add to blocked IPs if severely over limit
            if current_requests > limit * 2:
                self.blocked_ips[identifier] = now + timedelta(minutes=15)
            
            return {
                'limited': True,
                'current_requests': current_requests,
                'limit': limit,
                'reset_time': (window_start + timedelta(seconds=window_seconds)).isoformat()
            }
        
        # Add current request
        self.requests[identifier].append(now)
        
        return {
            'limited': False,
            'current_requests': current_requests + 1,
            'limit': limit,
            'remaining': limit - current_requests - 1
        }
    
    def is_blocked(self, identifier: str) -> bool:
        """Check if IP is temporarily blocked"""
        if identifier in self.blocked_ips:
            if datetime.utcnow() > self.blocked_ips[identifier]:
                del self.blocked_ips[identifier]
                return False
            return True
        return False

class AuditLogger:
    """Security audit logging"""
    
    def __init__(self):
        self.logger = logging.getLogger("security_audit")
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], 
                          severity: str = "INFO", user_id: str = None, ip_address: str = None):
        """Log security-related events"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "severity": severity,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details
        }
        
        log_message = f"Security Event: {event_type} | {details}"
        
        if severity == "CRITICAL":
            self.logger.critical(log_message, extra=log_entry)
        elif severity == "WARNING":
            self.logger.warning(log_message, extra=log_entry)
        else:
            self.logger.info(log_message, extra=log_entry)
    
    def log_file_upload(self, filename: str, file_size: int, user_id: str = None, 
                       ip_address: str = None, success: bool = True):
        """Log file upload events"""
        self.log_security_event(
            "FILE_UPLOAD",
            {
                "filename": filename,
                "file_size": file_size,
                "success": success
            },
            severity="INFO" if success else "WARNING",
            user_id=user_id,
            ip_address=ip_address
        )
    
    def log_authentication_attempt(self, user_id: str, success: bool, ip_address: str = None):
        """Log authentication attempts"""
        self.log_security_event(
            "AUTH_ATTEMPT",
            {
                "user_id": user_id,
                "success": success
            },
            severity="INFO" if success else "WARNING",
            user_id=user_id,
            ip_address=ip_address
        )
    
    def log_suspicious_activity(self, activity_type: str, details: Dict[str, Any], 
                               ip_address: str = None):
        """Log suspicious activities"""
        self.log_security_event(
            "SUSPICIOUS_ACTIVITY",
            {
                "activity_type": activity_type,
                **details
            },
            severity="CRITICAL",
            ip_address=ip_address
        )

# Global instances
security_validator = SecurityValidator()
rate_limiter = RateLimiter()
audit_logger = AuditLogger()