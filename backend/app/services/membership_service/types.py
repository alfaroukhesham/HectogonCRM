# membership-service/types.py

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase

# Import the membership models to re-export them
from app.models.membership import MembershipRole, MembershipStatus

class MembershipOperation(str, Enum):
    """Membership operations for logging and monitoring"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST_USER = "list_user_memberships"
    LIST_ORG = "list_org_members"

class PermissionLevel(str, Enum):
    """Permission levels for authorization checks"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

class AggregationStage(str, Enum):
    """MongoDB aggregation stage types"""
    MATCH = "$match"
    LOOKUP = "$lookup"
    UNWIND = "$unwind"
    PROJECT = "$project"
    ADD_FIELDS = "$addFields"

# Type aliases for clarity
DatabaseType = "AsyncIOMotorDatabase"
MembershipDict = Dict[str, Any]
AggregationPipeline = List[Dict[str, Any]]
QueryDict = Dict[str, Any]
ProjectionDict = Dict[str, Any]
UserId = str
OrganizationId = str
MembershipId = str

# Role hierarchy type for permission checking
RoleHierarchy = Dict[str, int]

# Service result types
class MembershipResult:
    """Result object for membership operations"""
    def __init__(self, success: bool, data: Any = None, error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error

    def __bool__(self):
        return self.success

# Error types for better error handling
class MembershipError(Exception):
    """Base membership service error"""
    pass

class UserNotFoundError(MembershipError):
    """User not found error"""
    pass

class OrganizationNotFoundError(MembershipError):
    """Organization not found error"""
    pass

class DuplicateMembershipError(MembershipError):
    """Duplicate membership error"""
    pass

class InvalidMembershipError(MembershipError):
    """Invalid membership data error"""
    pass
