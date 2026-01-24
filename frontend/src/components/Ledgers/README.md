# Ledger Components

React components for displaying the 4 Ledgers dashboard in Oh My Coins.

## Overview

This module provides the base `LedgerCard` component and 4 specialized variants for displaying different types of crypto market data:

- **GlassLedgerCard**: On-chain metrics (TVL, fees, revenue)
- **HumanLedgerCard**: Social sentiment and trending topics
- **CatalystLedgerCard**: Real-time events and alerts
- **ExchangeLedgerCard**: Price data and portfolio tracking

## Features

✅ **4 Component States**: Loading, Error, Empty, Live  
✅ **Accessibility**: WCAG 2.1 AA compliant (REQ-UX-001, REQ-UX-004, REQ-UX-005)  
✅ **Table View Toggle**: Accessible alternative to charts for screen readers  
✅ **Keyboard Navigation**: Full keyboard support with focus indicators  
✅ **Real-time Updates**: Live data with pulse animation and timestamps  
✅ **Color-coded Alerts**: Visual priority indicators (normal, warning, critical)

## Components

### LedgerCard (Base Component)

Base component that handles common functionality across all ledger types.

```tsx
import { LedgerCard } from './components/Ledgers';

<LedgerCard
  ledgerType="glass"
  data={data}
  isLoading={false}
  error={null}
  showTableView={false}
  onToggleTableView={() => setShowTable(!showTable)}
  onDrillDown={(id) => console.log('Drill down:', id)}
/>
```

#### Props

| Prop | Type | Description |
|------|------|-------------|
| `ledgerType` | `'glass' \| 'human' \| 'catalyst' \| 'exchange'` | Type of ledger to display |
| `data` | `LedgerData` | Ledger data to display |
| `isLoading` | `boolean` | Show loading skeleton |
| `error` | `Error \| null` | Error to display |
| `showTableView` | `boolean` | Show table instead of chart |
| `onToggleTableView` | `() => void` | Toggle table view callback |
| `onDrillDown` | `(id: string) => void` | Drill down callback |
| `alertLevel` | `'normal' \| 'warning' \| 'critical'` | Visual alert indicator |

### GlassLedgerCard

Displays on-chain metrics including Total Value Locked (TVL), fees, and revenue.

```tsx
import { GlassLedgerCard, type GlassLedgerData } from './components/Ledgers';

const data: GlassLedgerData = {
  id: 'glass-1',
  timestamp: new Date(),
  lastUpdated: new Date(),
  tvl: 42500000000, // $42.5B
  fees: 12300000, // $12.3M
  revenue: 8500000, // $8.5M
  tvlChange24h: 5.23,
  feesChange24h: -2.15,
};

<GlassLedgerCard ledgerType="glass" data={data} />
```

### HumanLedgerCard

Displays social sentiment, trending coins, and news volume.

```tsx
import { HumanLedgerCard, type HumanLedgerData } from './components/Ledgers';

const data: HumanLedgerData = {
  id: 'human-1',
  timestamp: new Date(),
  lastUpdated: new Date(),
  sentiment: 'bullish',
  sentimentScore: 0.73,
  trendingCoins: ['BTC', 'ETH', 'SOL'],
  newsVolume: 1247,
};

<HumanLedgerCard ledgerType="human" data={data} />
```

### CatalystLedgerCard

Displays real-time events with priority badges and type indicators.

```tsx
import { CatalystLedgerCard, type CatalystLedgerData } from './components/Ledgers';

const data: CatalystLedgerData = {
  id: 'catalyst-1',
  timestamp: new Date(),
  lastUpdated: new Date(),
  events: [
    {
      id: 'event-1',
      title: 'SEC Approves Bitcoin ETF',
      type: 'regulation',
      priority: 'critical',
      timestamp: new Date(),
      description: 'Breaking news...',
    },
  ],
};

<CatalystLedgerCard 
  ledgerType="catalyst" 
  data={data} 
  alertLevel="critical" 
/>
```

### ExchangeLedgerCard

Displays price data, portfolio value, top gainers/losers, and sparklines.

```tsx
import { ExchangeLedgerCard, type ExchangeLedgerData } from './components/Ledgers';

const data: ExchangeLedgerData = {
  id: 'exchange-1',
  timestamp: new Date(),
  lastUpdated: new Date(),
  portfolioValue: 125000,
  topGainer: { symbol: 'SOL', change: 15.32 },
  topLoser: { symbol: 'ADA', change: -8.45 },
  sparklines: [
    {
      symbol: 'BTC',
      prices: [45000, 45200, 45500, 46000],
      currentPrice: 45900,
      change24h: 2.15,
    },
  ],
};

<ExchangeLedgerCard ledgerType="exchange" data={data} />
```

### LedgerTableView

Standalone table view component for accessible data display.

```tsx
import { LedgerTableView } from './components/Ledgers';

<LedgerTableView
  ledgerType="glass"
  data={data}
  showTableView={showTable}
  onToggleTableView={() => setShowTable(!showTable)}
/>
```

