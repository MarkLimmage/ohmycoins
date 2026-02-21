#!/usr/bin/env python3
"""
Governance Supervisor Script
Location: scripts/governance/supervisor.py
Author: The Architect

Purpose:
  This script enforces the Project Governance protocol.
  It compares the REALITY (agent status files) against the PLAN (registry).
  
  Alerts on:
  1. STAGNATION: Agent has not updated status > 10 mins.
  2. DRIFT: Agent is working on unauthorized tasks.
  3. INTEGRITY: Status file is missing or corrupted.

Usage:
  This script is run periodically by the Architect or a Cron job.
  It updates `logs/alerts_for_architect.json` with high-priority warnings.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# --- Configuration ---
SCRIPT_DIR = Path(__file__).parent.resolve()
REGISTRY_FILE = SCRIPT_DIR / "registry.json"
# We assume worktrees are at ../../sprint-X.XX/track-X relative to repo root
# Or simply ../../track-X for flattened structure.
# Let's use a flexible search pattern.
REPO_ROOT = SCRIPT_DIR.parent.parent
WORKTREE_ROOT = REPO_ROOT.parent # e.g. /home/mark/omc/

ALERT_FILE = REPO_ROOT / "logs" / "alerts_for_architect.json" # Ensure consistent path
STALE_THRESHOLD_SECONDS = 600 # 10 minutes

def load_registry() -> Dict[str, Any]:
    if not REGISTRY_FILE.exists():
        print(f"CRITICAL: Registry file not found at {REGISTRY_FILE}")
        return {}
    with open(REGISTRY_FILE, "r") as f:
        return json.load(f)

def scan_worktrees(registry: Dict[str, Any]) -> list:
    alerts = []
    
    print(f"Scanning worktrees in {WORKTREE_ROOT}...")
    
    # 1. Iterate through expected tracks in registry
    for track_name, expectations in registry.items():
        # Dynamically find the track directory
        # It could be ../sprint-2.29/track-a or ../track-a or ../omc-track-a
        # We search recursively for a directory named 'track-a'
        found_dirs = list(WORKTREE_ROOT.glob(f"**/{track_name}"))
        
        if not found_dirs:
            # If not found, skip (maybe sprint hasn't started)
            print(f"Warning: Worktree for {track_name} not found.")
            continue
            
        # Use the first match (assuming no duplicates)
        track_dir = found_dirs[0]
        status_file = track_dir / "status.json"
        
        # 2. Check for STATUS Presence
        if not status_file.exists():
            alerts.append({
                "agent": track_name,
                "timestamp": datetime.now().isoformat(),
                "issue": f"MISSING HEARTBEAT: {status_file} not found. Agent may be dormant.",
                "severity": "HIGH"
            })
            continue
            
        # 3. Validation Logic
        try:
            with open(status_file, "r") as f:
                status = json.load(f)
                
            # Check Stagnation
            last_update_str = status.get("last_update", "")
            try:
                # Handle possible offset issues by forcing both to naive
                last_update = datetime.fromisoformat(last_update_str)
                if last_update.tzinfo is not None:
                    last_update = last_update.replace(tzinfo=None)
                
                delta = (datetime.now() - last_update).total_seconds()
                
                if delta > STALE_THRESHOLD_SECONDS:
                     alerts.append({
                        "agent": track_name,
                        "timestamp": datetime.now().isoformat(),
                        "issue": f"STAGNATION: Agent silent for {int(delta/60)} mins. Last update: {last_update_str}",
                        "severity": "MEDIUM"
                    })
            except ValueError:
                 alerts.append({
                    "agent": track_name,
                    "timestamp": datetime.now().isoformat(),
                    "issue": f"CORRUPT TIMESTAMP: Could not parse '{last_update_str}'",
                    "severity": "LOW"
                })

            # Check Task Drift
            current_task = status.get("current_task", "Unknown")
            authorized = expectations.get("authorized_task", "Any")
            
            # Simple keyword matching to allow slight variation
            if authorized != "Any" and authorized.lower() not in current_task.lower():
                 alerts.append({
                    "agent": track_name,
                    "timestamp": datetime.now().isoformat(),
                    "issue": f"DRIFT DETECTED: Working on '{current_task}', but registered for '{authorized}'",
                    "severity": "HIGH"
                })

        except json.JSONDecodeError:
            alerts.append({
                "agent": track_name,
                "timestamp": datetime.now().isoformat(),
                "issue": f"CORRUPT FILE: {status_file} contains invalid JSON.",
                "severity": "MEDIUM"
            })
            
    return alerts

def main():
    print(f"Supervisor Active. Root: {REPO_ROOT}")
    registry = load_registry()
    
    if not registry:
        sys.exit(1)
        
    alerts = scan_worktrees(registry)
    
    # Merge with existing Watchdog alerts if possible to present a unified view
    existing_data = {}
    if ALERT_FILE.exists():
        try:
            with open(ALERT_FILE, "r") as f:
                existing_data = json.load(f)
        except:
            pass
    
    # Combine lists (supervisor alerts + watchdog alerts)
    existing_alerts = existing_data.get("alerts", [])
    # Filter out previous Supervisor alerts to avoid duplicates/stale data
    # We assume 'severity' key distinguishes Supervisor alerts from Watchdog (which uses 'file')
    watchdog_alerts = [a for a in existing_alerts if "severity" not in a]
    
    final_alerts = watchdog_alerts + alerts
    
    if alerts:
        print(f"🚨 GOVERNANCE VIOLATION: Found {len(alerts)} issues.")
        for a in alerts:
            print(f"  - [{a['agent']}] {a['issue']}")
    else:
        print("✅ Governance Check Passed.")

    # Write back
    try:
        ALERT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(ALERT_FILE, "w") as f:
            json.dump({
                "alerts": final_alerts,
                "last_scan": datetime.now().isoformat(),
                "status": "active"
            }, f, indent=4)
    except Exception as e:
        print(f"Error writing alert file: {e}")

if __name__ == "__main__":
    main()
