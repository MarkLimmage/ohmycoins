# Parallel Development Guide - Oh My Coins (OMC!)

**Last Updated:** 2025-11-20  
**Purpose:** Coordinate parallel development for next sprint cycle
**Context:** Phase 2.5 and Infrastructure (Weeks 1-6) complete. Phase 3 at 60% completion.

---

## Sprint Status Summary

### ✅ Completed Work (Current Sprint)
| Developer | Phase | Status | Key Deliverables |
|-----------|-------|--------|------------------|
| **Developer A** | Phase 2.5 Data Collection | ✅ 100% | 5 collectors, quality monitoring, 105+ tests |
| **Developer B** | Phase 3 Agentic (Weeks 1-8) | ✅ 60% | LangGraph, 4 agents, ReAct loop, 109+ tests |
| **Developer C** | Phase 9 Infrastructure (Weeks 1-6) | ✅ 100% | AWS staging deployed, EKS cluster, 8 test suites |

### 🎯 Next Sprint Priorities

| Track A | Track B | Track C |
|---------|---------|---------|
| **Phase 6: Trading System** | **Phase 3: Complete Agentic** | **Application Deployment** |
| Coinspot trading API, execution engine | HiTL features, reporting, finalization | Deploy to staging, monitoring stack |
| **Timeline:** 6-8 weeks | **Timeline:** 4 weeks | **Timeline:** 4-6 weeks |
| **Developer:** Developer A | **Developer:** Developer B | **Developer:** Developer C |

**Key Insight:** All three tracks are independent and can proceed in parallel. Integration testing in Week 4 and Week 8.

---

## Current Sprint Plan (Next 8 Weeks)

### Week 1-2: Parallel Independent Development

**Developer A: Phase 6 - Trading Integration (Weeks 1-2)**
- [ ] Implement Coinspot trading API client (buy/sell)
- [ ] Add order execution service with queue
- [ ] Implement position management
- [ ] Write comprehensive unit tests
- **Directory:** `backend/app/services/trading/`
- **No conflicts with:** Developer B or C

**Developer B: Phase 3 - Human-in-the-Loop (Weeks 9-10)**
- [ ] Implement clarification system
- [ ] Implement choice presentation
- [ ] Implement user override mechanism
- [ ] Add approval gates
- **Directory:** `backend/app/services/agent/`
- **No conflicts with:** Developer A or C

**Developer C: Application Deployment (Weeks 7-8)**
- [ ] Create Kubernetes manifests for backend
- [ ] Set up Helm charts
- [ ] Deploy Phase 2.5 collectors to staging
- [ ] Deploy Phase 3 agentic system to staging
- **Directory:** `infrastructure/kubernetes/`
- **No conflicts with:** Developer A or B

### Week 3-4: Continued Parallel + Integration Point

**Developer A: Phase 6 - Execution Engine (Weeks 3-4)**
- [ ] Create live trading executor
- [ ] Implement execution scheduler
- [ ] Add safety mechanisms
- [ ] Implement trade recording
- **Integration:** None required yet

**Developer B: Phase 3 - Reporting (Weeks 11-12)**
- [ ] Implement ReportingAgent
- [ ] Implement artifact management
- [ ] Complete integration testing
- [ ] Finalize documentation
- **Integration:** Week 4 - Phase 3 complete, deploy to staging

**Developer C: Monitoring Stack (Weeks 9-10)**
- [ ] Deploy Prometheus and Grafana
- [ ] Configure Loki/Promtail
- [ ] Create application dashboards
- [ ] Set up alerting rules
- **Integration:** Week 4 - Test Phase 3 deployment

### Week 5-6: Developer A Continues, B & C Support Integration

**Developer A: Phase 6 - P&L System (Weeks 5-6)**
- [ ] Implement P&L engine
- [ ] Create P&L APIs
- [ ] Implement trade history tracking
- [ ] Add comprehensive testing

