# invite-service/service.py

import logging
from typing import List, Optional, TYPE_CHECKING
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

if TYPE_CHECKING:
    from app.core.email import EmailService

from app.models.invite import (
    Invite, InviteCreate, InviteUpdate, InviteResponse, InviteAccept,
    InviteRevoke, InviteListResponse, InviteStatus
)
from app.models.membership import MembershipCreate, MembershipRole, MembershipStatus
from app.core.email import EmailService

from .constants import (
    INVITE_NOT_FOUND_ERROR, INVITE_NOT_USABLE_ERROR, EMAIL_MISMATCH_ERROR,
    USER_NOT_FOUND_ERROR, ORGANIZATION_NOT_FOUND_ERROR, EMAIL_SEND_FAILED_ERROR,
    LOG_INVITE_CREATED, LOG_INVITE_ACCEPTED, LOG_INVITE_REVOKED, LOG_INVITE_EXPIRED,
    LOG_EMAIL_SENT, LOG_EMAIL_FAILED, LOG_MEMBERSHIP_CREATED, MAX_CODE_GEN_ATTEMPTS
)
from .utils import (
    generate_invite_code, create_invite_dict, create_update_dict,
    create_revoke_update_dict, create_accept_update_dict, create_atomic_accept_update,
    create_atomic_accept_filter, validate_invite_usability, check_email_match, 
    build_organization_invites_pipeline, build_expired_invites_query,
    create_expire_update_dict, convert_object_id_to_string, extract_invite_list_response_data,
    create_email_context, build_invite_query_by_code, build_invite_query_by_id,
    build_user_query_by_id, build_organization_query_by_id, validate_invite_data
)
from .types import (
    InviteOperation, InviteValidationResult, EmailDeliveryStatus,
    InviteNotFoundError, InviteExpiredError, InviteRevokedError, 
    InviteMaxUsesReachedError, EmailMismatchError, EmailDeliveryError,
    InvalidInviteDataError, InviteValidation, EmailContext
)

logger = logging.getLogger(__name__)

