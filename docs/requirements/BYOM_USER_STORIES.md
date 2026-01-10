# BYOM (Bring Your Own Model) - User Stories

**Feature:** Bring Your Own Model (BYOM)  
**Date Created:** 2026-01-11  
**Status:** APPROVED - Ready for Implementation  
**Priority:** HIGH (Sprint 2.8 Target)

---

## Epic: User-Provided LLM Integration

**As a** OMC platform user  
**I want to** use my own LLM provider and API keys for agent operations  
**So that** I can control costs, choose preferred models, and maintain data sovereignty

---

## User Stories

### US-BYOM-001: User API Key Management

**As a** registered user  
**I want to** securely store my own LLM API keys in my profile  
**So that** I can use my preferred AI models without relying on system-provided credits

**Acceptance Criteria:**
- User can add/update/delete API keys for supported providers (OpenAI, Google, Anthropic)
- API keys are encrypted at rest using existing encryption service
- Keys are never returned in plaintext to frontend (masked display only)
- Users can test their API key validity before saving
- Multiple providers can be configured per user (future-proofing)

**Priority:** HIGH  
**Story Points:** 8

---

### Priority 2: Model Selection per Session

#### User Story 2.1: Select Model per Session
**As a** user starting a new agent session  
**I want to** choose which LLM model to use (system default or my own)  
**So that** I can control costs and experiment with different models

**Acceptance Criteria:**
- [ ] Session creation UI includes model selection dropdown
- [ ] Options: "System Default" or "My Custom Model" (if API key configured)
- [ ] Selected model is stored with the session
- [ ] Session uses the selected model for all agent operations

#### Priority 2: User API Key Management

**As a user, I want to** securely store my own LLM provider API keys  
**So that I can** use my own models without sharing account credentials

**Acceptance Criteria:**
- Users can add/update/delete API keys for multiple providers (OpenAI, Google, Anthropic)
- API keys are encrypted at rest using existing encryption service
- Keys are never returned to frontend (masked display only)
- Users can test key validity before saving
- Keys can be rotated or deleted at any time

#### US-BYOM-003: Model Selection per Session
**As a** user  
**I want to** choose which AI model to use when starting a new agent session  
**So that** I can optimize for cost, performance, or use my preferred provider

**Acceptance Criteria:**
- Session creation UI includes model selection dropdown
- Options: "System Default" or "My Model" (if configured)
- Session stores the selected model for its lifetime
- Previous sessions display which model was used

### 2.2 Advanced User Stories

**US-004: Manage Multiple Provider Keys**
As a user, I want to configure API keys for multiple providers (OpenAI, Google, Anthropic) so that I can switch between them based on my needs.

**US-005: Model Selection per Session**
As a user, I want to select which model to use when starting a new agent session, so that I can optimize for cost or performance based on my specific task.

---

## 3. EARS Requirements

### 3.1 Functional Requirements

**REQ-BYOM-001: User Model Configuration**
- **WHILE** user is authenticated
- **WHEN** user navigates to settings
- **THEN** the system shall display options to configure LLM provider credentials
- **WHERE** providers include OpenAI, Google (Gemini), Anthropic, and Azure OpenAI

**REQ-BYOM-001**: The system shall allow authenticated users to configure their own LLM provider credentials.

**REQ-BYOM-002**: The system shall support the following LLM providers:
- OpenAI (GPT-4, GPT-4 Turbo, GPT-3.5 Turbo)
- Google (Gemini 1.5 Pro, Gemini Pro)
- Anthropic (Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Sonnet)
- Azure OpenAI (future extension)

**Acceptance Criteria:**
- Users can store encrypted API keys for each provider
- Users can select preferred model from available options
- System validates API keys before storing
- Keys are never returned to frontend (masked only)

### 2.2 Session-Level Model Selection
**US-002**: As a user, I want to select which LLM model to use when starting a new agent session, so I can choose between system default and my own models.

**Priority:** HIGH  
**Sprint:** 2.9 (Week 2)

**Acceptance Criteria:**
- Session creation UI includes model selection dropdown
- Options: "System Default" or "My Model" (if user has configured keys)
- Model selection stored in AgentSession
- Session creation validates user has necessary credentials
- Clear error messaging if selected provider unavailable

