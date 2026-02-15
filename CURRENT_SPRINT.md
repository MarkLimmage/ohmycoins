# Current Sprint - Sprint 2.28 (Collector Uplift)

**Status:** 🚀 ACTIVE
**Overall Goal:** Revolutionize data collection management by moving it from code to an Admin UI, enabling simple addition/modification of data sources.
**SIM**: [docs/sprints/SIM_SPRINT_2.28.md](docs/sprints/SIM_SPRINT_2.28.md)

---

## 🎯 Sprint 2.28 Objectives

### 1. Plugin Architecture (Track A)
*   **Goal**: Create a robust, extensible backend for data collection.
*   **Tasks**:
    *   **Registry**: Build `CollectorRegistry` to auto-discover strategies.
    *   **Interface**: Define `ICollector` protocol for all plugins.
    *   **Migration**: Port current price collectors to the new plugin format.
    *   **Reference**: Port `CoinDesk` and `Yahoo` scrapers from reference code.

### 2. Admin UI Dashboard (Track B)
*   **Goal**: Build the "Control Center" for data collection strategies.
*   **Tasks**:
    *   **Dynamic Forms**: Render configuration inputs based on plugin JSON schemas.
    *   **Dashboard**: Visualize collector health (Green/Red indicators).
    *   **Actions**: "Run Now", "Pause", "Resume" instance controls.

### 3. Signal Pipeline (Track A)
*   **Goal**: Standardize the output of all collectors.
*   **Tasks**:
    *   **Models**: Create `Signal`, `NewsItem`, and `SentimentScore` DB models.
    *   **Ingestion**: Build a service to normalize plugin output into these models.

---

## 📦 Deliverables

1.  **Collector Registry**: Backend system that loads strategies from `backend/app/collectors/strategies/`.
2.  **Plugin Library**: At least 3 working plugins (Price, CoinDesk, Yahoo).
3.  **Dynamic UI**: Admin panel that adapts to the configuration needs of each plugin.

---

**Last Updated:** Feb 15, 2026
