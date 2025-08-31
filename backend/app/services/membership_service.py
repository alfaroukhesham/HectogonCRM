from typing import List, Optional, TYPE_CHECKING, Any
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
import logging

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase
    from app.services.cache_service import CacheService

from app.models.membership import (
    Membership, MembershipCreate, MembershipUpdate, MembershipResponse,
    UserMembershipResponse, OrganizationMembershipResponse,
    MembershipRole, MembershipStatus
)
from app.models.user import User
from app.models.organization import Organization

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
        session=None
    ) -> Membership:
        """Create a new membership."""
        # Validate user exists
        try:
            user = await self.users_collection.find_one({"_id": ObjectId(membership_data.user_id)}, session=session)
            if not user:
                raise ValueError("User not found")
        except InvalidId:
            raise ValueError("Invalid user ID format")
        
        # Validate organization exists
        try:
            org = await self.organizations_collection.find_one({"_id": ObjectId(membership_data.organization_id)}, session=session)
            if not org:
                raise ValueError("Organization not found")
        except InvalidId:
            raise ValueError("Invalid organization ID format")
        
        # Check if membership already exists
        existing = await self.collection.find_one({
            "user_id": membership_data.user_id,
            "organization_id": membership_data.organization_id
        }, session=session)
        
        if existing:
            raise ValueError("User is already a member of this organization")
        
        membership_dict = membership_data.model_dump()
        membership_dict["created_at"] = datetime.now(timezone.utc)
        membership_dict["updated_at"] = datetime.now(timezone.utc)
        
        result = await self.collection.insert_one(membership_dict, session=session)
        membership_dict["_id"] = str(result.inserted_id)
        
        return Membership(**membership_dict)
    
    async def get_membership(
        self, 
        user_id: str, 
        organization_id: str
    ) -> Optional[Membership]:
        """Get membership by user and organization."""
        membership_data = await self.collection.find_one({
            "user_id": user_id,
            "organization_id": organization_id
        })
        
        if membership_data:
            membership_data["_id"] = str(membership_data["_id"])
            return Membership(**membership_data)
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
        update_dict = {k: v for k, v in membership_data.model_dump().items() if v is not None}
        if not update_dict:
            return await self.get_membership_by_id(membership_id)
        
        update_dict["updated_at"] = datetime.now(timezone.utc)
        
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(membership_id)},
                {"$set": update_dict}
            )
            
            if result.modified_count:
                return await self.get_membership_by_id(membership_id)
            return None
        except InvalidId:
            return None
    
    async def delete_membership(self, membership_id: str) -> bool:
        """Delete membership."""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(membership_id)})
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
            logger.info(f"Getting memberships for user: {user_id}, status: {status}")
            
            # 1. Check cache first if cache service is available and no status filter
            if self.cache_service and not status:
                cached_memberships = await self.cache_service.get_cached_user_memberships(user_id)
                if cached_memberships is not None:
                    logger.info(f"Found {len(cached_memberships)} cached memberships for user {user_id}")
                    # Convert cached data back to OrganizationMembershipResponse objects
                    return [
                        OrganizationMembershipResponse(**membership) 
                        for membership in cached_memberships
                    ]
            
            # 2. If cache miss or status filter, query the database
            # Build match query
            match_query = {"user_id": user_id}
            if status:
                match_query["status"] = status
            
            # Optimized aggregation pipeline that handles string-to-ObjectId conversion
            pipeline = [
                # 1. Match memberships for the user
                {"$match": match_query},
                # 2. Convert organization_id string to ObjectId for lookup
                {
                    "$addFields": {
                        "organization_object_id": {"$toObjectId": "$organization_id"}
                    }
                },
                # 3. Join with organizations collection
                {
                    "$lookup": {
                        "from": "organizations",
                        "localField": "organization_object_id",
                        "foreignField": "_id",
                        "as": "organization_details"
                    }
                },
                # 4. Unwind the organization array (should contain exactly one organization)
                {"$unwind": "$organization_details"},
                # 5. Project the final structure
                {
                    "$project": {
                        "_id": 1,
                        "user_id": 1,
                        "organization_id": "$organization_details._id",
                        "organization_name": "$organization_details.name",
                        "organization_slug": "$organization_details.slug",
                        "organization_logo_url": "$organization_details.logo_url",
                        "role": 1,
                        "status": 1,
                        "joined_at": 1,
                        "last_accessed": 1
                    }
                }
            ]
            
            logger.info(f"Running optimized aggregation pipeline for user {user_id}")
            
            memberships = []
            async for doc in self.collection.aggregate(pipeline):
                try:
                    membership = OrganizationMembershipResponse(
                        id=str(doc["_id"]),
                        user_id=doc["user_id"],
                        organization_id=str(doc["organization_id"]),
                        organization_name=doc["organization_name"],
                        organization_slug=doc["organization_slug"],
                        organization_logo_url=doc.get("organization_logo_url"),
                        role=doc["role"],
                        status=doc["status"],
                        joined_at=doc.get("joined_at"),
                        last_accessed=doc.get("last_accessed")
                    )
                    memberships.append(membership)
                    logger.info(f"Successfully processed membership for organization: {doc['organization_name']}")
                except Exception as e:
                    logger.error(f"Error processing membership document: {doc}, error: {str(e)}")
                    continue
            
            # 3. Cache the result before returning (only if no status filter and cache service available)
            if self.cache_service and not status and memberships:
                # Convert to serializable format for caching
                memberships_data = [membership.model_dump() for membership in memberships]
                await self.cache_service.cache_user_memberships(user_id, memberships_data)
            
            logger.info(f"Returning {len(memberships)} memberships for user {user_id}")
            return memberships
            
        except Exception as e:
            logger.error(f"Error in get_user_memberships for user {user_id}: {str(e)}")
            logger.error(f"Exception type: {type(e)}")
            raise
    
    async def get_organization_members(
        self, 
        organization_id: str, 
        status: Optional[MembershipStatus] = None
    ) -> List[UserMembershipResponse]:
        """Get all members of an organization with user details using efficient aggregation."""
        # Build match query
        match_query = {"organization_id": organization_id}
        if status:
            match_query["status"] = status
        
        # Optimized aggregation pipeline that handles string-to-ObjectId conversion
        pipeline = [
            # 1. Match memberships for the organization
            {"$match": match_query},
            # 2. Convert user_id string to ObjectId for lookup
            {
                "$addFields": {
                    "user_object_id": {"$toObjectId": "$user_id"}
                }
            },
            # 3. Join with users collection
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_object_id",
                    "foreignField": "_id",
                    "as": "user_details"
                }
            },
            # 4. Unwind the user array (should contain exactly one user)
            {"$unwind": "$user_details"},
            # 5. Project the final structure
            {
                "$project": {
                    "_id": 1,
                    "user_id": "$user_details._id",
                    "user_email": "$user_details.email",
                    "user_name": "$user_details.full_name",
                    "user_avatar_url": "$user_details.avatar_url",
                    "organization_id": 1,
                    "role": 1,
                    "status": 1,
                    "invited_by": 1,
                    "joined_at": 1,
                    "last_accessed": 1
                }
            }
        ]
        
        memberships = []
        async for doc in self.collection.aggregate(pipeline):
            try:
                membership = UserMembershipResponse(
                    id=str(doc["_id"]),
                    user_id=str(doc["user_id"]),
                    user_email=doc["user_email"],
                    user_name=doc["user_name"],
                    user_avatar_url=doc.get("user_avatar_url"),
                    organization_id=doc["organization_id"],
                    role=doc["role"],
                    status=doc["status"],
                    invited_by=doc.get("invited_by"),
                    joined_at=doc.get("joined_at"),
                    last_accessed=doc.get("last_accessed")
                )
                memberships.append(membership)
            except Exception as e:
                logger.error(f"Error processing organization member document: {doc}, error: {str(e)}")
                continue
        
        return memberships
    
    async def update_last_accessed(self, user_id: str, organization_id: str):
        """Update the last accessed timestamp for a membership."""
        await self.collection.update_one(
            {
                "user_id": user_id,
                "organization_id": organization_id
            },
            {
                "$set": {
                    "last_accessed": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
    
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
        
        # Role hierarchy: ADMIN > EDITOR > VIEWER
        role_hierarchy = {
            MembershipRole.VIEWER: 1,
            MembershipRole.EDITOR: 2,
            MembershipRole.ADMIN: 3
        }
        
        return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0) 