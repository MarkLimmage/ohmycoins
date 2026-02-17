import logging

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
