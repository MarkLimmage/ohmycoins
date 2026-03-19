# ⚙️ DevOps Protocol: Parallel Agentic Orchestration

**Version:** 1.3 (Updated: v1.3 Conversational Scientific Grid)
**Classification:** EYES ONLY (Supervisor Agent)
**Context:** This protocol dictates the Git Worktree topology, resource allocation, and worker-delegation strategy required to build "The Lab" in parallel without integration conflicts or context degradation.

---

## 1. 🌳 The Worktree Topology

To enable simultaneous execution without git stash/checkout conflicts, the Supervisor **shall** initialize the following isolated environments from the root repository.

| Worker Persona | Branch Name | Target Directory | Responsibility |
| --- | --- | --- | --- |
| **Graph Agent** | `feature/langgraph-orchestrator` | `../omc-lab-graph` | LangGraph state machine (`LangGraphWorkflow`), EventLedger, 4 interrupts, mandatory scope confirmation, POST /message, circuit breaker escalation, FastAPI WebSocket + rehydration. |
| **Glass Agent** | `feature/react-frontend` | `../omc-lab-ui` | React + Tailwind CSS 3-column Scientific Grid, event router, HITL cards, ChatInput, useRehydration hook, Activity Tracker. |

> **Note:** The Engine Agent is not active in this sprint. Dagger/MLflow work was completed in prior phases.

---

## 2. 🚦 Resource Isolation Matrix

### 2.1 Port Allocations (Per-Worktree Docker Isolation)

Each worktree runs its own Docker Compose stack with isolated ports via `docker-compose.override.yml`.

| Service | Graph Agent (`../omc-lab-graph`) | Glass Agent (`../omc-lab-ui`) | Supervisor (main) |
| --- | --- | --- | --- |
| **Proxy** | `8020` | `8030` | `8080` |
| **Postgres** | `5434` | `5435` | `5432` |
| **Redis** | shared | shared | `6379` |
| **Mock WS** | — | `8002` | `8002` |
| **Vite Dev** | — | `5173` | — |

### 2.2 Docker Project Isolation

Each worktree's `.env` sets `COMPOSE_PROJECT_NAME` to prevent container name collisions:

* Graph: `COMPOSE_PROJECT_NAME=omc-lab-graph`
* Glass: `COMPOSE_PROJECT_NAME=omc-lab-ui`

---

## 3. 🏁 Initialization Sequence (Phase 0)

Before assigning tasks to the worker agents, the Supervisor **must** complete:

1. **Verify Contracts:** Ensure root `API_CONTRACTS.md` v1.3 is finalized — the canonical schema with 7 event types, 4 interrupts, POST /message, and mandatory scope confirmation.
2. **Generate Mock Server:** `mock_ws_v13.py` on Port `8002` broadcasts the exact v1.3 JSON schemas with monotonic `sequence_id` and ISO-8601 `timestamp`.
3. **Initialize Worktrees:** Execute the Scorched Earth provisioning (nuke old worktrees, create fresh branches, seed contracts).
4. **Seed Environments:** Copy `API_CONTRACTS.md`, `REQUIREMENTS.md`, `ROADMAP_STRATEGY.md` into each worktree root.
5. **Write WORKER_MISSION.md:** Place hardened, role-specific mission files in each worktree.

---

## 4. 🧠 Worker Delegation & "The Context Diet"

Worker agents suffer from hallucination when exposed to out-of-scope system architecture. The Supervisor **shall strictly limit** the context passed to each worker.

### 4.1 Delegation Rules

* **Never** pass this `DEVOPS_PROTOCOL.md` to a worker agent.
* **Never** pass the entire `ROADMAP_STRATEGY.md` to a worker agent.
* **Always** pass the `API_CONTRACTS.md` v1.3 to every worker agent.
* **Always** seed a `WORKER_MISSION.md` with explicit task list and role boundaries.

### 4.2 Current Sprint Prompting Templates (v1.3.1 — Sprint 2.52)

**For the Graph Agent (Workstream F — 6 enforcement fixes):**

> "You are the Graph Agent. You are the sole developer here. Ignore legacy docs. Read WORKER_MISSION.md for your task list (F1-F6): Scope confirmation fallback → circuit_breaker_v1, runner publishes node pending_events instead of generic interrupt, add task_id to ALL status_update payloads, emit plan_established on error/fallback paths, deduplicate runner vs node action_request, fix stage progression in status_updates. Strictly follow API_CONTRACTS.md v1.3.1 §0.1 Enforcement Rules. If a contract is impossible, write a CONTRACT_RFC.md and halt."

**For the Glass Agent (Workstream G — 8 enforcement fixes):**

> "You are the Glass Agent. You are the sole developer here. Ignore legacy docs. Read WORKER_MISSION.md for your task list (G1-G8): sequence_id deduplication, inline action_request HITL cards per subtype, remove legacy Resume button, fix pipeline colors (green/blue/gray), enable ChatInput during RUNNING/AWAITING_APPROVAL, Stage Outputs driven by selection, rehydration/WS after_seq overlap fix, differentiate message senders. Strictly follow API_CONTRACTS.md v1.3.1 §0.1. If a contract is impossible, write a CONTRACT_RFC.md and halt."

---

## 5. 🛑 The RFC (Request for Comments) Protocol

### 5.1 Worker Submission

If a worker encounters a blocker, it must generate `CONTRACT_RFC.md` in its root directory:

```markdown
### 🚨 Contract Exception Request
**Violated Schema:** (e.g., `render_output` payload)
**Technical Blocker:** (Explanation of why the current contract fails)
**Proposed Change:** (The exact JSON schema adjustment required)
```

### 5.2 Supervisor Resolution

1. Evaluate the proposed change.
2. **If Approved:** Update master `API_CONTRACTS.md`, update `mock_ws_v13.py`, push updated contracts to all worktrees, instruct worker to delete RFC and resume.
3. **If Rejected:** Provide alternative approach and instruct retry.

---

## 6. 🚨 Emergency Fallback Procedures

* **Unapproved Violation:** Supervisor rejects commit, wipes changes (`git reset --hard`), reprompts with specific contract violation.
* **Infinite Loop Breaker:** After 3 consecutive resets for the same issue, force worker to generate `CONTRACT_RFC.md`.
* **Merge Conflicts:** Halt integration, isolate conflicting files, resolve scaffolding via `git checkout --ours`, then retry.

---

## 7. 🔗 Integration Sequence

Merge order: **Graph → Main**, then **Glass → Main**.

1. Pre-merge: Verify clean working trees in each worktree.
2. Scaffolding conflicts (WORKER_MISSION.md, CLAUDE.md): Resolve with `git checkout --ours`.
3. Post-merge: Run `scripts/lint.sh` and test suite.
4. On failure: Execute Integration Failure Protocol (revert, capture logs, write INTEGRATION_FAILURE.md, delegate to worker).