class InviteService:
    """Service for invite operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase, email_service: EmailService):
        self.db = db
        self.collection = db.invites
        self.organizations_collection = db.organizations
        self.users_collection = db.users
        self.email_service = email_service
    
    async def create_invite(
        self, 
        invite_data: InviteCreate, 
        invited_by: str
    ) -> Invite:
        """Create a new invite."""
        # Validate invite data
        validation_errors = validate_invite_data(invite_data.model_dump())
        if validation_errors:
            raise InvalidInviteDataError(f"Invalid invite data: {', '.join(validation_errors)}")
        
        # Generate unique invite code and insert (handle rare collisions)
        for _ in range(MAX_CODE_GEN_ATTEMPTS):
            code = generate_invite_code()
            invite_dict = create_invite_dict(invite_data.model_dump(), invited_by)
            invite_dict["code"] = code
            try:
                result = await self.collection.insert_one(invite_dict)
                invite_dict["_id"] = result.inserted_id
                invite = Invite(**convert_object_id_to_string(invite_dict))
                break
            except DuplicateKeyError as e:
                details = getattr(e, "details", {}) or {}
                key_pattern = details.get("keyPattern") or {}
                # Retry only if the unique index that failed involves the "code" field.
                if "code" in key_pattern or " code " in str(e):
                    logger.warning("Invite code collision detected; regenerating.")
                    continue
                # Different unique violation (e.g., email/org). Surface original error.
                raise
        else:
            raise RuntimeError("Failed to generate a unique invite code after multiple attempts.")
        
        logger.info(LOG_INVITE_CREATED.format(
            code=code, 
            organization_id=invite_data.organization_id, 
            invited_by=invited_by
        ))
        
        # Send invite email if email is provided
        if invite_data.email:
            try:
                await self._send_invite_email(invite)
            except Exception as e:
                logger.warning(LOG_EMAIL_FAILED.format(code=code, error=str(e)))
                # Continue - don't fail invite creation due to email failure
        
        return invite
    
    async def get_invite_by_code(self, code: str) -> Optional[Invite]:
        """Get invite by code."""
        try:
            invite_data = await self.collection.find_one(build_invite_query_by_code(code))
            if invite_data:
                invite_data = convert_object_id_to_string(invite_data)
                return Invite(**invite_data)
            return None
        except Exception as e:
            logger.error(f"Error getting invite by code {code}: {e}")
            return None
    
    async def get_invite_by_id(self, invite_id: str) -> Optional[Invite]:
        """Get invite by ID."""
        try:
            invite_data = await self.collection.find_one(build_invite_query_by_id(invite_id))
            if invite_data:
                invite_data = convert_object_id_to_string(invite_data)
                return Invite(**invite_data)
            return None
        except Exception as e:
            logger.error(f"Error getting invite by ID {invite_id}: {e}")
            return None
    
    async def update_invite(
        self, 
        invite_id: str, 
        invite_data: InviteUpdate
    ) -> Optional[Invite]:
        """Update invite."""
        update_dict = create_update_dict(invite_data.model_dump())
        if not update_dict:
            return await self.get_invite_by_id(invite_id)
        
        try:
            result = await self.collection.update_one(
                build_invite_query_by_id(invite_id),
                {"$set": update_dict}
            )
            
            if result.modified_count:
                return await self.get_invite_by_id(invite_id)
            return None
        except Exception as e:
            logger.error(f"Error updating invite {invite_id}: {e}")
            return None
    
    async def revoke_invite(
        self, 
        invite_id: str, 
        revoked_by: str, 
        reason: Optional[str] = None
    ) -> Optional[Invite]:
        """Revoke an invite."""
        update_dict = create_revoke_update_dict(revoked_by, reason)
        
        try:
            result = await self.collection.update_one(
                build_invite_query_by_id(invite_id),
                {"$set": update_dict}
            )
            
            if result.modified_count:
                logger.info(LOG_INVITE_REVOKED.format(invite_id=invite_id, revoked_by=revoked_by))
                return await self.get_invite_by_id(invite_id)
            return None
        except Exception as e:
            logger.error(f"Error revoking invite {invite_id}: {e}")
            return None
    
    async def accept_invite(
        self, 
        code: str, 
        user_id: str
    ) -> Optional[Invite]:
        """Accept an invite and create membership with atomic operations to prevent race conditions."""
        # Get and validate invite
        invite = await self.get_invite_by_code(code)
        if not invite:
            raise InviteNotFoundError(INVITE_NOT_FOUND_ERROR)
        
        # Validate invite usability (basic checks)
        validation = validate_invite_usability(invite.model_dump())
        if not validation.is_valid:
            if validation.result == InviteValidationResult.EXPIRED:
                raise InviteExpiredError(validation.message)
            elif validation.result == InviteValidationResult.REVOKED:
                raise InviteRevokedError(validation.message)
            elif validation.result == InviteValidationResult.MAX_USES_REACHED:
                raise InviteMaxUsesReachedError(validation.message)
            else:
                raise InviteNotFoundError(INVITE_NOT_USABLE_ERROR)
        
        # Check email match if invite is for specific email
        if invite.email:
            user_data = await self.users_collection.find_one(build_user_query_by_id(user_id))
            if not user_data:
                raise InviteNotFoundError(USER_NOT_FOUND_ERROR)
            
            if not check_email_match(invite.model_dump(), user_data["email"]):
                raise EmailMismatchError(EMAIL_MISMATCH_ERROR)
        
        # Atomic update to prevent race conditions
        try:
            # Use atomic update with conditions to ensure usage limits are respected
            atomic_filter = create_atomic_accept_filter(invite.id)
            atomic_update = create_atomic_accept_update(user_id)
            
            result = await self.collection.update_one(atomic_filter, atomic_update)
            
            if result.modified_count == 0:
                # The atomic update failed, which means either:
                # 1. The invite is no longer pending
                # 2. The usage limit has been reached
                # 3. The invite was modified between our initial check and this update
                
                # Re-fetch the invite to get current state
                current_invite = await self.get_invite_by_id(invite.id)
                if not current_invite:
                    raise InviteNotFoundError(INVITE_NOT_FOUND_ERROR)
                
                # Check what changed
                if current_invite.status != InviteStatus.PENDING.value:
                    if current_invite.status == InviteStatus.ACCEPTED.value:
                        raise InviteMaxUsesReachedError("Invite has already been accepted")
                    elif current_invite.status == InviteStatus.REVOKED.value:
                        raise InviteRevokedError("Invite has been revoked")
                    elif current_invite.status == InviteStatus.EXPIRED.value:
                        raise InviteExpiredError("Invite has expired")
                
                # If still pending, it means usage limit was reached
                if current_invite.current_uses >= current_invite.max_uses:
                    raise InviteMaxUsesReachedError("Invite has reached maximum uses")
                
                # If we get here, something else went wrong
                raise InviteNotFoundError(INVITE_NOT_USABLE_ERROR)
            
            # Create membership after successful atomic update
            from app.services import MembershipService
            membership_service = MembershipService(self.db)
            
            membership_data = MembershipCreate(
                user_id=user_id,
                organization_id=invite.organization_id,
                role=MembershipRole(invite.target_role),
                status=MembershipStatus.ACTIVE,
                invited_by=invite.invited_by
            )
            
            await membership_service.create_membership(membership_data)
            
            logger.info(LOG_MEMBERSHIP_CREATED.format(
                user_id=user_id, 
                organization_id=invite.organization_id
            ))
            
            logger.info(LOG_INVITE_ACCEPTED.format(code=code, user_id=user_id))
            
            return await self.get_invite_by_id(invite.id)
            
        except ValueError as e:
            # Re-raise validation errors (e.g., user already member)
            raise e
        except Exception as e:
            logger.error(f"Error accepting invite {code}: {e}")
            raise
    
    async def get_organization_invites(
        self, 
        organization_id: str, 
        status: Optional[InviteStatus] = None
    ) -> List[InviteListResponse]:
        """Get all invites for an organization."""
        try:
            pipeline = build_organization_invites_pipeline(
                organization_id, 
                status.value if status else None
            )
            
            invites = []
            async for doc in self.collection.aggregate(pipeline):
                try:
                    invite_data = extract_invite_list_response_data(doc)
                    invite = InviteListResponse(**invite_data)
                    invites.append(invite)
                except Exception as e:
                    logger.error(f"Error processing invite document: {e}")
                    continue
            
            return invites
        except Exception as e:
            logger.error(f"Error getting organization invites for {organization_id}: {e}")
            return []
    
    async def cleanup_expired_invites(self) -> int:
        """Mark expired invites as expired."""
        try:
            query = build_expired_invites_query()
            update = create_expire_update_dict()
            
            result = await self.collection.update_many(query, update)
            
            if result.modified_count > 0:
                logger.info(LOG_INVITE_EXPIRED.format(count=result.modified_count))
            
            return result.modified_count
        except Exception as e:
            logger.error(f"Error cleaning up expired invites: {e}")
            return 0
    
    async def _send_invite_email(self, invite: Invite):
        """Send invite email to user."""
        try:
            # Get organization details
            org_data = await self.organizations_collection.find_one(
                build_organization_query_by_id(invite.organization_id)
            )
            
            if not org_data:
                raise EmailDeliveryError(ORGANIZATION_NOT_FOUND_ERROR)
            
            # Get inviter details
            inviter_data = await self.users_collection.find_one(
                build_user_query_by_id(invite.invited_by)
            )
            
            if not inviter_data:
                raise EmailDeliveryError(USER_NOT_FOUND_ERROR)
            
            # Create email context
            email_context = create_email_context(
                invite.model_dump(), 
                org_data, 
                inviter_data
            )
            
            # Send email
            await self.email_service.send_organization_invite(
                to_email=email_context.to_email,
                organization_name=email_context.organization_name,
                inviter_name=email_context.inviter_name,
                invite_code=email_context.invite_code,
                role=email_context.role,
                expires_at=email_context.expires_at
            )
            
            logger.info(LOG_EMAIL_SENT.format(code=invite.code, email="[redacted]"))
            
        except Exception as e:
            logger.error(LOG_EMAIL_FAILED.format(code=invite.code, error=str(e)))
            raise EmailDeliveryError(EMAIL_SEND_FAILED_ERROR)
    
    async def resend_invite_email(self, invite_id: str) -> bool:
        """Resend invite email."""
        try:
            invite = await self.get_invite_by_id(invite_id)
            if not invite or not invite.email:
                return False
            
            # Validate invite is still usable
            validation = validate_invite_usability(invite.model_dump())
            if not validation.is_valid:
                return False
            
            await self._send_invite_email(invite)
            return True
            
        except Exception as e:
            logger.error(f"Error resending invite email for {invite_id}: {e}")
            return False
    
    async def validate_invite(self, code: str) -> dict:
        """Validate an invite and return detailed status."""
        try:
            invite = await self.get_invite_by_code(code)
            if not invite:
                return {
                    "is_valid": False,
                    "code": code,
                    "status": "not_found",
                    "message": INVITE_NOT_FOUND_ERROR
                }
            
            validation = validate_invite_usability(invite.model_dump())
            
            # Get organization name for response
            org_data = await self.organizations_collection.find_one(
                build_organization_query_by_id(invite.organization_id)
            )
            
            return {
                "is_valid": validation.is_valid,
                "code": code,
                "status": validation.result.value,
                "message": validation.message,
                "organization_name": org_data["name"] if org_data else None,
                "target_role": invite.target_role,
                "expires_at": invite.expires_at,
                "is_expired": validation.result == InviteValidationResult.EXPIRED,
                "uses_remaining": invite.max_uses - invite.current_uses if validation.is_valid else 0
            }
            
        except Exception as e:
            logger.error(f"Error validating invite {code}: {e}")
            return {
                "is_valid": False,
                "code": code,
                "status": "error",
                "message": "Internal server error"
            }
    
    async def get_invite_stats(self, organization_id: Optional[str] = None) -> dict:
        """Get invite statistics."""
        try:
            match_query = {}
            if organization_id:
                match_query["organization_id"] = organization_id
            
            pipeline = [
                {"$match": match_query},
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            stats = {
                "total_invites": 0,
                "pending_invites": 0,
                "accepted_invites": 0,
                "revoked_invites": 0,
                "expired_invites": 0
            }
            
            async for doc in self.collection.aggregate(pipeline):
                status = doc["_id"]
                count = doc["count"]
                stats["total_invites"] += count
                
                if status == InviteStatus.PENDING.value:
                    stats["pending_invites"] = count
                elif status == InviteStatus.ACCEPTED.value:
                    stats["accepted_invites"] = count
                elif status == InviteStatus.REVOKED.value:
                    stats["revoked_invites"] = count
                elif status == InviteStatus.EXPIRED.value:
                    stats["expired_invites"] = count
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting invite stats: {e}")
            return {
                "total_invites": 0,
                "pending_invites": 0,
                "accepted_invites": 0,
                "revoked_invites": 0,
                "expired_invites": 0
            }
