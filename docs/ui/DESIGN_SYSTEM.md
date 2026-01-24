# UI Design System - Oh My Coins

**Version**: 1.0  
**Date**: 2026-01-24  
**Status**: ACTIVE  
**Purpose**: Component library specification and interaction patterns for Oh My Coins platform

---

## 1. Design Principles

### 1.1 Core Principles

**Data Density**: 4 Ledgers require high-information layouts
- Challenge: Display Glass, Human, Catalyst, Exchange data simultaneously
- Solution: Card-based grid with progressive disclosure (drill-down modals)
- Principle: Show summary first, details on demand

**Real-Time First**: All data updates via WebSocket/SSE
- Challenge: Keep UI responsive during high-frequency updates
- Solution: Throttle updates (max 1 per second per component), use animations for transitions
- Principle: Never block user interaction for data updates

**Safety-Critical UI**: Trading controls must be fail-safe
- Challenge: Prevent accidental trades, ensure emergency stop always works
- Solution: Confirmation modals, typed confirmations ("STOP"), fallback mechanisms
- Principle: When in doubt, require extra confirmation

---

## 2. Component Library

### 2.1 Core Components

#### LedgerCard
**Purpose**: Standardized widget for displaying ledger data across 4 Ledgers dashboard

**Props**:
```typescript
interface LedgerCardProps {
  ledgerType: 'glass' | 'human' | 'catalyst' | 'exchange';
  data: LedgerData;  // Varies by ledger type
  onDrillDown?: (id: string) => void;  // Navigate to detail view
  alertLevel?: 'normal' | 'warning' | 'critical';  // For Catalyst alerts
  isLoading?: boolean;
  error?: Error | null;
}
```

**Variants**:
- **GlassLedgerCard**: TVL/Fee line charts
  - Primary visual: Dual Y-axis line chart (recharts)
  - Secondary metrics: Current TVL (large number), 24h % change, 30d fees
  - Interaction: Click data point → drill down to protocol detail
  
- **HumanLedgerCard**: Sentiment heatmap
  - Primary visual: Calendar heatmap (visx)
  - Secondary metrics: Current sentiment emoji, trending coins, news volume
  - Interaction: Click cell → sentiment detail modal with news articles

- **CatalystLedgerCard**: Event ticker with priority badges
  - Primary visual: Scrolling list (auto-updates via WebSocket)
  - Secondary actions: "Analyze in Lab" button, "Set Alert" button
  - Interaction: Click event → detail modal, click "Analyze" → Lab session creation

- **ExchangeLedgerCard**: Real-time price sparklines
  - Primary visual: Multi-coin sparklines (lightweight-charts)
  - Secondary metrics: Portfolio value, top gainer, top loser
  - Interaction: Hover → show current price, click → detailed coin chart

**States**:
- **Loading**: Skeleton screen (react-loading-skeleton)
  - Show approximate layout: placeholder for chart, metrics boxes
  - Preserve card dimensions (no layout shift)
- **Error**: Retry button with error message
  - Display: "Unable to load [Ledger] data"
  - Last updated timestamp: "Last updated: 2 minutes ago"
  - Button: "Retry" (calls refetch function)
- **Empty**: "No data available" with data range context
  - Message: "No [Ledger] data for selected time period"
  - Suggestion: "Try expanding date range to 90 days"
- **Live**: Auto-updating with last-update timestamp
  - Subtle pulse animation on data update
  - Timestamp: "Updated 3 seconds ago" (relative time)

**File Location**: `frontend/src/components/Ledgers/LedgerCard.tsx`

**Figma Link**: [To be added]

---

#### AgentTerminal
**Purpose**: Streaming console for agent execution, showing real-time logs from LLM agent

**Props**:
```typescript
interface AgentTerminalProps {
  sessionId: string;  // Agent session ID
  streamUrl: string;  // WebSocket endpoint (wss://...)
  allowInteraction: boolean;  // Enable user input mid-execution
  onExport?: () => void;  // Export transcript callback
  onCancel?: () => void;  // Cancel session callback
}
```

**Features**:
- **ANSI Color Support**: Parse ANSI escape codes for colored agent logs
  - Agent thoughts: Gray italic
  - Tool invocations: Blue with tool icon
  - Tool results: Green (success) / Red (error)
  - User input requests: Amber with input field
  - Final output: Bold with highlighted background

