# membership-service/utils.py

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from bson import ObjectId
from bson.errors import InvalidId

from .constants import ROLE_HIERARCHY, USER_MEMBERSHIP_PROJECTION, ORG_MEMBER_PROJECTION
from .types import MembershipRole, QueryDict, AggregationPipeline, ProjectionDict

def create_user_aggregation_pipeline(user_id: str, status: Optional[str] = None) -> AggregationPipeline:
    """Create aggregation pipeline for user memberships with organization details"""
    # Build match query
    match_query = {"user_id": user_id}
    if status:
        match_query["status"] = status
    
    return [
        # 1. Match memberships for the user
        {"$match": match_query},
        # 2. Convert organization_id string to ObjectId for lookup
        {
            "$addFields": {
                "organization_object_id": {
                    "$convert": {
                        "input": "$organization_id",
                        "to": "objectId",
                        "onError": None,
                        "onNull": None
                    }
                }
            }
        },
        # 3. Join with organizations collection
        {
            "$lookup": {
                "from": "organizations",
                "localField": "organization_object_id",
                "foreignField": "_id",
                "as": "organization_details"
            }
        },
        # 4. Unwind the organization array (should contain exactly one organization)
        {"$unwind": "$organization_details"},
        # 5. Project the final structure
        {"$project": USER_MEMBERSHIP_PROJECTION}
    ]

def create_organization_members_pipeline(organization_id: str, status: Optional[str] = None) -> AggregationPipeline:
    """Create aggregation pipeline for organization members with user details"""
    match_query = {"organization_id": organization_id}
    if status:
        match_query["status"] = status
    
    return [
        {"$match": match_query},
        # Convert user_id string to ObjectId for lookup
        {
            "$addFields": {
                "user_object_id": {
                    "$convert": {
                        "input": "$user_id",
                        "to": "objectId",
                        "onError": None,
                        "onNull": None
                    }
                }
            }
        },
        # Join with users collection
        {
            "$lookup": {
                "from": "users",
                "localField": "user_object_id",
                "foreignField": "_id",
                "as": "user_details"
            }
        },
        {"$unwind": "$user_details"},
        {"$project": ORG_MEMBER_PROJECTION}
    ]

def validate_object_id(object_id: str, field_name: str = "ID") -> ObjectId:
    """Validate and convert string to ObjectId"""
    try:
        return ObjectId(object_id)
    except InvalidId:
        raise ValueError(f"Invalid {field_name} format")

def normalize_id(value: Any) -> Optional[str]:
    """Normalize ID value safely, handling ObjectId and None values"""
    if value is None:
        return None
    if isinstance(value, ObjectId):
        return str(value)
    return str(value) if value else None

def convert_membership_dict_to_response(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert database document to response format for user memberships"""
    if not doc or "_id" not in doc:
        raise ValueError("Invalid document: missing required fields")
    
    return {
        "id": str(doc["_id"]),
        "user_id": normalize_id(doc.get("user_id")),
        "organization_id": normalize_id(doc.get("organization_id")),
        "organization_name": doc.get("organization_name"),
        "organization_slug": doc.get("organization_slug"),
        "organization_logo_url": doc.get("organization_logo_url"),
        "role": doc.get("role"),
        "status": doc.get("status"),
        "joined_at": doc.get("joined_at"),
        "last_accessed": doc.get("last_accessed")
    }

def convert_member_dict_to_response(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert database document to response format for organization members"""
    if not doc or "_id" not in doc:
        raise ValueError("Invalid document: missing required fields")
    
    return {
        "id": str(doc["_id"]),
        "user_id": normalize_id(doc.get("user_id")),
        "user_email": doc.get("user_email"),
        "user_name": doc.get("user_name"),
        "user_avatar_url": doc.get("user_avatar_url"),
        "organization_id": normalize_id(doc.get("organization_id")),
        "role": doc.get("role"),
        "status": doc.get("status"),
        "invited_by": doc.get("invited_by"),
        "joined_at": doc.get("joined_at"),
        "last_accessed": doc.get("last_accessed")
    }

def has_sufficient_role(user_role: MembershipRole, required_role: MembershipRole) -> bool:
    """Check if user has sufficient role for operation"""
    user_level = ROLE_HIERARCHY.get(user_role.value, 0)
    required_level = ROLE_HIERARCHY.get(required_role.value, 0)
    return user_level >= required_level

def create_membership_update_dict(update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create update dictionary with timestamp"""
    update_dict = {}
    
    # Validate and add role
    role_val = update_data.get("role")
    if role_val is not None:
        role_str = role_val.value if isinstance(role_val, MembershipRole) else str(role_val)
        role_str = role_str.strip().lower()
        if not role_str:
            raise ValueError("Role cannot be empty")
        if role_str not in ROLE_HIERARCHY:
            raise ValueError(f"Invalid role: {role_str}")
        update_dict["role"] = role_str
    
    # Validate and add status
    status_val = update_data.get("status")
    if status_val is not None:
        allowed_statuses = {"active", "inactive", "pending", "suspended"}
        status_str = status_val.value if hasattr(status_val, "value") else str(status_val)
        status_str = status_str.strip().lower()
        if not status_str:
            raise ValueError("Status cannot be empty")
        if status_str not in allowed_statuses:
            raise ValueError(f"Invalid status: {status_str}")
        update_dict["status"] = status_str

    update_dict["updated_at"] = datetime.now(timezone.utc)
    return update_dict

def create_timestamp_fields() -> Dict[str, datetime]:
    """Create common timestamp fields for new documents"""
    now = datetime.now(timezone.utc)
    return {
        "created_at": now,
        "updated_at": now
    }

def prepare_cache_membership_data(membership_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare membership data for caching"""
    cache_data = membership_dict.copy()
    # Ensure id field is set for cache compatibility
    if "_id" in cache_data:
        cache_data["id"] = str(cache_data["_id"])
    return cache_data

def build_membership_query(user_id: str, organization_id: str) -> QueryDict:
    """Build query for finding membership"""
    return {
        "user_id": user_id,
        "organization_id": organization_id
    }

def build_last_accessed_update() -> Dict[str, Any]:
    """Build update for last accessed timestamp"""
    return {
        "$set": {
            "last_accessed": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    }

def extract_user_ids_from_memberships(memberships: List[Dict[str, Any]]) -> List[str]:
    """Extract user IDs from membership documents"""
    return [membership.get("user_id") for membership in memberships if membership.get("user_id")]

def extract_organization_ids_from_memberships(memberships: List[Dict[str, Any]]) -> List[str]:
    """Extract organization IDs from membership documents"""
    return [membership.get("organization_id") for membership in memberships if membership.get("organization_id")]
