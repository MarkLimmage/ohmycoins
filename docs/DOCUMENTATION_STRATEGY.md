# Documentation Strategy & Uplift Plan

**Version**: 1.1  
**Date**: 2026-01-24  
**Status**: DRAFT - Incorporating Consultant Feedback  
**Reviewers**: Development Consultant (2026-01-24)

## Executive Summary

This document defines a comprehensive strategy to transform Oh My Coins documentation from a traditional static model into a **Living Documentation System** integrated into the development workflow. The goal is to prevent documentation sprawl while ensuring complete coverage across all system modules (4 Ledgers, The Lab, The Floor, BYOM).

**Key Principle**: Documentation is code. It lives with code, is validated like code, and is treated as part of the Definition of Done.

---

## 1. Current State Assessment

### 1.1 Existing Documentation Strengths
✅ **SYSTEM_REQUIREMENTS.md**: Excellent EARS-formatted functional requirements for backend systems  
✅ **BYOM Requirements**: Comprehensive security, backend, and data model specifications  
✅ **ARCHITECTURE.md**: Clear microservices structure and system diagram  
✅ **PROJECT_HANDOFF.md**: Good operational context  

### 1.2 Critical Gaps Identified

| Gap Category | Impact | Examples |
|--------------|--------|----------|
| **UI/UX Specifications** | HIGH | No component library specs, no interaction patterns, no data visualization requirements |
| **User Journey Maps** | HIGH | How users flow from Ledgers → Lab → Floor is undocumented |
| **Frontend-Backend Contracts** | MEDIUM | API-to-UI mappings not formalized beyond OpenAPI |
| **Trading Operations** | HIGH | Floor UI controls, safety mechanisms, and risk workflows lack detail |
| **Data Visualization** | HIGH | How to present 4 Ledgers data to users is undefined |

---

## 2. Documentation Architecture: The Tiered Model

### 2.1 The Four-Tier Hierarchy

```
Tier 1: SYSTEM CORE (Low Change Frequency)
├── Single Source of Truth for business logic
├── EARS-formatted requirements
└── Owned by: Product Lead / Tech Lead

Tier 2: FEATURE MODULES (Medium Change Frequency)
├── Feature-specific technical specs
├── User stories and acceptance criteria
└── Owned by: Feature Leads

Tier 3: UI/UX CONTRACTS (High Change Frequency)
├── Component specifications
├── Interaction patterns and workflows
└── Owned by: Frontend Team / Design

Tier 4: AUTO-GENERATED DOCS (Dynamic)
├── OpenAPI/Swagger schemas
├── Database ERD diagrams
└── Owned by: CI/CD Pipeline
```

### 2.2 Tier 1: System Core Documents (3 Master Documents)

#### Document 1: `SYSTEM_REQUIREMENTS.md` (EXISTING - ENHANCE)
**Purpose**: Single Source of Truth for all "The System Shall..." requirements

**Current Structure**: ✅ Already excellent
- Section 3: Data Collection (4 Ledgers) ✅
- Section 7: BYOM Requirements ✅  
- Section 8: Trading Execution (The Floor) ✅

**Enhancement Needed**:
- Add Section 9: **UI/UX Non-Functional Requirements**
  - Response time targets for UI updates
  - Data refresh rates for dashboards
  - Accessibility standards (WCAG 2.1 AA)
- Add Section 10: **Cross-Module Integration Requirements**
  - Lab-to-Floor promotion workflow
  - Ledger-to-Lab data pipeline
  - BYOM integration with all agents

#### Document 2: `USER_JOURNEYS.md` (NEW)
**Purpose**: Persona-driven interaction flows

**Structure**:
```markdown
# User Journeys - Oh My Coins

## Journey 1: The Discovery Flow (4 Ledgers → Lab)
**Persona**: Sarah, Retail Trader
**Goal**: Spot a trend and validate it with AI agents

### Steps:
1. User logs in and navigates to "4 Ledgers Dashboard"
2. User sees Catalyst alert: "SEC filing detected: BlackRock ETF approval"
3. User clicks alert → Catalyst detail modal opens
4. User clicks "Analyze in Lab" button
5. Lab session creation modal opens with pre-filled context
6. User selects LLM model (BYOM or system default)
7. User submits natural language goal: "What's the correlation between ETF filings and BTC price?"
8. Agent orchestrator begins execution...

### UI Touchpoints:
- LedgerDashboard.tsx
- CatalystDetailModal.tsx
- LabSessionCreation.tsx
- AgentTerminal.tsx

### Backend Flows:
- REQ-CL-001, REQ-CL-003 (Catalyst detection)
- REQ-AG-001, REQ-AG-002 (Agent orchestration)
```

**Sections**:
1. Discovery Flow (4 Ledgers → The Lab)
2. BYOM Setup Journey
3. The Lab Analysis Journey (Ad-hoc exploration)
4. Lab-to-Floor Promotion Journey
5. The Floor Monitoring & Risk Management Journey

