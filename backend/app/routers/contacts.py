from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime

from app.models.contact import Contact, ContactCreate, ContactUpdate
from app.core.database import get_database


router = APIRouter(
    prefix="/contacts",
    tags=["contacts"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Contact)
async def create_contact(
    contact: ContactCreate,
    db=Depends(get_database)
):
    """Create a new contact."""
    contact_dict = contact.dict()
    contact_obj = Contact(**contact_dict)
    await db.contacts.insert_one(contact_obj.dict())
    return contact_obj


@router.get("/", response_model=List[Contact])
async def get_contacts(
    search: Optional[str] = None,
    db=Depends(get_database)
):
    """Get all contacts with optional search."""
    query = {}
    if search:
        query = {
            "$or": [
                {"first_name": {"$regex": search, "$options": "i"}},
                {"last_name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"company": {"$regex": search, "$options": "i"}}
            ]
        }
    
    contacts = await db.contacts.find(query).sort("created_at", -1).to_list(1000)
    return [Contact(**contact) for contact in contacts]


@router.get("/{contact_id}", response_model=Contact)
async def get_contact(
    contact_id: str,
    db=Depends(get_database)
):
    """Get a specific contact by ID."""
    contact = await db.contacts.find_one({"id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return Contact(**contact)


@router.put("/{contact_id}", response_model=Contact)
async def update_contact(
    contact_id: str,
    contact: ContactUpdate,
    db=Depends(get_database)
):
    """Update a contact."""
    update_data = {k: v for k, v in contact.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.contacts.update_one(
        {"id": contact_id}, 
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    updated_contact = await db.contacts.find_one({"id": contact_id})
    return Contact(**updated_contact)


@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: str,
    db=Depends(get_database)
):
    """Delete a contact."""
    result = await db.contacts.delete_one({"id": contact_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact deleted successfully"} 