from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime

from app.models.deal import Deal, DealCreate, DealUpdate
from app.core.database import get_database


router = APIRouter(
    prefix="/deals",
    tags=["deals"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Deal)
async def create_deal(
    deal: DealCreate,
    db=Depends(get_database)
):
    """Create a new deal."""
    # Verify contact exists
    contact = await db.contacts.find_one({"id": deal.contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    deal_dict = deal.dict()
    deal_obj = Deal(**deal_dict)
    await db.deals.insert_one(deal_obj.dict())
    return deal_obj


@router.get("/", response_model=List[Deal])
async def get_deals(db=Depends(get_database)):
    """Get all deals."""
    deals = await db.deals.find().sort("created_at", -1).to_list(1000)
    return [Deal(**deal) for deal in deals]


@router.get("/{deal_id}", response_model=Deal)
async def get_deal(
    deal_id: str,
    db=Depends(get_database)
):
    """Get a specific deal by ID."""
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return Deal(**deal)


@router.put("/{deal_id}", response_model=Deal)
async def update_deal(
    deal_id: str,
    deal: DealUpdate,
    db=Depends(get_database)
):
    """Update a deal."""
    update_data = {k: v for k, v in deal.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.deals.update_one(
        {"id": deal_id}, 
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    updated_deal = await db.deals.find_one({"id": deal_id})
    return Deal(**updated_deal)


@router.delete("/{deal_id}")
async def delete_deal(
    deal_id: str,
    db=Depends(get_database)
):
    """Delete a deal."""
    result = await db.deals.delete_one({"id": deal_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Deal not found")
    return {"message": "Deal deleted successfully"} 