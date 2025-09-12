# invite-service/constants.py

from datetime import datetime

# Error messages
INVITE_NOT_FOUND_ERROR = "Invite not found"
INVITE_EXPIRED_ERROR = "Invite has expired"
INVITE_REVOKED_ERROR = "Invite has been revoked"
INVITE_MAX_USES_REACHED_ERROR = "Invite has reached maximum uses"
INVITE_NOT_USABLE_ERROR = "Invite is not usable"
EMAIL_MISMATCH_ERROR = "This invite is for a specific email address"
USER_NOT_FOUND_ERROR = "User not found"
ORGANIZATION_NOT_FOUND_ERROR = "Organization not found"
USER_ALREADY_MEMBER_ERROR = "User is already a member of this organization"
EMAIL_SEND_FAILED_ERROR = "Failed to send invite email"

# Collection names
INVITES_COLLECTION = "invites"
ORGANIZATIONS_COLLECTION = "organizations"
USERS_COLLECTION = "users"

# Retry limits
MAX_CODE_GEN_ATTEMPTS = 5

# Default values
DEFAULT_MAX_USES = 1
DEFAULT_EXPIRES_HOURS = 168  # 7 days
DEFAULT_INVITE_ROLE = "viewer"

# MongoDB aggregation pipeline components
ORGANIZATION_LOOKUP_STAGE = {
    "$lookup": {
        "from": "organizations",
        "localField": "organization_id",
        "foreignField": "_id",
        "as": "organization"
    }
}

INVITER_LOOKUP_STAGE = {
    "$lookup": {
        "from": "users",
        "localField": "invited_by",
        "foreignField": "_id",
        "as": "inviter"
    }
}

UNWIND_ORGANIZATION_STAGE = {"$unwind": "$organization"}
UNWIND_INVITER_STAGE = {"$unwind": "$inviter"}

# Email template keys
EMAIL_TEMPLATE_ORGANIZATION_INVITE = "organization_invite"
EMAIL_TEMPLATE_INVITE_REMINDER = "invite_reminder"

# Invite code generation
INVITE_CODE_LENGTH = 32
INVITE_CODE_CHARSET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

# Time constants
SECONDS_PER_HOUR = 3600
HOURS_PER_DAY = 24

# Log messages
LOG_INVITE_CREATED = "Created invite {code} for organization {organization_id} by user {invited_by}"
LOG_INVITE_ACCEPTED = "Invite {code} accepted by user {user_id}"
LOG_INVITE_REVOKED = "Invite {invite_id} revoked by user {revoked_by}"
LOG_INVITE_EXPIRED = "Marked {count} expired invites as expired"
LOG_EMAIL_SENT = "Sent invite email for invite {code} to {email}"
LOG_EMAIL_FAILED = "Failed to send invite email for invite {code}: {error}"
LOG_MEMBERSHIP_CREATED = "Created membership for user {user_id} in organization {organization_id}"

# Query patterns
def get_expired_invites_query(current_time: datetime = None) -> dict:
    """Get query for expired invites.
    
    Args:
        current_time: Optional datetime to compare against. Defaults to datetime.utcnow()
        
    Returns:
        MongoDB query dict for expired invites
    """
    if current_time is None:
        current_time = datetime.utcnow()
    
    return {
        "status": "pending",
        "expires_at": {"$lt": current_time}
    }

def usable_invite_filter(now):
    return {
        "status": "pending",
        "expires_at": {"$gt": now},
        "$expr": {
            "$lt": [
                {"$ifNull": ["$current_uses", 0]},
                {"$ifNull": ["$max_uses", DEFAULT_MAX_USES]},
            ]
        },
    }
# Status transitions
VALID_STATUS_TRANSITIONS = {
    "pending": ["accepted", "revoked", "expired"],
    "accepted": [],
    "revoked": [],
    "expired": []
}

# Role validation
VALID_INVITE_ROLES = ["viewer", "editor", "admin"]

# Limits
MAX_INVITES_PER_ORGANIZATION = 1000
MAX_INVITES_PER_USER_PER_DAY = 50
MAX_INVITE_CODE_GENERATION_ATTEMPTS = 10
