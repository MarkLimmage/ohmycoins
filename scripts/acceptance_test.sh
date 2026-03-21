#!/bin/bash
# =============================================================================
# Production Acceptance Test — v1.3.1 Gap Detection
# Phase 0 (Setup) + Phase 1 (API Contract Validation)
# Run ON the production server via SSH
# =============================================================================
set -euo pipefail

HOST="192.168.0.241"
BASE="http://localhost:8001"
H=(-H "Host: $HOST")
PASS=0
FAIL=0
SKIP=0
RESULTS=""

log_result() {
    local id="$1" name="$2" status="$3" detail="$4"
    if [ "$status" = "PASS" ]; then ((PASS++)); fi
    if [ "$status" = "FAIL" ]; then ((FAIL++)); fi
    if [ "$status" = "SKIP" ]; then ((SKIP++)); fi
    RESULTS+="| $id | $name | **$status** | $detail |\n"
    echo "[$status] $id: $name — $detail"
}

# --- Phase 0: Auth ---
echo "========== PHASE 0: SETUP =========="
TOKEN=$(curl -s -X POST "$BASE/api/v1/login/access-token" \
    "${H[@]}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=labtest@ohmycoins.com&password=TestPass123!" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

AUTH=(-H "Authorization: Bearer $TOKEN")
echo "Token acquired for labtest@ohmycoins.com"

# Helper: API call
api() {
    local method="$1" path="$2" data="${3:-}"
    if [ -n "$data" ]; then
        curl -s -X "$method" "$BASE$path" "${H[@]}" "${AUTH[@]}" \
            -H "Content-Type: application/json" -d "$data" 2>/dev/null
    else
        curl -s -X "$method" "$BASE$path" "${H[@]}" "${AUTH[@]}" 2>/dev/null
    fi
}

# Baseline
echo "=== 0.3: Baseline sessions ==="
BASELINE=$(api GET "/api/v1/lab/agent/sessions/")
BASELINE_COUNT=$(echo "$BASELINE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('count', len(d)) if isinstance(d, dict) else len(d))" 2>/dev/null || echo "0")
echo "Baseline sessions: $BASELINE_COUNT"

# ========== PHASE 1: API CONTRACT VALIDATION ==========
echo ""
echo "========== PHASE 1: API CONTRACT VALIDATION =========="

# --- 1.1 Session Lifecycle ---
echo ""
echo "--- 1.1 Session Lifecycle ---"

# A1: Create session
echo "Creating session..."
CREATE_RESP=$(api POST "/api/v1/lab/agent/sessions/" '{"goal":"Analyze BTC price trends over the last 30 days and identify key support/resistance levels"}')
echo "Create response: $CREATE_RESP" | head -c 500
SESSION_ID=$(echo "$CREATE_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id', d.get('id', '')))" 2>/dev/null || echo "")

if [ -n "$SESSION_ID" ] && [ "$SESSION_ID" != "" ] && [ "$SESSION_ID" != "None" ]; then
    log_result "A1" "Create session" "PASS" "session_id=$SESSION_ID"
else
    SESSION_ID=""
    log_result "A1" "Create session" "FAIL" "No session_id returned: $(echo "$CREATE_RESP" | head -c 200)"
fi

# If session creation failed, try to find the endpoint
if [ -z "$SESSION_ID" ]; then
    echo "Trying alternate endpoints..."
    # Check available routes
    ROUTES=$(curl -s "$BASE/api/v1/lab/" "${H[@]}" "${AUTH[@]}" 2>/dev/null | head -c 500)
    echo "Lab routes: $ROUTES"
    ROUTES2=$(curl -s "$BASE/api/v1/agent/sessions/" "${H[@]}" "${AUTH[@]}" 2>/dev/null | head -c 500)
    echo "Agent sessions routes: $ROUTES2"
    # Try /openapi.json for correct paths
    OPENAPI_PATHS=$(curl -s "$BASE/openapi.json" "${H[@]}" 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
for p in sorted(d.get('paths',{}).keys()):
    if 'agent' in p.lower() or 'lab' in p.lower() or 'session' in p.lower():
        methods = ','.join(d['paths'][p].keys())
        print(f'{methods:12s} {p}')
" 2>/dev/null || echo "Could not parse openapi.json")
    echo "Relevant API paths:"
    echo "$OPENAPI_PATHS"
fi

if [ -z "$SESSION_ID" ]; then
    echo "FATAL: Cannot proceed without session_id. Remaining tests will be skipped."
    log_result "A2" "List sessions" "SKIP" "No session"
    log_result "A3" "Get session detail" "SKIP" "No session"
    log_result "A4" "Send user message" "SKIP" "No session"
    log_result "A5" "Rehydrate" "SKIP" "No session"
    log_result "A6" "Delete session" "SKIP" "No session"
else
    # A2: List sessions
    LIST_RESP=$(api GET "/api/v1/lab/agent/sessions/")
    HAS_SESSION=$(echo "$LIST_RESP" | python3 -c "
import sys,json
d=json.load(sys.stdin)
items = d.get('data', d) if isinstance(d, dict) else d
found = any(str(s.get('session_id', s.get('id',''))) == '$SESSION_ID' for s in (items if isinstance(items, list) else []))
print('yes' if found else 'no')
" 2>/dev/null || echo "error")
    if [ "$HAS_SESSION" = "yes" ]; then
        log_result "A2" "List sessions" "PASS" "Session found in list"
    else
        log_result "A2" "List sessions" "FAIL" "Session not in list: $(echo "$LIST_RESP" | head -c 200)"
    fi

    # A3: Get session detail
    DETAIL_RESP=$(api GET "/api/v1/lab/agent/sessions/$SESSION_ID")
    HAS_DETAIL=$(echo "$DETAIL_RESP" | python3 -c "
import sys,json
d=json.load(sys.stdin)
sid = d.get('session_id', d.get('id',''))
print('yes' if str(sid) == '$SESSION_ID' else 'no')
" 2>/dev/null || echo "error")
    if [ "$HAS_DETAIL" = "yes" ]; then
        SESSION_STATUS=$(echo "$DETAIL_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null)
        log_result "A3" "Get session detail" "PASS" "status=$SESSION_STATUS"
    else
        log_result "A3" "Get session detail" "FAIL" "$(echo "$DETAIL_RESP" | head -c 200)"
    fi

    # Wait for agent to process (scope confirmation takes a few seconds)
    echo "Waiting 15s for agent processing..."
    sleep 15

    # A5: Rehydrate (do this before A4 to capture scope confirmation events)
    REHYDRATE_RESP=$(api GET "/api/v1/lab/agent/sessions/$SESSION_ID/rehydrate")
    REHYDRATE_OK=$(echo "$REHYDRATE_RESP" | python3 -c "
import sys,json
d=json.load(sys.stdin)
ledger = d.get('event_ledger', d.get('events', []))
last_seq = d.get('last_sequence_id', -1)
print(f'yes|{len(ledger)}|{last_seq}')
" 2>/dev/null || echo "no|0|0")
    IFS='|' read -r ROK RCOUNT RLAST <<< "$REHYDRATE_OK"
    if [ "$ROK" = "yes" ] && [ "$RCOUNT" -gt 0 ]; then
        log_result "A5" "Rehydrate" "PASS" "$RCOUNT events, last_seq=$RLAST"
    elif [ "$ROK" = "yes" ]; then
        log_result "A5" "Rehydrate" "FAIL" "0 events returned (agent may not have started)"
    else
        log_result "A5" "Rehydrate" "FAIL" "$(echo "$REHYDRATE_RESP" | head -c 300)"
    fi

    # A4: Send user message (only if session is in a state that accepts messages)
    MSG_RESP=$(api POST "/api/v1/lab/agent/sessions/$SESSION_ID/message" '{"content":"Focus on ETH as well"}')
    MSG_SEQ=$(echo "$MSG_RESP" | python3 -c "
import sys,json
d=json.load(sys.stdin)
seq = d.get('sequence_id', -1)
print(seq)
" 2>/dev/null || echo "-1")
    if [ "$MSG_SEQ" != "-1" ] && [ "$MSG_SEQ" != "" ]; then
        log_result "A4" "Send user message" "PASS" "sequence_id=$MSG_SEQ"
    else
        log_result "A4" "Send user message" "FAIL" "$(echo "$MSG_RESP" | head -c 300)"
    fi

    # ========== 1.2 Event Ledger Contract ==========
    echo ""
    echo "--- 1.2 Event Ledger Contract ---"
    
    # Wait a bit more for events after message
    sleep 5
    
    # Re-rehydrate to get full ledger including message
    FULL_LEDGER=$(api GET "/api/v1/lab/agent/sessions/$SESSION_ID/rehydrate")
    
    # Run comprehensive validation
    echo "$FULL_LEDGER" | python3 -c "
import sys, json, re
from datetime import datetime

d = json.load(sys.stdin)
ledger = d.get('event_ledger', d.get('events', []))
last_seq = d.get('last_sequence_id', -1)

VALID_TYPES = {'stream_chat','status_update','render_output','error','action_request','user_message','plan_established'}
VALID_STAGES = {'BUSINESS_UNDERSTANDING','DATA_ACQUISITION','PREPARATION','EXPLORATION','MODELING','EVALUATION','DEPLOYMENT', None, ''}
VALID_ACTION_IDS = {'scope_confirmation_v1','approve_modeling_v1','model_selection_v1','circuit_breaker_v1'}
results = []

# B1: Sequence monotonicity
seq_ids = [e.get('sequence_id') for e in ledger if e.get('sequence_id') is not None]
mono_ok = all(seq_ids[i+1] == seq_ids[i]+1 for i in range(len(seq_ids)-1)) if len(seq_ids) > 1 else True
gaps = []
for i in range(len(seq_ids)-1):
    if seq_ids[i+1] != seq_ids[i]+1:
        gaps.append(f'{seq_ids[i]}->{seq_ids[i+1]}')
if mono_ok and len(seq_ids) > 0:
    results.append(('B1','Sequence monotonicity','PASS',f'{len(seq_ids)} events, range {seq_ids[0]}-{seq_ids[-1]}'))
elif len(seq_ids) == 0:
    results.append(('B1','Sequence monotonicity','FAIL','No sequence_ids found'))
else:
    results.append(('B1','Sequence monotonicity','FAIL',f'Gaps: {gaps[:5]}'))

# B2: Event type routing
bad_types = set()
for e in ledger:
    et = e.get('event_type','')
    if et not in VALID_TYPES:
        bad_types.add(et)
if not bad_types:
    type_counts = {}
    for e in ledger:
        et = e.get('event_type','')
        type_counts[et] = type_counts.get(et, 0) + 1
    results.append(('B2','Event type routing','PASS', str(type_counts)))
else:
    results.append(('B2','Event type routing','FAIL',f'Unknown types: {bad_types}'))

# B3: plan_established present
plans = [e for e in ledger if e.get('event_type') == 'plan_established']
if plans:
    results.append(('B3','plan_established present','PASS',f'{len(plans)} plan(s) found'))
else:
    results.append(('B3','plan_established present','FAIL','No plan_established event in ledger'))

# B4: plan_established structure
if plans:
    p = plans[0].get('payload', plans[0])
    plan_data = p.get('plan', p.get('data', {}).get('plan', []))
    if isinstance(plan_data, list) and len(plan_data) > 0:
        all_have_stage = all('stage' in s for s in plan_data)
        all_have_tasks = all('tasks' in s for s in plan_data)
        task_ids = []
        for stage in plan_data:
            for t in stage.get('tasks', []):
                tid = t.get('task_id', '')
                if tid: task_ids.append(tid)
        if all_have_stage and all_have_tasks and task_ids:
            results.append(('B4','plan_established structure','PASS',f'{len(plan_data)} stages, {len(task_ids)} tasks: {task_ids[:5]}'))
        else:
            results.append(('B4','plan_established structure','FAIL',f'Missing stage/tasks: stages={all_have_stage} tasks={all_have_tasks} ids={len(task_ids)}'))
    else:
        results.append(('B4','plan_established structure','FAIL',f'plan is not a list or empty: {type(plan_data)}'))
else:
    results.append(('B4','plan_established structure','SKIP','No plan_established'))

# B5: status_update has task_id
status_updates = [e for e in ledger if e.get('event_type') == 'status_update']
missing_tid = []
for su in status_updates:
    payload = su.get('payload', su)
    tid = payload.get('task_id', payload.get('data', {}).get('task_id'))
    if not tid:
        missing_tid.append(su.get('sequence_id', '?'))
if status_updates and not missing_tid:
    results.append(('B5','status_update has task_id','PASS',f'All {len(status_updates)} have task_id'))
elif not status_updates:
    results.append(('B5','status_update has task_id','SKIP','No status_update events yet'))
else:
    results.append(('B5','status_update has task_id','FAIL',f'{len(missing_tid)} missing at seq_ids: {missing_tid[:10]}'))

# B6: task_id matches plan
if plans and status_updates:
    p = plans[0].get('payload', plans[0])
    plan_data = p.get('plan', p.get('data', {}).get('plan', []))
    plan_task_ids = set()
    for stage in (plan_data if isinstance(plan_data, list) else []):
        for t in stage.get('tasks', []):
            plan_task_ids.add(t.get('task_id', ''))
    orphans = []
    for su in status_updates:
        payload = su.get('payload', su)
        tid = payload.get('task_id', payload.get('data', {}).get('task_id', ''))
        if tid and tid not in plan_task_ids:
            orphans.append(f'{tid}@seq{su.get(\"sequence_id\",\"?\")}')
    if not orphans:
        results.append(('B6','task_id matches plan','PASS',f'All task_ids in plan. Plan IDs: {plan_task_ids}'))
    else:
        results.append(('B6','task_id matches plan','FAIL',f'Orphan task_ids: {orphans[:10]}'))
else:
    results.append(('B6','task_id matches plan','SKIP','Missing plan or status_updates'))

# B7: action_request subtypes
action_reqs = [e for e in ledger if e.get('event_type') == 'action_request']
bad_actions = []
for ar in action_reqs:
    payload = ar.get('payload', ar)
    aid = payload.get('action_id', payload.get('data', {}).get('action_id', ''))
    if aid and aid not in VALID_ACTION_IDS and not aid.startswith('approve_'):
        bad_actions.append(aid)
if action_reqs and not bad_actions:
    aids = [ar.get('payload', ar).get('action_id', ar.get('data',{}).get('action_id','?')) for ar in action_reqs]
    results.append(('B7','action_request subtypes','PASS',f'action_ids: {aids}'))
elif not action_reqs:
    results.append(('B7','action_request subtypes','SKIP','No action_request events'))
else:
    results.append(('B7','action_request subtypes','FAIL',f'Unknown action_ids: {bad_actions}'))

# B8: No silent fallback
fallbacks = []
for e in ledger:
    if e.get('event_type') == 'stream_chat':
        payload = e.get('payload', e)
        text = str(payload.get('text_delta', payload.get('data', {}).get('text_delta', '')))
        if 'fallback due to error' in text.lower():
            fallbacks.append(e.get('sequence_id', '?'))
if not fallbacks:
    results.append(('B8','No silent fallback','PASS','No fallback messages found'))
else:
    results.append(('B8','No silent fallback','FAIL',f'Fallback at seq_ids: {fallbacks}'))

# B9: stage field valid
bad_stages = []
for e in ledger:
    stage = e.get('stage', '')
    if stage and stage not in VALID_STAGES:
        bad_stages.append(f'{stage}@seq{e.get(\"sequence_id\",\"?\")}')
if not bad_stages:
    results.append(('B9','stage field valid','PASS','All stages valid'))
else:
    results.append(('B9','stage field valid','FAIL',f'Invalid stages: {bad_stages[:10]}'))

# B10: Timestamps ISO-8601
bad_ts = []
for e in ledger:
    ts = e.get('timestamp', '')
    if ts:
        try:
            datetime.fromisoformat(ts.replace('Z', '+00:00'))
        except:
            bad_ts.append(f'{ts}@seq{e.get(\"sequence_id\",\"?\")}')
if not bad_ts:
    results.append(('B10','Timestamps ISO-8601','PASS','All timestamps valid'))
else:
    results.append(('B10','Timestamps ISO-8601','FAIL',f'Bad timestamps: {bad_ts[:5]}'))

# C1: Scope confirmation fires
scope_confs = [e for e in ledger if e.get('event_type') == 'action_request' and 
    (e.get('payload', e).get('action_id', e.get('data',{}).get('action_id','')) == 'scope_confirmation_v1' or
     e.get('payload', e).get('data',{}).get('action_id','') == 'scope_confirmation_v1')]
cb_events = [e for e in ledger if e.get('event_type') == 'action_request' and 
    (e.get('payload', e).get('action_id', e.get('data',{}).get('action_id','')) == 'circuit_breaker_v1' or
     e.get('payload', e).get('data',{}).get('action_id','') == 'circuit_breaker_v1')]
if scope_confs:
    results.append(('C1','Scope confirmation fires','PASS',f'Found {len(scope_confs)} scope_confirmation_v1'))
elif cb_events:
    results.append(('C1','Scope confirmation fires','PASS','LLM failed → circuit_breaker_v1 (E1 path)'))
else:
    results.append(('C1','Scope confirmation fires','FAIL','No scope_confirmation_v1 or circuit_breaker_v1'))

# C2: Scope confirmation structure (or circuit breaker structure)
if scope_confs:
    sc = scope_confs[0]
    p = sc.get('payload', sc)
    data = p.get('data', p) if isinstance(p, dict) else p
    has_interp = 'interpretation' in str(data)
    has_options = 'options' in str(data)
    if has_interp and has_options:
        results.append(('C2','Scope confirmation structure','PASS','Has interpretation + options'))
    else:
        results.append(('C2','Scope confirmation structure','FAIL',f'interp={has_interp} options={has_options}: {str(data)[:200]}'))
elif cb_events:
    cb = cb_events[0]
    p = cb.get('payload', cb)
    data = p.get('data', p) if isinstance(p, dict) else p
    has_suggestions = 'suggestions' in str(data) or 'suggestion' in str(data).lower()
    has_options = 'options' in str(data)
    results.append(('C2','Circuit breaker structure','PASS' if has_options else 'FAIL',
        f'suggestions={has_suggestions} options={has_options}: {str(data)[:200]}'))
else:
    results.append(('C2','Scope confirmation structure','SKIP','No scope/CB events'))

# C6: No generic approve_ overwrite
generic_approves = [e for e in ledger if e.get('event_type') == 'action_request' and 
    re.match(r'approve_\w+$', str(e.get('payload', e).get('action_id', e.get('data',{}).get('action_id',''))))]
structured_ids = {e.get('payload', e).get('action_id', e.get('data',{}).get('action_id','')) for e in action_reqs}
if generic_approves:
    gen_aids = [e.get('payload',e).get('action_id','') for e in generic_approves]
    results.append(('C6','No generic approve_ overwrite','FAIL',f'Generic approves found: {gen_aids}'))
else:
    results.append(('C6','No generic approve_ overwrite','PASS','No generic approve_ events'))

# C7: Circuit breaker on LLM fail
if cb_events:
    results.append(('C7','Circuit breaker on LLM fail','PASS','circuit_breaker_v1 fired'))
elif scope_confs:
    results.append(('C7','Circuit breaker on LLM fail','SKIP','LLM succeeded — scope_confirmation_v1 returned'))
else:
    results.append(('C7','Circuit breaker on LLM fail','FAIL','Neither scope_confirmation nor circuit_breaker'))

# Print results
print()
print('='*80)
for r in results:
    status_icon = '✅' if r[2]=='PASS' else ('❌' if r[2]=='FAIL' else '⏭️')
    print(f'{status_icon} [{r[2]}] {r[0]}: {r[1]} — {r[3]}')
print('='*80)
" 2>&1

    # D1-D3: POST /message contract
    echo ""
    echo "--- 1.4 POST /message Contract ---"
    if [ "$MSG_SEQ" != "-1" ] && [ "$MSG_SEQ" != "" ]; then
        log_result "D1" "Returns sequence_id" "PASS" "sequence_id=$MSG_SEQ"
        
        # D2: Check message in ledger
        LEDGER2=$(api GET "/api/v1/lab/agent/sessions/$SESSION_ID/rehydrate")
        D2_CHECK=$(echo "$LEDGER2" | python3 -c "
import sys,json
d=json.load(sys.stdin)
ledger=d.get('event_ledger',d.get('events',[]))
user_msgs=[e for e in ledger if e.get('event_type')=='user_message']
print(f'{len(user_msgs)} user_message events found')
for m in user_msgs:
    print(f'  seq={m.get(\"sequence_id\",\"?\")} payload={str(m.get(\"payload\",m))[:100]}')
" 2>/dev/null || echo "error")
        echo "D2: $D2_CHECK"
        if echo "$D2_CHECK" | grep -q "user_message events found" && ! echo "$D2_CHECK" | grep -q "^0 "; then
            log_result "D2" "User message in ledger" "PASS" "$D2_CHECK"
        else
            log_result "D2" "User message in ledger" "FAIL" "$D2_CHECK"
        fi
    else
        log_result "D1" "Returns sequence_id" "FAIL" "Message send failed"
        log_result "D2" "User message in ledger" "SKIP" "No message sent"
    fi

    # A6: Delete (create a throwaway session for this — don't delete our main test session)
    DEL_RESP=$(api POST "/api/v1/lab/agent/sessions/" '{"goal":"Throwaway session for delete test"}')
    DEL_SID=$(echo "$DEL_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id', d.get('id', '')))" 2>/dev/null || echo "")
    if [ -n "$DEL_SID" ] && [ "$DEL_SID" != "" ] && [ "$DEL_SID" != "None" ]; then
        sleep 2
        DEL_RESULT=$(api DELETE "/api/v1/lab/agent/sessions/$DEL_SID")
        DEL_CODE=$(echo "$DEL_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print('ok' if d.get('deleted') or d.get('message') or d.get('status') else 'fail')" 2>/dev/null || echo "fail")
        if [ "$DEL_CODE" = "ok" ]; then
            log_result "A6" "Delete session" "PASS" "Deleted $DEL_SID"
        else
            log_result "A6" "Delete session" "FAIL" "$(echo "$DEL_RESULT" | head -c 200)"
        fi
    else
        log_result "A6" "Delete session" "FAIL" "Could not create throwaway session"
    fi
fi

# ========== SUMMARY ==========
echo ""
echo "=========================================="
echo "  TEST SUMMARY"
echo "=========================================="
echo "  PASS: $PASS"
echo "  FAIL: $FAIL"  
echo "  SKIP: $SKIP"
echo "  TOTAL: $((PASS + FAIL + SKIP))"
echo "=========================================="
echo ""
echo "| ID | Test | Result | Detail |"
echo "|-----|------|--------|--------|"
echo -e "$RESULTS"
echo ""
echo "Test session ID: ${SESSION_ID:-NONE}"
echo "Done."
