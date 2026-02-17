from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)

login_data = {
    "username": settings.FIRST_SUPERUSER,
    "password": settings.FIRST_SUPERUSER_PASSWORD,
}

print(f"Attempting login with username: {login_data['username']}")  # noqa: T201
r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)

print(f"Status Code: {r.status_code}")  # noqa: T201
print(f"Response: {r.json()}")  # noqa: T201
