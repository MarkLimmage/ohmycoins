# Oh My Coins (OMC) - Project Roadmap

**Status**: Active Development (Integration & Deployment)
**Last Updated**: 2026-01-09

## 1. Project Overview
This roadmap tracks the development of the OMC platform across its three parallel tracks:
*   **Track A**: Data Collection & Backend (The 4 Ledgers, Trading Engine)
*   **Track B**: Agentic AI (The Lab)
*   **Track C**: Infrastructure (AWS/EKS)

## 2. Active Phases

### Phase 9: Infrastructure & Production Readiness (Weeks 1-12)
*   **Owner**: Developer C
*   **Goal**: Zero-downtime, scalable EKS environment.
*   **Status**:
    *   [x] Week 1-2: VPC & Network Architecture
    *   [x] Week 3-4: EKS Cluster & Node Groups
    *   [x] Week 5-6: RDS & ElastiCache (Redis)
    *   [x] Week 7-8: Monitoring (Prometheus/Grafana) & Logging
    *   [x] Week 9-10: Staging Environment Deployment
    *   [ ] Week 11-12: Production Rollout & Secrets Management

### Integration Phase (Weeks 7-13)
*   **Owner**: All Developers
*   **Goal**: Seamless end-to-end operation.
*   **Status**:
    *   [x] Data -> Agent Handoff (DB Schema alignment)
    *   [ ] Agent -> Trading Handoff (Artifact promotion)
    *   [ ] System-wide Integration Tests (Staging)

## 3. Completed Phases

### Phase 2.5: Comprehensive Data Collection
*   **Owner**: Developer A
*   **Outcome**: Fully operational 4-Ledger collectors (Glass, Human, Catalyst, Exchange).

### Phase 3: Agentic Data Science System
*   **Owner**: Developer B
*   **Outcome**: Autonomous ReAct agents capable of planning, analysis, and model training.

## 4. Future Roadmap

### Phase 4: Strategy Execution (The Floor)
*   **Planned Start**: Week 14
*   **Scope**: Live paper trading, risk management enforcement, and gradual capital deployment.

### Phase 5: Dashboard & Analytics
*   **Planned Start**: Week 16
*   **Scope**: Advanced visualization for Agent decisions and P&L tracking.
