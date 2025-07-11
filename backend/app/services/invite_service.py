from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.invite import (
    Invite, InviteCreate, InviteUpdate, InviteResponse, InviteAccept,
    InviteRevoke, InviteListResponse, InviteStatus
)
from app.models.membership import MembershipCreate, MembershipRole, MembershipStatus
from app.core.email import EmailService


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
        invite_dict = invite_data.dict()
        invite_dict["invited_by"] = invited_by
        invite_dict["created_at"] = datetime.now(timezone.utc)
        invite_dict["updated_at"] = datetime.now(timezone.utc)
        
        result = await self.collection.insert_one(invite_dict)
        invite_dict["_id"] = str(result.inserted_id)
        
        invite = Invite(**invite_dict)
        
        # Send invite email if email is provided
        if invite_data.email:
            await self._send_invite_email(invite)
        
        return invite
    
    async def get_invite_by_code(self, code: str) -> Optional[Invite]:
        """Get invite by code."""
        invite_data = await self.collection.find_one({"code": code})
        if invite_data:
            invite_data["_id"] = str(invite_data["_id"])
            return Invite(**invite_data)
        return None
    
    async def get_invite_by_id(self, invite_id: str) -> Optional[Invite]:
        """Get invite by ID."""
        invite_data = await self.collection.find_one({"_id": ObjectId(invite_id)})
        if invite_data:
            invite_data["_id"] = str(invite_data["_id"])
            return Invite(**invite_data)
        return None
    
    async def update_invite(
        self, 
        invite_id: str, 
        invite_data: InviteUpdate
    ) -> Optional[Invite]:
        """Update invite."""
        update_dict = {k: v for k, v in invite_data.dict().items() if v is not None}
        if not update_dict:
            return await self.get_invite_by_id(invite_id)
        
        update_dict["updated_at"] = datetime.now(timezone.utc)
        
        result = await self.collection.update_one(
            {"_id": ObjectId(invite_id)},
            {"$set": update_dict}
        )
        
        if result.modified_count:
            return await self.get_invite_by_id(invite_id)
        return None
    
    async def revoke_invite(
        self, 
        invite_id: str, 
        revoked_by: str, 
        reason: Optional[str] = None
    ) -> Optional[Invite]:
        """Revoke an invite."""
        update_dict = {
            "status": InviteStatus.REVOKED,
            "revoked_by": revoked_by,
            "revoked_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        result = await self.collection.update_one(
            {"_id": ObjectId(invite_id)},
            {"$set": update_dict}
        )
        
        if result.modified_count:
            return await self.get_invite_by_id(invite_id)
        return None
    
    async def accept_invite(
        self, 
        code: str, 
        user_id: str
    ) -> Optional[Invite]:
        """Accept an invite and create membership."""
        invite = await self.get_invite_by_code(code)
        if not invite or not invite.is_usable:
            return None
        
        # Check if invite is for specific email
        if invite.email:
            user_data = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user_data or user_data["email"] != invite.email:
                raise ValueError("This invite is for a specific email address")
        
        # Create membership
        from app.services.membership_service import MembershipService
        membership_service = MembershipService(self.db)
        
        try:
            membership_data = MembershipCreate(
                user_id=user_id,
                organization_id=invite.organization_id,
                role=MembershipRole(invite.target_role),
                status=MembershipStatus.ACTIVE,
                invited_by=invite.invited_by
            )
            
            await membership_service.create_membership(membership_data)
            
            # Update invite
            update_dict = {
                "status": InviteStatus.ACCEPTED,
                "used_by": user_id,
                "used_at": datetime.now(timezone.utc),
                "current_uses": invite.current_uses + 1,
                "updated_at": datetime.now(timezone.utc)
            }
            
            await self.collection.update_one(
                {"_id": ObjectId(invite.id)},
                {"$set": update_dict}
            )
            
            return await self.get_invite_by_id(invite.id)
            
        except ValueError as e:
            # User already member
            raise e
    
    async def get_organization_invites(
        self, 
        organization_id: str, 
        status: Optional[InviteStatus] = None
    ) -> List[InviteListResponse]:
        """Get all invites for an organization."""
        query = {"organization_id": organization_id}
        if status:
            query["status"] = status
        
        pipeline = [
            {"$match": query},
            {
                "$lookup": {
                    "from": "organizations",
                    "localField": "organization_id",
                    "foreignField": "_id",
                    "as": "organization"
                }
            },
            {"$unwind": "$organization"},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "invited_by",
                    "foreignField": "_id",
                    "as": "inviter"
                }
            },
            {"$unwind": "$inviter"}
        ]
        
        invites = []
        async for doc in self.collection.aggregate(pipeline):
            org = doc["organization"]
            inviter = doc["inviter"]
            
            invite = InviteListResponse(
                id=str(doc["_id"]),
                code=doc["code"],
                organization_id=str(org["_id"]),
                organization_name=org["name"],
                invited_by=str(inviter["_id"]),
                invited_by_name=inviter["full_name"],
                target_role=doc["target_role"],
                email=doc.get("email"),
                status=doc["status"],
                expires_at=doc["expires_at"],
                max_uses=doc["max_uses"],
                current_uses=doc["current_uses"],
                created_at=doc["created_at"],
                is_expired=doc["expires_at"] < datetime.now(timezone.utc),
                is_usable=(
                    doc["status"] == InviteStatus.PENDING and
                    doc["expires_at"] > datetime.now(timezone.utc) and
                    doc["current_uses"] < doc["max_uses"]
                )
            )
            invites.append(invite)
        
        return invites
    
    async def cleanup_expired_invites(self) -> int:
        """Mark expired invites as expired."""
        result = await self.collection.update_many(
            {
                "status": InviteStatus.PENDING,
                "expires_at": {"$lt": datetime.now(timezone.utc)}
            },
            {
                "$set": {
                    "status": InviteStatus.EXPIRED,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        return result.modified_count
    
    async def _send_invite_email(self, invite: Invite):
        """Send invite email to user."""
        try:
            # Get organization details
            org_data = await self.organizations_collection.find_one(
                {"_id": ObjectId(invite.organization_id)}
            )
            
            if not org_data:
                return
            
            # Get inviter details
            inviter_data = await self.users_collection.find_one(
                {"_id": ObjectId(invite.invited_by)}
            )
            
            if not inviter_data:
                return
            
            await self.email_service.send_organization_invite(
                to_email=invite.email,
                organization_name=org_data["name"],
                inviter_name=inviter_data["full_name"],
                invite_code=invite.code,
                role=invite.target_role,
                expires_at=invite.expires_at
            )
        except Exception as e:
            # Log error but don't fail invite creation
            print(f"Failed to send invite email: {e}")
    
    async def resend_invite_email(self, invite_id: str) -> bool:
        """Resend invite email."""
        invite = await self.get_invite_by_id(invite_id)
        if not invite or not invite.email or not invite.is_usable:
            return False
        
        await self._send_invite_email(invite)
        return True 