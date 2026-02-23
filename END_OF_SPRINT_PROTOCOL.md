# End-of-Sprint Integration & Cleanup Protocol

## 1. Context & Architecture (The "Sprint Map")
Before starting integration, establishing the landscape is critical.
*   **Structure**: Sprints are organized as `../sprint-X.XX/track-{a,b,c}` relative to the `ohmycoins` main repository.
    *   Each track is a **Git Worktree**.
    *   Each track runs a **Docker Compose Project** named `track-{letter}`.
*   **Isolation**:
    *   **Ports**: Track A (8001), C (8002), B (8020/3001). Main (80).
    *   **Database**: Each track has its own distinct postgres container/volume.
*   **State check**: `git worktree list` and `docker ps` are the sources of truth.

## 2. Integration Sequence (Per Track)
For *each* track (A, B, C), follow this standard procedure:

### A. Verification (In the Track Worktree)
1.  **Navigate**: `cd ../sprint-X.XX/track-{letter}`
2.  **Status Check**: `git status` (Ensure clean), `docker compose ps` (Ensure healthy).
3.  **Test**:
    *   Backend: `docker compose exec backend pytest`
    *   Frontend: `docker run --rm -v $(pwd)/frontend:/app -w /app node:20 /bin/sh -c "npm install && npm test"` (Use transient container if needed).
    *   *Fixes*: If tests fail, fix them **in the worktree** and commit.

### B. Shutdown (The "Handoff")
1.  **Stop**: `docker compose -p track-{letter} down`
    *   *Crucial*: Must stop to release locks and ports.

### C. Merge (In the Main Repo)
1.  **Navigate**: `cd ../../ohmycoins` (or absolute path).
2.  **Checkout**: `git checkout main` (or master).
3.  **Merge**: `git merge origin/feat/{FEATURE_NAME}`
    *   *Conflict Resolution*:
        *   `LOGBOOK.md`: Keep ALL entries (append/interleave history).
        *   `docker-compose.override.yml`: **Always revert to Main's configuration** (Port 8001, standard volumes). Do not keep track-specific ports.
        *   `.vscode/settings.json`: Revert to Main's color (Orange/Red).

## 3. Post-Integration Stabilization (The "Regression")
After merging *all* tracks:

1.  **Environment Reset**:
    *   `docker compose down` (Clear old main containers).
    *   `docker compose up -d --build` (Force rebuild to include new dependencies).
2.  **Deep Cleaning (The "Root" Fix)**:
    *   If `rm -rf` fails due to permissions: `docker run --rm -v $(pwd)/..:/work alpine rm -rf /work/sprint-X.XX`
3.  **Test Suite Audit**:
    *   Run `docker compose exec backend pytest`.
    *   *Singleton Fix*: Ensure `conftest.py` resets singletons (`OrderQueue._instance = None`).
    *   *Legacy Audit*: If tests fail due to API changes (e.g. `/my/orders` -> `/ro/my/orders`), updates the **Test**, do not revert code.
    *   *Obsolete Tests*: Delete tests for features that are explicitly depreciated or purely exploratory/mocked without implementation.

## 4. Final Polish
1.  **Push**: `git push origin main`.
2.  **Cleanup**: `git worktree prune`.
