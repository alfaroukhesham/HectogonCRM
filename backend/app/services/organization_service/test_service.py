# organization-service/test_service.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from bson import ObjectId

from .service import OrganizationService
from .types import (
    SlugExistsError, OrganizationNotFoundError, InvalidOrganizationDataError,
    InvalidSlugError
)
from .models import OrganizationCreate, OrganizationUpdate, Organization
from .constants import (
    ORG_NAME_REQUIRED_ERROR, ORG_SLUG_REQUIRED_ERROR, INVALID_SLUG_FORMAT_ERROR,
    SLUG_TOO_LONG_ERROR, CREATED_BY_REQUIRED_ERROR, SLUG_EXISTS_ERROR
)

@pytest.mark.asyncio
class TestOrganizationService:
    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.organizations = AsyncMock()
        db.memberships = AsyncMock()
        db.client = AsyncMock()
        return db

    @pytest.fixture
    def organization_service(self, mock_db):
        return OrganizationService(mock_db)

    @pytest.fixture
    def sample_organization_create(self):
        return OrganizationCreate(
            name="Test Organization",
            slug="test-org",
            description="A test organization"
        )

    async def test_create_organization_success(self, organization_service, mock_db, sample_organization_create):
        """Test successful organization creation"""
        # Arrange
        created_by = str(ObjectId())
        mock_db.organizations.find_one.return_value = None  # Slug available
        mock_db.organizations.insert_one.return_value = AsyncMock(inserted_id=ObjectId())

        # Act
        result = await organization_service.create_organization(sample_organization_create, created_by)

        # Assert
        assert isinstance(result, Organization)
        assert result.name == sample_organization_create.name
        assert result.slug == sample_organization_create.slug
        assert result.created_by == created_by
        mock_db.organizations.insert_one.assert_called_once()

    async def test_create_organization_empty_name(self, organization_service, sample_organization_create):
        """Test organization creation with empty name"""
        # Arrange
        invalid_org_data = OrganizationCreate(
            name="",
            slug=sample_organization_create.slug,
            description=sample_organization_create.description
        )
        created_by = str(ObjectId())

        # Act & Assert
        with pytest.raises(InvalidOrganizationDataError, match=ORG_NAME_REQUIRED_ERROR):
            await organization_service.create_organization(invalid_org_data, created_by)

    async def test_create_organization_empty_slug(self, organization_service, sample_organization_create):
        """Test organization creation with empty slug"""
        # Arrange
        invalid_org_data = OrganizationCreate(
            name=sample_organization_create.name,
            slug="",
            description=sample_organization_create.description
        )
        created_by = str(ObjectId())

        # Act & Assert
        with pytest.raises(InvalidOrganizationDataError, match=ORG_SLUG_REQUIRED_ERROR):
            await organization_service.create_organization(invalid_org_data, created_by)

    async def test_create_organization_invalid_slug_format(self, organization_service, sample_organization_create):
        """Test organization creation with invalid slug format"""
        # Arrange
        invalid_org_data = OrganizationCreate(
            name=sample_organization_create.name,
            slug="invalid_slug_with_underscores!",
            description=sample_organization_create.description
        )
        created_by = str(ObjectId())

        # Act & Assert
        with pytest.raises(InvalidSlugError, match=INVALID_SLUG_FORMAT_ERROR):
            await organization_service.create_organization(invalid_org_data, created_by)

    async def test_create_organization_slug_too_long(self, organization_service, sample_organization_create):
        """Test organization creation with slug too long"""
        # Arrange
        invalid_org_data = OrganizationCreate(
            name=sample_organization_create.name,
            slug="a" * 85,  # Exceeds 80 character limit
            description=sample_organization_create.description
        )
        created_by = str(ObjectId())

        # Act & Assert
        with pytest.raises(InvalidSlugError, match=SLUG_TOO_LONG_ERROR):
            await organization_service.create_organization(invalid_org_data, created_by)

    async def test_create_organization_empty_created_by(self, organization_service, sample_organization_create):
        """Test organization creation with empty created_by"""
        # Arrange
        created_by = ""

        # Act & Assert
        with pytest.raises(InvalidOrganizationDataError, match=CREATED_BY_REQUIRED_ERROR):
            await organization_service.create_organization(sample_organization_create, created_by)

    async def test_create_organization_slug_exists(self, organization_service, mock_db, sample_organization_create):
        """Test organization creation when slug already exists"""
        # Arrange
        created_by = str(ObjectId())
        mock_db.organizations.find_one.return_value = {"slug": sample_organization_create.slug}

        # Act & Assert
        with pytest.raises(SlugExistsError):
            await organization_service.create_organization(sample_organization_create, created_by)

    async def test_get_organization_success(self, organization_service, mock_db):
        """Test successful organization retrieval by ID"""
        # Arrange
        org_id = str(ObjectId())
        org_data = {
            "_id": ObjectId(org_id),
            "name": "Test Org",
            "slug": "test-org",
            "created_by": str(ObjectId()),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        mock_db.organizations.find_one.return_value = org_data

        # Act
        result = await organization_service.get_organization(org_id)

        # Assert
        assert result is not None
        assert isinstance(result, Organization)
        assert result.name == org_data["name"]
        assert result.slug == org_data["slug"]

    async def test_get_organization_not_found(self, organization_service, mock_db):
        """Test organization retrieval when not found"""
        # Arrange
        org_id = str(ObjectId())
        mock_db.organizations.find_one.return_value = None

        # Act
        result = await organization_service.get_organization(org_id)

        # Assert
        assert result is None

    async def test_get_organization_by_slug_success(self, organization_service, mock_db):
        """Test successful organization retrieval by slug"""
        # Arrange
        slug = "test-org"
        org_data = {
            "_id": ObjectId(),
            "name": "Test Org",
            "slug": slug,
            "created_by": str(ObjectId()),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        mock_db.organizations.find_one.return_value = org_data

        # Act
        result = await organization_service.get_organization_by_slug(slug)

        # Assert
        assert result is not None
        assert isinstance(result, Organization)
        assert result.slug == slug

    async def test_update_organization_success(self, organization_service, mock_db):
        """Test successful organization update"""
        # Arrange
        org_id = str(ObjectId())
        update_data = OrganizationUpdate(name="Updated Name")
        
        mock_db.organizations.update_one.return_value = AsyncMock(modified_count=1)
        updated_org_data = {
            "_id": ObjectId(org_id),
            "name": "Updated Name",
            "slug": "test-org",
            "created_by": str(ObjectId()),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        mock_db.organizations.find_one.return_value = updated_org_data

        # Act
        result = await organization_service.update_organization(org_id, update_data)

        # Assert
        assert result is not None
        assert isinstance(result, Organization)
        assert result.name == "Updated Name"
        mock_db.organizations.update_one.assert_called_once()

    async def test_update_organization_no_changes(self, organization_service, mock_db):
        """Test organization update with no actual changes"""
        # Arrange
        org_id = str(ObjectId())
        update_data = OrganizationUpdate()  # No fields set
        
        original_org_data = {
            "_id": ObjectId(org_id),
            "name": "Test Org",
            "slug": "test-org",
            "created_by": str(ObjectId()),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        mock_db.organizations.find_one.return_value = original_org_data

        # Act
        result = await organization_service.update_organization(org_id, update_data)

        # Assert
        assert result is not None
        assert isinstance(result, Organization)
        # Should call find_one to get current org since no updates
        mock_db.organizations.find_one.assert_called()

    async def test_delete_organization_success(self, organization_service, mock_db):
        """Test successful organization deletion"""
        # Arrange
        org_id = str(ObjectId())
        
        # Mock session and transaction
        mock_session = AsyncMock()
        mock_transaction = AsyncMock()
        mock_session.start_transaction.return_value = mock_transaction
        mock_db.client.start_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.client.start_session.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_db.organizations.delete_one.return_value = AsyncMock(deleted_count=1)
        mock_db.memberships.delete_many.return_value = AsyncMock(deleted_count=3)

        # Act
        result = await organization_service.delete_organization(org_id)

        # Assert
        assert result is True

    async def test_list_organizations_success(self, organization_service, mock_db):
        """Test successful organization listing"""
        # Arrange
        org_data_list = [
            {
                "_id": ObjectId(),
                "name": "Org 1",
                "slug": "org-1",
                "created_by": str(ObjectId()),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "_id": ObjectId(),
                "name": "Org 2", 
                "slug": "org-2",
                "created_by": str(ObjectId()),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
        
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__ = AsyncMock(return_value=iter(org_data_list))
        mock_db.organizations.find.return_value.skip.return_value.limit.return_value = mock_cursor

        # Act
        result = await organization_service.list_organizations()

        # Assert
        assert len(result) == 2
        assert all(isinstance(org, Organization) for org in result)
        assert result[0].name == "Org 1"
        assert result[1].name == "Org 2"

    async def test_create_default_organization_success(self, organization_service, mock_db):
        """Test successful default organization creation"""
        # Arrange
        user_id = str(ObjectId())
        user_name = "John Doe"
        
        mock_db.organizations.find_one.return_value = None  # Slug available
        mock_db.organizations.insert_one.return_value = AsyncMock(inserted_id=ObjectId())

        # Act
        result = await organization_service.create_default_organization(user_id, user_name)

        # Assert
        assert isinstance(result, Organization)
        assert "John Doe's Organization" in result.name
        assert result.created_by == user_id
        mock_db.organizations.insert_one.assert_called_once()

    async def test_create_default_organization_empty_user_id(self, organization_service):
        """Test default organization creation with empty user ID"""
        # Arrange
        user_id = ""
        user_name = "John Doe"

        # Act & Assert
        with pytest.raises(InvalidOrganizationDataError):
            await organization_service.create_default_organization(user_id, user_name)

    async def test_check_slug_availability_available(self, organization_service, mock_db):
        """Test slug availability check when slug is available"""
        # Arrange
        slug = "available-slug"
        mock_db.organizations.find_one.return_value = None

        # Act
        result = await organization_service.check_slug_availability(slug)

        # Assert
        assert result is True

    async def test_check_slug_availability_taken(self, organization_service, mock_db):
        """Test slug availability check when slug is taken"""
        # Arrange
        slug = "taken-slug"
        mock_db.organizations.find_one.return_value = {"slug": slug}

        # Act
        result = await organization_service.check_slug_availability(slug)

        # Assert
        assert result is False

    async def test_get_user_organizations_success(self, organization_service, mock_db):
        """Test getting organizations for a user"""
        # Arrange
        user_id = str(ObjectId())
        org_id_1 = str(ObjectId())
        org_id_2 = str(ObjectId())
        
        # Mock membership data
        membership_data = [
            {"organization_id": org_id_1},
            {"organization_id": org_id_2}
        ]
        mock_membership_cursor = AsyncMock()
        mock_membership_cursor.__aiter__ = AsyncMock(return_value=iter(membership_data))
        mock_db.memberships.find.return_value = mock_membership_cursor
        
        # Mock organization data
        org_data_list = [
            {
                "_id": ObjectId(org_id_1),
                "name": "Org 1",
                "slug": "org-1",
                "created_by": user_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "_id": ObjectId(org_id_2),
                "name": "Org 2",
                "slug": "org-2", 
                "created_by": user_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
        mock_org_cursor = AsyncMock()
        mock_org_cursor.__aiter__ = AsyncMock(return_value=iter(org_data_list))
        mock_db.organizations.find.return_value = mock_org_cursor

        # Act
        result = await organization_service.get_user_organizations(user_id)

        # Assert
        assert len(result) == 2
        assert all(isinstance(org, Organization) for org in result)
        assert result[0].name == "Org 1"
        assert result[1].name == "Org 2"
