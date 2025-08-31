from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, validator
from enum import Enum
from bson import ObjectId


class MembershipRole(str, Enum):
    """Roles within an organization."""
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class MembershipStatus(str, Enum):
    """Membership status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


class Membership(BaseModel):
    """User membership in an organization."""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    organization_id: str
    role: MembershipRole
    status: MembershipStatus = MembershipStatus.ACTIVE
    invited_by: Optional[str] = None  # User ID who invited this member
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class MembershipCreate(BaseModel):
    """Model for creating memberships."""
    user_id: str
    organization_id: str
    role: MembershipRole
    status: MembershipStatus = MembershipStatus.ACTIVE
    invited_by: Optional[str] = None


class MembershipUpdate(BaseModel):
    """Model for updating memberships."""
    role: Optional[MembershipRole] = None
    status: Optional[MembershipStatus] = None


class MembershipResponse(BaseModel):
    """Response model for memberships."""
    id: str
    user_id: str
    organization_id: str
    role: MembershipRole
    status: MembershipStatus
    invited_by: Optional[str]
    joined_at: datetime
    last_accessed: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class UserMembershipResponse(BaseModel):
    """Extended membership response with user details."""
    id: str
    user_id: str
    user_email: str
    user_name: str
    user_avatar_url: Optional[str]
    organization_id: str
    role: MembershipRole
    status: MembershipStatus
    invited_by: Optional[str]
    joined_at: Optional[datetime]
    last_accessed: Optional[datetime]


class OrganizationMembershipResponse(BaseModel):
    """Extended membership response with organization details."""
    id: str
    user_id: str
    organization_id: str
    organization_name: str
    organization_slug: str
    organization_logo_url: Optional[str]
    role: MembershipRole
    status: MembershipStatus
    joined_at: Optional[datetime]
    last_accessed: Optional[datetime]


class OrganizationContext(BaseModel):
    """Organization context for requests."""
    organization_id: str
    user_role: MembershipRole 