# Data Visualization Specification - Oh My Coins

**Version**: 1.0  
**Date**: 2026-01-24  
**Status**: ACTIVE  
**Purpose**: Define exact chart types and data transformations for 4 Ledgers dashboard

---

## Overview

This document specifies how to visualize data from the 4 Ledgers (Glass, Human, Catalyst, Exchange) on the Oh My Coins dashboard. Each ledger has unique data characteristics requiring tailored visualization approaches.

**Design Principle**: Progressive disclosure - Show summary first, details on demand.

---

## The 4 Ledgers Dashboard Layout

### Grid Structure

**Desktop** (≥1280px):
```
┌─────────────────┬─────────────────┐
│  Glass Ledger   │  Human Ledger   │
│  (TVL Charts)   │  (Sentiment)    │
├─────────────────┼─────────────────┤
│ Catalyst Ledger │ Exchange Ledger │
│  (Events)       │  (Prices)       │
└─────────────────┴─────────────────┘
```

**Tablet** (768-1279px): Same 2x2 grid, smaller cards

**Mobile** (< 768px): Vertical stack, priority order:
1. Catalyst (most time-sensitive)
2. Exchange (portfolio monitoring)
3. Human (sentiment trends)
4. Glass (DeFi metrics)

---

## 1. Glass Ledger Card

**Purpose**: Visualize DeFi protocol metrics (TVL, fees, active addresses)

### Primary Chart: TVL Over Time

**Chart Type**: Line chart with dual Y-axis  
**Library**: recharts (React wrapper for D3)

