# Component Library - Oh My Coins

**Version**: 1.0  
**Date**: 2026-01-24  
**Status**: Active

## Architecture Overview

This document describes the component architecture for the Oh My Coins platform, implementing requirements REQ-UX-001, REQ-UX-004, and REQ-UX-005 for accessibility and user experience.

### Core Design Principles

1. **Accessibility First (WCAG 2.1 AA)**
   - All components keyboard-accessible (Tab, Shift+Tab, Enter, Esc)
   - ARIA labels on all interactive elements
   - Focus indicators: 2px solid blue (#3b82f6) outline with 4px offset
   - Focus indicators meet 3:1 contrast ratio requirement
   - Color never the sole indicator of state

2. **Data Visualization Accessibility (REQ-UX-001)**
   - All charts provide table view toggle
   - Global keyboard shortcut: Ctrl+Shift+T toggles all table views
   - Tables support keyboard navigation and CSV export

3. **Real-Time First**
   - Components designed for WebSocket/SSE updates
   - Smooth animations for data transitions
   - Never block user interaction during updates

4. **Safety-Critical Design**
   - Confirmation flows for destructive actions
   - Typed confirmations for emergency operations
   - Audit logging for safety-critical interactions

## Component Directory Structure

```
components/
├── Ledgers/
│   ├── LedgerCard.tsx          # Base card component
│   ├── GlassLedgerCard.tsx     # Glass ledger variant
│   ├── HumanLedgerCard.tsx     # Human ledger variant
│   ├── CatalystLedgerCard.tsx  # Catalyst ledger variant
│   ├── ExchangeLedgerCard.tsx  # Exchange ledger variant
│   └── LedgerTableView.tsx     # Accessible table view (REQ-UX-001)
├── Lab/
│   ├── AgentTerminal.tsx       # Streaming console for agent logs
│   └── AgentMessage.tsx        # Individual message component
├── Floor/
│   ├── SafetyButton.tsx        # Base safety button
│   ├── KillSwitch.tsx          # Emergency stop variant
│   ├── ConfirmTrade.tsx        # Trade confirmation variant
│   └── EmergencyStop.tsx       # Typed confirmation variant
└── Common/
    ├── LoadingSkeleton.tsx     # Skeleton screen component
    └── ErrorBoundary.tsx       # Error boundary wrapper
```

## Component Specifications

### LedgerCard

**Purpose**: Standardized widget for displaying ledger data across 4 Ledgers dashboard

**Props**:
```typescript
interface LedgerCardProps {
  ledgerType: 'glass' | 'human' | 'catalyst' | 'exchange';
  data: LedgerData;
  onDrillDown?: (id: string) => void;
  alertLevel?: 'normal' | 'warning' | 'critical';
  isLoading?: boolean;
  error?: Error | null;
  showTableView?: boolean;
  onToggleTableView?: () => void;
}
```

**Variants**:
- **GlassLedgerCard**: TVL/Fee line charts (recharts)
- **HumanLedgerCard**: Sentiment heatmap
- **CatalystLedgerCard**: Event ticker with priority badges
- **ExchangeLedgerCard**: Real-time price sparklines

**States**:
- **Loading**: Skeleton screen (preserves layout)
- **Error**: Retry button with error message and timestamp
- **Empty**: "No data available" with suggestions
- **Live**: Auto-updating with timestamp and pulse animation

**Accessibility Features (REQ-UX-001, REQ-UX-005)**:
- ARIA labels describing chart content and trends
- Table view toggle for screen readers
- Keyboard navigation (Tab, Enter)
- Focus indicators on all interactive elements

**Performance Target**: < 100ms render time (NFR-UX-P-003)

### AgentTerminal

**Purpose**: Streaming console for agent execution with real-time logs

**Props**:
```typescript
interface AgentTerminalProps {
  sessionId: string;
  streamUrl: string;
  allowInteraction: boolean;
  onExport?: () => void;
  onCancel?: () => void;
}
```

**Features**:
- **ANSI Color Support**: Parses escape codes for colored logs
- **Virtual Scrolling**: Uses react-window for performance
- **Auto-scroll**: Scrolls to bottom on new messages
- **Search**: Ctrl/Cmd+F to search transcript
- **Copy**: Export transcript to clipboard

**Message Types**:
- Thought: Agent reasoning (gray italic)
- Tool: Tool invocation (blue with icon)
- Result: Tool output (green success / red error)
- Input Request: User input needed (amber)
- Output: Final result (bold)

**Accessibility Features (REQ-UX-004, REQ-UX-005)**:
- ARIA live regions for new messages
- Keyboard shortcuts (Ctrl+F search, Ctrl+C copy)
- Tab navigation for all controls
- Screen reader announcements for status changes

**Performance Target**: < 100ms update latency (NFR-UX-P-002)

### SafetyButton

**Purpose**: Fail-safe control for trading operations

**Props**:
```typescript
interface SafetyButtonProps {
  action: 'kill' | 'confirm' | 'stop';
  onConfirm: () => Promise<void>;
  requireConfirmation: boolean;
  confirmationText?: string;
  isDisabled?: boolean;
  cooldownSeconds?: number;
}
```

**Variants**:
- **KillSwitch**: Large red button (120x120px), fixed position
- **ConfirmTrade**: Two-step confirmation modal
- **EmergencyStop**: Requires typed "STOP" confirmation

**Safety Features**:
- 5-second cooldown after use
- Audit logging for all clicks
- Confirmation modals for destructive actions
- Clear warning messages

**Accessibility Features (REQ-UX-004, REQ-UX-005, REQ-UX-009)**:
- Detailed aria-describedby for emergency actions
- Keyboard shortcut: Ctrl+Shift+K focuses Kill Switch
- ARIA live regions with assertive priority for confirmations
- Focus trap in confirmation modals

**Performance Target**: < 50ms interaction latency (NFR-UX-P-004)

## Global Features

### Keyboard Shortcuts (REQ-UX-004)

| Shortcut | Action |
|----------|--------|
| Ctrl+Shift+K | Focus Kill Switch (when active) |
| Ctrl+Shift+T | Toggle all table views |
| Tab / Shift+Tab | Navigate between elements |
| Enter / Space | Activate focused element |
| Esc | Close modals/dialogs |

### Color Palette

**Ledger Colors**:
- Glass: #3b82f6 (blue-500)
- Human: #10b981 (green-500)
- Catalyst: #f59e0b (amber-500)
- Exchange: #8b5cf6 (purple-500)

**Functional Colors**:
- Danger: #ef4444 (red-500)
- Success: #22c55e (green-500)
- Warning: #f59e0b (amber-500)
- Info: #3b82f6 (blue-500)
- Neutral: #6b7280 (gray-500)

### Error Handling

**Network Errors**:
- Toast notification with auto-dismiss
- Retry with exponential backoff
- Connection status indicators

**Validation Errors**:
- Inline messages below inputs
- Red border on invalid fields
- Specific error messages from backend

**Critical Errors**:
- Full-page error boundary
- Error ID for support reference
- Contact support button

## Testing Strategy

### Accessibility Testing
- Keyboard navigation test for all interactive elements
- Screen reader compatibility (NVDA, JAWS, VoiceOver)
- Color contrast validation (3:1 minimum for focus, 4.5:1 for text)
- ARIA attribute validation

### Performance Testing
- Render time benchmarks
- Update latency measurements
- Virtual scrolling performance
- Memory leak detection

### Integration Testing
- WebSocket connection handling
- API error scenarios
- Loading states
- Empty states

## Implementation Notes

### Styling Approach
- Uses Chakra UI component library
- Utility-first approach with Chakra's style props
- Custom theme tokens for brand colors
- Responsive design with Chakra's breakpoint system

### State Management
- React Query for API data fetching
- Local component state for UI interactions
- Context API for global keyboard shortcuts
- WebSocket state managed at component level

### Dependencies
- @chakra-ui/react: UI component library
- @tanstack/react-query: Data fetching
- react-icons: Icon library
- recharts: Chart library (to be added)
- react-window: Virtual scrolling (to be added)
- react-syntax-highlighter: Code highlighting (to be added)

## Requirements Traceability

| Requirement | Component | Implementation |
|-------------|-----------|----------------|
| REQ-UX-001 | LedgerCard | Table view toggle for all chart variants |
| REQ-UX-002 | LedgerTableView | Keyboard navigation, sorting, CSV export |
| REQ-UX-003 | LedgerCard | Descriptive ARIA labels on charts |
| REQ-UX-004 | Global | Keyboard shortcuts (Ctrl+Shift+K, Ctrl+Shift+T) |
| REQ-UX-005 | All | Tab/Shift+Tab navigation, Enter/Space activation |
| REQ-UX-006 | All | 2px focus outline, 3:1 contrast ratio |
| REQ-UX-007 | SafetyButton | ARIA live regions with assertive priority |
| REQ-UX-008 | AgentTerminal | ARIA live regions with polite priority |
| REQ-UX-009 | KillSwitch | Detailed aria-describedby description |

## Next Steps

1. Implement LedgerCard component with all variants and states
2. Implement AgentTerminal with virtual scrolling and ANSI support
3. Implement SafetyButton with all variants and confirmation flows
4. Add global keyboard shortcut handler
5. Create accessibility test suite
6. Validate against WCAG 2.1 AA standards
