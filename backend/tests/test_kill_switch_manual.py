
import httpx

BASE_URL = "http://localhost:8000/api/v1"

def test_kill_switch():
    print(f"Testing Kill Switch at {BASE_URL}")

    # Login
    print("Logging in...")
    login_data = {
        "username": "admin@example.com",
        "password": "adminadmin"
    }
    try:
        r = httpx.post(f"{BASE_URL}/login/access-token", data=login_data)
        if r.status_code != 200:
            print(f"Login Failed: {r.status_code} - {r.text}")
            return
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login Successful!")
    except Exception as e:
        print(f"Failed to connect for login: {e}")
        return

    # Check initial status
    try:
        r = httpx.get(f"{BASE_URL}/admin/emergency-stop/status", headers=headers)
        print(f"Initial Status: {r.status_code} - {r.json()}")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    # Activate
    print("\nActivating Emergency Stop...")
    r = httpx.post(f"{BASE_URL}/admin/emergency-stop/activate", headers=headers)
    print(f"Activation Response: {r.status_code} - {r.json()}")

    # Check Status
    print("\nChecking Status (Expect Active)...")
    r = httpx.get(f"{BASE_URL}/admin/emergency-stop/status", headers=headers)
    print(f"Status: {r.status_code} - {r.json()}")
    if r.json().get("status") == "active":
        print("✅ Correct: Status is Active")
    else:
        print("❌ Incorrect: Status should be Active")

    # Clear
    print("\nClearing Emergency Stop...")
    r = httpx.post(f"{BASE_URL}/admin/emergency-stop/clear", headers=headers)
    print(f"Clear Response: {r.status_code} - {r.json()}")

    # Check Status
    print("\nChecking Status (Expect Inactive)...")
    r = httpx.get(f"{BASE_URL}/admin/emergency-stop/status", headers=headers)
    print(f"Status: {r.status_code} - {r.json()}")
    if r.json().get("status") == "inactive":
        print("✅ Correct: Status is Inactive")
    else:
        print("❌ Incorrect: Status should be Inactive")

if __name__ == "__main__":
    test_kill_switch()