**Developer B: Phase 3 Integration Support**
- [ ] Support integration testing on staging
- [ ] Fix any issues found in staging deployment
- [ ] Optimize performance based on staging metrics
- [ ] Begin planning Phase 5 (Algorithm Promotion)

**Developer C: Production Preparation**
- [ ] Configure DNS and SSL certificates
- [ ] Enable WAF on ALB
- [ ] Set up backup policies
- [ ] Implement AWS Config rules

### Week 7-8: Integration Testing & Planning

**All Developers: Integration Testing**
- [ ] End-to-end testing on staging
- [ ] Performance testing
- [ ] Security testing
- [ ] Documentation review

**Planning:**
- [ ] Review Phase 6 progress (Trading System)
- [ ] Plan Phase 5 (Algorithm Promotion) - Developer A
- [ ] Plan Phase 7 (Floor Dashboard) - Developer B  
- [ ] Plan Production Deployment - Developer C

---

- Week 3: Reddit API integration

**Files Created:**
- `backend/app/services/collectors/human/reddit.py`
- `backend/tests/services/collectors/human/test_reddit.py`

**No Conflicts With:** Any other work stream

---

#### Stream 3: LangGraph Foundation
**Owner:** Developer B  
**Duration:** 2 weeks  
**Dependencies:** None (can use existing price data)

- Week 1-2: Install LangGraph, configure, create basic workflow

**Files Modified:**
- `backend/requirements.txt`
- `backend/app/services/agent/orchestrator.py`
- `.env` (add OpenAI/Anthropic API keys)

**Potential Conflicts:** None (working in agent/ directory)

---

#### Stream 4: AWS Infrastructure
**Owner:** Developer C or DevOps  
**Duration:** 4-8 weeks  
**Dependencies:** None (can be designed and implemented independently)

- Weeks 1-2: Design and planning
- Weeks 3-6: Terraform/CloudFormation implementation
- Weeks 7-8: CI/CD enhancements

**Files Created:**
- `infrastructure/terraform/` (or `infrastructure/cloudformation/`)
- `.github/workflows/deploy-aws.yml`

**No Conflicts With:** Any development work (infrastructure is separate)

---

### Level 2: Low-Coordination Parallel Work (Minimal Sync)

These require occasional sync-ups but can mostly work independently:

#### Track A + Track B: Data Collection + Agentic System
**Coordination Points:**
- **Week 0**: Agree on data access APIs (already exist via SQLModel)
- **Week 4**: Dev A provides Phase 2.5 collectors operational
- **Week 6**: Integration testing - Dev B starts using Phase 2.5 data

**Why It Works:**
- Phase 3 can start with existing price data
- Phase 2.5 collectors add new tables, don't modify existing ones
- Agent tools can be stubbed out and filled in later

## Coordination Strategies for Next Sprint

### Strategy 1: Weekly Sync Meetings (1 hour every Monday)
**Participants:** All 3 developers + project manager  
**Format:**
- Review previous week's progress (15 min)
- Demo completed features (20 min)
- Identify integration points and blockers (15 min)
- Plan upcoming week coordination (10 min)

**Key Topics:**
- Week 1: Kickoff, confirm independent tracks
- Week 2: Progress check, identify any early issues
- Week 4: Integration planning (Phase 3 → Staging)
- Week 6: Mid-sprint review, adjust plans if needed
- Week 8: Sprint retrospective, plan next sprint

### Strategy 2: Daily Async Standups (Slack/Discord)
**When:** Every morning by 10 AM  
**Format:** Each developer posts:
- ✅ Completed yesterday
- 🔨 Working on today
- 🚧 Any blockers or questions

**Benefits:** 
- Minimal overhead (5 min per person)
- Asynchronous (respects different schedules)
- Creates written record
- Quick identification of conflicts

### Strategy 3: Integration Testing Windows
**Week 4 Integration (3 days)**
- **Tuesday:** Developer C deploys Phase 3 to staging
- **Wednesday:** Developer B tests Phase 3 on staging, Developer C monitors
- **Thursday:** Fix any issues found, re-test

