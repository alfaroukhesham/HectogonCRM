from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
from enum import Enum


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class DealStage(str, Enum):
    lead = "Lead"
    qualified = "Qualified"
    proposal = "Proposal"
    negotiation = "Negotiation"
    closed_won = "Closed Won"
    closed_lost = "Closed Lost"

class ActivityType(str, Enum):
    call = "Call"
    email = "Email"
    meeting = "Meeting"
    note = "Note"
    task = "Task"

class Priority(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"

# Models
class Contact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ContactCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

class Deal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    contact_id: str
    value: float
    stage: DealStage
    probability: int = 50  # percentage
    expected_close_date: Optional[datetime] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class DealCreate(BaseModel):
    title: str
    contact_id: str
    value: float
    stage: DealStage = DealStage.lead
    probability: int = 50
    expected_close_date: Optional[datetime] = None
    description: Optional[str] = None

class DealUpdate(BaseModel):
    title: Optional[str] = None
    value: Optional[float] = None
    stage: Optional[DealStage] = None
    probability: Optional[int] = None
    expected_close_date: Optional[datetime] = None
    description: Optional[str] = None

class Activity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    contact_id: str
    deal_id: Optional[str] = None
    type: ActivityType
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    completed: bool = False
    priority: Priority = Priority.medium
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ActivityCreate(BaseModel):
    contact_id: str
    deal_id: Optional[str] = None
    type: ActivityType
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Priority = Priority.medium

class ActivityUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    completed: Optional[bool] = None
    priority: Optional[Priority] = None

# Contact endpoints
@api_router.post("/contacts", response_model=Contact)
async def create_contact(contact: ContactCreate):
    contact_dict = contact.dict()
    contact_obj = Contact(**contact_dict)
    await db.contacts.insert_one(contact_obj.dict())
    return contact_obj

@api_router.get("/contacts", response_model=List[Contact])
async def get_contacts(search: Optional[str] = None):
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

@api_router.get("/contacts/{contact_id}", response_model=Contact)
async def get_contact(contact_id: str):
    contact = await db.contacts.find_one({"id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return Contact(**contact)

@api_router.put("/contacts/{contact_id}", response_model=Contact)
async def update_contact(contact_id: str, contact: ContactUpdate):
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

@api_router.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: str):
    result = await db.contacts.delete_one({"id": contact_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact deleted successfully"}

# Deal endpoints
@api_router.post("/deals", response_model=Deal)
async def create_deal(deal: DealCreate):
    # Verify contact exists
    contact = await db.contacts.find_one({"id": deal.contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    deal_dict = deal.dict()
    deal_obj = Deal(**deal_dict)
    await db.deals.insert_one(deal_obj.dict())
    return deal_obj

@api_router.get("/deals", response_model=List[Deal])
async def get_deals():
    deals = await db.deals.find().sort("created_at", -1).to_list(1000)
    return [Deal(**deal) for deal in deals]

@api_router.get("/deals/{deal_id}", response_model=Deal)
async def get_deal(deal_id: str):
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return Deal(**deal)

@api_router.put("/deals/{deal_id}", response_model=Deal)
async def update_deal(deal_id: str, deal: DealUpdate):
    update_data = {k: v for k, v in deal.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.deals.update_one(
        {"id": deal_id}, 
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    updated_deal = await db.deals.find_one({"id": deal_id})
    return Deal(**updated_deal)

@api_router.delete("/deals/{deal_id}")
async def delete_deal(deal_id: str):
    result = await db.deals.delete_one({"id": deal_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Deal not found")
    return {"message": "Deal deleted successfully"}

# Activity endpoints
@api_router.post("/activities", response_model=Activity)
async def create_activity(activity: ActivityCreate):
    # Verify contact exists
    contact = await db.contacts.find_one({"id": activity.contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    activity_dict = activity.dict()
    activity_obj = Activity(**activity_dict)
    await db.activities.insert_one(activity_obj.dict())
    return activity_obj

@api_router.get("/activities", response_model=List[Activity])
async def get_activities(contact_id: Optional[str] = None, deal_id: Optional[str] = None):
    query = {}
    if contact_id:
        query["contact_id"] = contact_id
    if deal_id:
        query["deal_id"] = deal_id
    
    activities = await db.activities.find(query).sort("created_at", -1).to_list(1000)
    return [Activity(**activity) for activity in activities]

@api_router.put("/activities/{activity_id}", response_model=Activity)
async def update_activity(activity_id: str, activity: ActivityUpdate):
    update_data = {k: v for k, v in activity.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.activities.update_one(
        {"id": activity_id}, 
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    updated_activity = await db.activities.find_one({"id": activity_id})
    return Activity(**updated_activity)

@api_router.delete("/activities/{activity_id}")
async def delete_activity(activity_id: str):
    result = await db.activities.delete_one({"id": activity_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Activity not found")
    return {"message": "Activity deleted successfully"}

# Dashboard endpoints
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    # Get counts
    total_contacts = await db.contacts.count_documents({})
    total_deals = await db.deals.count_documents({})
    won_deals = await db.deals.count_documents({"stage": DealStage.closed_won})
    
    # Calculate total revenue
    won_deals_data = await db.deals.find({"stage": DealStage.closed_won}).to_list(1000)
    total_revenue = sum(deal["value"] for deal in won_deals_data)
    
    # Calculate pipeline value
    active_deals = await db.deals.find({
        "stage": {"$nin": [DealStage.closed_won, DealStage.closed_lost]}
    }).to_list(1000)
    pipeline_value = sum(deal["value"] for deal in active_deals)
    
    # Deals by stage
    stages = [stage.value for stage in DealStage]
    deals_by_stage = {}
    for stage in stages:
        count = await db.deals.count_documents({"stage": stage})
        deals_by_stage[stage] = count
    
    return {
        "total_contacts": total_contacts,
        "total_deals": total_deals,
        "won_deals": won_deals,
        "total_revenue": total_revenue,
        "pipeline_value": pipeline_value,
        "deals_by_stage": deals_by_stage
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()