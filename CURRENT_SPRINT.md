# Current Sprint - Sprint 2.23 (The Guard)

**Status:** 🛡️ ACTIVE
**Date Started:** May 3, 2026
**Date Ends:** May 16, 2026
**Duration:** 2 Weeks
**Previous Sprint:** Sprint 2.22 - Complete ✅
**Focus:** Risk Management & Safety First

---

## 🎯 Sprint 2.23 Objectives

**🚨 CRITICAL PIVOT**: Infrastructure migration to Local Server (192.168.0.241).
See [Migration Plan](docs/sprints/PLAN_LOCAL_MIGRATION.md) for immediate tasks.

### Primary Goal
Implement "The Guard," a hard-coded, non-AI safety layer that validates every order against strict risk parameters (Max Drawdown, Position Size, Daily Loss Limit) *before* execution.
**Simultaneously**: Deploy this functionality to the new local server infrastructure.

### Success Criteria
- [ ] **RiskCheckService**: Service active and intercepting all trade requests.
- [ ] **Circuit Breakers**: "Kill Switch" functionality triggered automatically on drawdown > 5%.
- [ ] **Audit Logging**: Immutable Ledger of all attempts (Accepted/Rejected).
- [ ] **Onboarding Wizard**: Secure flow for users to set their API keys and Risk Limits.

### Sprint Metrics
| Category | Target | Result |
|----------|--------|--------|
| Latency Impact | < 50ms | TBD |
| False Positives | 0% | TBD |
| Test Coverage | 100% (Safety Critical) | TBD |

**Track Status:**
- ⚪ **Track D** (Dockmaster): Pending
- ⚪ **Track A** (Risk Engine): Pending
- ⚪ **Track B** (UI Control): Pending

---

## 📦 Deliverables

- `RiskCheckService` (Middleware)
- `AuditLog` table and service
- `OnboardingWizard` (Frontend Component)
- `KillSwitch` implementation

---

**Last Updated:** May 3, 2026
