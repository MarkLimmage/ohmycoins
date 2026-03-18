# 📜 API_CONTRACTS.md: The Lab 2.0

> **⚠️ CANONICAL SOURCE MOVED TO ROOT**
>
> The authoritative API contract for The Lab is now maintained at the project root:
> **[/API_CONTRACTS.md](/API_CONTRACTS.md)** (v1.3 — Conversational Scientific Grid)
>
> This file previously contained v1.2. All v1.2 schemas remain valid within v1.3
> (backward-compatible envelope). The v1.3 contract adds:
> - `stream_chat`, `user_message`, `plan_established` event types (7 total, was 5)
> - 3-Cell routing contract (Dialogue | Activity | Outputs)
> - 4 `action_request` subtypes: `scope_confirmation_v1`, `approve_modeling_v1`, `model_selection_v1`, `circuit_breaker_v1`
> - `POST /message` endpoint with `sequence_id` return guarantee
> - 4 interrupt points (was 2): `scope_confirmation`, `train_model`, `model_selection`, `finalize`
> - Mandatory scope confirmation at BUSINESS_UNDERSTANDING (no skip)
> - Circuit breaker → `action_request` escalation (was TERMINAL_ERROR)
> - Rehydration replays ALL event types to reconstruct all 3 cells
>
> **Do NOT maintain a separate copy here.** Always read the root file.
