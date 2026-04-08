# CONTRACT RFC: B2 Inline Edit Blocked

**Agent:** Glass Agent (Sprint 2.61)
**Date:** 2025-04-09
**Status:** BLOCKED — Awaiting Supervisor/Backend Agent

## Issue

B2 (inline edit mode for LLM credentials) requires a `PATCH /api/v1/users/me/llm-credentials/{id}` endpoint to update `model_name` and rotate `api_key`.

The current `frontend/openapi.json` does **not** contain this PATCH endpoint. The generated client (`sdk.gen.ts`) has no `updateLlmCredential()` method.

## What's Needed

The Backend Agent (Workstream A) must:
1. Implement `PATCH /api/v1/users/me/llm-credentials/{id}` accepting optional `model_name` and `api_key` fields
2. Export the updated OpenAPI spec to `frontend/openapi.json`
3. Regenerate the TypeScript client

## Completed Work (B1, B3, B4)

- **B1:** Credentials grouped by provider with collapsible Accordion sections
- **B3:** `model_name` is now required in the create form; helper text added
- **B4:** Delete confirmation dialog added

## What Remains (B2)

Once the PATCH endpoint is available in `openapi.json`:
- Add "Edit" icon button to each credential row
- Inline edit form with `model_name` text input + optional `api_key` rotation
- Validate before save, invalidate React Query cache on success
