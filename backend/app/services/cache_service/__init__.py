# cache-service/__init__.py

from fastapi import Depends
from .service import CacheService
from .models import (
    CacheEntry, CacheStats, OAuthStateData, PasswordResetTokenData,
    EmailVerificationTokenData, DashboardStatsCache, MembershipCacheData
)
from .types import (
    CacheOperation, TokenType, CacheResult
)
from .utils import (
    serialize_data, deserialize_data, format_cache_key,
    decode_redis_value, parse_cached_data, extract_token_type_from_pattern,
    calculate_refresh_token_ttl, truncate_jti_for_logging, hash_token_secure
)
from .constants import (
    DASHBOARD_STATS_KEY, REFRESH_TOKEN_KEY, OAUTH_STATE_KEY, PASSWORD_RESET_KEY,
    EMAIL_VERIFICATION_KEY, JTI_DENYLIST_KEY, USER_MEMBERSHIPS_KEY,
    USER_MEMBERSHIPS_PATTERN_BY_USER, USER_MEMBERSHIPS_PATTERN_BY_ORG,
    ALL_USER_MEMBERSHIPS_PATTERN, TOKEN_CLEANUP_PATTERNS,
    OAUTH_STATE_TTL, PASSWORD_RESET_TTL, EMAIL_VERIFICATION_TTL,
    LOG_DASHBOARD_INVALIDATED, LOG_DASHBOARD_CACHED, LOG_REFRESH_TOKEN_STORED,
    LOG_REFRESH_TOKEN_REVOKED, LOG_JTI_BLACKLISTED, LOG_MEMBERSHIP_CACHED,
    LOG_MEMBERSHIP_INVALIDATED, LOG_TOKEN_CLEANUP
)

# Dependency injection function
from app.core.redis_client import get_redis_client

async def get_cache_service(
    redis_client = Depends(get_redis_client)
) -> CacheService:
    return CacheService(redis_client)

__all__ = [
    "CacheService",
    "get_cache_service",
    # Models
    "CacheEntry",
    "CacheStats", 
    "OAuthStateData",
    "PasswordResetTokenData",
    "EmailVerificationTokenData",
    "DashboardStatsCache",
    "MembershipCacheData",
    # Types
    "CacheOperation",
    "TokenType",
    "CacheResult",
    # Utils
    "serialize_data",
    "deserialize_data", 
    "format_cache_key",
    "decode_redis_value",
    "parse_cached_data",
    "extract_token_type_from_pattern",
    "calculate_refresh_token_ttl",
    "truncate_jti_for_logging",
    "hash_token_secure",
    # Constants
    "DASHBOARD_STATS_KEY",
    "REFRESH_TOKEN_KEY",
    "OAUTH_STATE_KEY",
    "PASSWORD_RESET_KEY",
    "EMAIL_VERIFICATION_KEY",
    "JTI_DENYLIST_KEY",
    "USER_MEMBERSHIPS_KEY",
    "USER_MEMBERSHIPS_PATTERN_BY_USER",
    "USER_MEMBERSHIPS_PATTERN_BY_ORG",
    "ALL_USER_MEMBERSHIPS_PATTERN",
    "TOKEN_CLEANUP_PATTERNS",
    "OAUTH_STATE_TTL",
    "PASSWORD_RESET_TTL",
    "EMAIL_VERIFICATION_TTL",
    "LOG_DASHBOARD_INVALIDATED",
    "LOG_DASHBOARD_CACHED",
    "LOG_REFRESH_TOKEN_STORED",
    "LOG_REFRESH_TOKEN_REVOKED",
    "LOG_JTI_BLACKLISTED",
    "LOG_MEMBERSHIP_CACHED",
    "LOG_MEMBERSHIP_INVALIDATED",
    "LOG_TOKEN_CLEANUP"
]
