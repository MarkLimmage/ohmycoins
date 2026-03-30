"""Lab Workflow Driver — CLI tool for driving and observing Lab workflows.

Usage:
    python scripts/lab_driver.py create --goal "Analyze BTC sentiment..."
    python scripts/lab_driver.py watch <session_id> --timeout 120
    python scripts/lab_driver.py approve <session_id>
    python scripts/lab_driver.py status <session_id>
    python scripts/lab_driver.py auto --goal "..." --timeout 300

Exit codes: 0=success, 1=error, 2=HITL gate, 3=timeout
"""
import argparse
import json
import os
import sys
import time

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_HOST = os.environ.get("LAB_HOST", "http://192.168.0.241:8001")
DEFAULT_USER = os.environ.get("LAB_USER", "labtest@ohmycoins.com")
DEFAULT_PASS = os.environ.get("LAB_PASSWORD", "TestPass123!")
POLL_INTERVAL = 2  # seconds between rehydrate polls
STALL_WARN = 60  # seconds without new events before warning

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_GATE = 2
EXIT_TIMEOUT = 3

# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

_token_cache: dict[str, str] = {}


def login(host: str) -> str:
    """Authenticate and return JWT token."""
    if host in _token_cache:
        return _token_cache[host]
    r = requests.post(
        f"{host}/api/v1/login/access-token",
        data={"username": DEFAULT_USER, "password": DEFAULT_PASS},
        timeout=10,
    )
    if r.status_code != 200:
        print(f"LOGIN FAILED: {r.status_code} {r.text[:200]}", file=sys.stderr)
        sys.exit(EXIT_ERROR)
    token = r.json()["access_token"]
    _token_cache[host] = token
    return token


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def api_get(host: str, token: str, path: str, retries: int = 2) -> dict:
    url = f"{host}/api/v1/lab/agent{path}"
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, headers=headers(token), timeout=60)
            if r.status_code != 200:
                print(f"GET {path} → {r.status_code}: {r.text[:300]}", file=sys.stderr)
                sys.exit(EXIT_ERROR)
            return r.json()
        except requests.exceptions.Timeout:
            if attempt < retries:
                print(f"  (timeout on GET {path}, retry {attempt + 1}/{retries})")
                time.sleep(2)
            else:
                print(f"GET {path} → timeout after {retries + 1} attempts", file=sys.stderr)
                sys.exit(EXIT_ERROR)
    return {}  # unreachable


def api_post(host: str, token: str, path: str, body: dict | None = None, retries: int = 2) -> dict:
    url = f"{host}/api/v1/lab/agent{path}"
    # Approve can take a long time as the server resumes the workflow synchronously
    is_approve = "/approve" in path
    timeout = 120 if is_approve else 60
    for attempt in range(retries + 1):
        try:
            r = requests.post(url, headers=headers(token), json=body, timeout=timeout)
            if r.status_code not in (200, 201):
                print(f"POST {path} → {r.status_code}: {r.text[:300]}", file=sys.stderr)
                sys.exit(EXIT_ERROR)
            return r.json()
        except requests.exceptions.Timeout:
            if attempt < retries:
                print(f"  (timeout on POST {path}, retry {attempt + 1}/{retries})")
                time.sleep(2)
            else:
                print(f"POST {path} → timeout after {retries + 1} attempts", file=sys.stderr)
                sys.exit(EXIT_ERROR)
    return {}  # unreachable


# ---------------------------------------------------------------------------
# Event formatting
# ---------------------------------------------------------------------------

