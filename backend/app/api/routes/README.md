# API Routes Documentation

## UI Component Support (Sprint 2.15)

### Mock UI Endpoints
Mock endpoints are available in **local development environment only** (`ENVIRONMENT=local`) to support Storybook and frontend component development without requiring a full backend state.

**Base Path**: `/api/v1/mock`

#### Endpoints
- `GET /mock/ledgers/{ledger_type}`: Returns mock P&L summary data for LedgerCards.
  - Query Params: `state` (success, loading, error, empty)
- `GET /mock/agent/sessions/{session_id}/messages`: Returns mock chat stream for AgentTerminal.
- `POST /mock/safety/{action_type}`: Simulates SafetyButton actions.
  - Query Params: `confirm` (true/false)

### Response Model Enhancements
All UI-facing response models now extend `APIResponseBase` to support progressive loading states:
- `is_loading` (bool): Indicates if data is stale/refreshing.
- `last_updated` (datetime): Timestamp of last successful update.
- `data_staleness_seconds` (float): Age of the data in seconds.

### Global Error Handling
The API now implements a standardized error response format per `API_CONTRACTS.md`:
```json
{
  "message": "User-facing error message",
  "detail": "Technical details for debugging",
  "error_code": "ERROR_CODE_STRING"
}
```
Ref: `backend/app/main.py` global exception handler.