**Axes**:
- **Left Y-axis**: TVL in USD (log scale)
  - Range: Auto-scaled based on data
  - Format: `$42.5B`, `$1.2M` (human-readable with K/M/B suffixes)
  - Grid lines: Horizontal, subtle gray (#e5e7eb)
  
- **Right Y-axis**: Fees in USD (linear scale)
  - Range: 0 to max(fees) * 1.1 (10% padding)
  - Format: `$12.3M`
  - Color: #10b981 (green-500) to differentiate from TVL

- **X-axis**: Time (last 30 days, daily granularity)
  - Format: `Jan 24`, `Feb 1` (abbreviated month + day)
  - Ticks: Every 5 days
  - Range: Configurable via date picker (7d, 30d, 90d, 1y)

**Data Lines**:
- **TVL Line**: #3b82f6 (blue-500), 2px stroke, smooth curve
- **Fees Line**: #10b981 (green-500), 2px stroke, dashed pattern

**Interaction**:
- **Hover**: Show vertical line cross-hair, tooltip with exact values
  ```
  ┌─────────────────────┐
  │ Jan 24, 2026        │
  │ TVL: $42,501,234    │
  │ Fees: $12,345,678   │
  └─────────────────────┘
  ```
- **Click data point**: Drill down to protocol detail view (navigate to `/ledgers/glass/{protocol}`)
- **Zoom**: Mouse wheel to zoom in/out, pinch gesture on touch

**Loading State**: 
- Skeleton: Gray rectangles approximating line chart shape
- Animation: Pulse effect, 1.5s duration

**Error State**:
```
❌ Unable to load Glass data
Last updated: 2 minutes ago
[Retry]
```

**API Integration**:
```typescript
// GET /api/v1/data/glass?protocol=<protocol>&days=30
interface GlassData {
  protocol: string;
  tvl: Array<{ date: string; value: number }>;
  fees: Array<{ date: string; value: number }>;
  active_addresses?: Array<{ date: string; value: number }>; // Phase 2
}

// Example response
{
  "protocol": "Uniswap V3",
  "tvl": [
    { "date": "2026-01-24", "value": 42501234000 },
    { "date": "2026-01-23", "value": 41876543000 },
    ...
  ],
  "fees": [
    { "date": "2026-01-24", "value": 12345678 },
    { "date": "2026-01-23", "value": 11987654 },
    ...
  ]
}
```

**Component Props**:
```typescript
interface GlassLedgerChartProps {
  protocol: string;
  timeRange: 7 | 30 | 90 | 365;  // days
  showFees?: boolean;  // Toggle fees line
  showActiveAddresses?: boolean;  // Phase 2 feature
}
```

---

### Secondary Metrics (Cards Below Chart)

**Metric 1: Current TVL**
```
┌────────────────────────┐
│ Current TVL            │
│ $42.5B                 │
│ +2.3% (24h) ↗          │
└────────────────────────┘
```
- Large number: 32px, bold
- 24h change: Green (positive) or red (negative) with arrow icon
- Format: Human-readable with B/M/K suffix

**Metric 2: 30d Fees**
```
┌────────────────────────┐
│ 30d Fees               │
│ $387.2M                │
│ Avg: $12.9M/day        │
└────────────────────────┘
```

**Metric 3: Active Addresses** (Phase 2 only)
```
┌────────────────────────┐
│ Active Addresses       │
│ 1.2M                   │
│ +5.2% (7d) ↗           │
└────────────────────────┘
```

**Requirements**: REQ-GL-001, REQ-GL-002

---

## 2. Human Ledger Card

**Purpose**: Visualize social sentiment trends across cryptocurrency community

### Primary Chart: Sentiment Heatmap

**Chart Type**: Calendar heatmap (visx primitives)  
**Library**: visx (Airbnb's low-level visualization components)

**Layout**:
- Grid: 7 columns (days of week) × 5 rows (weeks)
- Time range: Last 30 days
- Cell size: 40px × 40px (desktop), 24px × 24px (mobile)

**Color Scale**:
- **Bullish sentiment** (positive): Green gradient
  - +0.7 to +1.0: #10b981 (green-500)
  - +0.4 to +0.7: #34d399 (green-400)
  - +0.0 to +0.4: #6ee7b7 (green-300)
  
- **Neutral sentiment** (zero): #e5e7eb (gray-200)
  
- **Bearish sentiment** (negative): Red gradient
  - -0.4 to 0.0: #fca5a5 (red-300)
  - -0.7 to -0.4: #f87171 (red-400)
  - -1.0 to -0.7: #ef4444 (red-500)

**Cell Content**:
- Border: 1px solid #d1d5db (gray-300)
- Tooltip on hover:
  ```
  ┌─────────────────────────┐
  │ Jan 24, 2026            │
  │ Sentiment: 🔥 Bullish   │
  │ Score: +0.82            │
  │ Volume: 1,234 mentions  │
  │                         │
  │ Top Keywords:           │
  │ • ETF approval          │
  │ • bull run              │
  │ • institutional         │
  └─────────────────────────┘
  ```

**Interaction**:
- **Click cell**: Open "Sentiment Detail" modal
  - Shows: News articles, Reddit posts, Twitter threads for that day
  - Breakdown: Sentiment by source (Reddit 0.9, Twitter 0.7, News 0.8)
  - Timeline: Hourly sentiment throughout the day

- **Filter by source**: Toggle buttons at top
  ```
  [Reddit ✓] [Twitter ✓] [News ✓]
  ```
  - Unchecking source recalculates sentiment without that data

- **Sentiment threshold slider**: Highlight only strong signals
  ```
  Show only: [====|====] ≥ 0.5 (Strong bullish)
  ```

**API Integration**:
```typescript
// GET /api/v1/data/human?days=30
interface HumanData {
  date: string;  // ISO 8601 date
  sentiment_score: number;  // -1 to +1
  volume: number;  // Number of mentions
  top_keywords: string[];  // Top 3-5 keywords/hashtags
  sources: Array<{
    source: 'reddit' | 'news' | 'twitter';
    count: number;
    avg_sentiment: number;
  }>;
}[]

// Example response
[
  {
    "date": "2026-01-24",
    "sentiment_score": 0.82,
    "volume": 1234,
    "top_keywords": ["ETF approval", "bull run", "institutional"],
    "sources": [
      { "source": "reddit", "count": 456, "avg_sentiment": 0.9 },
      { "source": "twitter", "count": 678, "avg_sentiment": 0.7 },
      { "source": "news", "count": 100, "avg_sentiment": 0.8 }
    ]
  },
  ...
]
```

---

### Secondary Metrics

**Metric 1: Current Sentiment**
```
┌────────────────────────┐
│ Current Sentiment      │
│ 🔥 Bullish (+0.82)     │
└────────────────────────┘
```
- Emoji indicators:
  - 🔥 Bullish (> 0.5)
  - 😐 Neutral (-0.2 to 0.5)
  - 🧊 Bearish (< -0.2)

**Metric 2: Trending Coins**
```
┌────────────────────────┐
│ Trending Coins (24h)   │
│ 1. BTC (2,345 mentions)│
│ 2. ETH (1,876 mentions)│
│ 3. SOL (987 mentions)  │
└────────────────────────┘
```

**Metric 3: News Volume**
```
┌────────────────────────┐
│ News Volume (24h)      │
│ 234 articles           │
│ +12% vs yesterday ↗    │
└────────────────────────┘
```

**Requirements**: REQ-HL-001, REQ-HL-002

---

## 3. Catalyst Ledger Card

**Purpose**: Display real-time cryptocurrency events (listings, regulations, hacks, upgrades)

### Primary View: Real-Time Event Ticker

**Chart Type**: Scrolling list with auto-updates (custom component)  
**Library**: Custom React component + WebSocket

**Layout**:
```
┌──────────────────────────────────────────┐
│ ⚡ LIVE EVENTS                    [⋮]    │
├──────────────────────────────────────────┤
│ 🔴 CRITICAL | 2 mins ago                 │
│ SEC filing detected: BlackRock ETF       │
│ approval | Source: SEC.gov | BTC, ETH    │
├──────────────────────────────────────────┤
│ 🟠 HIGH | 15 mins ago                    │
│ New listing on Binance: RENDER token     │
│ Source: Binance Blog | RENDER            │
├──────────────────────────────────────────┤
│ ⚪ NORMAL | 1 hour ago                   │
│ Ethereum upgrade scheduled for Feb 15    │
│ Source: Ethereum Foundation | ETH        │
└──────────────────────────────────────────┘
```

**Event Structure**:
- **Priority Badge**: Icon + text (🔴 CRITICAL, 🟠 HIGH, ⚪ NORMAL)
- **Timestamp**: Relative time ("2 mins ago", "1 hour ago")
- **Title**: Short event description (max 60 characters)
- **Details**: Source + related coins (tags)
- **Background Color**: 
  - Critical: #fee2e2 (red-100)
  - High: #fed7aa (amber-100)
  - Normal: #f3f4f6 (gray-100)

**Auto-Update Behavior**:
- New events: Slide in from top with fade animation (300ms)
- Old events: Fade out after 30 seconds (normal priority only)
- Max visible: 5 events (older events accessible via "View All" link)

**Interaction**:
- **Click event**: Open detail modal
  ```
  ┌─────────────────────────────────────┐
  │ SEC Filing Detected: BlackRock ETF  │
  │ Approval                            │
  ├─────────────────────────────────────┤
  │ Priority: 🔴 CRITICAL               │
  │ Time: Jan 24, 2026 4:32 PM EST     │
  │ Source: SEC.gov                     │
  │ Related Coins: BTC, ETH             │
  │                                     │
  │ Full Description:                   │
  │ BlackRock filed Form 19b-4 for...  │
  │                                     │
  │ Historical Price Impact:            │
  │ Similar events: +8% avg (7 days)    │
  │                                     │
  │ [Analyze in Lab] [Set Alert] [Close]│
  └─────────────────────────────────────┘
  ```

- **"Analyze in Lab" button**: Pre-fill Lab session with event context
- **"Set Alert" button**: Subscribe to similar event types
- **Filter by priority**: Dropdown to show only critical/high

**Sound Alerts**:
- Critical events: Play chime (user can disable in settings)
- Sound file: `assets/sounds/alert.mp3` (< 1 second, low volume)
- Mute button in card header

**WebSocket Integration**:
```typescript
// WebSocket: wss://api.ohmycoins.com/ws/catalyst/live?token={jwt}
interface CatalystEvent {
  id: string;  // Unique event ID
  type: 'listing' | 'regulation' | 'hack' | 'upgrade' | 'other';
  title: string;
  description: string;  // Full description (for modal)
  source: string;  // "SEC", "CoinSpot", "Twitter", "Etherscan"
  priority: 'critical' | 'high' | 'normal';
  timestamp: string;  // ISO 8601
  related_coins: string[];  // ["BTC", "ETH"]
}

// Example WebSocket message
{
  "id": "evt-abc-123",
  "type": "regulation",
  "title": "SEC filing detected: BlackRock ETF approval",
  "description": "BlackRock filed Form 19b-4 with the SEC for a spot Bitcoin ETF...",
  "source": "SEC.gov",
  "priority": "critical",
  "timestamp": "2026-01-24T16:32:00Z",
  "related_coins": ["BTC", "ETH"]
}
```

---

### Secondary Actions

**Quick Actions Bar**:
```
[🔔 Alerts (3)] [⚙️ Filters] [📋 View All]
```

- **Alerts**: Show count of active alert subscriptions
- **Filters**: Toggle event types (Listings ✓, Regulations ✓, Hacks ✓, Upgrades ✓)
- **View All**: Navigate to `/ledgers/catalyst/history` (full event log)

**Requirements**: REQ-CL-001, REQ-CL-003, NFR-CL-001 (< 30s latency)

---

## 4. Exchange Ledger Card

**Purpose**: Visualize real-time price movements for user's portfolio coins

### Primary Chart: Multi-Coin Sparklines

**Chart Type**: Small line charts (sparklines)  
**Library**: lightweight-charts (TradingView's high-performance library)

**Layout**:
```
┌──────────────────────────────────────────┐
│ Top 10 Coins (by portfolio value)       │
├──────────────────────────────────────────┤
│ BTC    $94,623  +2.3%  ▁▂▃▅▇█▅▃        │
│ ETH    $3,287   +1.8%  ▁▁▂▃▅▆▅▃        │
│ SOL    $142.50  -0.5%  ▃▅▇▆▅▃▂▁        │
│ ADA    $0.62    +5.2%  ▁▂▂▃▅▇█▆        │
│ ...                                      │
└──────────────────────────────────────────┘
```

**Sparkline Specifications**:
- **Time Range**: Last 24 hours, 5-minute candles
- **Width**: 80px
- **Height**: 24px
- **Y-axis**: Hidden (relative scale, auto-fitted to data range)
- **X-axis**: Hidden (time implicit from "24h" label)
- **Line Color**:
  - Green (#22c55e) if 24h change positive
  - Red (#ef4444) if 24h change negative
  - Gray (#6b7280) if no change
- **Line Width**: 1.5px
- **Area Fill**: Semi-transparent gradient (opacity 0.2 at top, 0 at bottom)

**Coin Row Layout**:
- **Coin Symbol**: 3-4 characters, bold, 14px
- **Current Price**: Tabular numbers, 16px, updated every 10 seconds
- **24h Change**: Percentage with + or - sign, colored (green/red)
- **Sparkline**: Inline chart

**Interaction**:
- **Hover**: Show tooltip with current price and 24h change
  ```
  BTC: $94,623
  24h: +2.3% (+$2,124)
  High: $95,210
  Low: $92,456
  ```
- **Click row**: Navigate to detailed coin chart page (`/ledgers/exchange/{coin}`)
- **Real-time updates**: Price updates every 10 seconds via polling (or WebSocket for critical coins)

**API Integration**:
```typescript
// GET /api/v1/data/exchange/prices?coins=BTC,ETH,SOL&interval=5m&hours=24
interface ExchangePriceData {
  coin: string;  // "BTC", "ETH", etc.
  prices: Array<{
    timestamp: string;  // ISO 8601
    price: number;  // Current price in AUD
    volume: number;  // 24h volume
  }>;
  change_24h: number;  // Percentage change
  high_24h: number;
  low_24h: number;
}[]

// Example response
[
  {
    "coin": "BTC",
    "prices": [
      { "timestamp": "2026-01-24T00:00:00Z", "price": 92456, "volume": 123456 },
      { "timestamp": "2026-01-24T00:05:00Z", "price": 92578, "volume": 124567 },
      ...
    ],
    "change_24h": 2.3,
    "high_24h": 95210,
    "low_24h": 92456
  },
  ...
]
```

---

### Secondary Metrics

**Metric 1: Portfolio Value**
```
┌────────────────────────┐
│ Portfolio Value        │
│ $12,345.67 AUD         │
│ +2.1% (24h) ↗          │
└────────────────────────┘
```
- Large number: Sum of (coin_amount × current_price) for all holdings
- 24h change: Green (positive) or red (negative)

**Metric 2: Top Gainer**
```
┌────────────────────────┐
│ Top Gainer (24h)       │
│ ADA +5.2%              │
│ $0.62                  │
└────────────────────────┘
```
- Green background (#10b981 / 20% opacity)

**Metric 3: Top Loser**
```
┌────────────────────────┐
│ Top Loser (24h)        │
│ SOL -0.5%              │
│ $142.50                │
└────────────────────────┘
```
- Red background (#ef4444 / 20% opacity)

**Requirements**: REQ-EL-001, REQ-EL-002, NFR-EL-001 (< 10s latency)

---

## Performance Optimization

### Chart Rendering Performance

**Target Frame Rate**: 60 FPS (16ms per frame)

**Optimization Strategies**:
1. **Debounce Updates**: For real-time data, throttle updates to max 1 per second per chart
2. **Virtual Rendering**: For long lists (Catalyst events), render only visible items
3. **Memoization**: Use React.memo() for chart components (re-render only when data changes)
4. **Web Workers**: Offload heavy calculations (sentiment aggregation, statistical analysis) to background thread
5. **Canvas vs. SVG**:
   - Use Canvas for high-frequency updates (Exchange sparklines)
   - Use SVG for static/slow-updating charts (Glass TVL, Human heatmap)

**Code Example** (React Query with optimistic updates):
```typescript
const { data } = useQuery(
  ['ledger-data', ledgerType],
  () => fetchLedgerData(ledgerType),
  {
    refetchInterval: 5000,  // Poll every 5 seconds
    staleTime: 2000,  // Consider data stale after 2 seconds
    cacheTime: 300000,  // Cache for 5 minutes
  }
);
```

---

## Accessibility Features

### Chart Alternatives (REQ-UX-001)

**Table View Toggle**: All charts must have accessible table alternative

**Example** (Glass Ledger):
```
[View as Table] ← Toggle button below chart

When toggled, show:

| Date       | TVL (USD)    | Fees (USD) | Change % |
|------------|--------------|------------|----------|
| Jan 24     | $42,501,234  | $12.3M     | +2.3%    |
| Jan 23     | $41,876,543  | $11.9M     | +1.5%    |
| Jan 22     | $41,254,321  | $11.7M     | -0.8%    |
...

Features:
- Sortable columns (click header to sort)
- Keyboard navigation (arrow keys)
- Export to CSV
- Pagination (50 rows per page)
```

### Screen Reader Support

**ARIA Labels**:
```html
<div role="img" aria-label="Glass Ledger TVL chart showing upward trend over 30 days, current value $42.5 billion">
  <!-- Chart SVG/Canvas -->
</div>
```

**Live Region Announcements**:
```html
<div aria-live="polite" aria-atomic="true">
  <!-- Catalyst alerts announced here -->
  New critical alert: SEC filing detected
</div>
```

**Keyboard Shortcuts**:
- Cmd/Ctrl+Shift+T: Toggle table view for all charts globally
- Tab: Navigate between chart elements
- Enter/Space: Activate drill-down (same as click)

---

## Testing Strategy

### Visual Regression Testing

**Tool**: Chromatic (integrates with Storybook)

**Test Cases**:
1. **Snapshot Tests**: Capture chart appearance with fixed mock data
2. **Responsive Tests**: Test charts at mobile/tablet/desktop breakpoints
3. **State Tests**: Loading, error, empty states

**Example** (Storybook story):
```typescript
export const GlassLedgerWithData = () => (
  <GlassLedgerCard data={mockGlassData} timeRange={30} />
);

export const GlassLedgerLoading = () => (
  <GlassLedgerCard data={null} isLoading={true} />
);

export const GlassLedgerError = () => (
  <GlassLedgerCard data={null} error={new Error('Network error')} />
);
```

### Performance Testing

**Metrics**:
- **Chart Render Time**: < 100ms for initial render
- **Update Latency**: < 50ms from data received to UI updated
- **Memory Usage**: < 50MB per chart (prevent memory leaks on long sessions)

**Tools**:
- React DevTools Profiler
- Chrome Performance tab
- Lighthouse

---

## Document Maintenance

**Update Triggers**:
- New data source added (5th Ledger?)
- Chart library upgraded (recharts 2.x → 3.x)
- Performance issues identified
- Accessibility feedback from users

**Review Schedule**:
- Per Sprint: Add new visualizations from sprint work
- Monthly: Frontend Lead reviews for performance
- Quarterly: Design review with Product + UX teams

**Ownership**:
- Frontend Lead: Technical implementation
- Design Lead: Visual consistency
- Data Team: Data accuracy and API contracts

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-24  
**Next Review**: 2026-02-24  
**Related Docs**: DESIGN_SYSTEM.md, API_CONTRACTS.md
