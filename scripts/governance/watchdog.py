#!/usr/bin/env python3
"""
Governance Watchdog Script
Location: scripts/governance/watchdog.py

This script monitors the centralized log hub for critical errors across all active agent tracks.
It is designed to run on the HOST machine or within a Governance Container.

Log Path Logic:
- HOST MODE: Looks for logs in `../../logs/hub` relative to the script location (assuming script is in repo/scripts/governance).
- CONTAINER MODE: Looks for logs in `/var/log/omc-agents` (if mounted).
- ENV OVERRIDE: Uses `OMC_LOG_HUB` environment variable if set.
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime

# --- Configuration ---
# Determine the log directory dynamically
SCRIPT_DIR = Path(__file__).parent.resolve()
# Default host path: (repo)/scripts/governance/../../../../logs/hub -> (project_root)/../logs/hub
# Actually, if we are in /home/mark/omc/ohmycoins/scripts/governance
# We want /home/mark/omc/logs/hub
HOST_LOG_DEFAULT = Path("/home/mark/omc/logs/hub")
CONTAINER_LOG_DEFAULT = Path("/var/log/omc-agents")

# Choose logic based on environment
if os.environ.get("OMC_LOG_HUB"):
    LOG_DIR = Path(os.environ["OMC_LOG_HUB"])
elif CONTAINER_LOG_DEFAULT.exists():
    LOG_DIR = CONTAINER_LOG_DEFAULT
else:
    LOG_DIR = HOST_LOG_DEFAULT

ALERT_FILE = LOG_DIR.parent / "alerts_for_architect.json"

# Critical patterns that halt development
ERROR_PATTERNS = [
    "Error:", "exception", "failed", "traceback", 
    "Port already in use", "rate limit exceeded", 
    "context_length_exceeded", "infinite loop detected",
    "FATAL", "CRITICAL", "BlockingIOError"
]

def scan_logs():
    alerts = []
    
    if not LOG_DIR.exists():
        # Only warn, do not crash, as logs might appear later
        # print(f"Waiting for logs at {LOG_DIR}...")
        return []

    # Scan for track-specific log files (e.g., track-a/session.log)
    # Recursively look for any .log file, but ideally session.log
    for log_path in LOG_DIR.glob("**/*.log"):
        agent_name = log_path.parent.name
        
        try:
            with open(log_path, "r", encoding='utf-8', errors='ignore') as f:
                # Read last 50 lines to keep context fresh and token-light
                lines = f.readlines()[-50:]
                
                for line in lines:
                    if any(pattern.lower() in line.lower() for pattern in ERROR_PATTERNS):
                        alerts.append({
                            "agent": agent_name,
                            "timestamp": datetime.now().isoformat(),
                            "issue": line.strip(),
                            "file": str(log_path)
                        })
                        # Once we find a critical error, we move to the next file
                        break 
        except Exception as e:
            print(f"Error reading {log_path}: {e}")

    return alerts

def main():
    print(f"Watchdog active. Monitoring {LOG_DIR}...")
    
    # Ensure logs directory exists for output
    try:
        ALERT_FILE.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Could not create alert file directory: {e}")

    while True:
        try:
            current_alerts = scan_logs()
            
            # Write to a JSON file the Architect can "read" in one shot
            with open(ALERT_FILE, "w") as f:
                json.dump({
                    "alerts": current_alerts, 
                    "last_scan": datetime.now().isoformat(),
                    "status": "active",
                    "monitored_path": str(LOG_DIR)
                }, f, indent=4)
            
            if current_alerts:
                print(f"🚨 Found {len(current_alerts)} issues. Updated {ALERT_FILE}")
        except Exception as e:
            print(f"Watchdog Loop Error: {e}")
        
        # Poll every 30 seconds to save CPU/Disk IO
        time.sleep(30)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nWatchdog stopped.")