**Week 8 Integration (5 days)**
- **Monday-Tuesday:** Developer C deploys all applications to staging
- **Wednesday:** All developers run end-to-end integration tests
- **Thursday-Friday:** Fix issues, optimize performance, final testing

---

## Developer Work Boundaries (Avoid Conflicts)

### Developer A (Trading System)
**Primary Directories:**
- `backend/app/services/trading/` (NEW - exclusive ownership)
- `backend/app/api/v1/floor/` (NEW - trading endpoints)
- `backend/tests/services/trading/` (NEW - trading tests)

**Shared Files:**
- `backend/app/models.py` - Coordinate if adding trading-related models
- `backend/requirements.txt` - Coordinate if adding dependencies

**No Conflicts Expected With:** Developer B (agent/) or C (infrastructure/)

### Developer B (Agentic Completion)
**Primary Directories:**
- `backend/app/services/agent/` (exclusive ownership)
- `backend/app/api/v1/lab/` (agent endpoints)
- `backend/tests/services/agent/` (agent tests)

**Shared Files:**
- None expected (all agent code is isolated)

**No Conflicts Expected With:** Developer A (trading/) or C (infrastructure/)

### Developer C (Infrastructure & Deployment)
**Primary Directories:**
- `infrastructure/kubernetes/` (NEW - exclusive ownership)
- `infrastructure/terraform/` (exclusive ownership)
- `.github/workflows/` (deployment workflows)

**Shared Files:**
- `docker-compose.yml` - Coordinate if modifying services
- `Dockerfile` - Inform if changing base images

**No Conflicts Expected With:** Developer A (trading/) or B (agent/)

---

## Risk Mitigation Strategies

### Risk 1: Integration Delays
**Symptom:** Phase 3 deployment to staging takes longer than expected  
**Mitigation:**
- Start deployment preparation in Week 3 (early)
- Have Developer C create deployment runbook
- Test deployment process in Week 3 (dry run)
- Buffer time in Week 4 for fixes

**Owner:** Developer C with support from Developer B

### Risk 2: Trading API Changes
**Symptom:** Coinspot API changes, breaks trading implementation  
**Mitigation:**
- Implement comprehensive error handling
- Add API version detection
- Create fallback mechanisms
- Monitor Coinspot API announcements

**Owner:** Developer A

### Risk 3: Resource Constraints on Staging
**Symptom:** Staging environment runs out of resources with all apps deployed  
**Mitigation:**
- Monitor staging resource usage from Week 1
- Scale up staging resources if needed (increase RDS, Redis sizes)
- Optimize application resource requests
- Consider deploying only essential services initially

**Owner:** Developer C

### Risk 4: Phase 3 Completion Delays
**Symptom:** HiTL or Reporting features take longer than 4 weeks  
**Mitigation:**
- Prioritize HiTL features by importance
- Consider phased rollout (basic HiTL first)
- Developer C or A can assist with testing
- Extend timeline if needed (acceptable)

**Owner:** Developer B

### Risk 5: Testing Gaps
**Symptom:** Integration tests reveal major issues in Week 8  
**Mitigation:**
- Continuous integration testing throughout sprint
- Developer C runs health checks on staging weekly
- Each developer runs their tests before integration windows
- Have rollback plan for staging deployments

**Owner:** All developers

---

## Success Metrics for This Sprint

### Process Metrics
- [ ] All developers complete assigned tasks by Week 8
- [ ] Zero merge conflicts requiring >1 hour to resolve
- [ ] Integration testing windows complete on schedule
- [ ] All 3 developers attend weekly sync meetings
- [ ] Daily standups posted >90% of days

### Outcome Metrics
- [ ] Phase 3 (Agentic) reaches 100% completion
- [ ] Phase 6 (Trading) reaches 75% completion (6 of 8 weeks)
- [ ] All applications deployed to staging environment
- [ ] Monitoring stack operational on staging
- [ ] 250+ total tests passing (current 214+ plus new tests)
- [ ] Zero critical bugs in staging

