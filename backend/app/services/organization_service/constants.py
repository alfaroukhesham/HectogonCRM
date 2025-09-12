# organization-service/constants.py

from types import MappingProxyType

# Error messages
ORG_NAME_REQUIRED_ERROR = "Organization name is required"
ORG_SLUG_REQUIRED_ERROR = "Organization slug is required"
INVALID_SLUG_FORMAT_ERROR = "Slug must start and end with alphanumeric characters, contain only lowercase letters, numbers, and hyphens"
SLUG_TOO_LONG_ERROR = "Slug must be 80 characters or less"
CREATED_BY_REQUIRED_ERROR = "Created by user ID is required"
SLUG_EXISTS_ERROR = "Organization with slug '{slug}' already exists"
USER_ID_REQUIRED_ERROR = "User ID is required"

# Collection names
ORGANIZATIONS_COLLECTION = "organizations"
MEMBERSHIPS_COLLECTION = "memberships"

# Default values
DEFAULT_USER_NAME = "User"
DEFAULT_ORG_DESCRIPTION = "Default organization created during registration"
DEFAULT_SLUG_PREFIX = "user"

# Limits
MAX_SLUG_LENGTH = 80
DEFAULT_LIST_LIMIT = 100
UUID_SUFFIX_LENGTH = 8

# Regex patterns
SLUG_PATTERN = r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'
SLUG_CLEANUP_PATTERN = r'[^a-z0-9-]'

# MongoDB aggregation stages
ORGANIZATION_LOOKUP_STAGE = {
    "$lookup": {
        "from": ORGANIZATIONS_COLLECTION,
        "localField": "organization_id", 
        "foreignField": "_id",
        "as": "organization"
    }
}

# Safer pipeline-style lookup with field projection
ORGANIZATION_LOOKUP_STAGE_PIPELINE = {
    "$lookup": {
        "from": ORGANIZATIONS_COLLECTION,
        "let": {"orgId": "$organization_id"},
        "pipeline": [
            {"$match": {"$expr": {"$eq": ["$_id", "$$orgId"]}}},
            {"$project": {"_id": 1, "name": 1, "slug": 1}}  # restrict fields
        ],
        "as": "organization",
    }
}

# Default organization settings (immutable)
DEFAULT_ORG_SETTINGS = MappingProxyType({
    "allow_public_signup": False,
    "require_email_verification": True,
    "default_member_role": "viewer",
    "max_members": None,
})

# Log messages
LOG_ORG_CREATED = "Created organization {name} with slug {slug} for user {user_id}"
LOG_ORG_UPDATED = "Updated organization {org_id}"
LOG_ORG_DELETED = "Deleted organization {org_id} and {membership_count} memberships"
LOG_SLUG_GENERATION = "Generated unique slug {slug} for user {user_name}"
LOG_DEFAULT_ORG_CREATED = "Created default organization for user {user_id}: {org_name}"
