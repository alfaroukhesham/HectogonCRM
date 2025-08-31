from datetime import datetime, timezone, timedelta
from typing import Optional
from pydantic import BaseModel, Field, validator
from enum import Enum
from bson import ObjectId
import secrets
import uuid


class InviteStatus(str, Enum):
    """Invite status enumeration."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class Invite(BaseModel):
    """Organization invite model."""
    id: Optional[str] = Field(None, alias="_id")
    code: str = Field(..., description="Secure invite code (UUID)")
    organization_id: str
    invited_by: str  # User ID who created the invite
    target_role: str  # Role to assign when invite is accepted
    email: Optional[str] = None  # Optional: specific email this invite is for
    status: InviteStatus = InviteStatus.PENDING
    expires_at: datetime
    used_by: Optional[str] = None  # User ID who used the invite
    used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None
    max_uses: int = 1  # How many times this invite can be used
    current_uses: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @validator('code', pre=True)
    def generate_secure_code(cls, v):
        """Generate a secure invite code if not provided."""
        if not v:
            return str(uuid.uuid4())
        return v

    @validator('expires_at', pre=True)
    def set_default_expiry(cls, v):
        """Set default expiry to 7 days if not provided."""
        if not v:
            return datetime.now(timezone.utc) + timedelta(days=7)
        return v

    @property
    def is_expired(self) -> bool:
        """Check if invite is expired."""
        return self.expires_at < datetime.now(timezone.utc)

    @property
    def is_usable(self) -> bool:
        """Check if invite can be used."""
        return (
            self.status == InviteStatus.PENDING and
            not self.is_expired and
            self.current_uses < self.max_uses
        )

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class InviteCreate(BaseModel):
    """Model for creating invites."""
    organization_id: str
    target_role: str
    email: Optional[str] = None
    expires_at: Optional[datetime] = None
    max_uses: int = 1

    @validator('expires_at', pre=True)
    def validate_expiry_future(cls, v):
        """Ensure expiry is in the future."""
        if v and v <= datetime.now(timezone.utc):
            raise ValueError("Expiry date must be in the future")
        return v

    @validator('max_uses')
    def validate_max_uses(cls, v):
        """Ensure max_uses is positive."""
        if v < 1:
            raise ValueError("Max uses must be at least 1")
        return v


class InviteUpdate(BaseModel):
    """Model for updating invites."""
    target_role: Optional[str] = None
    email: Optional[str] = None
    expires_at: Optional[datetime] = None
    max_uses: Optional[int] = None

    @validator('expires_at')
    def validate_expiry_future(cls, v):
        """Ensure expiry is in the future."""
        if v and v <= datetime.now(timezone.utc):
            raise ValueError("Expiry date must be in the future")
        return v

    @validator('max_uses')
    def validate_max_uses(cls, v):
        """Ensure max_uses is positive."""
        if v is not None and v < 1:
            raise ValueError("Max uses must be at least 1")
        return v


class InviteResponse(BaseModel):
    """Response model for invites."""
    id: str
    code: str
    organization_id: str
    invited_by: str
    target_role: str
    email: Optional[str]
    status: InviteStatus
    expires_at: datetime
    used_by: Optional[str]
    used_at: Optional[datetime]
    max_uses: int
    current_uses: int
    created_at: datetime
    is_expired: bool
    is_usable: bool


class InviteAccept(BaseModel):
    """Model for accepting invites."""
    code: str


class InviteRevoke(BaseModel):
    """Model for revoking invites."""
    reason: Optional[str] = None


class InviteListResponse(BaseModel):
    """Response model for listing invites with organization details."""
    id: str
    code: str
    organization_id: str
    organization_name: str
    invited_by: str
    invited_by_name: str
    target_role: str
    email: Optional[str]
    status: InviteStatus
    expires_at: datetime
    max_uses: int
    current_uses: int
    created_at: datetime
    is_expired: bool
    is_usable: bool 