# backend/app/services/cache_service.py

import logging
import json
from fastapi import Depends
from app.core.redis_client import get_redis_client
from app.core.config import settings
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self, redis_client: redis.Redis = Depends(get_redis_client)):
        self.redis = redis_client

    async def invalidate_dashboard_stats(self, organization_id: str):
        """
        Deletes the cached dashboard stats for a given organization.
        Logs success/failure but doesn't raise exceptions to avoid breaking main request flow.
        """
        try:
            cache_key = f"dashboard:stats:{organization_id}"
            result = await self.redis.delete(cache_key)
            logger.info(f"Successfully invalidated dashboard cache for org: {organization_id} (keys deleted: {result})")
        except Exception as e:
            # Log the error but don't re-raise it to avoid breaking the main request
            logger.error(f"Cache invalidation failed for org {organization_id}: {e}")

    # Part 1: Refresh Token Storage Methods
    async def store_refresh_token(self, user_id: str, token: str):
        """
        Stores a user's refresh token in Redis with a TTL.
        """
        key = f"refresh_token:{user_id}"
        # Set the expiration to match the refresh token's lifetime
        ttl_seconds = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        await self.redis.set(key, token, ex=ttl_seconds)
        logger.info(f"Stored refresh token for user {user_id} with TTL {ttl_seconds}s")

    async def get_refresh_token(self, user_id: str) -> str | None:
        """
        Retrieves a user's refresh token from Redis.
        """
        key = f"refresh_token:{user_id}"
        token = await self.redis.get(key)
        if token:
            return token.decode('utf-8') if isinstance(token, bytes) else token
        return None

    async def revoke_refresh_token(self, user_id: str):
        """
        Revokes a user's refresh token by deleting it from Redis.
        """
        key = f"refresh_token:{user_id}"
        result = await self.redis.delete(key)
        logger.info(f"Revoked refresh token for user {user_id} (keys deleted: {result})")
        return result > 0

    # Part 2: Membership and Permission Caching Methods
    async def cache_user_memberships(self, user_id: str, memberships: list):
        """
        Caches a list of a user's organization memberships.
        """
        key = f"user_memberships:{user_id}"
        # Cache for a reasonable time, e.g., 1 hour
        await self.redis.set(key, json.dumps(memberships, default=str), ex=3600)
        logger.info(f"Cached {len(memberships)} memberships for user {user_id}")

    async def get_cached_user_memberships(self, user_id: str) -> list | None:
        """
        Retrieves cached memberships for a user.
        """
        key = f"user_memberships:{user_id}"
        cached_data = await self.redis.get(key)
        if cached_data:
            data = cached_data.decode('utf-8') if isinstance(cached_data, bytes) else cached_data
            return json.loads(data)
        return None

    async def invalidate_user_memberships(self, user_id: str):
        """
        Invalidates cached memberships for a user.
        """
        key = f"user_memberships:{user_id}"
        result = await self.redis.delete(key)
        logger.info(f"Invalidated membership cache for user {user_id} (keys deleted: {result})")
        return result > 0
