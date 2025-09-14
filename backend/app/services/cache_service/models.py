# cache-service/models.py

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any
from datetime import datetime, timezone

class CacheEntry(BaseModel):
    """Generic cache entry model"""
    key: str
    value: Any
    ttl: Optional[int] = None
    created_at: Optional[datetime] = None

class CacheStats(BaseModel):
    """Cache statistics model"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    invalidations: int = 0

class OAuthStateData(BaseModel):
    """OAuth state data model for caching"""
    provider: str
    redirect_uri: HttpUrl
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PasswordResetTokenData(BaseModel):
    """Password reset token data model"""
    user_id: str
    created_at: datetime

class EmailVerificationTokenData(BaseModel):
    """Email verification token data model"""
    user_id: str
    created_at: datetime

class DashboardStatsCache(BaseModel):
    """Dashboard statistics cache model"""
    organization_id: str
    stats: Dict[str, Any]
    cached_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ttl: int = Field(ge=1, description="Seconds to live")

class MembershipCacheData(BaseModel):
    """Membership data for caching"""
    id: str
    user_id: str
    organization_id: str
    organization_name: str
    organization_slug: str
    organization_logo_url: Optional[str] = None
    role: str
    status: str
    joined_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