**Integration with Testing**:
Each user journey MUST have a corresponding Playwright E2E test:
- Journey 1 → `tests/e2e/discovery_flow.spec.ts`
- Journey 2 → `tests/e2e/byom_setup.spec.ts`
- Journey 3 → `tests/e2e/lab_analysis.spec.ts`
- Journey 4 → `tests/e2e/lab_to_floor_promotion.spec.ts`
- Journey 5 → `tests/e2e/floor_risk_management.spec.ts`

This ensures documented workflows remain functional.

#### Document 3: `API_CONTRACTS.md` (NEW)
**Purpose**: Document API interaction patterns and UI behavior contracts (NOT an exhaustive endpoint list)

**Important**: This document defines **patterns** and **UI behaviors** for API interactions. For exact schemas, the FastAPI OpenAPI/Swagger documentation is the single source of truth.

**Structure**:
```markdown
# API-Frontend Integration Contracts

## Purpose & Scope
This document defines:
- **Interaction Patterns**: How the UI handles common API states (loading, error, success)
- **Error Handling Standards**: User-facing messages for HTTP error codes
- **UI Behavior Contracts**: What the frontend displays during API operations
- **Authentication Flows**: Token refresh, session expiry patterns

**NOT Included** (see OpenAPI/Swagger instead):
- Exact request/response schemas (use Pydantic models)
- Complete endpoint catalog (auto-generated)
- Field-level validation rules (defined in code)

## Global API Patterns

## Example: BYOM Configuration

### POST /api/v1/users/me/llm-credentials
**Purpose**: Save new LLM API key

**Frontend Component**: `APIKeyInput.tsx`

**Request**:
```typescript
{
  provider: 'openai' | 'google' | 'anthropic',
  model_name: string,
  api_key: string
}
```

**Success Response (200)**:
```typescript
{
  id: string,
  provider: string,
  model_name: string,
  masked_key: string, // "sk-...xyz"
  created_at: timestamp
}
```

**Error States**:
- 400: Invalid key format → "The API key format is incorrect. Keys should start with 'sk-'."
- 401: Key validation failed → "Could not authenticate with OpenAI. Please check your key."
- 429: Rate limit → "Too many validation attempts. Please try again in 10 minutes."

**UI Behavior**:
- Loading: Show spinner in "Test Connection" button
- Success: Green checkmark, save button enabled
- Error: Red X, error message below input, link to provider docs
```

---

### 2.3 Tier 2: Feature Module Documentation

#### Strategy: Co-locate with Code
Instead of sprawling `/docs`, move feature-specific docs next to implementation:

```
backend/app/services/
├── agent/
│   ├── README.md          # Agent architecture overview
│   ├── ORCHESTRATOR.md    # Orchestrator patterns
│   └── agents/
│       ├── README.md      # Agent catalog
│       └── planner/
│           └── README.md  # Planner agent specifics
│
├── collectors/
│   ├── README.md          # Collector architecture
│   └── catalyst/
│       └── LISTING_DETECTION.md  # Critical path docs
│
└── trading/
    ├── README.md          # Floor architecture
    └── RISK_MANAGEMENT.md # Safety mechanisms

frontend/src/features/
├── lab/
│   ├── README.md          # Lab UI architecture
│   └── AGENT_TERMINAL.md  # Terminal component spec
│
├── ledgers/
│   ├── README.md          # 4 Ledgers UI overview
│   └── CATALYST_ALERTS.md # Critical alerts UI
│
└── trading-floor/
    ├── README.md          # Floor UI architecture
    └── KILL_SWITCH.md     # Emergency stop UI spec
```

**Benefit**: Developers update docs in the same PR as code changes

#### Existing `/docs/requirements/` → Refactor
- **KEEP**: `BYOM_EARS_REQUIREMENTS.md` (reference specification)
- **MOVE**: `BYOM_USER_STORIES.md` → `USER_JOURNEYS.md` (consolidate all journeys)
- **CREATE**: Feature-specific READMEs in code folders

---

### 2.4 Tier 3: UI/UX Documentation (NEW)

#### Document: `docs/ui/DESIGN_SYSTEM.md`
**Purpose**: Component library specification and interaction patterns

