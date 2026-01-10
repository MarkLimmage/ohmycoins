# BYOM (Bring Your Own Model) - EARS Requirements Specification

**Feature:** Bring Your Own Model (BYOM)  
**Date Created:** 2026-01-11  
**Status:** APPROVED  
**Format:** EARS (Easy Approach to Requirements Syntax)

---

## 1. Ubiquitous Requirements

**REQ-BYOM-UBI-001: System-Wide Encryption**
- **The system SHALL** encrypt all user-provided LLM API keys using AES-256 encryption before storing them in the database.

**REQ-BYOM-UBI-002: Key Masking**
- **The system SHALL** never return unencrypted API keys in any API response; API keys **SHALL** be displayed in masked format (e.g., `sk-...xyz`) showing only the last 4 characters.

**REQ-BYOM-UBI-003: Audit Logging**
- **The system SHALL** log all operations on user LLM credentials (create, read, update, delete) with user ID, timestamp, and operation type.

**REQ-BYOM-UBI-004: Provider Support**
- **The system SHALL** support the following LLM providers: OpenAI, Google (Gemini), Anthropic (Claude), and Azure OpenAI (future).

**REQ-BYOM-UBI-005: Backward Compatibility**
- **WHERE** a user has not configured custom LLM credentials, **THE system SHALL** use the system default LLM configuration.

---

## 2. Event-Driven Requirements

### 2.1 User Credential Management

**REQ-BYOM-EVT-001: Add API Key**
- **WHEN** a user submits a new LLM API key via the settings UI,
- **THEN** the system **SHALL**:
  1. Validate the API key format
  2. Test the API key by making a minimal API call to the provider
  3. IF the key is valid, encrypt and store it in the `user_llm_credentials` table
  4. IF the key is invalid, return an error message with troubleshooting guidance
  5. Log the operation to the audit log

**REQ-BYOM-EVT-002: Update API Key**
- **WHEN** a user updates an existing LLM API key,
- **THEN** the system **SHALL**:
  1. Validate and test the new API key
  2. IF valid, replace the encrypted key in the database
  3. Invalidate any cached credentials
  4. Log the update operation

**REQ-BYOM-EVT-003: Delete API Key**
- **WHEN** a user deletes an LLM API key,
- **THEN** the system **SHALL**:
  1. Remove the encrypted key from the database
  2. Terminate any active agent sessions using that key
  3. Log the deletion operation
  4. Notify the user if active sessions were terminated

**REQ-BYOM-EVT-004: Test API Key Connection**
- **WHEN** a user clicks "Test Connection" for an API key,
- **THEN** the system **SHALL**:
  1. Make a minimal API call to the provider (e.g., model listing or simple completion)
  2. IF successful, display "Connection successful" with provider details
  3. IF failed, display a user-friendly error message with:
     - Specific error reason (authentication, network, invalid key)
     - Link to provider documentation
     - Troubleshooting steps
  4. Log the test operation (without logging the API key)

### 2.2 Session Creation with Model Selection

**REQ-BYOM-EVT-005: Start Session with Model Selection**
- **WHEN** a user starts a new agent session and selects a model configuration,
- **THEN** the system **SHALL**:
  1. Validate that the user has necessary credentials for the selected provider
  2. Retrieve the encrypted API key from the database
  3. Decrypt the API key using the EncryptionService
  4. Initialize the LLM client with the decrypted key
  5. Create the AgentSession record with the selected model configuration
  6. IF any step fails, return a clear error message and do NOT create the session

**REQ-BYOM-EVT-006: Session Model Fallback**
- **WHEN** an agent session fails to initialize due to invalid or expired user credentials,
- **THEN** the system **SHALL**:
  1. Log the failure (without logging the API key)
  2. Notify the user of the credential issue
  3. Optionally offer to fall back to system default (if enabled in settings)
  4. IF fallback is declined, terminate session creation

**REQ-BYOM-EVT-007: Session with System Default**
- **WHEN** a user starts a session and selects "System Default" model,
- **THEN** the system **SHALL**:
  1. Use the system-configured LLM provider (from environment variables)
  2. NOT check for or use user-provided credentials
  3. Mark the session as using system default in the database

### 2.3 Agent Execution with User Model

