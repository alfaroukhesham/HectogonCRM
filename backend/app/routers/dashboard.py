from fastapi import APIRouter, Depends

from app.models.deal import DealStage
from app.core.database import get_database


router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


@router.get("/stats")
async def get_dashboard_stats(db=Depends(get_database)):
    """Get dashboard statistics."""
    # Get counts
    total_contacts = await db.contacts.count_documents({})
    total_deals = await db.deals.count_documents({})
    won_deals = await db.deals.count_documents({"stage": DealStage.closed_won})
    
    # Calculate total revenue
    won_deals_data = await db.deals.find({"stage": DealStage.closed_won}).to_list(1000)
    total_revenue = sum(deal["value"] for deal in won_deals_data)
    
    # Calculate pipeline value
    active_deals = await db.deals.find({
        "stage": {"$nin": [DealStage.closed_won, DealStage.closed_lost]}
    }).to_list(1000)
    pipeline_value = sum(deal["value"] for deal in active_deals)
    
    # Deals by stage
    stages = [stage.value for stage in DealStage]
    deals_by_stage = {}
    for stage in stages:
        count = await db.deals.count_documents({"stage": stage})
        deals_by_stage[stage] = count
    
    return {
        "total_contacts": total_contacts,
        "total_deals": total_deals,
        "won_deals": won_deals,
        "total_revenue": total_revenue,
        "pipeline_value": pipeline_value,
        "deals_by_stage": deals_by_stage
    } 