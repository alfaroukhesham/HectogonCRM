from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_database
from app.core.dependencies import (
    get_current_active_user, get_organization_context, require_org_admin,
    get_membership_service, get_cache_service
)
from app.core.email import EmailService
from app.models.user import User
from app.models.invite import (
    Invite, InviteCreate, InviteUpdate, InviteResponse, InviteAccept,
    InviteRevoke, InviteListResponse, InviteStatus
)
from app.models.membership import MembershipRole
from app.services import InviteService, MembershipService, CacheService


router = APIRouter(prefix="/invites", tags=["invites"])
logger = logging.getLogger(__name__)


async def get_invite_service(
    db = Depends(get_database)
) -> InviteService:
    """Get invite service."""
    email_service = EmailService()
    return InviteService(db, email_service)


@router.post("/", response_model=InviteResponse)
async def create_invite(
    invite_data: InviteCreate,
    current_user: User = Depends(get_current_active_user),
    org_context: tuple[str, MembershipRole] = Depends(require_org_admin),
    invite_service: InviteService = Depends(get_invite_service)
):
    """Create a new invite (admin only)."""
    org_id, user_role = org_context
    
    if invite_data.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create invites for your organization"
        )
    
    try:
        invite = await invite_service.create_invite(invite_data, current_user.id)
        
        # Convert to response model
        response = InviteResponse(
            **invite.dict(),
            is_expired=invite.is_expired,
            is_usable=invite.is_usable
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create invite: {str(e)}"
        )


@router.get("/", response_model=List[InviteListResponse])
async def get_organization_invites(
    status: Optional[InviteStatus] = None,
    org_context: tuple[str, MembershipRole] = Depends(get_organization_context),
    invite_service: InviteService = Depends(get_invite_service)
):
    """Get all invites for the current organization."""
    org_id, user_role = org_context
    
    # Only admins and editors can view invites
    if user_role == MembershipRole.VIEWER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view invites"
        )
    
    return await invite_service.get_organization_invites(org_id, status)


@router.get("/{invite_id}", response_model=InviteResponse)
async def get_invite(
    invite_id: str,
    org_context: tuple[str, MembershipRole] = Depends(get_organization_context),
    invite_service: InviteService = Depends(get_invite_service)
):
    """Get invite details."""
    org_id, user_role = org_context
    
    # Only admins and editors can view invites
    if user_role == MembershipRole.VIEWER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view invites"
        )
    
    invite = await invite_service.get_invite_by_id(invite_id)
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found"
        )
    
    # Check if invite belongs to current organization
    if invite.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this invite"
        )
    
    return InviteResponse(
        **invite.dict(),
        is_expired=invite.is_expired,
        is_usable=invite.is_usable
    )


@router.put("/{invite_id}", response_model=InviteResponse)
async def update_invite(
    invite_id: str,
    invite_data: InviteUpdate,
    org_context: tuple[str, MembershipRole] = Depends(require_org_admin),
    invite_service: InviteService = Depends(get_invite_service)
):
    """Update invite (admin only)."""
    org_id, user_role = org_context
    
    # Check if invite exists and belongs to organization
    existing_invite = await invite_service.get_invite_by_id(invite_id)
    if not existing_invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found"
        )
    
    if existing_invite.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this invite"
        )
    
    invite = await invite_service.update_invite(invite_id, invite_data)
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found"
        )
    
    return InviteResponse(
        **invite.dict(),
        is_expired=invite.is_expired,
        is_usable=invite.is_usable
    )


@router.post("/{invite_id}/revoke")
async def revoke_invite(
    invite_id: str,
    revoke_data: InviteRevoke,
    current_user: User = Depends(get_current_active_user),
    org_context: tuple[str, MembershipRole] = Depends(require_org_admin),
    invite_service: InviteService = Depends(get_invite_service)
):
    """Revoke invite (admin only)."""
    org_id, user_role = org_context
    
    # Check if invite exists and belongs to organization
    existing_invite = await invite_service.get_invite_by_id(invite_id)
    if not existing_invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found"
        )
    
    if existing_invite.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this invite"
        )
    
    invite = await invite_service.revoke_invite(
        invite_id, 
        current_user.id, 
        revoke_data.reason
    )
    
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found"
        )
    
    return {"message": "Invite revoked successfully"}


@router.post("/{invite_id}/resend")
async def resend_invite(
    invite_id: str,
    org_context: tuple[str, MembershipRole] = Depends(require_org_admin),
    invite_service: InviteService = Depends(get_invite_service)
):
    """Resend invite email (admin only)."""
    org_id, user_role = org_context
    
    # Check if invite exists and belongs to organization
    existing_invite = await invite_service.get_invite_by_id(invite_id)
    if not existing_invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found"
        )
    
    if existing_invite.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this invite"
        )
    
    success = await invite_service.resend_invite_email(invite_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot resend invite email"
        )
    
    return {"message": "Invite email sent successfully"}


@router.post("/accept", response_model=dict)
async def accept_invite(
    invite_data: InviteAccept,
    current_user: User = Depends(get_current_active_user),
    invite_service: InviteService = Depends(get_invite_service),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Accept an invite."""
    try:
        invite = await invite_service.accept_invite(invite_data.code, current_user.id)
        if not invite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired invite code"
            )
        
        # Best-effort cache invalidation; don't block acceptance on cache errors
        try:
            await cache_service.invalidate_user_membership(current_user.id, invite.organization_id)
            logger.info(f"Successfully invalidated membership cache for user {current_user.id} in org {invite.organization_id} after invite acceptance")
        except Exception as cache_error:
            logger.warning(f"Failed to invalidate membership cache for user {current_user.id} in org {invite.organization_id}: {cache_error}. Invite acceptance succeeded anyway.")
        
        return {
            "message": "Invite accepted successfully",
            "organization_id": invite.organization_id
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/code/{code}", response_model=dict)
async def get_invite_info(
    code: str,
    invite_service: InviteService = Depends(get_invite_service),
    db = Depends(get_database)
):
    """Get invite information by code (for preview before accepting)."""
    invite = await invite_service.get_invite_by_code(code)
    if not invite or not invite.is_usable:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired invite code"
        )
    
    # Get organization details
    org_data = await db.organizations.find_one({"_id": invite.organization_id})
    if not org_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Get inviter details
    inviter_data = await db.users.find_one({"_id": invite.invited_by})
    inviter_name = inviter_data["full_name"] if inviter_data else "Unknown"
    
    return {
        "organization_name": org_data["name"],
        "organization_description": org_data.get("description"),
        "role": invite.target_role,
        "invited_by": inviter_name,
        "expires_at": invite.expires_at,
        "email": invite.email if invite.email else None  # Only show if invite is for specific email
    } 