- **Auto-scroll**: Scroll to bottom on new messages (with sticky-scroll option)
  - Default: Auto-scroll enabled
  - User scrolls up: Auto-scroll pauses
  - Button appears: "Jump to Latest" (re-enables auto-scroll)

- **Searchable Transcript**: Cmd/Ctrl+F to search terminal content
  - Search bar appears at top
  - Highlight all matches in yellow
  - Navigate: "Next" / "Previous" buttons

- **Copy to Clipboard**: Copy transcript button
  - Button in header: "Export Transcript"
  - Copies entire terminal content as plain text
  - Success toast: "Transcript copied to clipboard"

**WebSocket Message Format**:
```typescript
interface AgentMessage {
  id: string;  // Unique message ID
  type: 'thought' | 'tool' | 'result' | 'input_request' | 'output';
  content: string;  // Message content (may include markdown)
  timestamp: string;  // ISO 8601
  metadata?: {
    tool_name?: string;  // For type='tool'
    execution_time?: number;  // milliseconds
    error?: string;  // For type='result' with error
  };
}
```

**UI Layout**:
```
┌──────────────────────────────────────────────┐
│  Session: BTC Correlation Analysis   [Export]│
├──────────────────────────────────────────────┤
│  🧠 Agent Thought: Analyzing data...         │
│  🔧 Tool: query_glass_ledger                 │
│      ├─ args: {protocol: "Bitcoin"}          │
│      └─ execution: 1.2s                      │
│  ✅ Result: 1825 records retrieved           │
│  ...                                         │
│  [Jump to Latest]                            │
└──────────────────────────────────────────────┘
```

**File Location**: `frontend/src/components/Lab/AgentTerminal.tsx`

**Requirements**: REQ-AG-002, REQ-AG-009

---

#### SafetyButton
**Purpose**: Fail-safe control for The Floor operations (trading)

**Variants**:
- **KillSwitch**: Full red, large, always visible
- **ConfirmTrade**: Two-step confirmation modal
- **EmergencyStop**: Requires typed confirmation: "STOP"

**Props**:
```typescript
interface SafetyButtonProps {
  action: 'kill' | 'confirm' | 'stop';
  onConfirm: () => Promise<void>;  // Async action (API call)
  requireConfirmation: boolean;  // Show confirmation modal?
  confirmationText?: string;  // For typed confirmations (e.g., "STOP")
  isDisabled?: boolean;  // Disabled state
  cooldownSeconds?: number;  // Prevent double-click
}
```