## Usage Example: 4 Ledgers Dashboard

```tsx
import React from 'react';
import { Grid, Box } from '@chakra-ui/react';
import {
  GlassLedgerCard,
  HumanLedgerCard,
  CatalystLedgerCard,
  ExchangeLedgerCard,
} from './components/Ledgers';

export function LedgersDashboard() {
  const [tableViews, setTableViews] = React.useState({
    glass: false,
    human: false,
    catalyst: false,
    exchange: false,
  });

  const toggleTableView = (ledger: keyof typeof tableViews) => {
    setTableViews(prev => ({ ...prev, [ledger]: !prev[ledger] }));
  };

  return (
    <Box padding="24px">
      <Grid templateColumns="repeat(2, 1fr)" gap="24px">
        <GlassLedgerCard
          ledgerType="glass"
          data={glassData}
          showTableView={tableViews.glass}
          onToggleTableView={() => toggleTableView('glass')}
        />
        <HumanLedgerCard
          ledgerType="human"
          data={humanData}
          showTableView={tableViews.human}
          onToggleTableView={() => toggleTableView('human')}
        />
        <CatalystLedgerCard
          ledgerType="catalyst"
          data={catalystData}
          showTableView={tableViews.catalyst}
          onToggleTableView={() => toggleTableView('catalyst')}
          alertLevel="critical"
        />
        <ExchangeLedgerCard
          ledgerType="exchange"
          data={exchangeData}
          showTableView={tableViews.exchange}
          onToggleTableView={() => toggleTableView('exchange')}
        />
      </Grid>
    </Box>
  );
}
```

## Accessibility Features

All components follow WCAG 2.1 AA standards:

### Keyboard Navigation
- **Tab**: Navigate between interactive elements
- **Enter/Space**: Activate buttons and drill-down actions
- **Escape**: Close modals (future feature)

### ARIA Labels
- All charts have descriptive `aria-label` attributes
- Interactive elements have clear labels
- Live updates announced via `aria-live` regions

### Focus Indicators
- 2px blue outline on focus
- 4px offset for visibility
- Visible on all interactive elements

### Table View Toggle (REQ-UX-001)
- Every chart has a "View Table" button
- Table view provides same data in accessible format
- Screen readers can navigate table with arrow keys

### Color Contrast
- All text meets 4.5:1 contrast ratio (normal text)
- 3:1 for large text (≥18px)
- Color never sole indicator (paired with icons/text)

## Performance

- **Render Time**: <100ms target (REQ-UX-004)
- **Bundle Size**: Minimal dependencies (Chakra UI only)
- **Updates**: Throttled to 1 update/second max
- **Animations**: GPU-accelerated (transform/opacity only)

## Component States

### Loading
Shows skeleton screens with preserved layout to prevent layout shift.

### Error
Displays error message with retry button and last updated timestamp.

### Empty
Shows friendly message with suggestions (e.g., "Try expanding date range").

### Live
Real-time updates with pulse animation and relative timestamps.

## Styling

Components use Chakra UI v3 with the project theme:

### Ledger Colors
- Glass: `#3b82f6` (blue)
- Human: `#10b981` (green)
- Catalyst: `#f59e0b` (amber)
- Exchange: `#8b5cf6` (purple)

### Functional Colors
- Success: `#22c55e` (green)
- Danger: `#ef4444` (red)
- Warning: `#f59e0b` (amber)
- Neutral: `#6b7280` (gray)

## Dependencies

- **@chakra-ui/react**: ^3.27.0
- **date-fns**: Latest (for relative timestamps)
- **React**: ^18.x

## Files

```
components/Ledgers/
├── LedgerCard.tsx              # Base component
├── GlassLedgerCard.tsx         # TVL/Fee display
├── HumanLedgerCard.tsx         # Sentiment display
├── CatalystLedgerCard.tsx      # Event list
├── ExchangeLedgerCard.tsx      # Price list
├── LedgerTableView.tsx         # Accessible table view
├── types.ts                     # TypeScript types
├── index.ts                     # Public exports
├── LedgerCard.example.tsx      # Usage examples
└── README.md                    # This file
```

## Requirements Satisfied

- ✅ REQ-UX-001: Table view toggle for screen readers
- ✅ REQ-UX-004: <100ms render time
- ✅ REQ-UX-005: WCAG 2.1 AA accessibility
- ✅ 4 component states (loading, error, empty, live)
- ✅ Keyboard navigation with focus indicators
- ✅ ARIA labels on all interactive elements
- ✅ Color contrast compliance
- ✅ Real-time updates with timestamps

## Future Enhancements

- [ ] Chart drill-down modals
- [ ] Advanced chart visualizations (recharts, visx, lightweight-charts)
- [ ] Export to CSV functionality
- [ ] Customizable time ranges
- [ ] Chart zoom and pan
- [ ] WebSocket integration for real-time updates
- [ ] Alert notifications for Catalyst events
- [ ] Mobile responsive layouts
