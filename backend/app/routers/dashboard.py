from fastapi import APIRouter, Depends, HTTPException, status

from app.models.deal import DealStage
from app.models.user import User
from app.models.membership import MembershipRole
from app.core.database import get_database
from app.core.dependencies import get_current_active_user, get_organization_context, require_org_viewer
from app.core.redis_client import get_redis_client
import redis.asyncio as redis
import json


router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


@router.get("/stats")
async def get_dashboard_stats(
    org_context: tuple[str, MembershipRole] = Depends(require_org_viewer),
    db=Depends(get_database),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """Get dashboard statistics for the current organization."""
    organization_id, user_role = org_context
    
    # 1. Define a unique cache key for this organization's dashboard
    cache_key = f"dashboard:stats:{organization_id}"
    
    # 2. Try to fetch from cache first
    cached_stats = await redis_client.get(cache_key)
    if cached_stats:
        return json.loads(cached_stats)  # Return cached data if it exists
    
    # 3. If it's a "cache miss", proceed with the original database query
    try:
        # Get counts for current organization
        total_contacts = await db.contacts.count_documents({"organization_id": organization_id})
        total_deals = await db.deals.count_documents({"organization_id": organization_id})
        won_deals = await db.deals.count_documents({
            "organization_id": organization_id,
            "stage": DealStage.closed_won.value
        })
        
        # Calculate total revenue (accurate, server-side)
        revenue_agg = await db.deals.aggregate([
            {"$match": {
                "organization_id": organization_id,
                "stage": DealStage.closed_won.value
            }},
            {"$group": {"_id": None, "total": {"$sum": "$value"}}}
        ]).to_list(length=1)
        total_revenue = revenue_agg[0]["total"] if revenue_agg else 0
        
        # Calculate pipeline value (accurate, server-side)
        pipeline_agg = await db.deals.aggregate([
            {"$match": {
                "organization_id": organization_id,
                "stage": {"$nin": [DealStage.closed_won.value, DealStage.closed_lost.value]}
            }},
            {"$group": {"_id": None, "total": {"$sum": "$value"}}}
        ]).to_list(length=1)
        pipeline_value = pipeline_agg[0]["total"] if pipeline_agg else 0
        
        # Deals by stage
        stages = [stage.value for stage in DealStage]
        deals_by_stage = {}
        for stage in stages:
            count = await db.deals.count_documents({
                "organization_id": organization_id,
                "stage": stage
            })
            deals_by_stage[stage] = count
        
        stats = {
            "total_contacts": total_contacts,
            "total_deals": total_deals,
            "won_deals": won_deals,
            "total_revenue": total_revenue,
            "pipeline_value": pipeline_value,
            "deals_by_stage": deals_by_stage
        }
        
        # 4. Store the fresh stats in Redis before returning (best-effort)
        try:
            await redis_client.set(
                cache_key,
                json.dumps(stats),
                ex=600  # Cache for 10 minutes (600 seconds)
            )
        except Exception:
            # Best-effort cache write; don't fail the request
            pass
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) 