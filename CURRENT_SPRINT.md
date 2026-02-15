# Current Sprint - Sprint 2.28 (Collector Uplift)

**Status:** 🚀 ACTIVE
**Overall Goal:** Revolutionize data collection management by moving it from code to an Admin UI, enabling simple addition/modification of data sources.
**SIM**: [docs/sprints/SIM_SPRINT_2.28.md](docs/sprints/SIM_SPRINT_2.28.md)

---

## 🎯 Sprint 2.28 Objectives

### 1. Collector Management API (Track A)
*   **Goal**: Create the backend infrastructure for dynamic collector management.
*   **Tasks**:
    *   **Model**: Design `Collector` SQLAlchemy model with JSON configuration fields.
    *   **API**: Implement `CRUD /api/v1/collectors` endpoints.
    *   **Engine**: Refactor `collector_engine` to load jobs from the DB.

### 2. Admin UI Dashboard (Track B)
*   **Goal**: Build the "Control Center" for data collection.
*   **Tasks**:
    *   **Dashboard**: Visualize collector health (Green/Red indicators), last run time, and success rate.
    *   **Form**: Dynamic form for creating specific collector types (API vs Scraper).
    *   **Actions**: "Run Now", "Pause", "Resume" buttons.

### 3. Dynamic Scraper Logic (Track A+B)
*   **Goal**: Allow scraping rules to be defined without code deployment.
*   **Tasks**:
    *   **Storage**: Store CSS/XPath selectors and extraction rules in JSON.
    *   **Execution**: Build a generic `WebScraperCollector` that parses this config at runtime.

---

## 📦 Deliverables

1.  **Collector Admin Panel**: Accessible at `/admin/collectors`.
2.  **Generic Scraper**: A collector type that can be configured purely via UI to scrape a new site.
3.  **Automated Scheduling**: Pausing a collector in UI stops it in the backend immediately.

---

**Last Updated:** Feb 15, 2026
