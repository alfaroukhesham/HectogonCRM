from fastapi import APIRouter, Depends

from app.models.deal import DealStage
from app.models.user import User
from app.models.membership import MembershipRole
from app.core.database import get_database
from app.core.dependencies import get_current_active_user, get_organization_context, require_org_viewer


router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


@router.get("/stats")
async def get_dashboard_stats(
    org_context: tuple[str, MembershipRole] = Depends(require_org_viewer),
    db=Depends(get_database)
):
    """Get dashboard statistics for the current organization."""
    organization_id, user_role = org_context
    
    # Get counts for current organization
    total_contacts = await db.contacts.count_documents({"organization_id": organization_id})
    total_deals = await db.deals.count_documents({"organization_id": organization_id})
    won_deals = await db.deals.count_documents({
        "organization_id": organization_id,
        "stage": DealStage.closed_won
    })
    
    # Calculate total revenue
    won_deals_data = await db.deals.find({
        "organization_id": organization_id,
        "stage": DealStage.closed_won
    }).to_list(1000)
    total_revenue = sum(deal["value"] for deal in won_deals_data)
    
    # Calculate pipeline value
    active_deals = await db.deals.find({
        "organization_id": organization_id,
        "stage": {"$nin": [DealStage.closed_won, DealStage.closed_lost]}
    }).to_list(1000)
    pipeline_value = sum(deal["value"] for deal in active_deals)
    
    # Deals by stage
    stages = [stage.value for stage in DealStage]
    deals_by_stage = {}
    for stage in stages:
        count = await db.deals.count_documents({
            "organization_id": organization_id,
            "stage": stage
        })
        deals_by_stage[stage] = count
    
    return {
        "total_contacts": total_contacts,
        "total_deals": total_deals,
        "won_deals": won_deals,
        "total_revenue": total_revenue,
        "pipeline_value": pipeline_value,
        "deals_by_stage": deals_by_stage
    } 