**Technical Requirements:**
- AgentSession model extended with model configuration fields
- Session creation API validates user credentials for selected provider
- Frontend session creation UI includes model selection

**EARS Requirements:**
- WHILE user has configured LLM credentials, WHEN creating a new agent session, THE system SHALL display available model options
- IF user selects custom model, THEN system SHALL use user's encrypted credentials
- IF user has not configured credentials, THEN system SHALL fall back to system default
- WHEN user deletes API key, THEN all active sessions using that key SHALL be terminated gracefully

### 2. Security & Encryption

**Priority:** HIGH  
**Effort:** Medium (2-3 days)  
**Dependencies:** None

**Story:** As a user, I want my API keys stored securely so that my credentials remain private and protected.

**Requirements:**
1. **WHILE** storing user LLM API keys, **IF** the key is not empty, **THEN** the system **SHALL** encrypt the key using the existing EncryptionService
2. **WHERE** API keys are stored in the database, the system **SHALL** store only encrypted values
3. **WHEN** displaying API keys to users, **THEN** the system **SHALL** mask all but the last 4 characters
4. **IF** a user deletes their account or API key, **THEN** the system **SHALL** securely delete the encrypted key from the database

**User Stories:**
- As a user, I want my API keys encrypted at rest so that my credentials are secure
- As a user, I want to be able to delete my stored API keys at any time
- As a developer, I need to ensure API keys are never logged or returned to frontend

**Files to Modify:**
- Create: `backend/app/models/user_llm_credentials.py`
- Update: `backend/app/models.py` to include relationship
- Extend: `backend/app/services/encryption.py` for LLM key encryption
- Add: New CRUD operations for LLM credentials

---

### 3. Backend Agent Refactoring

**Priority:** HIGH  
**Sprint:** 2.8 (Foundation) + 2.9 (Integration)

**User Stories:**

**US-3.1:** As a system, I want to inject user-specific LLM configurations into agent sessions, so that each session uses the correct model and credentials.

**US-3.2:** As a developer, I want a factory pattern for LLM client instantiation, so that I can support multiple providers without conditional logic everywhere.

**Requirements (EARS):**

- **REQ-BYOM-3.1:** WHEN an AgentSession is created, the system SHALL retrieve the user's LLM configuration from the database.
- **REQ-BYOM-3.2:** IF the user has configured a custom LLM, the system SHALL use the user's encrypted API key; ELSE the system SHALL use the default system credentials.
- **REQ-BYOM-3.3:** The BaseAgent class SHALL accept an optional llm parameter during initialization.
- **REQ-BYOM-3.4:** The system SHALL implement an LLMFactory that returns LangChain LLM instances based on provider and credentials.
- **REQ-BYOM-3.5:** WHERE a user-provided API key fails authentication, the system SHALL log the error and notify the user without exposing the key.

**Implementation Files:**
- `backend/app/services/agent/orchestrator.py` - Update `start_session` method
- `backend/app/services/agent/agents/base.py` - Accept dynamic LLM instance
- `backend/app/services/agent/llm_factory.py` (NEW) - LLM client factory
- `backend/app/services/agent/agents/*.py` - Update agent initialization

---

### 4. Multi-Provider LLM Support

**Priority:** HIGH  
**Sprint:** 2.8 (Google/Gemini) + 2.9 (Anthropic)

**User Stories:**

**US-4.1:** As a user, I want to select Google Gemini as my model provider, so that I can use Google's AI models.

**US-4.2:** As a user, I want to select Anthropic Claude as my model provider, so that I can use Claude models.

**US-4.3:** As a system administrator, I want to configure default provider settings, so that users without custom configurations get a working default.

**Requirements (EARS):**

