import re
import uuid
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.organization import (
    Organization, OrganizationCreate, OrganizationUpdate, OrganizationResponse
)
from app.models.membership import Membership, MembershipCreate, MembershipRole, MembershipStatus


class OrganizationService:
    """Service for organization operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.organizations
        self.membership_collection = db.memberships
    
    async def create_organization(
        self, 
        org_data: OrganizationCreate, 
        created_by: str
    ) -> Organization:
        """Create a new organization."""
        # Validate input data
        if not org_data.name or not org_data.name.strip():
            raise ValueError("Organization name is required")
        
        if not org_data.slug or not org_data.slug.strip():
            raise ValueError("Organization slug is required")
        
        # Validate slug format (alphanumeric and hyphens, no leading/trailing hyphens)
        if not re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$', org_data.slug):
            raise ValueError("Slug must start and end with alphanumeric characters, contain only lowercase letters, numbers, and hyphens")
        
        if len(org_data.slug) > 80:  # Add reasonable length limit
            raise ValueError("Slug must be 80 characters or less")
        
        # Validate created_by parameter
        if not created_by or not created_by.strip():
            raise ValueError("Created by user ID is required")
        
        # Check if slug is unique
        if await self.collection.find_one({"slug": org_data.slug}):
            raise ValueError(f"Organization with slug '{org_data.slug}' already exists")
        
        org_dict = org_data.dict()
        org_dict["created_by"] = created_by
        org_dict["created_at"] = datetime.now(timezone.utc)
        org_dict["updated_at"] = datetime.now(timezone.utc)
        
        # Ensure settings are included with defaults if not provided
        if "settings" not in org_dict or org_dict["settings"] is None:
            from app.models.organization import OrganizationSettings
            org_dict["settings"] = OrganizationSettings().dict()
        
        result = await self.collection.insert_one(org_dict)
        org_dict["_id"] = str(result.inserted_id)
        
        return Organization(**org_dict)
    
    async def get_organization(self, org_id: str) -> Optional[Organization]:
        """Get organization by ID."""
        org_data = await self.collection.find_one({"_id": ObjectId(org_id)})
        if org_data:
            org_data["_id"] = str(org_data["_id"])
            return Organization(**org_data)
        return None
    
    async def get_organization_by_slug(self, slug: str) -> Optional[Organization]:
        """Get organization by slug."""
        org_data = await self.collection.find_one({"slug": slug})
        if org_data:
            org_data["_id"] = str(org_data["_id"])
            return Organization(**org_data)
        return None
    
    async def update_organization(
        self, 
        org_id: str, 
        org_data: OrganizationUpdate
    ) -> Optional[Organization]:
        """Update organization."""
        update_dict = {k: v for k, v in org_data.dict().items() if v is not None}
        if not update_dict:
            return await self.get_organization(org_id)
        
        update_dict["updated_at"] = datetime.now(timezone.utc)
        
        result = await self.collection.update_one(
            {"_id": ObjectId(org_id)},
            {"$set": update_dict}
        )
        
        if result.modified_count:
            return await self.get_organization(org_id)
        return None
    
    async def delete_organization(self, org_id: str) -> bool:
        """Delete organization and all related data."""
        # Note: In production, you might want to soft delete or archive
        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                # Delete organization
                result = await self.collection.delete_one(
                    {"_id": ObjectId(org_id)}, 
                    session=session
                )
                
                if result.deleted_count > 0:
                    # Delete all memberships for this organization
                    await self.membership_collection.delete_many(
                        {"organization_id": org_id}, 
                        session=session
                    )
                
                return result.deleted_count > 0
    
    async def list_organizations(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Organization]:
        """List all organizations."""
        cursor = self.collection.find().skip(skip).limit(limit)
        organizations = []
        
        async for org_data in cursor:
            org_data["_id"] = str(org_data["_id"])
            organizations.append(Organization(**org_data))
        
        return organizations
    
    async def get_user_organizations(self, user_id: str) -> List[Organization]:
        """Get all organizations a user belongs to."""
        # Get user's memberships
        cursor = self.membership_collection.find({
            "user_id": user_id,
            "status": MembershipStatus.ACTIVE
        })
        
        org_ids = []
        async for membership in cursor:
            org_ids.append(ObjectId(membership["organization_id"]))
        
        if not org_ids:
            return []
        
        # Get organizations
        cursor = self.collection.find({"_id": {"$in": org_ids}})
        organizations = []
        
        async for org_data in cursor:
            org_data["_id"] = str(org_data["_id"])
            organizations.append(Organization(**org_data))
        
        return organizations
    
    async def create_default_organization(self, user_id: str, user_name: str) -> Organization:
        """Create a default organization for a new user."""
        if not user_id or not user_id.strip():
            raise ValueError("User ID is required")
        
        if not user_name or not user_name.strip():
            user_name = "User"  # Fallback name
        
        # Generate a slug from the user name
        base_slug = re.sub(r'[^a-z0-9-]', '', user_name.lower().replace(' ', '-'))
        if not base_slug:
            base_slug = "user"
        
        # Add a unique suffix to ensure uniqueness
        unique_slug = f"{base_slug}-{str(uuid.uuid4())[:8]}"
        
        org_data = OrganizationCreate(
            name=f"{user_name}'s Organization",
            slug=unique_slug,
            description="Default organization created during registration"
        )
        
        return await self.create_organization(org_data, user_id) 