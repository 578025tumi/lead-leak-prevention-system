from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse,RedirectResponse
from pydantic import ValidationError
import logging
import asyncio
import httpx # Import httpx to close its client on shutdown
from typing import Optional


from src.models.lead import Lead
from src.core.config import settings
from src.services.notification_service import NotificationService
from src.services.crm_service import CrmService
from src.services.messaging_service import MessagingService

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Lead Leak Prevention System API",
    version="1.0.0",
    description="API for ingesting leads, sending instant notifications, and triggering auto-responders.",
    docs_url="/docs",
    redoc_url="/redoc"
)

from fastapi import FastAPI
from src.api.leads import router as leads_router
from src.api.clients import router as clients_router
from src.api.events import router as events_router
from dotenv import load_dotenv
import os
app = FastAPI()

app.include_router(leads_router)
app.include_router(clients_router)
app.include_router(events_router)

CLIENT_ID = os.getenv("HUBSPOT_CLIENT_ID")
CLIENT_SECRET = os.getenv("HUBSPOT_CLIENT_SECRET")
REDIRECT_URI = os.getenv("HUBSPOT_REDIRECT_URI")
AUTH_URL = f"https://app.hubspot.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=crm.objects.contacts.read crm.objects.contacts.write"

@app.get("/authorize_hubspot")
def authorize():
    return RedirectResponse(AUTH_URL)

@app.get("/oauth2callback_hubspot")
async def oauth_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://api.hubapi.com/oauth/v1/token",
            data={
                "grant_type": "authorization_code",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "code": code,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    tokens = token_resp.json()
    return tokens

@app.get("/hubspot/contacts")
async def get_contacts(access_token: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.hubapi.com/crm/v3/objects/contacts",
            headers={"Authorization": f"Bearer {access_token}"}
        )
    return resp.json()

@app.get("/authorize_hubspot")
def authorize():
    auth_url = (
        "https://app.hubspot.com/oauth/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=crm.objects.contacts.read crm.objects.contacts.write"
    )
    return RedirectResponse(auth_url)
@app.get("/oauth2callback_hubspot")
async def oauth_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://api.hubapi.com/oauth/v1/token",
            data={
                "grant_type": "authorization_code",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "code": code,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    tokens = token_resp.json()
    # tokens = { "access_token": "...", "refresh_token": "...", "expires_in": 3600 }
    return tokens
async def refresh_token(refresh_token: str):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.hubapi.com/oauth/v1/token",
            data={
                "grant_type": "refresh_token",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": refresh_token,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    return resp.json()


# Global service instances
notification_service: Optional[NotificationService] = None
crm_service: Optional[CrmService] = None
messaging_service: Optional[MessagingService] = None

@app.on_event("startup")
async def startup_event():
    logger.info(f"API is starting up in {settings.ENVIRONMENT} mode.")
    global notification_service, crm_service, messaging_service
    
    # Initialize services
    notification_service = NotificationService(settings)
    crm_service = CrmService(settings)
    messaging_service = MessagingService(settings)
    
    logger.info("Services initialized.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("API is shutting down.")
    
    # Close httpx clients in services
    if notification_service and notification_service.client:
        await notification_service.client.aclose()
        logger.info("NotificationService httpx client closed.")
    if crm_service and crm_service.client:
        await crm_service.client.aclose()
        logger.info("CrmService httpx client closed.")
    
    # Note: Twilio and SendGrid clients don't typically need explicit 'aclose()'
    # because they use standard HTTP connections or are synchronous.

@app.post("/webhook/lead", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def ingest_lead(lead: Lead, request: Request):
    logger.info(f"Received new lead: {lead.email} from {lead.source}")

    try:
        # Senior Dev Tip: Use `asyncio.create_task` for fire-and-forget background tasks.
        # This immediately returns a 202 Accepted response, preventing webhook timeouts.
        asyncio.create_task(process_lead_in_background(lead))

        return JSONResponse(
            content={"message": "Lead received and processing initiated.", "lead_id": lead.email},
            status_code=status.HTTP_202_ACCEPTED
        )
    except Exception as e:
        logger.error(f"Error initiating background processing for lead {lead.email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate lead processing."
        )

async def process_lead_in_background(lead: Lead):
    """
    This function will contain the main business logic for processing a lead
    (sending notifications, updating CRM, sending auto-responders).
    It runs in the background.
    """
    try:
        logger.info(f"Background processing started for lead: {lead.email}")

        # 1. Send Instant Notifications
        if notification_service:
            await notification_service.send_new_lead_notification(lead)
        else:
            logger.error("NotificationService not initialized.")

        # 2. Update CRM
        if crm_service:
            await crm_service.create_or_update_lead(lead)
        else:
            logger.error("CrmService not initialized.")

        # 3. Send Auto-Responder
        if messaging_service:
            await messaging_service.send_welcome_email_or_sms(lead)
        else:
            logger.error("MessagingService not initialized.")

        logger.info(f"Background processing completed for lead: {lead.email}")

    except ValidationError as ve:
        logger.error(f"Data validation error during background processing for lead {lead.email}: {ve.errors()}", exc_info=True)
        # Implement internal alerting for failed processing due to data issues
    except Exception as e:
        logger.critical(f"Unhandled CRITICAL error during background processing for lead {lead.email}: {e}", exc_info=True)
        # Implement dead-letter queue, retry mechanism, or critical internal alert system here.
        # For a production system, this would trigger an immediate Ops alert.

@app.get("/")
async def root():
    return {"message": "Lead Leak Prevention System API is running!"}