**Structure**:
```markdown
# UI Design System

## 1. Design Principles
- **Data Density**: 4 Ledgers require high-information layouts
- **Real-Time First**: All data updates via WebSocket/SSE
- **Safety-Critical UI**: Trading controls must be fail-safe

## 2. Component Library

### Core Components

#### LedgerCard
**Purpose**: Standardized widget for displaying ledger data

**Props**:
```typescript
interface LedgerCardProps {
  ledgerType: 'glass' | 'human' | 'catalyst' | 'exchange';
  data: LedgerData;
  onDrillDown?: (id: string) => void;
  alertLevel?: 'normal' | 'warning' | 'critical';
}
```

**Variants**:
- `GlassLedgerCard`: TVL/Fee line charts (recharts)
- `HumanLedgerCard`: Sentiment heatmap (visx)
- `CatalystLedgerCard`: Event ticker with priority badges
- `ExchangeLedgerCard`: Real-time price sparklines

**States**:
- Loading: Skeleton screen (react-loading-skeleton)
- Error: Retry button with error message
- Empty: "No data available" with data range context
- Live: Auto-updating with last-update timestamp

#### AgentTerminal
**Purpose**: Streaming console for agent execution

**Features**:
- ANSI color support for agent logs
- Auto-scroll to bottom (with sticky-scroll option)
- Searchable transcript
- Copy transcript to clipboard

**Props**:
```typescript
interface AgentTerminalProps {
  sessionId: string;
  streamUrl: string; // WebSocket endpoint
  allowInteraction: boolean; // Enable user input mid-execution
}
```

#### SafetyButton
**Purpose**: Fail-safe control for Floor operations

**Variants**:
- `KillSwitch`: Full red, large, always visible
- `ConfirmTrade`: Two-step confirmation modal
- `EmergencyStop`: Requires typed confirmation: "STOP"

**Props**:
```typescript
interface SafetyButtonProps {
  action: 'kill' | 'confirm' | 'stop';
  onConfirm: () => Promise<void>;
  requireConfirmation: boolean;
  confirmationText?: string; // For typed confirmations
}
```

## 3. Layout Templates

### SplitView (Lab & Ledgers)
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

### CommandCenter (The Floor)
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

## 4. Interaction Patterns

### Real-Time Updates
- **Polling**: Use React Query with 5s refetch for non-critical data
- **WebSocket**: Use for critical updates (prices, agent logs, P&L)
- **Optimistic UI**: Show user actions immediately, rollback on error

### Error Handling
- **Network Errors**: Retry with exponential backoff, show retry count
- **Validation Errors**: Inline messages below inputs, highlight in red
- **Critical Errors**: Full-page error boundary with "Contact Support" CTA

### Loading States
- **Skeleton Screens**: For data-heavy components (charts, tables)
- **Spinners**: For quick actions (< 2s expected)
- **Progress Bars**: For long-running tasks (model training, backtests)

## 5. Data Visualization Standards

### Chart Types by Ledger
| Ledger | Primary Viz | Library | Update Frequency |
|--------|-------------|---------|------------------|
| Glass | Line (TVL) | recharts | Daily |
| Human | Heatmap (Sentiment) | visx | 15 min |
| Catalyst | Timeline/Ticker | Custom | Real-time |
| Exchange | Candlestick/Sparkline | lightweight-charts | 10s |

### Color Palette
- **Glass**: Blue (#3b82f6) - On-chain data
- **Human**: Green (#10b981) - Social sentiment
- **Catalyst**: Amber (#f59e0b) - Events
- **Exchange**: Purple (#8b5cf6) - Trading data
- **Danger**: Red (#ef4444) - Alerts, losses
- **Success**: Green (#22c55e) - Profits, confirmations

## 6. Accessibility

### WCAG 2.1 AA Compliance (Required)
- All interactive elements must be keyboard-navigable
- Color is not the sole indicator of state (use icons + text)
- ARIA labels for screen readers on all charts
- Loading states announced to screen readers

### Trading-Specific Accessibility (REQ-UX-001)
**Chart Table View Toggle**: All charts MUST have a "View as Table" toggle button.
- **Rationale**: Screen readers cannot interpret canvas-based charts (recharts, lightweight-charts)
- **Implementation**: Provide tabular data below each chart with sortable columns
- **Example**: Glass Ledger TVL chart → Show data table with Date, TVL, Fees columns
- **Keyboard Shortcut**: Ctrl+Shift+T to toggle table view globally

**Live Data Announcements**: 
- Catalyst alerts: Announce via ARIA live region ("New critical alert: SEC filing detected")
- P&L updates: Only announce significant changes (>5%) to avoid spam
- Agent status: Announce state transitions ("Agent started", "Agent completed")

## 7. Mobile Strategy
- **Phase 1**: Desktop-first (Lab & Floor too complex for mobile)
- **Phase 2**: Mobile view for 4 Ledgers (read-only monitoring)
- **Phase 3**: Mobile-optimized P&L dashboard (Floor monitoring only)
```

---

#### Document: `docs/ui/DATA_VISUALIZATION_SPEC.md`
**Purpose**: Define exact chart types and data transformations for 4 Ledgers

