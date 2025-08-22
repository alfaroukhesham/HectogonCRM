from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.core.config import settings
from app.models.user import TokenData
import secrets
import string
import uuid


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Store for refresh tokens (in production, use Redis or database)
refresh_token_store: Dict[str, Dict[str, Any]] = {}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token with unique JTI for denylist functionality."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire, 
        "type": "access",
        "jti": str(uuid.uuid4())  # Add unique identifier for token denylist
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: str) -> str:
    """Create refresh token and store it."""
    # Generate a secure random token
    token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))
    
    # Store token with expiration
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token_store[token] = {
        "user_id": user_id,
        "expires_at": expire,
        "created_at": datetime.now(timezone.utc)
    }
    
    return token


def verify_token(token: str) -> Optional[TokenData]:
    """Verify JWT token and return token data."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        # Check if token is access token
        if payload.get("type") != "access":
            return None
            
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: Optional[str] = payload.get("role")  # Role is optional now
        
        if user_id is None:
            return None
            
        token_data = TokenData(user_id=user_id, email=email, role=role)
        return token_data
        
    except JWTError:
        return None


def verify_refresh_token(token: str) -> Optional[str]:
    """Verify refresh token and return user_id."""
    # Validate token format first
    if not token or len(token) != 64 or not all(c in string.ascii_letters + string.digits for c in token):
        return None
        
    if token not in refresh_token_store:
        return None
        
    token_data = refresh_token_store[token]
    
    # Check if token is expired
    if datetime.now(timezone.utc) > token_data["expires_at"]:
        # Remove expired token
        del refresh_token_store[token]
        return None
        
    return token_data["user_id"]


def revoke_refresh_token(token: str) -> bool:
    """Revoke refresh token."""
    if token in refresh_token_store:
        del refresh_token_store[token]
        return True
    return False


def revoke_all_refresh_tokens(user_id: str) -> int:
    """Revoke all refresh tokens for a user."""
    tokens_to_remove = []
    for token, data in refresh_token_store.items():
        if data["user_id"] == user_id:
            tokens_to_remove.append(token)
    
    for token in tokens_to_remove:
        del refresh_token_store[token]
        
    return len(tokens_to_remove)


def revoke_all_user_refresh_tokens(user_id: str) -> int:
    """Revoke all refresh tokens for a user (alias for revoke_all_refresh_tokens)."""
    return revoke_all_refresh_tokens(user_id)


def create_token_pair(user_id: str, email: str, role: Optional[str] = None) -> Dict[str, Any]:
    """Create access and refresh token pair."""
    # Create access token
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {"sub": user_id, "email": email}
    if role:
        token_data["role"] = role
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token = create_refresh_token(user_id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def get_password_hash(password: str) -> str:
    """Hash a password (alias for hash_password)."""
    return hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def generate_state_token() -> str:
    """Generate a secure state token for OAuth flows."""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))


def generate_oauth_state() -> str:
    """Generate a secure OAuth state token (alias for generate_state_token)."""
    return generate_state_token()


# Store for OAuth state tokens (in production, use Redis)
oauth_state_store: Dict[str, Dict[str, Any]] = {}

# Store for password reset tokens (in production, use Redis)
password_reset_store: Dict[str, Dict[str, Any]] = {}

# Store for email verification tokens (in production, use Redis)
email_verification_store: Dict[str, Dict[str, Any]] = {}


def store_oauth_state(state: str, provider: str, redirect_uri: str) -> None:
    """Store OAuth state token."""
    oauth_state_store[state] = {
        "provider": provider,
        "redirect_uri": redirect_uri,
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)  # 10 minute expiry
    }


def verify_oauth_state(state: str) -> Optional[Dict[str, Any]]:
    """Verify OAuth state token."""
    # Validate state format first
    if not state or len(state) != 32 or not all(c in string.ascii_letters + string.digits for c in state):
        return None
        
    if state not in oauth_state_store:
        return None
        
    state_data = oauth_state_store[state]
    
    # Check if state is expired
    if datetime.now(timezone.utc) > state_data["expires_at"]:
        del oauth_state_store[state]
        return None
        
    # Remove state after verification (one-time use)
    del oauth_state_store[state]
    return state_data


def generate_password_reset_token() -> str:
    """Generate a secure password reset token."""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))


def store_password_reset_token(token: str, user_id: str) -> None:
    """Store password reset token."""
    password_reset_store[token] = {
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1)  # 1 hour expiry
    }


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify password reset token and return user_id."""
    # Validate token format first
    if not token or len(token) != 64 or not all(c in string.ascii_letters + string.digits for c in token):
        return None
        
    if token not in password_reset_store:
        return None
        
    token_data = password_reset_store[token]
    
    # Check if token is expired
    if datetime.now(timezone.utc) > token_data["expires_at"]:
        del password_reset_store[token]
        return None
        
    return token_data["user_id"]


def revoke_password_reset_token(token: str) -> bool:
    """Revoke password reset token."""
    if token in password_reset_store:
        del password_reset_store[token]
        return True
    return False


def generate_email_verification_token() -> str:
    """Generate a secure email verification token."""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))


def store_email_verification_token(token: str, user_id: str) -> None:
    """Store email verification token."""
    email_verification_store[token] = {
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=24)  # 24 hour expiry
    }


def verify_email_verification_token(token: str) -> Optional[str]:
    """Verify email verification token and return user_id."""
    # Validate token format first
    if not token or len(token) != 64 or not all(c in string.ascii_letters + string.digits for c in token):
        return None
        
    if token not in email_verification_store:
        return None
        
    token_data = email_verification_store[token]
    
    # Check if token is expired
    if datetime.now(timezone.utc) > token_data["expires_at"]:
        del email_verification_store[token]
        return None
        
    return token_data["user_id"]


def revoke_email_verification_token(token: str) -> bool:
    """Revoke email verification token."""
    if token in email_verification_store:
        del email_verification_store[token]
        return True
    return False


def cleanup_expired_tokens() -> None:
    """Clean up expired tokens from all stores."""
    current_time = datetime.now(timezone.utc)
    
    # Clean up refresh tokens
    expired_refresh_tokens = [
        token for token, data in refresh_token_store.items()
        if current_time > data["expires_at"]
    ]
    for token in expired_refresh_tokens:
        del refresh_token_store[token]
    
    # Clean up OAuth state tokens
    expired_oauth_states = [
        state for state, data in oauth_state_store.items()
        if current_time > data["expires_at"]
    ]
    for state in expired_oauth_states:
        del oauth_state_store[state]
    
    # Clean up password reset tokens
    expired_reset_tokens = [
        token for token, data in password_reset_store.items()
        if current_time > data["expires_at"]
    ]
    for token in expired_reset_tokens:
        del password_reset_store[token]
    
    # Clean up email verification tokens
    expired_verification_tokens = [
        token for token, data in email_verification_store.items()
        if current_time > data["expires_at"]
    ]
    for token in expired_verification_tokens:
        del email_verification_store[token] 
 
 
 