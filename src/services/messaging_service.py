import logging
from typing import Optional
from twilio.rest import Client as TwilioClient
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To

from src.core.config import settings
from src.models.lead import Lead

logger = logging.getLogger(__name__)

class MessagingService:
    def __init__(self, config=settings):
        self.config = config
        self.twilio_client: Optional[TwilioClient] = None
        if self.config.TWILIO_ACCOUNT_SID and self.config.TWILIO_AUTH_TOKEN:
            try:
                self.twilio_client = TwilioClient(self.config.TWILIO_ACCOUNT_SID, self.config.TWILIO_AUTH_TOKEN)
                logger.info("Twilio client initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}", exc_info=True)

        self.sendgrid_client: Optional[SendGridAPIClient] = None
        if self.config.SENDGRID_API_KEY:
            try:
                self.sendgrid_client = SendGridAPIClient(self.config.SENDGRID_API_KEY)
                logger.info("SendGrid client initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize SendGrid client: {e}", exc_info=True)


    async def send_sms(self, to_phone_number: str, message_body: str) -> bool:
        """Sends an SMS message via Twilio."""
        if not self.twilio_client or not self.config.TWILIO_PHONE_NUMBER:
            logger.warning("Twilio is not fully configured. Skipping SMS.")
            return False

        try:
            # Validate to_phone_number format (Twilio requires E.164)
            # We expect lead.phone_number to be E.164, but a double-check can be useful
            # For simplicity here, we assume it's correctly formatted from the Lead model.
            message = self.twilio_client.messages.create(
                to=to_phone_number,
                from_=self.config.TWILIO_PHONE_NUMBER,
                body=message_body
            )
            logger.info(f"SMS sent successfully to {to_phone_number}. SID: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_phone_number}: {e}", exc_info=True)
        return False

    async def send_email(self, to_email: str, subject: str, html_content: str, plain_text_content: Optional[str] = None) -> bool:
        """Sends an email via SendGrid."""
        if not self.sendgrid_client or not self.config.FROM_EMAIL_ADDRESS:
            logger.warning("SendGrid is not fully configured. Skipping email.")
            return False

        if not plain_text_content:
            # Basic conversion for plain text if not provided
            plain_text_content = html_content.replace("<br>", "\n").replace("<p>", "\n").replace("</p>", "").strip()


        message = Mail(
            from_email=Email(self.config.FROM_EMAIL_ADDRESS),
            to_emails=To(to_email),
            subject=subject,
            html_content=html_content,
            plain_text_content=plain_text_content
        )

        try:
            # SendGrid's send method is synchronous, so we await it directly or use run_in_threadpool if it's blocking
            # The sendgrid-python library often uses synchronous HTTP calls.
            # If this were a critical performance path, we might run this in a thread pool.
            # For now, we'll let it block the current async task.
            response = self.sendgrid_client.send(message)
            if 200 <= response.status_code < 300:
                logger.info(f"Email sent successfully to {to_email}. Status Code: {response.status_code}")
                return True
            else:
                logger.error(f"Failed to send email to {to_email}. Status Code: {response.status_code}, Body: {response.body}")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
        return False

    async def send_welcome_email_or_sms(self, lead: Lead) -> None:
        """
        Sends a personalized welcome SMS or Email to the lead.
        Prioritizes email if configured, otherwise falls back to SMS.
        """
        subject = f"Welcome, {lead.first_name}! Your Inquiry with [Your Agency Name]"
        email_html = f"""
        <html>
        <body>
            <p>Hi {lead.first_name},</p>
            <p>Thank you for reaching out to [Your Agency Name]! We received your inquiry and are excited to connect with you.</p>
            <p>One of our team members will be in touch shortly to discuss your needs further. In the meantime, feel free to explore our website: <a href="https://youragency.com">youragency.com</a></p>
            <p>Best regards,<br/>The Team at [Your Agency Name]</p>
        </body>
        </html>
        """
        sms_body = f"Hi {lead.first_name}, thanks for contacting [Your Agency Name]! We received your inquiry and will be in touch shortly. - [Your Agency Name]"

        email_sent = False
        sms_sent = False

        if self.config.SENDGRID_API_KEY and self.config.FROM_EMAIL_ADDRESS and lead.email:
            email_sent = await self.send_email(lead.email, subject, email_html)
            if email_sent:
                logger.info(f"Welcome email sent to {lead.email}.")
            else:
                logger.warning(f"Failed to send welcome email to {lead.email}.")

        if not email_sent and self.config.TWILIO_ACCOUNT_SID and self.config.TWILIO_PHONE_NUMBER and lead.phone_number:
            sms_sent = await self.send_sms(lead.phone_number, sms_body)
            if sms_sent:
                logger.info(f"Welcome SMS sent to {lead.phone_number}.")
            else:
                logger.warning(f"Failed to send welcome SMS to {lead.phone_number}.")

        if not email_sent and not sms_sent:
            logger.warning(f"No auto-responder (email or SMS) sent for lead {lead.email} / {lead.phone_number}. Check configurations.")