### Quality Metrics
- [ ] Test coverage maintained >80% for new code
- [ ] All code reviewed before merge
- [ ] Documentation updated for new features
- [ ] Security scans passing (no critical vulnerabilities)
- [ ] Performance benchmarks met on staging

---

## Coordination Strategies

### Strategy 1: Daily Standups (15 minutes)
**When:** Every morning  
**Participants:** All active developers  
**Format:**
- What did I complete yesterday?
- What am I working on today?
- Any blockers or dependencies?

**Focus:** Identify integration points early

---

### Strategy 2: Weekly Integration Reviews (1 hour)
**When:** End of each week  
**Participants:** All developers + tech lead  
**Format:**
- Demo completed work
- Review integration points
- Plan next week's coordination
- Identify risks

**Deliverables:** 
- Updated integration plan
- Risk mitigation actions

---

### Strategy 3: Integration Sprints (2-3 days)
**When:** Week 6, Week 12  
**Participants:** All developers  
**Format:**
- Pause independent work
- Focus on integration testing
- Resolve conflicts
- End-to-end testing

**Deliverables:**
- Integrated system working end-to-end
- Integration test suite passing

---

## Developer Assignment Recommendations

### 2-Developer Team (Recommended)

**Developer A: Data Specialist**
- **Skills:** Python, web scraping, APIs, databases
- **Track:** Phase 2.5 Data Collection
- **Timeline:** 4-6 weeks primary, then support Phase 3 integration
- **Workload:** 60% Phase 2.5, 20% integration, 20% Phase 6 prep

**Developer B: AI/ML Specialist**
- **Skills:** Python, LangChain, machine learning, scikit-learn
- **Track:** Phase 3 Agentic System
- **Timeline:** 12-14 weeks
- **Workload:** 90% Phase 3, 10% integration

**Sync Points:**
- Week 0: Architecture alignment
- Week 4: Phase 2.5 data ready for use
- Week 6-7: Integration sprint
- Week 12: Final integration testing

---

### 3-Developer Team (Optimal)

**Developer A: Data Specialist**
- Same as above

**Developer B: AI/ML Specialist**
- Same as above

**Developer C: DevOps/Infrastructure**
- **Skills:** AWS, Terraform, CI/CD, Docker, Kubernetes
- **Track:** Phase 9 Infrastructure
- **Timeline:** 4-8 weeks (can extend to support both tracks)
- **Workload:** 60% infrastructure, 40% support dev/test environments

**Benefits:**
- Production infrastructure ready when features complete
- Better dev/test environments
- Deployment expertise available throughout

---

### 4-Developer Team (Maximum Parallelization)

**Team 1: Data Infrastructure (2 developers)**
- Developer A1: Catalyst + Human Ledgers
- Developer A2: Glass + Exchange Ledgers (enhancement)
- **Timeline:** 2-3 weeks

**Team 2: Agentic System (2 developers)**
- Developer B1: Data agents + Orchestration
- Developer B2: Modeling agents + HiTL
- **Timeline:** 8-10 weeks

**Outcome:**
- Phase 2.5 complete in 3 weeks (vs. 6 weeks)
- Phase 3 complete in 10 weeks (vs. 14 weeks)
- Total timeline: 10 weeks (vs. 20 weeks sequential)

---

## Risk Mitigation for Parallel Development

### Risk 1: Integration Conflicts
**Symptom:** Different developers modify same files  
**Mitigation:**
- Clear ownership boundaries (directories)
- Feature branches for all work
- Frequent small merges (daily if possible)
- Code review before merge

**Example Boundaries:**
- Developer A: `backend/app/services/collectors/*`
- Developer B: `backend/app/services/agent/*`
- Shared: `backend/app/models.py` (coordinate changes)

---