**REQ-BYOM-EVT-008: Agent Tool Invocation**
- **WHEN** an agent invokes a tool during a session using a user-provided model,
- **THEN** the system **SHALL**:
  1. Use the LLM client configured for that session (user-specific or system default)
  2. Handle provider-specific errors gracefully (e.g., rate limits, invalid tool schemas)
  3. Log errors without exposing API keys

**REQ-BYOM-EVT-009: Provider-Specific Prompt Handling**
- **WHEN** sending a prompt to a Google Gemini model,
- **THEN** the system **SHALL** convert system messages to human messages (Gemini limitation).

- **WHEN** sending a prompt to an Anthropic Claude model,
- **THEN** the system **SHALL** use XML-style formatting for optimal results.

- **WHEN** sending a prompt to an OpenAI model,
- **THEN** the system **SHALL** use standard LangChain message formatting.

---

## 3. State-Driven Requirements

**REQ-BYOM-STATE-001: User Has No LLM Credentials**
- **WHILE** a user has not configured any LLM credentials,
- **IF** they attempt to start a session,
- **THEN** the system **SHALL** only offer "System Default" as an option.

**REQ-BYOM-STATE-002: User Has Configured LLM Credentials**
- **WHILE** a user has configured LLM credentials for at least one provider,
- **IF** they navigate to the session creation page,
- **THEN** the system **SHALL** display:
  - "System Default" option
  - "My [Provider] Model" option for each configured provider

**REQ-BYOM-STATE-003: Active Session Using User Credentials**
- **WHILE** an agent session is active and using user-provided credentials,
- **IF** the user deletes those credentials,
- **THEN** the system **SHALL**:
  1. Terminate the session gracefully
  2. Save the session state up to the point of termination
  3. Notify the user that the session was terminated due to credential deletion

**REQ-BYOM-STATE-004: Encrypted Key in Database**
- **WHILE** a user's LLM API key is stored in the database,
- **THE system SHALL** ensure the key remains encrypted at rest.
- **IF** the encryption key is rotated,
- **THEN** the system **SHALL** re-encrypt all stored API keys with the new encryption key.

---

## 4. Optional Feature Requirements

**REQ-BYOM-OPT-001: Cost Estimation (Future)**
- **IF** the feature is enabled,
- **WHEN** a user selects a custom model for a session,
- **THEN** the system **MAY** display an estimated cost per session based on:
  - Selected model pricing (from provider documentation)
  - Average token usage for similar sessions
  - User-defined session duration

**REQ-BYOM-OPT-002: Automatic Fallback (Configurable)**
- **IF** automatic fallback is enabled in user settings,
- **WHEN** a user's custom model fails to initialize,
- **THEN** the system **MAY** automatically fall back to the system default model and notify the user.

**REQ-BYOM-OPT-003: Provider Availability Check (Future)**
- **IF** real-time provider health checks are enabled,
- **WHEN** a user starts a session,
- **THEN** the system **MAY** check provider status and warn if the selected provider is experiencing issues.

---

## 5. Unwanted Behavior Requirements

**REQ-BYOM-UNW-001: No API Keys in Logs**
- **The system SHALL NOT** log API keys in any format (plaintext, encrypted, masked).
- **WHERE** debugging requires credential information, logs **SHALL** only include:
  - Provider name (e.g., "OpenAI")
  - Last 4 characters of the key (e.g., "...xyz")
  - Success/failure status

**REQ-BYOM-UNW-002: No API Keys in Frontend**
- **The system SHALL NOT** send unencrypted or decrypted API keys to the frontend.
- **WHERE** the frontend needs to display key status, the backend **SHALL** send only:
  - Provider name
  - Model name
  - Masked key (e.g., `sk-...xyz`)
  - Configuration status (configured, not configured)

**REQ-BYOM-UNW-003: No Cross-User Key Access**
- **The system SHALL NOT** allow any user to access, view, or use another user's LLM credentials.
- **WHERE** an administrative function requires viewing user configurations, **SHALL** display only masked keys.

**REQ-BYOM-UNW-004: No Unvalidated Keys**
- **The system SHALL NOT** store an API key without first validating it against the provider's API.
- **WHERE** validation fails, the system **SHALL** reject the key and provide an error message.