- **REQ-BYOM-4.1:** The system SHALL support OpenAI (gpt-4, gpt-3.5-turbo), Google (gemini-1.5-pro, gemini-pro), and Anthropic (claude-3-opus, claude-3-sonnet) providers.
- **REQ-BYOM-4.2:** WHEN Google Gemini is selected, the system SHALL use `langchain-google-genai` with proper system message conversion.
- **REQ-BYOM-4.3:** WHEN Anthropic Claude is selected, the system SHALL use `langchain-anthropic` with Claude-specific prompt templates.
- **REQ-BYOM-4.4:** The LLMFactory SHALL validate that the requested model is available for the selected provider.
- **REQ-BYOM-4.5:** IF a provider's API is unavailable, the system SHALL retry up to 3 times with exponential backoff BEFORE failing the request.

**Implementation Files:**
- `backend/pyproject.toml` - Add `langchain-google-genai`, `langchain-anthropic`
- `backend/app/core/config.py` - Add provider-specific settings
- `backend/app/services/agent/llm_factory.py` - Implement multi-provider logic
- `backend/app/services/agent/prompts/` - Provider-specific prompt templates

---

### 5. Prompt Engineering for Multi-Provider Support

**Priority:** MEDIUM  
**Sprint:** 2.9

**User Stories:**

**US-5.1:** As a system, I want provider-optimized prompts, so that each LLM performs optimally regardless of provider.

**US-5.2:** As a developer, I want to test prompts across all providers, so that I can ensure consistent agent behavior.

**Requirements (EARS):**

- **REQ-BYOM-5.1:** The system SHALL maintain provider-specific prompt templates for system messages, function calling, and error handling.
- **REQ-BYOM-5.2:** WHERE Gemini is used, the system SHALL convert system messages to human messages (Gemini limitation).
- **REQ-BYOM-5.3:** WHERE Claude is used, the system SHALL use XML-style prompt formatting for optimal results.
- **REQ-BYOM-5.4:** The system SHALL include unit tests comparing agent outputs across all three providers for identical inputs.

**Implementation Files:**
- `backend/app/services/agent/prompts/base_prompts.py` (NEW) - Base prompt templates
- `backend/app/services/agent/prompts/openai_prompts.py` (NEW)
- `backend/app/services/agent/prompts/google_prompts.py` (NEW)
- `backend/app/services/agent/prompts/anthropic_prompts.py` (NEW)
- `backend/tests/services/agent/test_multi_provider_prompts.py` (NEW)

---

### 6. Frontend User Settings UI

**Priority:** MEDIUM  
**Sprint:** 2.9 + 2.10

**User Stories:**

**US-6.1:** As a user, I want a settings page where I can configure my LLM preferences, so that I can bring my own API keys.

**US-6.2:** As a user, I want to see masked API keys in the UI, so that my credentials remain secure while allowing me to verify they're set.

**US-6.3:** As a user, I want to test my API key connection, so that I know my configuration works before starting a session.

**Requirements (EARS):**

- **REQ-BYOM-6.1:** The frontend SHALL provide a user settings page with sections for LLM configuration.
- **REQ-BYOM-6.2:** The settings page SHALL display provider selection (OpenAI, Google, Anthropic, System Default).
- **REQ-BYOM-6.3:** WHEN a user selects a provider, the form SHALL display model options specific to that provider.
- **REQ-BYOM-6.4:** API keys SHALL be displayed as `***...last4characters` in the UI.
- **REQ-BYOM-6.5:** The settings page SHALL include a "Test Connection" button that validates the API key without starting a full session.
- **REQ-BYOM-6.6:** WHERE the test connection fails, the system SHALL display a user-friendly error message with troubleshooting steps.

**Implementation Files:**
- `frontend/src/components/UserSettings/LLMSettings.tsx` (NEW)
- `frontend/src/components/UserSettings/ProviderSelector.tsx` (NEW)
- `frontend/src/components/UserSettings/APIKeyInput.tsx` (NEW)
- `frontend/src/routes/_layout/settings.tsx` - Add LLM settings section

---

### 7. Session Creation with Model Selection

**Priority:** MEDIUM  
**Sprint:** 2.10

**User Stories:**

**US-7.1:** As a user, when I start a new agent session, I want to choose between using my custom model or the system default, so that I have flexibility per session.

**US-7.2:** As a user, I want to see estimated costs before starting a session with my API key, so that I can make informed decisions.

**Requirements (EARS):**

