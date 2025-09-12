# invite-service/types.py

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from enum import Enum
from datetime import datetime

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase
    from app.core.email import EmailService

# Import invite models to re-export them
from app.models.invite import (
    Invite, InviteCreate, InviteUpdate, InviteResponse, InviteAccept,
    InviteRevoke, InviteListResponse, InviteStatus
)
from app.models.membership import MembershipRole, MembershipStatus

class InviteOperation(str, Enum):
    """Invite operations for logging and monitoring"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    ACCEPT = "accept"
    REVOKE = "revoke"
    LIST = "list"
    CLEANUP = "cleanup"
    RESEND_EMAIL = "resend_email"

class InviteValidationResult(str, Enum):
    """Result of invite validation"""
    VALID = "valid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    MAX_USES_REACHED = "max_uses_reached"
    EMAIL_MISMATCH = "email_mismatch"
    NOT_FOUND = "not_found"

class EmailDeliveryStatus(str, Enum):
    """Status of email delivery"""
    SENT = "sent"
    FAILED = "failed"
    PENDING = "pending"
    NOT_REQUIRED = "not_required"

# Type aliases for clarity
DatabaseType = "AsyncIOMotorDatabase"
EmailServiceType = "EmailService"
InviteDict = Dict[str, Any]
InviteList = List[Invite]
UserId = str
OrganizationId = str
InviteId = str
InviteCode = str
EmailAddress = str

# Service result types
class InviteResult:
    """Result object for invite operations"""
    def __init__(self, success: bool, data: Any = None, error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error

    def __bool__(self):
        return self.success

class InviteValidation:
    """Invite validation result with details"""
    def __init__(
        self, 
        is_valid: bool, 
        result: InviteValidationResult, 
        message: Optional[str] = None,
        invite: Optional[Invite] = None
    ):
        self.is_valid = is_valid
        self.result = result
        self.message = message
        self.invite = invite

# Error types for better error handling
class InviteError(Exception):
    """Base invite service error"""
    pass

class InviteNotFoundError(InviteError):
    """Invite not found error"""
    pass

class InviteExpiredError(InviteError):
    """Invite expired error"""
    pass

class InviteRevokedError(InviteError):
    """Invite revoked error"""
    pass

class InviteMaxUsesReachedError(InviteError):
    """Invite max uses reached error"""
    pass

class EmailMismatchError(InviteError):
    """Email mismatch error"""
    pass

class EmailDeliveryError(InviteError):
    """Email delivery error"""
    pass

class InvalidInviteDataError(InviteError):
    """Invalid invite data error"""
    pass

# Bulk operation types
class BulkInviteOperation:
    """Bulk operation for invites"""
    def __init__(self, operation: str, invites: List[Dict[str, Any]]):
        self.operation = operation
        self.invites = invites

# Search and filter types
class InviteFilters:
    """Filters for invite queries"""
    def __init__(
        self,
        organization_id: Optional[str] = None,
        status: Optional[InviteStatus] = None,
        email: Optional[str] = None,
        invited_by: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        expires_after: Optional[datetime] = None,
        expires_before: Optional[datetime] = None,
        include_expired: bool = False
    ):
        self.organization_id = organization_id
        self.status = status
        self.email = email
        self.invited_by = invited_by
        self.created_after = created_after
        self.created_before = created_before
        self.expires_after = expires_after
        self.expires_before = expires_before
        self.include_expired = include_expired

class InviteStats:
    """Statistics for invites"""
    def __init__(
        self,
        total_invites: int = 0,
        pending_invites: int = 0,
        accepted_invites: int = 0,
        revoked_invites: int = 0,
        expired_invites: int = 0,
        by_organization: Dict[str, int] = None,
        by_role: Dict[str, int] = None
    ):
        self.total_invites = total_invites
        self.pending_invites = pending_invites
        self.accepted_invites = accepted_invites
        self.revoked_invites = revoked_invites
        self.expired_invites = expired_invites
        self.by_organization = by_organization or {}
        self.by_role = by_role or {}

# Email context types
class EmailContext:
    """Context for sending invite emails"""
    def __init__(
        self,
        to_email: str,
        organization_name: str,
        inviter_name: str,
        invite_code: str,
        role: str,
        expires_at: datetime,
        organization_logo_url: Optional[str] = None
    ):
        self.to_email = to_email
        self.organization_name = organization_name
        self.inviter_name = inviter_name
        self.invite_code = invite_code
        self.role = role
        self.expires_at = expires_at
        self.organization_logo_url = organization_logo_url
