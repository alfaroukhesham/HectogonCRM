# invite-service/models.py

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# Re-export the main models from app.models for convenience
from app.models.invite import (
    Invite, InviteCreate, InviteUpdate, InviteResponse, InviteAccept,
    InviteRevoke, InviteListResponse, InviteStatus
)
from app.models.membership import MembershipRole, MembershipStatus

class InviteQuery(BaseModel):
    """Query parameters for invite operations"""
    code: Optional[str] = None
    organization_id: Optional[str] = None
    email: Optional[str] = None
    status: Optional[InviteStatus] = None

class InviteStats(BaseModel):
    """Statistics for invite operations"""
    total_invites: int = 0
    pending_invites: int = 0
    accepted_invites: int = 0
    revoked_invites: int = 0
    expired_invites: int = 0
    by_organization: Dict[str, int] = Field(default_factory=dict)
    by_role: Dict[str, int] = Field(default_factory=dict)

class InviteBulkOperation(BaseModel):
    """Bulk operation request for invites"""
    operation: str  # create, revoke, cleanup
    invites: List[Dict[str, Any]]

class InviteSearchFilters(BaseModel):
    """Advanced search filters for invites"""
    organization_id: Optional[str] = None
    status: Optional[InviteStatus] = None
    email_contains: Optional[str] = None
    invited_by: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    expires_after: Optional[datetime] = None
    expires_before: Optional[datetime] = None
    role: Optional[MembershipRole] = None
    include_expired: bool = False

class InviteCreationRequest(BaseModel):
    """Enhanced invite creation request"""
    organization_id: str
    target_role: MembershipRole
    email: Optional[str] = None
    max_uses: Optional[int] = 1
    expires_hours: Optional[int] = 168  # 7 days default
    send_email: bool = True
    custom_message: Optional[str] = None
    
    @validator('max_uses')
    def max_uses_must_be_positive(cls, v):
        if v is not None and (not isinstance(v, int) or v <= 0):
            raise ValueError('Max uses must be a positive integer')
        return v
    
    @validator('expires_hours')
    def expires_hours_must_be_positive(cls, v):
        if v is not None and (not isinstance(v, int) or v <= 0):
            raise ValueError('Expires hours must be a positive integer')
        return v

class InviteAcceptanceRequest(BaseModel):
    """Request for accepting an invite"""
    code: str
    user_id: str
    
    @validator('code')
    def code_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Invite code cannot be empty')
        return v.strip()
    
    @validator('user_id')
    def user_id_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('User ID cannot be empty')
        return v.strip()

class InviteRevocationRequest(BaseModel):
    """Request for revoking an invite"""
    invite_id: str
    revoked_by: str
    reason: Optional[str] = None
    
    @validator('invite_id', 'revoked_by')
    def ids_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Value cannot be empty')
        return v.strip()
    
    @validator('reason')
    def reason_length_limit(cls, v):
        if v and len(v) > 500:
            raise ValueError('Reason must be 500 characters or less')
        return v

class InviteListRequest(BaseModel):
    """Request parameters for listing invites"""
    organization_id: str
    status: Optional[InviteStatus] = None
    skip: int = 0
    limit: int = 100
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"
    include_expired: bool = False
    
    @validator('limit')
    def limit_must_be_reasonable(cls, v):
        if v <= 0:
            raise ValueError('Limit must be positive')
        if v > 1000:
            raise ValueError('Limit cannot exceed 1000')
        return v
    
    @validator('skip')
    def skip_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError('Skip must be non-negative')
        return v

class InviteValidationResponse(BaseModel):
    """Response for invite validation"""
    is_valid: bool
    code: str
    status: str
    message: Optional[str] = None
    organization_name: Optional[str] = None
    target_role: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_expired: bool = False
    uses_remaining: Optional[int] = None

class InviteEmailRequest(BaseModel):
    """Request for sending/resending invite email"""
    invite_id: str
    custom_message: Optional[str] = None
    
    @validator('custom_message')
    def custom_message_length_limit(cls, v):
        if v and len(v) > 1000:
            raise ValueError('Custom message must be 1000 characters or less')
        return v

class InviteCleanupRequest(BaseModel):
    """Request for cleaning up expired invites"""
    organization_id: Optional[str] = None
    dry_run: bool = False
    older_than_days: Optional[int] = None

class InviteCleanupResponse(BaseModel):
    """Response for cleanup operation"""
    cleaned_count: int
    total_expired: int
    organization_id: Optional[str] = None
    dry_run: bool

class OrganizationInviteSummary(BaseModel):
    """Summary of invites for an organization"""
    organization_id: str
    organization_name: str
    total_invites: int
    pending_invites: int
    accepted_invites: int
    revoked_invites: int
    expired_invites: int
    most_recent_invite: Optional[datetime] = None

class UserInviteSummary(BaseModel):
    """Summary of invites sent by a user"""
    user_id: str
    user_name: str
    total_invites_sent: int
    pending_invites_sent: int
    accepted_invites_sent: int
    organizations: List[str] = Field(default_factory=list)
