# cache-service/service.py

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from app.core.config import settings
import redis.asyncio as redis
from redis.exceptions import RedisError

from .constants import (
    DASHBOARD_STATS_KEY, REFRESH_TOKEN_KEY, OAUTH_STATE_KEY, PASSWORD_RESET_KEY,
    EMAIL_VERIFICATION_KEY, JTI_DENYLIST_KEY, USER_MEMBERSHIPS_KEY,
    USER_MEMBERSHIPS_PATTERN_BY_USER, USER_MEMBERSHIPS_PATTERN_BY_ORG,
    TOKEN_CLEANUP_PATTERNS, OAUTH_STATE_TTL, PASSWORD_RESET_TTL, EMAIL_VERIFICATION_TTL,
    LOG_DASHBOARD_INVALIDATED, LOG_DASHBOARD_CACHED, LOG_REFRESH_TOKEN_STORED,
    LOG_REFRESH_TOKEN_REVOKED, LOG_JTI_BLACKLISTED, LOG_MEMBERSHIP_CACHED,
    LOG_MEMBERSHIP_INVALIDATED, LOG_TOKEN_CLEANUP
)
from .utils import (
    serialize_data, deserialize_data, format_cache_key, decode_redis_value,
    parse_cached_data, extract_token_type_from_pattern, calculate_refresh_token_ttl,
    truncate_jti_for_logging, hash_token_secure
)
from .types import TokenCleanupStats, CacheKey, CacheValue, TTLSeconds

logger = logging.getLogger(__name__)

