"""
Tests for Alert API routes.

Covers CRUD operations for alert rules and alert history endpoints.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.main import app
from app.models import AlertLog, AlertRule, User


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


def test_list_alert_rules_admin(
    client: TestClient, db: Session, test_superuser: User, superuser_token_headers: dict
) -> None:
    """Test listing alert rules (admin only)."""
    # Create test rule
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

    response = client.get("/api/v1/alerts/rules", headers=superuser_token_headers)

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "count" in data
    assert len(data["data"]) > 0


def test_create_alert_rule_admin(
    client: TestClient, superuser_token_headers: dict
) -> None:
    """Test creating an alert rule (admin only)."""
    rule_data = {
        "name": "New Rule",
        "alert_type": "anomaly_severity",
        "min_severity": "HIGH",
        "channels": ["slack", "email"],
        "recipients": ["test@example.com"],
        "cooldown_minutes": 30,
        "enabled": True,
    }

    response = client.post(
        "/api/v1/alerts/rules",
        json=rule_data,
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Rule"
    assert data["alert_type"] == "anomaly_severity"
    assert "slack" in data["channels"]


def test_create_alert_rule_non_admin(
    client: TestClient, normal_user_token_headers: dict
) -> None:
    """Test creating alert rule as non-admin fails."""
    rule_data = {
        "name": "New Rule",
        "alert_type": "anomaly_severity",
        "min_severity": "HIGH",
        "channels": ["slack"],
        "recipients": [],
        "enabled": True,
    }

    response = client.post(
        "/api/v1/alerts/rules",
        json=rule_data,
        headers=normal_user_token_headers,
    )

    assert response.status_code == 403


def test_update_alert_rule_admin(
    client: TestClient, db: Session, superuser_token_headers: dict
) -> None:
    """Test updating an alert rule."""
    # Create rule
    rule = AlertRule(
        name="Original Name",
        alert_type="anomaly_severity",
        min_severity="HIGH",
        channels=["slack"],
        recipients=[],
        enabled=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    update_data = {
        "name": "Updated Name",
        "enabled": False,
    }

    response = client.patch(
        f"/api/v1/alerts/rules/{rule.id}",
        json=update_data,
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["enabled"] is False


def test_delete_alert_rule_admin(
    client: TestClient, db: Session, superuser_token_headers: dict
) -> None:
    """Test deleting an alert rule."""
    # Create rule
    rule = AlertRule(
        name="To Delete",
        alert_type="anomaly_severity",
        min_severity="HIGH",
        channels=["slack"],
        recipients=[],
        enabled=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    response = client.delete(
        f"/api/v1/alerts/rules/{rule.id}",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200

    # Verify rule is deleted (need to refresh session to see DB changes)
    db.expunge_all()  # Clear session cache
    deleted_rule = db.get(AlertRule, rule.id)
    assert deleted_rule is None


def test_list_alert_log_with_filters(
    client: TestClient, db: Session, superuser_token_headers: dict
) -> None:
    """Test listing alert history with filters."""
    # Create test logs
    log1 = AlertLog(
        alert_type="anomaly_severity",
        severity="HIGH",
        payload={},
        channels_dispatched=["slack"],
        success=True,
    )
    log2 = AlertLog(
        alert_type="anomaly_severity",
        severity="MEDIUM",
        payload={},
        channels_dispatched=["email"],
        success=True,
    )
    db.add(log1)
    db.add(log2)
    db.commit()

    # Filter by severity
    response = client.get(
        "/api/v1/alerts/log?severity=HIGH",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["severity"] == "HIGH"


def test_list_alert_log_pagination(
    client: TestClient, db: Session, superuser_token_headers: dict
) -> None:
    """Test alert log pagination."""
    # Create multiple logs
    for i in range(25):
        log = AlertLog(
            alert_type="anomaly_severity",
            severity="HIGH",
            payload={},
            channels_dispatched=["slack"],
            success=True,
        )
        db.add(log)
    db.commit()

    # Get first page
    response = client.get(
        "/api/v1/alerts/log?skip=0&limit=10",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 10
    assert data["count"] == 25


@pytest.mark.asyncio
async def test_send_test_alert_admin(
    client: TestClient, db: Session, superuser_token_headers: dict
) -> None:
    """Test sending a test alert."""
    with patch(
        "app.services.alerting.AlertService.process_alert", new_callable=AsyncMock
    ) as mock_process:
        from app.services.alerting import AlertResult

        mock_process.return_value = AlertResult(
            success=True,
            message="Test alert sent",
            channels_dispatched=["slack"],
        )

        response = client.post(
            "/api/v1/alerts/test",
            headers=superuser_token_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


def test_send_test_alert_non_admin(
    client: TestClient, normal_user_token_headers: dict
) -> None:
    """Test sending test alert as non-admin fails."""
    response = client.post(
        "/api/v1/alerts/test",
        headers=normal_user_token_headers,
    )

    assert response.status_code == 403


def test_update_nonexistent_rule(
    client: TestClient, superuser_token_headers: dict
) -> None:
    """Test updating non-existent rule."""
    import uuid

    fake_id = str(uuid.uuid4())

    response = client.patch(
        f"/api/v1/alerts/rules/{fake_id}",
        json={"name": "New Name"},
        headers=superuser_token_headers,
    )

    assert response.status_code == 404


def test_delete_nonexistent_rule(
    client: TestClient, superuser_token_headers: dict
) -> None:
    """Test deleting non-existent rule."""
    import uuid

    fake_id = str(uuid.uuid4())

    response = client.delete(
        f"/api/v1/alerts/rules/{fake_id}",
        headers=superuser_token_headers,
    )

    assert response.status_code == 404
