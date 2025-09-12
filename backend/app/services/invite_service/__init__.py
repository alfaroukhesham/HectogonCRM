# invite-service/__init__.py

from fastapi import Depends
from .service import InviteService
from .models import *
from .types import *
from .utils import *
from .constants import *

# Dependency injection function
from app.core.database import get_database
from app.core.email import EmailService

async def get_invite_service(
    db = Depends(get_database)
) -> InviteService:
    # Create EmailService instance for now - in production this would be properly injected
    from app.core.email import email_service
    return InviteService(db, email_service)

__all__ = [
    # Main service
    "InviteService",
    "get_invite_service",
    
    # Models from app.models.invite (re-exported)
    "Invite",
    "InviteCreate",
    "InviteUpdate",
    "InviteResponse",
    "InviteAccept",
    "InviteRevoke",
    "InviteListResponse",
    "InviteStatus",
    
    # Service-specific models
    "InviteQuery",
    "InviteStats",
    "InviteBulkOperation",
    "InviteSearchFilters",
    "InviteCreationRequest",
    "InviteAcceptanceRequest",
    "InviteRevocationRequest",
    "InviteListRequest",
    "InviteValidationResponse",
    "InviteEmailRequest",
    "InviteCleanupRequest",
    "InviteCleanupResponse",
    "OrganizationInviteSummary",
    "UserInviteSummary",
    
    # Types
    "InviteOperation",
    "InviteValidationResult",
    "EmailDeliveryStatus",
    "DatabaseType",
    "EmailServiceType",
    "InviteDict",
    "InviteList",
    "UserId",
    "OrganizationId",
    "InviteId",
    "InviteCode",
    "EmailAddress",
    "InviteResult",
    "InviteValidation",
    "InviteError",
    "InviteNotFoundError",
    "InviteExpiredError",
    "InviteRevokedError",
    "InviteMaxUsesReachedError",
    "EmailMismatchError",
    "EmailDeliveryError",
    "InvalidInviteDataError",
    "BulkInviteOperation",
    "InviteFilters",
    "EmailContext",
    
    # Utils
    "generate_invite_code",
    "create_invite_dict",
    "create_update_dict",
    "create_revoke_update_dict",
    "create_accept_update_dict",
    "validate_invite_usability",
    "check_email_match",
    "build_organization_invites_pipeline",
    "build_expired_invites_query",
    "create_expire_update_dict",
    "convert_object_id_to_string",
    "extract_invite_list_response_data",
    "create_email_context",
    "is_valid_invite_role",
    "can_transition_status",
    "calculate_expires_at",
    "is_invite_expired",
    "build_invite_query_by_code",
    "build_invite_query_by_id",
    "build_user_query_by_id",
    "build_organization_query_by_id",
    "generate_unique_invite_code",
    "validate_invite_data",
    
    # Constants
    "INVITE_NOT_FOUND_ERROR",
    "INVITE_EXPIRED_ERROR",
    "INVITE_REVOKED_ERROR",
    "INVITE_MAX_USES_REACHED_ERROR",
    "INVITE_NOT_USABLE_ERROR",
    "EMAIL_MISMATCH_ERROR",
    "USER_NOT_FOUND_ERROR",
    "ORGANIZATION_NOT_FOUND_ERROR",
    "EMAIL_SEND_FAILED_ERROR",
    "DEFAULT_MAX_USES",
    "DEFAULT_EXPIRES_HOURS",
    "INVITE_CODE_LENGTH",
    "VALID_INVITE_ROLES"
]