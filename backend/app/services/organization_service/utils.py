# organization-service/utils.py

import re
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from bson import ObjectId
from copy import deepcopy

from .constants import (
    SLUG_PATTERN, SLUG_CLEANUP_PATTERN, MAX_SLUG_LENGTH, DEFAULT_USER_NAME,
    DEFAULT_SLUG_PREFIX, UUID_SUFFIX_LENGTH, DEFAULT_ORG_SETTINGS
)
from .types import SlugString, OrganizationDict

def validate_slug_format(slug: str) -> bool:
    """Validate organization slug format"""
    return bool(re.match(SLUG_PATTERN, slug))

def clean_slug_string(text: str) -> str:
    """Clean text to create a valid slug"""
    # Convert to lowercase and replace spaces with hyphens
    cleaned = text.lower().replace(' ', '-')
    # Remove invalid characters
    cleaned = re.sub(SLUG_CLEANUP_PATTERN, '', cleaned)
    return cleaned

def generate_slug_from_name(name: str) -> SlugString:
    """Generate a slug from organization name"""
    if not name or not name.strip():
        return DEFAULT_SLUG_PREFIX
    
    base_slug = clean_slug_string(name.strip())
    if not base_slug:
        return DEFAULT_SLUG_PREFIX
    
    # Ensure it meets pattern requirements
    if not validate_slug_format(base_slug):
        return DEFAULT_SLUG_PREFIX

    # Enforce length after cleaning
    if not validate_slug_length(base_slug):
        base_slug = base_slug[:MAX_SLUG_LENGTH].rstrip('-')
        if not validate_slug_format(base_slug):
            return DEFAULT_SLUG_PREFIX

    return base_slug

def generate_unique_slug(base_name: str, suffix_length: int = UUID_SUFFIX_LENGTH) -> SlugString:
    """Generate a unique slug with UUID suffix, respecting MAX_SLUG_LENGTH"""
    base_slug = generate_slug_from_name(base_name) if base_name else DEFAULT_SLUG_PREFIX
    # Use hex to avoid hyphens in the suffix and clamp length
    suffix = uuid.uuid4().hex[:max(4, min(suffix_length, MAX_SLUG_LENGTH - 2))]
    # Ensure final length (account for hyphen)
    base_max_len = MAX_SLUG_LENGTH - 1 - len(suffix)
    base_slug = base_slug[:max(1, base_max_len)].rstrip('-')
    return f"{base_slug}-{suffix}"

def create_organization_dict(
    org_data: Dict[str, Any], 
    created_by: str,
    include_defaults: bool = True
) -> OrganizationDict:
    """Create organization dictionary with timestamps and defaults"""
    org_dict = org_data.copy()
    org_dict["created_by"] = created_by
    now = datetime.now(timezone.utc)
    org_dict["created_at"] = now
    org_dict["updated_at"] = now
    
    if include_defaults:
        # Ensure settings are included with defaults if not provided
        if "settings" not in org_dict or org_dict["settings"] is None:
            org_dict["settings"] = deepcopy(DEFAULT_ORG_SETTINGS)
    
    return org_dict

def create_update_dict(update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create update dictionary filtering None values and adding timestamp"""
    update_dict = {k: v for k, v in update_data.items() if v is not None}
    if update_dict:  # Only add timestamp if there are actual updates
        update_dict["updated_at"] = datetime.now(timezone.utc)
    return update_dict

def convert_object_id_to_string(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB ObjectId to string in document"""
    if "_id" in doc and isinstance(doc["_id"], ObjectId):
        doc["_id"] = str(doc["_id"])
    return doc

def build_organization_query_by_ids(org_ids: List[str]) -> Dict[str, Any]:
    """Build MongoDB query for multiple organization IDs"""
    object_ids = [ObjectId(org_id) for org_id in org_ids if org_id and ObjectId.is_valid(org_id)]
    return {"_id": {"$in": object_ids}}

def build_membership_query_for_user(user_id: str, status: Optional[str] = None) -> Dict[str, Any]:
    """Build query for user memberships"""
    query = {"user_id": user_id}
    if status:
        query["status"] = status
    return query

def extract_organization_ids_from_memberships(memberships: List[Dict[str, Any]]) -> List[str]:
    """Extract organization IDs from membership documents"""
    return [
        membership["organization_id"] 
        for membership in memberships 
        if "organization_id" in membership
    ]

def validate_organization_name(name: str) -> bool:
    """Validate organization name"""
    return bool(name and name.strip())

def validate_user_id(user_id: str) -> bool:
    """Validate user ID"""
    return bool(user_id and user_id.strip())

def sanitize_organization_name(name: str) -> str:
    """Sanitize organization name for display"""
    return name.strip() if name else ""

def create_default_organization_name(user_name: str) -> str:
    """Create default organization name for user"""
    clean_name = user_name.strip() if user_name else DEFAULT_USER_NAME
    return f"{clean_name}'s Organization"

def validate_slug_length(slug: str) -> bool:
    """Validate slug length"""
    return len(slug) <= MAX_SLUG_LENGTH

def is_slug_format_valid(slug: str) -> bool:
    """Comprehensive slug validation"""
    if not slug or not slug.strip():
        return False
    
    slug = slug.strip()
    
    # Check length
    if not validate_slug_length(slug):
        return False
    
    # Check format
    return validate_slug_format(slug)

def prepare_organization_for_response(org_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare organization data for API response"""
    # Convert ObjectId to string
    org_dict = convert_object_id_to_string(org_dict.copy())
    
    # Ensure required fields exist
    if "settings" not in org_dict:
        org_dict["settings"] = deepcopy(DEFAULT_ORG_SETTINGS)
    
    return org_dict

def build_organization_search_query(
    name_pattern: Optional[str] = None,
    created_by: Optional[str] = None
) -> Dict[str, Any]:
    """Build search query for organizations"""
    query = {}
    
    if name_pattern:
        # Case-insensitive partial match on name
        query["name"] = {"$regex": name_pattern, "$options": "i"}
    
    if created_by:
        query["created_by"] = created_by
    
    return query
