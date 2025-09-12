# organization-service/__init__.py

from fastapi import Depends
from .service import OrganizationService
from .models import *
from .types import *
from .utils import *
from .constants import *

# Dependency injection function
from app.core.database import get_database

async def get_organization_service(
    db = Depends(get_database)
) -> OrganizationService:
    return OrganizationService(db)

__all__ = [
    # Main service
    "OrganizationService",
    "get_organization_service",
    
    # Models from app.models.organization (re-exported)
    "Organization",
    "OrganizationCreate",
    "OrganizationUpdate",
    "OrganizationResponse",
    "OrganizationSettings",
    
    # Service-specific models
    "OrganizationQuery",
    "OrganizationStats",
    "OrganizationListRequest",
    "DefaultOrganizationRequest",
    "OrganizationBulkOperation",
    "OrganizationSearchFilters",
    "OrganizationMembershipSummary",
    "OrganizationSettingsUpdate",
    "SlugAvailabilityCheck",
    "SlugAvailabilityResponse",
    "OrganizationCreationRequest",
    
    # Types
    "OrganizationOperation",
    "SlugGenerationStrategy",
    "DatabaseType",
    "OrganizationDict",
    "OrganizationList",
    "UserId",
    "OrganizationId",
    "SlugString",
    "OrganizationResult",
    "OrganizationError",
    "InvalidSlugError",
    "SlugExistsError",
    "OrganizationNotFoundError",
    "InvalidOrganizationDataError",
    "BulkOrganizationOperation",
    "OrganizationFilters",
    
    # Utils
    "validate_slug_format",
    "clean_slug_string",
    "generate_slug_from_name",
    "generate_unique_slug",
    "create_organization_dict",
    "create_update_dict",
    "convert_object_id_to_string",
    "build_organization_query_by_ids",
    "build_membership_query_for_user",
    "extract_organization_ids_from_memberships",
    "validate_organization_name",
    "validate_user_id",
    "sanitize_organization_name",
    "create_default_organization_name",
    "validate_slug_length",
    "is_slug_format_valid",
    "prepare_organization_for_response",
    "build_organization_search_query",
    
    # Constants
    "ORG_NAME_REQUIRED_ERROR",
    "ORG_SLUG_REQUIRED_ERROR",
    "INVALID_SLUG_FORMAT_ERROR",
    "SLUG_TOO_LONG_ERROR",
    "CREATED_BY_REQUIRED_ERROR",
    "SLUG_EXISTS_ERROR",
    "USER_ID_REQUIRED_ERROR",
    "MAX_SLUG_LENGTH",
    "DEFAULT_LIST_LIMIT",
    "SLUG_PATTERN",
    "DEFAULT_ORG_SETTINGS"
]