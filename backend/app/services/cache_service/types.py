# cache-service/types.py

from enum import Enum
from typing import Dict, Any, Optional

class CacheOperation(str, Enum):
    """Cache operations enum for logging and monitoring"""
    GET = "get"
    SET = "set"
    DELETE = "delete"
    INVALIDATE = "invalidate"
    SCAN = "scan"
    EXPIRE = "expire"

class TokenType(str, Enum):
    """Token types for cache management"""
    REFRESH_TOKEN = "refresh_token"
    OAUTH_STATE = "oauth_state"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
    JTI_DENYLIST = "jti_denylist"

class CacheResult:
    """Result object for cache operations"""
    def __init__(self, success: bool, data: Any = None, error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error

    def __bool__(self):
        return self.success

# Type aliases for clarity
TokenCleanupStats = Dict[str, int]
CacheKey = str
CacheValue = Any
TTLSeconds = int
