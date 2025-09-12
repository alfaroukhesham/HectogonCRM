# backend/app/services/membership_service/test_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from bson import ObjectId

from .service import MembershipService
from .types import (
    UserNotFoundError, OrganizationNotFoundError, DuplicateMembershipError,
    MembershipRole, MembershipStatus
)
from .models import (
    MembershipCreate, MembershipUpdate, Membership,
    OrganizationMembershipResponse, UserMembershipResponse
)

class TestMembershipService:
    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.memberships = AsyncMock()
        db.users = AsyncMock()
        db.organizations = AsyncMock()
        return db

    @pytest.fixture
    def mock_cache_service(self):
        return AsyncMock()

    @pytest.fixture
    def membership_service(self, mock_db, mock_cache_service):
        return MembershipService(mock_db, mock_cache_service)

    @pytest.fixture
    def sample_membership_create(self):
        return MembershipCreate(
            user_id=str(ObjectId()),
            organization_id=str(ObjectId()),
            role=MembershipRole.EDITOR,
            status=MembershipStatus.ACTIVE
        )

    @pytest.mark.asyncio
    async def test_create_membership_success(self, membership_service, mock_db, sample_membership_create):
        """Test successful membership creation"""
        # Arrange
        mock_db.users.find_one.return_value = {"_id": ObjectId(sample_membership_create.user_id)}
        mock_db.organizations.find_one.return_value = {"_id": ObjectId(sample_membership_create.organization_id)}
        mock_db.memberships.find_one.return_value = None  # No existing membership
        mock_db.memberships.insert_one.return_value = AsyncMock(inserted_id=ObjectId())

        # Act
        result = await membership_service.create_membership(sample_membership_create)

        # Assert
        assert isinstance(result, Membership)
        assert result.user_id == sample_membership_create.user_id
        assert result.organization_id == sample_membership_create.organization_id
        assert result.role == sample_membership_create.role
        mock_db.memberships.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_membership_user_not_found(self, membership_service, mock_db, sample_membership_create):
        """Test membership creation with non-existent user"""
        # Arrange
        mock_db.users.find_one.return_value = None

        # Act & Assert
        with pytest.raises(UserNotFoundError):
            await membership_service.create_membership(sample_membership_create)

    @pytest.mark.asyncio
    async def test_create_membership_organization_not_found(self, membership_service, mock_db, sample_membership_create):
        """Test membership creation with non-existent organization"""
        # Arrange
        mock_db.users.find_one.return_value = {"_id": ObjectId(sample_membership_create.user_id)}
        mock_db.organizations.find_one.return_value = None

        # Act & Assert
        with pytest.raises(OrganizationNotFoundError):
            await membership_service.create_membership(sample_membership_create)

    @pytest.mark.asyncio
    async def test_create_membership_already_exists(self, membership_service, mock_db, sample_membership_create):
        """Test membership creation when user is already a member"""
        # Arrange
        mock_db.users.find_one.return_value = {"_id": ObjectId(sample_membership_create.user_id)}
        mock_db.organizations.find_one.return_value = {"_id": ObjectId(sample_membership_create.organization_id)}
        mock_db.memberships.find_one.return_value = {"_id": ObjectId()}  # Existing membership

        # Act & Assert
        with pytest.raises(DuplicateMembershipError):
            await membership_service.create_membership(sample_membership_create)

    @pytest.mark.asyncio
    async def test_get_membership_from_cache(self, membership_service, mock_cache_service):
        """Test getting membership from cache"""
        # Arrange
        user_id = str(ObjectId())
        org_id = str(ObjectId())
        cached_data = {
            "id": str(ObjectId()),
            "user_id": user_id,
            "organization_id": org_id,
            "role": "editor",
            "status": "active"
        }
        mock_cache_service.get_cached_user_membership.return_value = cached_data

        # Act
        result = await membership_service.get_membership(user_id, org_id)

        # Assert
        assert result is not None
        assert isinstance(result, Membership)
        assert result.user_id == user_id
        assert result.organization_id == org_id
        mock_cache_service.get_cached_user_membership.assert_called_once_with(user_id, org_id)

    @pytest.mark.asyncio
    async def test_get_membership_from_database(self, membership_service, mock_db, mock_cache_service):
        """Test getting membership from database when cache misses"""
        # Arrange
        user_id = str(ObjectId())
        org_id = str(ObjectId())
        membership_id = ObjectId()
        
        mock_cache_service.get_cached_user_membership.return_value = None
        mock_db.memberships.find_one.return_value = {
            "_id": membership_id,
            "user_id": user_id,
            "organization_id": org_id,
            "role": "editor",
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        # Act
        result = await membership_service.get_membership(user_id, org_id)

        # Assert
        assert result is not None
        assert isinstance(result, Membership)
        assert result.user_id == user_id
        assert result.organization_id == org_id
        mock_db.memberships.find_one.assert_called_once()
        mock_cache_service.cache_user_memberships.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_membership_by_id_success(self, membership_service, mock_db):
        """Test getting membership by ID"""
        # Arrange
        membership_id = str(ObjectId())
        user_id = str(ObjectId())
        org_id = str(ObjectId())
        
        mock_db.memberships.find_one.return_value = {
            "_id": ObjectId(membership_id),
            "user_id": user_id,
            "organization_id": org_id,
            "role": "admin",
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        # Act
        result = await membership_service.get_membership_by_id(membership_id)

        # Assert
        assert result is not None
        assert isinstance(result, Membership)
        assert result.user_id == user_id
        assert result.role == MembershipRole.ADMIN

    @pytest.mark.asyncio
    async def test_update_membership_success(self, membership_service, mock_db):
        """Test successful membership update"""
        # Arrange
        membership_id = str(ObjectId())
        update_data = MembershipUpdate(role=MembershipRole.ADMIN)

        mock_db.memberships.update_one.return_value = MagicMock(modified_count=1)
        mock_db.memberships.find_one.return_value = {
            "_id": ObjectId(membership_id),
            "user_id": str(ObjectId()),
            "organization_id": str(ObjectId()),
            "role": "admin",
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        # Act
        result = await membership_service.update_membership(membership_id, update_data)

        # Assert
        assert result is not None
        assert isinstance(result, Membership)
        assert result.role == MembershipRole.ADMIN
        mock_db.memberships.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_membership_success(self, membership_service, mock_db, mock_cache_service):
        """Test successful membership deletion"""
        # Arrange
        membership_id = str(ObjectId())
        user_id = str(ObjectId())
        org_id = str(ObjectId())

        # Mock getting membership before deletion
        mock_db.memberships.find_one.return_value = {
            "_id": ObjectId(membership_id),
            "user_id": user_id,
            "organization_id": org_id,
            "role": "editor",
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        mock_db.memberships.delete_one.return_value = MagicMock(deleted_count=1)

        # Act
        result = await membership_service.delete_membership(membership_id)

        # Assert
        assert result is True
        mock_db.memberships.delete_one.assert_called_once()

        # Assert cache invalidation was called with correct keys
        mock_cache_service.invalidate_user_membership.assert_called_once_with(user_id, org_id)

    @pytest.mark.asyncio
    async def test_check_user_role_success(self, membership_service, mock_db, mock_cache_service):
        """Test checking user role in organization"""
        # Arrange
        user_id = str(ObjectId())
        org_id = str(ObjectId())
        
        mock_cache_service.get_cached_user_membership.return_value = None
        mock_db.memberships.find_one.return_value = {
            "_id": ObjectId(),
            "user_id": user_id,
            "organization_id": org_id,
            "role": "admin",
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        # Act
        result = await membership_service.check_user_role(user_id, org_id)

        # Assert
        assert result == MembershipRole.ADMIN

    @pytest.mark.asyncio
    async def test_check_user_role_no_membership(self, membership_service, mock_db, mock_cache_service):
        """Test checking user role when no membership exists"""
        # Arrange
        user_id = str(ObjectId())
        org_id = str(ObjectId())
        
        mock_cache_service.get_cached_user_membership.return_value = None
        mock_db.memberships.find_one.return_value = None

        # Act
        result = await membership_service.check_user_role(user_id, org_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_has_permission_sufficient_role(self, membership_service, mock_db, mock_cache_service):
        """Test permission check with sufficient role"""
        # Arrange
        user_id = str(ObjectId())
        org_id = str(ObjectId())
        
        mock_cache_service.get_cached_user_membership.return_value = None
        mock_db.memberships.find_one.return_value = {
            "_id": ObjectId(),
            "user_id": user_id,
            "organization_id": org_id,
            "role": "admin",
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        # Act
        result = await membership_service.has_permission(user_id, org_id, MembershipRole.EDITOR)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_has_permission_insufficient_role(self, membership_service, mock_db, mock_cache_service):
        """Test permission check with insufficient role"""
        # Arrange
        user_id = str(ObjectId())
        org_id = str(ObjectId())
        
        mock_cache_service.get_cached_user_membership.return_value = None
        mock_db.memberships.find_one.return_value = {
            "_id": ObjectId(),
            "user_id": user_id,
            "organization_id": org_id,
            "role": "viewer",
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        # Act
        result = await membership_service.has_permission(user_id, org_id, MembershipRole.ADMIN)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_update_last_accessed(self, membership_service, mock_db, mock_cache_service):
        """Test updating last accessed timestamp"""
        # Arrange
        user_id = str(ObjectId())
        org_id = str(ObjectId())
        mock_db.memberships.update_one.return_value = MagicMock(modified_count=1)

        # Act
        await membership_service.update_last_accessed(user_id, org_id)

        # Assert
        mock_db.memberships.update_one.assert_called_once()
        mock_cache_service.invalidate_user_membership.assert_called_once_with(user_id, org_id)

    @pytest.mark.asyncio
    async def test_cache_error_handling(self, membership_service, mock_cache_service, mock_db):
        """Test graceful handling of cache errors"""
        # Arrange
        user_id = str(ObjectId())
        org_id = str(ObjectId())
        
        mock_cache_service.get_cached_user_membership.side_effect = Exception("Cache error")
        mock_db.memberships.find_one.return_value = {
            "_id": ObjectId(),
            "user_id": user_id,
            "organization_id": org_id,
            "role": "editor",
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        # Act
        result = await membership_service.get_membership(user_id, org_id)

        # Assert
        assert result is not None
        assert isinstance(result, Membership)
        # Should continue to database query despite cache error
