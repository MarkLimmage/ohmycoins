# End-of-Sprint Integration & Cleanup Protocol

## 1. Context & Architecture (The "Sprint Map")
Before starting integration, establishing the landscape is critical.
*   **Structure**: Worktrees are organized as `../omc-lab-{name}` relative to the `ohmycoins` main repository.
    *   Each worktree is a **Git Worktree** on its own feature branch.
    *   Each worktree runs a **Docker Compose Project** with isolated ports via `docker-compose.override.yml`.
*   **Current Topology (Sprint 2.52)**:
    *   `../omc-lab-graph` — Graph Agent (`fix/graph-enforcement`), proxy:8020, db:5434
    *   `../omc-lab-ui` — Glass Agent (`fix/glass-enforcement`), proxy:8030, db:5435
*   **Isolation**:
    *   **Ports**: Per-worktree via `docker-compose.override.yml`. Main repo uses 8010/5433.
    *   **Database**: Each worktree has its own Postgres port. `COMPOSE_PROJECT_NAME` prevents container conflicts.
*   **State check**: `git worktree list` and `docker ps` are the sources of truth.

## 2. Integration Sequence (Per Worktree)
For *each* worktree (graph, ui), follow this standard procedure:

### A. Verification (In the Worktree)
1.  **Navigate**: `cd ../omc-lab-{name}`
2.  **Status Check**: `git status` (Ensure clean), `docker compose ps` (Ensure healthy).
3.  **Test**:
    *   Backend: `docker compose exec backend pytest`
    *   Frontend: `docker compose run --rm frontend-dev npx tsc --noEmit`
    *   *Fixes*: If tests fail, fix them **in the worktree** and commit.

### B. Shutdown (The "Handoff")
1.  **Stop**: `docker compose down`
    *   *Crucial*: Must stop to release locks and ports.

### C. Merge (In the Main Repo)
1.  **Navigate**: `cd /home/mark/claude/ohmycoins` (or the main repo path).
2.  **Checkout**: `git checkout main`.
3.  **Merge**: `git merge feature/{branch-name}`
    *   *Conflict Resolution*:
        *   `LOGBOOK.md`: Keep ALL entries.
        *   `WORKER_MISSION.md`, `CLAUDE.md`, `CURRENT_SPRINT.md`: Resolve with `git checkout --ours` (scaffolding files differ by design).
        *   `docker-compose.override.yml`: **Always revert to Main's configuration**. Do not keep worktree-specific ports.

## 3. Post-Integration Stabilization (The "Regression")
After merging *all* worktrees:

1.  **Environment Reset**:
    *   `docker compose down` (Clear old main containers).
    *   `docker compose up -d --build` (Force rebuild).
2.  **Worktree Cleanup**:
    *   `git worktree remove ../omc-lab-graph`
    *   `git worktree remove ../omc-lab-ui`
    *   `git worktree prune`
3.  **Test Suite Audit**:
    *   Run `docker compose exec backend pytest`.
    *   Run frontend type check: `docker compose run --rm frontend-dev npx tsc --noEmit`.
    *   *Legacy Audit*: If tests fail due to API changes, update the **test**, do not revert code.

## 4. Final Polish
1.  **Push**: `git push origin main`.
2.  **Cleanup**: `git worktree prune`.
