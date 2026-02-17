import os
import time

import httpx

# Running inside container, target localhost or self
BASE_URL = "http://localhost:8000/api/v1"

# Try to get credentials from env or default
USERNAME = os.getenv("FIRST_SUPERUSER", "admin@example.com")
PASSWORD = os.getenv("FIRST_SUPERUSER_PASSWORD", "changethis")

def main():

    # Authenticate
    try:
        r = httpx.post(f"{BASE_URL}/login/access-token", data={
            "username": USERNAME,
            "password": PASSWORD
        })
        if r.status_code != 200:
            # Fallback attempt
            if PASSWORD != "adminadmin":
                 r = httpx.post(f"{BASE_URL}/login/access-token", data={
                    "username": USERNAME,
                    "password": "adminadmin"
                 })

        if r.status_code != 200:
             return

        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

    except Exception:
        return

    # Toggle Kill Switch a few times
    for i in range(1, 6):
        active = (i % 2 != 0) # True, False, True, False, True

        r = httpx.post(
            f"{BASE_URL}/risk/kill-switch",
            params={"active": active},
            headers=headers
        )

        if r.status_code == 200:
            pass
        else:
            pass

        time.sleep(0.5)

if __name__ == "__main__":
    main()