**REQ-BYOM-UNW-005: No Silent Failures**
- **WHERE** a user-provided model fails during session creation or execution,
- **THE system SHALL NOT** fail silently.
- **THE system SHALL** notify the user with a clear error message and log the failure.

---

## 6. Complex Requirements

### 6.1 LLM Factory Multi-Provider Instantiation

**REQ-BYOM-CMP-001: LLM Client Instantiation**
- **WHEN** the `LLMFactory` is invoked to create an LLM client,
- **WHERE** the provider is specified as "openai",
- **THEN** the system **SHALL**:
  1. Validate that `OPENAI_API_KEY` (user or system) is present
  2. Instantiate a `ChatOpenAI` client from `langchain-openai`
  3. Configure the client with the specified model (e.g., `gpt-4-turbo-preview`)
  4. Return the configured client instance

- **WHERE** the provider is specified as "google",
- **THEN** the system **SHALL**:
  1. Validate that `GOOGLE_API_KEY` is present
  2. Instantiate a `ChatGoogleGenerativeAI` client from `langchain-google-genai`
  3. Configure with `convert_system_message_to_human=True` (Gemini requirement)
  4. Configure the client with the specified model (e.g., `gemini-1.5-pro`)
  5. Return the configured client instance

- **WHERE** the provider is specified as "anthropic",
- **THEN** the system **SHALL**:
  1. Validate that `ANTHROPIC_API_KEY` is present
  2. Instantiate a `ChatAnthropic` client from `langchain-anthropic`
  3. Configure the client with the specified model (e.g., `claude-3-opus-20240229`)
  4. Return the configured client instance

- **WHERE** the provider is not recognized,
- **THEN** the system **SHALL** raise a `ValueError` with a list of supported providers.

### 6.2 Agent Orchestrator Session Initialization

**REQ-BYOM-CMP-002: Session-Specific LLM Injection**
- **WHEN** `AgentOrchestrator.start_session` is called,
- **THEN** the system **SHALL**:
  1. Retrieve the `model_provider` and `model_name` from the session creation request
  2. **IF** `model_provider` is not "system_default":
     a. Query `UserLLMCredentials` table for the user's credentials for that provider
     b. **IF** credentials are found:
        i. Decrypt the API key using `EncryptionService`
        ii. Call `LLMFactory.create_llm(provider, model, api_key)`
        iii. Pass the LLM instance to all agents in the session
     c. **IF** credentials are NOT found:
        i. Raise `CredentialsNotFoundError`
        ii. Return error to user with link to settings
  3. **IF** `model_provider` is "system_default":
     a. Use system environment variables for LLM configuration
     b. Call `LLMFactory.create_llm(system_provider, system_model, system_key)`
     c. Pass the system LLM instance to all agents
  4. Instantiate agents with the selected LLM instance
  5. Return the initialized orchestrator

### 6.3 Encryption Service Extension

**REQ-BYOM-CMP-003: LLM Key Encryption/Decryption**
- **WHEN** the `EncryptionService.encrypt_llm_key(api_key: str)` method is called,
- **THEN** the system **SHALL**:
  1. Validate that `api_key` is a non-empty string
  2. Retrieve the encryption key from environment variable `ENCRYPTION_KEY`
  3. Use AES-256-CBC encryption with a randomly generated IV (Initialization Vector)
  4. Return a base64-encoded string containing: `<IV>:<encrypted_key>`

- **WHEN** the `EncryptionService.decrypt_llm_key(encrypted_key: str)` method is called,
- **THEN** the system **SHALL**:
  1. Decode the base64 string
  2. Extract the IV and encrypted key
  3. Use AES-256-CBC decryption with the system encryption key
  4. Return the plaintext API key
  5. **IF** decryption fails, raise `DecryptionError`

---

## 7. Performance Requirements

**REQ-BYOM-PERF-001: Key Retrieval Latency**
- **WHEN** retrieving and decrypting a user's LLM API key,
- **THEN** the operation **SHALL** complete in <100ms (95th percentile).

**REQ-BYOM-PERF-002: Session Initialization Latency**
- **WHEN** initializing an agent session with user-provided credentials,
- **THEN** the session **SHALL** be ready in <3 seconds (including key retrieval, decryption, and LLM client initialization).

