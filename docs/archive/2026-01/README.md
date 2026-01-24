# Archived Documentation - January 2026

This folder contains documentation that has been superseded or consolidated into newer documents as part of the Documentation Uplift initiative (Sprint 2.11).

## Archived Files

### BYOM_USER_STORIES.md
- **Archived Date**: 2026-01-24
- **Reason**: Content consolidated into `/docs/USER_JOURNEYS.md` (Journey 2: BYOM Setup)
- **Original Location**: `/docs/requirements/BYOM_USER_STORIES.md`
- **Superseded By**: `/docs/USER_JOURNEYS.md`

The original BYOM user stories (595 lines) have been integrated into the comprehensive USER_JOURNEYS document, which now serves as the single source of truth for all user interaction flows across the Oh My Coins platform. The new document includes:
- Journey 2: BYOM Setup (6 detailed steps)
- Links to E2E tests (`byom_setup.spec.ts`)
- UI component mappings
- Backend requirement references (REQ-BYOM-001 through REQ-BYOM-004)

### implementation-details/COINSPOT_WEB_SCRAPING_IMPLEMENTATION.md
- **Archived Date**: 2026-01-24
- **Reason**: Implementation-specific details belong in service README (`backend/app/services/collectors/`)
- **Original Location**: `/docs/COINSPOT_WEB_SCRAPING_IMPLEMENTATION.md`
- **Note**: Per Documentation Strategy Tier 2, feature-specific technical specs should be co-located with code

### implementation-details/RATE_LIMITING.md
- **Archived Date**: 2026-01-24
- **Reason**: Rate limiting strategy should be documented in ARCHITECTURE.md or API service README
- **Original Location**: `/docs/RATE_LIMITING.md`
- **Note**: Too granular for top-level docs, should be in service documentation

## Archive Policy

**When to Archive**:
- Content duplicated in newer, more comprehensive documents
- Documentation no longer reflects current system architecture
- Requirements superseded by newer specifications
- Historical reference needed but not actively maintained

**Retention Period**: 2 years (documents archived before 2024-01-24 may be permanently deleted)

**Related Documents**:
- `/docs/DOCUMENTATION_STRATEGY.md` - Archive policy details
- `/docs/USER_JOURNEYS.md` - Current user journey documentation
- `/docs/SYSTEM_REQUIREMENTS.md` - Current requirements documentation

---

**Last Updated**: 2026-01-24  
**Maintained By**: Documentation Working Group
