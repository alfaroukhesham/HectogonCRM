# invite-service/utils.py

import secrets
import string
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from bson import ObjectId

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
    invite_dict["invited_by"] = invited_by
    invite_dict["created_at"] = datetime.now(timezone.utc)
    invite_dict["updated_at"] = datetime.now(timezone.utc)
    
    # Validate expires_at timezone if provided
    if "expires_at" in invite_dict:
        expires_at = invite_dict["expires_at"]
        if isinstance(expires_at, datetime) and expires_at.tzinfo is None:
            # Convert naive datetime to UTC for robustness
            invite_dict["expires_at"] = expires_at.replace(tzinfo=timezone.utc)
    
    # Set defaults if not provided
    if "max_uses" not in invite_dict:
        invite_dict["max_uses"] = DEFAULT_MAX_USES
    
    if "current_uses" not in invite_dict:
        invite_dict["current_uses"] = 0
    
    if "expires_at" not in invite_dict:
        invite_dict["expires_at"] = datetime.now(timezone.utc) + timedelta(hours=DEFAULT_EXPIRES_HOURS)
    
    if "status" not in invite_dict:
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
    """Create update dictionary for accepting an invite"""
    return {
        "status": InviteStatus.ACCEPTED.value,
        "used_by": user_id,
        "used_at": datetime.now(timezone.utc),
        "current_uses": current_uses + 1,
        "updated_at": datetime.now(timezone.utc)
    }

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
    
    # Check expiration
    expires_at = invite.get("expires_at")
    if expires_at:
        # Ensure timezone-aware comparison
        if isinstance(expires_at, datetime) and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
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
    if "_id" in doc and isinstance(doc["_id"], ObjectId):
        doc["_id"] = str(doc["_id"])
    return doc

def extract_invite_list_response_data(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Extract data for InviteListResponse from aggregation result"""
    org = doc["organization"]
    inviter = doc["inviter"]
    now = datetime.now(timezone.utc)
    
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
        "is_expired": doc["expires_at"] < now,
        "is_usable": (
            doc["status"] == InviteStatus.PENDING.value and
            doc["expires_at"] > now and
            doc["current_uses"] < doc["max_uses"]
        )
    }

def create_email_context(
    invite: Dict[str, Any],
    org_data: Dict[str, Any],
    inviter_data: Dict[str, Any]
) -> EmailContext:
    """Create email context for sending invite emails"""
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
    # Ensure timezone-aware comparison
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at < datetime.now(timezone.utc)
    
def build_invite_query_by_code(code: str) -> Dict[str, Any]:
    """Build query to find invite by code"""
    return {"code": code}

def validate_and_convert_object_id(id_value: str, id_name: str) -> ObjectId:
    """Validate ObjectId string and convert to ObjectId"""
    if not ObjectId.is_valid(id_value):
        raise ValueError(f"Invalid {id_name}: {id_value}")
    return ObjectId(id_value)

def build_invite_query_by_id(invite_id: str) -> Dict[str, Any]:
    """Build query to find invite by ID"""
    return {"_id": validate_and_convert_object_id(invite_id, "invite ID")}

def build_user_query_by_id(user_id: str) -> Dict[str, Any]:
    """Build query to find user by ID"""
    return {"_id": validate_and_convert_object_id(user_id, "user ID")}

def build_organization_query_by_id(organization_id: str) -> Dict[str, Any]:
    """Build query to find organization by ID"""
    return {"_id": validate_and_convert_object_id(organization_id, "organization ID")}
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
    
    # Validate expires_at if provided
    expires_at = invite_data.get("expires_at")
    if expires_at:
        if isinstance(expires_at, datetime):
            # Ensure timezone-aware comparison
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at <= datetime.now(timezone.utc):
                errors.append("Expiration date must be in the future")
        else:
            errors.append("Expiration date must be a datetime object")
    
    return errors
