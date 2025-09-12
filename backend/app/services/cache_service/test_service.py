# cache-service/test_service.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from .service import CacheService
from .types import CacheResult, TokenCleanupStats
from .models import CacheEntry, OAuthStateData
from .utils import serialize_data, deserialize_data

@pytest.mark.asyncio
class TestCacheService:
    @pytest.fixture
    def mock_redis(self):
        return AsyncMock()

    @pytest.fixture
    def cache_service(self, mock_redis):
        return CacheService(mock_redis)

    def async_iterable(self, items):
        """Helper to create async iterable from items list"""
        async def _gen():
            for i in items:
                yield i
        return _gen()

    async def test_store_refresh_token_success(self, cache_service, mock_redis):
        """Test successful refresh token storage"""
        # Arrange
        mock_redis.set.return_value = True
        user_id = "test_user_123"
        token = "test_refresh_token"

        # Act
        result = await cache_service.store_refresh_token(user_id, token)

        # Assert
        assert result is True
        mock_redis.set.assert_called_once()
        args, kwargs = mock_redis.set.call_args
        assert f"refresh_token:{user_id}" in args[0]

    async def test_get_refresh_token_success(self, cache_service, mock_redis):
        """Test successful refresh token retrieval"""
        # Arrange
        expected_token = "test_refresh_token"
        mock_redis.get.return_value = expected_token.encode('utf-8')
        user_id = "test_user_123"

        # Act
        result = await cache_service.get_refresh_token(user_id)

        # Assert
        assert result == expected_token
        mock_redis.get.assert_called_once()

    async def test_revoke_refresh_token_success(self, cache_service, mock_redis):
        """Test successful refresh token revocation"""
        # Arrange
        mock_redis.delete.return_value = 1
        user_id = "test_user_123"

        # Act
        result = await cache_service.revoke_refresh_token(user_id)

        # Assert
        assert result is True
        mock_redis.delete.assert_called_once()

    async def test_cache_user_memberships_success(self, cache_service, mock_redis):
        """Test successful membership caching"""
        # Arrange
        mock_redis.set.return_value = True
        user_id = "user123"
        org_id = "org456" 
        membership_data = {"role": "admin", "status": "active"}

        # Act
        result = await cache_service.cache_user_memberships(user_id, org_id, membership_data)

        # Assert
        assert result is True
        mock_redis.set.assert_called_once()

    async def test_get_cached_user_membership_success(self, cache_service, mock_redis):
        """Test successful membership retrieval"""
        # Arrange
        membership_data = {"role": "admin", "status": "active"}
        mock_redis.get.return_value = serialize_data(membership_data).encode('utf-8')
        user_id = "user123"
        org_id = "org456"

        # Act
        result = await cache_service.get_cached_user_membership(user_id, org_id)

        # Assert
        assert result == membership_data
        mock_redis.get.assert_called_once()

    async def test_invalidate_user_membership_success(self, cache_service, mock_redis):
        """Test successful membership invalidation"""
        # Arrange
        mock_redis.delete.return_value = 1
        user_id = "user123"
        org_id = "org456"

        # Act
        result = await cache_service.invalidate_user_membership(user_id, org_id)

        # Assert
        assert result is True
        mock_redis.delete.assert_called_once()

    async def test_store_oauth_state_success(self, cache_service, mock_redis):
        """Test OAuth state storage"""
        # Arrange
        mock_redis.set.return_value = True
        state = "test_state"
        provider = "google"
        redirect_uri = "http://localhost:3000/callback"

        # Act
        result = await cache_service.store_oauth_state(state, provider, redirect_uri)

        # Assert
        assert result is True
        mock_redis.set.assert_called_once()

    async def test_get_oauth_state_success(self, cache_service, mock_redis):
        """Test OAuth state retrieval with GETDEL"""
        # Arrange
        state_data = {
            "provider": "google",
            "redirect_uri": "http://localhost:3000/callback",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        mock_redis.execute_command.return_value = serialize_data(state_data).encode('utf-8')
        state = "test_state"

        # Act
        result = await cache_service.get_oauth_state(state)

        # Assert
        assert result == state_data
        mock_redis.execute_command.assert_called_once_with("GETDEL", f"oauth_state:{state}")

    async def test_blacklist_token_jti_success(self, cache_service, mock_redis):
        """Test JTI token blacklisting"""
        # Arrange
        mock_redis.set.return_value = True
        jti = "test_jti_123"
        ttl_seconds = 3600

        # Act
        result = await cache_service.blacklist_token_jti(jti, ttl_seconds)

        # Assert
        assert result is True
        mock_redis.set.assert_called_once()

    async def test_is_token_blacklisted_true(self, cache_service, mock_redis):
        """Test checking if token is blacklisted - positive case"""
        # Arrange
        mock_redis.get.return_value = b"revoked"
        jti = "test_jti_123"

        # Act
        result = await cache_service.is_token_blacklisted(jti)

        # Assert
        assert result is True
        mock_redis.get.assert_called_once()

    async def test_is_token_blacklisted_false(self, cache_service, mock_redis):
        """Test checking if token is blacklisted - negative case"""
        # Arrange
        mock_redis.get.return_value = None
        jti = "test_jti_123"

        # Act
        result = await cache_service.is_token_blacklisted(jti)

        # Assert
        assert result is False
        mock_redis.get.assert_called_once()

    async def test_redis_failure_graceful_fallback(self, cache_service, mock_redis):
        """Test graceful handling of Redis failures"""
        # Arrange
        mock_redis.get.side_effect = Exception("Redis connection failed")
        user_id = "user123"

        # Act
        result = await cache_service.get_refresh_token(user_id)

        # Assert
        assert result is None  # Should return fallback value

    async def test_cleanup_expired_tokens_success(self, cache_service, mock_redis):
        """Test token cleanup operation"""
        # Arrange
        mock_redis.scan_iter.return_value = AsyncMock()
        mock_redis.scan_iter.return_value.__aiter__.return_value = self.async_iterable([])

        # Act
        result = await cache_service.cleanup_expired_tokens()

        # Assert
        assert isinstance(result, dict)
        assert "refresh_token" in result

    async def test_dashboard_stats_caching(self, cache_service, mock_redis):
        """Test dashboard stats caching operations"""
        # Arrange
        mock_redis.set.return_value = True
        mock_redis.get.return_value = serialize_data({"users": 10, "active": 5}).encode('utf-8')
        mock_redis.delete.return_value = 1
        org_id = "org123"
        stats_data = {"users": 10, "active": 5}

        # Act & Assert - Cache
        cache_result = await cache_service.cache_dashboard_stats(org_id, stats_data)
        assert cache_result is True

        # Act & Assert - Retrieve
        get_result = await cache_service.get_cached_dashboard_stats(org_id)
        assert get_result == stats_data

        # Act & Assert - Invalidate
        await cache_service.invalidate_dashboard_stats(org_id)
        mock_redis.delete.assert_called_once()

    async def test_invalidate_organization_members_cache(self, cache_service, mock_redis):
        """Test organization-wide cache invalidation"""
        # Arrange
        mock_keys = [b'user_memberships:org123:user1', b'user_memberships:org123:user2']
        mock_redis.scan_iter.return_value = AsyncMock()
        mock_redis.scan_iter.return_value.__aiter__.return_value = self.async_iterable(mock_keys)
        mock_redis.delete.return_value = len(mock_keys)
        org_id = "org123"

        # Act
        result = await cache_service.invalidate_organization_members_cache(org_id)

        # Assert
        assert result == len(mock_keys)
        mock_redis.delete.assert_called_once_with(*mock_keys)