**REQ-BYOM-PERF-003: API Key Validation Timeout**
- **WHEN** testing an API key against a provider,
- **THEN** the system **SHALL** timeout the test after 10 seconds and return an error.

**REQ-BYOM-PERF-004: Provider Failover**
- **WHERE** a provider API call fails,
- **THEN** the system **SHALL** retry up to 3 times with exponential backoff (1s, 2s, 4s) before failing the request.

---

## 8. Security Requirements

**REQ-BYOM-SEC-001: API Key Storage Encryption**
- **ALL** user-provided LLM API keys **SHALL** be encrypted at rest using AES-256 encryption.
- **The encryption key SHALL** be stored in AWS Secrets Manager (production) or securely in environment variables (development).

**REQ-BYOM-SEC-002: API Key Transmission**
- **API keys SHALL** only be transmitted over HTTPS (TLS 1.2+).
- **API keys SHALL NOT** be included in URL parameters or GET requests.

**REQ-BYOM-SEC-003: Rate Limiting**
- **The system SHALL** implement rate limiting for LLM credential operations:
  - Max 10 credential updates per hour per user
  - Max 20 "Test Connection" requests per hour per user
  - Max 50 credential reads per hour per user

**REQ-BYOM-SEC-004: Audit Logging**
- **ALL** operations on LLM credentials **SHALL** be logged with:
  - User ID
  - Operation type (create/read/update/delete/test)
  - Timestamp
  - Success/failure status
  - Provider name (NOT the API key)

**REQ-BYOM-SEC-005: Access Control**
- **Users SHALL** only be able to access their own LLM credentials.
- **System administrators SHALL NOT** have direct access to decrypt user API keys without explicit audit logging.

**REQ-BYOM-SEC-006: Key Deletion**
- **WHEN** a user deletes their account,
- **THEN** the system **SHALL** securely delete all associated LLM credentials within 24 hours.

**REQ-BYOM-SEC-007: Encryption Key Rotation**
- **The system SHALL** support encryption key rotation without data loss.
- **WHERE** the encryption key is rotated,
- **THEN** all stored API keys **SHALL** be re-encrypted with the new key within 7 days.

---

## 9. Usability Requirements

**REQ-BYOM-USE-001: API Key Input Validation**
- **WHEN** a user enters an API key,
- **THEN** the UI **SHALL** validate the format in real-time and display format examples.

**REQ-BYOM-USE-002: Error Messages**
- **ALL** error messages related to LLM credentials **SHALL** be user-friendly and include:
  - What went wrong (in non-technical language)
  - Why it happened (e.g., "The API key format is incorrect")
  - How to fix it (e.g., "Please check your key from the provider dashboard")
  - Link to relevant documentation

**REQ-BYOM-USE-003: In-App Help**
- **The LLM settings page SHALL** include:
  - Tooltips for each field
  - Link to provider documentation for obtaining API keys
  - FAQ section for common issues

**REQ-BYOM-USE-004: Visual Feedback**
- **WHEN** testing an API key connection,
- **THEN** the UI **SHALL** display:
  - Loading spinner during the test
  - Clear success/failure indicator
  - Response time for the test

---

## 10. Data Model Requirements

