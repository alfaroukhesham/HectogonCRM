from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
from bson import ObjectId
import uuid


class OrganizationPlan(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class OrganizationSettings(BaseModel):
    """Organization-specific settings."""
    timezone: str = "UTC"
    date_format: str = "MM/DD/YYYY"
    currency: str = "USD"
    language: str = "en"
    allow_user_registration: bool = True
    require_email_verification: bool = True
    max_users: Optional[int] = None
    custom_branding: Dict[str, Any] = {}


class Organization(BaseModel):
    """Organization model for multi-tenancy."""
    id: Optional[str] = Field(None, alias="_id")
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=50)  # URL-friendly identifier
    description: Optional[str] = Field(None, max_length=500)
    plan: OrganizationPlan = OrganizationPlan.FREE
    logo_url: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None  # e.g., "1-10", "11-50", "51-200"
    settings: OrganizationSettings = Field(default_factory=OrganizationSettings)
    is_active: bool = True
    created_by: str  # User ID of the creator
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @validator('slug')
    def validate_slug(cls, v):
        """Ensure slug is URL-friendly."""
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
        if v.startswith('-') or v.endswith('-'):
            raise ValueError("Slug cannot start or end with a hyphen")
        return v

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class OrganizationCreate(BaseModel):
    """Model for creating organizations."""
    name: str = Field(..., min_length=1, max_length=100)
    slug: Optional[str] = None  # Auto-generated if not provided
    description: Optional[str] = Field(None, max_length=500)
    plan: OrganizationPlan = OrganizationPlan.FREE
    logo_url: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    settings: Optional[OrganizationSettings] = None

    @validator('slug', pre=True)
    def generate_slug_if_empty(cls, v, values):
        """Auto-generate slug from name if not provided."""
        if not v and 'name' in values:
            import re
            slug = re.sub(r'[^a-zA-Z0-9\s-]', '', values['name'])
            slug = re.sub(r'\s+', '-', slug.strip())
            slug = slug.lower()
            return slug[:50]  # Limit length
        return v


class OrganizationUpdate(BaseModel):
    """Model for updating organizations."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    plan: Optional[OrganizationPlan] = OrganizationPlan.FREE
    logo_url: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    settings: Optional[OrganizationSettings] = None


class OrganizationResponse(BaseModel):
    """Response model for organizations."""
    id: str
    name: str
    slug: str
    description: Optional[str]
    plan: OrganizationPlan
    logo_url: Optional[str]
    website: Optional[str]
    industry: Optional[str]
    size: Optional[str]
    settings: OrganizationSettings
    is_active: bool
    created_at: datetime
    updated_at: datetime 