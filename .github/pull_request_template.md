## Description
<!-- What does this PR do? Explain the "why" behind the change. -->

## Requirements Addressed
**Primary**: REQ-XX-YYY  
**Secondary**: REQ-XX-ZZZ (if applicable)

<!-- Link to SYSTEM_REQUIREMENTS.md section -->
**SYSTEM_REQUIREMENTS.md Reference**: Section X.Y

---

## Documentation Updates ✅

### Tier 1: System Core
- [ ] SYSTEM_REQUIREMENTS.md updated (if new requirement added)
- [ ] USER_JOURNEYS.md updated (if workflow changed)
- [ ] API_CONTRACTS.md updated (if API pattern changed)
- [ ] N/A: No Tier 1 changes

### Tier 2: Feature Documentation
- [ ] Service README.md updated (`backend/app/services/[service]/README.md`)
- [ ] Feature README.md updated (`frontend/src/features/[feature]/README.md`)
- [ ] Architecture diagram added/updated (Mermaid.js)
- [ ] N/A: No Tier 2 changes

### Tier 3: UI/UX Documentation
- [ ] Storybook story created/updated
- [ ] Component documented in feature README.md
- [ ] DESIGN_SYSTEM.md updated (if new component pattern)
- [ ] N/A: No UI changes

### Tier 4: Auto-Generated Documentation
- [ ] Pydantic models have `Field(description="...")` for all new fields
- [ ] OpenAPI `/docs` validates correctly (check http://localhost:8000/docs)
- [ ] N/A: No API changes

---

## Testing ✅

### Test Coverage
- [ ] Unit tests added/updated (`pytest` or `vitest`)
- [ ] Integration tests added (if API changes)
- [ ] E2E tests added (if USER_JOURNEYS.md changed)
  - **E2E Test File**: `tests/e2e/[test_name].spec.ts`
- [ ] N/A: Documentation-only PR

### Test Results
```
pytest: X/X passed
vitest: X/X passed  
playwright: X/X passed
```

### Code Quality
- [ ] Code follows style guide (`black`, `prettier`, `biome`)
- [ ] No new linting errors (`ruff`, `eslint`)
- [ ] Type checking passes (`mypy`, `tsc`)

### Accessibility (Frontend only)
- [ ] ARIA labels on interactive elements
- [ ] Keyboard navigation tested (Tab, Enter, Esc)
- [ ] axe-core accessibility audit passed
- [ ] REQ-UX-001 table view toggle implemented (if chart component)
- [ ] N/A: No UI changes

---

## Documentation Gate Validation

**Automated Checks** (will run via GitHub Actions):
- ⏳ Requirement traceability (REQ-XX-YYY exists in SYSTEM_REQUIREMENTS.md)
- ⏳ Tier 2 documentation updated (service/feature README.md)
- ⏳ Tier 4 OpenAPI schemas generated (if backend changes)
- ⏳ USER_JOURNEYS → E2E test linkage validated (if workflow changed)

**Manual Validation** (reviewer):
- [ ] DOCS_GOVERNANCE.md agent persona constraints followed
- [ ] Commits follow atomic pattern: docs → implementation → tests
- [ ] No documentation drift (Tier 1 aligns with implementation)

**Gate Status**: 🟡 PENDING / 🟢 APPROVED / 🔴 BLOCKED

---

## Agent Persona (for AI-driven development)

**Agent Role**: The [Architect | Feature Developer | UI/UX Agent | Quality Agent]  
**Tiered Access**:
- **READ**: [List Tier 1-3 docs read]
- **WRITE**: [List Tier 2-4 docs written]

**Constraints Followed**:
- [ ] Used EARS syntax for requirements (if Tier 1 changes)
- [ ] Followed API_CONTRACTS.md patterns (if API changes)
- [ ] Followed DESIGN_SYSTEM.md specs (if UI changes)
- [ ] No custom CSS (Tailwind only, if frontend)

---

## Screenshots / Demo (if UI changes)
<!-- Add before/after screenshots, Storybook links, or video demo -->

**Storybook Link**: http://localhost:6006/?path=/story/[component-name]

---

## Security Checklist
- [ ] No plaintext secrets or API keys in code
- [ ] API keys masked in logs (if credential handling)
- [ ] Input validation added (if user-facing inputs)
- [ ] SQL injection prevention (if database queries)
- [ ] XSS prevention (if rendering user content)
- [ ] N/A: No security-sensitive changes

---

## Deployment Notes
<!-- Any special deployment considerations? Database migrations? Environment variables? -->

**Database Migrations**: Yes / No  
- [ ] Alembic migration script created (`alembic revision --autogenerate`)
- [ ] Migration tested locally

**Environment Variables**: Yes / No  
- [ ] New variables documented in `.env.template`
- [ ] Variables added to AWS Secrets Manager (production)

**Breaking Changes**: Yes / No  
- [ ] Migration guide added to PR description
- [ ] Backward compatibility maintained

---

## Reviewer Checklist

- [ ] Code review complete (logic, style, best practices)
- [ ] All tests pass (CI/CD green)
- [ ] Documentation gates passed (see above)
- [ ] Security checklist reviewed
- [ ] No merge conflicts with main
- [ ] PR title follows convention: `feat(module): description` or `docs(module): description`

---

## Related Issues / PRs
<!-- Link to related tickets, issues, or PRs -->

Closes: #XXX  
Related: #YYY

---

## Post-Merge Actions
- [ ] Update CURRENT_SPRINT.md progress tracker
- [ ] Notify stakeholders (if major feature)
- [ ] Update ROADMAP.md (if milestone completed)
