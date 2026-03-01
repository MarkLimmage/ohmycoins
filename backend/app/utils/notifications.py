import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_slack_alert(message: str) -> bool:
    """
    Send an alert to Slack via webhook.
    Returns True if successful, False otherwise.
    """
    if not settings.SLACK_WEBHOOK_URL:
        logger.warning("Slack webhook URL not configured. Skipping alert.")
        return False

    try:
        async with httpx.AsyncClient() as client:
            payload = {"text": message}
            response = await client.post(str(settings.SLACK_WEBHOOK_URL), json=payload)
            response.raise_for_status()
            logger.info("Slack alert sent successfully.")
            return True
    except Exception as e:
        logger.error(f"Failed to send Slack alert: {str(e)}")
        return False


async def send_email_alert(
    message: str, recipients: list[str], subject: str = "OMC Alert"
) -> bool:
    """
    Send an alert via email using configured SMTP settings.

    Args:
        message: Email body message
        recipients: List of email addresses to send to
        subject: Email subject line

    Returns:
        True if successful, False otherwise
    """
    if not settings.emails_enabled:
        logger.warning("Email not configured. Skipping email alert.")
        return False

    if not recipients:
        logger.warning("No recipients specified for email alert.")
        return False

    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.EMAILS_FROM_EMAIL or "noreply@ohmycoins.local"
        msg["To"] = ", ".join(recipients)

        # Attach text and HTML versions
        part = MIMEText(message, "plain")
        msg.attach(part)

        # Send via SMTP
        with smtplib.SMTP(
            settings.SMTP_HOST or "localhost", settings.SMTP_PORT, timeout=10
        ) as server:
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            from_email = settings.EMAILS_FROM_EMAIL or "noreply@ohmycoins.local"
            server.sendmail(from_email, recipients, msg.as_string())

        logger.info(f"Email alert sent to {recipients}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email alert: {str(e)}")
        return False
