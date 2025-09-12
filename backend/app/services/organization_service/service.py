# organization-service/service.py

import logging
from typing import List, Optional, TYPE_CHECKING, Any
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from pymongo.results import InsertOneResult

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.organization import (
    Organization, OrganizationCreate, OrganizationUpdate, OrganizationResponse
)
from app.models.membership import Membership, MembershipCreate, MembershipRole, MembershipStatus

from .constants import (
    ORG_NAME_REQUIRED_ERROR, ORG_SLUG_REQUIRED_ERROR, INVALID_SLUG_FORMAT_ERROR,
    SLUG_TOO_LONG_ERROR, CREATED_BY_REQUIRED_ERROR, SLUG_EXISTS_ERROR,
    USER_ID_REQUIRED_ERROR, DEFAULT_USER_NAME, DEFAULT_ORG_DESCRIPTION,
    MAX_SLUG_LENGTH, DEFAULT_LIST_LIMIT
)
from .utils import (
    validate_slug_format, generate_slug_from_name, generate_unique_slug,
    create_organization_dict, create_update_dict, convert_object_id_to_string,
    build_organization_query_by_ids, build_membership_query_for_user,
    extract_organization_ids_from_memberships, validate_organization_name,
    validate_user_id, create_default_organization_name, is_slug_format_valid,
    prepare_organization_for_response, build_organization_search_query
)
from .types import (
    OrganizationOperation, SlugExistsError, OrganizationNotFoundError,
    InvalidOrganizationDataError, InvalidSlugError, DatabaseType, OrganizationDict
)

logger = logging.getLogger(__name__)

