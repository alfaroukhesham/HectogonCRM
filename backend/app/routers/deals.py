from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timezone

from app.models.deal import Deal, DealCreate, DealUpdate, DealStage
from app.models.user import User
from app.models.membership import MembershipRole, OrganizationContext
from app.core.database import get_database
from app.core.dependencies import (
    get_current_active_user, get_organization_context,
    require_org_editor, require_org_viewer, get_common_services, CommonServices
)


router = APIRouter(
    prefix="/deals",
    tags=["deals"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Deal)
async def create_deal(
    deal: DealCreate,
    background_tasks: BackgroundTasks,
    org_context: OrganizationContext = Depends(require_org_editor),
    db=Depends(get_database),
    services: CommonServices = Depends(get_common_services)
):
    """Create a new deal."""
    organization_id = org_context.organization_id
    
    deal_dict = deal.dict()
    deal_dict["organization_id"] = organization_id
    deal_obj = Deal(**deal_dict)
    await db.deals.insert_one(deal_obj.dict())
    
    # Schedule cache invalidation as background task (deal creation affects dashboard counts)
    background_tasks.add_task(services.cache.invalidate_dashboard_stats, organization_id)
    
    return deal_obj


@router.get("/", response_model=List[Deal])
async def get_deals(
    stage: Optional[DealStage] = None,
    org_context: OrganizationContext = Depends(require_org_viewer),
    db=Depends(get_database)
):
    """Get all deals with optional stage filter."""
    organization_id = org_context.organization_id
    
    query = {"organization_id": organization_id}
    if stage:
        query["stage"] = stage
    
    deals = await db.deals.find(query).sort("created_at", -1).to_list(1000)
    return [Deal(**deal) for deal in deals]


@router.get("/{deal_id}", response_model=Deal)
async def get_deal(
    deal_id: str,
    org_context: OrganizationContext = Depends(require_org_viewer),
    db=Depends(get_database)
):
    """Get a specific deal by ID."""
    organization_id = org_context.organization_id
    
    deal = await db.deals.find_one({
        "id": deal_id,
        "organization_id": organization_id
    })
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return Deal(**deal)


@router.put("/{deal_id}", response_model=Deal)
async def update_deal(
    deal_id: str,
    deal: DealUpdate,
    background_tasks: BackgroundTasks,
    org_context: OrganizationContext = Depends(require_org_editor),
    db=Depends(get_database),
    services: CommonServices = Depends(get_common_services)
):
    """Update a deal."""
    organization_id = org_context.organization_id
    
    update_data = {k: v for k, v in deal.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    result = await db.deals.update_one(
        {"id": deal_id, "organization_id": organization_id}, 
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Check if any dashboard-affecting fields were updated (stage, value)
    dashboard_fields_updated = any(field in update_data for field in ['stage', 'value'])
    if dashboard_fields_updated:
        # Schedule cache invalidation as background task (stage/value changes affect dashboard stats)
        background_tasks.add_task(services.cache.invalidate_dashboard_stats, organization_id)
    
    updated_deal = await db.deals.find_one({
        "id": deal_id,
        "organization_id": organization_id
    })
    return Deal(**updated_deal)


@router.delete("/{deal_id}")
async def delete_deal(
    deal_id: str,
    background_tasks: BackgroundTasks,
    org_context: OrganizationContext = Depends(require_org_editor),
    db=Depends(get_database),
    services: CommonServices = Depends(get_common_services)
):
    """Delete a deal."""
    organization_id = org_context.organization_id
    
    result = await db.deals.delete_one({
        "id": deal_id,
        "organization_id": organization_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Schedule cache invalidation as background task (deal deletion affects dashboard counts)
    background_tasks.add_task(services.cache.invalidate_dashboard_stats, organization_id)
    
    return {"message": "Deal deleted successfully"} 