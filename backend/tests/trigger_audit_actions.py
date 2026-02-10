import httpx
import time

BASE_URL = "http://localhost:8000/api/v1"

def trigger_actions():
    print(f"Triggering Actions at {BASE_URL}")

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
        print(f"Failed to connect: {e}")
        return

    # Activate
    print("\nActivating Emergency Stop (Should log CRITICAL)...")
    r = httpx.post(f"{BASE_URL}/admin/emergency-stop/activate", headers=headers)
    print(f"Response: {r.status_code}")

    # Clear
    print("\nClearing Emergency Stop (Should log WARNING)...")
    r = httpx.post(f"{BASE_URL}/admin/emergency-stop/clear", headers=headers)
    print(f"Response: {r.status_code}")

if __name__ == "__main__":
    trigger_actions()
