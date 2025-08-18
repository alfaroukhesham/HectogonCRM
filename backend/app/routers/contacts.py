from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime

from app.models.contact import Contact, ContactCreate, ContactUpdate
from app.models.user import User
from app.models.membership import MembershipRole
from app.core.database import get_database
from app.core.dependencies import (
    get_current_active_user, get_organization_context, 
    require_org_editor, require_org_viewer, get_cache_service
)


router = APIRouter(
    prefix="/contacts",
    tags=["contacts"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Contact)
async def create_contact(
    contact: ContactCreate,
    org_context: tuple[str, MembershipRole] = Depends(require_org_editor),
    db=Depends(get_database),
    cache_service=Depends(get_cache_service)
):
    """Create a new contact."""
    organization_id, user_role = org_context
    
    contact_dict = contact.dict()
    contact_dict["organization_id"] = organization_id
    contact_obj = Contact(**contact_dict)
    await db.contacts.insert_one(contact_obj.dict())
    
    # Invalidate the cache AFTER the DB write is successful
    await cache_service.invalidate_dashboard_stats(organization_id)
    
    return contact_obj


@router.get("/", response_model=List[Contact])
async def get_contacts(
    search: Optional[str] = None,
    org_context: tuple[str, MembershipRole] = Depends(require_org_viewer),
    db=Depends(get_database)
):
    """Get all contacts with optional search."""
    organization_id, user_role = org_context
    
    query = {"organization_id": organization_id}
    if search:
        query["$and"] = [
            {"organization_id": organization_id},
            {
                "$or": [
                    {"first_name": {"$regex": search, "$options": "i"}},
                    {"last_name": {"$regex": search, "$options": "i"}},
                    {"email": {"$regex": search, "$options": "i"}},
                    {"company": {"$regex": search, "$options": "i"}}
                ]
            }
        ]
    
    contacts = await db.contacts.find(query).sort("created_at", -1).to_list(1000)
    return [Contact(**contact) for contact in contacts]


@router.get("/{contact_id}", response_model=Contact)
async def get_contact(
    contact_id: str,
    org_context: tuple[str, MembershipRole] = Depends(require_org_viewer),
    db=Depends(get_database)
):
    """Get a specific contact by ID."""
    organization_id, user_role = org_context
    
    contact = await db.contacts.find_one({
        "id": contact_id,
        "organization_id": organization_id
    })
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return Contact(**contact)


@router.put("/{contact_id}", response_model=Contact)
async def update_contact(
    contact_id: str,
    contact: ContactUpdate,
    org_context: tuple[str, MembershipRole] = Depends(require_org_editor),
    db=Depends(get_database),
    cache_service=Depends(get_cache_service)
):
    """Update a contact."""
    organization_id, user_role = org_context
    
    update_data = {k: v for k, v in contact.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.contacts.update_one(
        {"id": contact_id, "organization_id": organization_id}, 
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Invalidate the cache AFTER the DB write is successful
    await cache_service.invalidate_dashboard_stats(organization_id)
    
    updated_contact = await db.contacts.find_one({
        "id": contact_id,
        "organization_id": organization_id
    })
    return Contact(**updated_contact)


@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: str,
    org_context: tuple[str, MembershipRole] = Depends(require_org_editor),
    db=Depends(get_database),
    cache_service=Depends(get_cache_service)
):
    """Delete a contact."""
    organization_id, user_role = org_context
    
    result = await db.contacts.delete_one({
        "id": contact_id,
        "organization_id": organization_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Invalidate the cache AFTER the DB write is successful
    await cache_service.invalidate_dashboard_stats(organization_id)
    
    return {"message": "Contact deleted successfully"} 