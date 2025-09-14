# membership-service/service.py

from typing import List, Optional, TYPE_CHECKING, Any
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
import logging
from pymongo.errors import DuplicateKeyError

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase
    from app.services import CacheService

from app.models.membership import (
    Membership, MembershipCreate, MembershipUpdate, MembershipResponse,
    UserMembershipResponse, OrganizationMembershipResponse,
    MembershipRole, MembershipStatus
)
from app.models.user import User
from app.models.organization import Organization

from .constants import (
    USER_NOT_FOUND_ERROR, ORGANIZATION_NOT_FOUND_ERROR, INVALID_USER_ID_ERROR,
    INVALID_ORGANIZATION_ID_ERROR, ALREADY_MEMBER_ERROR, ROLE_HIERARCHY,
    USER_MEMBERSHIP_PROJECTION, ORG_MEMBER_PROJECTION,
    LOG_GETTING_USER_MEMBERSHIPS, LOG_RUNNING_AGGREGATION, LOG_PROCESSED_MEMBERSHIP,
    LOG_MEMBERSHIP_ERROR, LOG_RETURNING_MEMBERSHIPS, LOG_USER_MEMBERSHIPS_ERROR,
    LOG_ORG_MEMBER_ERROR, LOG_CACHED_MEMBERSHIP_FOUND, LOG_CACHE_ERROR,
    LOG_FAILED_CACHE_MEMBERSHIP
)
from .utils import (
    create_user_aggregation_pipeline, create_organization_members_pipeline,
    validate_object_id, convert_membership_dict_to_response, convert_member_dict_to_response,
    has_sufficient_role, create_membership_update_dict, create_timestamp_fields,
    prepare_cache_membership_data, build_membership_query, build_last_accessed_update
)
from .types import (
    MembershipOperation, DatabaseType, MembershipDict, UserId, OrganizationId,
    UserNotFoundError, OrganizationNotFoundError, DuplicateMembershipError
)

logger = logging.getLogger(__name__)

