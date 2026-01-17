# Documentation Organization Plan - Sprint 2.9

**Date:** January 17, 2026  
**Status:** Ready to Execute

## Issues Identified

### Root Directory Clutter (7 markdown files)
1. ❌ **ACTION_REQUIRED_SPRINT_2.7_COMPLETE.md** - Obsolete (Sprint 2.7 complete)
2. ❌ **AWS_STAGING_DEPLOYMENT_COMPLETE.md** - Obsolete (deployment done Jan 11)
3. ❌ **DEPLOYMENT_STATUS_2026-01-11.md** - Obsolete (point-in-time status)
4. ❌ **SPRINT_INITIALIZATION.md** - Obsolete (Sprint 2.7 initialization, now archived)
5. ✅ **CURRENT_SPRINT.md** - KEEP (active sprint tracking)
6. ✅ **ROADMAP.md** - KEEP (project roadmap)
7. ✅ **README.md** - KEEP (project README)

### Archive Structure Issues
- Sprints properly organized in `docs/archive/history/sprints/`
- General archive in `docs/archive/history/` needs review
- Decision archive in `docs/archive/decisions/` looks good

## Reorganization Actions

### Action 1: Archive Sprint 2.7 Completion Documents
Move to: `docs/archive/history/sprints/sprint-2.7/`
- ACTION_REQUIRED_SPRINT_2.7_COMPLETE.md
- SPRINT_INITIALIZATION.md (Sprint 2.7 init doc)

### Action 2: Archive Deployment Status Documents
Move to: `docs/archive/history/deployments/`
- AWS_STAGING_DEPLOYMENT_COMPLETE.md
- DEPLOYMENT_STATUS_2026-01-11.md

### Action 3: Update Active Documentation
Keep in root:
- CURRENT_SPRINT.md (updated to Sprint 2.9)
- ROADMAP.md (updated with Sprint 2.8 results)
- README.md (project overview)

### Action 4: Verify docs/ Structure
Ensure proper organization:
- docs/ARCHITECTURE.md ✅
- docs/TESTING.md ✅
- docs/PROJECT_HANDOFF.md ✅
- docs/DEPLOYMENT_STATUS.md ✅ (current status, not point-in-time)
- docs/SECRETS_MANAGEMENT.md ✅
- docs/SSL_DNS_AUTOMATION.md ✅
- docs/SYSTEM_REQUIREMENTS.md ✅
- docs/requirements/ ✅
- docs/archive/ ✅

## Target Structure

```
/home/mark/omc/ohmycoins/
├── README.md                          ✅ Keep
├── ROADMAP.md                         ✅ Keep (updated)
├── CURRENT_SPRINT.md                  ✅ Keep (Sprint 2.9)
├── docs/
│   ├── ARCHITECTURE.md                ✅ Active
│   ├── TESTING.md                     ✅ Active
│   ├── PROJECT_HANDOFF.md             ✅ Active
│   ├── DEPLOYMENT_STATUS.md           ✅ Active (current)
│   ├── SECRETS_MANAGEMENT.md          ✅ Active
│   ├── SSL_DNS_AUTOMATION.md          ✅ Active
│   ├── SYSTEM_REQUIREMENTS.md         ✅ Active
│   ├── requirements/
│   │   ├── BYOM_EARS_REQUIREMENTS.md  ✅ Active
│   │   └── BYOM_USER_STORIES.md       ✅ Active
│   └── archive/
│       ├── decisions/                 ✅ Good
│       └── history/
│           ├── sprints/
│           │   ├── sprint-2.6/        ✅ Archived
│           │   ├── sprint-2.7/        📁 Add completion docs
│           │   └── sprint-2.8/        ✅ Archived
│           └── deployments/           📁 Create new
│               ├── AWS_STAGING_DEPLOYMENT_COMPLETE.md
│               └── DEPLOYMENT_STATUS_2026-01-11.md
└── infrastructure/terraform/          ✅ Good (deployment guides)
```

## Benefits

1. **Cleaner Root Directory:** Only 3 active files (README, ROADMAP, CURRENT_SPRINT)
2. **Better Archive Organization:** Deployment history separate from sprint history
3. **Easier Navigation:** Clear separation between active docs and historical records
4. **Sprint Pattern Established:** Each sprint has complete archive in its own directory

## Execution Order

1. Create `docs/archive/history/deployments/` directory
2. Move deployment documents
3. Move Sprint 2.7 completion documents
4. Verify all references/links still work
5. Update this cleanup plan to mark complete
