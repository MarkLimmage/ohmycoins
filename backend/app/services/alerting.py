"""
Alert Service for processing and dispatching notifications.

Handles alert payloads from the LangGraph workflow, evaluates them against
alert rules, and dispatches notifications via Slack and/or email.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session, select

from app.core.config import settings
from app.models import AlertLog, AlertRule
from app.utils.notifications import send_email_alert, send_slack_alert

logger = logging.getLogger(__name__)


class AlertResult:
    """Result of alert processing."""

    def __init__(
        self,
        success: bool,
        message: str,
        channels_dispatched: list[str] | None = None,
        error: str | None = None,
    ) -> None:
        self.success = success
        self.message = message
        self.channels_dispatched = channels_dispatched or []
        self.error = error


class AlertService:
    """Processes alert payloads and dispatches notifications."""

    def __init__(self, session: Session) -> None:
        """
        Initialize AlertService with database session.

        Args:
            session: SQLModel database session
        """
        self.session = session

    async def process_alert(self, payload: dict[str, Any]) -> AlertResult:
        """
        Main entry point for processing alerts.

        1. Validate payload shape
        2. Find matching alert rules
        3. Check cooldown for each rule
        4. Dispatch to configured channels
        5. Log the alert to DB

        Args:
            payload: Alert payload from LangGraph workflow

        Returns:
            AlertResult with success status and dispatch details
        """
        try:
            # Validate payload
            if not self._validate_payload(payload):
                return AlertResult(
                    success=False,
                    message="Invalid alert payload shape",
                    error="Missing required payload fields",
                )

            alert_type = payload.get("type", "unknown")
            severity = payload.get("severity", "UNKNOWN")

            # Find matching rules
            rules = self._find_matching_rules(alert_type, severity)
            if not rules:
                logger.info(f"No alert rules matched for {alert_type}/{severity}")
                return AlertResult(
                    success=True,
                    message="No alert rules matched",
                    channels_dispatched=[],
                )

            # Dispatch to each rule's channels
            all_channels = set()
            for rule in rules:
                # Check cooldown
                if not await self._check_cooldown(rule, payload):
                    logger.info(f"Alert rule {rule.id} still in cooldown")
                    continue

                # Dispatch to channels
                for channel in rule.channels:
                    try:
                        if channel == "slack":
                            await self.dispatch_slack(payload)
                            all_channels.add("slack")
                        elif channel == "email":
                            await self.dispatch_email(payload, rule.recipients)
                            all_channels.add("email")
                    except Exception as e:
                        logger.error(f"Failed to dispatch to {channel}: {e}")

            # Log the alert
            self._log_alert(payload, list(all_channels), success=True)

            channels_msg = ", ".join(all_channels) if all_channels else "no channels"
            return AlertResult(
                success=True,
                message=f"Alert dispatched to {channels_msg}",
                channels_dispatched=list(all_channels),
            )

        except Exception as e:
            logger.error(f"Error processing alert: {e}")
            self._log_alert(payload, [], success=False, error_message=str(e))
            return AlertResult(
                success=False, message="Error processing alert", error=str(e)
            )

    async def dispatch_slack(self, payload: dict[str, Any]) -> bool:
        """
        Format and send Slack notification using existing send_slack_alert().

        Args:
            payload: Alert payload

        Returns:
            True if successful, False otherwise
        """
        try:
            message = self.format_alert_message(payload)
            return await send_slack_alert(message)
        except Exception as e:
            logger.error(f"Failed to dispatch Slack: {e}")
            return False

    async def dispatch_email(
        self, payload: dict[str, Any], recipients: list[str]
    ) -> bool:
        """
        Format and send email notification using existing SMTP config.

        Args:
            payload: Alert payload
            recipients: List of email addresses

        Returns:
            True if successful, False otherwise
        """
        if not recipients:
            logger.warning("No email recipients configured")
            return False

        if not settings.emails_enabled:
            logger.warning("Email not configured")
            return False

        try:
            message = self.format_alert_message(payload)
            return await send_email_alert(
                message=message, recipients=recipients, subject="OMC Alert"
            )
        except Exception as e:
            logger.error(f"Failed to dispatch email: {e}")
            return False

    def format_alert_message(self, payload: dict[str, Any]) -> str:
        """
        Format payload into human-readable message.

        Args:
            payload: Alert payload

        Returns:
            Formatted message string
        """
        severity = payload.get("severity", "UNKNOWN")
        count = payload.get("count", 0)
        coins = payload.get("coins", [])
        summary = payload.get("summary", "")

        coins_str = ", ".join(coins) if coins else "unknown"

        return (
            f"⚠️ {severity} Severity Alert: {count} anomalies detected\n"
            f"Coins: {coins_str}\n\n"
            f"{summary}"
        )

    async def _check_cooldown(self, rule: AlertRule, payload: dict[str, Any]) -> bool:
        """
        Check if alert should be sent (cooldown expired).

        Args:
            rule: AlertRule to check
            payload: Alert payload

        Returns:
            True if cooldown expired or no previous alert, False if in cooldown
        """
        # Get last alert for this rule
        statement = (
            select(AlertLog)
            .where(AlertLog.rule_id == rule.id)
            .order_by(AlertLog.created_at.desc())  # type: ignore[attr-defined]
            .limit(1)
        )
        last_alert = self.session.exec(statement).first()

        if last_alert is None:
            return True

        elapsed = datetime.now(timezone.utc) - last_alert.created_at
        cooldown_seconds = rule.cooldown_minutes * 60
        return elapsed.total_seconds() >= cooldown_seconds

    def _validate_payload(self, payload: dict[str, Any]) -> bool:
        """
        Validate alert payload shape.

        Args:
            payload: Alert payload to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["type", "severity", "timestamp"]
        return all(field in payload for field in required_fields)

    def _find_matching_rules(self, alert_type: str, severity: str) -> list[AlertRule]:
        """
        Find alert rules matching the alert type and severity.

        Args:
            alert_type: Type of alert (e.g., "anomaly_severity")
            severity: Severity level (LOW, MEDIUM, HIGH)

        Returns:
            List of matching enabled alert rules
        """
        severity_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
        alert_severity_level = severity_order.get(severity, 0)

        statement = select(AlertRule).where(
            AlertRule.alert_type == alert_type,
            AlertRule.enabled == True,  # noqa: E712
        )
        rules = self.session.exec(statement).all()

        # Filter by minimum severity
        matching = [
            r
            for r in rules
            if severity_order.get(r.min_severity, 0) <= alert_severity_level
        ]
        return matching

    def _log_alert(
        self,
        payload: dict[str, Any],
        channels_dispatched: list[str],
        success: bool,
        rule_id: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """
        Log alert to database.

        Args:
            payload: Alert payload
            channels_dispatched: Channels the alert were dispatched to
            success: Whether dispatch was successful
            rule_id: Optional rule ID
            error_message: Optional error message
        """
        try:
            import uuid

            alert_log = AlertLog(
                rule_id=uuid.UUID(rule_id) if rule_id else None,
                alert_type=payload.get("type", "unknown"),
                severity=payload.get("severity", "UNKNOWN"),
                payload=payload,
                channels_dispatched=channels_dispatched,
                success=success,
                error_message=error_message,
            )
            self.session.add(alert_log)
            self.session.commit()
        except Exception as e:
            logger.error(f"Failed to log alert: {e}")
            self.session.rollback()
