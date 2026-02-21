# Current Sprint - Sprint 2.29 (Collector UI & Signal Standardization)

**Status:** 🚀 ACTIVE
**Overall Goal:** Complete the **Collector Management System** by finalizing the Admin UI (Dynamic Forms & Dashboard) and standardizing all collector outputs into a unified **Signal Pipeline**.
**SIM**: [docs/sprints/SIM_SPRINT_2.29.md](docs/sprints/SIM_SPRINT_2.29.md)

---

## 🎯 Sprint 2.29 Objectives

### 1. Signal Pipeline (Track A)
*   **Goal**: Standardize the output of all collectors into actionable signals.
*   **Tasks**:
    *   **Domain Models**: Create `Signal`, `NewsItem`, and `SentimentScore` DB models.
    *   **Ingestion Service**: Build a service to normalize plugin output into these models.
    *   **Aggregator**: Create `CollectorStatsService` for dashboard metrics (throughput, errors).

### 2. Collector Dashboard & Dynamic Forms (Track B)
*   **Goal**: creating the "Mission Control" for data acquisition.
*   **Tasks**:
    *   **Dynamic Forms**: Finalize `CollectorForm.tsx` to render JSON Schema inputs.
    *   **Dashboard**: Implement `CollectorDashboard.tsx` visualizing active streams and throughput.
    *   **Status Indicators**: Real-time health checks (Green/Red) and "Last Successful Run" metrics.
    *   **Actions**: Wire up "Run Now", "Edit", and "Delete" buttons to the API.

---

## 📦 Deliverables

1.  **Signal Pipeline**: Verified flow from Plugin -> Ingestion -> Normalized DB Records.
2.  **Admin UI**: Full CRUD capability for Collector instances via Dynamic Forms.
3.  **Operation Dashboard**: "Central Command" view showing real-time volume and health.
4.  **End-to-End Verification**: Proven ability to configure a plugin in UI and see normalized data in backend.

---

**Last Updated:** Feb 21, 2026
