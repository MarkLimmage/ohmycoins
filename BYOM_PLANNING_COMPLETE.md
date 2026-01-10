# BYOM Feature Planning Complete

**Date**: 2026-01-10  
**Status**: Planning Phase Complete ✅  
**Next Step**: Human Review & Sprint 2.8 Initialization

---

## 📋 Planning Summary

Comprehensive planning for the **Bring Your Own Model (BYOM)** feature has been completed. The BYOM feature will enable users to configure custom LLM providers (OpenAI, Google Gemini, Anthropic Claude) for agent execution.

**Strategic Approach:**
- **Phased implementation** across 4 sprints (2.8-2.11)
- **Minimal disruption** to existing development priorities
- **Foundation work in Sprint 2.8** (8-12 hours) parallel to test fixes
- **Security-first design** with AES-256 encryption
- **Backward compatible** - existing users unaffected

---

## 📚 Documentation Created

### 1. Requirements Documentation

**[docs/requirements/BYOM_USER_STORIES.md](docs/requirements/BYOM_USER_STORIES.md)**
- 10 user stories with acceptance criteria and story points
- Sprint integration plan for Sprints 2.8-2.11
- Risk management strategy
- Success metrics for each phase
- 33 files to modify/create
- Total effort: 56-72 hours

**[docs/requirements/BYOM_EARS_REQUIREMENTS.md](docs/requirements/BYOM_EARS_REQUIREMENTS.md)**
- 57 formal requirements across 11 categories:
  - Ubiquitous (5): System-wide encryption, key masking, audit logging
  - Event-driven (9): API key management, session creation, agent execution
  - State-driven (4): User/session state handling
  - Optional (3): Feature flags, model selection
  - Unwanted behavior (5): Security constraints
  - Complex (3): LLM factory, agent orchestrator, encryption service
  - Performance (4): Key retrieval <100ms, session init <3s
  - Security (7): AES-256, rate limiting, access control, key rotation
  - Usability (4): <2 min config time, real-time validation
  - Data model (3): UserLLMCredentials, AgentSession extensions
  - Testing (4): Unit, integration, E2E, provider compatibility
- 4 acceptance criteria phases mapping to sprints
- Requirement traceability matrix

### 2. Architecture Documentation

