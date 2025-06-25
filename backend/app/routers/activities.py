from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime

from app.models.activity import Activity, ActivityCreate, ActivityUpdate
from app.core.database import get_database


router = APIRouter(
    prefix="/activities",
    tags=["activities"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Activity)
async def create_activity(
    activity: ActivityCreate,
    db=Depends(get_database)
):
    """Create a new activity."""
    # Verify contact exists
    contact = await db.contacts.find_one({"id": activity.contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    activity_dict = activity.dict()
    activity_obj = Activity(**activity_dict)
    await db.activities.insert_one(activity_obj.dict())
    return activity_obj


@router.get("/", response_model=List[Activity])
async def get_activities(
    contact_id: Optional[str] = None,
    deal_id: Optional[str] = None,
    db=Depends(get_database)
):
    """Get activities with optional filtering by contact or deal."""
    query = {}
    if contact_id:
        query["contact_id"] = contact_id
    if deal_id:
        query["deal_id"] = deal_id
    
    activities = await db.activities.find(query).sort("created_at", -1).to_list(1000)
    return [Activity(**activity) for activity in activities]


@router.get("/{activity_id}", response_model=Activity)
async def get_activity(
    activity_id: str,
    db=Depends(get_database)
):
    """Get a specific activity by ID."""
    activity = await db.activities.find_one({"id": activity_id})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return Activity(**activity)


@router.put("/{activity_id}", response_model=Activity)
async def update_activity(
    activity_id: str,
    activity: ActivityUpdate,
    db=Depends(get_database)
):
    """Update an activity."""
    update_data = {k: v for k, v in activity.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.activities.update_one(
        {"id": activity_id}, 
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    updated_activity = await db.activities.find_one({"id": activity_id})
    return Activity(**updated_activity)


@router.delete("/{activity_id}")
async def delete_activity(
    activity_id: str,
    db=Depends(get_database)
):
    """Delete an activity."""
    result = await db.activities.delete_one({"id": activity_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Activity not found")
    return {"message": "Activity deleted successfully"} 