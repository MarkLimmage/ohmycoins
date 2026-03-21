#!/usr/bin/env python3
"""Production Acceptance Test — v1.3.1 Gap Detection (Phases 0+1)"""
import json, sys, re, time, subprocess
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode

HOST = "192.168.0.241"
BASE = "http://localhost:8001"
RESULTS = []

def api(method, path, data=None, token=None, follow=True):
    """Make API request, following redirects."""
    url = f"{BASE}{path}"
    headers = {"Host": HOST, "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    
    # Follow redirects manually for POST
    for _ in range(3):
        req = Request(url, data=body, headers=headers, method=method)
        try:
            resp = urlopen(req)
            return json.loads(resp.read().decode())
        except HTTPError as e:
            if e.code in (307, 308) and follow:
                loc = e.headers.get("Location", "")
                if loc.startswith("http"):
                    # Rewrite to localhost
                    from urllib.parse import urlparse
                    parsed = urlparse(loc)
                    url = f"{BASE}{parsed.path}"
                    if parsed.query:
                        url += f"?{parsed.query}"
                    continue
                url = f"{BASE}{loc}"
                continue
            body_text = e.read().decode() if e.fp else ""
            try:
                return json.loads(body_text)
            except:
                return {"error": e.code, "detail": body_text[:500]}
    return {"error": "too many redirects"}

def login(email, password):
    url = f"{BASE}/api/v1/login/access-token"
    data = urlencode({"username": email, "password": password}).encode()
    headers = {"Host": HOST, "Content-Type": "application/x-www-form-urlencoded"}
    req = Request(url, data=data, headers=headers, method="POST")
    resp = urlopen(req)
    return json.loads(resp.read().decode())["access_token"]

def log(tid, name, status, detail):
    RESULTS.append((tid, name, status, detail))
    icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️"}.get(status, "?")
    print(f"{icon} [{status}] {tid}: {name} — {detail}")

# ============================================================
# PHASE 0: SETUP
# ============================================================
print("=" * 60)
print("PHASE 0: SETUP")
print("=" * 60)

token = login("labtest@ohmycoins.com", "TestPass123!")
print(f"Token acquired: {token[:20]}...")

# Check OpenAPI for correct schema
print("\nDiscovering API schema...")
openapi = api("GET", "/openapi.json")
session_endpoints = {}
for path, methods in openapi.get("paths", {}).items():
    if "agent" in path and "session" in path.lower():
        for m in methods:
            session_endpoints[f"{m.upper()} {path}"] = methods[m]
            
print("Agent/Session endpoints:")
for ep in sorted(session_endpoints):
    print(f"  {ep}")

# Find create session schema
create_schema = None
for ep, spec in session_endpoints.items():
    if ep.startswith("POST") and "create" in json.dumps(spec).lower()[:500]:
        rb = spec.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
        ref = rb.get("$ref", "")
        if ref:
            schema_name = ref.split("/")[-1]
            create_schema = openapi.get("components", {}).get("schemas", {}).get(schema_name, {})
            print(f"  Create schema ({schema_name}): {json.dumps(create_schema, indent=2)}")

# Get baseline
baseline = api("GET", "/api/v1/lab/agent/sessions", token=token)
if isinstance(baseline, list):
    print(f"Baseline sessions: {len(baseline)}")
elif isinstance(baseline, dict):
    count = baseline.get("count", len(baseline.get("data", baseline.get("items", []))))
    print(f"Baseline sessions: {count}")

# ============================================================
# PHASE 1: API CONTRACT VALIDATION
# ============================================================
print("\n" + "=" * 60)
print("PHASE 1: API CONTRACT VALIDATION")
print("=" * 60)

# --- A1: Create session ---
print("\n--- 1.1 Session Lifecycle ---")
create_resp = api("POST", "/api/v1/lab/agent/sessions", 
                  data={"user_goal": "Analyze BTC price trends over the last 30 days and identify key support/resistance levels"},
                  token=token)
print(f"Create response: {json.dumps(create_resp)[:500]}")

session_id = create_resp.get("session_id") or create_resp.get("id")
if session_id:
    log("A1", "Create session", "PASS", f"session_id={session_id}")
else:
    log("A1", "Create session", "FAIL", f"No session_id: {json.dumps(create_resp)[:300]}")
    # Try to recover
    if create_resp.get("detail"):
        print(f"  Detail: {create_resp['detail']}")

if not session_id:
    print("\nFATAL: No session_id. Skipping remaining tests.")
    for tid, name in [("A2","List"), ("A3","Detail"), ("A4","Message"), ("A5","Rehydrate"), ("A6","Delete")]:
        log(tid, name, "SKIP", "No session")
    # Print summary and exit
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    p = sum(1 for r in RESULTS if r[2]=="PASS")
    f = sum(1 for r in RESULTS if r[2]=="FAIL")
    s = sum(1 for r in RESULTS if r[2]=="SKIP")
    print(f"PASS={p} FAIL={f} SKIP={s} TOTAL={len(RESULTS)}")
    for r in RESULTS:
        print(f"  {r[2]:4s} {r[0]:4s} {r[1]}")
    sys.exit(1)

# --- A2: List sessions ---
list_resp = api("GET", "/api/v1/lab/agent/sessions", token=token)
sessions_list = list_resp if isinstance(list_resp, list) else list_resp.get("data", list_resp.get("items", []))
found = any(str(s.get("session_id", s.get("id"))) == str(session_id) for s in sessions_list)
if found:
    log("A2", "List sessions", "PASS", f"Session in list ({len(sessions_list)} total)")
else:
    log("A2", "List sessions", "FAIL", f"Session not in list. Got: {json.dumps(list_resp)[:300]}")

# --- A3: Get session detail ---
detail_resp = api("GET", f"/api/v1/lab/agent/sessions/{session_id}", token=token)
detail_sid = str(detail_resp.get("session_id", detail_resp.get("id", "")))
if detail_sid == str(session_id):
    session_status = detail_resp.get("status", "unknown")
    log("A3", "Get session detail", "PASS", f"status={session_status}")
else:
    log("A3", "Get session detail", "FAIL", f"{json.dumps(detail_resp)[:300]}")

# --- Wait for agent ---
print("\nWaiting 20s for agent processing (scope confirmation)...")
time.sleep(20)

# --- A5: Rehydrate ---
rehydrate_resp = api("GET", f"/api/v1/lab/agent/sessions/{session_id}/rehydrate", token=token)
ledger = rehydrate_resp.get("event_ledger", rehydrate_resp.get("events", []))
last_seq = rehydrate_resp.get("last_sequence_id", -1)

if isinstance(ledger, list) and len(ledger) > 0:
    log("A5", "Rehydrate", "PASS", f"{len(ledger)} events, last_seq={last_seq}")
else:
    log("A5", "Rehydrate", "FAIL", f"Events={len(ledger) if isinstance(ledger, list) else 'N/A'}, resp={json.dumps(rehydrate_resp)[:300]}")

# --- A4: Send user message ---
msg_resp = api("POST", f"/api/v1/lab/agent/sessions/{session_id}/messages",
               data={"content": "Also analyze ETH if possible"},
               token=token)
msg_seq = msg_resp.get("sequence_id", -1)
if msg_seq and msg_seq != -1:
    log("A4", "Send user message", "PASS", f"sequence_id={msg_seq}")
else:
    log("A4", "Send user message", "FAIL", f"{json.dumps(msg_resp)[:300]}")

# Wait for message processing
time.sleep(5)

# --- 1.2 Event Ledger Contract ---
print("\n--- 1.2 Event Ledger Contract ---")

# Re-rehydrate for full ledger
full_resp = api("GET", f"/api/v1/lab/agent/sessions/{session_id}/rehydrate", token=token)
ledger = full_resp.get("event_ledger", full_resp.get("events", []))

if not isinstance(ledger, list) or len(ledger) == 0:
    print(f"WARNING: Empty ledger. Full response: {json.dumps(full_resp)[:500]}")
    for tid in ["B1","B2","B3","B4","B5","B6","B7","B8","B9","B10","C1","C2","C6","C7"]:
        log(tid, f"(skipped)", "SKIP", "Empty ledger")
else:
    VALID_TYPES = {"stream_chat","status_update","render_output","error","action_request","user_message","plan_established"}
    VALID_STAGES = {"BUSINESS_UNDERSTANDING","DATA_ACQUISITION","PREPARATION","EXPLORATION","MODELING","EVALUATION","DEPLOYMENT", None, ""}
    VALID_ACTION_IDS = {"scope_confirmation_v1","approve_modeling_v1","model_selection_v1","circuit_breaker_v1"}

    # Helper to get nested payload
    def get_payload(event):
        p = event.get("payload", event)
        if isinstance(p, dict) and "data" in p and isinstance(p["data"], dict):
            return p["data"]
        return p

    # Detect circuit-breaker path (E1: no working LLM)
    cb_path = any(get_payload(e).get("action_id") == "circuit_breaker_v1" for e in ledger if e.get("event_type") == "action_request")

    # B1: Sequence monotonicity
    seq_ids = [e.get("sequence_id") for e in ledger if e.get("sequence_id") is not None]
    if len(seq_ids) > 1:
        gaps = [(seq_ids[i], seq_ids[i+1]) for i in range(len(seq_ids)-1) if seq_ids[i+1] != seq_ids[i]+1]
        if not gaps:
            log("B1", "Sequence monotonicity", "PASS", f"{len(seq_ids)} events, {seq_ids[0]}-{seq_ids[-1]}")
        else:
            log("B1", "Sequence monotonicity", "FAIL", f"Gaps: {gaps[:5]}")
    elif len(seq_ids) == 1:
        log("B1", "Sequence monotonicity", "PASS", f"1 event at seq={seq_ids[0]}")
    else:
        log("B1", "Sequence monotonicity", "FAIL", "No sequence_ids")

    # B2: Event types
    type_counts = {}
    bad_types = set()
    for e in ledger:
        et = e.get("event_type", "")
        type_counts[et] = type_counts.get(et, 0) + 1
        if et not in VALID_TYPES:
            bad_types.add(et)
    if not bad_types:
        log("B2", "Event type routing", "PASS", str(type_counts))
    else:
        log("B2", "Event type routing", "FAIL", f"Unknown: {bad_types}")

    # B3: plan_established present
    plans = [e for e in ledger if e.get("event_type") == "plan_established"]
    if plans:
        log("B3", "plan_established present", "PASS", f"{len(plans)} plan(s)")
    elif cb_path:
        log("B3", "plan_established present", "SKIP", "E1 circuit-breaker path — LLM failed, no plan expected")
    else:
        log("B3", "plan_established present", "FAIL", "No plan_established event")

    # B4: plan_established structure
    plan_task_ids = set()
    if plans:
        p = get_payload(plans[0])
        plan_data = p.get("plan", [])
        if isinstance(plan_data, list) and plan_data:
            for stage in plan_data:
                for t in stage.get("tasks", []):
                    if t.get("task_id"):
                        plan_task_ids.add(t["task_id"])
            if plan_task_ids:
                log("B4", "plan_established structure", "PASS", f"{len(plan_data)} stages, task_ids={sorted(plan_task_ids)}")
            else:
                log("B4", "plan_established structure", "FAIL", f"No task_ids. Plan: {json.dumps(plan_data)[:300]}")
        else:
            log("B4", "plan_established structure", "FAIL", f"Not a list: {json.dumps(p)[:300]}")
    else:
        log("B4", "plan_established structure", "SKIP", "No plan")

    # B5: status_update has task_id (init events before plan are exempt)
    status_updates = [e for e in ledger if e.get("event_type") == "status_update"]
    if status_updates:
        missing = []
        for su in status_updates:
            p = get_payload(su)
            tid = p.get("task_id")
            if not tid:
                missing.append(su.get("sequence_id", "?"))
        if not missing:
            log("B5", "status_update has task_id", "PASS", f"All {len(status_updates)} have task_id")
        elif cb_path:
            log("B5", "status_update has task_id", "SKIP", f"E1 circuit-breaker path — {len(missing)} init events without task_id (expected)")
        else:
            log("B5", "status_update has task_id", "FAIL", f"{len(missing)} missing at seq: {missing[:10]}")
    else:
        log("B5", "status_update has task_id", "SKIP", "No status_update events")

    # B6: task_id matches plan
    if plan_task_ids and status_updates:
        orphans = []
        for su in status_updates:
            p = get_payload(su)
            tid = p.get("task_id", "")
            if tid and tid not in plan_task_ids:
                orphans.append(f"{tid}@seq{su.get('sequence_id','?')}")
        if not orphans:
            log("B6", "task_id matches plan", "PASS", f"All in plan")
        else:
            log("B6", "task_id matches plan", "FAIL", f"Orphans: {orphans[:10]}")
    else:
        log("B6", "task_id matches plan", "SKIP", "Missing plan or updates")

    # B7: action_request subtypes
    action_reqs = [e for e in ledger if e.get("event_type") == "action_request"]
    if action_reqs:
        aids = []
        bad_aids = []
        for ar in action_reqs:
            p = get_payload(ar)
            aid = p.get("action_id", "")
            aids.append(aid)
            if aid and aid not in VALID_ACTION_IDS:
                bad_aids.append(aid)
        if not bad_aids:
            log("B7", "action_request subtypes", "PASS", f"action_ids={aids}")
        else:
            log("B7", "action_request subtypes", "FAIL", f"Unknown: {bad_aids}")
    else:
        log("B7", "action_request subtypes", "SKIP", "No action_requests")

    # B8: No silent fallback
    fallbacks = []
    for e in ledger:
        if e.get("event_type") == "stream_chat":
            p = get_payload(e)
            text = str(p.get("text_delta", p.get("content", "")))
            if "fallback due to error" in text.lower():
                fallbacks.append(e.get("sequence_id", "?"))
    if not fallbacks:
        log("B8", "No silent fallback", "PASS", "No fallback messages")
    else:
        log("B8", "No silent fallback", "FAIL", f"Fallback at seq: {fallbacks}")

    # B9: stage field valid
    bad_stages = []
    for e in ledger:
        stage = e.get("stage", "")
        if stage and stage not in VALID_STAGES:
            bad_stages.append(f"{stage}@seq{e.get('sequence_id','?')}")
    if not bad_stages:
        log("B9", "stage field valid", "PASS", "All valid")
    else:
        log("B9", "stage field valid", "FAIL", f"Invalid: {bad_stages[:10]}")

    # B10: Timestamps
    bad_ts = []
    for e in ledger:
        ts = e.get("timestamp", "")
        if ts:
            try:
                datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except:
                bad_ts.append(ts)
    if not bad_ts:
        log("B10", "Timestamps ISO-8601", "PASS", "All valid")
    else:
        log("B10", "Timestamps ISO-8601", "FAIL", f"Bad: {bad_ts[:5]}")

    # --- 1.3 Interrupt Topology ---
    print("\n--- 1.3 Interrupt Topology ---")

    scope_confs = [e for e in ledger if e.get("event_type") == "action_request" and get_payload(e).get("action_id") == "scope_confirmation_v1"]
    cb_events = [e for e in ledger if e.get("event_type") == "action_request" and get_payload(e).get("action_id") == "circuit_breaker_v1"]

    # C1: Scope confirmation fires
    if scope_confs:
        log("C1", "Scope confirmation fires", "PASS", f"{len(scope_confs)} scope_confirmation_v1")
    elif cb_events:
        log("C1", "Scope confirmation fires", "PASS", "LLM fail → circuit_breaker_v1 (E1 path)")
    else:
        all_aids = [get_payload(e).get("action_id","?") for e in action_reqs]
        log("C1", "Scope confirmation fires", "FAIL", f"No scope/CB. action_ids={all_aids}")

    # C2: Structure check
    if scope_confs:
        p = get_payload(scope_confs[0])
        has_i = "interpretation" in json.dumps(p)
        has_o = "options" in json.dumps(p)
        if has_i and has_o:
            log("C2", "Scope confirmation structure", "PASS", "Has interpretation + options")
        else:
            log("C2", "Scope confirmation structure", "FAIL", f"interp={has_i} opts={has_o}: {json.dumps(p)[:200]}")
    elif cb_events:
        p = get_payload(cb_events[0])
        has_s = "suggestion" in json.dumps(p).lower()
        has_o = "options" in json.dumps(p)
        st = "PASS" if has_o else "FAIL"
        log("C2", "Circuit breaker structure", st, f"suggestions={has_s} options={has_o}: {json.dumps(p)[:200]}")
    else:
        log("C2", "Scope/CB structure", "SKIP", "No events")

    # C6: No generic approve_ overwrite
    generic = [e for e in action_reqs if re.match(r"^approve_\w+$", get_payload(e).get("action_id", ""))]
    if generic:
        gen_aids = [get_payload(e).get("action_id") for e in generic]
        log("C6", "No generic approve_ overwrite", "FAIL", f"Generic: {gen_aids}")
    else:
        log("C6", "No generic approve_ overwrite", "PASS", "No generic approve_ events")

    # C7: Circuit breaker on LLM fail
    if cb_events:
        log("C7", "Circuit breaker on LLM fail", "PASS", "circuit_breaker_v1 fired")
    elif scope_confs:
        log("C7", "Circuit breaker on LLM fail", "SKIP", "LLM succeeded")
    else:
        log("C7", "Circuit breaker on LLM fail", "FAIL", "Neither scope nor CB")

# --- 1.4 POST /message ---
print("\n--- 1.4 POST /message ---")

if msg_seq and msg_seq != -1:
    log("D1", "Returns sequence_id", "PASS", f"seq={msg_seq}")
    
    # D2: Check in ledger
    user_msgs = [e for e in ledger if e.get("event_type") == "user_message"]
    if user_msgs:
        log("D2", "User message in ledger", "PASS", f"{len(user_msgs)} user_message(s)")
    else:
        log("D2", "User message in ledger", "FAIL", "No user_message in ledger")
    
    # D3: Agent response at N+1
    if user_msgs and len(ledger) > 0:
        um_seqs = [e.get("sequence_id") for e in user_msgs if e.get("sequence_id")]
        next_events = []
        for s in um_seqs:
            nxt = [e for e in ledger if e.get("sequence_id") == s + 1]
            if nxt:
                next_events.append(nxt[0].get("event_type","?"))
        if next_events:
            log("D3", "Agent response at N+1", "PASS", f"Next events: {next_events}")
        else:
            log("D3", "Agent response at N+1", "SKIP", "Agent hasn't responded yet")
    else:
        log("D3", "Agent response at N+1", "SKIP", "No user messages")
else:
    log("D1", "Returns sequence_id", "FAIL", f"msg_resp={json.dumps(msg_resp)[:200]}")
    log("D2", "User message in ledger", "SKIP", "No message")
    log("D3", "Agent response at N+1", "SKIP", "No message")

# --- A6: Delete (throwaway session) ---
print("\n--- Delete test ---")
del_resp = api("POST", "/api/v1/lab/agent/sessions",
               data={"user_goal": "Throwaway for delete test"},
               token=token)
del_sid = del_resp.get("session_id") or del_resp.get("id")
if del_sid:
    time.sleep(2)
    del_result = api("DELETE", f"/api/v1/lab/agent/sessions/{del_sid}", token=token)
    if del_result.get("error") and del_result["error"] != 200:
        log("A6", "Delete session", "FAIL", f"{json.dumps(del_result)[:200]}")
    else:
        log("A6", "Delete session", "PASS", f"Deleted {del_sid}")
else:
    log("A6", "Delete session", "FAIL", f"Couldn't create: {json.dumps(del_resp)[:200]}")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("PHASE 0+1 TEST SUMMARY")
print("=" * 60)
p = sum(1 for r in RESULTS if r[2]=="PASS")
f = sum(1 for r in RESULTS if r[2]=="FAIL")
s = sum(1 for r in RESULTS if r[2]=="SKIP")
print(f"  PASS: {p}")
print(f"  FAIL: {f}")
print(f"  SKIP: {s}")
print(f"  TOTAL: {len(RESULTS)}")
print("=" * 60)
print(f"\n{'ID':<6} {'Status':<6} {'Test':<35} {'Detail'}")
print("-" * 100)
for r in RESULTS:
    icon = {"PASS":"✅","FAIL":"❌","SKIP":"⏭️"}.get(r[2],"?")
    print(f"{r[0]:<6} {icon}{r[2]:<5} {r[1]:<35} {r[3][:80]}")

print(f"\nTest session: {session_id}")

# Dump raw ledger for debugging
print("\n--- RAW LEDGER (first 10 events) ---")
for e in ledger[:10]:
    p = e.get("payload", {})
    print(f"  seq={e.get('sequence_id','?'):>4} type={e.get('event_type','?'):<20} stage={e.get('stage','?'):<25} payload_keys={list(p.keys()) if isinstance(p,dict) else '?'}")

if len(ledger) > 10:
    print(f"  ... and {len(ledger)-10} more events")

# Exit code
sys.exit(1 if f > 0 else 0)
