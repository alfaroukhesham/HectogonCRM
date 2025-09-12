# cache-service/constants.py

# Cache key patterns
DASHBOARD_STATS_KEY = "dashboard:stats:{organization_id}"
REFRESH_TOKEN_KEY = "refresh_token:{user_id}:{session_id}"
OAUTH_STATE_KEY = "oauth_state:{state_hash}"
PASSWORD_RESET_KEY = "password_reset:{token_hash}"
EMAIL_VERIFICATION_KEY = "email_verification:{token_hash}"
JTI_DENYLIST_KEY = "jti_denylist:{jti}"
USER_MEMBERSHIPS_KEY = "user_memberships:{organization_id}:{user_id}"

# Cache key patterns for scanning
USER_MEMBERSHIPS_PATTERN_BY_USER = "user_memberships:*:{user_id}"
USER_MEMBERSHIPS_PATTERN_BY_ORG = "user_memberships:{organization_id}:*"
ALL_USER_MEMBERSHIPS_PATTERN = "user_memberships:*"

# Token cleanup patterns
TOKEN_CLEANUP_PATTERNS = [
    "refresh_token:*",
    "oauth_state:*", 
    "password_reset:*",
    "email_verification:*",
    "jti_denylist:*"
]

# Cache operation timeouts
OAUTH_STATE_TTL = 600  # 10 minutes
PASSWORD_RESET_TTL = 3600  # 1 hour
EMAIL_VERIFICATION_TTL = 86400  # 24 hours

# Logging messages
LOG_DASHBOARD_INVALIDATED = "Successfully invalidated dashboard cache for org: {organization_id} (keys deleted: {result})"
LOG_DASHBOARD_CACHED = "Cached dashboard stats for org: {organization_id} (TTL: {ttl}s)"
LOG_REFRESH_TOKEN_STORED = "Stored refresh token for user {user_id} with TTL {ttl_seconds}s"
LOG_REFRESH_TOKEN_REVOKED = "Revoked refresh token for user {user_id} (keys deleted: {result})"
LOG_JTI_BLACKLISTED = "Blacklisted token JTI: {jti} for {ttl_seconds}s"
LOG_MEMBERSHIP_CACHED = "Cached membership for user {user_id} in org {organization_id} (TTL: {ttl}s)"
LOG_MEMBERSHIP_INVALIDATED = "Invalidated membership cache for user {user_id} in org {organization_id} (keys deleted: {result})"
LOG_TOKEN_CLEANUP = "Token cleanup completed: {cleanup_stats}"
