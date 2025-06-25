from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class ContactBase(BaseModel):
    """Base contact model with common fields."""
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class ContactCreate(ContactBase):
    """Contact model for creation."""
    pass


class ContactUpdate(BaseModel):
    """Contact model for updates."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class Contact(ContactBase):
    """Complete contact model with all fields."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow) 