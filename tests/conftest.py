import pytest
import asyncio
from httpx import AsyncClient
from fastapi import FastAPI
from unittest.mock import MagicMock

from services.messaging_service import MessagingService
from src.api.main import app as fastapi_app # Import the FastAPI app
from src.core.config import Settings, settings

from src.services.notification_service import NotificationService
from src.services.crm_service import CrmService
from src.services.messaging_service import MessagingService

# This fixture allows us to test async FastAPI routes
@pytest.fixture(scope="session")
def event_loop():
    """Force the test runner to use a single loop."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_client():
    """Async test client for FastAPI application."""
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        yield client

@pytest.fixture(scope="module")
def mock_settings():
    """
    Fixture to provide mock settings for testing services.
    Allows overriding specific settings without touching the actual .env.
    """
    original_settings = settings # Keep a reference to original
    # Create a mock Settings instance. You can override specific values here.
    mock = MagicMock(spec=Settings)
    mock.ENVIRONMENT = "test"
    mock.SLACK_WEBHOOK_URL = "http://mock-slack.com/webhook"
    mock.DISCORD_WEBHOOK_URL = "http://mock-discord.com/webhook"
    mock.GOHIGHLEVEL_API_KEY = "mock_ghl_key"
    mock.HUBSPOT_API_KEY = "mock_hubspot_key"
    mock.TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    mock.TWILIO_AUTH_TOKEN = "mock_twilio_token"
    mock.TWILIO_PHONE_NUMBER = "+15005550006"
    mock.SENDGRID_API_KEY = "mock_sendgrid_key"
    mock.FROM_EMAIL_ADDRESS = "test@example.com"
    # Overwrite the global settings instance temporarily
    # NOTE: This is an advanced technique and requires careful management
    # For simple cases, passing the mock to service constructors is safer.
    # However, if services directly import the global `settings` object, this might be needed.
    # For better isolation, consider dependency injection for `settings` into services.
    fastapi_app.dependency_overrides[Settings] = lambda: mock # Example for FastAPI dependency injection if we refactor Settings later

    yield mock # Provide the mock settings
    # Restore original settings (if you modified the global one)
    # fastapi_app.dependency_overrides = {} # Clear overrides

@pytest.fixture
def mock_notification_service():
    """Mock the NotificationService for testing interactions."""
    return MagicMock(spec=NotificationService)

@pytest.fixture
def mock_crm_service():
    """Mock the CrmService for testing interactions."""
    return MagicMock(spec=CrmService)

@pytest.fixture
def mock_messaging_service():
    """Mock the MessagingService for testing interactions."""
    return MagicMock(spec=MessagingService)