**Structure**:
```markdown
# Data Visualization Specification

## The 4 Ledgers Dashboard

### Layout
Grid: 2x2 on desktop, 1x4 on tablet, scrollable on mobile

### 1. Glass Ledger Card

#### Primary Chart: TVL Over Time
**Type**: Line chart with dual Y-axis
- **Left Y-axis**: TVL (USD, log scale)
- **Right Y-axis**: Fees (USD, linear scale)
- **X-axis**: Time (last 30 days, daily granularity)

**Data Source**: `GET /api/v1/data/glass?protocol=<protocol>&days=30`

**Response Schema**:
```typescript
interface GlassData {
  protocol: string;
  tvl: Array<{ date: string; value: number }>;
  fees: Array<{ date: string; value: number }>;
  active_addresses?: Array<{ date: string; value: number }>; // Tier 2
}
```

**UI Behavior**:
- Hover: Show exact values in tooltip
- Click data point: Drill down to protocol detail view
- Loading: Show skeleton with approximate data range
- Error: "Unable to load Glass data. Last updated: <timestamp>"

#### Secondary Metrics (Cards)
- **Current TVL**: Large number with 24h % change (green/red)
- **30d Fees**: Sum with average per day
- **Active Addresses** (Tier 2 only): Latest count with trend arrow

### 2. Human Ledger Card

#### Primary Chart: Sentiment Heatmap
**Type**: Calendar heatmap (visx)
- **Cells**: Days (last 30 days)
- **Color**: Intensity of bullish sentiment (green) vs bearish (red)
- **Tooltip**: Top 3 keywords/hashtags for that day

**Data Source**: `GET /api/v1/data/human?days=30`

**Response Schema**:
```typescript
interface HumanData {
  date: string;
  sentiment_score: number; // -1 to +1
  volume: number; // Number of mentions
  top_keywords: string[];
  sources: Array<{ source: 'reddit' | 'news' | 'twitter'; count: number }>;
}[]
```

**UI Behavior**:
- Click cell: Open "Sentiment Detail" modal with news articles
- Filter by source: Toggle Reddit/News/Twitter
- Sentiment threshold: Slider to highlight only strong signals

#### Secondary Metrics
- **Current Sentiment**: Emoji indicator (🔥 bullish, 🧊 bearish, 😐 neutral)
- **Trending Coins**: Top 3 most mentioned today
- **News Volume**: Count with 24h % change

### 3. Catalyst Ledger Card

#### Primary View: Real-Time Event Ticker
**Type**: Scrolling list (auto-updates via WebSocket)
- **Badge**: Event type (Listing, Regulation, Hack, Upgrade)
- **Title**: Short event description
- **Timestamp**: "2 mins ago" (relative time)
- **Priority**: Background color (red=critical, amber=high, gray=normal)

**Data Source**: `WebSocket /ws/catalyst/live`

**WebSocket Message Schema**:
```typescript
interface CatalystEvent {
  id: string;
  type: 'listing' | 'regulation' | 'hack' | 'upgrade' | 'other';
  title: string;
  description: string;
  source: string; // "SEC", "CoinSpot", "Twitter", etc.
  priority: 'critical' | 'high' | 'normal';
  timestamp: string;
  related_coins: string[]; // ["BTC", "ETH"]
}
```

**UI Behavior**:
- Click event: Open detail modal with full description
- Filter by priority: Show only critical/high
- Auto-dismiss: Normal priority events fade after 30 seconds
- Sound alert: Play chime for critical events (user can disable)

#### Secondary Actions
- **Analyze in Lab**: Button to create agent session with event context
- **Set Alert**: Subscribe to similar event types

### 4. Exchange Ledger Card

#### Primary Chart: Multi-Coin Sparklines
**Type**: Small line charts (lightweight-charts)
- **Display**: Top 10 coins by portfolio value
- **Y-axis**: Hidden (relative scale)
- **X-axis**: Last 24h, 5-minute candles
- **Color**: Green if 24h change positive, red if negative

**Data Source**: `GET /api/v1/data/exchange/prices?coins=BTC,ETH&interval=5m&hours=24`

**Response Schema**:
```typescript
interface ExchangePriceData {
  coin: string;
  prices: Array<{ timestamp: string; price: number; volume: number }>;
  change_24h: number; // Percentage
}[]
```

**UI Behavior**:
- Hover: Show current price and 24h change
- Click: Navigate to detailed coin chart page
- Real-time: Updates every 10 seconds via polling

#### Secondary Metrics
- **Portfolio Value**: Total AUD value with 24h % change
- **Top Gainer**: Coin with highest 24h % gain (green highlight)
- **Top Loser**: Coin with lowest 24h % loss (red highlight)

---

## Lab UI Specifications

### Agent Terminal Component

#### Streaming Logs Display
**Type**: Virtual scrolling list (react-window)
- **Message Types**:
  - `agent_thought`: Gray text, italicized
  - `tool_invocation`: Blue, indented with icon
  - `tool_result`: Green (success) / Red (error), code block
  - `user_input_request`: Amber, with input field
  - `final_output`: Bold, highlighted background

**WebSocket Data Source**: `/ws/agent/session/<session_id>`

**Message Schema**:
```typescript
interface AgentMessage {
  id: string;
  type: 'thought' | 'tool' | 'result' | 'input_request' | 'output';
  content: string;
  timestamp: string;
  metadata?: {
    tool_name?: string;
    execution_time?: number; // milliseconds
    error?: string;
  };
}
```

**UI Features**:
- **Syntax Highlighting**: Use `react-syntax-highlighter` for code blocks
- **Copy Button**: On hover over code blocks
- **Timestamp Toggle**: Show/hide timestamps
- **Search**: Ctrl+F to search transcript
- **Export**: Download full transcript as .txt

---

## Floor UI Specifications

### Kill Switch Component

#### Visual Design
- **Size**: 120px x 120px (large, always visible)
- **Position**: Bottom-right corner, fixed
- **Color**: #dc2626 (red-600)
- **Icon**: Octagon with X
- **Label**: "EMERGENCY STOP"

#### Interaction Flow
1. User clicks Kill Switch
2. Confirmation modal appears:
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
3. User types "STOP" (case-insensitive)
4. Confirm button enables
5. On confirm:
   - POST /api/v1/floor/emergency-stop
   - Show loading spinner
   - On success: Full-screen green checkmark "All systems halted"
   - On error: Retry prompt with support contact

#### Safety Features
- **Disabled State**: Grayed out if no algorithms active
- **Cooldown**: 5-second cooldown after use (prevent accidental double-click)
- **Audit Log**: Every click logged (even if cancelled)

#### Disconnected State (Critical Requirement)
**Problem**: What if the WebSocket connection drops during trading?

**Solution**:
1. **Visual Indicator**: Red "DISCONNECTED" banner at top of screen
2. **Kill Switch Behavior**: 
   - If WebSocket down > 5 seconds, automatically enable "Fallback Mode"
   - Kill Switch uses REST API fallback: `POST /api/v1/floor/emergency-stop`
   - If both WebSocket AND REST fail, show "MANUAL INTERVENTION REQUIRED" with support phone number
3. **Reconnection**: Auto-retry WebSocket connection every 2 seconds
4. **Data Staleness**: Display "Last updated: X seconds ago" on all real-time data
5. **Algorithm Pause**: Automatically pause all algorithms if disconnected > 30 seconds

**Requirement ID**: REQ-FL-DISC-001 (add to SYSTEM_REQUIREMENTS.md)

### P&L Ticker

#### Design
- **Bar Height**: 60px
- **Position**: Top of Floor view, full width
- **Background**: Gradient (green if positive P&L, red if negative)
- **Font**: Tabular numbers (for alignment)

#### Data Display
```
Realized P&L: +$1,234.56 | Unrealized P&L: -$234.12 | Total: +$1,000.44 | Drawdown: 5.2% ⚠️
```

**Update Frequency**: Every 2 seconds via WebSocket

**Alert Thresholds**:
- **Warning** (Amber ⚠️): Drawdown > 5%
- **Critical** (Red 🚨): Drawdown > 10% (also triggers audio alert)

---

## Responsiveness Strategy

### Breakpoints
- **Desktop**: >= 1280px (Full 2x2 ledger grid)
- **Tablet**: 768px - 1279px (2x2 grid, smaller cards)
- **Mobile**: < 768px (Single column, prioritize Catalyst & Exchange)

### Mobile-Specific Adjustments
- **4 Ledgers**: Show Catalyst first (most time-sensitive), then Exchange
- **Lab**: Desktop-only (too complex for mobile)
- **Floor**: Read-only P&L monitoring (no trading controls)

---

## Performance Targets

| Component | Initial Load | Update Latency | Data Retention |
|-----------|--------------|----------------|----------------|
| 4 Ledgers Dashboard | < 2s | < 500ms | 30 days |
| Agent Terminal | < 1s | < 100ms | Session lifetime |
| Floor P&L Ticker | < 500ms | < 2s | Real-time only |
| Charts (Lazy Load) | < 3s | N/A | As specified |

---

## Accessibility Compliance

### WCAG 2.1 AA Standards
- **Color Contrast**: Minimum 4.5:1 for text, 3:1 for UI components
- **Keyboard Navigation**: All actions accessible via keyboard (Tab, Enter, Esc)
- **Screen Reader Support**: ARIA labels on all non-text content
- **Motion**: Respect `prefers-reduced-motion` for animations

### Critical Features
- **Live Regions**: Announce new Catalyst alerts to screen readers
- **Focus Management**: Trap focus in modals, restore on close
- **Skip Links**: "Skip to Kill Switch" for Floor view
```

