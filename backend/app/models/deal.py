from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid


class DealStage(str, Enum):
    """Deal stages enumeration."""
    lead = "Lead"
    qualified = "Qualified"
    proposal = "Proposal"
    negotiation = "Negotiation"
    closed_won = "Closed Won"
    closed_lost = "Closed Lost"


class DealBase(BaseModel):
    """Base deal model with common fields."""
    title: str
    contact_id: str
    value: float
    stage: DealStage
    probability: int = 50  # percentage
    expected_close_date: Optional[datetime] = None
    description: Optional[str] = None


class DealCreate(DealBase):
    """Deal model for creation."""
    stage: DealStage = DealStage.lead
    probability: int = 50


class DealUpdate(BaseModel):
    """Deal model for updates."""
    title: Optional[str] = None
    value: Optional[float] = None
    stage: Optional[DealStage] = None
    probability: Optional[int] = None
    expected_close_date: Optional[datetime] = None
    description: Optional[str] = None


class Deal(DealBase):
    """Complete deal model with all fields."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Required for multi-tenancy
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow) 