def format_event(evt: dict) -> str:
    """Format a single event as a one-line string."""
    etype = evt.get("event_type", "unknown")
    stage = evt.get("stage", "")
    payload = evt.get("payload", {})
    seq = evt.get("sequence_id", "?")
    ts = evt.get("timestamp", "")
    # trim timestamp to HH:MM:SS
    if "T" in str(ts):
        ts = str(ts).split("T")[1][:8]

    if etype == "stream_chat":
        text = payload.get("text_delta", "") or payload.get("content", "")
        return f"{ts} [{seq:>3}] [CHAT] {text[:200]}"

    if etype == "status_update":
        status = payload.get("status", "")
        msg = payload.get("message", "")
        task_id = payload.get("task_id", "")
        prefix = f"{task_id} " if task_id else ""
        return f"{ts} [{seq:>3}] [TASK] {prefix}{status}: {msg}"

    if etype == "render_output":
        mime = payload.get("mime_type", "")
        content = payload.get("content", "")
        if isinstance(content, dict):
            content = json.dumps(content, default=str)[:200]
        elif isinstance(content, str):
            content = content[:200].replace("\n", " ↵ ")
        return f"{ts} [{seq:>3}] [OUTPUT:{stage}] ({mime}) {content}"

    if etype == "action_request":
        desc = payload.get("description", "")
        action_id = payload.get("action_id", "")
        return f"{ts} [{seq:>3}] [GATE] {action_id}: {desc}"

    if etype == "plan_established":
        return f"{ts} [{seq:>3}] [PLAN] {json.dumps(payload, default=str)[:200]}"

    if etype == "revision_start":
        revised = payload.get("revised_stage", "")
        stale = payload.get("stale_stages", [])
        return f"{ts} [{seq:>3}] [REVISION] stage={revised} stale={stale}"

    if etype == "user_message":
        content = payload.get("content", "")
        return f"{ts} [{seq:>3}] [USER] {content[:200]}"

    if etype == "error":
        msg = payload.get("message", str(payload))
        return f"{ts} [{seq:>3}] [ERROR] {msg}"

    # Fallback
    return f"{ts} [{seq:>3}] [{etype.upper()}] {json.dumps(payload, default=str)[:200]}"


def print_events(events: list[dict]) -> None:
    for evt in events:
        print(format_event(evt))


# ---------------------------------------------------------------------------
# Gate detection
# ---------------------------------------------------------------------------

def _safe_get(host: str, token: str, path: str) -> dict | None:
    """GET that returns None on error instead of sys.exit."""
    url = f"{host}/api/v1/lab/agent{path}"
    try:
        r = requests.get(url, headers=headers(token), timeout=30)
        if r.status_code == 200:
            return r.json()
    except requests.exceptions.RequestException:
        pass
    return None


def detect_gate(host: str, token: str, sid: str) -> dict | None:
    """Check all HITL endpoints. Returns gate info dict or None."""
    # Check session status first
    session = api_get(host, token, f"/sessions/{sid}")
    status = session.get("status", "")

    if status == "awaiting_approval":
        approvals = _safe_get(host, token, f"/sessions/{sid}/pending-approvals")
        if approvals and approvals.get("approval_needed"):
            pending = approvals.get("pending_approvals", [])
            return {
                "type": "approval",
                "pending": pending,
                "description": pending[0].get("description", "") if pending else "",
                "approval_type": pending[0].get("approval_type", "") if pending else "",
            }

    # Also check clarifications/choices even if status isn't explicit
    clar = _safe_get(host, token, f"/sessions/{sid}/clarifications")
    if clar and clar.get("awaiting_clarification"):
        return {
            "type": "clarification",
            "clarifications_needed": clar.get("clarifications_needed", []),
            "current_goal": clar.get("current_goal"),
        }

    choices = _safe_get(host, token, f"/sessions/{sid}/choices")
    if choices and choices.get("awaiting_choice"):
        return {
            "type": "choice",
            "choices_available": choices.get("choices_available", []),
            "recommendation": choices.get("recommendation"),
        }

    return None


def check_terminal(host: str, token: str, sid: str) -> str | None:
    """Return terminal status string if session is done, else None."""
    session = api_get(host, token, f"/sessions/{sid}")
    status = session.get("status", "")
    if status in ("completed", "failed", "cancelled"):
        return status
    return None


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_create(args: argparse.Namespace) -> None:
    token = login(args.host)
    data = api_post(args.host, token, "/sessions", {"user_goal": args.goal})
    sid = data["id"]
    status = data.get("status", "?")
    print(f"SESSION_ID={sid}")
    print(f"STATUS={status}")
    print(f"GOAL={args.goal}")