---

### 2.5 Tier 4: Auto-Generated Documentation

#### Strategy: Leverage Existing Tools
1. **OpenAPI/Swagger**: Already generated by FastAPI
   - Ensure all endpoints have `description` fields
   - Use Pydantic `Field(description="...")` for all models

2. **Database Schema Diagrams**: Auto-generate with each migration
   ```bash
   # In CI/CD after migrations
   postgresql_autodoc -d ohmycoins -o docs/schema/database_schema
   ```

3. **Component Documentation**: Use Storybook for React components
   ```bash
   # Add to frontend
   npm install --save-dev @storybook/react
   ```

---

## 3. Integration with Development Workflow

### 3.1 Documentation-as-Code Practices

#### Requirement: Link PRs to Requirements
Every PR must reference a requirement ID:

```markdown
## PR #123: Implement Catalyst Alert UI

**Requirements**: REQ-CL-001, REQ-CL-003, NFR-P-001

**Documentation Updated**:
- ✅ Updated `frontend/src/features/ledgers/README.md` (component usage)
- ✅ Added screenshots to `docs/ui/CATALYST_ALERTS.md`
- ❌ N/A: No SYSTEM_REQUIREMENTS changes (backend only)

**Tests**:
- Unit: 12 tests added
- E2E: `tests/ui/catalyst-alerts.spec.ts` added
```