**KillSwitch Specific Behavior**:
- **Size**: 120px × 120px (large, impossible to miss)
- **Position**: Bottom-right corner, fixed (stays visible on scroll)
- **Color**: #dc2626 (red-600), darkens to #991b1b on hover
- **Icon**: Octagon with X (SVG)
- **Label**: "EMERGENCY STOP" (white, bold)
- **Disabled State**: Grayed out (#9ca3af) when no algorithms active
- **Cooldown**: 5 seconds after use (prevents accidental double-click)
- **Audit**: Every click logged, even if cancelled

**Confirmation Modal** (for EmergencyStop):
```
⚠️ EMERGENCY STOP

This will:
- Cancel all open orders
- Liquidate all positions to AUD
- Disable all algorithms

Type "STOP" to confirm:
[_____________]

[Cancel]  [CONFIRM STOP]
```

**Typed Confirmation Behavior**:
- Input field: type="text", autoFocus
- Match: case-insensitive ("stop" or "STOP" both work)
- "CONFIRM STOP" button: disabled until correct text entered
- On confirm: Button shows spinner, input disabled
- On success: Full-screen green checkmark "All systems halted"
- On error: Show retry prompt with support contact

**File Location**: `frontend/src/components/Floor/SafetyButton.tsx`

**Requirements**: REQ-FL-008

---

### 2.2 Layout Components

#### SplitView
**Purpose**: Two-pane layout for The Lab and 4 Ledgers dashboard

**Usage**:
```typescript
<SplitView
  leftPane={<DataCharts />}
  rightPane={<AgentTerminal />}
  leftWidth={60}  // percentage
  rightWidth={40}
  resizable={true}  // Allow user to drag divider
/>
```

**Layout**:
```
┌─────────────────────────┬───────────────────┐
│  Data / Charts          │  Agent Terminal   │
│  (Left 60%)             │  (Right 40%)      │
│                         │                   │
│  - 4 Ledgers Grid       │  - Streaming logs │
│  - Historical charts    │  - User input     │
│  - Analysis results     │  - Tool outputs   │
└─────────────────────────┴───────────────────┘
```

**Responsive Behavior**:
- Desktop (≥1280px): 60/40 split
- Tablet (768-1279px): 50/50 split
- Mobile (< 768px): Stack vertically, terminal at bottom

**File Location**: `frontend/src/components/Layouts/SplitView.tsx`

---

#### CommandCenter
**Purpose**: Full-width layout for The Floor with P&L ticker and kill switch

**Layout**:
```
┌─────────────────────────────────────────────┐
│  Real-Time P&L Ticker (Always Visible)     │
├──────────────┬──────────────┬───────────────┤
│  Algorithm   │  Active      │  Risk         │
│  Status      │  Positions   │  Metrics      │
│  (33%)       │  (33%)       │  (33%)        │
├──────────────┴──────────────┴───────────────┤
│  Kill Switch                                │
│  (Bottom Bar, Full Width, Red)              │
└─────────────────────────────────────────────┘
```

**Components**:
- **Top Bar**: P&L Ticker (60px height, sticky)
- **Main Grid**: 3 equal columns (1fr 1fr 1fr)
  - Algorithm Status: List of active/paused algorithms
  - Active Positions: Table of open trades
  - Risk Metrics: Drawdown, position usage, win rate
- **Bottom Right**: Kill Switch (fixed position, overlays grid)

**File Location**: `frontend/src/components/Floor/CommandCenter.tsx`

**Requirements**: REQ-FL-004, REQ-FL-008

---

## 3. Interaction Patterns

### 3.1 Real-Time Updates

**Polling** (for non-critical data):
- Use: React Query with `refetchInterval`
- Frequency: 5 seconds for Ledger data
- Implementation:
  ```typescript
  const { data } = useQuery('ledger-data', fetchLedgerData, {
    refetchInterval: 5000,
    refetchOnWindowFocus: true
  });
  ```

**WebSocket** (for critical updates):
- Use: prices, agent logs, P&L
- Library: native WebSocket or socket.io-client
- Reconnection: Auto-retry with exponential backoff
- Implementation:
  ```typescript
  const ws = new WebSocket('wss://api.ohmycoins.com/ws/catalyst/live');
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    updateCatalystAlerts(message);
  };
  ```

**Optimistic UI**:
- Use: User preferences, non-critical mutations
- Pattern: Update UI immediately, rollback on error
- Example: Toggle dark mode (instant feedback, sync to backend)

---

### 3.2 Error Handling

**Network Errors**:
- **Display**: Toast notification (bottom-right, auto-dismiss 5s)
- **Action**: Retry with exponential backoff
- **Message**: "Connection lost. Retrying..." → "Reconnected!"
- **Show retry count**: "Retrying (attempt 3/5)..."

**Validation Errors**:
- **Display**: Inline messages below input fields
- **Highlight**: Red border on invalid field
- **Message**: Specific field error from backend (e.g., "Email already in use")
- **Icon**: Red X icon next to field

**Critical Errors**:
- **Display**: Full-page error boundary
- **Message**: "Something went wrong. Please contact support."
- **Actions**:
  - Button: "Refresh Page"
  - Button: "Contact Support" (opens support email/chat)
  - Display: Error ID for support reference

**Example Error Boundary**:
```typescript
class ErrorBoundary extends React.Component {
  componentDidCatch(error, errorInfo) {
    logErrorToService(error, errorInfo);
    this.setState({ hasError: true, errorId: generateErrorId() });
  }
  
  render() {
    if (this.state.hasError) {
      return <FullPageError errorId={this.state.errorId} />;
    }
    return this.props.children;
  }
}
```

---

### 3.3 Loading States

**Skeleton Screens** (for data-heavy components):
- Use: charts, tables, ledger cards
- Library: `react-loading-skeleton`
- Principle: Match content shape (chart → chart skeleton, table → table skeleton)
- Animation: Subtle shimmer effect (1.5s duration, infinite loop)

**Spinners** (for quick actions):
- Use: Button clicks, form submissions
- Expected duration: < 2 seconds
- Placement: Inline with button text (replace icon or text)
- Example: `[⏳ Saving...]`

**Progress Bars** (for long-running tasks):
- Use: Model training, backtests, large data imports
- Library: Custom progress bar or `rc-progress`
- Display: Percentage complete, estimated time remaining
- Example: `Processing... 67% complete (12 seconds remaining)`

---

### 3.4 Animations & Transitions

**Micro-interactions**:
- Button hover: Scale 1.02, transition 150ms
- Card hover: Shadow elevation increase, transition 200ms
- New data: Fade in with subtle pulse (500ms)

**Page Transitions**:
- Route change: Fade out → fade in (300ms)
- Modal open: Backdrop fade in + modal slide up (200ms)
- Modal close: Modal slide down + backdrop fade out (200ms)

**Performance Considerations**:
- Use `transform` and `opacity` for animations (GPU-accelerated)
- Avoid animating `width`, `height`, `top`, `left` (triggers reflow)
- Respect `prefers-reduced-motion` media query:
  ```css
  @media (prefers-reduced-motion: reduce) {
    * { animation-duration: 0.01ms !important; }
  }
  ```

**Requirements**: Accessibility consideration for motion sensitivity

---

## 4. Data Visualization Standards

### 4.1 Chart Library Selection

| Ledger | Primary Viz | Library | Rationale |
|--------|-------------|---------|-----------|
| Glass | Line (TVL) | recharts | Composable, responsive, dual Y-axis support |
| Human | Heatmap (Sentiment) | visx | Low-level control, calendar heatmap primitives |
| Catalyst | Timeline/Ticker | Custom | Real-time updates, WebSocket integration |
| Exchange | Candlestick/Sparkline | lightweight-charts | High performance, financial chart focus |

### 4.2 Chart Interactions

**Hover**:
- Show tooltip with exact values
- Highlight hovered data point (larger circle)
- Cross-hair lines (optional, for line/candlestick charts)

**Click**:
- Navigate to detail view
- Open drill-down modal
- Select data point (multi-select with Cmd/Ctrl)

**Zoom**:
- Mouse wheel: Zoom in/out (prevent page scroll during zoom)
- Pinch gesture: Zoom on touch devices
- Zoom controls: +/- buttons in chart header

**Pan**:
- Click + drag: Pan chart (for zoomed-in views)
- Touch + drag: Pan on touch devices

---

### 4.3 Color Palette

**Ledger Colors**:
- **Glass**: #3b82f6 (blue-500) - On-chain data, financial metrics
- **Human**: #10b981 (green-500) - Social sentiment, community activity
- **Catalyst**: #f59e0b (amber-500) - Events, alerts, breaking news
- **Exchange**: #8b5cf6 (purple-500) - Trading data, prices, volumes

**Functional Colors**:
- **Danger**: #ef4444 (red-500) - Alerts, losses, emergency actions
- **Success**: #22c55e (green-500) - Profits, confirmations, positive outcomes
- **Warning**: #f59e0b (amber-500) - Warnings, approaching limits
- **Info**: #3b82f6 (blue-500) - Neutral information, helper text
- **Neutral**: #6b7280 (gray-500) - Secondary text, borders

**Chart-Specific**:
- Positive trends: Green (#22c55e)
- Negative trends: Red (#ef4444)
- Neutral/baseline: Gray (#6b7280)
- Volume bars: Semi-transparent blue (#3b82f650)

---

### 4.4 Typography for Charts

**Axis Labels**:
- Font: Inter, 12px
- Color: #6b7280 (gray-500)
- Weight: 400 (regular)

**Chart Title**:
- Font: Inter, 16px
- Color: #111827 (gray-900)
- Weight: 600 (semi-bold)

**Tooltips**:
- Font: Inter, 14px
- Color: #ffffff (white) on dark background
- Weight: 500 (medium)

**Tabular Numbers** (for prices, P&L):
- Use `font-variant-numeric: tabular-nums;`
- Ensures consistent alignment in tables/tickers

---

## 5. Accessibility (WCAG 2.1 AA)

### 5.1 Keyboard Navigation

**All interactive elements must be keyboard-accessible**:
- Tab order: Logical flow (left-to-right, top-to-bottom)
- Focus indicators: Visible outline (2px blue, 4px offset)
- Skip links: "Skip to main content", "Skip to Kill Switch"

**Keyboard Shortcuts**:
- Cmd/Ctrl+K: Global search (future feature)
- Cmd/Ctrl+Shift+T: Toggle table view for charts
- Esc: Close modals
- Space/Enter: Activate buttons

---

### 5.2 Chart Table View Toggle (REQ-UX-001)

**Problem**: Screen readers cannot interpret canvas-based charts

**Solution**: Provide tabular data below each chart with toggle

**Implementation**:
```
[Chart: Glass Ledger TVL]
┌─────────────────────────┐
│  [Line Chart Visual]    │
└─────────────────────────┘
[View as Table] ← Toggle button

When toggled:

| Date       | TVL (USD)  | Fees (USD) |
|------------|------------|------------|
| 2026-01-24 | 42.5B      | 12.3M      |
| 2026-01-23 | 41.8B      | 11.9M      |
| ...        | ...        | ...        |
```

**Table Features**:
- Sortable columns (click header to sort)
- Pagination (50 rows per page)
- Export to CSV
- Keyboard navigation (arrow keys to navigate cells)

**ARIA Attributes**:
```html
<button aria-label="View Glass Ledger data as table" aria-expanded="false">
  View as Table
</button>
```

---

### 5.3 Live Data Announcements

**ARIA Live Regions**:
```html
<div aria-live="polite" aria-atomic="true">
  <!-- Catalyst alerts announced here -->
</div>
```

**Announcement Strategy**:
- **Catalyst alerts**: Announce immediately (aria-live="assertive" for critical)
- **P&L updates**: Only announce significant changes (> 5% to avoid spam)
- **Agent status**: Announce state transitions ("Agent started", "Agent completed")

**Example**:
```typescript
function announceCatalystAlert(alert) {
  const announcement = `New ${alert.priority} alert: ${alert.title}`;
  ariaLiveRegion.textContent = announcement;
}
```

---

### 5.4 Color Contrast

**Minimum Ratios** (WCAG AA):
- Normal text: 4.5:1
- Large text (≥18px or 14px bold): 3:1
- UI components (buttons, inputs): 3:1

**Testing**:
- Use browser DevTools (Chrome Lighthouse)
- Manual testing with contrast checker: https://webaim.org/resources/contrastchecker/

**Common Violations to Avoid**:
- Light gray text on white background (insufficient contrast)
- Amber (#f59e0b) on white (only 2.8:1, use darker shade #d97706)
- Color-only indicators (always pair color with icon or text)

---

## 6. Responsive Design

### 6.1 Breakpoints

| Breakpoint | Width | Target Device | Layout Adjustments |
|------------|-------|---------------|-------------------|
| Mobile | < 768px | Phones | Stack vertically, single column |
| Tablet | 768px - 1279px | iPad, small laptops | 2-column grid, reduced chart size |
| Desktop | ≥ 1280px | Desktop monitors | Full 2x2 grid, all features enabled |

### 6.2 Mobile Strategy

**Phase 1**: Desktop-first (current focus)
- The Lab and The Floor are too complex for mobile
- Focus on desktop/tablet experience
- Mobile redirects to "Desktop required" page

**Phase 2**: Mobile view for 4 Ledgers (read-only)
- Vertical scrolling list (Catalyst → Exchange → Human → Glass)
- Simplified charts (sparklines only)
- No drill-down modals (links to desktop view)

**Phase 3**: Mobile P&L dashboard (The Floor monitoring)
- Read-only P&L ticker
- Algorithm status (running/stopped)
- Emergency "Pause All" button (simplified kill switch)
- No algorithm deployment or configuration

---

### 6.3 Touch Interactions

**Tap Targets**:
- Minimum size: 44px × 44px (Apple HIG, WCAG)
- Spacing: 8px minimum between targets
- Example: Kill Switch is 120px × 120px (well above minimum)

**Gestures**:
- Pinch to zoom (on charts)
- Swipe to dismiss (modals, toasts)
- Long press (show context menu, future feature)

---

## 7. Mobile Strategy

**Phase 1**: Desktop-first (Lab & Floor too complex for mobile)
- Minimum supported width: 1024px
- Mobile users see: "Please open on desktop for full experience"

**Phase 2**: Mobile view for 4 Ledgers (read-only monitoring)
- Simplified cards, vertical scroll
- Touch-optimized controls

**Phase 3**: Mobile-optimized P&L dashboard (Floor monitoring only)
- Real-time P&L ticker
- Emergency pause button
- No trading configuration

**Requirements**: Future enhancement, not blocking MVP

---

## 8. Design Tokens

### 8.1 Spacing Scale

```typescript
const spacing = {
  xs: '4px',   // Tight spacing (icon padding)
  sm: '8px',   // Standard gap between elements
  md: '16px',  // Card padding, section spacing
  lg: '24px',  // Page margins
  xl: '32px',  // Large separators
  xxl: '48px', // Page header spacing
};
```

### 8.2 Border Radius

```typescript
const borderRadius = {
  sm: '4px',   // Buttons, inputs
  md: '8px',   // Cards, modals
  lg: '12px',  // Large containers
  full: '9999px', // Circular (kill switch, avatar)
};
```

### 8.3 Shadows

```typescript
const shadows = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',  // Subtle elevation
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)', // Card hover
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)', // Modal
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)', // Floating elements
};
```

---

## 9. Implementation Guidelines

### 9.1 Component Development Workflow

1. **Design**: Create Figma mockup with annotations
2. **Review**: Product Manager + Frontend Lead approval
3. **Document**: Add component to this design system doc
4. **Build**: Implement in TypeScript + React
5. **Test**: Unit tests (Jest), visual regression (Chromatic)
6. **Story**: Add to Storybook with usage examples
7. **Review**: Code review + design review
8. **Deploy**: Merge to main, deploy Storybook

---

### 9.2 Code Standards

**TypeScript**:
- All components must have TypeScript types
- Use `interface` for props (not `type`)
- Export types alongside components

**Styling**:
- Use Tailwind CSS for utility classes
- Custom styles: CSS modules (`.module.css`)
- Avoid inline styles except for dynamic values

**Accessibility**:
- Every interactive element needs `aria-label` or visible text
- Use semantic HTML (`<button>`, `<nav>`, `<main>`)
- Test with screen reader (VoiceOver on Mac, NVDA on Windows)

**Example Component**:
```typescript
interface LedgerCardProps {
  ledgerType: 'glass' | 'human' | 'catalyst' | 'exchange';
  data: LedgerData;
  onDrillDown?: (id: string) => void;
}

export function LedgerCard({ ledgerType, data, onDrillDown }: LedgerCardProps) {
  return (
    <article
      className="bg-white rounded-lg shadow-md p-4"
      aria-label={`${ledgerType} ledger data`}
    >
      {/* Component content */}
    </article>
  );
}
```

---

## 10. Storybook Integration

### 10.1 Story Structure

Each component should have a Storybook file with these stories:
- **Default**: Standard usage
- **Loading**: Skeleton/spinner state
- **Error**: Error message displayed
- **Empty**: No data state
- **Interactive**: All interactive features enabled

**Example** (`LedgerCard.stories.tsx`):
```typescript
export default {
  title: 'Ledgers/LedgerCard',
  component: LedgerCard,
};

export const Default = () => (
  <LedgerCard ledgerType="glass" data={mockGlassData} />
);

export const Loading = () => (
  <LedgerCard ledgerType="glass" data={null} isLoading={true} />
);

export const Error = () => (
  <LedgerCard ledgerType="glass" data={null} error={new Error('Failed to load')} />
);
```

---

## Document Maintenance

**Update Triggers**:
- New component added to component library
- Design pattern changes (new interaction paradigm)
- Accessibility requirements updated
- New chart type added
- Color palette adjustments

**Review Schedule**:
- Per Sprint: Add new components from sprint work
- Monthly: Design Lead reviews for consistency
- Quarterly: Full audit with Product + Design + Frontend teams

**Ownership**:
- Design Lead: Primary owner, approves all changes
- Frontend Lead: Technical implementation guidance
- Product Manager: User experience validation

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-24  
**Next Review**: 2026-02-24  
**Figma Link**: [To be added]  
**Storybook URL**: [To be deployed]
