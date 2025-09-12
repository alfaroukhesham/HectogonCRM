# membership-service/models.py

from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import Optional, List, Dict, Any, Literal, Union
from datetime import datetime

# Re-export the main models from app.models for convenience
from app.models.membership import (
    Membership, MembershipCreate, MembershipUpdate, MembershipResponse,
    UserMembershipResponse, OrganizationMembershipResponse,
    MembershipRole, MembershipStatus, OrganizationContext
)

class MembershipQuery(BaseModel):
    """Query parameters for membership operations"""
    user_id: str
    organization_id: str

class MembershipStats(BaseModel):
    """Statistics for membership operations"""
    total_memberships: int = 0
    active_memberships: int = 0
    pending_memberships: int = 0
    inactive_memberships: int = 0
    by_role: Dict[str, int] = Field(default_factory=dict)

class MembershipPartialUpdate(BaseModel):
    """Partial update for membership (only fields to be updated)"""
    user_id: str
    organization_id: str
    role: Optional[MembershipRole] = None
    status: Optional[MembershipStatus] = None
    last_accessed: Optional[datetime] = None

class MembershipBulkOperation(BaseModel):
    """Bulk operation request for memberships"""
    operation: Literal["create", "update", "delete"]
    memberships: List[Union[MembershipCreate, MembershipPartialUpdate]]

class MembershipSearchFilters(BaseModel):
    """Search filters for membership queries"""
    role: Optional[MembershipRole] = None
    status: Optional[MembershipStatus] = None
    joined_after: Optional[datetime] = None
    joined_before: Optional[datetime] = None
    last_accessed_after: Optional[datetime] = None

class MembershipAggregationResult(BaseModel):
    """Result of membership aggregation operations"""
    user_id: str
    organization_id: str
    organization_name: str
    organization_slug: str
    organization_logo_url: Optional[str] = None
    role: MembershipRole
    status: MembershipStatus
    joined_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None

class RoleChangeRequest(BaseModel):
    """Request to change a user's role in an organization"""
    user_id: str
    organization_id: str
    new_role: MembershipRole
    changed_by: str  # User ID of who made the change

class MembershipInviteData(BaseModel):
    """Data for membership invitations"""
    organization_id: str
    invited_email: EmailStr
    role: MembershipRole
    invited_by: str
    expires_at: Optional[datetime] = None
class OrganizationMemberSummary(BaseModel):
    """Summary of members in an organization"""
    organization_id: str
    total_members: int
    admins: int
    editors: int
    viewers: int
    active_members: int
    pending_members: int