def cmd_watch(args: argparse.Namespace) -> None:
    token = login(args.host)
    sid = args.session_id
    timeout = args.timeout
    event_count = 0
    last_new_event_time = time.time()
    start = time.time()
    stall_warned = False

    if args.all:
        last_seq = 0
    else:
        # Start from current last_seq so subsequent watches only show NEW events
        rehydrate = api_get(args.host, token, f"/sessions/{sid}/rehydrate")
        last_seq = rehydrate.get("last_sequence_id", 0) or 0

    print(f"WATCHING session={sid} timeout={timeout}s (from seq={last_seq})")
    print("---")

    while True:
        elapsed = time.time() - start

        # Check timeout
        if timeout and elapsed > timeout:
            print(f"\n--- TIMEOUT after {elapsed:.0f}s | events={event_count} ---")
            sys.exit(EXIT_TIMEOUT)

        # Check terminal state
        terminal = check_terminal(args.host, token, sid)
        if terminal:
            # Drain remaining events
            rehydrate = api_get(args.host, token, f"/sessions/{sid}/rehydrate")
            ledger = rehydrate.get("event_ledger", [])
            new_events = [e for e in ledger if (e.get("sequence_id") or 0) > last_seq]
            if new_events:
                print_events(new_events)
                event_count += len(new_events)
            print(f"\n--- {terminal.upper()} | events={event_count} | elapsed={elapsed:.0f}s ---")
            sys.exit(EXIT_OK if terminal == "completed" else EXIT_ERROR)

        # Poll rehydrate for new events
        rehydrate = api_get(args.host, token, f"/sessions/{sid}/rehydrate")
        ledger = rehydrate.get("event_ledger", [])
        new_events = [e for e in ledger if (e.get("sequence_id") or 0) > last_seq]

        if new_events:
            print_events(new_events)
            event_count += len(new_events)
            last_seq = max(e.get("sequence_id", 0) or 0 for e in new_events)
            last_new_event_time = time.time()
            stall_warned = False

        # Check for HITL gate
        gate = detect_gate(args.host, token, sid)
        if gate:
            gtype = gate["type"]
            if gtype == "approval":
                desc = gate.get("description", "")
                atype = gate.get("approval_type", "")
                print(f"\n--- GATE: {gtype} | approval_type={atype} | {desc} ---")
                for p in gate.get("pending", []):
                    print(f"  {p.get('approval_type', '?')}: {p.get('description', '')}")
            elif gtype == "clarification":
                print(f"\n--- GATE: {gtype} ---")
                for c in gate.get("clarifications_needed", []):
                    print(f"  {c}")
            elif gtype == "choice":
                print(f"\n--- GATE: {gtype} ---")
                for c in gate.get("choices_available", []):
                    print(f"  {c}")
                rec = gate.get("recommendation")
                if rec:
                    print(f"  Recommendation: {rec}")
            sys.exit(EXIT_GATE)

        # Stall detection
        stall_secs = time.time() - last_new_event_time
        if stall_secs > STALL_WARN and not stall_warned:
            print(f"  ⚠ STALL: no new events for {stall_secs:.0f}s (last_seq={last_seq})")
            stall_warned = True

        time.sleep(POLL_INTERVAL)


def cmd_approve(args: argparse.Namespace) -> None:
    token = login(args.host)
    sid = args.session_id
    approved = not args.reject
    body: dict = {"approved": approved}
    if args.reason:
        body["reason"] = args.reason

    result = api_post(args.host, token, f"/sessions/{sid}/approve", body)
    status = "APPROVED" if approved else "REJECTED"
    print(f"{status}: {result.get('message', 'done')}")


def cmd_clarify(args: argparse.Namespace) -> None:
    token = login(args.host)
    sid = args.session_id

    # Show current clarification state
    clar = api_get(args.host, token, f"/sessions/{sid}/clarifications")
    if not clar.get("awaiting_clarification"):
        print("No clarification pending")
        return

    print("Clarifications needed:")
    for c in clar.get("clarifications_needed", []):
        print(f"  {c}")

    responses = json.loads(args.responses)
    result = api_post(args.host, token, f"/sessions/{sid}/clarifications", {"responses": responses})
    print(f"CLARIFIED: {result.get('message', 'done')}")


