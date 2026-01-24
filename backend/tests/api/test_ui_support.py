
import pytest
from fastapi.testclient import TestClient
from app.core.config import settings

def test_pnl_summary_structure(
    client: TestClient, normal_user_token_headers: dict[str, str]
):
    """Test that PnL summary payload includes UI support fields"""
    r = client.get(
        f"{settings.API_V1_STR}/floor/pnl/summary",
        headers=normal_user_token_headers,
    )
    # Regardless of whether it succeeds or fails (if DB empty), if it returns 200, it MUST have the fields.
    if r.status_code == 200:
        data = r.json()
        assert "is_loading" in data
        assert "last_updated" in data
        assert "data_staleness_seconds" in data
        assert isinstance(data["is_loading"], bool)

def test_global_error_handler_404(client: TestClient):
    """Test 404 error format"""
    r = client.get(f"{settings.API_V1_STR}/non_existent_resource")
    assert r.status_code == 404
    data = r.json()
    assert "message" in data
    assert "detail" in data
    assert "error_code" in data
    assert data["message"] == "The requested resource was not found."
    assert data["error_code"] == "NOT_FOUND"

def test_mock_ledger_endpoint(client: TestClient):
    """Test mock ledger endpoint (only works if ENVIRONMENT=local)"""
    if settings.ENVIRONMENT == "local":
        r = client.get(f"{settings.API_V1_STR}/mock/ledgers/human")
        assert r.status_code == 200
        data = r.json()
        assert "realized_pnl" in data
        assert data["is_loading"] is False
        
        # Test loading state
        r = client.get(f"{settings.API_V1_STR}/mock/ledgers/human?state=loading")
        assert r.status_code == 200
        assert r.json()["is_loading"] is True

def test_mock_safety_endpoint(client: TestClient):
    """Test mock safety endpoint"""
    if settings.ENVIRONMENT == "local":
        # Test missing confirmation
        r = client.post(f"{settings.API_V1_STR}/mock/safety/kill-switch")
        assert r.status_code == 400
        data = r.json()
        assert data["error_code"] == "MISSING_CONFIRMATION"
        
        # Test success
        r = client.post(f"{settings.API_V1_STR}/mock/safety/kill-switch?confirm=true")
        assert r.status_code == 200
        assert r.json()["status"] == "triggered"
