# organization-service/models.py

from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# Re-export the main models from app.models for convenience
from app.models.organization import (
    Organization, OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrganizationSettings
)

class OrganizationQuery(BaseModel):
    """Query parameters for organization operations"""
    name: Optional[str] = None
    slug: Optional[str] = None
    created_by: Optional[str] = None

class OrganizationStats(BaseModel):
    """Statistics for organization"""
    total_members: int = 0
    active_members: int = 0
    pending_members: int = 0
    admin_count: int = 0
    editor_count: int = 0
    viewer_count: int = 0
    created_at: datetime
    last_activity: Optional[datetime] = None

class OrganizationListRequest(BaseModel):
    """Request parameters for listing organizations"""
    skip: int = 0
    limit: int = 100
    name_filter: Optional[str] = None
    created_by_filter: Optional[str] = None
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"
    
    @validator('limit')
    def limit_must_be_positive(cls, v):
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

class DefaultOrganizationRequest(BaseModel):
    """Request for creating default organization"""
    user_id: str
    user_name: Optional[str] = None
    include_default_settings: bool = True

class OrganizationBulkOperation(BaseModel):
    """Bulk operation request for organizations"""
    operation: str  # create, update, delete
    organizations: List[Dict[str, Any]]

class OrganizationSearchFilters(BaseModel):
    """Advanced search filters for organizations"""
    name_contains: Optional[str] = None
    slug_contains: Optional[str] = None
    created_by: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    has_logo: Optional[bool] = None
    member_count_min: Optional[int] = None
    member_count_max: Optional[int] = None
    
    @field_validator('member_count_min', 'member_count_max')
    @classmethod
    def validate_member_counts(cls, v):
        if v is not None and v < 0:
            raise ValueError('Member count must be non-negative')
        return v
    
    @model_validator(mode='after')
    def validate_date_range(self):
        if (self.created_after is not None and 
            self.created_before is not None and 
            self.created_after > self.created_before):
            raise ValueError('created_after cannot be later than created_before')
        return self
    
    @model_validator(mode='after')
    def validate_member_count_range(self):
        if (self.member_count_min is not None and 
            self.member_count_max is not None and 
            self.member_count_min > self.member_count_max):
            raise ValueError('member_count_min cannot be greater than member_count_max')
        return self

class OrganizationMembershipSummary(BaseModel):
    """Summary of user's membership in organization"""
    organization_id: str
    organization_name: str
    organization_slug: str
    organization_logo_url: Optional[str] = None
    user_role: str
    user_status: str
    joined_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None

class OrganizationSettingsUpdate(BaseModel):
    """Update request for organization settings"""
    allow_public_signup: Optional[bool] = None
    require_email_verification: Optional[bool] = None
    default_member_role: Optional[str] = None
    max_members: Optional[int] = None
    custom_branding: Optional[Dict[str, Any]] = None
    
    @field_validator('max_members')
    @classmethod
    def validate_max_members(cls, v):
        if v is not None and v <= 0:
            raise ValueError('max_members must be positive')
        return v

class SlugAvailabilityCheck(BaseModel):
    """Request to check slug availability"""
    slug: str
    exclude_organization_id: Optional[str] = None  # For updates

class SlugAvailabilityResponse(BaseModel):
    """Response for slug availability check"""
    slug: str
    available: bool
    suggestions: Optional[List[str]] = None

class OrganizationCreationRequest(BaseModel):
    """Enhanced organization creation request"""
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website_url: Optional[str] = None
    settings: Optional[OrganizationSettings] = None
    created_by: str
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Organization name cannot be empty')
        return v.strip()
    
    @validator('slug')
    def slug_must_be_valid(cls, v):
        import re
        if not v or not v.strip():
            raise ValueError('Organization slug cannot be empty')
        
        v = v.strip().lower()
        if not re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$', v):
            raise ValueError('Slug must start and end with alphanumeric characters, contain only lowercase letters, numbers, and hyphens')
        
        if len(v) > 80:
            raise ValueError('Slug must be 80 characters or less')
        
        return v
