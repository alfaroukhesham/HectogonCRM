# membership-service/constants.py

# Error messages
USER_NOT_FOUND_ERROR = "User not found"
ORGANIZATION_NOT_FOUND_ERROR = "Organization not found"
INVALID_USER_ID_ERROR = "Invalid user ID format"
INVALID_ORGANIZATION_ID_ERROR = "Invalid organization ID format"
ALREADY_MEMBER_ERROR = "User is already a member of this organization"

# Collection names
MEMBERSHIPS_COLLECTION = "memberships"
USERS_COLLECTION = "users"
ORGANIZATIONS_COLLECTION = "organizations"

# MongoDB Aggregation Pipeline Components
def user_match_stage(user_id: str) -> dict:
    """Create a MongoDB match stage for filtering by user_id."""
    return {"$match": {"user_id": user_id}}

def org_match_stage(organization_id: str) -> dict:
    """Create a MongoDB match stage for filtering by organization_id."""
    return {"$match": {"organization_id": organization_id}}

# Projection fields for user memberships
USER_MEMBERSHIP_PROJECTION = {
    "_id": 1,
    "user_id": 1,
    "organization_id": "$organization_details._id",
    "organization_name": "$organization_details.name",
    "organization_slug": "$organization_details.slug",
    "organization_logo_url": "$organization_details.logo_url",
    "role": 1,
    "status": 1,
    "joined_at": 1,
    "last_accessed": 1
}

# Projection fields for organization members
ORG_MEMBER_PROJECTION = {
    "_id": 1,
    "user_id": "$user_details._id",
    "user_email": "$user_details.email",
    "user_name": "$user_details.full_name",
    "user_avatar_url": "$user_details.avatar_url",
    "organization_id": 1,
    "role": 1,
    "status": 1,
    "invited_by": 1,
    "joined_at": 1,
    "last_accessed": 1
}

# Role hierarchy for permission checking
ROLE_HIERARCHY = {
    "viewer": 1,
    "editor": 2,
    "admin": 3
}

# Log messages
# backend/app/services/membership_service/constants.py

LOG_GETTING_USER_MEMBERSHIPS = "Getting memberships for user: {user_id}, status: {status}"
LOG_RUNNING_AGGREGATION    = "Running optimized aggregation pipeline for user {user_id}"
LOG_PROCESSED_MEMBERSHIP   = "Successfully processed membership for organization: {organization_name}"
LOG_MEMBERSHIP_ERROR       = "Error processing membership for user {user_id} in org {organization_id}: {error}"
LOG_RETURNING_MEMBERSHIPS  = "Returning {count} memberships for user {user_id}"
LOG_USER_MEMBERSHIPS_ERROR = "Error in get_user_memberships for user {user_id}: {error}"
LOG_ORG_MEMBER_ERROR       = "Error processing organization member {user_id} in org {organization_id}: {error}"
LOG_CACHED_MEMBERSHIP_FOUND = "Found cached membership for user {user_id} in org {organization_id}"
LOG_CACHE_ERROR            = "Cache error when getting membership for user {user_id} in org {organization_id}: {error}"
LOG_FAILED_CACHE_MEMBERSHIP = "Failed to cache membership for user {user_id} in org {organization_id}: {error}"
# Default values
DEFAULT_MEMBERSHIP_STATUS = "active"
DEFAULT_ROLE = "viewer"
