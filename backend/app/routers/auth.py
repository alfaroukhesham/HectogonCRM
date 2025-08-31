from datetime import datetime, timezone, timedelta
from typing import Dict, Any
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from ..core.database import get_database
from ..core.config import settings
from ..core.security import (
    create_access_token, 
    create_refresh_token, 
    verify_password, 
    get_password_hash, 
    verify_refresh_token,
    revoke_refresh_token,
    revoke_all_user_refresh_tokens,
    generate_oauth_state,
    store_oauth_state,
    verify_oauth_state,
    generate_password_reset_token,
    store_password_reset_token,
    verify_password_reset_token,
    revoke_password_reset_token,
    generate_email_verification_token,
    store_email_verification_token,
    verify_email_verification_token,
    revoke_email_verification_token,
    cleanup_expired_tokens
)
from ..core.oauth import get_oauth_provider, get_authorization_url, exchange_code_for_token, get_user_info
from ..core.email import email_service
from ..models.user import (
    User, 
    UserCreate, 
    UserLogin, 
    UserResponse, 
    Token, 
    RefreshTokenRequest, 
    UserRole, 
    OAuthProvider, 
    AuthMethod,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordChange,
    EmailVerificationRequest,
    EmailVerificationConfirm
)
from ..core.dependencies import get_current_user, get_redis_client, get_cache_service
from ..services.organization_service import OrganizationService
from ..services.membership_service import MembershipService
from ..services.invite_service import InviteService
from ..services.cache_service import CacheService
from ..models.organization import OrganizationCreate
from ..models.membership import MembershipCreate, MembershipRole, MembershipStatus
from jose import jwt, JWTError

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()
logger = logging.getLogger(__name__)