#### Tool: PR Template
Create `.github/pull_request_template.md`:

```markdown
## Description
<!-- What does this PR do? -->

## Requirements Addressed
<!-- List requirement IDs: REQ-XX-XXX -->

## Documentation Updates
- [ ] Updated relevant README.md files
- [ ] Updated SYSTEM_REQUIREMENTS.md (if requirements changed)
- [ ] Updated UI specs (if frontend changes)
- [ ] Updated API_CONTRACTS.md (if API changes)
- [ ] N/A: No documentation changes needed

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] E2E tests added/updated (if UI changes)

## Screenshots (if UI changes)
<!-- Add before/after screenshots -->
```

### 3.2 Automated Documentation Checks

#### Pre-Commit Hook: Markdown Linting
```bash
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.39.0
    hooks:
      - id: markdownlint
        args: ['--fix']
```

#### CI/CD: Link Validation
```yaml
# .github/workflows/docs-check.yml
name: Documentation Check

on: [pull_request]

jobs:
  validate-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Check for broken internal links
        uses: gaurav-nelson/github-action-markdown-link-check@v1
        with:
          use-quiet-mode: 'yes'
          config-file: '.markdown-link-check.json'
      
      - name: Verify requirement IDs
        run: |
          # Check that all REQ-XX-XXX in code have corresponding entries in SYSTEM_REQUIREMENTS.md
          python scripts/validate_requirement_ids.py
```

### 3.3 Documentation Review Process

#### Definition of Done (DoD) Expansion
Add to existing DoD:

```markdown
## Documentation Criteria
- [ ] If requirements changed: SYSTEM_REQUIREMENTS.md updated with EARS syntax
- [ ] If UI changed: Component added to Storybook with usage examples
- [ ] If API changed: OpenAPI descriptions updated (Field(...) in Pydantic models)
- [ ] If workflow changed: USER_JOURNEYS.md updated
- [ ] Feature README.md updated in relevant service folder
```

---

## 4. Migration Plan: Existing Docs → New Structure

### Phase 1: Consolidation (Week 1)
**Goal**: Reduce fragmentation, establish Tier 1 docs

**Actions**:
1. ✅ Keep `SYSTEM_REQUIREMENTS.md` as-is (already excellent)
2. Create `USER_JOURNEYS.md`:
   - Migrate BYOM user stories
   - Add Lab journey
   - Add Floor journey
3. Create `API_CONTRACTS.md`:
   - Extract API-UI mappings from ARCHITECTURE.md
   - Add error state specifications
4. Archive outdated plans:
   - Move `/docs/archive/decisions/` to `/docs/archive/history/`

**Deliverable**: 3 core Tier 1 documents established

### Phase 2: UI/UX Documentation (Week 2)
**Goal**: Close the UI specification gap

**Actions**:
1. Create `docs/ui/` folder
2. Write `DESIGN_SYSTEM.md` (component library)
3. Write `DATA_VISUALIZATION_SPEC.md` (4 Ledgers charts)
4. Write `TRADING_UI_SPEC.md` (The Floor controls with disconnected state)
5. Add accessibility requirements (table view toggles, ARIA live regions)

**Deliverable**: Frontend team has actionable component specs

### Phase 3: Code Co-location (Week 3)
**Goal**: Move feature docs next to code

**Actions**:
1. Create README.md in each service folder:
   - `backend/app/services/agent/README.md`
   - `backend/app/services/collectors/README.md`
   - `frontend/src/features/lab/README.md`
   - `frontend/src/features/ledgers/README.md`
