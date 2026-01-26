# Performance Feature

## Component Hierarchy

- **PerformanceDashboard** (`routes/audit/performance.tsx` or `features/performance/PerformanceDashboard.tsx`)
  - **StrategyMetricsOverview**
    - **StrategyCard** (Displays individual strategy metrics: Sharpe, Win Rate, Drawdown)
  - **PerformanceVisuals**
    - **EquityCurve** (Line chart using Recharts showing equity over time)
    - **DrawdownChart** (Optional/Future: Area chart showing drawdown)

## State Management
- Data fetching via React Query (hooks to be defined in `api/`)

## Responsive Design Strategy
- **Mobile (< 768px):** 
  - Stacked layout (Cards first, then Charts).
  - Sidebar collapsed (handled by global layout).
  - Charts simplified or with horizontal scroll.
- **Desktop:**
  - Grid layout.
  - Sidebar visible.
