# Current Sprint - Sprint 2.28 (Collector Uplift)

**Status:** 🚀 ACTIVE
**Overall Goal:** Revolutionize data collection management by implementing a **Plugin-Based Architecture** allowing Admins to manage standard data sources via the UI.
**SIM**: [docs/sprints/SIM_SPRINT_2.28.md](docs/sprints/SIM_SPRINT_2.28.md)

---

## 🎯 Sprint 2.28 Objectives

### 1. Collector Plugin System (Track A)
*   **Goal**: Create a robust, extensible backend for data collection.
*   **Tasks**:
    *   **Registry**: Build `CollectorRegistry` to auto-discover strategies in `backend/app/collectors/strategies/`.
    *   **Interface**: Define `ICollector` protocol for all plugins (Collect, Config Schema, Test Connection).
    *   **Migration**: Port current price collectors to the new plugin format.
    *   **Reference**: Port `CoinDesk`, `Yahoo`, and `CryptoPanic` scrapers as standard plugins.

### 2. Admin UI Dashboard (Track B)
*   **Goal**: Build the "Control Center" for data collection strategies.
*   **Tasks**:
    *   **Dynamic Forms**: Render configuration inputs (API Keys, Intervals, Symbols) based on plugin JSON schemas.
    *   **Dashboard**: Visualize collector health (Green/Red indicators), last run time, and success rate.
    *   **Actions**: "Run Now", "Pause", "Resume", "Delete" instance controls.

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
4.  **Documentation**: Updated Architecture and User Journeys reflecting the Plugin model.

---

**Last Updated:** Feb 19, 2026
