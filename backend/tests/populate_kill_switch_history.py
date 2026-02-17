import os
import time

import httpx

# Running inside container, target localhost or self
BASE_URL = "http://localhost:8000/api/v1"

# Try to get credentials from env or default
USERNAME = os.getenv("FIRST_SUPERUSER", "admin@example.com")
PASSWORD = os.getenv("FIRST_SUPERUSER_PASSWORD", "changethis")

def main():
    print(f"Connecting to {BASE_URL} with user {USERNAME}...")

    # Authenticate
    try:
        r = httpx.post(f"{BASE_URL}/login/access-token", data={
            "username": USERNAME,
            "password": PASSWORD
        })
        if r.status_code != 200:
            print(f"Login failed: {r.status_code} {r.text}")
            # Fallback attempt
            if PASSWORD != "adminadmin":
                 print("Retrying with adminadmin...")
                 r = httpx.post(f"{BASE_URL}/login/access-token", data={
                    "username": USERNAME,
                    "password": "adminadmin"
                 })

        if r.status_code != 200:
             print(f"Login really failed: {r.status_code} {r.text}")
             return

        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Logged in successfully.")

    except Exception as e:
        print(f"Connection error: {e}")
        return

    # Toggle Kill Switch a few times
    print("Generating Kill Switch Audit Logs...")
    for i in range(1, 6):
        active = (i % 2 != 0) # True, False, True, False, True
        print(f"[{i}/5] Setting Kill Switch to {active}...")

        r = httpx.post(
            f"{BASE_URL}/risk/kill-switch",
            params={"active": active},
            headers=headers
        )

        if r.status_code == 200:
            print(f"Success: {r.json()}")
        else:
            print(f"Failed: {r.status_code} {r.text}")

        time.sleep(0.5)

if __name__ == "__main__":
    main()