2. Update `docs/requirements/BYOM_USER_STORIES.md` to reference co-located docs
3. Add "See also: [link]" cross-references

**Deliverable**: Documentation lives with code

### Phase 4: Automation (Week 4)
**Goal**: Integrate docs into CI/CD

**Actions**:
1. Set up Storybook for React components
2. Add pre-commit hooks for markdown linting
3. Create GitHub Actions workflow for doc validation
4. Add PR template requiring doc updates
5. Create `scripts/validate_requirement_ids.py`

**Deliverable**: Automated enforcement of doc standards

---

## 5. Governance & Maintenance

### 5.1 Documentation Ownership Matrix

| Document | Primary Owner | Review Cadence | Update Trigger |
|----------|---------------|----------------|----------------|
| SYSTEM_REQUIREMENTS.md | Tech Lead | Quarterly | New feature specs |
| USER_JOURNEYS.md | Product Manager | Monthly | UX changes |
| API_CONTRACTS.md | Backend Lead | Per Release | API changes |
| Design System | Design Lead | Monthly | New components |
| Service READMEs | Feature Teams | Continuous | Code changes |

### 5.2 Review Schedule

#### Weekly: Doc Hygiene Check
- Review open PRs for "Documentation Updated" checklist
- Identify orphaned docs (not updated in > 3 months)
- Check for broken internal links

#### Monthly: Content Audit
- Review Tier 1 docs for accuracy
- Update USER_JOURNEYS if workflows changed
- Archive obsolete feature docs

#### Quarterly: Architecture Sync
- Validate that ARCHITECTURE.md matches actual system
- Update SYSTEM_REQUIREMENTS with new NFRs
- Review and consolidate feature READMEs

### 5.3 Metrics for Success

| Metric | Target | Measurement |
|--------|--------|-------------|
| PRs with Doc Updates | > 80% | GitHub PR analytics |
| Broken Links | 0 | CI/CD check |
| Orphaned Docs (>6mo old) | < 5 | Manual audit |
| Time to Find Info | < 2 min | Developer survey |
| New Dev Onboarding | < 2 days | Survey after 1 week |

---

## 6. Tools & Resources

### 6.1 Recommended Tools

| Purpose | Tool | Rationale |
|---------|------|-----------|
| Markdown Editing | Obsidian / Notion | Internal linking, graph view |
| Diagram Creation | Mermaid.js (in-doc) | Text-based, version-controlled |
| API Documentation | FastAPI OpenAPI | Auto-generated from code |
| Component Docs | Storybook | Visual component library |
| Link Validation | markdown-link-check | CI/CD automation |
| Requirement Tracking | Linear / Jira | Link issues to REQ-IDs |

### 6.2 Documentation Templates

#### Template: Feature README.md
```markdown
# <Feature Name>

## Overview
Brief description (2-3 sentences)

## Architecture
Mermaid diagram or link to ARCHITECTURE.md

## Requirements
Links to relevant REQ-IDs in SYSTEM_REQUIREMENTS.md

## API Endpoints
- `GET /api/v1/...` - Description
- `POST /api/v1/...` - Description

## Database Schema
- Tables: ...
- Key relationships: ...

## Testing
- Unit tests: `tests/unit/<feature>/`
- Integration tests: `tests/integration/<feature>/`

## Dependencies
- Internal: Other services this depends on
- External: Third-party APIs

## Troubleshooting
Common issues and solutions

## See Also
- [Parent Architecture](../../ARCHITECTURE.md)
- [API Contracts](../../../docs/API_CONTRACTS.md)
```

---

## 7. Success Criteria

### 7.1 Phase 1 Completion (Week 1)
- ✅ 3 Tier 1 master documents established
- ✅ USER_JOURNEYS.md covers all major workflows
- ✅ API_CONTRACTS.md has 100% endpoint coverage

### 7.2 Phase 2 Completion (Week 2)
- ✅ Frontend team can build components from specs
- ✅ DATA_VISUALIZATION_SPEC.md defines all 4 Ledgers charts
- ✅ TRADING_UI_SPEC.md covers all Floor safety mechanisms
- ✅ Disconnected state behavior documented for The Floor
- ✅ Accessibility requirements include table view toggles
- ✅ All charts have WCAG 2.1 AA compliant alternatives

### 7.3 Phase 3 Completion (Week 3)
- ✅ Every service folder has a README.md
- ✅ Feature docs co-located with code
- ✅ Zero orphaned docs in `/docs`

### 7.4 Phase 4 Completion (Week 4)
- ✅ CI/CD blocks PRs with broken doc links
- ✅ Storybook deployed with component library
- ✅ 100% of PRs reference requirement IDs

### 7.5 Long-Term Success (3 Months)
- ✅ New developers onboard in < 2 days
- ✅ Time to find documentation < 2 minutes
- ✅ Zero critical bugs due to misunderstood requirements
- ✅ Documentation perceived as asset, not burden

