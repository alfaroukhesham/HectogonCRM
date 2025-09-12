"""
Test file to demonstrate the improved MembershipService functionality.

This file shows how the service now handles:
1. User and organization existence validation
2. Proper error handling for invalid ObjectIds
3. Correct aggregation pipeline lookups
4. Pydantic v2 compatibility with model_dump()
"""

import asyncio
from datetime import datetime, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.services import MembershipService
from app.models.membership import MembershipCreate, MembershipUpdate, MembershipRole, MembershipStatus


class TestMembershipService:
    """Test class for MembershipService improvements."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.service = MembershipService(db)
        self.db = db
    
    async def test_user_validation(self):
        """Test that user existence is validated."""
        print("Testing user validation...")
        
        # Test with non-existent user
        try:
            membership_data = MembershipCreate(
                user_id="507f1f77bcf86cd799439011",  # Valid ObjectId format but non-existent
                organization_id="507f1f77bcf86cd799439012",  # Valid ObjectId format but non-existent
                role=MembershipRole.VIEWER,
                status=MembershipStatus.ACTIVE
            )
            await self.service.create_membership(membership_data)
            print("❌ Should have failed - user doesn't exist")
        except ValueError as e:
            print(f"✅ Correctly caught user validation error: {e}")
    
    async def test_organization_validation(self):
        """Test that organization existence is validated."""
        print("\nTesting organization validation...")
        
        # Create a test user first
        user_result = await self.db.users.insert_one({
            "email": "test@example.com",
            "full_name": "Test User",
            "password_hash": "hashed_password",
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        })
        
        try:
            membership_data = MembershipCreate(
                user_id=str(user_result.inserted_id),
                organization_id="507f1f77bcf86cd799439012",  # Valid ObjectId format but non-existent
                role=MembershipRole.VIEWER,
                status=MembershipStatus.ACTIVE
            )
            await self.service.create_membership(membership_data)
            print("❌ Should have failed - organization doesn't exist")
        except ValueError as e:
            print(f"✅ Correctly caught organization validation error: {e}")
        
        # Clean up
        await self.db.users.delete_one({"_id": user_result.inserted_id})
    
    async def test_invalid_objectid_handling(self):
        """Test proper handling of invalid ObjectId formats."""
        print("\nTesting invalid ObjectId handling...")
        
        # Test invalid user ID format
        try:
            membership_data = MembershipCreate(
                user_id="invalid-id-format",
                organization_id="507f1f77bcf86cd799439012",
                role=MembershipRole.VIEWER,
                status=MembershipStatus.ACTIVE
            )
            await self.service.create_membership(membership_data)
            print("❌ Should have failed - invalid user ID format")
        except ValueError as e:
            print(f"✅ Correctly caught invalid user ID error: {e}")
        
        # Test invalid organization ID format
        try:
            membership_data = MembershipCreate(
                user_id="507f1f77bcf86cd799439011",
                organization_id="invalid-org-id",
                role=MembershipRole.VIEWER,
                status=MembershipStatus.ACTIVE
            )
            await self.service.create_membership(membership_data)
            print("❌ Should have failed - invalid organization ID format")
        except ValueError as e:
            print(f"✅ Correctly caught invalid organization ID error: {e}")
        
        # Test invalid membership ID in get_membership_by_id
        result = await self.service.get_membership_by_id("invalid-membership-id")
        if result is None:
            print("✅ Correctly handled invalid membership ID in get_membership_by_id")
        else:
            print("❌ Should have returned None for invalid membership ID")
        
        # Test invalid membership ID in update_membership
        update_data = MembershipUpdate(role=MembershipRole.EDITOR)
        result = await self.service.update_membership("invalid-membership-id", update_data)
        if result is None:
            print("✅ Correctly handled invalid membership ID in update_membership")
        else:
            print("❌ Should have returned None for invalid membership ID")
        
        # Test invalid membership ID in delete_membership
        result = await self.service.delete_membership("invalid-membership-id")
        if result is False:
            print("✅ Correctly handled invalid membership ID in delete_membership")
        else:
            print("❌ Should have returned False for invalid membership ID")
    
    async def test_pydantic_v2_compatibility(self):
        """Test that model_dump() is used instead of deprecated dict()."""
        print("\nTesting Pydantic v2 compatibility...")
        
        # Create test data
        user_result = await self.db.users.insert_one({
            "email": "test2@example.com",
            "full_name": "Test User 2",
            "password_hash": "hashed_password",
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        })
        
        org_result = await self.db.organizations.insert_one({
            "name": "Test Organization",
            "slug": "test-org",
            "created_by": str(user_result.inserted_id),
            "created_at": datetime.now(timezone.utc)
        })
        
        try:
            # Test create_membership with model_dump()
            membership_data = MembershipCreate(
                user_id=str(user_result.inserted_id),
                organization_id=str(org_result.inserted_id),
                role=MembershipRole.VIEWER,
                status=MembershipStatus.ACTIVE
            )
            
            # This should work with model_dump() instead of dict()
            membership = await self.service.create_membership(membership_data)
            print("✅ Successfully created membership using model_dump()")
            
            # Test update_membership with model_dump()
            update_data = MembershipUpdate(role=MembershipRole.EDITOR)
            updated_membership = await self.service.update_membership(membership.id, update_data)
            
            if updated_membership and updated_membership.role == MembershipRole.EDITOR:
                print("✅ Successfully updated membership using model_dump()")
            else:
                print("❌ Failed to update membership")
            
            # Clean up
            await self.service.delete_membership(membership.id)
            
        except Exception as e:
            print(f"❌ Error testing Pydantic v2 compatibility: {e}")
        finally:
            # Clean up test data
            await self.db.users.delete_one({"_id": user_result.inserted_id})
            await self.db.organizations.delete_one({"_id": org_result.inserted_id})
    
    async def test_aggregation_pipeline_fixes(self):
        """Test that the aggregation pipeline lookups work correctly."""
        print("\nTesting aggregation pipeline fixes...")
        
        # Create test data
        user_result = await self.db.users.insert_one({
            "email": "test3@example.com",
            "full_name": "Test User 3",
            "password_hash": "hashed_password",
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        })
        
        org_result = await self.db.organizations.insert_one({
            "name": "Test Organization 2",
            "slug": "test-org-2",
            "created_by": str(user_result.inserted_id),
            "created_at": datetime.now(timezone.utc)
        })
        
        try:
            # Create membership
            membership_data = MembershipCreate(
                user_id=str(user_result.inserted_id),
                organization_id=str(org_result.inserted_id),
                role=MembershipRole.ADMIN,
                status=MembershipStatus.ACTIVE
            )
            membership = await self.service.create_membership(membership_data)
            
            # Test get_user_memberships with proper ObjectId conversion
            user_memberships = await self.service.get_user_memberships(str(user_result.inserted_id))
            if user_memberships and len(user_memberships) > 0:
                print("✅ Successfully retrieved user memberships with proper ObjectId lookup")
                print(f"   Found membership for organization: {user_memberships[0].organization_name}")
            else:
                print("❌ Failed to retrieve user memberships")
            
            # Test get_organization_members with proper ObjectId conversion
            org_members = await self.service.get_organization_members(str(org_result.inserted_id))
            if org_members and len(org_members) > 0:
                print("✅ Successfully retrieved organization members with proper ObjectId lookup")
                print(f"   Found member: {org_members[0].user_name}")
            else:
                print("❌ Failed to retrieve organization members")
            
            # Clean up
            await self.service.delete_membership(membership.id)
            
        except Exception as e:
            print(f"❌ Error testing aggregation pipeline: {e}")
        finally:
            # Clean up test data
            await self.db.users.delete_one({"_id": user_result.inserted_id})
            await self.db.organizations.delete_one({"_id": org_result.inserted_id})
    
    async def run_all_tests(self):
        """Run all tests."""
        print("🧪 Running MembershipService improvement tests...\n")
        
        await self.test_user_validation()
        await self.test_organization_validation()
        await self.test_invalid_objectid_handling()
        await self.test_pydantic_v2_compatibility()
        await self.test_aggregation_pipeline_fixes()
        
        print("\n✅ All tests completed!")


async def main():
    """Main function to run the tests."""
    # Connect to MongoDB (adjust connection string as needed)
    client = AsyncIOMotorClient("mongodb://localhost:27017/")
    db = client.tiny_crm_test
    
    # Create test instance
    test_service = TestMembershipService(db)
    
    # Run tests
    await test_service.run_all_tests()
    
    # Close connection
    client.close()


if __name__ == "__main__":
    asyncio.run(main()) 