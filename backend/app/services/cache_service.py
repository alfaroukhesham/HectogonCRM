# backend/app/services/cache_service.py

from fastapi import Depends
from app.core.redis_client import get_redis_client
import redis.asyncio as redis

class CacheService:
    def __init__(self, redis_client: redis.Redis = Depends(get_redis_client)):
        self.redis = redis_client

    async def invalidate_dashboard_stats(self, organization_id: str):
        """
        Deletes the cached dashboard stats for a given organization.
        """
        cache_key = f"dashboard:stats:{organization_id}"
        await self.redis.delete(cache_key)
