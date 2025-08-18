# backend/app/services/cache_service.py

import logging
from fastapi import Depends
from app.core.redis_client import get_redis_client
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
