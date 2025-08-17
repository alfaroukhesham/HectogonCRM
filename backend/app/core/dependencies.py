from typing import Optional, TYPE_CHECKING, Any
import logging
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis.asyncio import Redis
from app.core.security import verify_token
from app.core.database import get_database
from app.core.redis_client import get_redis_client
from app.models.user import User, TokenData
from app.models.membership import MembershipRole, MembershipStatus, OrganizationContext
from bson import ObjectId
from bson.errors import InvalidId

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase
    from app.services.membership_service import MembershipService
    from app.services.organization_service import OrganizationService


# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """Get current user from JWT token."""
    token = credentials.credentials
    token_data = verify_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data


async def get_current_user(
    token_data: TokenData = Depends(get_current_user_token),
    db: Any = Depends(get_database)
) -> User:
    """Get current user from database."""
    try:
        user_doc = await db.users.find_one({"_id": ObjectId(token_data.user_id)})
    except InvalidId as e:
        # Log the specific error for debugging
        logging.error(f"Invalid ObjectId in get_current_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        # Log the specific error for debugging
        logging.error(f"Database error in get_current_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user_doc is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Convert ObjectId to string for the User model
    user_doc["_id"] = str(user_doc["_id"])
    user = User(**user_doc)
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    return current_user


async def get_current_organization_id(
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-ID")
) -> Optional[str]:
    """Get current organization ID from header."""
    return x_organization_id


async def get_organization_context(
    request: Request,
    organization_id: Optional[str] = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_active_user),
    db: Any = Depends(get_database)
) -> OrganizationContext:
    """Get organization context and user's role in it."""
    if not organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization ID is required. Please provide X-Organization-ID header."
        )
    
    from app.services.membership_service import MembershipService
    membership_service = MembershipService(db)
    
    # Fetch the full membership document
    membership = await membership_service.get_membership(current_user.id, organization_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this organization"
        )
    
    # Store the membership object in the request state for later use
    request.state.membership = membership
    
    # Update last accessed timestamp
    await membership_service.update_last_accessed(current_user.id, organization_id)
    
    return OrganizationContext(organization_id=organization_id, user_role=membership.role)


def require_organization_role(required_role: MembershipRole):
    """Dependency factory for organization role-based access control."""
    async def role_checker(
        org_context: OrganizationContext = Depends(get_organization_context)
    ) -> OrganizationContext:
        role_hierarchy = {
            MembershipRole.VIEWER: 1,
            MembershipRole.EDITOR: 2,
            MembershipRole.ADMIN: 3
        }
        
        user_level = role_hierarchy.get(org_context.user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions in this organization. Required role: {required_role}"
            )
        
        return org_context
    
    return role_checker


# Organization role dependencies
require_org_admin = require_organization_role(MembershipRole.ADMIN)
require_org_editor = require_organization_role(MembershipRole.EDITOR)
require_org_viewer = require_organization_role(MembershipRole.VIEWER)


# Legacy role-based access control removed
# Use organization-based permissions instead via require_org_* dependencies


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Any = Depends(get_database)
) -> Optional[User]:
    """Get current user if token is provided, otherwise return None."""
    if credentials is None:
        return None
    
    try:
        token_data = verify_token(credentials.credentials)
        if token_data is None:
            return None
        
        user_doc = await db.users.find_one({"_id": ObjectId(token_data.user_id)})
        if user_doc is None:
            return None
        
        # Convert ObjectId to string for the User model
        user_doc["_id"] = str(user_doc["_id"])
        user = User(**user_doc)
        return user if user.is_active else None
        
    except Exception:
        return None


async def get_optional_organization_context(
    request: Request,
    organization_id: Optional[str] = Depends(get_current_organization_id),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Any = Depends(get_database)
) -> Optional[OrganizationContext]:
    """Get optional organization context."""
    if not organization_id or not current_user:
        return None
    
    from app.services.membership_service import MembershipService
    membership_service = MembershipService(db)
    membership = await membership_service.get_membership(current_user.id, organization_id)
    
    if membership:
        # Store the membership object in the request state for later use
        request.state.membership = membership
        await membership_service.update_last_accessed(current_user.id, organization_id)
        return OrganizationContext(organization_id=organization_id, user_role=membership.role)
    
    return None


# Service dependencies
async def get_organization_service(
    db: Any = Depends(get_database)
) -> Any:
    """Get organization service."""
    from app.services.organization_service import OrganizationService
    return OrganizationService(db)


async def get_membership_service(
    db: Any = Depends(get_database)
) -> Any:
    """Get membership service."""
    from app.services.membership_service import MembershipService
    return MembershipService(db)


async def get_redis() -> Redis:
    """
    Get Redis client instance.
    
    This dependency provides a Redis client that can be injected into
    route handlers for caching and other Redis operations.
    
    Returns:
        Redis: Redis client instance from the connection pool
    """
    return get_redis_client() 