- **REQ-BYOM-7.1:** The "Start Session" UI SHALL include a model selection dropdown.
- **REQ-BYOM-7.2:** The dropdown SHALL display: "System Default (Free)", "My OpenAI Model", "My Google Model", "My Anthropic Model".
- **REQ-BYOM-7.3:** IF a user selects a custom model that is not configured, the system SHALL display an inline warning with a link to settings.
- **REQ-BYOM-7.4:** The session creation request SHALL include the selected model configuration.
- **REQ-BYOM-7.5:** The backend SHALL validate that the user has permission to use the selected model configuration.

**Implementation Files:**
- `frontend/src/components/Agent/SessionCreation.tsx` - Add model selector
- `backend/app/api/routes/agent.py` - Update session creation endpoint

---

### 8. Security & Key Management

**Priority:** CRITICAL  
**Sprint:** 2.8 (Foundation) + Ongoing

**User Stories:**

**US-8.1:** As a security administrator, I want all user API keys encrypted at rest, so that we minimize risk if the database is compromised.

**US-8.2:** As a user, I want to rotate or delete my API keys at any time, so that I maintain control over my credentials.

**US-8.3:** As a developer, I want audit logs for all API key operations, so that we can track key usage and detect anomalies.

**Requirements (EARS):**

- **REQ-BYOM-8.1:** ALL user API keys SHALL be encrypted using AES-256 before storage.
- **REQ-BYOM-8.2:** The encryption key SHALL be stored in AWS Secrets Manager (production) or environment variables (development).
- **REQ-BYOM-8.3:** API keys SHALL NEVER be returned in API responses; only masked versions SHALL be returned.
- **REQ-BYOM-8.4:** The system SHALL provide endpoints for creating, updating, and deleting LLM credentials.
- **REQ-BYOM-8.5:** WHERE an API key is deleted, the system SHALL immediately invalidate any active sessions using that key.
- **REQ-BYOM-8.6:** The system SHALL log all operations on LLM credentials (create, read, update, delete) with user ID and timestamp.
- **REQ-BYOM-8.7:** The system SHALL implement rate limiting on LLM credential operations (max 10 updates per hour per user).

**Implementation Files:**
- `backend/app/services/encryption.py` - Extend for LLM keys
- `backend/app/api/routes/users.py` - Add LLM credential endpoints
- `backend/app/services/audit_log.py` (NEW) - Audit logging service
- `backend/app/middleware/rate_limiter.py` - Rate limiting for sensitive operations

---

### 9. Testing & Validation

**Priority:** HIGH  
**Sprint:** 2.9 + 2.10

**User Stories:**

**US-9.1:** As a developer, I want integration tests that validate multi-provider functionality, so that I can catch provider-specific bugs.

**US-9.2:** As a QA engineer, I want to test the entire BYOM flow end-to-end, so that I can ensure the user experience is seamless.

**Requirements (EARS):**

- **REQ-BYOM-9.1:** The test suite SHALL include tests for each supported provider (OpenAI, Google, Anthropic).
- **REQ-BYOM-9.2:** Integration tests SHALL verify that agents can successfully invoke tools with all providers.
- **REQ-BYOM-9.3:** Security tests SHALL verify that API keys are properly encrypted and never exposed in logs or responses.
- **REQ-BYOM-9.4:** Performance tests SHALL measure latency differences between providers.
- **REQ-BYOM-9.5:** The test suite SHALL include failure scenario tests (invalid API keys, provider downtime, rate limits).

**Implementation Files:**
- `backend/tests/services/agent/test_multi_provider_agents.py` (NEW)
- `backend/tests/integration/test_byom_flow.py` (NEW)
- `backend/tests/security/test_llm_key_encryption.py` (NEW)
- `backend/tests/performance/test_provider_latency.py` (NEW)

---

### 10. Documentation & Migration

**Priority:** MEDIUM  
**Sprint:** 2.10 + 2.11

**User Stories:**

**US-10.1:** As a user, I want clear documentation on how to set up my own API keys, so that I can use BYOM without confusion.

**US-10.2:** As a developer, I want architectural documentation explaining the BYOM implementation, so that future developers can maintain and extend it.

**Requirements (EARS):**

