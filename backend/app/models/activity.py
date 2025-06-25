from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid


class ActivityType(str, Enum):
    """Activity types enumeration."""
    call = "Call"
    email = "Email"
    meeting = "Meeting"
    note = "Note"
    task = "Task"


class Priority(str, Enum):
    """Priority levels enumeration."""
    low = "Low"
    medium = "Medium"
    high = "High"


class ActivityBase(BaseModel):
    """Base activity model with common fields."""
    contact_id: str
    deal_id: Optional[str] = None
    type: ActivityType
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    completed: bool = False
    priority: Priority = Priority.medium


class ActivityCreate(ActivityBase):
    """Activity model for creation."""
    priority: Priority = Priority.medium


class ActivityUpdate(BaseModel):
    """Activity model for updates."""
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    completed: Optional[bool] = None
    priority: Optional[Priority] = None


class Activity(ActivityBase):
    """Complete activity model with all fields."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow) 