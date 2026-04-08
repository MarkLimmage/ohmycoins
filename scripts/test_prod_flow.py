"""Test the full approval flow on prod to reproduce routing loop."""
import requests
import json
import time
import sys

BASE = "http://localhost:8000/api/v1"

def login():
    r = requests.post(f"{BASE}/login/access-token", data={"username": "labtest@ohmycoins.com", "password": "TestPass123!"})
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def get_session(headers, sid):
    r = requests.get(f"{BASE}/lab/agent/sessions/{sid}", headers=headers)
    r.raise_for_status()
    return r.json()

def print_session(data):
    print(f"  Status: {data.get('status')}")
    print(f"  Current node: {data.get('current_node')}")
    stages = data.get("stages", [])
    for s in stages:
        print(f"    Stage: {s.get('name')} -> {s.get('status')}")
    # Print pending approvals
    pending = data.get("pending_events", [])
    if pending:
        for p in pending:
            print(f"    Pending: {p.get('event_type')} at {p.get('node_name')}")

def approve(headers, sid, event_id):
    r = requests.post(f"{BASE}/lab/agent/sessions/{sid}/approve", json={"approved": True}, headers=headers)
    print(f"  Approve response: {r.status_code}")
    if r.status_code != 200:
        print(f"  Body: {r.text[:300]}")
    return r

def resume(headers, sid):
    r = requests.post(f"{BASE}/lab/agent/sessions/{sid}/resume", headers=headers)
    print(f"  Resume response: {r.status_code}")
    if r.status_code != 200:
        print(f"  Body: {r.text[:300]}")
    return r

def main():
    headers = login()
    print("Logged in")
    
    # If session ID provided, use existing
    if len(sys.argv) > 1:
        sid = sys.argv[1]
        print(f"\nUsing existing session: {sid}")
    else:
        # Create new session
        r = requests.post(f"{BASE}/lab/agent/sessions", json={"user_goal": "Build a machine learning model to predict BTC price using historical data"}, headers=headers)
        r.raise_for_status()
        data = r.json()
        sid = data["id"]
        print(f"\nCreated session: {sid}")
        print_session(data)
    
    # Wait for initial processing
    print("\nWaiting 10s for initial processing...")
    time.sleep(10)
    
    data = get_session(headers, sid)
    print(f"\nAfter initial processing:")
    print_session(data)
    
    # Loop: approve and watch for up to 5 cycles
    for cycle in range(5):
        status = data.get("status", "")
        if status not in ("awaiting_approval", "paused"):
            print(f"\nSession is '{status}', not awaiting approval. Done.")
            break
        
        print(f"\n--- Cycle {cycle+1}: Approving ---")
        approve(headers, sid, None)
        
        print("Waiting 15s for processing...")
        time.sleep(15)
        
        data = get_session(headers, sid)
        print(f"\nAfter approval cycle {cycle+1}:")
        print_session(data)
    
    print(f"\nFinal session state:")
    data = get_session(headers, sid)
    print(json.dumps({k: data.get(k) for k in ["id", "status", "current_node", "stages", "pending_events"]}, indent=2, default=str))

if __name__ == "__main__":
    main()