def cmd_choose(args: argparse.Namespace) -> None:
    token = login(args.host)
    sid = args.session_id

    # Show current choices
    choices = api_get(args.host, token, f"/sessions/{sid}/choices")
    if not choices.get("awaiting_choice"):
        print("No choice pending")
        return

    print("Available choices:")
    for c in choices.get("choices_available", []):
        print(f"  {c}")
    rec = choices.get("recommendation")
    if rec:
        print(f"Recommendation: {rec}")

    body: dict = {"action": args.action}
    if args.model:
        body["selected_model"] = args.model
    result = api_post(args.host, token, f"/sessions/{sid}/choices", body)
    print(f"CHOSEN: {result.get('message', 'done')}")


def cmd_status(args: argparse.Namespace) -> None:
    token = login(args.host)
    sid = args.session_id

    # Session metadata
    session = api_get(args.host, token, f"/sessions/{sid}")
    print(f"Session: {sid}")
    print(f"  Status:  {session.get('status')}")
    print(f"  Created: {session.get('created_at')}")
    print(f"  Updated: {session.get('updated_at')}")
    if session.get("error_message"):
        print(f"  Error:   {session['error_message']}")

    # Pending approvals
    try:
        approvals = api_get(args.host, token, f"/sessions/{sid}/pending-approvals")
        if approvals.get("approval_needed"):
            print(f"  GATE: approval needed")
            for p in approvals.get("pending_approvals", []):
                print(f"    {p.get('approval_type')}: {p.get('description')}")
    except SystemExit:
        pass

    # Event ledger summary
    rehydrate = api_get(args.host, token, f"/sessions/{sid}/rehydrate")
    ledger = rehydrate.get("event_ledger", [])
    print(f"  Events:  {len(ledger)} (last_seq={rehydrate.get('last_sequence_id')})")

    # Group by stage
    stages: dict[str, list[dict]] = {}
    for evt in ledger:
        stage = evt.get("stage", "UNKNOWN")
        stages.setdefault(stage, []).append(evt)

    print("\n--- Events by Stage ---")
    for stage, events in stages.items():
        types = {}
        for e in events:
            t = e.get("event_type", "?")
            types[t] = types.get(t, 0) + 1
        type_summary = ", ".join(f"{k}={v}" for k, v in sorted(types.items()))
        print(f"\n  [{stage}] ({len(events)} events: {type_summary})")
        for evt in events:
            print(f"    {format_event(evt)}")


def cmd_events(args: argparse.Namespace) -> None:
    token = login(args.host)
    sid = args.session_id

    rehydrate = api_get(args.host, token, f"/sessions/{sid}/rehydrate")
    ledger = rehydrate.get("event_ledger", [])

    if args.json:
        for evt in ledger:
            print(json.dumps(evt, default=str))
    else:
        print_events(ledger)
        print(f"\n--- {len(ledger)} events | last_seq={rehydrate.get('last_sequence_id')} ---")


