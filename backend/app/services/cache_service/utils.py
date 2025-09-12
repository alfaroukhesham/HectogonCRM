# cache-service/utils.py

import json
import hashlib
import logging
from typing import Any, Optional
from .types import CacheKey, CacheValue

logger = logging.getLogger(__name__)

def serialize_data(data: Any) -> str:
    """Serialize data for Redis storage using JSON"""
    return json.dumps(data, default=str)

def deserialize_data(data: str) -> Any:
    """Deserialize data from Redis"""
    return json.loads(data)

def format_cache_key(pattern: str, **kwargs) -> CacheKey:
    """Generate cache key from pattern and parameters"""
    return pattern.format(**kwargs)

def decode_redis_value(value: bytes) -> str:
    """Safely decode Redis byte values to string"""
    if isinstance(value, bytes):
        return value.decode('utf-8')
    return value

def parse_cached_data(cached_data: Optional[Any]) -> Optional[dict]:
    """Parse cached data with error handling"""
    if not cached_data:
        return None
    
    try:
        data = decode_redis_value(cached_data)
        return json.loads(data)
    except (json.JSONDecodeError, TypeError) as e:
        # Log error but don't raise to maintain graceful degradation
        logger.warning(f"Failed to parse cached data: {e}")
        return None

def extract_token_type_from_pattern(pattern: str) -> str:
    """Extract token type from cleanup pattern"""
    return pattern.replace("*", "").rstrip(":")

def calculate_refresh_token_ttl(expire_days: int) -> int:
    """Calculate TTL in seconds for refresh tokens"""
    return expire_days * 24 * 60 * 60

def truncate_jti_for_logging(jti: str, length: int = 8) -> str:
    """Truncate JTI for secure logging"""
    return f"{jti[:length]}..." if len(jti) > length else jti

def hash_token_secure(token: str) -> str:
    """Create a secure SHA-256 hash of a token for use in cache keys"""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()
