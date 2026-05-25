import httpx
from src.core.config import HUBSPOT_CLIENT_ID, HUBSPOT_CLIENT_SECRET, HUBSPOT_REDIRECT_URI

TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"
CONTACTS_URL = "https://api.hubapi.com/crm/v3/objects/contacts"

class HubSpotService:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None

    async def exchange_code(self, code: str):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": HUBSPOT_CLIENT_ID,
                    "client_secret": HUBSPOT_CLIENT_SECRET,
                    "redirect_uri": HUBSPOT_REDIRECT_URI,
                    "code": code,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        tokens = resp.json()
        self.access_token = tokens.get("access_token")
        self.refresh_token = tokens.get("refresh_token")
        return tokens

    async def refresh_access_token(self):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "client_id": HUBSPOT_CLIENT_ID,
                    "client_secret": HUBSPOT_CLIENT_SECRET,
                    "refresh_token": self.refresh_token,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        tokens = resp.json()
        self.access_token = tokens.get("access_token")
        return tokens

    async def create_contact(self, lead: dict):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                CONTACTS_URL,
                headers={"Authorization": f"Bearer {self.access_token}"},
                json={"properties": lead},
            )
        return resp.json()
