# membership-service/__init__.py

from fastapi import Depends
from .service import MembershipService
from .models import *
from .types import *
from .utils import *
from .constants import *

# Dependency injection function
from app.core.database import get_database
from ..cache_service import get_cache_service

async def get_membership_service(
    db = Depends(get_database),
    cache_service = Depends(get_cache_service)
) -> MembershipService:
    return MembershipService(db, cache_service)

__all__ = [
    # Main service
    "MembershipService",
    "get_membership_service",
    
    # Models from app.models.membership (re-exported)
    "Membership",
    "MembershipCreate",
    "MembershipUpdate", 
    "MembershipResponse",
    "UserMembershipResponse",
    "OrganizationMembershipResponse",
    "MembershipRole",
    "MembershipStatus",
    "OrganizationContext",
    
    # Service-specific models
    "MembershipQuery",
    "MembershipStats",
    "MembershipBulkOperation",
    "MembershipSearchFilters",
    "MembershipAggregationResult",
    "RoleChangeRequest",
    "MembershipInviteData",
    "OrganizationMemberSummary",
    
    # Types
    "MembershipOperation",
    "PermissionLevel", 
    "AggregationStage",
    "DatabaseType",
    "MembershipDict",
    "AggregationPipeline",
    "QueryDict",
    "ProjectionDict",
    "UserId",
    "OrganizationId",
    "MembershipId",
    "RoleHierarchy",
    "MembershipResult",
    "MembershipError",
    "UserNotFoundError",
    "OrganizationNotFoundError",
    "DuplicateMembershipError",
    "InvalidMembershipError",
    
    # Utils
    "create_user_aggregation_pipeline",
    "create_organization_members_pipeline",
    "validate_object_id",
    "convert_membership_dict_to_response",
    "convert_member_dict_to_response",
    "has_sufficient_role",
    "create_membership_update_dict",
    "create_timestamp_fields",
    "prepare_cache_membership_data",
    "build_membership_query",
    "build_last_accessed_update",
    "extract_user_ids_from_memberships",
    "extract_organization_ids_from_memberships",
    
    # Constants
    "USER_NOT_FOUND_ERROR",
    "ORGANIZATION_NOT_FOUND_ERROR",
    "INVALID_USER_ID_ERROR",
    "INVALID_ORGANIZATION_ID_ERROR",
    "ALREADY_MEMBER_ERROR",
    "ROLE_HIERARCHY",
    "USER_MEMBERSHIP_PROJECTION",
    "ORG_MEMBER_PROJECTION"
]