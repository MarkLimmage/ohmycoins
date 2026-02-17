
import httpx

BASE_URL = "http://localhost:8000/api/v1"

def trigger_actions():

    # Login
    login_data = {
        "username": "admin@example.com",
        "password": "adminadmin"
    }
    try:
        r = httpx.post(f"{BASE_URL}/login/access-token", data=login_data)
        if r.status_code != 200:
            return
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
    except Exception:
        return

    # Activate
    r = httpx.post(f"{BASE_URL}/admin/emergency-stop/activate", headers=headers)

    # Clear
    r = httpx.post(f"{BASE_URL}/admin/emergency-stop/clear", headers=headers)

if __name__ == "__main__":
    trigger_actions()
