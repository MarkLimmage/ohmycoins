# ALERT: TRACK B BLOCKED BY MISSING DEPENDENCIES

**From**: The Architect
**To**: Track B (Frontend Dev)
**Priority**: CRITICAL
**Status**: BLOCKED

## Issue Diagnosis
You are encountering `Cannot find module` errors because your worktree (`../sprint-2.31/track-b`) is a fresh checkout.
- `node_modules` is `.gitignore`d, so it does not exist in your new directory.
- Docker volumes mounts (`./frontend:/app`) are masking the inner container's pre-installed `node_modules` with your empty local directory.

## Remediation Steps

Execute the following commands in your terminal immediately to unblock your development:

1.  **Navigate to Frontend Root**:
    ```bash
    cd frontend
    ```

2.  **Install Dependencies**:
    ```bash
    npm install
    ```
    *This will populate your local `node_modules` folder, allowing the TypeScript language server and Vite to resolve `recharts` and `chakra-ui`.*

3.  **Restart Development Server**:
    If your dev server is running, kill it (`Ctrl+C`) and restart it to pick up the new modules.

4.  **Confirm Fix**:
    Check that `CollectorCard.tsx` no longer shows red squiggles under the imports.

## Note on Client Generation
Since the backend (Track A) has just added the `/stats` endpoint, your API client (`sdk.gen.ts`) is outdated.
- **Do NOT** wait for auto-generation.
- **Continue** using your manual `fetch` / `mock` implementation in `hooks.ts` as you planned.
- We will synchronize `sdk.gen.ts` in the merge phase.

**Proceed with `CollectorCard` implementation immediately after `npm install`.**
