# BYOM API Reference - Developer B Quick Guide

**Purpose:** Quick reference for Developer B to integrate frontend with existing BYOM backend APIs  
**Last Updated:** January 17, 2026

---

## Authentication

All endpoints require authentication via JWT token in Authorization header:
```
Authorization: Bearer <jwt_token>
```

User is identified from JWT token (no need to pass user_id in requests).

---

## API Endpoints

### Base URL
- **Local Development:** `http://localhost:8000/api/v1`
- **Staging:** TBD
- **Production:** TBD

---

## 1. Create LLM Credentials

**Endpoint:** `POST /users/me/llm-credentials`

**Description:** Create new LLM API credentials for the current user.

**Request Body:**
```json
{
  "provider": "openai",           // Required: "openai" | "google" | "anthropic"
  "api_key": "sk-...",           // Required: API key (will be encrypted)
  "model_name": "gpt-4",         // Optional: Model name (uses provider default if omitted)
  "is_default": true             // Optional: Set as default credential (default: false)
}
```

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "660e8400-e29b-41d4-a716-446655440000",
  "provider": "openai",
  "model_name": "gpt-4",
  "api_key_masked": "sk-...xyz",   // Only last 4 characters visible
  "is_default": true,
  "is_active": true,
  "last_validated_at": null,       // Null until validated
  "created_at": "2026-01-17T07:18:00Z",
  "updated_at": "2026-01-17T07:18:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Provider already has active credentials
- `422 Unprocessable Entity` - Invalid provider or validation error
- `500 Internal Server Error` - Encryption failure

---

## 2. List LLM Credentials

**Endpoint:** `GET /users/me/llm-credentials`

**Description:** List all active LLM credentials for the current user.

**Response:** `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "660e8400-e29b-41d4-a716-446655440000",
    "provider": "openai",
    "model_name": "gpt-4",
    "api_key_masked": "sk-...xyz",
    "is_default": true,
    "is_active": true,
    "last_validated_at": "2026-01-17T08:00:00Z",
    "created_at": "2026-01-17T07:18:00Z",
    "updated_at": "2026-01-17T08:00:00Z"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "user_id": "660e8400-e29b-41d4-a716-446655440000",
    "provider": "anthropic",
    "model_name": "claude-3-sonnet-20240229",
    "api_key_masked": "sk-...abc",
    "is_default": false,
    "is_active": true,
    "last_validated_at": null,
    "created_at": "2026-01-17T07:20:00Z",
    "updated_at": "2026-01-17T07:20:00Z"
  }
]
```

**Notes:**
- Returns only active credentials (`is_active=true`)
- API keys are always masked (only last 4 chars visible)
- Ordered by `created_at` descending

---

## 3. Set Default Credential

**Endpoint:** `PUT /users/me/llm-credentials/{credential_id}/default`

**Description:** Set a credential as the default for agent execution.

