from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.orm_models import Lead
from src.models.lead import Lead as LeadSchema
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.services.hubspot import HubSpotService
from dotenv import load_dotenv
import httpx
import os

load_dotenv()
HUBSPOT_CLIENT_ID = os.getenv("HUBSPOT_CLIENT_ID")
HUBSPOT_CLIENT_SECRET = os.getenv("HUBSPOT_CLIENT_SECRET")
HUBSPOT_REDIRECT_URI = os.getenv("HUBSPOT_REDIRECT_URI")

YOUR_ACCOUNT_SID = os.getenv("YOUR_ACCOUNT_SID")
YOUR_AUTH_TOKEN = os.getenv("YOUR_AUTH_TOKEN")
YOUR_TWILIO_NUMBER = os.getenv("YOUR_TWILIO_NUMBER")

router = APIRouter(prefix="/leads", tags=["Leads"])
hubspot_service = HubSpotService()


class Lead(BaseModel):
    firstname: str
    email: str
    phone: str
    source: str

@router.get("/hubspot/contacts")
async def get_contacts(access_token: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.hubapi.com/crm/v3/objects/contacts",
            headers={"Authorization": f"Bearer {access_token}"}
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return resp.json()


@router.post("/webhook/leads")
async def receive_lead(lead: Lead):
    if not hubspot_service.access_token:
        raise HTTPException(status_code=401, detail="HubSpot not authorized")
    
    try:
        # 1. Push to HubSpot CRM
        hubspot_result = await hubspot_service.create_contact(lead.dict())

        # 2. Notify Slack
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
                json={"text": f"New lead: {lead.firstname}, {lead.email}, {lead.phone}, source: {lead.source}"}
            )

        # 3. Send Twilio SMS auto‑responder
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://api.twilio.com/2010-04-01/Accounts/YOUR_ACCOUNT_SID/Messages.json",
                data={
                    "From": YOUR_TWILIO_NUMBER,
                    "To": lead.phone,
                    "Body": f"Hi {lead.firstname}, thanks for reaching out! We'll contact you shortly."
                },
                auth=(YOUR_ACCOUNT_SID, YOUR_AUTH_TOKEN)
            )

        return {
            "status": "success",
            "hubspot_response": hubspot_result,
            "message": "Lead processed: HubSpot + Slack + Twilio"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    

@router.post("/", response_model=LeadSchema)
def create_lead(lead: LeadSchema, db: Session = Depends(get_db)):
    db_lead = Lead(**lead.dict())
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead

@router.get("/{lead_id}", response_model=LeadSchema)
def read_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@router.put("/{lead_id}", response_model=LeadSchema)
def update_lead(lead_id: int, lead: LeadSchema, db: Session = Depends(get_db)):
    db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    for key, value in lead.dict().items():
        setattr(db_lead, key, value)
    db.commit()
    db.refresh(db_lead)
    return db_lead

@router.delete("/{lead_id}")
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.delete(db_lead)
    db.commit()
    return {"detail": "Lead deleted"}
