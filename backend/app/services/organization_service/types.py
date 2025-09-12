# organization-service/types.py

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase

# Import organization models to re-export them
from app.models.organization import Organization, OrganizationCreate, OrganizationUpdate, OrganizationResponse
from app.models.membership import MembershipStatus

class OrganizationOperation(str, Enum):
    """Organization operations for logging and monitoring"""
    CREATE = "create"
    READ = "read" 
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    CREATE_DEFAULT = "create_default"

class SlugGenerationStrategy(str, Enum):
    """Strategies for generating organization slugs"""
    USER_NAME = "user_name"
    ORGANIZATION_NAME = "organization_name" 
    RANDOM = "random"
    UUID = "uuid"

# Type aliases for clarity
DatabaseType = "AsyncIOMotorDatabase"
OrganizationDict = Dict[str, Any]
OrganizationList = List[Organization]
UserId = str
OrganizationId = str
SlugString = str

# Service result types
class OrganizationResult:
    """Result object for organization operations"""
    def __init__(self, success: bool, data: Any = None, error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error

    def __bool__(self):
        return self.success

# Error types for better error handling
class OrganizationError(Exception):
    """Base organization service error"""
    pass

class InvalidSlugError(OrganizationError):
    """Invalid slug format error"""
    pass

class SlugExistsError(OrganizationError):
    """Slug already exists error"""
    pass

class OrganizationNotFoundError(OrganizationError):
    """Organization not found error"""
    pass

class InvalidOrganizationDataError(OrganizationError):
    """Invalid organization data error"""
    pass

# Bulk operation types
class BulkOrganizationOperation:
    """Bulk operation for organizations"""
    def __init__(self, operation: str, organizations: List[Dict[str, Any]]):
        self.operation = operation
        self.organizations = organizations

# Search and filter types
class OrganizationFilters:
    """Filters for organization queries"""
    def __init__(
        self, 
        created_by: Optional[str] = None,
        name_pattern: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None
    ):
        self.created_by = created_by
        self.name_pattern = name_pattern
        self.created_after = created_after
        self.created_before = created_before
