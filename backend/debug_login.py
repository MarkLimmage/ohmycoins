from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

login_data = {
    "username": settings.FIRST_SUPERUSER,
    "password": settings.FIRST_SUPERUSER_PASSWORD,
}

print(f"Attempting login with username: {login_data['username']}")
r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)

print(f"Status Code: {r.status_code}")
print(f"Response: {r.json()}")
