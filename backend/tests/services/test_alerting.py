"""
Tests for the AlertService.

Covers alert processing, dispatch logic, cooldown checks, and logging.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import Session, select

from app.models import AlertLog, AlertRule
from app.services.alerting import AlertService


@pytest.fixture
def alert_service(db: Session) -> AlertService:
    """Create AlertService with test database session."""
    return AlertService(session=db)


def test_validate_payload_valid(alert_service: AlertService) -> None:
    """Test payload validation with valid payload."""
    payload = {
        "type": "anomaly_severity",
        "severity": "HIGH",
        "timestamp": "2026-02-27T14:30:00",
        "count": 2,
        "coins": ["BTC", "ETH"],
        "summary": "Test alert",
    }
    assert alert_service._validate_payload(payload) is True


def test_validate_payload_missing_fields(alert_service: AlertService) -> None:
    """Test payload validation with missing required fields."""
    payload = {
        "type": "anomaly_severity",
        "severity": "HIGH",
        # Missing 'timestamp'
    }
    assert alert_service._validate_payload(payload) is False


def test_find_matching_rules(
    alert_service: AlertService, db: Session
) -> None:
    """Test finding alert rules matching type and severity."""
    # Create test rules
    rule1 = AlertRule(
        name="High Alerts",
        alert_type="anomaly_severity",
        min_severity="HIGH",
        channels=["slack"],
        recipients=[],
        enabled=True,
    )
    rule2 = AlertRule(
        name="All Alerts",
        alert_type="anomaly_severity",
        min_severity="LOW",
        channels=["email"],
        recipients=["test@example.com"],
        enabled=True,
    )
    rule3 = AlertRule(
        name="Disabled Rule",
        alert_type="anomaly_severity",
        min_severity="HIGH",
        channels=["slack"],
        recipients=[],
        enabled=False,
    )

    db.add(rule1)
    db.add(rule2)
    db.add(rule3)
    db.commit()

    # Find rules for HIGH severity
    matching = alert_service._find_matching_rules("anomaly_severity", "HIGH")
    assert len(matching) == 2  # rule1 and rule2 (not rule3, disabled)
    assert any(r.name == "High Alerts" for r in matching)
    assert any(r.name == "All Alerts" for r in matching)


@pytest.mark.asyncio
async def test_check_cooldown_expired(
    alert_service: AlertService, db: Session
) -> None:
    """Test cooldown check when cooldown has expired."""
    rule = AlertRule(
        name="Test Rule",
        alert_type="anomaly_severity",
        min_severity="HIGH",
        channels=["slack"],
        recipients=[],
        cooldown_minutes=1,
        enabled=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    # Create old alert log
    old_alert = AlertLog(
        rule_id=rule.id,
        alert_type="anomaly_severity",
        severity="HIGH",
        payload={},
        channels_dispatched=["slack"],
        success=True,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )
    db.add(old_alert)
    db.commit()

    payload = {"type": "anomaly_severity", "severity": "HIGH", "timestamp": "test"}
    assert await alert_service._check_cooldown(rule, payload) is True


@pytest.mark.asyncio
async def test_check_cooldown_still_active(
    alert_service: AlertService, db: Session
) -> None:
    """Test cooldown check when cooldown is still active."""
    rule = AlertRule(
        name="Test Rule",
        alert_type="anomaly_severity",
        min_severity="HIGH",
        channels=["slack"],
        recipients=[],
        cooldown_minutes=30,
        enabled=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    # Create recent alert log
    recent_alert = AlertLog(
        rule_id=rule.id,
        alert_type="anomaly_severity",
        severity="HIGH",
        payload={},
        channels_dispatched=["slack"],
        success=True,
        created_at=datetime.now(timezone.utc) - timedelta(seconds=10),
    )
    db.add(recent_alert)
    db.commit()

    payload = {"type": "anomaly_severity", "severity": "HIGH", "timestamp": "test"}
    assert await alert_service._check_cooldown(rule, payload) is False


def test_format_alert_message(alert_service: AlertService) -> None:
    """Test alert message formatting."""
    payload = {
        "severity": "HIGH",
        "count": 2,
        "coins": ["BTC", "ETH"],
        "summary": "Test summary",
    }
    message = alert_service.format_alert_message(payload)

    assert "HIGH" in message
    assert "2" in message
    assert "BTC" in message
    assert "ETH" in message
    assert "Test summary" in message


@pytest.mark.asyncio
async def test_process_alert_success(
    alert_service: AlertService, db: Session
) -> None:
    """Test successful alert processing and dispatch."""
    # Create rule
    rule = AlertRule(
        name="Test Rule",
        alert_type="anomaly_severity",
        min_severity="HIGH",
        channels=["slack"],
        recipients=[],
        enabled=True,
    )
    db.add(rule)
    db.commit()

    payload = {
        "type": "anomaly_severity",
        "severity": "HIGH",
        "count": 1,
        "coins": ["BTC"],
        "summary": "Test alert",
        "timestamp": "2026-02-27T14:30:00",
    }

    # Mock dispatch_slack
    with patch.object(
        alert_service, "dispatch_slack", new_callable=AsyncMock
    ) as mock_slack:
        mock_slack.return_value = True

        result = await alert_service.process_alert(payload)

        assert result.success is True
        assert "slack" in result.channels_dispatched
        mock_slack.assert_called_once()

    # Verify log was created
    logs = db.exec(select(AlertLog)).all()
    assert len(logs) == 1
    assert logs[0].success is True


@pytest.mark.asyncio
async def test_process_alert_cooldown_suppression(
    alert_service: AlertService, db: Session
) -> None:
    """Test alert suppression due to cooldown."""
    # Create rule with short cooldown
    rule = AlertRule(
        name="Test Rule",
        alert_type="anomaly_severity",
        min_severity="HIGH",
        channels=["slack"],
        recipients=[],
        cooldown_minutes=30,
        enabled=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    # Create recent alert
    old_alert = AlertLog(
        rule_id=rule.id,
        alert_type="anomaly_severity",
        severity="HIGH",
        payload={},
        channels_dispatched=["slack"],
        success=True,
        created_at=datetime.now(timezone.utc) - timedelta(seconds=10),
    )
    db.add(old_alert)
    db.commit()

    payload = {
        "type": "anomaly_severity",
        "severity": "HIGH",
        "count": 1,
        "coins": ["BTC"],
        "summary": "Test",
        "timestamp": "2026-02-27T14:30:00",
    }

    with patch.object(
        alert_service, "dispatch_slack", new_callable=AsyncMock
    ) as mock_slack:
        result = await alert_service.process_alert(payload)

        # Should still be successful but with no channels dispatched
        assert result.success is True
        assert len(result.channels_dispatched) == 0
        mock_slack.assert_not_called()


@pytest.mark.asyncio
async def test_process_alert_invalid_payload(alert_service: AlertService) -> None:
    """Test alert processing with invalid payload."""
    payload = {
        "type": "anomaly_severity",
        # Missing 'severity' and 'timestamp'
    }

    result = await alert_service.process_alert(payload)

    assert result.success is False
    assert "Invalid" in result.message


@pytest.mark.asyncio
async def test_dispatch_slack(alert_service: AlertService) -> None:
    """Test Slack dispatch calls send_slack_alert."""
    payload = {
        "severity": "HIGH",
        "count": 1,
        "coins": ["BTC"],
        "summary": "Test",
    }

    with patch("app.services.alerting.send_slack_alert", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True

        result = await alert_service.dispatch_slack(payload)

        assert result is True
        mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_dispatch_email(alert_service: AlertService) -> None:
    """Test email dispatch with recipients."""
    payload = {
        "severity": "HIGH",
        "count": 1,
        "coins": ["BTC"],
        "summary": "Test",
    }
    recipients = ["test@example.com"]

    with patch("app.services.alerting.send_email_alert", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True

        result = await alert_service.dispatch_email(payload, recipients)

        assert result is True
        mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_dispatch_email_no_recipients(alert_service: AlertService) -> None:
    """Test email dispatch with no recipients."""
    payload = {"severity": "HIGH", "count": 1, "coins": ["BTC"], "summary": "Test"}

    result = await alert_service.dispatch_email(payload, [])

    assert result is False


def test_log_alert(alert_service: AlertService, db: Session) -> None:
    """Test alert logging to database."""
    payload = {
        "type": "anomaly_severity",
        "severity": "HIGH",
        "count": 1,
        "coins": ["BTC"],
        "summary": "Test",
    }

    alert_service._log_alert(payload, ["slack"], success=True)

    logs = db.exec(select(AlertLog)).all()
    assert len(logs) == 1
    assert logs[0].alert_type == "anomaly_severity"
    assert logs[0].severity == "HIGH"
    assert logs[0].success is True
    assert "slack" in logs[0].channels_dispatched
