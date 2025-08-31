from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum
from bson import ObjectId
import re


class UserRole(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class OAuthProvider(str, Enum):
    GOOGLE = "google"
    FACEBOOK = "facebook"
    TWITTER = "twitter"


class AuthMethod(str, Enum):
    PASSWORD = "password"
    OAUTH = "oauth"


def validate_password_strength(password: str) -> str:
    """Validate password meets security requirements."""
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters long")
    
    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        raise ValueError("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        raise ValueError("Password must contain at least one digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValueError("Password must contain at least one special character")
    
    return password


class User(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    email: EmailStr
    full_name: str
    password_hash: Optional[str] = None  # For password auth
    avatar_url: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    auth_methods: List[AuthMethod] = []  # Track which auth methods user has
    oauth_providers: List[OAuthProvider] = []
    oauth_ids: Dict[str, str] = {}
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None
    email_verification_token: Optional[str] = None
    email_verification_expires: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None

    @validator('auth_methods')
    def validate_auth_methods(cls, v, values):
        """Ensure auth_methods matches actual auth data."""
        has_password = bool(values.get('password_hash'))
        has_oauth = bool(values.get('oauth_ids'))
        
        if has_password and AuthMethod.PASSWORD not in v:
            raise ValueError("PASSWORD auth method missing when password_hash is present")
        if has_oauth and AuthMethod.OAUTH not in v:
            raise ValueError("OAUTH auth method missing when oauth_ids is present")
        if AuthMethod.PASSWORD in v and not has_password:
            raise ValueError("PASSWORD auth method present but no password_hash")
        if AuthMethod.OAUTH in v and not has_oauth:
            raise ValueError("OAUTH auth method present but no oauth_ids")
            
        return v

    @validator('password_reset_expires')
    def validate_password_reset_expires(cls, v, values):
        """Ensure password_reset_expires is set when password_reset_token exists."""
        token = values.get('password_reset_token')
        if token and not v:
            raise ValueError("password_reset_expires must be set when password_reset_token exists")
        if not token and v:
            raise ValueError("password_reset_token must be set when password_reset_expires exists")
        return v

    @validator('email_verification_expires')
    def validate_email_verification_expires(cls, v, values):
        """Ensure email_verification_expires is set when email_verification_token exists."""
        token = values.get('email_verification_token')
        if token and not v:
            raise ValueError("email_verification_expires must be set when email_verification_token exists")
        if not token and v:
            raise ValueError("email_verification_token must be set when email_verification_expires exists")
        return v

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=12)
    full_name: str
    invite_code: Optional[str] = None  # For joining organizations

    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password meets security requirements."""
        return validate_password_strength(v)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    avatar_url: Optional[str]
    is_active: bool
    is_verified: bool
    auth_methods: List[AuthMethod]
    oauth_providers: List[OAuthProvider]
    created_at: datetime
    last_login: Optional[datetime]


class TokenData(BaseModel):
    user_id: str
    email: str
    organization_id: Optional[str] = None  # Current active organization
    role: Optional[str] = None


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=12)

    @validator('new_password')
    def validate_new_password_strength(cls, v):
        """Validate new password meets security requirements."""
        return validate_password_strength(v)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=12)

    @validator('new_password')
    def validate_new_password_strength(cls, v):
        """Validate new password meets security requirements."""
        return validate_password_strength(v)


class EmailVerificationRequest(BaseModel):
    email: EmailStr


class EmailVerificationConfirm(BaseModel):
    token: str 
 