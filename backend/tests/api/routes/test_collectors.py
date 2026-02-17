import uuid
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import Collector

def test_create_collector(client: TestClient, superuser_token_headers: dict[str, str], session: Session) -> None:
    data = {"name": "Test Collector", "type": "API", "config": {"url": "http://example.com"}}
    response = client.post(
        f"{settings.API_V1_STR}/collectors/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == data["name"]
    assert content["type"] == data["type"]
    assert content["config"] == data["config"]
    assert "id" in content

def test_read_collector(client: TestClient, superuser_token_headers: dict[str, str], session: Session) -> None:
    collector = Collector(name="Read Collector", type="API", config={})
    session.add(collector)
    session.commit()
    
    response = client.get(
        f"{settings.API_V1_STR}/collectors/{collector.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == collector.name
    assert content["id"] == str(collector.id)

def test_update_collector(client: TestClient, superuser_token_headers: dict[str, str], session: Session) -> None:
    collector = Collector(name="Update Collector", type="API", config={})
    session.add(collector)
    session.commit()
    
    data = {"name": "Updated Collector", "is_active": False}
    response = client.put(
        f"{settings.API_V1_STR}/collectors/{collector.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == "Updated Collector"
    assert content["is_active"] is False

def test_delete_collector(client: TestClient, superuser_token_headers: dict[str, str], session: Session) -> None:
    collector = Collector(name="Delete Collector", type="API", config={})
    session.add(collector)
    session.commit()
    
    response = client.delete(
        f"{settings.API_V1_STR}/collectors/{collector.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    
    response = client.get(
        f"{settings.API_V1_STR}/collectors/{collector.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
