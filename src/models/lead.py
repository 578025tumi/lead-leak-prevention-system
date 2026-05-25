from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import Optional, Dict, Any
from datetime import datetime

class Lead(BaseModel):
    """
    Represents a lead with essential contact information and additional context.
    """
    first_name: str = Field(..., description="First name of the lead")
    last_name: str = Field(..., description="Last name of the lead")
    email: EmailStr = Field(..., description="Email address of the lead")
    phone_number: str = Field(..., description="Phone number of the lead (e.g., E.164 format: +15551234567)")
    source: str = Field(..., description="Where the lead originated from (e.g., 'Facebook Ads', 'Google Search', 'Website Form')")
    campaign: Optional[str] = Field(None, description="Specific campaign that generated the lead")
    ad_group: Optional[str] = Field(None, description="Ad group within the campaign")
    landing_page_url: Optional[HttpUrl] = Field(None, description="URL of the landing page the lead converted on")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp when the lead was generated")
    notes: Optional[str] = Field(None, description="Any additional notes or context about the lead")
    tags: Optional[list[str]] = Field(None, description="List of tags associated with the lead")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Flexible dictionary for any extra custom fields")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                    "phone_number": "+15551234567",
                    "source": "Facebook Ads",
                    "campaign": "Summer Sale 2024",
                    "ad_group": "Target Audience A",
                    "landing_page_url": "https://youragency.com/summer-sale",
                    "notes": "Interested in marketing services.",
                    "tags": ["new_lead", "facebook"],
                    "custom_fields": {"budget": "5000", "industry": "retail"}
                }
            ]
        }
    }