@router.get("/providers")
async def get_oauth_providers():
    """Get available OAuth providers."""
    providers = []
    
    if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
        providers.append({
            "name": "google",
            "display_name": "Google",
            "icon": "🔍"
        })
    
    if settings.FACEBOOK_CLIENT_ID and settings.FACEBOOK_CLIENT_SECRET:
        providers.append({
            "name": "facebook", 
            "display_name": "Facebook",
            "icon": "👥"
        })
    
    if settings.TWITTER_CLIENT_ID and settings.TWITTER_CLIENT_SECRET:
        providers.append({
            "name": "twitter",
            "display_name": "X (Twitter)", 
            "icon": "🐦"
        })
    
    return {"providers": providers}


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db=Depends(get_database)):
    """Register a new user with email and password."""
    try:
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        password_hash = get_password_hash(user_data.password)
        
        # Create user document
        user_doc = {
            "email": user_data.email,
            "full_name": user_data.full_name,
            "password_hash": password_hash,
            "is_active": True,
            "is_verified": False,  # Require email verification
            "auth_methods": [AuthMethod.PASSWORD.value],
            "oauth_providers": [],
            "oauth_ids": {},
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Insert user
        result = await db.users.insert_one(user_doc)
        user_id = str(result.inserted_id)
        user_doc["_id"] = user_id
        
        # Handle invite code if provided
        organization_id = None
        if user_data.invite_code:
            invite_service = InviteService(db, email_service)
            try:
                invite = await invite_service.accept_invite(user_data.invite_code, user_id)
                if invite:
                    organization_id = invite.organization_id
            except ValueError as e:
                # If invite is invalid, continue with normal registration
                logger.warning(f"Invalid invite code during registration: {e}")
        
        # If no invite or invite failed, create default organization
        if not organization_id:
            org_service = OrganizationService(db)
            membership_service = MembershipService(db)
            
            # Create default organization
            organization = await org_service.create_default_organization(user_id, user_data.full_name)
            organization_id = organization.id
            
            # Create admin membership
            membership_data = MembershipCreate(
                user_id=user_id,
                organization_id=organization_id,
                role=MembershipRole.ADMIN,
                status=MembershipStatus.ACTIVE
            )
            await membership_service.create_membership(membership_data)
        
        # Generate and send email verification token
        verification_token = generate_email_verification_token()
        store_email_verification_token(verification_token, user_id)
        
        # Send verification email
        email_sent = email_service.send_email_verification_email(
            user_data.email, 
            verification_token, 
            user_data.full_name
        )
        
        if not email_sent:
            logger.warning(f"Failed to send verification email to {user_data.email}")
        
        # Return user response
        # Convert ObjectId to string for the User model (if needed)
        user_doc["_id"] = str(user_doc["_id"])
        user = User(**user_doc)
        response = UserResponse(
            id=user_id,
            email=user.email,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
            is_verified=user.is_verified,
            auth_methods=user.auth_methods,
            oauth_providers=user.oauth_providers,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
        return response
        
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin, 
    db=Depends(get_database),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Authenticate user with email and password."""
    try:
        # Find user by email
        user_doc = await db.users.find_one({"email": user_credentials.email})
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Convert ObjectId to string for the User model
        user_doc["_id"] = str(user_doc["_id"])
        user = User(**user_doc)
        
        # Check if user has password auth method
        if AuthMethod.PASSWORD.value not in user.auth_methods:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password authentication not available for this account"
            )
        
        # Verify password
        if not user.password_hash or not verify_password(user_credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        # Update last login
        await db.users.update_one(
            {"_id": ObjectId(user_doc["_id"])},
            {"$set": {"last_login": datetime.now(timezone.utc)}}
        )
        
        # Create tokens
        access_token = create_access_token(
            data={"sub": str(user_doc["_id"]), "email": user.email}
        )
        refresh_token = create_refresh_token(str(user_doc["_id"]))
        
        # Store the refresh token in Redis with a TTL
        await cache_service.store_refresh_token(
            user_id=str(user_doc["_id"]),
            token=refresh_token
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=30 * 60  # 30 minutes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/forgot-password")
async def forgot_password(request: PasswordResetRequest, db=Depends(get_database)):
    """Request password reset."""
    try:
        # Find user by email
        user_doc = await db.users.find_one({"email": request.email})
        if not user_doc:
            # Don't reveal if email exists or not
            return {"message": "If the email exists, a reset link has been sent"}
        
        # Convert ObjectId to string for the User model
        user_doc["_id"] = str(user_doc["_id"])
        user = User(**user_doc)
        
        # Check if user has password auth method
        if AuthMethod.PASSWORD.value not in user.auth_methods:
            return {"message": "If the email exists, a reset link has been sent"}
        
        # Generate reset token
        reset_token = generate_password_reset_token()
        store_password_reset_token(reset_token, str(user_doc["_id"]))
        
        # Send reset email
        email_sent = email_service.send_password_reset_email(
            request.email,
            reset_token,
            user.full_name
        )
        
        if not email_sent:
            logger.warning(f"Failed to send password reset email to {request.email}")
        
        return {"message": "If the email exists, a reset link has been sent"}
        
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(request: PasswordResetConfirm, db=Depends(get_database)):
    """Reset password with token."""
    try:
        # Verify reset token
        user_id = verify_password_reset_token(request.token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Find user
        user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Hash new password
        password_hash = get_password_hash(request.new_password)
        
        # Update password
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "password_hash": password_hash,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        # Revoke the reset token
        revoke_password_reset_token(request.token)
        
        # Revoke all refresh tokens for security
        revoke_all_user_refresh_tokens(user_id)
        
        # Send confirmation email
        # Convert ObjectId to string for the User model
        user_doc["_id"] = str(user_doc["_id"])
        user = User(**user_doc)
        email_service.send_password_changed_notification(
            user.email,
            user.full_name
        )
        
        return {"message": "Password reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.post("/change-password")
async def change_password(
    request: PasswordChange, 
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """Change password for authenticated user."""
    try:
        # Check if user has password auth method
        if AuthMethod.PASSWORD.value not in current_user.auth_methods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password authentication not available for this account"
            )
        
        # Verify current password
        if not current_user.password_hash or not verify_password(request.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        password_hash = get_password_hash(request.new_password)
        
        # Update password
        await db.users.update_one(
            {"_id": ObjectId(current_user.id)},
            {
                "$set": {
                    "password_hash": password_hash,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        # Revoke all refresh tokens for security
        revoke_all_user_refresh_tokens(current_user.id)
        
        # Send confirmation email
        email_service.send_password_changed_notification(
            current_user.email,
            current_user.full_name
        )
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/verify-email")
async def verify_email(request: EmailVerificationConfirm, db=Depends(get_database)):
    """Verify email address with token."""
    try:
        # Verify email token
        user_id = verify_email_verification_token(request.token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        # Update user verification status
        result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "is_verified": True,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Revoke the verification token
        revoke_email_verification_token(request.token)
        
        return {"message": "Email verified successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


@router.post("/resend-verification")
async def resend_verification(request: EmailVerificationRequest, db=Depends(get_database)):
    """Resend email verification."""
    try:
        # Find user by email
        user_doc = await db.users.find_one({"email": request.email})
        if not user_doc:
            # Don't reveal if email exists or not
            return {"message": "If the email exists and is unverified, a verification link has been sent"}
        
        # Convert ObjectId to string for the User model
        user_doc["_id"] = str(user_doc["_id"])
        user = User(**user_doc)
        
        # Check if already verified
        if user.is_verified:
            return {"message": "Email is already verified"}
        
        # Generate verification token
        verification_token = generate_email_verification_token()
        store_email_verification_token(verification_token, str(user_doc["_id"]))
        
        # Send verification email
        email_sent = email_service.send_email_verification_email(
            request.email,
            verification_token,
            user.full_name
        )
        
        if not email_sent:
            logger.warning(f"Failed to send verification email to {request.email}")
        
        return {"message": "If the email exists and is unverified, a verification link has been sent"}
        
    except Exception as e:
        logger.error(f"Resend verification error: {str(e)}")
        return {"message": "If the email exists and is unverified, a verification link has been sent"}


# OAuth endpoints
@router.get("/oauth/{provider}")
async def oauth_login(provider: str, redirect_uri: str = None):
    """Initiate OAuth login."""
    try:
        # Validate provider
        if provider not in ["google", "facebook", "twitter"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Unsupported OAuth provider"
            )
        
        oauth_provider = get_oauth_provider(provider)
        if not oauth_provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="OAuth provider not configured"
            )
        
        # Generate state for CSRF protection
        state = generate_oauth_state()
        store_oauth_state(state, provider, redirect_uri or settings.FRONTEND_URL)
        
        # Get authorization URL
        auth_url = get_authorization_url(oauth_provider, state, redirect_uri)
        
        return {"authorization_url": auth_url, "state": state}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth login error for {provider}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth login failed"
        )


@router.get("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str, 
    code: str, 
    state: str, 
    error: str = None,
    db=Depends(get_database),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Handle OAuth callback."""
    try:
        # Handle OAuth errors
        if error:
            logger.error(f"OAuth error from {provider}: {error}")
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error=oauth_error",
                status_code=status.HTTP_302_FOUND
            )
        
        # Verify state
        state_data = verify_oauth_state(state)
        if not state_data or state_data["provider"] != provider:
            logger.error(f"Invalid OAuth state for {provider}")
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error=invalid_state",
                status_code=status.HTTP_302_FOUND
            )
        
        # Get OAuth provider
        oauth_provider = get_oauth_provider(provider)
        if not oauth_provider:
            logger.error(f"OAuth provider {provider} not configured")
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error=provider_not_configured",
                status_code=status.HTTP_302_FOUND
            )
        
        # Exchange code for token
        token_data = await exchange_code_for_token(oauth_provider, code, state_data.get("redirect_uri"))
        if not token_data:
            logger.error(f"Failed to exchange code for token with {provider}")
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error=token_exchange_failed",
                status_code=status.HTTP_302_FOUND
            )
        
        # Get user info
        user_info = await get_user_info(oauth_provider, token_data["access_token"])
        if not user_info:
            logger.error(f"Failed to get user info from {provider}")
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error=user_info_failed",
                status_code=status.HTTP_302_FOUND
            )
        
        # Find or create user
        user_doc = await db.users.find_one({"email": user_info["email"]})
        
        if user_doc:
            # Update existing user
            # Convert ObjectId to string for the User model
            user_doc["_id"] = str(user_doc["_id"])
            user = User(**user_doc)
            
            # Add OAuth provider if not already present
            oauth_provider_enum = OAuthProvider(provider)
            if oauth_provider_enum.value not in user.oauth_providers:
                user.oauth_providers.append(oauth_provider_enum.value)
            
            # Add OAuth auth method if not already present
            if AuthMethod.OAUTH.value not in user.auth_methods:
                user.auth_methods.append(AuthMethod.OAUTH.value)
            
            # Update OAuth ID
            user.oauth_ids[provider] = user_info["id"]
            
            # Update user info
            await db.users.update_one(
                {"_id": ObjectId(user_doc["_id"])},
                {
                    "$set": {
                        "oauth_providers": user.oauth_providers,
                        "auth_methods": user.auth_methods,
                        "oauth_ids": user.oauth_ids,
                        "avatar_url": user_info.get("avatar_url", user.avatar_url),
                        "is_verified": True,  # OAuth accounts are considered verified
                        "last_login": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            user_id = str(user_doc["_id"])
        else:
            # Create new user
            user_doc = {
                "email": user_info["email"],
                "full_name": user_info["name"],
                "avatar_url": user_info.get("avatar_url"),
                "is_active": True,
                "is_verified": True,  # OAuth accounts are considered verified
                "auth_methods": [AuthMethod.OAUTH.value],
                "oauth_providers": [provider],
                "oauth_ids": {provider: user_info["id"]},
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "last_login": datetime.now(timezone.utc)
            }
            
            result = await db.users.insert_one(user_doc)
            user_id = str(result.inserted_id)
            
            # Create default organization for new OAuth user (like password registration)
            org_service = OrganizationService(db)
            membership_service = MembershipService(db)
            
            # Create default organization
            organization = await org_service.create_default_organization(user_id, user_info["name"])
            
            # Create admin membership
            membership_data = MembershipCreate(
                user_id=user_id,
                organization_id=organization.id,
                role=MembershipRole.ADMIN,
                status=MembershipStatus.ACTIVE
            )
            await membership_service.create_membership(membership_data)
        
        # Create tokens
        access_token = create_access_token(
            data={"sub": user_id, "email": user_info["email"]}
        )
        refresh_token = create_refresh_token(user_id)
        
        # Store the refresh token in Redis with a TTL
        await cache_service.store_refresh_token(
            user_id=user_id,
            token=refresh_token
        )
        
        # Redirect to frontend with tokens
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/oauth/callback?access_token={access_token}&refresh_token={refresh_token}",
            status_code=status.HTTP_302_FOUND
        )
        
    except Exception as e:
        logger.error(f"OAuth callback error for {provider}: {str(e)}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=oauth_callback_failed",
            status_code=status.HTTP_302_FOUND
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest, 
    db=Depends(get_database),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Refresh access token."""
    try:
        # First, try to decode the refresh token to get the user ID
        user_id = verify_refresh_token(request.refresh_token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        # Get the valid refresh token from Redis
        valid_token = await cache_service.get_refresh_token(user_id=user_id)

        # Compare the tokens
        if not valid_token or valid_token != request.refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )
        
        # Get user from database
        user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Convert ObjectId to string for the User model
        user_doc["_id"] = str(user_doc["_id"])
        user = User(**user_doc)
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated"
            )
        
        # Create new tokens
        access_token = create_access_token(
            data={"sub": user_id, "email": user.email}
        )
        new_refresh_token = create_refresh_token(user_id)
        
        # Store the new refresh token in Redis and revoke the old one
        await cache_service.store_refresh_token(
            user_id=user_id,
            token=new_refresh_token
        )
        
        # Also revoke old refresh token from the in-memory store for backward compatibility
        revoke_refresh_token(request.refresh_token)
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=30 * 60  # 30 minutes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout", summary="Logout user and invalidate token")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    redis_client = Depends(get_redis_client)
):
    """
    Invalidates the user's access token by adding its JTI to a denylist in Redis.
    This fixes the 403 error by using the proper authentication flow.
    """
    try:
        
        # Extract token from credentials
        token = credentials.credentials
        
        # Decode token to get JTI
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        jti = payload.get("jti")
        
        if not jti:
            # If for some reason a token has no JTI, we can't deny it,
            # but we should still let the user log out.
            return {"message": "Logout successful (token has no jti)"}

        # The token is valid, so add its JTI to the denylist.
        # Set the expiration to match the original token's lifetime.
        token_lifetime = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        await redis_client.set(f"jti_denylist:{jti}", "revoked", ex=token_lifetime)

        return {"message": "Logout successful"}
        
    except JWTError:
        # If the token is already invalid (e.g., expired), the user is effectively
        # logged out. We can return a success message.
        return {"message": "Logout successful (token was already invalid)"}
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return {"message": "Logout successful"}  # Always return success


@router.post("/logout-all")
async def logout_all(
    current_user: User = Depends(get_current_user),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Logout from all devices (revoke all refresh tokens)."""
    try:
        # Revoke all refresh tokens for the user from both Redis and in-memory store
        await cache_service.revoke_refresh_token(current_user.id)
        revoke_all_user_refresh_tokens(current_user.id)
        
        return {"message": "Logged out from all devices successfully"}
        
    except Exception as e:
        logger.error(f"Logout all error: {str(e)}")
        return {"message": "Logged out from all devices successfully"}  # Always return success


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        auth_methods=current_user.auth_methods,
        oauth_providers=current_user.oauth_providers,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.post("/cleanup-tokens")
async def cleanup_tokens(current_user: User = Depends(get_current_user)):
    """Cleanup expired tokens (admin endpoint)."""
    try:
        # Note: Admin check removed as role system has been simplified
        # All authenticated users can cleanup tokens for now
        
        cleanup_expired_tokens()
        return {"message": "Token cleanup completed"}
    except Exception as e:
        logger.error(f"Token cleanup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token cleanup failed"
        ) 
 