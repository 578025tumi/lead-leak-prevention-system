import httpx
import logging
from typing import Dict, Any, Optional
from pydantic import ValidationError

from src.core.config import settings
from src.models.lead import Lead

logger = logging.getLogger(__name__)

class CrmService:
    def __init__(self, config=settings):
        self.config = config
        self.client = httpx.AsyncClient()

    async def _gohighlevel_request(self, method: str, path: str, json_data: Optional[Dict] = None) -> Optional[Dict]:
        """Helper for GoHighLevel API requests."""
        if not self.config.GOHIGHLEVEL_API_KEY:
            logger.warning("GoHighLevel API key not configured. Skipping GoHighLevel request.")
            return None

        headers = {
            "Authorization": f"Bearer {self.config.GOHIGHLEVEL_API_KEY}",
            "Content-Type": "application/json",
            "Version": "2021-07-28" # GHL API version
        }
        base_url = "https://rest.gohighlevel.com/v1" # This might vary, check GHL docs

        try:
            response = await self.client.request(method, f"{base_url}{path}", headers=headers, json=json_data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"GoHighLevel API HTTP error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"GoHighLevel API request error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error with GoHighLevel API: {e}", exc_info=True)
        return None

    async def create_or_update_gohighlevel_lead(self, lead: Lead) -> bool:
        """Creates or updates a contact in GoHighLevel."""
        # GoHighLevel typically creates if not exists, updates if found by email/phone
        contact_data = {
            "firstName": lead.first_name,
            "lastName": lead.last_name,
            "email": lead.email,
            "phone": lead.phone_number,
            "source": lead.source,
            # Add custom fields as needed. GHL uses 'customFields' list of dicts or direct field names
            "tags": lead.tags or []
            # You might need to add specific custom fields here, e.g.,
            # "customFields": [
            #     {"id": "CUSTOM_FIELD_ID_1", "value": lead.campaign},
            #     {"id": "CUSTOM_FIELD_ID_2", "value": lead.notes}
            # ]
        }
        if lead.notes:
            contact_data["notes"] = lead.notes

        try:
            # GHL API often uses a single endpoint for create/update based on unique identifiers
            response = await self._gohighlevel_request("POST", "/contacts/", json_data=contact_data)
            if response:
                logger.info(f"GoHighLevel contact created/updated for {lead.email}.")
                return True
        except Exception as e:
            logger.error(f"Error processing GoHighLevel lead {lead.email}: {e}", exc_info=True)
        return False

    async def _hubspot_request(self, method: str, path: str, json_data: Optional[Dict] = None) -> Optional[Dict]:
        """Helper for HubSpot API requests."""
        if not self.config.HUBSPOT_API_KEY:
            logger.warning("HubSpot API key not configured. Skipping HubSpot request.")
            return None

        headers = {
            "Authorization": f"Bearer {self.config.HUBSPOT_API_KEY}",
            "Content-Type": "application/json"
        }
        base_url = "https://api.hubapi.com/crm/v3"

        try:
            response = await self.client.request(method, f"{base_url}{path}", headers=headers, json=json_data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HubSpot API HTTP error: {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 400: # Bad Request, often validation error
                logger.error(f"HubSpot error details: {e.response.json()}")
        except httpx.RequestError as e:
            logger.error(f"HubSpot API request error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error with HubSpot API: {e}", exc_info=True)
        return None

    async def create_or_update_hubspot_lead(self, lead: Lead) -> bool:
        """Creates or updates a contact in HubSpot."""
        properties = {
            "firstname": lead.first_name,
            "lastname": lead.last_name,
            "email": lead.email,
            "phone": lead.phone_number,
            "lead_source": lead.source, # HubSpot often has a 'lead_source' property
            "hs_latest_source": lead.source # Another common source property
            # Custom properties in HubSpot would be their internal name, e.g., 'my_custom_campaign_field'
            # For campaign, you might map it to 'original_source_data_2' or a custom property
            # "campaign": lead.campaign # This would require a custom property named 'campaign'
        }
        # Add notes or other fields if they exist as properties in HubSpot
        if lead.notes:
            properties["notes"] = lead.notes # Assuming a 'notes' property

        # HubSpot uses a specific endpoint for creating contacts
        # For updating, we'd typically need to search by email first
        try:
            # First, try to find existing contact by email
            search_body = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "email",
                                "operator": "EQ",
                                "value": lead.email
                            }
                        ]
                    }
                ]
            }
            # HubSpot search endpoint: POST /crm/v3/objects/{objectType}/search
            # Docs: https://developers.hubspot.com/docs/api/crm/search
            search_response = await self._hubspot_request("POST", "/objects/contacts/search", json_data=search_body)

            contact_id = None
            if search_response and search_response.get("results"):
                contact_id = search_response["results"][0]["id"]
                logger.info(f"HubSpot contact {lead.email} found (ID: {contact_id}). Updating.")
                # Update existing contact
                update_response = await self._hubspot_request(
                    "PATCH", f"/objects/contacts/{contact_id}", json_data={"properties": properties}
                )
                if update_response:
                    logger.info(f"HubSpot contact {lead.email} updated.")
                    return True
            else:
                logger.info(f"HubSpot contact {lead.email} not found. Creating new contact.")
                # Create new contact
                create_response = await self._hubspot_request(
                    "POST", "/objects/contacts", json_data={"properties": properties}
                )
                if create_response:
                    logger.info(f"HubSpot contact {lead.email} created.")
                    return True

        except Exception as e:
            logger.error(f"Error processing HubSpot lead {lead.email}: {e}", exc_info=True)
        return False


    async def create_or_update_lead(self, lead: Lead) -> None:
        """
        Orchestrates creating/updating a lead in the configured CRM(s).
        """
        successes = []
        if self.config.GOHIGHLEVEL_API_KEY:
            successes.append(await self.create_or_update_gohighlevel_lead(lead))
        else:
            logger.info("GoHighLevel API key not configured, skipping CRM update for GoHighLevel.")

        if self.config.HUBSPOT_API_KEY:
            successes.append(await self.create_or_update_hubspot_lead(lead))
        else:
            logger.info("HubSpot API key not configured, skipping CRM update for HubSpot.")

        if not any(successes):
            logger.warning(f"No CRM updates were successfully performed for lead {lead.email}.")