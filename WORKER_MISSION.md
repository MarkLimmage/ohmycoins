# Worker Mission: Glass Bridge Agent (Workstream E)

**Spec Version:** v1.2
**Dependency:** Workstreams A + B (merge last — needs EventLedger, rehydration endpoint, action_request)

## Task
Refactor the React frontend from "Flat Chat" to the "Scientific Grid" architecture.

## Deliverables
1. **E1: Stage-Isolated Grid** — Replace flat `LabCell[]` with `Map<StageID, LabCell[]>`. Each DSLC stage gets a discrete cell.
2. **E2: Sequence-ID Ordering** — Sort events by `sequence_id`. Discard out-of-order events with lower sequence_id than current state.
3. **E3: Mime-Type Dispatcher** — Route `render_output` to the correct renderer based on `mime_type` (Markdown, Plotly, Blueprint card, Tearsheet, PNG).
4. **E4: `useRehydration()` Hook** — REST-first (call rehydration endpoint on mount), then WebSocket-live (connect with `?after_seq`).
5. **E5: HITL Action Request Controls** — Render high-contrast Approve/Reject/Edit buttons when `action_request` events arrive.
6. **E6: Model Discarded UI** — Visual indicator when a model is tagged `lifecycle: discarded`.
7. **E7: Cached Parquet Badge** — Show badge when Parquet data was served from cache.

## Files to Modify
- `frontend/src/features/lab/` — Grid components, stage cells
- `frontend/src/features/lab/hooks/` — `useRehydration`, WebSocket hooks
- `frontend/src/features/lab/components/` — mime-type renderers, HITL buttons

## Constraints
- Connect WebSocket to `ws://localhost:8002` for development (Supervisor mock server).
- Assume all backend data matches `API_CONTRACTS.md` v1.2 exactly.
- Use React + Chakra UI. No other UI frameworks.
- If UI needs data not in `API_CONTRACTS.md` v1.2, write `CONTRACT_RFC.md` and halt.
