from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from bson import ObjectId

from app.core.database import get_database
from app.core.dependencies import (
    get_current_active_user, get_organization_context, require_org_admin,
    get_organization_service, get_membership_service
)
from app.models.user import User
from app.models.organization import (
    Organization, OrganizationCreate, OrganizationUpdate, OrganizationResponse
)
from app.models.membership import (
    MembershipRole, MembershipCreate, MembershipStatus,
    OrganizationMembershipResponse
)
from app.services.organization_service import OrganizationService
from app.services.membership_service import MembershipService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("/", response_model=OrganizationResponse)
async def create_organization(
    organization_data: OrganizationCreate,
    current_user: User = Depends(get_current_active_user),
    org_service: OrganizationService = Depends(get_organization_service),
    membership_service: MembershipService = Depends(get_membership_service)
):
    """Create a new organization."""
    try:
        # Create organization
        organization = await org_service.create_organization(organization_data, current_user.id)
        
        # Create admin membership for creator
        membership_data = MembershipCreate(
            user_id=current_user.id,
            organization_id=organization.id,
            role=MembershipRole.ADMIN,
            status=MembershipStatus.ACTIVE
        )
        await membership_service.create_membership(membership_data)
        
        return OrganizationResponse(**organization.dict())
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[OrganizationMembershipResponse])
async def get_user_organizations(
    current_user: User = Depends(get_current_active_user),
    membership_service: MembershipService = Depends(get_membership_service)
):
    """Get all organizations the current user belongs to."""
    try:
        logger.info(f"Loading organizations for user: {current_user.id}")
        
        memberships = await membership_service.get_user_memberships(
            current_user.id, 
            MembershipStatus.ACTIVE
        )
        
        logger.info(f"Found {len(memberships)} organizations for user {current_user.id}")
        
        if not memberships:
            logger.warning(f"No organizations found for user {current_user.id}")
        
        return memberships
        
    except Exception as e:
        logger.error(f"Error loading organizations for user {current_user.id}: {str(e)}")
        logger.error(f"Exception type: {type(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load organizations: {str(e)}"
        )


@router.get("/debug/{user_id}")
async def debug_user_organizations(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Debug endpoint to check user organizations directly from database."""
    try:
        # Check if user exists
        user_count = await db.users.count_documents({"_id": ObjectId(user_id)})
        logger.info(f"User {user_id} exists: {user_count > 0}")
        
        # Check memberships
        memberships = await db.memberships.find({"user_id": user_id}).to_list(100)
        logger.info(f"Found {len(memberships)} raw memberships for user {user_id}")
        
        # Check organizations
        org_ids = [m["organization_id"] for m in memberships]
        organizations = []
        for org_id in org_ids:
            try:
                org = await db.organizations.find_one({"_id": ObjectId(org_id)})
                if org:
                    org["_id"] = str(org["_id"])
                    organizations.append(org)
            except Exception as e:
                logger.error(f"Error loading organization {org_id}: {str(e)}")
        
        logger.info(f"Found {len(organizations)} organizations for user {user_id}")
        
        return {
            "user_exists": user_count > 0,
            "memberships_count": len(memberships),
            "organizations_count": len(organizations),
            "memberships": memberships,
            "organizations": organizations
        }
        
    except Exception as e:
        logger.error(f"Debug error: {str(e)}")
        return {"error": str(e)}


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: str,
    current_user: User = Depends(get_current_active_user),
    org_service: OrganizationService = Depends(get_organization_service),
    membership_service: MembershipService = Depends(get_membership_service)
):
    """Get organization details."""
    # Check if user has access to this organization
    user_role = await membership_service.check_user_role(current_user.id, organization_id)
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this organization"
        )
    
    organization = await org_service.get_organization(organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return OrganizationResponse(**organization.dict())


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: str,
    organization_data: OrganizationUpdate,
    org_context: tuple[str, MembershipRole] = Depends(require_org_admin),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """Update organization (admin only)."""
    org_id, user_role = org_context
    
    organization = await org_service.update_organization(organization_id, organization_data)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return OrganizationResponse(**organization.dict())


@router.delete("/{organization_id}")
async def delete_organization(
    organization_id: str,
    org_context: tuple[str, MembershipRole] = Depends(require_org_admin),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """Delete organization (admin only)."""
    org_id, user_role = org_context
    
    success = await org_service.delete_organization(organization_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return {"message": "Organization deleted successfully"} 