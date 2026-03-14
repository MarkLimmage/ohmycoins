# RFC: Standardization of Event Sequencing & Timestamping

**Status:** PROPOSED
**Author:** Worker Agent (Phase 5)
**Date:** 2026-03-15

## 1. Problem Statement
The current Server-to-Client message wrapper in `API_CONTRACTS.md` lacks ordering guarantees and temporal context.

- **No Sequence ID:** The frontend cannot detect dropped messages or process out-of-order delivery reliably.
- **No Timestamp:** The frontend cannot calculate latency or display accurate event times for historical logs.

## 2. Current Schema
```json
{
  "event_type": "stream_chat | status_update | render_output | error",
  "stage": "<StageID>",
  "payload": { ... }
}
```

## 3. Proposed Schema
We propose adding `sequence_id` (integer, monotonic) and `timestamp` (ISO-8601 UTC string) to the root of the message wrapper.

```json
{
  "event_type": "stream_chat | status_update | render_output | error",
  "stage": "<StageID>",
  "sequence_id": 42,
  "timestamp": "2026-03-15T14:30:00Z",
  "payload": { ... }
}
```

### Field Definitions
*   **`sequence_id`**: An incrementing integer counter, unique per session. Starts at 1.
*   **`timestamp`**: The server-side time of event generation in ISO-8601 format (UTC).

## 4. Impact Analysis
*   **Backend (`BaseAgent`):** Must maintain a counter in `state` or `session` and append it to `emit_event` logic automatically.
*   **Frontend:** Must update type definitions to accept these new fields.