### Risk 2: API Contract Changes
**Symptom:** Dev A changes data schema, breaks Dev B's code  
**Mitigation:**
- Define API contracts upfront (Week 0)
- Use feature flags for schema changes
- Version APIs if breaking changes needed
- Communication before any schema changes

**Contract Example:**
```python
# Agreed API for Phase 2.5 data access
def get_catalyst_events(start_date, end_date, event_type=None):
    """Returns list of CatalystEvent objects"""
    
def get_sentiment_data(start_date, end_date, platform=None):
    """Returns list of SentimentData objects"""
```

---

### Risk 3: Environment Conflicts
**Symptom:** Different dependencies cause conflicts  
**Mitigation:**
- Use Docker for development (consistent environments)
- Pin dependency versions in requirements.txt
- Document any new dependencies immediately
- Test in clean environment before merge

---

### Risk 4: Knowledge Silos
**Symptom:** Only one person understands their subsystem  
**Mitigation:**
- Code reviews by other developers
- Pair programming on complex features
- Regular demos and knowledge sharing
- Documentation as you go (not at end)

**Knowledge Sharing Activities:**
- Weekly "teach me" sessions (30 min)
- Code walkthrough during standups
- Shared documentation (inline comments + README)

---

### Risk 5: Testing Gaps
**Symptom:** Integration issues not found until late  
**Mitigation:**
- Unit tests required for all PRs
- Integration tests in CI/CD pipeline
- Regular integration testing sprints
- Mock interfaces for external dependencies

**Testing Strategy:**
- Developer A: Unit tests for collectors
- Developer B: Unit tests for agents
- Both: Integration tests for agent + data workflows
- CI/CD: Automated test suite runs on every commit

---

## Communication Tools

### Recommended Setup

**Code Collaboration:**
- GitHub for version control
- Feature branches for all work
- Pull requests with code review
- CI/CD runs tests automatically

**Communication:**
- Slack/Discord for quick questions
- GitHub Issues for task tracking
- GitHub Projects for sprint planning
- Zoom/Meet for standups and reviews

**Documentation:**
- README.md in each major directory
- Inline code comments for complex logic
- Architecture Decision Records (ADRs) for major decisions
- Confluence/Notion for design docs

---

## Success Metrics for Parallel Development

### Process Metrics
- [ ] Zero merge conflicts requiring more than 30 minutes to resolve
- [ ] All PRs reviewed within 24 hours
- [ ] CI/CD tests passing >95% of time
- [ ] Integration sprints complete all planned scenarios
- [ ] No developer blocked for more than 4 hours waiting for dependency

### Outcome Metrics
- [ ] Phase 2.5 complete in 4-6 weeks (vs. 6-8 sequential)
- [ ] Phase 3 foundation complete in 12-14 weeks (vs. 16-18 sequential)
- [ ] Total timeline 12-16 weeks (vs. 24-32 sequential)
- [ ] 40-50% timeline reduction achieved
- [ ] Zero critical integration bugs in production

---

## Immediate Action Plan for Next Sprint

### Monday (Week 1, Day 1): Sprint Kickoff
**All Developers - 2 hour meeting**

**Agenda:**
1. Review completed work from previous sprint (30 min)
   - Developer A: Phase 2.5 demo
   - Developer B: Phase 3 (weeks 1-8) demo
   - Developer C: Staging environment walkthrough
2. Review this updated parallel development guide (30 min)
3. Confirm work assignments and timelines (30 min)
4. Identify potential risks and mitigation strategies (15 min)
5. Set up communication channels (Slack, standup schedule) (15 min)

**Deliverables:**
- [ ] All developers confirm their assignments
- [ ] Integration testing dates confirmed (Week 4, Week 8)
- [ ] Communication channels set up
- [ ] First daily standup scheduled

### Week 1, Days 2-5: Begin Independent Development

**Developer A:**
- [ ] Set up trading service directory structure
- [ ] Research Coinspot trading API endpoints
- [ ] Implement basic trading client skeleton
- [ ] Write initial unit tests

