from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    # General Settings
    ENVIRONMENT: str = "development" # "development", "staging", "production"

    # Notification Service
    SLACK_WEBHOOK_URL: str | None = None
    DISCORD_WEBHOOK_URL: str | None = None

    # CRM Service
    GOHIGHLEVEL_API_KEY: str | None = None
    HUBSPOT_API_KEY: str | None = None # Or choose one

    # Messaging Service (SMS)
    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    TWILIO_PHONE_NUMBER: str | None = None

    # Messaging Service (Email)
    SENDGRID_API_KEY: str | None = None
    FROM_EMAIL_ADDRESS: str | None = None

    DATABASE_URL: str | None = None


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore" # Ignore extra env vars not defined here
    )

# Initialize settings
settings = Settings()

# Debugging: Print loaded settings (be careful not to print sensitive data in prod)
if settings.ENVIRONMENT == "development":
    print("Loaded Settings:")
    for key, value in settings.model_dump().items():
        if "KEY" not in key and "TOKEN" not in key and "SID" not in key and "URL" not in key and "PASSWORD" not in key: # Basic redaction
            print(f"  {key}: {value}")
        elif value:
            print(f"  {key}: {'********'}") # Indicate it's set without showing it
        else:
            print(f"  {key}: {value}")