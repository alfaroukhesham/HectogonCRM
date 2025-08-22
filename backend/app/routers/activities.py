from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from app.models.activity import Activity, ActivityCreate, ActivityUpdate
from app.models.user import User
from app.models.membership import MembershipRole, OrganizationContext
from app.core.database import get_database
from app.core.dependencies import (
    get_current_active_user, get_organization_context,
    require_org_editor, require_org_viewer, get_common_services, CommonServices
)


router = APIRouter(
    prefix="/activities",
    tags=["activities"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Activity)
async def create_activity(
    activity: ActivityCreate,
    background_tasks: BackgroundTasks,
    org_context: OrganizationContext = Depends(require_org_editor),
    db=Depends(get_database)
):
    """Create a new activity."""
    organization_id = org_context.organization_id
    
    # Verify contact exists in the same organization
    contact = await db.contacts.find_one({
        "id": activity.contact_id,
        "organization_id": organization_id
    })
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Verify deal exists in the same organization (if provided)
    if activity.deal_id:
        deal = await db.deals.find_one({
            "id": activity.deal_id,
            "organization_id": organization_id
        })
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
    
    activity_dict = activity.dict()
    activity_dict["organization_id"] = organization_id
    activity_obj = Activity(**activity_dict)
    await db.activities.insert_one(activity_obj.dict())
    
    # Activities don't affect dashboard stats (dashboard only tracks contacts/deals counts and revenue)
    # No cache invalidation needed
    
    return activity_obj


@router.get("/", response_model=List[Activity])
async def get_activities(
    contact_id: Optional[str] = None,
    deal_id: Optional[str] = None,
    org_context: OrganizationContext = Depends(require_org_viewer),
    db=Depends(get_database)
):
    """Get activities with optional filtering by contact or deal."""
    organization_id = org_context.organization_id
    
    query = {"organization_id": organization_id}
    if contact_id:
        query["contact_id"] = contact_id
    if deal_id:
        query["deal_id"] = deal_id
    
    activities = await db.activities.find(query).sort("created_at", -1).to_list(1000)
    return [Activity(**activity) for activity in activities]


@router.get("/{activity_id}", response_model=Activity)
async def get_activity(
    activity_id: str,
    org_context: OrganizationContext = Depends(require_org_viewer),
    db=Depends(get_database)
):
    """Get a specific activity by ID."""
    organization_id = org_context.organization_id
    
    activity = await db.activities.find_one({
        "id": activity_id,
        "organization_id": organization_id
    })
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return Activity(**activity)


@router.put("/{activity_id}", response_model=Activity)
async def update_activity(
    activity_id: str,
    activity: ActivityUpdate,
    background_tasks: BackgroundTasks,
    org_context: OrganizationContext = Depends(require_org_editor),
    db=Depends(get_database)
):
    """Update an activity."""
    organization_id = org_context.organization_id
    
    update_data = {k: v for k, v in activity.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.activities.update_one(
        {"id": activity_id, "organization_id": organization_id}, 
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Activities don't affect dashboard stats (dashboard only tracks contacts/deals counts and revenue)
    # No cache invalidation needed
    
    updated_activity = await db.activities.find_one({
        "id": activity_id,
        "organization_id": organization_id
    })
    return Activity(**updated_activity)


@router.delete("/{activity_id}")
async def delete_activity(
    activity_id: str,
    background_tasks: BackgroundTasks,
    org_context: OrganizationContext = Depends(require_org_editor),
    db=Depends(get_database)
):
    """Delete an activity."""
    organization_id = org_context.organization_id
    
    result = await db.activities.delete_one({
        "id": activity_id,
        "organization_id": organization_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Activities don't affect dashboard stats (dashboard only tracks contacts/deals counts and revenue)
    # No cache invalidation needed
    
    return {"message": "Activity deleted successfully"}