**[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Section 11 Added**
- Complete BYOM architecture (1,200+ lines)
- Data model design: `UserLLMCredentials` table, `AgentSession` extensions
- Encryption architecture: AES-256 via `EncryptionService` extension
- LLM Factory pattern for multi-provider instantiation
- API endpoints specification (CRUD for credentials, validation)
- Frontend integration: Settings page, session creation modal
- Provider-specific prompt engineering strategies
- Security & compliance considerations
- Testing strategy (unit, integration, E2E)
- Monitoring & observability (metrics, dashboards, alerts)
- Migration & rollout plan (4-phase deployment)
- Future enhancements (Azure OpenAI, prompt caching, fine-tuning)

### 3. Project Documentation Updates

**[docs/PROJECT_HANDOFF.md](docs/PROJECT_HANDOFF.md) - Section 6 Added**
- Feature overview and technical impact analysis
- Implementation phases (Sprints 2.8-2.11 breakdown)
- Integration with existing systems (Data, Agent, Infrastructure)
- Dependencies & prerequisites
- Success criteria for each sprint
- Risk assessment with mitigation strategies
- Documentation requirements (developer, user, operations)

**[docs/SYSTEM_REQUIREMENTS.md](docs/SYSTEM_REQUIREMENTS.md) - Section 7 Added**
- 13 functional requirements (FR-BYOM-001 through FR-BYOM-013)
- 12 non-functional requirements:
  - Performance: <100ms key retrieval, <500ms session overhead
  - Security: AES-256 encryption, audit logging, rate limiting
  - Usability: <2 min config time, real-time validation, cost alerts
  - Backward compatibility: Existing users unaffected
- Data model requirements
- Integration requirements (EncryptionService, LLMFactory, AgentOrchestrator)
- Testing requirements (100% coverage, all providers validated)

**[ROADMAP.md](ROADMAP.md) - BYOM Added to Future Roadmap**
- Sprint 2.8-2.11 phased rollout overview
- Effort estimate: 56-72 hours total
- Links to requirements and architecture documentation

---

## 🎯 Sprint 2.8 Foundation Work

**Scope**: Database schema, encryption, basic multi-provider support  
**Effort**: 8-12 hours  
**Can be done in parallel with**: Test fixes, AWS staging deployment

### Deliverables

1. **Database Schema** (2-3 hours)
   - Alembic migration for `user_llm_credentials` table
   - Alembic migration to extend `agent_session` table
   - Fields: provider (ENUM), model_name, encrypted_api_key, encryption_key_id, is_default, is_active, timestamps

2. **Encryption Service Extension** (2-3 hours)
   - Extend `backend/app/services/encryption_service.py`
   - Add `encrypt_api_key()` and `decrypt_api_key()` methods
   - Reuse existing AES-256 Fernet pattern (same as CoinSpot credentials)
   - Unit tests with 100% coverage

3. **LLM Factory Implementation** (3-4 hours)
   - Create `backend/app/services/agent/llm_factory.py`
   - Implement `LLMFactory.create_llm(session, user_id)` method
   - Support OpenAI (`ChatOpenAI`) and Google Gemini (`ChatGoogleGenerativeAI`)
   - Fallback to system default if user has no BYOM config
   - Unit tests for factory pattern

4. **Backend API Endpoints** (2-3 hours)
   - POST `/api/v1/users/me/llm-credentials` (create credentials)
   - GET `/api/v1/users/me/llm-credentials` (list with masked keys)
   - DELETE `/api/v1/users/me/llm-credentials/{id}` (soft delete)
   - PUT `/api/v1/users/me/llm-credentials/{id}/default` (set default)
   - POST `/api/v1/users/me/llm-credentials/validate` (test API key)
   - Integration tests for all endpoints

### Dependencies

**Required before Sprint 2.8 start:**
1. ✅ Sprint 2.7 completion (COMPLETE - 97.6% pass rate)
2. 🔲 Human operator review of BYOM design (this document)
3. 🔲 Test API keys obtained:
   - OpenAI API key (for testing)
   - Google Gemini API key
   - Anthropic Claude API key (Sprint 2.9)
4. 🔲 `ENCRYPTION_KEY` environment variable configured in all environments (reuse existing)

**Optional but recommended:**
- Beta user group identified for Sprint 2.10 (5-10 users)
- Cost monitoring thresholds defined (e.g., alert if session exceeds $10)

---

## ⚡ Integration Strategy

### Parallel Development

BYOM foundation work (Sprint 2.8) can proceed in parallel with:
- **Track A (Developer A)**: Fixing remaining 16 test failures (seed data, PnL logic, etc.)
- **Track C (Developer C)**: AWS staging deployment validation
- **Track B (Developer B)**: BYOM foundation work + agent test fixes

### Minimal Disruption

**Sprint 2.8 priorities remain unchanged:**
1. **Priority 1**: Fix remaining test failures (16 tests)
2. **Priority 2**: AWS staging deployment validation
3. **Priority 3**: BYOM foundation (8-12 hours, can be done in parallel)

**Why this works:**
- BYOM foundation is self-contained (new files, no major refactoring)
- Backward compatible (no impact on existing functionality)
- Agent orchestrator refactoring deferred to Sprint 2.9
- Frontend UI deferred to Sprint 2.10

---

## 📊 Success Metrics

### Sprint 2.8 Goals
- ✅ Migration applied successfully to dev + staging databases
- ✅ Users can create/read/update/delete LLM credentials via API
- ✅ API keys encrypted/decrypted correctly (100% unit test coverage)
- ✅ OpenAI and Google Gemini LLMs instantiated successfully
- ✅ System default fallback works for users without BYOM config

### Sprint 2.9 Goals
- ✅ Agent sessions use user-configured LLM when available
- ✅ All 318 agent tests pass with OpenAI, Google, and Anthropic
- ✅ Session metadata correctly tracks provider and model
- ✅ Prompt templates optimized for each provider

### Sprint 2.10 Goals
- ✅ Users can configure LLM credentials in <2 minutes
- ✅ API key validation provides real-time feedback (<3 seconds)
- ✅ Session creation modal shows available models
- ✅ E2E tests cover full BYOM workflow

### Sprint 2.11 Goals
- ✅ Cost tracking displays accurate estimates per session
- ✅ Alerts trigger when cost limits exceeded
- ✅ Security audit finds no vulnerabilities in key handling
- ✅ 20% of active users configure BYOM within 2 weeks of launch

---

## 🛡️ Risk Management

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Prompt compatibility issues across providers | High | Medium | Provider-specific templates, A/B testing in Sprint 2.9 |
| API key security breach | Critical | Low | AES-256 encryption, audit logging, penetration testing |
| Cost overruns for users | Medium | Medium | Cost alerts, per-session limits, clear UI warnings |
| Function calling differences (Gemini/Claude vs OpenAI) | High | High | Abstraction layer in LangChain, fallback to system default |
| User confusion about API key setup | Low | Medium | Help text, video tutorials, support documentation |
| Sprint 2.8 delays from test fixes | Medium | Low | BYOM foundation is optional - can be deferred to Sprint 2.9 if needed |

### Fallback Strategy

If critical issues arise during Sprint 2.9/2.10:
1. BYOM can be feature-flagged off without impacting existing functionality
2. System default LLM remains operational for all users
3. Database schema exists but is unused (no rollback required)
4. Implementation can be paused and resumed in future sprints

---

## 📋 Next Steps for Human Operator

### 1. Review BYOM Design (30-60 minutes)
- [ ] Read [BYOM User Stories](docs/requirements/BYOM_USER_STORIES.md)
- [ ] Review [BYOM EARS Requirements](docs/requirements/BYOM_EARS_REQUIREMENTS.md)
- [ ] Review [BYOM Architecture](docs/ARCHITECTURE.md#11-bring-your-own-model-byom-architecture) (Section 11)
- [ ] Approve or request changes to design

### 2. Obtain Test API Keys (if approved)
- [ ] OpenAI API key (for testing)
  - Create at: https://platform.openai.com/api-keys
  - Recommended: $5-10 credit for testing
- [ ] Google Gemini API key
  - Create at: https://aistudio.google.com/app/apikey
  - Free tier available
- [ ] Anthropic Claude API key (Sprint 2.9)
  - Create at: https://console.anthropic.com/
  - Recommended: $5-10 credit for testing

### 3. Sprint 2.8 Decision

**Option A: Include BYOM Foundation in Sprint 2.8**
- Pros: Earliest integration, momentum maintained, minimal disruption
- Cons: Adds 8-12 hours to Sprint 2.8 (but can be parallel)
- Decision: Add BYOM foundation to Sprint 2.8 priorities (Priority 3)

**Option B: Defer BYOM to Sprint 2.9+**
- Pros: Full focus on test fixes and staging deployment
- Cons: BYOM delayed by 2 weeks, less time for testing
- Decision: Keep Sprint 2.8 focused on stability only

**Recommendation**: Option A (include foundation work)
- BYOM foundation is low-risk and self-contained
- Can be developed in parallel with test fixes
- Allows Sprint 2.9 to focus on agent refactoring (higher complexity)
- Maintains development momentum

### 4. Identify Beta Users (Optional)
- [ ] Recruit 5-10 beta users for Sprint 2.10 testing
- [ ] Users should have experience with LLM APIs (OpenAI, etc.)
- [ ] Beta period: 1 week before general availability

### 5. Approve Sprint 2.8 Start
- [ ] Review ACTION_REQUIRED_SPRINT_2.7_COMPLETE.md
- [ ] Approve Sprint 2.8 priorities:
  1. Fix remaining 16 test failures
  2. AWS staging deployment validation
  3. BYOM foundation (if approved)
- [ ] Set Sprint 2.8 start date (e.g., 2026-01-13)

---

## 📖 Key Documentation Links

### BYOM Planning Documents
- [BYOM User Stories](docs/requirements/BYOM_USER_STORIES.md)
- [BYOM EARS Requirements](docs/requirements/BYOM_EARS_REQUIREMENTS.md)
- [BYOM Architecture](docs/ARCHITECTURE.md#11-bring-your-own-model-byom-architecture)

### Project Documentation
- [Project Handoff](docs/PROJECT_HANDOFF.md#6-upcoming-feature-bring-your-own-model-byom)
- [System Requirements](docs/SYSTEM_REQUIREMENTS.md#7-bring-your-own-model-byom-requirements)
- [Roadmap](ROADMAP.md#bring-your-own-model-byom-feature-sprints-28-211)

### Sprint 2.7 Completion
- [ACTION_REQUIRED_SPRINT_2.7_COMPLETE.md](ACTION_REQUIRED_SPRINT_2.7_COMPLETE.md)
- [Sprint 2.7 Final Report](docs/archive/history/sprints/sprint-2.7/SPRINT_2.7_FINAL_REPORT.md)

---

## 🚀 Git Status

**Branch**: main  
**Last Commit**: `5c82d7b` - feat: Add BYOM (Bring Your Own Model) comprehensive planning  
**Pushed to Remote**: ✅ Yes

**Files Added:**
- `docs/requirements/BYOM_USER_STORIES.md` (created)
- `docs/requirements/BYOM_EARS_REQUIREMENTS.md` (created)

**Files Modified:**
- `docs/ARCHITECTURE.md` (Section 11 added)
- `docs/PROJECT_HANDOFF.md` (Section 6 added)
- `docs/SYSTEM_REQUIREMENTS.md` (Section 7 added)
- `ROADMAP.md` (BYOM added to Future Roadmap)

**Total Changes**: 2,117 insertions across 6 files

---

## 📞 Questions or Concerns?

If you have questions about the BYOM design or Sprint 2.8 planning:
1. Review the comprehensive architecture documentation (Section 11 of ARCHITECTURE.md)
2. Check the risk mitigation strategies (Section 6.7 of PROJECT_HANDOFF.md)
3. Review the phased implementation plan (BYOM_USER_STORIES.md)

**Key Design Decisions:**
- **Why 4 sprints?** Phased approach minimizes risk, allows for continuous validation
- **Why AES-256?** Industry standard, already used for CoinSpot credentials
- **Why LangChain?** Provider abstraction reduces complexity, supports all 3 providers
- **Why dependency injection?** Avoids global state, enables per-user LLM configuration
- **Why Sprint 2.8 foundation?** Earliest integration, parallel with test fixes, low risk

---

**Status**: READY FOR HUMAN REVIEW ✅  
**Next Action**: Human operator approval & Sprint 2.8 initialization