class OrganizationService:
    def __init__(self, db: "AsyncIOMotorDatabase"):
        self.db = db
        self.collection = db.organizations
        self.membership_collection = db.memberships
    
    async def create_organization(
        self, 
        org_data: OrganizationCreate, 
        created_by: str,
        session=None
    ) -> Organization:
        """Create a new organization."""
        # Validate input data
        if not validate_organization_name(org_data.name):
            raise InvalidOrganizationDataError(ORG_NAME_REQUIRED_ERROR)
        
        if not org_data.slug or not org_data.slug.strip():
            raise InvalidOrganizationDataError(ORG_SLUG_REQUIRED_ERROR)
        
        # Validate slug format
        if not is_slug_format_valid(org_data.slug):
            if len(org_data.slug) > MAX_SLUG_LENGTH:
                raise InvalidSlugError(SLUG_TOO_LONG_ERROR)
            else:
                raise InvalidSlugError(INVALID_SLUG_FORMAT_ERROR)
        
        # Validate created_by parameter
        if not validate_user_id(created_by):
            raise InvalidOrganizationDataError(CREATED_BY_REQUIRED_ERROR)
        
        # Check if slug is unique
        org_dict = create_organization_dict(org_data.model_dump(), created_by)

        try:
            result = await self.collection.insert_one(org_dict, session=session)
        except DuplicateKeyError:
            raise SlugExistsError(SLUG_EXISTS_ERROR.format(slug=org_data.slug))        
        org_dict["_id"] = str(result.inserted_id)
        
        logger.info(f"Created organization {org_data.name} with slug {org_data.slug} for user {created_by}")
        
        return Organization(**org_dict)
    
    async def get_organization(self, org_id: str) -> Optional[Organization]:
        """Get organization by ID."""
        # Validate organization ID format
        if not ObjectId.is_valid(org_id):
            logger.warning(f"Invalid organization ID format: {org_id}")
            return None

        try:
            org_data = await self.collection.find_one({"_id": ObjectId(org_id)})
            if org_data:
                org_data = prepare_organization_for_response(org_data)
                return Organization(**org_data)
            return None
        except Exception as e:
            logger.error(f"Error getting organization {org_id}: {e}")
            return None
    
    async def get_organization_by_slug(self, slug: str) -> Optional[Organization]:
        """Get organization by slug."""
        try:
            org_data = await self.collection.find_one({"slug": slug})
            if org_data:
                org_data = prepare_organization_for_response(org_data)
                return Organization(**org_data)
            return None
        except Exception as e:
            logger.error(f"Error getting organization by slug {slug}: {e}")
            return None
    
    async def update_organization(self, org_id: str, org_data: OrganizationUpdate) -> Optional[Organization]:
        """Update organization."""
        update_dict = create_update_dict(org_data.model_dump())
        if not update_dict:
            return await self.get_organization(org_id)
        
        try:
            if not ObjectId.is_valid(org_id):
                logger.warning(f"Invalid organization ID format for update: {org_id}")
                return None
            result = await self.collection.update_one(
                {"_id": ObjectId(org_id)},
                {"$set": update_dict}
            )
            
            if result.modified_count:
                logger.info(f"Updated organization {org_id}")
                return await self.get_organization(org_id)
            return None
        except Exception as e:
            logger.error(f"Error updating organization {org_id}: {e}")
            return None
    async def delete_organization(self, org_id: str) -> bool:
        """Delete organization and all related data."""
        session = None
        try:
            # Note: In production, you might want to soft delete or archive
            session = await self.db.client.start_session()
            async with session:
                async with session.start_transaction():
                    # Delete organization
                    result = await self.collection.delete_one(
                        {"_id": ObjectId(org_id)},
                        session=session
                    )

                    membership_count = 0
                    if result.deleted_count > 0:
                        # Delete all memberships for this organization
                        membership_result = await self.membership_collection.delete_many(
                            {"organization_id": org_id},
                            session=session
                        )
                        membership_count = membership_result.deleted_count

                    if result.deleted_count > 0:
                        logger.info(f"Deleted organization {org_id} and {membership_count} memberships")

                    return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting organization {org_id}: {e}")
            return False
        finally:
            if session:
                try:
                    await session.end_session()
                except Exception as e:
                    logger.warning(f"Error ending session for organization {org_id}: {e}")
    
    async def list_organizations(
        self, 
        skip: int = 0, 
        limit: int = DEFAULT_LIST_LIMIT
    ) -> List[Organization]:
        """List all organizations."""
        try:
            cursor = self.collection.find().skip(skip).limit(limit)
            organizations = []
            
            async for org_data in cursor:
                org_data = prepare_organization_for_response(org_data)
                organizations.append(Organization(**org_data))
            
            return organizations
        except Exception as e:
            logger.error(f"Error listing organizations: {e}")
            return []
    
    async def get_user_organizations(self, user_id: str) -> List[Organization]:
        """Get all organizations a user belongs to."""
        try:
            # Get user's memberships
            cursor = self.membership_collection.find(
                build_membership_query_for_user(user_id, MembershipStatus.ACTIVE.value)
            )
            
            org_ids = []
            async for membership in cursor:
                org_ids.append(membership["organization_id"])
            
            if not org_ids:
                return []
            
            # Get organizations
            query = build_organization_query_by_ids(org_ids)
            cursor = self.collection.find(query)
            organizations = []
            
            async for org_data in cursor:
                org_data = prepare_organization_for_response(org_data)
                organizations.append(Organization(**org_data))
            
            return organizations
        except Exception as e:
            logger.error(f"Error getting organizations for user {user_id}: {e}")
            return []
    
    async def create_default_organization(self, user_id: str, user_name: str) -> Organization:
        """Create a default organization for a new user."""
        if not validate_user_id(user_id):
            raise InvalidOrganizationDataError(USER_ID_REQUIRED_ERROR)
        
        if not user_name or not user_name.strip():
            user_name = DEFAULT_USER_NAME
        
        # Generate a unique slug
        unique_slug = generate_unique_slug(user_name)
        
        org_data = OrganizationCreate(
            name=create_default_organization_name(user_name),
            slug=unique_slug,
            description=DEFAULT_ORG_DESCRIPTION
        )
        
        logger.info(f"Creating default organization for user {user_id}: {org_data.name}")
        
        return await self.create_organization(org_data, user_id)
    
    async def check_slug_availability(self, slug: str, exclude_org_id: Optional[str] = None) -> bool:
        """Check if organization slug is available."""
        if not slug or not is_slug_format_valid(slug):
            return False

        # Validate exclude_org_id if provided
        if exclude_org_id and not ObjectId.is_valid(exclude_org_id):
            logger.warning(f"Invalid exclude_org_id format: {exclude_org_id}")
            return False

        try:
            query = {"slug": slug}
            if exclude_org_id:
                query["_id"] = {"$ne": ObjectId(exclude_org_id)}

            existing = await self.collection.find_one(query)
            return existing is None
        except Exception as e:
            logger.error(f"Error checking slug availability for {slug}: {e}")
            return False
    
    async def search_organizations(
        self,
        name_pattern: Optional[str] = None,
        created_by: Optional[str] = None,
        skip: int = 0,
        limit: int = DEFAULT_LIST_LIMIT
    ) -> List[Organization]:
        """Search organizations with filters."""
        try:
            query = build_organization_search_query(name_pattern, created_by)
            cursor = self.collection.find(query).skip(skip).limit(limit)
            
            organizations = []
            async for org_data in cursor:
                org_data = prepare_organization_for_response(org_data)
                organizations.append(Organization(**org_data))
            
            return organizations
        except Exception as e:
            logger.error(f"Error searching organizations: {e}")
            return []
    
    async def get_organization_count(self) -> int:
        """Get total number of organizations."""
        try:
            return await self.collection.count_documents({})
        except Exception as e:
            logger.error(f"Error getting organization count: {e}")
            return 0
    
    async def get_user_organization_count(self, user_id: str) -> int:
        """Get number of organizations a user belongs to."""
        try:
            return await self.membership_collection.count_documents(
                build_membership_query_for_user(user_id, MembershipStatus.ACTIVE.value)
            )
        except Exception as e:
            logger.error(f"Error getting organization count for user {user_id}: {e}")
            return 0
