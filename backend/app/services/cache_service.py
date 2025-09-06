# backend/app/services/cache_service.py

import logging
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from fastapi import Depends
from app.core.redis_client import get_redis_client
from app.core.config import settings
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class CacheService:
    """
    Comprehensive caching service for Redis-based token and data caching.
    Provides graceful fallback behavior when Redis is unavailable.
    """
    
    def __init__(self, redis_client: redis.Redis = Depends(get_redis_client)):
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
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis {operation_name} failed: {e}")
            return fallback_value
        except Exception as e:
            logger.error(f"Unexpected error during Redis {operation_name}: {e}")
            return fallback_value

    async def invalidate_dashboard_stats(self, organization_id: str):
        """
        Deletes the cached dashboard stats for a given organization.
        Logs success/failure but doesn't raise exceptions to avoid breaking main request flow.
        """
        async def _delete_cache():
            cache_key = f"dashboard:stats:{organization_id}"
            result = await self.redis.delete(cache_key)
            logger.info(f"Successfully invalidated dashboard cache for org: {organization_id} (keys deleted: {result})")
            return result

        await self._safe_redis_operation("dashboard cache invalidation", _delete_cache)

    async def cache_dashboard_stats(self, organization_id: str, stats_data: dict):
        """
        Cache dashboard statistics for an organization.
        """
        async def _cache():
            cache_key = f"dashboard:stats:{organization_id}"
            ttl = settings.DASHBOARD_CACHE_TTL
            await self.redis.set(cache_key, json.dumps(stats_data, default=str), ex=ttl)
            logger.info(f"Cached dashboard stats for org: {organization_id} (TTL: {ttl}s)")
            return True

        return await self._safe_redis_operation("dashboard stats caching", _cache, False)

    async def get_cached_dashboard_stats(self, organization_id: str) -> Optional[dict]:
        """
        Retrieve cached dashboard statistics for an organization.
        """
        async def _get():
            cache_key = f"dashboard:stats:{organization_id}"
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                data = cached_data.decode('utf-8') if isinstance(cached_data, bytes) else cached_data
                return json.loads(data)
            return None

        return await self._safe_redis_operation("dashboard stats retrieval", _get)

    # =============================================================================
    # TOKEN MANAGEMENT METHODS
    # =============================================================================

    # Part 1: Refresh Token Storage Methods
    async def store_refresh_token(self, user_id: str, token: str):
        """
        Stores a user's refresh token in Redis with a TTL.
        """
        async def _store():
            key = f"refresh_token:{user_id}"
            ttl_seconds = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
            await self.redis.set(key, token, ex=ttl_seconds)
            logger.info(f"Stored refresh token for user {user_id} with TTL {ttl_seconds}s")
            return True

        return await self._safe_redis_operation("refresh token storage", _store, False)

    async def get_refresh_token(self, user_id: str) -> Optional[str]:
        """
        Retrieves a user's refresh token from Redis.
        """
        async def _get():
            key = f"refresh_token:{user_id}"
            token = await self.redis.get(key)
            if token:
                return token.decode('utf-8') if isinstance(token, bytes) else token
            return None

        return await self._safe_redis_operation("refresh token retrieval", _get)

    async def revoke_refresh_token(self, user_id: str):
        """
        Revokes a user's refresh token by deleting it from Redis.
        """
        async def _revoke():
            key = f"refresh_token:{user_id}"
            result = await self.redis.delete(key)
            logger.info(f"Revoked refresh token for user {user_id} (keys deleted: {result})")
            return result > 0

        return await self._safe_redis_operation("refresh token revocation", _revoke, False)

    async def revoke_all_user_refresh_tokens(self, user_id: str) -> int:
        """
        Revoke all refresh tokens for a user (Redis implementation).
        """
        async def _revoke_all():
            # For Redis, we just need to delete the single refresh token per user
            key = f"refresh_token:{user_id}"
            result = await self.redis.delete(key)
            logger.info(f"Revoked all refresh tokens for user {user_id} (keys deleted: {result})")
            return result

        return await self._safe_redis_operation("all refresh token revocation", _revoke_all, 0)

    # Part 2: OAuth State Token Management
    async def store_oauth_state(self, state: str, provider: str, redirect_uri: str) -> bool:
        """
        Store OAuth state token with provider and redirect URI.
        """
        async def _store():
            key = f"oauth_state:{state}"
            state_data = {
                "provider": provider,
                "redirect_uri": redirect_uri,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            # OAuth states expire in 10 minutes
            await self.redis.set(key, json.dumps(state_data), ex=600)
            logger.info(f"Stored OAuth state for {provider}")
            return True

        return await self._safe_redis_operation("OAuth state storage", _store, False)

    async def get_oauth_state(self, state: str) -> Optional[Dict[str, Any]]:
        """
        Get and consume OAuth state token (one-time use).
        """
        async def _get():
            key = f"oauth_state:{state}"
            # Atomic get + delete (Redis >= 6.2)
            state_data = await self.redis.execute_command("GETDEL", key)
            if state_data:
                data = state_data.decode('utf-8') if isinstance(state_data, bytes) else state_data
                return json.loads(data)
            return None

        return await self._safe_redis_operation("OAuth state retrieval", _get)
    # Part 3: Password Reset Token Management
    async def store_password_reset_token(self, token: str, user_id: str) -> bool:
        """
        Store password reset token with user ID.
        """
        async def _store():
            key = f"password_reset:{token}"
            token_data = {
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            # Password reset tokens expire in 1 hour
            await self.redis.set(key, json.dumps(token_data), ex=3600)
            logger.info(f"Stored password reset token for user {user_id}")
            return True

        return await self._safe_redis_operation("password reset token storage", _store, False)

    async def get_password_reset_token(self, token: str) -> Optional[str]:
        """
        Get and consume password reset token (one-time use).
        """
        async def _get():
            key = f"password_reset:{token}"
            token_data = await self.redis.execute_command("GETDEL", key)
            if token_data:
                data = token_data.decode('utf-8') if isinstance(token_data, bytes) else token_data
                parsed_data = json.loads(data)
                return parsed_data.get("user_id")
            return None

        return await self._safe_redis_operation("password reset token retrieval", _get)
    async def revoke_password_reset_token(self, token: str) -> bool:
        """
        Revoke password reset token.
        """
        async def _revoke():
            key = f"password_reset:{token}"
            result = await self.redis.delete(key)
            return result > 0

        return await self._safe_redis_operation("password reset token revocation", _revoke, False)

    # Part 4: Email Verification Token Management
    async def store_email_verification_token(self, token: str, user_id: str) -> bool:
        """
        Store email verification token with user ID.
        """
        async def _store():
            key = f"email_verification:{token}"
            token_data = {
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            # Email verification tokens expire in 24 hours
            await self.redis.set(key, json.dumps(token_data), ex=86400)
            logger.info(f"Stored email verification token for user {user_id}")
            return True

        return await self._safe_redis_operation("email verification token storage", _store, False)

    async def get_email_verification_token(self, token: str) -> Optional[str]:
        """
        Get and consume email verification token (one-time use).
        """
        async def _get():
            key = f"email_verification:{token}"
            token_data = await self.redis.execute_command("GETDEL", key)
            if token_data:
                data = token_data.decode('utf-8') if isinstance(token_data, bytes) else token_data
                parsed_data = json.loads(data)
                return parsed_data.get("user_id")
            return None

        return await self._safe_redis_operation("email verification token retrieval", _get)
        return await self._safe_redis_operation("email verification token revocation", _revoke, False)

    # Part 5: Token Blacklisting for JWT Access Tokens
    async def blacklist_token_jti(self, jti: str, ttl_seconds: int) -> bool:
        """
        Add a token's JTI to the blacklist with TTL.
        
        Args:
            jti: Token's unique identifier
            ttl_seconds: How long to keep the JTI in the blacklist
        """
        async def _blacklist():
            key = f"jti_denylist:{jti}"
            await self.redis.set(key, "revoked", ex=ttl_seconds)
            logger.info(f"Blacklisted token JTI: {jti[:8]}... for {ttl_seconds}s")
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
            key = f"jti_denylist:{jti}"
            result = await self.redis.get(key)
            return result is not None

        return await self._safe_redis_operation("token blacklist check", _check, False)

    # =============================================================================
    # USER MEMBERSHIP AND PERMISSION CACHING
    # =============================================================================

    async def cache_user_memberships(self, user_id: str, organization_id: str, membership_data: dict):
        """
        Caches a user's membership for a specific organization.
        """
        async def _cache():
            key = f"user_memberships:{organization_id}:{user_id}"
            # Use configurable TTL from settings
            ttl = settings.USER_MEMBERSHIP_CACHE_TTL
            await self.redis.set(key, json.dumps(membership_data, default=str), ex=ttl)
            logger.info(f"Cached membership for user {user_id} in org {organization_id} (TTL: {ttl}s)")
            return True

        return await self._safe_redis_operation("membership caching", _cache, False)

    async def get_cached_user_membership(self, user_id: str, organization_id: str) -> Optional[dict]:
        """
        Retrieves cached membership for a user in a specific organization.
        """
        async def _get():
            key = f"user_memberships:{organization_id}:{user_id}"
            cached_data = await self.redis.get(key)
            if cached_data:
                data = cached_data.decode('utf-8') if isinstance(cached_data, bytes) else cached_data
                return json.loads(data)
            return None

        return await self._safe_redis_operation("membership retrieval", _get)
    
    async def get_cached_user_memberships(self, user_id: str, organization_ids: Optional[list] = None) -> list:
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
                key = f"user_memberships:{org_id}:{user_id}"
                cached_data = await self.redis.get(key)
                if cached_data:
                    data = cached_data.decode('utf-8') if isinstance(cached_data, bytes) else cached_data
                    memberships.append(json.loads(data))
            return memberships

        return await self._safe_redis_operation("multiple membership retrieval", _get_multiple, [])

    async def invalidate_user_membership(self, user_id: str, organization_id: str):
        """
        Invalidates cached membership for a user in a specific organization.
        """
        async def _invalidate():
            key = f"user_memberships:{organization_id}:{user_id}"
            result = await self.redis.delete(key)
            logger.info(f"Invalidated membership cache for user {user_id} in org {organization_id} (keys deleted: {result})")
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
                    key = f"user_memberships:{org_id}:{user_id}"
                    keys_to_delete.append(key)
            else:
                # Backward compatibility: scan for all memberships for this user
                pattern = f"user_memberships:*:{user_id}"
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
            pattern = f"user_memberships:{organization_id}:*"
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

    async def cleanup_expired_tokens(self) -> Dict[str, int]:
        """
        Cleanup expired tokens from Redis.
        Note: Redis TTL handles most of this automatically, but this method
        can be used for manual cleanup or monitoring.
        """
        async def _cleanup():
            patterns_to_check = [
                "refresh_token:*",
                "oauth_state:*", 
                "password_reset:*",
                "email_verification:*",
                "jti_denylist:*"
            ]
            
            cleanup_stats = {}
            for pattern in patterns_to_check:
                token_type = pattern.replace("*", "").rstrip(":")
                expired_count = 0
                
                async for key in self.redis.scan_iter(match=pattern):
                    ttl = await self.redis.ttl(key)
                    if ttl == -2:  # Key doesn't exist (expired)
                        expired_count += 1
                    elif ttl == -1:  # Key exists but has no TTL (shouldn't happen)
                        await self.redis.delete(key)
                        expired_count += 1
                
                cleanup_stats[token_type] = expired_count
            
            logger.info(f"Token cleanup completed: {cleanup_stats}")
            return cleanup_stats

        return await self._safe_redis_operation("token cleanup", _cleanup, {})
