# invite-service/utils.py

import secrets
import string
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from bson import ObjectId
from bson.errors import InvalidId

from .constants import (
    INVITE_CODE_LENGTH, INVITE_CODE_CHARSET, DEFAULT_EXPIRES_HOURS,
    DEFAULT_MAX_USES, ORGANIZATION_LOOKUP_STAGE, INVITER_LOOKUP_STAGE,
    UNWIND_ORGANIZATION_STAGE, UNWIND_INVITER_STAGE, VALID_INVITE_ROLES,
    VALID_STATUS_TRANSITIONS, MAX_INVITE_CODE_GENERATION_ATTEMPTS
)
from .types import (
    InviteDict, InviteCode, InviteValidation, InviteValidationResult,
    EmailContext, InviteStatus
)

def generate_invite_code(length: int = INVITE_CODE_LENGTH) -> InviteCode:
    """Generate a secure random invite code"""
    return ''.join(secrets.choice(INVITE_CODE_CHARSET) for _ in range(length))

def create_invite_dict(invite_data: Dict[str, Any], invited_by: str) -> InviteDict:
    """Create invite dictionary with timestamps and defaults"""
    invite_dict = invite_data.copy()
    now = datetime.now(timezone.utc)
    invite_dict["invited_by"] = invited_by
    invite_dict["created_at"] = now
    invite_dict["updated_at"] = now
    
    # Set defaults if not provided
    if "max_uses" not in invite_dict:
        invite_dict["max_uses"] = DEFAULT_MAX_USES

    # Always force server-controlled fields
    invite_dict["current_uses"] = 0
    
    if "expires_at" in invite_dict and isinstance(invite_dict["expires_at"], datetime):
        invite_dict["expires_at"] = ensure_utc_aware(invite_dict["expires_at"])
    else:
        invite_dict["expires_at"] = now + timedelta(hours=DEFAULT_EXPIRES_HOURS)
    
    invite_dict["status"] = InviteStatus.PENDING.value
    
    return invite_dict