**Path Parameters:**
- `credential_id` (UUID) - ID of the credential to set as default

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "660e8400-e29b-41d4-a716-446655440000",
  "provider": "openai",
  "model_name": "gpt-4",
  "api_key_masked": "sk-...xyz",
  "is_default": true,               // Now default
  "is_active": true,
  "last_validated_at": "2026-01-17T08:00:00Z",
  "created_at": "2026-01-17T07:18:00Z",
  "updated_at": "2026-01-17T09:00:00Z"  // Updated timestamp
}
```

**Error Responses:**
- `404 Not Found` - Credential not found or doesn't belong to user
- `403 Forbidden` - Not authorized to modify this credential

**Notes:**
- Automatically unsets any previous default credential
- Only one credential can be default at a time

---

## 4. Delete Credential

**Endpoint:** `DELETE /users/me/llm-credentials/{credential_id}`

**Description:** Delete (soft-delete) an LLM credential.

**Path Parameters:**
- `credential_id` (UUID) - ID of the credential to delete

**Response:** `200 OK`
```json
{
  "message": "LLM credential deleted successfully"
}
```

**Error Responses:**
- `404 Not Found` - Credential not found or doesn't belong to user
- `403 Forbidden` - Not authorized to delete this credential

**Notes:**
- Soft delete: Sets `is_active=false` instead of physical deletion
- Deleted credentials won't appear in list endpoint
- Cannot be undone (would need to recreate)

---

## 5. Validate Credential

**Endpoint:** `POST /users/me/llm-credentials/validate`

**Description:** Validate an API key before saving or test an existing credential.

**Request Body:**
```json
{
  "provider": "openai",          // Required: Provider to test
  "api_key": "sk-...",          // Required: API key to validate
  "model_name": "gpt-4"         // Optional: Model to test (uses default if omitted)
}
```

**Response:** `200 OK`
```json
{
  "is_valid": true,
  "provider": "openai",
  "model_name": "gpt-4",
  "message": "API key is valid and working",
  "tested_at": "2026-01-17T09:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid API key or validation failed
- `422 Unprocessable Entity` - Invalid provider
- `503 Service Unavailable` - Provider API unreachable

**Notes:**
- Makes a test call to the provider's API
- Does not store the API key (validation only)
- Useful for testing before creating credential
- Updates `last_validated_at` if validating existing credential

---

## Provider Information

### Supported Providers

| Provider | ID | Default Model | Cost (per 1M tokens) |
|----------|-----|---------------|---------------------|
| OpenAI | `openai` | `gpt-4o-mini` | Input: $0.15, Output: $0.60 |
| Google | `google` | `gemini-1.5-flash` | Input: $0.075, Output: $0.30 |
| Anthropic | `anthropic` | `claude-3-sonnet-20240229` | Input: $3.00, Output: $15.00 |

### Provider-Specific Notes

#### OpenAI
- **API Key Format:** `sk-...` (starts with "sk-")
- **Models Available:** gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo
- **Documentation:** https://platform.openai.com/docs

#### Google Gemini
- **API Key Format:** Free-form string
- **Models Available:** gemini-1.5-pro, gemini-1.5-flash, gemini-1.0-pro
- **Documentation:** https://ai.google.dev/docs

#### Anthropic Claude
- **API Key Format:** `sk-ant-...` (starts with "sk-ant-")
- **Models Available:** claude-3-opus, claude-3-sonnet, claude-3-haiku
- **Documentation:** https://docs.anthropic.com/claude/reference

---

## Security Considerations

### Frontend Security
1. **Never store plain-text API keys in state or localStorage**
2. **Clear sensitive form data after submission**
3. **Use password/sensitive input types for API key fields**
4. **Disable autocomplete on API key inputs**
5. **Show/hide toggle for API key visibility**
6. **Validate input format before submission**

### Backend Security (Already Implemented) ✅
- AES-256-GCM encryption at rest
- Keys never logged in plain text
- HTTPS-only transmission
- User isolation enforced
- Authorization on all endpoints
- Rate limiting per user

---

## Error Handling

### Common Error Patterns

```typescript
// 400 Bad Request - Validation error
{
  "detail": "Active openai credentials already exist. Use PUT to update or DELETE first."
}

// 401 Unauthorized - Not authenticated
{
  "detail": "Not authenticated"
}

// 403 Forbidden - Not authorized
{
  "detail": "Not authorized to access this credential"
}

// 404 Not Found - Credential doesn't exist
{
  "detail": "LLM credential not found"
}

// 422 Unprocessable Entity - Invalid input
{
  "detail": [
    {
      "loc": ["body", "provider"],
      "msg": "Provider must be one of: openai, google, anthropic",
      "type": "value_error"
    }
  ]
}

// 500 Internal Server Error - Server error
{
  "detail": "Failed to encrypt API key"
}

// 503 Service Unavailable - Provider unreachable
{
  "detail": "Failed to connect to OpenAI API. Please try again later."
}
```

---

## TypeScript Type Definitions

```typescript
// Request types
interface UserLLMCredentialCreate {
  provider: 'openai' | 'google' | 'anthropic';
  api_key: string;
  model_name?: string;
  is_default?: boolean;
}

interface UserLLMCredentialValidate {
  provider: 'openai' | 'google' | 'anthropic';
  api_key: string;
  model_name?: string;
}

// Response types
interface UserLLMCredential {
  id: string;
  user_id: string;
  provider: 'openai' | 'google' | 'anthropic';
  model_name?: string;
  api_key_masked: string;
  is_default: boolean;
  is_active: boolean;
  last_validated_at?: string;
  created_at: string;
  updated_at: string;
}

interface UserLLMCredentialValidationResult {
  is_valid: boolean;
  provider: string;
  model_name?: string;
  message: string;
  tested_at: string;
}

interface Message {
  message: string;
}

interface ErrorDetail {
  detail: string | Array<{
    loc: string[];
    msg: string;
    type: string;
  }>;
}
```

---

## Testing the API

### Using curl

```bash
# 1. Create credential
curl -X POST http://localhost:8000/api/v1/users/me/llm-credentials \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "api_key": "sk-test-key",
    "model_name": "gpt-4o-mini",
    "is_default": true
  }'

# 2. List credentials
curl -X GET http://localhost:8000/api/v1/users/me/llm-credentials \
  -H "Authorization: Bearer $JWT_TOKEN"

# 3. Set default
curl -X PUT http://localhost:8000/api/v1/users/me/llm-credentials/$CRED_ID/default \
  -H "Authorization: Bearer $JWT_TOKEN"

# 4. Validate credential
curl -X POST http://localhost:8000/api/v1/users/me/llm-credentials/validate \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "api_key": "sk-test-key",
    "model_name": "gpt-4o-mini"
  }'

# 5. Delete credential
curl -X DELETE http://localhost:8000/api/v1/users/me/llm-credentials/$CRED_ID \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Using the API Docs
1. Navigate to `http://localhost:8000/docs`
2. Click "Authorize" button
3. Enter JWT token
4. Test endpoints interactively

---

## OpenAPI Spec Generation

To generate TypeScript client from OpenAPI spec:

```bash
cd frontend
npm run generate-client  # or similar command

# This should create/update:
# - src/client/sdk.gen.ts
# - src/client/types.gen.ts
# - src/client/schemas.gen.ts
```

---

## Next Steps for Frontend Development

1. **Generate TypeScript client** from OpenAPI spec
2. **Create API hooks** using React Query or similar
3. **Build credential management UI** components
4. **Implement form validation** and error handling
5. **Add loading/success/error states**
6. **Test with all 3 providers**
7. **Write component tests**

---

**Last Updated:** January 17, 2026  
**Author:** Sprint 2.10 Developer B Initiation