class MembershipService:
    """Service for membership operations."""
    
    def __init__(self, db: Any, cache_service: Optional[Any] = None):
        self.db = db
        self.collection = db.memberships
        self.users_collection = db.users
        self.organizations_collection = db.organizations
        self.cache_service = cache_service
    
    async def create_membership(
        self, 
        membership_data: MembershipCreate,
        session=None,
        allow_existing: bool = False
    ) -> Membership:
        """Create a new membership.
        
        Args:
            membership_data: Membership data to create
            session: Database session for transactions
            allow_existing: If True, return existing membership instead of raising error
                           (useful for idempotent operations like invite acceptance)
        
        Returns:
            Membership: Created or existing membership
            
        Raises:
            DuplicateMembershipError: If membership exists and allow_existing=False
        """
        membership_dict = None
        inserted = False
        try:
            # Validate user exists
            try:
                user_id = validate_object_id(membership_data.user_id, "user ID")
                user = await self.users_collection.find_one({"_id": user_id}, session=session)
                if not user:
                    raise UserNotFoundError(USER_NOT_FOUND_ERROR)
            except ValueError:
                raise ValueError(INVALID_USER_ID_ERROR)
            
            # Validate organization exists
            try:
                org_id = validate_object_id(membership_data.organization_id, "organization ID")
                org = await self.organizations_collection.find_one({"_id": org_id}, session=session)
                if not org:
                    raise OrganizationNotFoundError(ORGANIZATION_NOT_FOUND_ERROR)
            except ValueError:
                raise ValueError(INVALID_ORGANIZATION_ID_ERROR)
            
            # Check if membership already exists
            existing = await self.collection.find_one(
                build_membership_query(membership_data.user_id, membership_data.organization_id), 
                session=session
            )
            
            if existing:
                if allow_existing:
                    # Return existing membership for idempotent operations
                    logger.info(f"Membership already exists for user {membership_data.user_id} in organization {membership_data.organization_id}")
                    return Membership(**convert_membership_dict_to_response(existing))
                else:
                    raise DuplicateMembershipError(ALREADY_MEMBER_ERROR)
            
            membership_dict = membership_data.model_dump()
            membership_dict.update(create_timestamp_fields())
            
            try:
                result = await self.collection.insert_one(membership_dict, session=session)
                membership_dict["_id"] = str(result.inserted_id)
                inserted = True
            except DuplicateKeyError:
                # Handles race conditions despite prior existence check
                if allow_existing:
                    # Race condition: another process created the membership
                    # Fetch and return the existing membership
                    existing = await self.collection.find_one(
                        build_membership_query(membership_data.user_id, membership_data.organization_id), 
                        session=session
                    )
                    if existing:
                        logger.info(f"Membership created by another process for user {membership_data.user_id} in organization {membership_data.organization_id}")
                        return Membership(**convert_membership_dict_to_response(existing))
                    else:
                        # This shouldn't happen, but handle gracefully
                        raise DuplicateMembershipError(ALREADY_MEMBER_ERROR)
                else:
                    raise DuplicateMembershipError(ALREADY_MEMBER_ERROR)
            
            return Membership(**membership_dict)
        finally:
            # Invalidate cache outside of transaction to avoid blocking
            if inserted and self.cache_service:
                try:
                    await self.cache_service.invalidate_user_membership(
                        membership_data.user_id, 
                        membership_data.organization_id
                    )
                except Exception as e:
                    logger.warning(f"Failed to invalidate cache after membership creation: {e}")
    
    async def get_membership(
        self, 
        user_id: str, 
        organization_id: str
    ) -> Optional[Membership]:
        """Get membership by user and organization."""
        # Check cache first if cache service is available
        if self.cache_service:
            try:
                cached_membership = await self.cache_service.get_cached_user_membership(user_id, organization_id)
                if cached_membership is not None:
                    logger.info(LOG_CACHED_MEMBERSHIP_FOUND.format(user_id=user_id, organization_id=organization_id))
                    # Convert cached data back to Membership object
                    cached_membership["_id"] = cached_membership.get("id")
                    return Membership(**cached_membership)
            except Exception as cache_error:
                logger.warning(LOG_CACHE_ERROR.format(user_id=user_id, organization_id=organization_id, error=cache_error))
                # Continue to database query if cache fails
        
        # Query database
        membership_data = await self.collection.find_one(build_membership_query(user_id, organization_id))
        
        if membership_data:
            membership_data["_id"] = str(membership_data["_id"])
            membership = Membership(**membership_data)
            
            # Cache the result for future use
            if self.cache_service:
                try:
                    membership_dict = prepare_cache_membership_data(membership.model_dump())
                    await self.cache_service.cache_user_memberships(user_id, organization_id, membership_dict)
                except Exception as cache_error:
                    logger.warning(LOG_FAILED_CACHE_MEMBERSHIP.format(user_id=user_id, organization_id=organization_id, error=cache_error))
            
            return membership
        return None
    
    async def get_membership_by_id(self, membership_id: str) -> Optional[Membership]:
        """Get membership by ID."""
        try:
            membership_data = await self.collection.find_one({"_id": ObjectId(membership_id)})
            if membership_data:
                membership_data["_id"] = str(membership_data["_id"])
                return Membership(**membership_data)
            return None
        except InvalidId:
            return None
    
    async def update_membership(
        self, 
        membership_id: str, 
        membership_data: MembershipUpdate
    ) -> Optional[Membership]:
        """Update membership."""
        try:
            update_dict = create_membership_update_dict(membership_data.model_dump())
            
            # Check if there are any fields to update
            if not update_dict:
                return await self.get_membership_by_id(membership_id)
            
            result = await self.collection.update_one(
                {"_id": ObjectId(membership_id)},
                {"$set": update_dict}
            )
            
            if result.matched_count:
                # Fetch the document regardless of modification for consistent return semantics
                updated_membership = await self.get_membership_by_id(membership_id)
                if updated_membership and self.cache_service:
                    try:
                        await self.cache_service.invalidate_user_membership(
                            updated_membership.user_id, updated_membership.organization_id
                        )
                    except Exception as e:
                        logger.warning(f"Failed to invalidate cache after membership update: {e}")
                return updated_membership
            return None
        except InvalidId:
            return None
    
    async def delete_membership(self, membership_id: str) -> bool:
        """Delete membership."""
        try:
            # Get the membership before deletion to know which user's cache to invalidate
            membership_to_delete = await self.get_membership_by_id(membership_id)
            
            result = await self.collection.delete_one({"_id": ObjectId(membership_id)})
            
            # Invalidate user membership cache if deletion was successful
            if result.deleted_count > 0 and membership_to_delete and self.cache_service:
                try:
                    await self.cache_service.invalidate_user_membership(
                        membership_to_delete.user_id, membership_to_delete.organization_id
                    )
                except Exception as e:
                    logger.warning(f"Failed to invalidate cache after membership deletion: {e}")
                
            return result.deleted_count > 0
        except InvalidId:
            return False
    
    async def get_user_memberships(
        self, 
        user_id: str, 
        status: Optional[MembershipStatus] = None
    ) -> List[OrganizationMembershipResponse]:
        """Get all memberships for a user with organization details using efficient aggregation."""
        try:
            logger.info(LOG_GETTING_USER_MEMBERSHIPS.format(user_id=user_id, status=status))
            
            # Skip cache for now since we don't know which organizations the user belongs to
            # With the new org-scoped cache schema, we can't efficiently retrieve all memberships
            # from cache without knowing the organization IDs. For individual org membership checks,
            # use get_user_role_in_organization which can use cache effectively.
            
            # Query the database with aggregation pipeline
            pipeline = create_user_aggregation_pipeline(user_id, status.value if status else None)
            logger.info(LOG_RUNNING_AGGREGATION.format(user_id=user_id))
            
            memberships = []
            async for doc in self.collection.aggregate(pipeline):
                try:
                    membership_data = convert_membership_dict_to_response(doc)
                    membership = OrganizationMembershipResponse(**membership_data)
                    memberships.append(membership)
                    logger.info(LOG_PROCESSED_MEMBERSHIP.format(organization_name=doc['organization_name']))
                except Exception as e:
                    logger.error(LOG_MEMBERSHIP_ERROR.format(doc=doc, error=str(e)))
                    continue
            
            # Cache each membership separately per organization (only if no status filter)
            if self.cache_service and not status and memberships:
                for membership in memberships:
                    try:
                        membership_data = membership.model_dump()
                        await self.cache_service.cache_user_memberships(
                            user_id, 
                            membership.organization_id, 
                            membership_data
                        )
                    except Exception as cache_error:
                        logger.warning(LOG_FAILED_CACHE_MEMBERSHIP.format(
                            user_id=user_id, organization_id=membership.organization_id, error=cache_error
                        ))
                        continue
            
            logger.info(LOG_RETURNING_MEMBERSHIPS.format(count=len(memberships), user_id=user_id))
            return memberships
            
        except Exception as e:
            logger.error(LOG_USER_MEMBERSHIPS_ERROR.format(user_id=user_id, error=str(e)))
            logger.error(f"Exception type: {type(e)}")
            raise
    
    async def get_organization_members(
        self, 
        organization_id: str, 
        status: Optional[MembershipStatus] = None
    ) -> List[UserMembershipResponse]:
        """Get all members of an organization with user details using efficient aggregation."""
        pipeline = create_organization_members_pipeline(organization_id, status.value if status else None)
        
        memberships = []
        async for doc in self.collection.aggregate(pipeline):
            try:
                member_data = convert_member_dict_to_response(doc)
                membership = UserMembershipResponse(**member_data)
                memberships.append(membership)
            except Exception as e:
                logger.error(LOG_ORG_MEMBER_ERROR.format(doc=doc, error=str(e)))
                continue
        
        return memberships
    
    async def update_last_accessed(self, user_id: str, organization_id: str) -> bool:
        """Update the last accessed timestamp for a membership."""
        try:
            result = await self.collection.update_one(
                build_membership_query(user_id, organization_id),
                build_last_accessed_update()
            )
            
            # Invalidate user membership cache if the update was successful
            if result.modified_count > 0:
                if self.cache_service:
                    try:
                        await self.cache_service.invalidate_user_membership(user_id, organization_id)
                    except Exception as e:
                        logger.warning(f"Failed to invalidate cache after updating last_accessed: {e}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update last_accessed for user {user_id} in org {organization_id}: {e}")
            return False
    
    async def check_user_role(
        self, 
        user_id: str, 
        organization_id: str
    ) -> Optional[MembershipRole]:
        """Check user's role in an organization."""
        membership = await self.get_membership(user_id, organization_id)
        if membership and membership.status == MembershipStatus.ACTIVE:
            return membership.role
        return None
    
    async def has_permission(
        self, 
        user_id: str, 
        organization_id: str, 
        required_role: MembershipRole
    ) -> bool:
        """Check if user has required role or higher in organization."""
        user_role = await self.check_user_role(user_id, organization_id)
        if not user_role:
            return False
        
        return has_sufficient_role(user_role, required_role)