- **REQ-BYOM-10.1:** User-facing documentation SHALL include step-by-step guides for obtaining API keys from each provider.
- **REQ-BYOM-10.2:** Documentation SHALL include troubleshooting guides for common API key issues.
- **REQ-BYOM-10.3:** Architecture documentation SHALL include sequence diagrams for the BYOM flow.
- **REQ-BYOM-10.4:** Developer documentation SHALL include instructions for adding new providers.
- **REQ-BYOM-10.5:** The system SHALL provide in-app tooltips and help text for all BYOM settings.

**Implementation Files:**
- `docs/user-guides/BYOM_SETUP.md` (NEW)
- `docs/architecture/BYOM_ARCHITECTURE.md` (NEW)
- `docs/developer-guides/ADDING_NEW_PROVIDERS.md` (NEW)
- Frontend tooltip components

---

## Sprint Integration Plan

### Sprint 2.8 (Current - Weeks 13-14): Foundation Phase

**Objectives:**
1. Fix remaining 16 test failures from Sprint 2.7
2. Execute AWS staging deployment
3. **BYOM Foundation: Database schema and encryption**

**BYOM Work (Sprint 2.8):**
- Add `UserLLMCredentials` model to database
- Extend encryption service for LLM keys
- Add Google Gemini support to LLMFactory
- Create LLMFactory with OpenAI + Google providers
- Basic CRUD operations for LLM credentials (backend only, no UI)
- Security audit of encryption implementation

**Estimated Effort:** 8-12 hours BYOM work (parallel with other Sprint 2.8 tasks)

**Deliverables:**
- Database migration for LLM credentials
- Encrypted storage working for test API keys
- LLMFactory supports OpenAI + Google
- Unit tests for encryption and factory

---

### Sprint 2.9 (Weeks 15-16): Backend Integration

**Objectives:**
1. **BYOM Core: Agent orchestrator refactoring**
2. Multi-provider prompt engineering
3. Anthropic Claude support

**BYOM Work (Sprint 2.9):**
- Refactor `AgentOrchestrator.start_session` to use user-specific LLM configs
- Update `BaseAgent` to accept dynamic LLM instances
- Add Anthropic Claude to LLMFactory
- Create provider-specific prompt templates
- Backend API endpoints for LLM credential management
- Integration tests for multi-provider agents

**Estimated Effort:** 16-20 hours

**Deliverables:**
- Agents use user-specific models per session
- All three providers (OpenAI, Google, Anthropic) supported
- API endpoints for managing LLM credentials
- Comprehensive integration tests

---

### Sprint 2.10 (Weeks 17-18): Frontend & User Experience

**Objectives:**
1. **BYOM UI: User settings and session creation**
2. End-to-end BYOM flow testing
3. Documentation

**BYOM Work (Sprint 2.10):**
- LLM Settings page in frontend
- Provider selector and API key input components
- Session creation with model selection
- "Test Connection" functionality
- User-facing documentation (BYOM setup guide)
- End-to-end testing of BYOM flow

**Estimated Effort:** 20-24 hours

**Deliverables:**
- Complete user-facing UI for BYOM
- Users can configure and use their own API keys
- Documentation and in-app help
- E2E tests covering full BYOM workflow

---

### Sprint 2.11 (Weeks 19-20): Polish & Production Readiness

**Objectives:**
1. **BYOM Production: Security hardening and monitoring**
2. Performance optimization
3. Production deployment

**BYOM Work (Sprint 2.11):**
- Audit logging for all LLM credential operations
- Rate limiting for sensitive operations
- Performance testing and optimization
- Production deployment to AWS
- Monitoring dashboards for BYOM usage
- Final security review

**Estimated Effort:** 12-16 hours

**Deliverables:**
- BYOM feature production-ready
- Comprehensive monitoring and logging
- Security audit complete
- Deployed to production

---

## Risk Management

### High-Risk Areas

1. **Prompt Compatibility Across Providers**
   - **Risk:** Agent behavior varies significantly between providers
   - **Mitigation:** Extensive testing, provider-specific prompt tuning, fallback to conservative prompts

