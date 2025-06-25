# Pydantic models for the CRM application

from .contact import Contact, ContactCreate, ContactUpdate
from .deal import Deal, DealCreate, DealUpdate, DealStage
from .activity import Activity, ActivityCreate, ActivityUpdate, ActivityType, Priority

__all__ = [
    "Contact", "ContactCreate", "ContactUpdate",
    "Deal", "DealCreate", "DealUpdate", "DealStage",
    "Activity", "ActivityCreate", "ActivityUpdate", "ActivityType", "Priority"
] 