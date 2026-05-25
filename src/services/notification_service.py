import httpx
import logging
from typing import Literal

from src.core.config import settings
from src.models.lead import Lead

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, config=settings):
        self.config = config
        self.client = httpx.AsyncClient() # Asynchronous HTTP client

    async def send_slack_notification(self, lead: Lead) -> bool:
        """Sends a new lead notification to Slack."""
        if not self.config.SLACK_WEBHOOK_URL:
            logger.warning("Slack webhook URL not configured. Skipping Slack notification.")
            return False

        message = {
            # ... (rest of your Slack message content) ...
        }

        try:
            response = await self.client.post(self.config.SLACK_WEBHOOK_URL, json=message)
            response.raise_for_status() # Raises an exception for 4xx/5xx responses
            logger.info(f"Slack notification sent successfully for lead: {lead.email}")
            return True
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to send Slack notification for lead {lead.email}: HTTP Error {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Failed to send Slack notification for lead {lead.email}: Request Error - {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while sending Slack notification for lead {lead.email}: {e}", exc_info=True)
        return False

    async def send_discord_notification(self, lead: Lead) -> bool:
        """Sends a new lead notification to Discord."""
        if not self.config.DISCORD_WEBHOOK_URL:
            logger.warning("Discord webhook URL not configured. Skipping Discord notification.")
            return False

        embed = {
            # ... (rest of your Discord embed content) ...
        }

        message = {
            "content": "@here New Lead!",
            "embeds": [embed]
        }

        try:
            response = await self.client.post(self.config.DISCORD_WEBHOOK_URL, json=message)
            response.raise_for_status()
            logger.info(f"Discord notification sent successfully for lead: {lead.email}")
            return True
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to send Discord notification for lead {lead.email}: HTTP Error {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Failed to send Discord notification for lead {lead.email}: Request Error - {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while sending Discord notification for lead {lead.email}: {e}", exc_info=True)
        return False

    async def send_new_lead_notification(self, lead: Lead, platform: Literal["slack", "discord", "all"] = "all") -> None:
        """
        Sends new lead notifications to specified platforms.
        Defaults to sending to both if configured.
        """
        successes = []
        if platform == "slack" or platform == "all":
            if self.config.SLACK_WEBHOOK_URL:
                successes.append(await self.send_slack_notification(lead))
            else:
                logger.info("Slack not configured, skipping.")

        if platform == "discord" or platform == "all":
            if self.config.DISCORD_WEBHOOK_URL:
                successes.append(await self.send_discord_notification(lead))
            else:
                logger.info("Discord not configured, skipping.")

        if not any(successes):
            logger.warning(f"No notifications were successfully sent for lead {lead.email}.")