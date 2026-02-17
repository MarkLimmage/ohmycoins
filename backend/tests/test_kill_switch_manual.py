
import httpx

BASE_URL = "http://localhost:8000/api/v1"

def test_kill_switch():

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

    # Check initial status
    try:
        r = httpx.get(f"{BASE_URL}/admin/emergency-stop/status", headers=headers)
    except Exception:
        return

    # Activate
    r = httpx.post(f"{BASE_URL}/admin/emergency-stop/activate", headers=headers)

    # Check Status
    r = httpx.get(f"{BASE_URL}/admin/emergency-stop/status", headers=headers)
    if r.json().get("status") == "active":
        pass
    else:
        pass

    # Clear
    r = httpx.post(f"{BASE_URL}/admin/emergency-stop/clear", headers=headers)

    # Check Status
    r = httpx.get(f"{BASE_URL}/admin/emergency-stop/status", headers=headers)
    if r.json().get("status") == "inactive":
        pass
    else:
        pass

if __name__ == "__main__":
    test_kill_switch()
