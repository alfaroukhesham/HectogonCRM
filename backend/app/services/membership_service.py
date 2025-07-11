from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

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
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.memberships
        self.users_collection = db.users
        self.organizations_collection = db.organizations
    
    async def create_membership(
        self, 
        membership_data: MembershipCreate
    ) -> Membership:
        """Create a new membership."""
        # Validate user exists
        try:
            user = await self.users_collection.find_one({"_id": ObjectId(membership_data.user_id)})
            if not user:
                raise ValueError("User not found")
        except InvalidId:
            raise ValueError("Invalid user ID format")
        
        # Validate organization exists
        try:
            org = await self.organizations_collection.find_one({"_id": ObjectId(membership_data.organization_id)})
            if not org:
                raise ValueError("Organization not found")
        except InvalidId:
            raise ValueError("Invalid organization ID format")
        
        # Check if membership already exists
        existing = await self.collection.find_one({
            "user_id": membership_data.user_id,
            "organization_id": membership_data.organization_id
        })
        
        if existing:
            raise ValueError("User is already a member of this organization")
        
        membership_dict = membership_data.model_dump()
        membership_dict["created_at"] = datetime.now(timezone.utc)
        membership_dict["updated_at"] = datetime.now(timezone.utc)
        
        result = await self.collection.insert_one(membership_dict)
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
        """Get all memberships for a user with organization details."""
        try:
            logger.info(f"Getting memberships for user: {user_id}, status: {status}")
            
            query = {"user_id": user_id}
            if status:
                query["status"] = status
            
            logger.info(f"Membership query: {query}")
            
            # First, check if user has any memberships at all
            membership_count = await self.collection.count_documents(query)
            logger.info(f"Found {membership_count} memberships matching query")
            
            if membership_count == 0:
                logger.warning(f"No memberships found for user {user_id}")
                return []
            
            pipeline = [
                {"$match": query},
                {
                    "$lookup": {
                        "from": "organizations",
                        "let": {"org_id": {"$toObjectId": "$organization_id"}},
                        "pipeline": [
                            {"$match": {"$expr": {"$eq": ["$_id", "$$org_id"]}}}
                        ],
                        "as": "organization"
                    }
                },
                {"$unwind": "$organization"}
            ]
            
            logger.info(f"Running aggregation pipeline: {pipeline}")
            
            memberships = []
            async for doc in self.collection.aggregate(pipeline):
                try:
                    org = doc["organization"]
                    membership = OrganizationMembershipResponse(
                        id=str(doc["_id"]),
                        user_id=doc["user_id"],
                        organization_id=str(org["_id"]),
                        organization_name=org["name"],
                        organization_slug=org["slug"],
                        organization_logo_url=org.get("logo_url"),
                        role=doc["role"],
                        status=doc["status"],
                        joined_at=doc.get("joined_at"),
                        last_accessed=doc.get("last_accessed")
                    )
                    memberships.append(membership)
                    logger.info(f"Successfully processed membership for organization: {org['name']}")
                except Exception as e:
                    logger.error(f"Error processing membership document: {doc}, error: {str(e)}")
                    continue
            
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
        """Get all members of an organization with user details."""
        query = {"organization_id": organization_id}
        if status:
            query["status"] = status
        
        pipeline = [
            {"$match": query},
            {
                "$lookup": {
                    "from": "users",
                    "let": {"uid": {"$toObjectId": "$user_id"}},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$_id", "$$uid"]}}}
                    ],
                    "as": "user"
                }
            },
            {"$unwind": "$user"}
        ]
        
        memberships = []
        async for doc in self.collection.aggregate(pipeline):
            user = doc["user"]
            membership = UserMembershipResponse(
                id=str(doc["_id"]),
                user_id=str(user["_id"]),
                user_email=user["email"],
                user_name=user["full_name"],
                user_avatar_url=user.get("avatar_url"),
                organization_id=doc["organization_id"],
                role=doc["role"],
                status=doc["status"],
                invited_by=doc.get("invited_by"),
                joined_at=doc.get("joined_at"),
                last_accessed=doc.get("last_accessed")
            )
            memberships.append(membership)
        
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