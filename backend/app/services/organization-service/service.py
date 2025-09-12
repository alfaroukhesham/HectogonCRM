# organization-service/service.py

import logging
import asyncio
from typing import List, Optional, TYPE_CHECKING, Any
from bson import ObjectId
from pymongo.errors import DuplicateKeyError, PyMongoError
from bson.errors import InvalidId

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
    """Service for organization operations."""
    
    def __init__(self, db: Any):
        self.db = db
        self.collection = db.organizations
        self.membership_collection = db.memberships
        self._index_created = False
        self._index_lock = asyncio.Lock()
    
    async def _ensure_unique_index(self):
        """Ensure unique index exists on slug field"""
        if not self._index_created:
            async with self._index_lock:  # Add this lock to __init__
                if not self._index_created:  # Double-check after acquiring lock
                    try:
                        # create_index is idempotent - won't fail if index exists
                        await self.collection.create_index("slug", unique=True)
                        self._index_created = True
                        logger.info("Ensured unique index exists on slug field")
                    except PyMongoError as e:
                        logger.warning(f"Failed to create unique index on slug: {e}")
                        # Don't set _index_created = True on failure
    
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
        
        # Ensure unique index exists
        await self._ensure_unique_index()
        
        # The unique index will handle slug uniqueness atomically
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
        try:
            org_data = await self.collection.find_one({"_id": ObjectId(org_id)})
            if org_data:
                org_data = prepare_organization_for_response(org_data)
                return Organization(**org_data)
            return None
        except (PyMongoError, InvalidId) as e:
            logger.error(f"Error getting organization {org_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting organization {org_id}: {e}")
            raise
    
    async def get_organization_by_slug(self, slug: str) -> Optional[Organization]:
        """Get organization by slug."""
        try:
            org_data = await self.collection.find_one({"slug": slug})
            if org_data:
                org_data = prepare_organization_for_response(org_data)
                return Organization(**org_data)
            return None
        except PyMongoError as e:
            logger.error(f"Error getting organization by slug {slug}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting organization by slug {slug}: {e}")
            raise
    
    async def update_organization(
        self, 
        org_id: str, 
        org_data: OrganizationUpdate
    ) -> Optional[Organization]:
        """Update organization."""
        update_dict = create_update_dict(org_data.model_dump())
        if not update_dict:
            return await self.get_organization(org_id)
        
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(org_id)},
                {"$set": update_dict}
            )
            
            if result.modified_count:
                logger.info(f"Updated organization {org_id}")
                return await self.get_organization(org_id)
            return None
        except (PyMongoError, InvalidId) as e:
            logger.error(f"Error updating organization {org_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error updating organization {org_id}: {e}")
            raise
    
    async def delete_organization(self, org_id: str) -> bool:
        """Delete organization and all related data."""
        try:
            # Note: In production, you might want to soft delete or archive
            async with await self.db.client.start_session() as session:
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
        except (PyMongoError, InvalidId) as e:
            logger.error(f"Error deleting organization {org_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting organization {org_id}: {e}")
            raise
    
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
        except PyMongoError as e:
            logger.error(f"Error listing organizations: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing organizations: {e}")
            raise
    
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
        except PyMongoError as e:
            logger.error(f"Error getting organizations for user {user_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting organizations for user {user_id}: {e}")
            raise
    
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
        
        try:
            query = {"slug": slug}
            if exclude_org_id:
                query["_id"] = {"$ne": ObjectId(exclude_org_id)}
            
            existing = await self.collection.find_one(query)
            return existing is None
        except (PyMongoError, InvalidId) as e:
            logger.error(f"Error checking slug availability for {slug}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking slug availability for {slug}: {e}")
            raise
    
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
        except PyMongoError as e:
            logger.error(f"Error searching organizations: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching organizations: {e}")
            raise
    
    async def get_organization_count(self) -> int:
        """Get total number of organizations."""
        try:
            return await self.collection.count_documents({})
        except PyMongoError as e:
            logger.error(f"Error getting organization count: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error getting organization count: {e}")
            raise
    
    async def get_user_organization_count(self, user_id: str) -> int:
        """Get number of organizations a user belongs to."""
        try:
            return await self.membership_collection.count_documents(
                build_membership_query_for_user(user_id, MembershipStatus.ACTIVE.value)
            )
        except PyMongoError as e:
            logger.error(f"Error getting organization count for user {user_id}: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error getting organization count for user {user_id}: {e}")
            raise