---

## 8. Next Steps

### Immediate Actions (This Week)
1. **Review & Approve** this strategy document
2. **Create** USER_JOURNEYS.md (prioritize BYOM + The Lab flows)
3. **Create** API_CONTRACTS.md (focus on error handling patterns, NOT endpoint catalog)
4. **Draft** DATA_VISUALIZATION_SPEC.md (4 Ledgers section)
5. **Link E2E Tests**: Create skeleton Playwright tests for each user journey

### Sprint 2.14 Integration
- Allocate 20% of sprint capacity to doc uplift
- Assign owners for each Tier 1 document
- Set up PR template and CI/CD checks
- Train team on new documentation standards

### Future Enhancements
- Interactive API documentation (Swagger UI theming)
- Video walkthroughs for complex workflows
- Auto-generated architecture diagrams from code
- AI-powered doc search (RAG on internal docs)

---

## Appendix: Document Inventory

### Current State (Pre-Migration)
```
docs/
├── SYSTEM_REQUIREMENTS.md         ✅ Excellent (keep)
├── ARCHITECTURE.md                 ✅ Good (enhance)
├── PROJECT_HANDOFF.md              ✅ Good (keep)
├── TESTING.md                      ✅ Good (keep)
├── requirements/
│   ├── BYOM_EARS_REQUIREMENTS.md   ✅ Reference (keep)
│   └── BYOM_USER_STORIES.md        ⚠️ Migrate to USER_JOURNEYS.md
├── archive/
│   └── ...                         ✅ Good (maintain)
└── ... (deployment, security)      ✅ Good (keep)
```

### Target State (Post-Migration)
```
docs/
├── SYSTEM_REQUIREMENTS.md         [Tier 1] Core requirements
├── USER_JOURNEYS.md                [Tier 1] Workflow documentation
├── API_CONTRACTS.md                [Tier 1] Frontend-Backend contracts
├── ARCHITECTURE.md                 [Tier 1] System design
├── ui/
│   ├── DESIGN_SYSTEM.md            [Tier 3] Component library
│   ├── DATA_VISUALIZATION_SPEC.md  [Tier 3] Chart specifications
│   └── TRADING_UI_SPEC.md          [Tier 3] Floor UI details
├── requirements/
│   └── BYOM_EARS_REQUIREMENTS.md   [Reference] BYOM spec
└── archive/                        [Historical]

backend/app/services/
├── agent/README.md                 [Tier 2] Feature docs
├── collectors/README.md            [Tier 2] Feature docs
└── trading/README.md               [Tier 2] Feature docs

frontend/src/features/
├── lab/README.md                   [Tier 2] Feature docs
├── ledgers/README.md               [Tier 2] Feature docs
└── trading-floor/README.md         [Tier 2] Feature docs
```

---

## 9. Consultant Feedback Integration

### 9.1 Key Recommendations Adopted

✅ **API_CONTRACTS Refactored**: Now focuses on interaction patterns rather than exhaustive endpoint listings. OpenAPI/Swagger is the source of truth for schemas.

✅ **User Journeys → E2E Tests**: Each documented user journey now requires a corresponding Playwright test to ensure functional validation.

✅ **Disconnected State Requirement**: Added comprehensive "what if WebSocket drops" requirements for The Floor, including fallback REST API behavior.

✅ **Accessibility Enhanced**: Added REQ-UX-001 requiring "Table View" toggles for all charts to support screen readers.

✅ **Nomenclature Standardized**: "The Lab" and "The Floor" consistently capitalized throughout to maintain brand identity.

### 9.2 Implementation Priority Adjustments

**High Priority** (Week 1-2):
1. API_CONTRACTS.md with global error handling patterns
2. Disconnected state specifications for The Floor
3. Table view accessibility requirements

**Medium Priority** (Week 3):
1. E2E test skeleton creation for all user journeys
2. Chromatic visual regression setup for Storybook

**Low Priority** (Week 4):
1. Video walkthroughs for complex workflows
2. AI-powered doc search

### 9.3 Risk Mitigation Strategy

**Primary Risk**: API_CONTRACTS.md drifting out of sync with code

**Mitigation**:
1. CI/CD check: Compare Pydantic models against API_CONTRACTS patterns
2. Quarterly audit: Backend lead reviews for alignment
3. PR template explicitly asks: "Did you update API interaction patterns?"

**Secondary Risk**: User Journeys becoming stale

**Mitigation**:
1. E2E tests serve as living documentation
2. Failing E2E test = outdated journey documentation
3. Monthly review of journey→test linkage

---

**End of Documentation Strategy**

**Review Status**: v1.1 - Consultant feedback incorporated  
**Next Review**: After Phase 1 completion  
**Approval Required**: Tech Lead, Product Manager, Frontend Lead  
**Contact**: Development Team Lead
