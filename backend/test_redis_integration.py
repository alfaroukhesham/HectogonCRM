#!/usr/bin/env python3
"""
Simple test script to validate Redis integration for authentication and session management.
This script tests the key functionality without requiring the full server setup.
"""

import asyncio
import logging
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_redis_integration():
    """Test Redis integration components."""
    # Import after setting up logging
    from app.core.redis_client import init_redis_pool, get_redis_client, close_redis_pool
    from app.services.cache_service import CacheService
    from app.core.security import create_refresh_token
    
    try:
        logger.info("🔧 Initializing Redis connection pool...")
        await init_redis_pool()
        logger.info("✅ Redis pool initialized")
        
        logger.info("🔧 Testing Redis connection...")
        redis_client = get_redis_client()
        
        # Test Redis connection
        await redis_client.ping()
        logger.info("✅ Redis connection successful")
        
        # Initialize cache service
        cache_service = CacheService(redis_client)
        
        # Test 1: Refresh Token Storage
        logger.info("🔧 Testing refresh token storage...")
        test_user_id = "test_user_123"
        test_token = create_refresh_token(test_user_id)
        
        # Store token
        await cache_service.store_refresh_token(test_user_id, test_token)
        logger.info("✅ Refresh token stored successfully")
        
        # Retrieve token
        retrieved_token = await cache_service.get_refresh_token(test_user_id)
        assert retrieved_token == test_token, "Retrieved token doesn't match stored token"
        logger.info("✅ Refresh token retrieved successfully")
        
        # Test 2: Membership Caching
        logger.info("🔧 Testing membership caching...")
        test_membership = {
            "id": "membership_1",
            "user_id": test_user_id,
            "organization_id": "org_123",
            "organization_name": "Test Org",
            "organization_slug": "test-org",
            "role": "admin",
            "status": "active",
            "joined_at": datetime.now(timezone.utc).isoformat()
        }
        test_org_id = "org_123"
        
        # Cache membership for specific organization
        await cache_service.cache_user_memberships(test_user_id, test_org_id, test_membership)
        logger.info("✅ Membership cached successfully")
        
        # Retrieve cached membership
        cached_membership = await cache_service.get_cached_user_membership(test_user_id, test_org_id)
        assert cached_membership is not None, "Failed to retrieve cached membership"
        assert cached_membership["organization_name"] == "Test Org", "Cached data mismatch"
        logger.info("✅ Membership retrieved from cache successfully")
        
        # Test 3: Cache Invalidation
        logger.info("🔧 Testing cache invalidation...")
        
        # Invalidate refresh token
        result = await cache_service.revoke_refresh_token(test_user_id)
        assert result == True, "Failed to revoke refresh token"
        
        # Verify token is gone
        retrieved_token = await cache_service.get_refresh_token(test_user_id)
        assert retrieved_token is None, "Token should be None after revocation"
        logger.info("✅ Refresh token revocation successful")
        
        # Invalidate membership for specific organization
        result = await cache_service.invalidate_user_membership(test_user_id, test_org_id)
        assert result == True, "Failed to invalidate membership"
        
        # Verify membership is gone
        cached_membership = await cache_service.get_cached_user_membership(test_user_id, test_org_id)
        assert cached_membership is None, "Membership should be None after invalidation"
        logger.info("✅ Membership cache invalidation successful")
        
        logger.info("🎉 All Redis integration tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Always clean up Redis connection pool
        try:
            await close_redis_pool()
            logger.info("✅ Redis connection pool closed")
        except Exception as cleanup_error:
            logger.warning(f"⚠️ Error during cleanup: {cleanup_error}")

async def main():
    """Main test function."""
    logger.info("🚀 Starting Redis integration tests...")
    await test_redis_integration()
    logger.info("✅ All tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
