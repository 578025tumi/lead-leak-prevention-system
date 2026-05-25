import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
import asyncio

# Ensure your conftest.py fixtures are accessible
from tests.conftest import test_client, mock_notification_service, mock_crm_service, mock_messaging_service # type: ignore

@pytest.mark.asyncio
async def test_root_endpoint(test_client: AsyncClient):
    response = await test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Lead Leak Prevention System API is running!"}

@pytest.mark.asyncio
@patch('src.api.main.process_lead_in_background') # Patch the background task directly
async def test_ingest_lead_success(mock_process_lead_in_background: MagicMock, test_client: AsyncClient):
    lead_data = {
        "first_name": "Test",
        "last_name": "Lead",
        "email": "test@example.com",
        "phone_number": "+1234567890",
        "source": "Test Source"
    }
    response = await test_client.post("/webhook/lead", json=lead_data)

    assert response.status_code == 202
    assert response.json()["message"] == "Lead received and processing initiated."
    # Verify that the background task was called with the correct lead data
    assert mock_process_lead_in_background.called
    # Check the type of the argument passed, a Lead object
    called_lead = mock_process_lead_in_background.call_args[0][0]
    assert called_lead.email == lead_data["email"]
    assert called_lead.first_name == lead_data["first_name"]

@pytest.mark.asyncio
async def test_ingest_lead_invalid_data(test_client: AsyncClient):
    invalid_lead_data = {
        "first_name": "Invalid",
        "email": "not-an-email", # Invalid email format
        "phone_number": "123",
        "source": "Bad Data"
    }
    response = await test_client.post("/webhook/lead", json=invalid_lead_data)
    assert response.status_code == 422 # FastAPI's validation error status code
    assert "value is not a valid email address" in response.json()["detail"][0]["msg"]

# Integration test for the background processing (requires mocking external services)
@pytest.mark.asyncio
@patch('src.api.main.notification_service', new_callable=MagicMock) # Mock the global service instances
@patch('src.api.main.crm_service', new_callable=MagicMock)
@patch('src.api.main.messaging_service', new_callable=MagicMock)
async def test_process_lead_in_background_calls_services(
    mock_messaging_service: MagicMock,
    mock_crm_service: MagicMock,
    mock_notification_service: MagicMock
):
    from src.api.main import process_lead_in_background # Import directly for testing
    from src.models.lead import Lead

    test_lead = Lead(
        first_name="Service",
        last_name="Test",
        email="service.test@example.com",
        phone_number="+1234567890",
        source="Test Runner"
    )

    # Configure mocks to return True for success
    mock_notification_service.send_new_lead_notification.return_value = True
    mock_crm_service.create_or_update_lead.return_value = True
    mock_messaging_service.send_welcome_email_or_sms.return_value = True

    await process_lead_in_background(test_lead)

    mock_notification_service.send_new_lead_notification.assert_called_once_with(test_lead)
    mock_crm_service.create_or_update_lead.assert_called_once_with(test_lead)
    mock_messaging_service.send_welcome_email_or_sms.assert_called_once_with(test_lead)