**Developer B:**
- [ ] Review HiTL requirements from Phase 3 plan
- [ ] Design clarification system architecture
- [ ] Implement basic clarification dialogue
- [ ] Write initial unit tests

**Developer C:**
- [ ] Create Kubernetes manifests directory
- [ ] Research Helm chart structure for FastAPI apps
- [ ] Create basic deployment manifests
- [ ] Test deployment to staging (dry run)

**Friday Sync:**
- [ ] Progress review
- [ ] Identify any early blockers
- [ ] Adjust plans if needed

### Week 2: Continue Development + Early Integration Prep

**All Developers:**
- [ ] Continue primary work tracks
- [ ] Submit PRs for code review
- [ ] Update documentation

**Developer C (Additional):**
- [ ] Prepare Phase 3 deployment runbook
- [ ] Test deployment process (Week 3 preparation)
- [ ] Monitor staging resource usage

### Week 3: Prepare for Integration

**Developer B:**
- [ ] Complete HiTL basic features
- [ ] Prepare Phase 3 for staging deployment
- [ ] Document deployment requirements

**Developer C:**
- [ ] Deploy Phase 3 to staging (end of week)
- [ ] Verify deployment health
- [ ] Monitor performance

**Developer A:**
- [ ] Continue trading system development
- [ ] Independent track (no integration needed)

### Week 4: Integration Testing Window

**All Developers:**
- [ ] Integration testing on staging
- [ ] Fix identified issues
- [ ] Performance optimization
- [ ] Documentation updates

---

## Conclusion

### Sprint Summary

**Current Status (November 20, 2025):**
- ✅ Phase 2.5 (Data Collection): 100% complete
- ✅ Phase 3 (Agentic): 60% complete (Weeks 1-8 done)
- ✅ Phase 9 (Infrastructure): Weeks 1-6 complete, staging deployed
- 🎯 **Ready for next sprint with 3 independent parallel tracks**

### Next Sprint Goals (8 Weeks)

**By End of Sprint:**
- ✅ Phase 3 Agentic System: 100% complete
- 🎯 Phase 6 Trading System: 75% complete (6 of 8 weeks)
- ✅ All applications deployed to staging
- ✅ Monitoring stack operational
- ✅ Ready for production deployment preparation

### Timeline Efficiency

**With Parallel Development:**
- Next Sprint: 8 weeks
- Work completed: 18 weeks equivalent (4 weeks Phase 3 + 6 weeks Phase 6 + 8 weeks Infrastructure)
- **Time savings: 55% reduction** (8 weeks instead of 18 weeks sequential)

**Cumulative Project Progress:**
- Previous sprints: Significant foundation laid
- Next sprint: All major features complete
- Following sprint: Production deployment and polish
- **Total timeline: Significantly reduced through effective parallelization**

### Critical Success Factors

1. ✅ **Clear Ownership:** Each developer has exclusive directories
2. ✅ **Staging Environment:** Available for testing
3. ✅ **Communication Plan:** Weekly syncs + daily standups
4. ✅ **Integration Windows:** Scheduled and planned
5. ✅ **Flexible Timeline:** Can adjust if needed

### Next Actions

**Immediate (This Week):**
1. [ ] Project manager schedules sprint kickoff meeting
2. [ ] All developers review this updated guide
3. [ ] Set up communication channels
4. [ ] Confirm work assignments

**Week 1:**
1. [ ] Sprint kickoff meeting (Monday)
2. [ ] Begin independent development (Tuesday-Friday)
3. [ ] First weekly sync (Friday)

**Ongoing:**
1. [ ] Daily async standups
2. [ ] Weekly sync meetings
3. [ ] Code reviews
4. [ ] Documentation updates

---

**Last Updated:** 2025-11-20  
**Next Review:** End of Week 4 (Integration Testing Window)  
**Contact:** Project Manager for questions or concerns