def create_update_dict(update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create update dictionary filtering None values and adding timestamp"""
    update_dict = {k: v for k, v in update_data.items() if v is not None}
    if update_dict:  # Only add timestamp if there are actual updates
        update_dict["updated_at"] = datetime.now(timezone.utc)
    return update_dict

def create_revoke_update_dict(revoked_by: str, reason: Optional[str] = None) -> Dict[str, Any]:
    """Create update dictionary for revoking an invite"""
    update_dict = {
        "status": InviteStatus.REVOKED.value,
        "revoked_by": revoked_by,
        "revoked_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    if reason:
        update_dict["revoke_reason"] = reason
    
    return update_dict

def create_accept_update_dict(user_id: str, current_uses: int) -> Dict[str, Any]:
    """Create update dictionary for accepting an invite
    
    Note: This function increments current_uses but doesn't validate against max_uses.
    The actual validation should be handled at the database level using atomic operations
    like $inc with conditions to prevent race conditions where multiple concurrent accepts
    could bypass the usage limit.
    
    Note: Status is not set to ACCEPTED here to allow multi-use invites to remain PENDING
    until fully consumed.
    """
    return {
        "used_by": user_id,
        "used_at": datetime.now(timezone.utc),
        "current_uses": current_uses + 1,
        "updated_at": datetime.now(timezone.utc)
    }

def create_atomic_accept_update(user_id: str) -> Dict[str, Any]:
    """Create atomic update for accepting an invite with race condition protection.
    
    This uses MongoDB's atomic $inc operation with conditions to prevent race conditions
    where multiple concurrent accepts could bypass the usage limit.
    
    Note: Status is not set to ACCEPTED here to allow multi-use invites to remain PENDING
    until fully consumed.
    """
    now = datetime.now(timezone.utc)
    
    return {
        "$inc": {"current_uses": 1},
        "$set": {
            "used_by": user_id,
            "used_at": now,
            "updated_at": now
        }
    }

def create_atomic_accept_filter(invite_id: str) -> Dict[str, Any]:
    """Create filter for atomic invite acceptance that ensures usage limits are respected."""
    try:
        _id = ObjectId(invite_id)
    except InvalidId:
        raise ValueError(f"Invalid invite ID format: {invite_id}")
    now = datetime.now(timezone.utc)
    return {
        "_id": _id,
        "status": InviteStatus.PENDING.value,
        "expires_at": {"$gt": now},
        "$expr": {"$lt": ["$current_uses", "$max_uses"]},
    }

def create_atomic_accept_update_pipeline(user_id: str) -> List[Dict[str, Any]]:
    """Create pipeline update that flips status only when the last use is taken (MongoDB 4.2+).
    
    This ensures multi-use invites remain PENDING until fully consumed, then flip to ACCEPTED.
    """
    now = datetime.now(timezone.utc)
    return [
        {
            "$set": {
                "current_uses": {"$add": ["$current_uses", 1]},
                "used_by": user_id,
                "used_at": now,
                "updated_at": now,
                "status": {
                    "$cond": [
                        {"$gte": [{"$add": ["$current_uses", 1]}, "$max_uses"]},
                        InviteStatus.ACCEPTED.value,
                        InviteStatus.PENDING.value,
                    ]
                },
            }
        }
    ]

def ensure_utc_aware(dt: datetime) -> datetime:
    """Ensure datetime is UTC-aware to prevent comparison errors"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def validate_invite_usability(invite: Dict[str, Any]) -> InviteValidation:
    """Validate if an invite is usable"""
    now = datetime.now(timezone.utc)
    
    # Check if invite exists
    if not invite:
        return InviteValidation(False, InviteValidationResult.NOT_FOUND, "Invite not found")
    
    # Check status
    status = invite.get("status", "pending")
    if status == InviteStatus.REVOKED.value:
        return InviteValidation(False, InviteValidationResult.REVOKED, "Invite has been revoked")
    
    if status == InviteStatus.EXPIRED.value:
        return InviteValidation(False, InviteValidationResult.EXPIRED, "Invite has expired")
    
    # Check expiration with timezone safety
    expires_at = invite.get("expires_at")
    if isinstance(expires_at, datetime):
        exp = ensure_utc_aware(expires_at)
        if exp < now:
            return InviteValidation(False, InviteValidationResult.EXPIRED, "Invite has expired")
    elif expires_at:
        return InviteValidation(False, InviteValidationResult.EXPIRED, "Invite has expired")
    
    # Check usage limits
    current_uses = invite.get("current_uses", 0)
    max_uses = invite.get("max_uses", 1)
    if current_uses >= max_uses:
        return InviteValidation(
            False, 
            InviteValidationResult.MAX_USES_REACHED, 
            "Invite has reached maximum uses"
        )
    
    return InviteValidation(True, InviteValidationResult.VALID, "Invite is valid")

def check_email_match(invite: Dict[str, Any], user_email: str) -> bool:
    """Check if user email matches invite email requirement"""
    invite_email = invite.get("email")
    if not invite_email:
        return True  # No email restriction
    
    return invite_email.lower() == user_email.lower()

def build_organization_invites_pipeline(organization_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Build aggregation pipeline for organization invites"""
    match_query = {"organization_id": organization_id}
    if status:
        match_query["status"] = status
    
    return [
        {"$match": match_query},
        ORGANIZATION_LOOKUP_STAGE,
        UNWIND_ORGANIZATION_STAGE,
        INVITER_LOOKUP_STAGE,
        UNWIND_INVITER_STAGE
    ]

def build_expired_invites_query() -> Dict[str, Any]:
    """Build query to find expired invites"""
    return {
        "status": InviteStatus.PENDING.value,
        "expires_at": {"$lt": datetime.now(timezone.utc)}
    }

def create_expire_update_dict() -> Dict[str, Any]:
    """Create update dictionary for expiring invites"""
    return {
        "$set": {
            "status": InviteStatus.EXPIRED.value,
            "updated_at": datetime.now(timezone.utc)
        }
    }

def convert_object_id_to_string(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB ObjectId to string in document"""
    doc = doc.copy()
    if "_id" in doc and isinstance(doc["_id"], ObjectId):
        doc["_id"] = str(doc["_id"])
    return doc

def extract_invite_list_response_data(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Extract data for InviteListResponse from aggregation result"""
    org = doc["organization"]
    inviter = doc["inviter"]
    now = datetime.now(timezone.utc)
    exp = ensure_utc_aware(doc["expires_at"])
    
    return {
        "id": str(doc["_id"]),
        "code": doc["code"],
        "organization_id": str(org["_id"]),
        "organization_name": org["name"],
        "invited_by": str(inviter["_id"]),
        "invited_by_name": inviter["full_name"],
        "target_role": doc["target_role"],
        "email": doc.get("email"),
        "status": doc["status"],
        "expires_at": doc["expires_at"],
        "max_uses": doc["max_uses"],
        "current_uses": doc["current_uses"],
        "created_at": doc["created_at"],
        "is_expired": exp < now,
        "is_usable": (
            doc["status"] == InviteStatus.PENDING.value and
            exp > now and
            doc["current_uses"] < doc["max_uses"]
        )
    }

def create_email_context(
    invite: Dict[str, Any],
    org_data: Dict[str, Any],
    inviter_data: Dict[str, Any]
) -> EmailContext:
    """Create email context for sending invite emails"""
    if not invite.get("email"):
        raise ValueError("Invite email is required to build email context")
    return EmailContext(
        to_email=invite["email"],
        organization_name=org_data["name"],
        inviter_name=inviter_data["full_name"],
        invite_code=invite["code"],
        role=invite["target_role"],
        expires_at=invite["expires_at"],
        organization_logo_url=org_data.get("logo_url")
    )

def is_valid_invite_role(role: str) -> bool:
    """Check if role is valid for invites"""
    return role in VALID_INVITE_ROLES

def can_transition_status(current_status: str, new_status: str) -> bool:
    """Check if status transition is valid"""
    valid_transitions = VALID_STATUS_TRANSITIONS.get(current_status, [])
    return new_status in valid_transitions

def calculate_expires_at(hours_from_now: int = DEFAULT_EXPIRES_HOURS) -> datetime:
    """Calculate expiration datetime"""
    return datetime.now(timezone.utc) + timedelta(hours=hours_from_now)

def is_invite_expired(expires_at: datetime) -> bool:
    """Check if invite is expired"""
    return ensure_utc_aware(expires_at) < datetime.now(timezone.utc)

def build_invite_query_by_code(code: str) -> Dict[str, Any]:
    """Build query to find invite by code"""
    return {"code": code}

def build_invite_query_by_id(invite_id: str) -> Dict[str, Any]:
    """Build query to find invite by ID"""
    try:
        return {"_id": ObjectId(invite_id)}
    except InvalidId:
        raise ValueError(f"Invalid invite ID format: {invite_id}")

def build_user_query_by_id(user_id: str) -> Dict[str, Any]:
    """Build query to find user by ID"""
    try:
        return {"_id": ObjectId(user_id)}
    except InvalidId:
        raise ValueError(f"Invalid user ID format: {user_id}")

def build_organization_query_by_id(organization_id: str) -> Dict[str, Any]:
    """Build query to find organization by ID"""
    try:
        return {"_id": ObjectId(organization_id)}
    except InvalidId:
        raise ValueError(f"Invalid organization ID format: {organization_id}")

def generate_unique_invite_code(existing_codes: set, max_attempts: int = MAX_INVITE_CODE_GENERATION_ATTEMPTS) -> Optional[str]:
    """Generate a unique invite code not in existing_codes"""
    for _ in range(max_attempts):
        code = generate_invite_code()
        if code not in existing_codes:
            return code
    return None  # Failed to generate unique code

def validate_invite_data(invite_data: Dict[str, Any]) -> List[str]:
    """Validate invite data and return list of errors"""
    errors = []
    
    # Check required fields
    if not invite_data.get("organization_id"):
        errors.append("Organization ID is required")
    
    if not invite_data.get("target_role"):
        errors.append("Target role is required")
    
    # Validate role
    target_role = invite_data.get("target_role")
    if target_role and not is_valid_invite_role(target_role):
        errors.append(f"Invalid role: {target_role}")
    
    # Validate max_uses
    max_uses = invite_data.get("max_uses", DEFAULT_MAX_USES)
    if not isinstance(max_uses, int) or max_uses <= 0:
        errors.append("Max uses must be a positive integer")
    
    # Validate expires_at if provided with timezone safety
    expires_at = invite_data.get("expires_at")
    if expires_at:
        if not isinstance(expires_at, datetime):
            errors.append("Expiration date must be a datetime")
        else:
            if ensure_utc_aware(expires_at) <= datetime.now(timezone.utc):
                errors.append("Expiration date must be in the future")
    
    return errors