**REQ-BYOM-DATA-001: UserLLMCredentials Table Schema**
- **The system SHALL** create a `user_llm_credentials` table with the following columns:
  - `id`: UUID (primary key)
  - `user_id`: UUID (foreign key to `user` table)
  - `provider`: ENUM('openai', 'google', 'anthropic', 'azure')
  - `model_name`: VARCHAR(100) (e.g., 'gpt-4-turbo-preview')
  - `encrypted_api_key`: TEXT (AES-256 encrypted)
  - `is_default`: BOOLEAN (whether this is the user's default provider)
  - `created_at`: TIMESTAMP
  - `updated_at`: TIMESTAMP
  - `last_used_at`: TIMESTAMP (nullable)

**REQ-BYOM-DATA-002: AgentSession Model Extension**
- **The `agent_session` table SHALL** be extended with the following columns:
  - `model_provider`: VARCHAR(50) (e.g., 'openai', 'google', 'system_default')
  - `model_name`: VARCHAR(100) (e.g., 'gpt-4-turbo-preview')
  - `using_custom_model`: BOOLEAN (TRUE if user-provided, FALSE if system default)

**REQ-BYOM-DATA-003: Foreign Key Constraints**
- **The `user_llm_credentials` table SHALL** have a foreign key constraint on `user_id` with `ON DELETE CASCADE`.
- **WHERE** a user is deleted,
- **THEN** all associated LLM credentials **SHALL** be automatically deleted.

---

## 11. Integration Testing Requirements

**REQ-BYOM-TEST-001: Multi-Provider Agent Tests**
- **The test suite SHALL** include integration tests that:
  1. Create a session with OpenAI credentials
  2. Verify the agent can invoke tools successfully
  3. Repeat for Google and Anthropic credentials
  4. Verify consistent agent behavior across all providers

**REQ-BYOM-TEST-002: Security Tests**
- **The test suite SHALL** include security tests that:
  1. Verify API keys are encrypted before storage
  2. Verify API keys are never returned in API responses
  3. Verify API keys are never logged in plaintext
  4. Verify users cannot access other users' credentials

**REQ-BYOM-TEST-003: Failure Scenario Tests**
- **The test suite SHALL** include tests for:
  1. Invalid API key format
  2. Expired API key
  3. Provider API downtime
  4. Rate limit exceeded
  5. Insufficient provider credits

**REQ-BYOM-TEST-004: Performance Tests**
- **The test suite SHALL** measure and validate:
  1. Key retrieval and decryption latency (<100ms)
  2. Session initialization latency with custom model (<3s)
  3. Provider API response time comparison (OpenAI vs Google vs Anthropic)

---

## 12. Acceptance Criteria Summary

**Phase 1 - Database & Security (Sprint 2.8):**
- ✅ `UserLLMCredentials` model created with proper schema
- ✅ Encryption service extended for LLM keys
- ✅ Unit tests for encryption/decryption passing
- ✅ Database migration successfully applied
- ✅ Zero security vulnerabilities in key storage

**Phase 2 - Backend Integration (Sprint 2.9):**
- ✅ `LLMFactory` supports OpenAI, Google, and Anthropic
- ✅ `AgentOrchestrator` uses user-specific LLM instances
- ✅ API endpoints for CRUD operations on LLM credentials functional
- ✅ Integration tests for multi-provider agents passing
- ✅ Agents successfully invoke tools with all three providers

**Phase 3 - Frontend & UX (Sprint 2.10):**
- ✅ LLM Settings page allows users to configure API keys
- ✅ Session creation includes model selection dropdown
- ✅ "Test Connection" validates API keys before saving
- ✅ User-facing documentation available
- ✅ End-to-end BYOM flow tested and working

**Phase 4 - Production Readiness (Sprint 2.11):**
- ✅ Audit logging captures all LLM credential operations
- ✅ Rate limiting prevents abuse
- ✅ Performance meets requirements (<3s session init)
- ✅ Security audit completed with zero critical issues
- ✅ BYOM feature deployed to production

---

## Appendix A: Requirement Traceability Matrix

| Requirement ID | User Story | Priority | Sprint | Test Case |
|----------------|------------|----------|--------|-----------|
| REQ-BYOM-EVT-001 | US-BYOM-001 | HIGH | 2.8 | TEST-BYOM-001 |
| REQ-BYOM-EVT-005 | US-BYOM-003 | HIGH | 2.9 | TEST-BYOM-005 |
| REQ-BYOM-CMP-001 | US-BYOM-004 | HIGH | 2.9 | TEST-BYOM-010 |
| REQ-BYOM-CMP-002 | US-BYOM-005 | HIGH | 2.9 | TEST-BYOM-011 |
| REQ-BYOM-SEC-001 | US-BYOM-008 | CRITICAL | 2.8 | TEST-BYOM-020 |
| ... | ... | ... | ... | ... |

---

**Total Requirements:** 57  
**Critical Requirements:** 12  
**High Priority Requirements:** 28  
**Medium Priority Requirements:** 13  
**Low Priority Requirements:** 4  

**Status:** APPROVED - Ready for Implementation  
**Next Review Date:** End of Sprint 2.8