class CacheService:
    """
    Comprehensive caching service for Redis-based token and data caching.
    Provides graceful fallback behavior when Redis is unavailable.
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def _safe_redis_operation(self, operation_name: str, operation_func, fallback_value=None):
        """
        Safely execute Redis operations with error handling and fallback.
        
        Args:
            operation_name: Name of the operation for logging
            operation_func: Function to execute
            fallback_value: Value to return if Redis is unavailable
        
        Returns:
            Result of operation or fallback_value if Redis fails
        """
        try:
            return await operation_func()
        except RedisError as e:
            logger.error(f"Redis {operation_name} failed: {e}")
            return fallback_value
        except Exception as e:
            logger.error(f"Unexpected error during Redis {operation_name}: {e}")
            return fallback_value

    # =============================================================================
    # DASHBOARD STATS CACHING
    # =============================================================================

    async def invalidate_dashboard_stats(self, organization_id: str):
        """
        Deletes the cached dashboard stats for a given organization.
        Logs success/failure but doesn't raise exceptions to avoid breaking main request flow.
        """
        async def _delete_cache():
            cache_key = format_cache_key(DASHBOARD_STATS_KEY, organization_id=organization_id)
            result = await self.redis.delete(cache_key)
            logger.info(LOG_DASHBOARD_INVALIDATED.format(organization_id=organization_id, result=result))
            return result

        await self._safe_redis_operation("dashboard cache invalidation", _delete_cache)

    async def cache_dashboard_stats(self, organization_id: str, stats_data: dict):
        """Cache dashboard statistics for an organization."""
        async def _cache():
            cache_key = format_cache_key(DASHBOARD_STATS_KEY, organization_id=organization_id)
            ttl = settings.DASHBOARD_CACHE_TTL
            await self.redis.set(cache_key, serialize_data(stats_data), ex=ttl)
            logger.info(LOG_DASHBOARD_CACHED.format(organization_id=organization_id, ttl=ttl))
            return True

        return await self._safe_redis_operation("dashboard stats caching", _cache, False)

    async def get_cached_dashboard_stats(self, organization_id: str) -> Optional[dict]:
        """Retrieve cached dashboard statistics for an organization."""
        async def _get():
            cache_key = format_cache_key(DASHBOARD_STATS_KEY, organization_id=organization_id)
            cached_data = await self.redis.get(cache_key)
            return parse_cached_data(cached_data)

        return await self._safe_redis_operation("dashboard stats retrieval", _get)

    # =============================================================================
    # TOKEN MANAGEMENT METHODS
    # =============================================================================

    # Refresh Token Storage Methods
    async def store_refresh_token(self, user_id: str, token: str, session_id: str = None):
        """Stores a user's refresh token in Redis with a TTL."""
        async def _store():
            # Generate session_id if not provided (for backward compatibility)
            actual_session_id = session_id
            if actual_session_id is None:
                import uuid
                actual_session_id = str(uuid.uuid4())
            
            key = format_cache_key(REFRESH_TOKEN_KEY, user_id=user_id, session_id=actual_session_id)
            ttl_seconds = calculate_refresh_token_ttl(settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
            await self.redis.set(key, token, ex=ttl_seconds)
            logger.info(LOG_REFRESH_TOKEN_STORED.format(user_id=user_id, ttl_seconds=ttl_seconds))
            return True

        return await self._safe_redis_operation("refresh token storage", _store, False)

    async def get_refresh_token(self, user_id: str, session_id: str = None) -> Optional[str]:
        """
        Retrieves a user's refresh token from Redis.
        
        Args:
            user_id: The user ID to retrieve the token for
            session_id: Optional session ID for session-specific retrieval.
                       If provided, performs direct key lookup for better performance.
                       If None, scans for any refresh token for the user (fallback mode).
        
        Returns:
            The refresh token if found, None otherwise.
            
        Note:
            When session_id is None, this method scans for any refresh token matching
            the user pattern and returns the first one found. This is non-deterministic
            in multi-session scenarios and should be used with caution.
        """
        async def _get():
            if session_id:
                # Direct lookup for specific session
                key = format_cache_key(REFRESH_TOKEN_KEY, user_id=user_id, session_id=session_id)
                token = await self.redis.get(key)
                return decode_redis_value(token) if token else None
            else:
                # Fallback: scan for any refresh token for this user
                pattern = format_cache_key(REFRESH_TOKEN_KEY, user_id=user_id, session_id="*")
                async for key in self.redis.scan_iter(match=pattern):
                    token = await self.redis.get(key)
                    if token:
                        return decode_redis_value(token)
            return None

        return await self._safe_redis_operation("refresh token retrieval", _get)

    async def revoke_refresh_token(self, user_id: str, session_id: Optional[str] = None) -> bool:
        """Revoke a user's refresh token; if session_id is provided, only that session."""
        async def _revoke():
            if session_id:
                key = format_cache_key(REFRESH_TOKEN_KEY, user_id=user_id, session_id=session_id)
                result = await self.redis.delete(key)
            else:
                # Back-compat: delete all sessions
                pattern = format_cache_key(REFRESH_TOKEN_KEY, user_id=user_id, session_id="*")
                keys_to_delete = []
                async for key in self.redis.scan_iter(match=pattern):
                    keys_to_delete.append(key)
                result = await self.redis.delete(*keys_to_delete) if keys_to_delete else 0
            logger.info(LOG_REFRESH_TOKEN_REVOKED.format(user_id=user_id, result=result))
            return result > 0

        return await self._safe_redis_operation("refresh token revocation", _revoke, False)

    async def revoke_all_user_refresh_tokens(self, user_id: str) -> int:
        """Revoke all refresh tokens for a user across all sessions."""
        async def _revoke_all():
            # Scan for all refresh tokens for this user
            pattern = format_cache_key(REFRESH_TOKEN_KEY, user_id=user_id, session_id="*")
            keys_to_delete = []
            async for key in self.redis.scan_iter(match=pattern):
                keys_to_delete.append(key)
            
            if keys_to_delete:
                result = await self.redis.delete(*keys_to_delete)
            else:
                result = 0
            logger.info(LOG_REFRESH_TOKEN_REVOKED.format(user_id=user_id, result=result))
            return result

        return await self._safe_redis_operation("all refresh token revocation", _revoke_all, 0)

    # OAuth State Token Management
    async def store_oauth_state(self, state: str, provider: str, redirect_uri: str) -> bool:
        """Store OAuth state token with provider and redirect URI."""
        async def _store():
            key = format_cache_key(OAUTH_STATE_KEY, state=state)
            state_data = {
                "provider": provider,
                "redirect_uri": redirect_uri,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await self.redis.set(key, serialize_data(state_data), ex=OAUTH_STATE_TTL)
            logger.info(f"Stored OAuth state for {provider}")
            return True

        return await self._safe_redis_operation("OAuth state storage", _store, False)

    async def get_oauth_state(self, state: str) -> Optional[Dict[str, Any]]:
        """Get and consume OAuth state token (one-time use)."""
        async def _get():
            key = format_cache_key(OAUTH_STATE_KEY, state=state)
            # Atomic get + delete (Redis >= 6.2)
            state_data = await self.redis.execute_command("GETDEL", key)
            if state_data:
                data = decode_redis_value(state_data)
                return deserialize_data(data)
            return None

        return await self._safe_redis_operation("OAuth state retrieval", _get)

    # Password Reset Token Management
    async def store_password_reset_token(self, token: str, user_id: str) -> bool:
        """Store password reset token with user ID."""
        async def _store():
            hashed_token = hash_token_secure(token)
            key = format_cache_key(PASSWORD_RESET_KEY, token=hashed_token)
            token_data = {
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await self.redis.set(key, serialize_data(token_data), ex=PASSWORD_RESET_TTL)
            logger.info(f"Stored password reset token for user {user_id}")
            return True

        return await self._safe_redis_operation("password reset token storage", _store, False)

    async def get_password_reset_token(self, token: str) -> Optional[str]:
        """Get and consume password reset token (one-time use)."""
        async def _get():
            hashed_token = hash_token_secure(token)
            key = format_cache_key(PASSWORD_RESET_KEY, token=hashed_token)
            token_data = await self.redis.execute_command("GETDEL", key)
            if token_data:
                data = decode_redis_value(token_data)
                parsed_data = deserialize_data(data)
                return parsed_data.get("user_id")
            return None

        return await self._safe_redis_operation("password reset token retrieval", _get)

    async def revoke_password_reset_token(self, token: str) -> bool:
        """Revoke password reset token."""
        async def _revoke():
            hashed_token = hash_token_secure(token)
            key = format_cache_key(PASSWORD_RESET_KEY, token=hashed_token)
            result = await self.redis.delete(key)
            return result > 0

        return await self._safe_redis_operation("password reset token revocation", _revoke, False)

    # Email Verification Token Management
    async def store_email_verification_token(self, token: str, user_id: str) -> bool:
        """Store email verification token with user ID."""
        async def _store():
            hashed_token = hash_token_secure(token)
            key = format_cache_key(EMAIL_VERIFICATION_KEY, token=hashed_token)
            token_data = {
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await self.redis.set(key, serialize_data(token_data), ex=EMAIL_VERIFICATION_TTL)
            logger.info(f"Stored email verification token for user {user_id}")
            return True

        return await self._safe_redis_operation("email verification token storage", _store, False)

    async def get_email_verification_token(self, token: str) -> Optional[str]:
        """Get and consume email verification token (one-time use)."""
        async def _get():
            hashed_token = hash_token_secure(token)
            key = format_cache_key(EMAIL_VERIFICATION_KEY, token=hashed_token)
            token_data = await self.redis.execute_command("GETDEL", key)
            if token_data:
                data = decode_redis_value(token_data)
                parsed_data = deserialize_data(data)
                return parsed_data.get("user_id")
            return None

        return await self._safe_redis_operation("email verification token retrieval", _get)

    # Token Blacklisting for JWT Access Tokens
    async def blacklist_token_jti(self, jti: str, ttl_seconds: int) -> bool:
        """
        Add a token's JTI to the blacklist with TTL.
        
        Args:
            jti: Token's unique identifier
            ttl_seconds: How long to keep the JTI in the blacklist
        """
        async def _blacklist():
            key = format_cache_key(JTI_DENYLIST_KEY, jti=jti)
            await self.redis.set(key, "revoked", ex=ttl_seconds)
            logger.info(LOG_JTI_BLACKLISTED.format(
                jti=truncate_jti_for_logging(jti), 
                ttl_seconds=ttl_seconds
            ))
            return True

        return await self._safe_redis_operation("token blacklisting", _blacklist, False)

    async def is_token_blacklisted(self, jti: str) -> bool:
        """
        Check if a token's JTI is blacklisted.
        
        Args:
            jti: Token's unique identifier
            
        Returns:
            True if blacklisted, False if not blacklisted or Redis is unavailable
        """
        async def _check():
            key = format_cache_key(JTI_DENYLIST_KEY, jti=jti)
            result = await self.redis.get(key)
            return result is not None

        return await self._safe_redis_operation("token blacklist check", _check, False)

    # =============================================================================
    # USER MEMBERSHIP AND PERMISSION CACHING
    # =============================================================================

    async def cache_user_memberships(self, user_id: str, organization_id: str, membership_data: dict):
        """Caches a user's membership for a specific organization."""
        async def _cache():
            key = format_cache_key(USER_MEMBERSHIPS_KEY, 
                                organization_id=organization_id, 
                                user_id=user_id)
            ttl = settings.USER_MEMBERSHIP_CACHE_TTL
            await self.redis.set(key, serialize_data(membership_data), ex=ttl)
            logger.info(LOG_MEMBERSHIP_CACHED.format(
                user_id=user_id, organization_id=organization_id, ttl=ttl
            ))
            return True

        return await self._safe_redis_operation("membership caching", _cache, False)

    async def get_cached_user_membership(self, user_id: str, organization_id: str) -> Optional[dict]:
        """Retrieves cached membership for a user in a specific organization."""
        async def _get():
            key = format_cache_key(USER_MEMBERSHIPS_KEY, 
                                organization_id=organization_id, 
                                user_id=user_id)
            cached_data = await self.redis.get(key)
            return parse_cached_data(cached_data)

        return await self._safe_redis_operation("membership retrieval", _get)
    
    async def get_cached_user_memberships(self, user_id: str, organization_ids: Optional[List[str]] = None) -> list:
        """
        Retrieves cached memberships for a user across multiple organizations.
        If organization_ids is provided, only checks those orgs. Otherwise, this method
        cannot efficiently retrieve all memberships and returns empty list.
        """
        if not organization_ids:
            logger.warning(f"get_cached_user_memberships called without organization_ids for user {user_id}. Cannot efficiently retrieve all memberships with new schema.")
            return []
        
        async def _get_multiple():
            memberships = []
            for org_id in organization_ids:
                key = format_cache_key(USER_MEMBERSHIPS_KEY, 
                                    organization_id=org_id, 
                                    user_id=user_id)
                cached_data = await self.redis.get(key)
                parsed_data = parse_cached_data(cached_data)
                if parsed_data:
                    memberships.append(parsed_data)
            return memberships

        return await self._safe_redis_operation("multiple membership retrieval", _get_multiple, [])

    async def invalidate_user_membership(self, user_id: str, organization_id: str):
        """Invalidates cached membership for a user in a specific organization."""
        async def _invalidate():
            key = format_cache_key(USER_MEMBERSHIPS_KEY, 
                                organization_id=organization_id, 
                                user_id=user_id)
            result = await self.redis.delete(key)
            logger.info(LOG_MEMBERSHIP_INVALIDATED.format(
                user_id=user_id, organization_id=organization_id, result=result
            ))
            return result > 0

        return await self._safe_redis_operation("membership invalidation", _invalidate, False)
    
    async def invalidate_user_memberships(self, user_id: str, organization_ids: Optional[List[str]] = None):
        """
        Invalidates cached memberships for a user across multiple organizations.
        If organization_ids is provided, only invalidates those orgs. Otherwise, scans for all
        user memberships (less efficient but maintains backward compatibility).
        """
        async def _invalidate():
            keys_to_delete = []
            
            if organization_ids:
                # Efficient: delete specific org memberships
                for org_id in organization_ids:
                    key = format_cache_key(USER_MEMBERSHIPS_KEY, 
                                        organization_id=org_id, 
                                        user_id=user_id)
                    keys_to_delete.append(key)
            else:
                # Backward compatibility: scan for all memberships for this user
                pattern = format_cache_key(USER_MEMBERSHIPS_PATTERN_BY_USER, user_id=user_id)
                async for key in self.redis.scan_iter(match=pattern):
                    keys_to_delete.append(key)
            
            if keys_to_delete:
                result = await self.redis.delete(*keys_to_delete)
                logger.info(f"Invalidated {result} membership caches for user {user_id}")
                return result
            return 0

        return await self._safe_redis_operation("membership invalidation", _invalidate, 0)

    async def invalidate_organization_members_cache(self, organization_id: str):
        """
        Invalidate caches for all members of an organization.
        This should be called when organization membership changes.
        With the new org-scoped key schema, we can safely target only the specific organization.
        """
        async def _invalidate():
            # Pattern to match all user membership caches for this specific organization
            pattern = format_cache_key(USER_MEMBERSHIPS_PATTERN_BY_ORG, organization_id=organization_id)
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                result = await self.redis.delete(*keys)
                logger.info(f"Invalidated {result} membership caches for organization {organization_id}")
                return result
            else:
                logger.info(f"No membership caches found to invalidate for organization {organization_id}")
                return 0

        return await self._safe_redis_operation("organization membership invalidation", _invalidate, 0)

    # =============================================================================
    # TOKEN CLEANUP UTILITIES
    # =============================================================================

    async def cleanup_expired_tokens(self) -> TokenCleanupStats:
        """
        Cleanup expired tokens from Redis.
        Note: Redis TTL handles most of this automatically, but this method
        can be used for manual cleanup or monitoring.
        """
        async def _cleanup():
            cleanup_stats = {}
            for pattern in TOKEN_CLEANUP_PATTERNS:
                token_type = extract_token_type_from_pattern(pattern)
                expired_count = 0
                
                async for key in self.redis.scan_iter(match=pattern):
                    ttl = await self.redis.ttl(key)
                    # ttl == -2 means key doesn't exist (shouldn't happen in scan results)
                    # ttl == -1 means key exists but has no TTL  
                    if ttl == -1:  # Key exists but has no TTL (shouldn't happen)
                        await self.redis.delete(key)
                        expired_count += 1
                    # Note: Keys with TTL > 0 will expire automatically
                
                cleanup_stats[token_type] = expired_count
            
            logger.info(LOG_TOKEN_CLEANUP.format(cleanup_stats=cleanup_stats))
            return cleanup_stats

        return await self._safe_redis_operation("token cleanup", _cleanup, {})
