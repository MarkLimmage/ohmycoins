# User Stories - Feature Store

## Context
These user stories define the "North Star" for the database feature store to ensure it provides tangible value for model development.

## Algorithmic Trading Architect

**Story:**
> As an Algo Architect, I want a pre-aligned dataset of price targets and sentiment signals so that I can train models without writing 500 lines of data-cleaning code.

**Acceptance Criteria:**
*   [ ] **No Look-Ahead Bias:** Data is strictly "point-in-time" correct. Future targets (e.g., +1h return) are available for training rows, but signals (e.g., sentiment) only use data available *at or before* the prediction time (T-1h lag).
*   [ ] **Target Definition:** Dataset includes explicit target variables for:
    *   1-hour forward return (`target_return_1h`)
    *   24-hour forward return (`target_return_24h`)
*   [ ] **Freshness:** New signals appear in the training set within 60 minutes of collection (via refreshing mechanism).
*   [ ] **Performance:** Querying 100k rows for model training takes < 2 seconds.
