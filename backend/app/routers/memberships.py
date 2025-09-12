from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import (
    get_current_active_user, get_organization_context, require_org_admin,
    get_membership_service, get_cache_service
)
from app.models.user import User
from app.models.membership import (
    MembershipUpdate, MembershipResponse, UserMembershipResponse,
    MembershipRole, MembershipStatus
)
from app.services import MembershipService, CacheService


router = APIRouter(prefix="/memberships", tags=["memberships"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[UserMembershipResponse])
async def get_organization_members(
    status: Optional[MembershipStatus] = None,
    org_context: tuple[str, MembershipRole] = Depends(get_organization_context),
    membership_service: MembershipService = Depends(get_membership_service)
):
    """Get all members of the current organization."""
    org_id, user_role = org_context
    
    # Only admins and editors can view members
    if user_role == MembershipRole.VIEWER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view members"
        )
    
    return await membership_service.get_organization_members(org_id, status)


@router.get("/{membership_id}", response_model=MembershipResponse)
async def get_membership(
    membership_id: str,
    org_context: tuple[str, MembershipRole] = Depends(get_organization_context),
    membership_service: MembershipService = Depends(get_membership_service)
):
    """Get membership details."""
    org_id, user_role = org_context
    
    # Only admins and editors can view membership details
    if user_role == MembershipRole.VIEWER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view membership details"
        )
    
    membership = await membership_service.get_membership_by_id(membership_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found"
        )
    
    # Check if membership belongs to current organization
    if membership.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this membership"
        )
    
    return MembershipResponse(**membership.dict())


@router.put("/{membership_id}", response_model=MembershipResponse)
async def update_membership(
    membership_id: str,
    membership_data: MembershipUpdate,
    current_user: User = Depends(get_current_active_user),
    org_context: tuple[str, MembershipRole] = Depends(require_org_admin),
    membership_service: MembershipService = Depends(get_membership_service),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Update membership (admin only)."""
    org_id, user_role = org_context
    
    # Check if membership exists and belongs to organization
    existing_membership = await membership_service.get_membership_by_id(membership_id)
    if not existing_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found"
        )
    
    if existing_membership.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this membership"
        )
    
    # Prevent admin from changing their own role
    if existing_membership.user_id == current_user.id:
        if membership_data.role and membership_data.role != MembershipRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot change your own admin role"
            )
    
    membership = await membership_service.update_membership(membership_id, membership_data)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found"
        )
    
    # Best-effort cache invalidation; don't block membership update on cache errors
    try:
        await cache_service.invalidate_user_membership(existing_membership.user_id, existing_membership.organization_id)
        logger.info(f"Successfully invalidated membership cache for user {existing_membership.user_id} in org {existing_membership.organization_id} after role update")
    except Exception as cache_error:
        logger.warning(f"Failed to invalidate membership cache for user {existing_membership.user_id} in org {existing_membership.organization_id}: {cache_error}. Membership update succeeded anyway.")
    
    return MembershipResponse(**membership.dict())


@router.delete("/{membership_id}")
async def remove_member(
    membership_id: str,
    current_user: User = Depends(get_current_active_user),
    org_context: tuple[str, MembershipRole] = Depends(require_org_admin),
    membership_service: MembershipService = Depends(get_membership_service),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Remove member from organization (admin only)."""
    org_id, user_role = org_context
    
    # Check if membership exists and belongs to organization
    existing_membership = await membership_service.get_membership_by_id(membership_id)
    if not existing_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found"
        )
    
    if existing_membership.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this membership"
        )
    
    # Prevent admin from removing themselves
    if existing_membership.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove yourself from the organization"
        )
    
    # Check if this is the last admin
    if existing_membership.role == MembershipRole.ADMIN:
        all_members = await membership_service.get_organization_members(org_id)
        admin_count = sum(1 for member in all_members if member.role == MembershipRole.ADMIN)
        
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last admin from the organization"
            )
    
    success = await membership_service.delete_membership(membership_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found"
        )
    
    # Best-effort cache invalidation; don't block member removal on cache errors
    try:
        await cache_service.invalidate_user_memberships(existing_membership.user_id)
        logger.info(f"Successfully invalidated membership cache for user {existing_membership.user_id} after removal")
    except Exception as cache_error:
        logger.warning(f"Failed to invalidate membership cache for user {existing_membership.user_id}: {cache_error}. Member removal succeeded anyway.")
    
    return {"message": "Member removed successfully"}


@router.post("/leave")
async def leave_organization(
    current_user: User = Depends(get_current_active_user),
    org_context: tuple[str, MembershipRole] = Depends(get_organization_context),
    membership_service: MembershipService = Depends(get_membership_service),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Leave the current organization."""
    org_id, user_role = org_context
    
    # Get current membership
    membership = await membership_service.get_membership(current_user.id, org_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found"
        )
    
    # Check if this is the last admin
    if user_role == MembershipRole.ADMIN:
        all_members = await membership_service.get_organization_members(org_id)
        admin_count = sum(1 for member in all_members if member.role == MembershipRole.ADMIN)
        
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are the last admin. Please assign another admin before leaving."
            )
    
    success = await membership_service.delete_membership(membership.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found"
        )
    
    # Best-effort cache invalidation; don't block leaving organization on cache errors
    try:
        await cache_service.invalidate_user_membership(current_user.id, organization_id)
        logger.info(f"Successfully invalidated membership cache for user {current_user.id} in org {organization_id} after leaving organization")
    except Exception as cache_error:
        logger.warning(f"Failed to invalidate membership cache for user {current_user.id} in org {organization_id}: {cache_error}. Leaving organization succeeded anyway.")
    
    return {"message": "Successfully left the organization"} 