2. **API Key Security**
   - **Risk:** User API keys compromised through database breach or logging
   - **Mitigation:** AES-256 encryption, no keys in logs, audit logging, regular security reviews

3. **Cost Management**
   - **Risk:** Users unintentionally rack up high API costs
   - **Mitigation:** (Future) Per-session cost estimates, usage warnings, rate limiting

4. **Provider-Specific Function Calling**
   - **Risk:** Tool invocation fails with certain providers
   - **Mitigation:** Provider-specific tool schemas, extensive integration tests, graceful degradation

### Medium-Risk Areas

1. **Migration of Existing Sessions**
   - **Risk:** Existing agent sessions break when BYOM is introduced
   - **Mitigation:** Backward compatibility, system default as fallback, gradual rollout

2. **Performance Variability**
   - **Risk:** Some providers are significantly slower, degrading UX
   - **Mitigation:** Provider-specific timeout configurations, performance monitoring, user warnings

---

## Success Metrics

**Phase 1 (Sprint 2.8-2.9):**
- ✅ Database schema supports user-specific LLM credentials
- ✅ Agents can use user-provided API keys
- ✅ All three providers (OpenAI, Google, Anthropic) functional
- ✅ Zero security vulnerabilities in key storage

**Phase 2 (Sprint 2.10):**
- ✅ Users can configure LLM settings via UI
- ✅ Users can start sessions with custom models
- ✅ >90% user satisfaction in UX testing
- ✅ <5% error rate in API key validation

**Phase 3 (Sprint 2.11):**
- ✅ BYOM feature deployed to production
- ✅ >80% of test users successfully configure BYOM
- ✅ Zero security incidents in first month
- ✅ Mean agent session start time <3 seconds (any provider)

---

## Open Questions

1. **Cost Attribution:** Should we track and display API usage costs to users? (Future sprint)
2. **Provider Availability:** How do we handle when a provider is down? Automatic fallback to system default?
3. **Model Versioning:** Should we allow users to specify model versions (e.g., gpt-4-0125-preview)?
4. **Team Sharing:** Should organizations be able to share LLM credentials across team members? (Future)
5. **Rate Limiting:** What are appropriate rate limits for switching models/keys?

---

## Appendix: Files to Modify/Create

### New Files (21)
```
docs/requirements/BYOM_REQUIREMENTS.md
backend/app/models/user_llm_credentials.py
backend/app/services/agent/llm_factory.py
backend/app/services/audit_log.py
backend/app/services/agent/prompts/base_prompts.py
backend/app/services/agent/prompts/openai_prompts.py
backend/app/services/agent/prompts/google_prompts.py
backend/app/services/agent/prompts/anthropic_prompts.py
backend/tests/services/agent/test_multi_provider_agents.py
backend/tests/integration/test_byom_flow.py
backend/tests/security/test_llm_key_encryption.py
backend/tests/performance/test_provider_latency.py
frontend/src/components/UserSettings/LLMSettings.tsx
frontend/src/components/UserSettings/ProviderSelector.tsx
frontend/src/components/UserSettings/APIKeyInput.tsx
docs/user-guides/BYOM_SETUP.md
docs/architecture/BYOM_ARCHITECTURE.md
docs/developer-guides/ADDING_NEW_PROVIDERS.md
```

### Modified Files (12)
```
docs/ARCHITECTURE.md
docs/PROJECT_HANDOFF.md
docs/SYSTEM_REQUIREMENTS.md
ROADMAP.md
backend/app/models.py
backend/app/services/encryption.py
backend/app/core/config.py
backend/pyproject.toml
backend/app/services/agent/orchestrator.py
backend/app/services/agent/agents/base.py
backend/app/api/routes/users.py
frontend/src/routes/_layout/settings.tsx
```

---

**Total Estimated Effort:** 56-72 hours across 4 sprints (2.8-2.11)  
**Earliest Integration:** Sprint 2.8 (database foundation)  
**User-Facing Feature:** Sprint 2.10  
**Production Ready:** Sprint 2.11

This plan balances early integration (Sprint 2.8 starts immediately) with minimized disruption (backend-first approach, frontend last). The phased rollout allows for continuous testing and refinement without blocking other development tracks.