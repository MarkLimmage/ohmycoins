# ⚙️ DevOps Protocol: Parallel Agentic Orchestration

**Version:** 1.1 (Updated: RFC Protocol Integration)
**Classification:** EYES ONLY (Supervisor Agent)
**Context:** This protocol dictates the Git Worktree topology, resource allocation, and worker-delegation strategy required to build "The Lab" in parallel without integration conflicts or context degradation.

---

## 1. 🌳 The Worktree Topology

To enable simultaneous execution without git stash/checkout conflicts, the Supervisor **shall** initialize the following isolated environments from the root repository (`/omc-lab-main`).

| Worker Persona | Branch Name | Target Directory | Responsibility |
| --- | --- | --- | --- |
| **Engine Agent** | `feature/dagger-engine` | `../omc-lab-engine` | Dagger sandbox, MV extraction, validation scripts. |
| **Graph Agent** | `feature/langgraph-orchestrator` | `../omc-lab-graph` | LangGraph state machine, FastAPI WebSocket router. |
| **Glass Agent** | `feature/vue-frontend` | `../omc-lab-ui` | Vue Flow, Multi-modal UI, REST API calls. |

**Command Specification:**

```bash
git worktree add ../omc-lab-engine feature/dagger-engine
git worktree add ../omc-lab-graph feature/langgraph-orchestrator
git worktree add ../omc-lab-ui feature/vue-frontend

```

---

## 2. 🚦 Resource Isolation Matrix

Parallel local development inevitably leads to port collisions and database locks if not strictly managed. The Supervisor **shall** enforce the following environmental boundaries on the workers:

### 2.1 Port Allocations

Under no circumstances shall a worker agent alter these port assignments dynamically.

* **Port `8000`:** Reserved exclusively for the Graph Agent (FastAPI Orchestrator).
* **Port `8002`:** Reserved exclusively for the Supervisor's Mock WebSocket Server.
* **Port `5173`:** Reserved exclusively for the Glass Agent (Vue Vite Server).
* **Port `5000`:** Reserved exclusively for the local MLflow Tracking Server.

### 2.2 Database Isolation

To prevent the Engine Agent from locking Postgres tables while the Graph Agent is testing state queries, the Supervisor **shall** instruct the workers to use separate logical databases or schemas via their `.env` files.

---

## 3. 🏁 Initialization Sequence (Phase 0)

Before assigning tasks to the worker agents, the Supervisor **must** complete the following setup sequence:

1. **Verify Contracts:** Ensure `API_CONTRACTS.md` is finalized and saved in the root directory.
2. **Generate Mock Server:** The Supervisor shall write a `mock_ws_server.py` script running on Port `8002` that broadcasts the exact JSON schemas defined in the Contracts.
3. **Initialize Worktrees:** Execute the Git CLI commands to spawn the isolated directories.
4. **Seed Environments:** Copy the `API_CONTRACTS.md` into the root of each spawned worktree.

---

## 4. 🧠 Worker Delegation & "The Context Diet"

Worker agents suffer from hallucination when exposed to out-of-scope system architecture. The Supervisor **shall strictly limit** the context passed to each worker.

### 4.1 Delegation Rules

* **Never** pass this `DEVOPS_PROTOCOL.md` to a worker agent.
* **Never** pass the entire `ROADMAP_STRATEGY.md` to a worker agent.
* **Always** pass the `API_CONTRACTS.md` to every worker agent.

### 4.2 Prompting Templates (with RFC Instructions)

When spinning up a worker, the Supervisor shall use the following prompt structures. Note the inclusion of the RFC escape hatch:

**For the Engine Agent:**

> "You are the Backend Engine Agent. Your isolated workspace is `../omc-lab-engine`. Your task is Phase 1 from the Roadmap. Build the Dagger execution sandbox and the MV-to-Parquet pipeline. Do not write any FastAPI routing or Vue.js code. Refer to `API_CONTRACTS.md` for tool schemas. *If a contract is technically impossible to implement, do not write unauthorized payloads. Instead, submit a `CONTRACT_RFC.md` file and halt execution.*"

**For the Graph Agent:**

> "You are the LangGraph Orchestrator Agent. Your isolated workspace is `../omc-lab-graph`. Your task is Phase 2 from the Roadmap. Build the AI state machine and WebSocket gateway on Port 8000. Adhere strictly to the JSON schemas in `API_CONTRACTS.md`. *If LangGraph mechanics require a deviation from the schema, do not guess. Submit a `CONTRACT_RFC.md` file and halt execution.*"

**For the Glass Agent:**

> "You are the Frontend UI Agent. Your isolated workspace is `../omc-lab-ui`. Your task is Phase 3 from the Roadmap. Build the Vue component grid. Connect your WebSocket client to `ws://localhost:8002`. *If the UI requires data not present in `API_CONTRACTS.md`, submit a `CONTRACT_RFC.md` file and halt execution.*"

---

## 5. 🛑 The RFC (Request for Comments) Protocol

To prevent infinite `git reset` loops when an API contract is legitimately flawed, the Supervisor must support a structured feedback loop.

### 5.1 Worker Submission

If a worker encounters a blocker, it must generate a file named `CONTRACT_RFC.md` in its root worktree directory formatted exactly as follows:

```markdown
### 🚨 Contract Exception Request
**Violated Schema:** (e.g., `render_output` payload)
**Technical Blocker:** (Explanation of why the current contract fails with the library/framework).
**Proposed Change:** (The exact JSON schema adjustment required).

```

### 5.2 Supervisor Resolution

Upon detecting a `CONTRACT_RFC.md`, the Supervisor **shall**:

1. Evaluate the proposed change.
2. **If Approved:** * Update the master `API_CONTRACTS.md`.
* Update the `mock_ws_server.py` to reflect the new schema.
* Push the updated `API_CONTRACTS.md` to *all* active worktrees to ensure the other agents adapt.
* Instruct the worker to delete the RFC file and resume.


3. **If Rejected:**
* Provide the worker with an alternative technical approach that satisfies the existing contract and instruct it to retry.



---

## 6. 🚨 Emergency Fallback Procedures

* **The Unapproved Violation:** **If** a worker agent modifies an API payload outside the bounds of `API_CONTRACTS.md` *without* submitting an RFC: The Supervisor **shall** reject the commit, wipe the worktree's uncommitted changes using `git reset --hard`, and reprompt the worker with the specific contract violation highlighted.
* **The Infinite Loop Breaker:** **If** a worker triggers a `git reset --hard` three times consecutively for the same issue, the Supervisor **shall** forcibly pause the worker and command it to generate a `CONTRACT_RFC.md` to articulate its failure point.
* **Merge Conflicts:** **If** an unresolvable merge conflict occurs between Engine and Graph: The Supervisor **shall** halt integration, isolate the conflicting files, and resolve the dependency manually before attempting the UI merge.

---

### 🚀 Next Step

With the RFC protocol in place, your agents now have a safe way to collaborate with you on architectural roadblocks.

**Would you like me to draft the `mock_ws_server.py` script now, so you have the foundational testing harness ready for the Glass Agent?**