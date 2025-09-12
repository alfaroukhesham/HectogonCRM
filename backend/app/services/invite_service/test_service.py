# invite-service/test_service.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
from bson import ObjectId

from .service import InviteService
from .types import (
    InviteNotFoundError, InviteExpiredError, InviteRevokedError,
    InviteMaxUsesReachedError, EmailMismatchError, EmailDeliveryError,
    InvalidInviteDataError, InviteStatus
)
from .models import InviteCreate, InviteUpdate, Invite, InviteListResponse
from .constants import (
    INVITE_NOT_FOUND_ERROR, EMAIL_MISMATCH_ERROR, USER_NOT_FOUND_ERROR
)

@pytest.mark.asyncio
class TestInviteService:
    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.invites = AsyncMock()
        db.organizations = AsyncMock()
        db.users = AsyncMock()
        return db

    @pytest.fixture
    def mock_email_service(self):
        return AsyncMock()

    @pytest.fixture
    def invite_service(self, mock_db, mock_email_service):
        return InviteService(mock_db, mock_email_service)

    @pytest.fixture
    def sample_invite_create(self):
        return InviteCreate(
            organization_id=str(ObjectId()),
            target_role="editor",
            email="test@example.com",
            max_uses=1
        )

    async def test_create_invite_success(self, invite_service, mock_db, mock_email_service, sample_invite_create):
        """Test successful invite creation"""
        # Arrange
        invited_by = str(ObjectId())
        mock_db.invites.insert_one.return_value = AsyncMock(inserted_id=ObjectId())
        
        # Mock organization and user data for email
        mock_db.organizations.find_one.return_value = {
            "_id": ObjectId(sample_invite_create.organization_id),
            "name": "Test Org"
        }
        mock_db.users.find_one.return_value = {
            "_id": ObjectId(invited_by),
            "full_name": "John Doe"
        }

        # Act
        result = await invite_service.create_invite(sample_invite_create, invited_by)

        # Assert
        assert isinstance(result, Invite)
        assert result.organization_id == sample_invite_create.organization_id
        assert result.target_role == sample_invite_create.target_role
        assert result.email == sample_invite_create.email
        assert result.invited_by == invited_by
        assert result.code is not None
        mock_db.invites.insert_one.assert_called_once()
        mock_email_service.send_organization_invite.assert_called_once()

    async def test_create_invite_invalid_data(self, invite_service, sample_invite_create):
        """Test invite creation with invalid data"""
        # Arrange
        sample_invite_create.organization_id = ""  # Invalid
        invited_by = str(ObjectId())

        # Act & Assert
        with pytest.raises(InvalidInviteDataError):
            await invite_service.create_invite(sample_invite_create, invited_by)

    async def test_get_invite_by_code_success(self, invite_service, mock_db):
        """Test successful invite retrieval by code"""
        # Arrange
        invite_code = "test_code_123"
        invite_data = {
            "_id": ObjectId(),
            "code": invite_code,
            "organization_id": str(ObjectId()),
            "target_role": "editor",
            "email": "test@example.com",
            "status": "pending",
            "invited_by": str(ObjectId()),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
            "max_uses": 1,
            "current_uses": 0
        }
        mock_db.invites.find_one.return_value = invite_data

        # Act
        result = await invite_service.get_invite_by_code(invite_code)

        # Assert
        assert result is not None
        assert isinstance(result, Invite)
        assert result.code == invite_code
        assert result.target_role == "editor"

    async def test_get_invite_by_code_not_found(self, invite_service, mock_db):
        """Test invite retrieval when not found"""
        # Arrange
        invite_code = "nonexistent_code"
        mock_db.invites.find_one.return_value = None

        # Act
        result = await invite_service.get_invite_by_code(invite_code)

        # Assert
        assert result is None

    async def test_get_invite_by_id_success(self, invite_service, mock_db):
        """Test successful invite retrieval by ID"""
        # Arrange
        invite_id = str(ObjectId())
        invite_data = {
            "_id": ObjectId(invite_id),
            "code": "test_code",
            "organization_id": str(ObjectId()),
            "target_role": "viewer",
            "email": "test@example.com",
            "status": "pending",
            "invited_by": str(ObjectId()),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
            "max_uses": 1,
            "current_uses": 0
        }
        mock_db.invites.find_one.return_value = invite_data

        # Act
        result = await invite_service.get_invite_by_id(invite_id)

        # Assert
        assert result is not None
        assert isinstance(result, Invite)
        assert result.target_role == "viewer"

    async def test_update_invite_success(self, invite_service, mock_db):
        """Test successful invite update"""
        # Arrange
        invite_id = str(ObjectId())
        update_data = InviteUpdate(max_uses=5)
        
        mock_db.invites.update_one.return_value = AsyncMock(modified_count=1)
        updated_invite_data = {
            "_id": ObjectId(invite_id),
            "code": "test_code",
            "organization_id": str(ObjectId()),
            "target_role": "editor",
            "max_uses": 5,
            "current_uses": 0,
            "status": "pending",
            "invited_by": str(ObjectId()),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=7)
        }
        mock_db.invites.find_one.return_value = updated_invite_data

        # Act
        result = await invite_service.update_invite(invite_id, update_data)

        # Assert
        assert result is not None
        assert isinstance(result, Invite)
        assert result.max_uses == 5
        mock_db.invites.update_one.assert_called_once()

    async def test_revoke_invite_success(self, invite_service, mock_db):
        """Test successful invite revocation"""
        # Arrange
        invite_id = str(ObjectId())
        revoked_by = str(ObjectId())
        reason = "No longer needed"
        
        mock_db.invites.update_one.return_value = AsyncMock(modified_count=1)
        revoked_invite_data = {
            "_id": ObjectId(invite_id),
            "code": "test_code",
            "organization_id": str(ObjectId()),
            "target_role": "editor",
            "status": "revoked",
            "revoked_by": revoked_by,
            "revoked_at": datetime.now(timezone.utc),
            "invited_by": str(ObjectId()),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
            "max_uses": 1,
            "current_uses": 0
        }
        mock_db.invites.find_one.return_value = revoked_invite_data

        # Act
        result = await invite_service.revoke_invite(invite_id, revoked_by, reason)

        # Assert
        assert result is not None
        assert isinstance(result, Invite)
        assert result.status == InviteStatus.REVOKED
        mock_db.invites.update_one.assert_called_once()

    async def test_accept_invite_success(self, invite_service, mock_db):
        """Test successful invite acceptance"""
        # Arrange
        invite_code = "valid_code"
        user_id = str(ObjectId())
        org_id = str(ObjectId())
        
        # Mock invite data
        invite_data = {
            "_id": ObjectId(),
            "code": invite_code,
            "organization_id": org_id,
            "target_role": "editor",
            "email": "user@example.com",
            "status": "pending",
            "invited_by": str(ObjectId()),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
            "max_uses": 1,
            "current_uses": 0
        }
        mock_db.invites.find_one.return_value = invite_data
        
        # Mock user data
        mock_db.users.find_one.return_value = {
            "_id": ObjectId(user_id),
            "email": "user@example.com"
        }
        
        # Mock membership service
        mock_db.invites.update_one.return_value = AsyncMock(modified_count=1)
        
        # Mock final invite retrieval
        accepted_invite_data = invite_data.copy()
        accepted_invite_data["status"] = "accepted"
        accepted_invite_data["used_by"] = user_id
        accepted_invite_data["current_uses"] = 1
        
        # Set up find_one to return different data on subsequent calls
        mock_db.invites.find_one.side_effect = [
            invite_data,  # First call for get_invite_by_code
            accepted_invite_data  # Second call for get_invite_by_id
        ]

        # Act
        result = await invite_service.accept_invite(invite_code, user_id)

        # Assert
        assert result is not None
        assert isinstance(result, Invite)
        mock_db.invites.update_one.assert_called_once()

    async def test_accept_invite_not_found(self, invite_service, mock_db):
        """Test invite acceptance when invite not found"""
        # Arrange
        invite_code = "nonexistent_code"
        user_id = str(ObjectId())
        mock_db.invites.find_one.return_value = None

        # Act & Assert
        with pytest.raises(InviteNotFoundError, match=INVITE_NOT_FOUND_ERROR):
            await invite_service.accept_invite(invite_code, user_id)

    async def test_accept_invite_expired(self, invite_service, mock_db):
        """Test invite acceptance when invite is expired"""
        # Arrange
        invite_code = "expired_code"
        user_id = str(ObjectId())
        
        expired_invite_data = {
            "_id": ObjectId(),
            "code": invite_code,
            "organization_id": str(ObjectId()),
            "target_role": "editor",
            "status": "pending",
            "invited_by": str(ObjectId()),
            "created_at": datetime.now(timezone.utc) - timedelta(days=8),
            "updated_at": datetime.now(timezone.utc) - timedelta(days=8),
            "expires_at": datetime.now(timezone.utc) - timedelta(days=1),  # Expired
            "max_uses": 1,
            "current_uses": 0
        }
        mock_db.invites.find_one.return_value = expired_invite_data

        # Act & Assert
        with pytest.raises(InviteExpiredError):
            await invite_service.accept_invite(invite_code, user_id)

    async def test_accept_invite_email_mismatch(self, invite_service, mock_db):
        """Test invite acceptance with email mismatch"""
        # Arrange
        invite_code = "code_with_email"
        user_id = str(ObjectId())
        
        invite_data = {
            "_id": ObjectId(),
            "code": invite_code,
            "organization_id": str(ObjectId()),
            "target_role": "editor",
            "email": "specific@example.com",  # Specific email required
            "status": "pending",
            "invited_by": str(ObjectId()),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
            "max_uses": 1,
            "current_uses": 0
        }
        mock_db.invites.find_one.return_value = invite_data
        
        # User with different email
        mock_db.users.find_one.return_value = {
            "_id": ObjectId(user_id),
            "email": "different@example.com"
        }

        # Act & Assert
        with pytest.raises(EmailMismatchError, match=EMAIL_MISMATCH_ERROR):
            await invite_service.accept_invite(invite_code, user_id)

    async def test_cleanup_expired_invites_success(self, invite_service, mock_db):
        """Test successful cleanup of expired invites"""
        # Arrange
        mock_db.invites.update_many.return_value = AsyncMock(modified_count=5)

        # Act
        result = await invite_service.cleanup_expired_invites()

        # Assert
        assert result == 5
        mock_db.invites.update_many.assert_called_once()

    async def test_validate_invite_valid(self, invite_service, mock_db):
        """Test invite validation for valid invite"""
        # Arrange
        invite_code = "valid_code"
        org_id = str(ObjectId())
        
        invite_data = {
            "_id": ObjectId(),
            "code": invite_code,
            "organization_id": org_id,
            "target_role": "editor",
            "status": "pending",
            "invited_by": str(ObjectId()),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
            "max_uses": 1,
            "current_uses": 0
        }
        mock_db.invites.find_one.return_value = invite_data
        mock_db.organizations.find_one.return_value = {
            "_id": ObjectId(org_id),
            "name": "Test Organization"
        }

        # Act
        result = await invite_service.validate_invite(invite_code)

        # Assert
        assert result["is_valid"] is True
        assert result["code"] == invite_code
        assert result["status"] == "valid"
        assert result["organization_name"] == "Test Organization"
        assert result["target_role"] == "editor"

    async def test_validate_invite_not_found(self, invite_service, mock_db):
        """Test invite validation for non-existent invite"""
        # Arrange
        invite_code = "nonexistent_code"
        mock_db.invites.find_one.return_value = None

        # Act
        result = await invite_service.validate_invite(invite_code)

        # Assert
        assert result["is_valid"] is False
        assert result["code"] == invite_code
        assert result["status"] == "not_found"
        assert INVITE_NOT_FOUND_ERROR in result["message"]

    async def test_get_invite_stats_success(self, invite_service, mock_db):
        """Test getting invite statistics"""
        # Arrange
        stats_data = [
            {"_id": "pending", "count": 10},
            {"_id": "accepted", "count": 5},
            {"_id": "revoked", "count": 2},
            {"_id": "expired", "count": 3}
        ]
        
        mock_cursor = AsyncMock()
        async def _aiter():
            for doc in stats_data:
                yield doc
        mock_cursor.__aiter__.return_value = _aiter()
        mock_db.invites.aggregate.return_value = mock_cursor        # Act
        result = await invite_service.get_invite_stats()

        # Assert
        assert result["total_invites"] == 20
        assert result["pending_invites"] == 10
        assert result["accepted_invites"] == 5
        assert result["revoked_invites"] == 2
        assert result["expired_invites"] == 3

    async def test_resend_invite_email_success(self, invite_service, mock_db, mock_email_service):
        """Test successful invite email resend"""
        # Arrange
        invite_id = str(ObjectId())
        org_id = str(ObjectId())
        inviter_id = str(ObjectId())
        
        invite_data = {
            "_id": ObjectId(invite_id),
            "code": "resend_code",
            "organization_id": org_id,
            "target_role": "editor",
            "email": "user@example.com",
            "status": "pending",
            "invited_by": inviter_id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
            "max_uses": 1,
            "current_uses": 0
        }
        
        mock_db.invites.find_one.return_value = invite_data
        mock_db.organizations.find_one.return_value = {
            "_id": ObjectId(org_id),
            "name": "Test Org"
        }
        mock_db.users.find_one.return_value = {
            "_id": ObjectId(inviter_id),
            "full_name": "John Doe"
        }

        # Act
        result = await invite_service.resend_invite_email(invite_id)

        # Assert
        assert result is True
        mock_email_service.send_organization_invite.assert_called_once()

    async def test_resend_invite_email_no_email(self, invite_service, mock_db):
        """Test invite email resend when invite has no email"""
        # Arrange
        invite_id = str(ObjectId())
        
        invite_data = {
            "_id": ObjectId(invite_id),
            "code": "no_email_code",
            "organization_id": str(ObjectId()),
            "target_role": "editor",
            "email": None,  # No email address
            "status": "pending",
            "invited_by": str(ObjectId()),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
            "max_uses": 1,
            "current_uses": 0
        }
        
        mock_db.invites.find_one.return_value = invite_data

        # Act
        result = await invite_service.resend_invite_email(invite_id)

        # Assert
        assert result is False