def cmd_auto(args: argparse.Namespace) -> None:
    token = login(args.host)
    timeout = args.timeout
    start = time.time()

    # Create session
    data = api_post(args.host, token, "/sessions", {"user_goal": args.goal})
    sid = data["id"]
    print(f"SESSION_ID={sid}")
    print(f"GOAL={args.goal}")
    print("---")

    last_seq = 0
    event_count = 0
    gate_count = 0

    while True:
        elapsed = time.time() - start
        if timeout and elapsed > timeout:
            print(f"\n--- TIMEOUT after {elapsed:.0f}s | events={event_count} gates={gate_count} ---")
            sys.exit(EXIT_TIMEOUT)

        # Check terminal state
        terminal = check_terminal(args.host, token, sid)
        if terminal:
            rehydrate = api_get(args.host, token, f"/sessions/{sid}/rehydrate")
            ledger = rehydrate.get("event_ledger", [])
            new_events = [e for e in ledger if (e.get("sequence_id") or 0) > last_seq]
            if new_events:
                print_events(new_events)
                event_count += len(new_events)
            print(f"\n--- {terminal.upper()} | events={event_count} | gates={gate_count} | elapsed={elapsed:.0f}s ---")
            sys.exit(EXIT_OK if terminal == "completed" else EXIT_ERROR)

        # Poll for new events
        rehydrate = api_get(args.host, token, f"/sessions/{sid}/rehydrate")
        ledger = rehydrate.get("event_ledger", [])
        new_events = [e for e in ledger if (e.get("sequence_id") or 0) > last_seq]
        if new_events:
            print_events(new_events)
            event_count += len(new_events)
            last_seq = max(e.get("sequence_id", 0) or 0 for e in new_events)

        # Auto-approve any gates
        gate = detect_gate(args.host, token, sid)
        if gate:
            gtype = gate["type"]
            gate_count += 1
            if gtype == "approval":
                desc = gate.get("description", "")
                print(f"\n  >> AUTO-APPROVE gate #{gate_count}: {desc}")
                api_post(args.host, token, f"/sessions/{sid}/approve", {"approved": True})
            elif gtype == "clarification":
                print(f"\n  >> AUTO-SKIP clarification gate #{gate_count} (cannot auto-respond)")
                # Can't auto-respond to clarifications — just approve if possible
                try:
                    api_post(args.host, token, f"/sessions/{sid}/approve", {"approved": True})
                except SystemExit:
                    print("  ⚠ Could not auto-approve clarification gate")
            elif gtype == "choice":
                rec = gate.get("recommendation")
                print(f"\n  >> AUTO-CHOOSE gate #{gate_count}: {rec or 'default'}")
                body: dict = {"action": "PROMOTE_MODEL"}
                if rec:
                    body["selected_model"] = rec
                try:
                    api_post(args.host, token, f"/sessions/{sid}/choices", body)
                except SystemExit:
                    # Fall back to simple approve
                    api_post(args.host, token, f"/sessions/{sid}/approve", {"approved": True})

        time.sleep(POLL_INTERVAL)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lab_driver",
        description="Drive and observe Lab agentic workflows via REST API.",
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"API host (default: {DEFAULT_HOST})")
    sub = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = sub.add_parser("create", help="Start a new workflow session")
    p_create.add_argument("--goal", required=True, help="User goal for the workflow")

    # watch
    p_watch = sub.add_parser("watch", help="Watch session events until gate or timeout")
    p_watch.add_argument("session_id", help="Session UUID")
    p_watch.add_argument("--timeout", type=int, default=120, help="Timeout in seconds (default: 120)")
    p_watch.add_argument("--all", action="store_true", help="Show all events from beginning (default: only new)")

    # approve
    p_approve = sub.add_parser("approve", help="Approve current HITL gate")
    p_approve.add_argument("session_id", help="Session UUID")
    p_approve.add_argument("--reject", action="store_true", help="Reject instead of approve")
    p_approve.add_argument("--reason", help="Reason for rejection")

    # clarify
    p_clarify = sub.add_parser("clarify", help="Respond to clarification request")
    p_clarify.add_argument("session_id", help="Session UUID")
    p_clarify.add_argument("--responses", required=True, help='JSON object: \'{"key": "value"}\'')

    # choose
    p_choose = sub.add_parser("choose", help="Select model at choice gate")
    p_choose.add_argument("session_id", help="Session UUID")
    p_choose.add_argument("--model", help="Model name to select")
    p_choose.add_argument("--action", default="PROMOTE_MODEL", help="Action (PROMOTE_MODEL or RETRAIN)")

    # status
    p_status = sub.add_parser("status", help="Full state dump for a session")
    p_status.add_argument("session_id", help="Session UUID")

    # events
    p_events = sub.add_parser("events", help="Dump raw event ledger")
    p_events.add_argument("session_id", help="Session UUID")
    p_events.add_argument("--json", action="store_true", help="Output as JSONL")

    # auto
    p_auto = sub.add_parser("auto", help="Unattended full run with auto-approve")
    p_auto.add_argument("--goal", required=True, help="User goal for the workflow")
    p_auto.add_argument("--timeout", type=int, default=300, help="Timeout in seconds (default: 300)")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    dispatch = {
        "create": cmd_create,
        "watch": cmd_watch,
        "approve": cmd_approve,
        "clarify": cmd_clarify,
        "choose": cmd_choose,
        "status": cmd_status,
        "events": cmd_events,
        "auto": cmd_auto,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
