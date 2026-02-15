# User Journeys - Oh My Coins

**Version**: 1.0  
**Date**: 2026-01-24  
**Status**: ACTIVE  
**Purpose**: Define persona-driven user interaction flows across all Oh My Coins modules

---

## Overview

This document defines the end-to-end user journeys across the Oh My Coins platform, linking UI touchpoints with backend requirements and E2E tests. Each journey is designed to be self-validating through automated Playwright tests.

**Covered Modules:**
- 4 Ledgers (Glass, Human, Catalyst, Exchange)
- The Lab (Agentic Data Science)
- The Floor (Algorithmic Trading)
- BYOM (Bring Your Own Model)
- Collector Management (Admin Only)

---

## 5. Collector Management (Admin Only)

**Goal**: Full lifecycle control over data collection sources, including creation, configuration, execution, and monitoring.

### J-COLL-001: Create and Activate New Collector
**Persona:** Administrator (Superuser)  
**Precondition:** Admin is logged in.

**Steps:**
1.  Admin navigates to **Connectors > Collectors** dashboard.
2.  Clicks **"Create Collector"**.
3.  Selects collector type (e.g., "Exchange API", "Web Scraper").
4.  Fills out **Details**:
    *   **Name**: "CoinGecko Market Data"
    *   **Endpoint URL**: `https://api.coingecko.com/api/v3/coins/markets`
    *   **Schedule**: `Every 5 minutes`
    *   **API Key**: `...` (optional)
5.  If "Web Scraper", defines scraping logic (e.g., CSS selectors).
6.  Tests logic with **"Test Run"** button (dry run).
7.  Clicks **"Save & Activate"**.
8.  **Result**: Collector appears in the dashboard with status **ACTIVE**.

### J-COLL-002: Monitor and Update Collector
**Persona:** Administrator (Superuser)  
**Precondition:** At least one collector is active.

**Steps:**
1.  Admin navigates to **Connectors > Collectors**.
2.  Views the **Collection Dashboard**:
    *   Sees list of collectors with status (`Running`, `Paused`, `Error`).
    *   Checks "Last Run" timestamp and "Success Rate".
3.  Identifies a failed collector (marked **Red**).
4.  Clicks on the collector to view **Logs**.
5.  Analyzes the error (e.g., 429 Too Many Requests).
6.  Updates the configuration:
    *   Decreases the **Frequency** or updates the **API Key**.
7.  Clicks **"Update"**.
8.  Manually triggers a run via **"Run Now"**.
9.  **Result**: Execution succeeds, status updates to **ACTIVE**.

### J-COLL-003: Pause and Resume Collection
**Persona:** Administrator (Superuser)  
**Precondition:** Collector is running.

**Steps:**
1.  Admin navigates to **Connectors > Collectors**.
2.  Locates an active collector.
3.  Clicks the **"Pause"** toggle.
4.  **Result**: Status updates to **PAUSED**. No further scheduled executions occur.
5.  Later, Admin clicks **"Resume"**.
6.  **Result**: Status updates to **ACTIVE**. Schedule resumes.

---

## Journey 1: The Discovery Flow (4 Ledgers → The Lab)

**Persona**: Sarah, Retail Trader  
**Goal**: Spot a market trend using 4 Ledgers data and validate it with AI agents  
**Entry Point**: 4 Ledgers Dashboard  
**Success Metric**: Completed agent analysis session with actionable insights

### Journey Steps

#### Step 1: Dashboard Login & Overview
**Action**: User logs in and navigates to "4 Ledgers Dashboard"

**UI State**:
- Four cards displayed in 2x2 grid (desktop)
- Glass Ledger: Shows TVL line chart for top protocols
- Human Ledger: Sentiment heatmap for last 30 days
- Catalyst Ledger: Real-time event ticker with live updates
- Exchange Ledger: Price sparklines for user's portfolio coins

**Backend Flow**:
- GET /api/v1/data/glass?days=30
- GET /api/v1/data/human?days=30
- WebSocket /ws/catalyst/live (subscribes to real-time events)
- GET /api/v1/data/exchange/prices?coins=BTC,ETH&hours=24

**Requirements**: REQ-GL-001, REQ-HL-001, REQ-CL-001, REQ-EL-001

---

#### Step 2: Catalyst Alert Detection
**Action**: User sees Catalyst alert: "🔥 CRITICAL: SEC filing detected - BlackRock Spot Bitcoin ETF approval"

**UI State**:
- Red banner appears at top of Catalyst Ledger card
- Alert badge shows "CRITICAL" with priority color
- Sound chime plays (if user has audio enabled)
- Alert text: "2 mins ago | Source: SEC.gov | Related coins: BTC"

**Backend Flow**:
- WebSocket message received:
  ```json
  {
    "type": "listing",
    "priority": "critical",
    "title": "SEC filing detected - BlackRock ETF approval",
    "source": "SEC",
    "related_coins": ["BTC"],
    "timestamp": "2026-01-24T15:32:00Z"
  }
  ```
- ARIA live region announces: "New critical alert: SEC filing detected"

**Requirements**: REQ-CL-001, REQ-CL-003, NFR-CL-001 (< 30s latency)

---

#### Step 3: Drill Down to Catalyst Details
**Action**: User clicks on the alert card

**UI State**:
- Modal opens: "Catalyst Event Details"
- Displays full description, source link, timestamp
- Shows related coins with 24h price impact
- Button: "Analyze in Lab" (primary CTA)
- Button: "Set Alert" (secondary action)
- Button: "Dismiss" (close modal)

**Backend Flow**:
- GET /api/v1/data/catalyst/{event_id}
- Response includes full event details, related news articles, historical price impact data

**Requirements**: REQ-CL-003

---

#### Step 4: Initiate Lab Session
**Action**: User clicks "Analyze in Lab" button

**UI State**:
- Lab Session Creation Modal opens
- Pre-filled context: "Catalyst Event: SEC ETF Approval"
- Natural language input field: "What should I analyze?"
- Model selection dropdown:
  - "System Default (GPT-4o - Free)" [selected]
  - "My OpenAI Model (GPT-4)" [if configured]
  - "My Google Model (Gemini 1.5 Pro)" [if configured]
  - "My Anthropic Model (Claude 3.5 Sonnet)" [if configured]
- Button: "Start Analysis"

**Backend Flow**:
- GET /api/v1/users/me/llm-credentials (check if user has BYOM configured)
- Frontend pre-fills model options based on available credentials

**Requirements**: REQ-AG-001, REQ-BYOM-7.1

---

#### Step 5: User Defines Analysis Goal
**Action**: User enters natural language goal: "What's the correlation between SEC ETF filings and BTC price movements in the past 5 years?"

**UI State**:
- User types in multi-line text area
- Character count: "245 / 2000"
- Suggestion chips appear: "Include historical data", "Compare to previous ETF announcements"
- User selects model: "System Default (GPT-4o - Free)"
- Button "Start Analysis" becomes enabled

**Requirements**: REQ-AG-001

---

#### Step 6: Agent Session Begins
**Action**: User clicks "Start Analysis"

**UI State**:
- Modal closes
- User navigated to: `/lab/session/{session_id}`
- Split-view layout:
  - Left 60%: Data context (Catalyst event details, related news)
  - Right 40%: Agent Terminal (streaming logs)
- Terminal shows: "Initializing agent orchestrator..."
- Loading spinner in terminal header

**Backend Flow**:
- POST /api/v1/agent/sessions
  ```json
  {
    "context": "Catalyst event: SEC ETF Approval",
    "goal": "What's the correlation between SEC ETF filings and BTC price...",
    "model_config": {
      "provider": "system_default",
      "model": "gpt-4o"
    }
  }
  ```
- WebSocket connection established: /ws/agent/session/{session_id}
- Agent orchestrator begins planning phase

**Requirements**: REQ-AG-001, REQ-AG-002

---

#### Step 7: Agent Execution & Real-Time Feedback
**Action**: Agent orchestrator executes analysis

**UI State (Terminal Messages)**:
```
🧠 Agent Thought: I need to gather historical data on BTC prices and SEC ETF filing dates...
🔧 Tool Invocation: query_glass_ledger(protocol="Bitcoin", days=1825)
✅ Tool Result: Retrieved 1825 daily price records
🔧 Tool Invocation: query_catalyst_events(type="regulation", keyword="ETF", days=1825)
✅ Tool Result: Found 12 SEC ETF filing events
🧠 Agent Thought: Now I'll calculate correlation coefficients...
🔧 Tool Invocation: run_statistical_analysis(data=...)
✅ Tool Result: Pearson correlation: 0.68 (strong positive correlation)
📊 Final Output:
---
Based on 5 years of data, there is a strong positive correlation (r=0.68) between SEC ETF filing announcements and BTC price movements. Key findings:
- Price typically increases 8-12% within 7 days of positive ETF news
- Negative filings (rejections) correlate with 5-8% drops
- Correlation strongest when filing comes from major institutions (BlackRock, Fidelity)
---
```

**Backend Flow**:
- Agent orchestrator sends WebSocket messages for each step
- Tools invoked: GlassLedgerTool, CatalystTool, StatisticalAnalysisTool
- Each tool execution logged to audit table

**Requirements**: REQ-AG-002, REQ-AG-003, REQ-AG-004, NFR-AG-001 (agent planning < 2s)

---

#### Step 8: Review Results & Next Actions
**Action**: User reads agent output and decides on next steps

**UI State**:
- Terminal shows final output with formatted markdown
- Buttons appear:
  - "Export Transcript" (download as .txt)
  - "Promote to Floor" (if user has trading enabled)
  - "Start New Session" (return to Lab home)
  - "Share Results" (future feature)
- User can scroll through full transcript, search via Ctrl+F

**Backend Flow**:
- Session marked as "completed" in database
- Final output stored in agent_sessions table

**Requirements**: REQ-AG-009

---

### UI Touchpoints Summary
| Component | File Path | Requirement |
|-----------|-----------|-------------|
| 4 Ledgers Dashboard | `frontend/src/routes/_layout/ledgers.tsx` | REQ-GL-001, REQ-CL-001 |
| Catalyst Event Modal | `frontend/src/components/Ledgers/CatalystDetailModal.tsx` | REQ-CL-003 |
| Lab Session Creation | `frontend/src/components/Lab/SessionCreationModal.tsx` | REQ-AG-001 |
| Agent Terminal | `frontend/src/components/Lab/AgentTerminal.tsx` | REQ-AG-002 |

### E2E Test Reference
**Test File**: `frontend/tests/e2e/discovery_flow.spec.ts`

**Test Coverage**:
1. User logs in and sees 4 Ledgers dashboard
2. Catalyst alert appears (mocked WebSocket)
3. User clicks alert → modal opens
4. User clicks "Analyze in Lab" → session creation modal
5. User enters goal → agent terminal appears
6. Agent messages stream in (mocked WebSocket)
7. Final output displayed with export button

---

## Journey 2: BYOM Setup Journey

**Persona**: Alex, Data Scientist  
**Goal**: Configure personal OpenAI API key to use GPT-4 for cost control  
**Entry Point**: User Settings  
**Success Metric**: API key validated and used in successful agent session

### Journey Steps

#### Step 1: Navigate to Settings
**Action**: User clicks profile dropdown → "Settings" → "AI Models" tab

**UI State**:
- Settings page with tabs: "Profile", "AI Models", "Security", "Billing"
- "AI Models" tab selected
- Card: "Bring Your Own Model (BYOM)"
- Description: "Use your own LLM provider to control costs and choose preferred models"
- Current status: "Using System Default (Free)"
- Button: "Configure Your API Keys"

**Requirements**: REQ-BYOM-6.1

---

#### Step 2: Select Provider
**Action**: User clicks "Configure Your API Keys"

**UI State**:
- Provider selection cards:
  - OpenAI (GPT-4, GPT-4 Turbo, GPT-3.5 Turbo)
  - Google (Gemini 1.5 Pro, Gemini Pro)
  - Anthropic (Claude 3.5 Sonnet, Claude 3 Opus)
- Each card shows: logo, supported models, setup link
- User clicks "OpenAI" card

**Requirements**: REQ-BYOM-001

---

#### Step 3: Enter API Key
**Action**: User enters OpenAI API key

**UI State**:
- Form appears:
  - Label: "OpenAI API Key"
  - Input field (type=password initially)
  - Toggle: "Show key" (reveals plaintext temporarily)
  - Model dropdown: "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"
  - Button: "Test Connection" (secondary)
  - Button: "Save" (primary, disabled until test passes)
- Help text: "Get your API key from platform.openai.com/api-keys"
- Security note: "Your key is encrypted and never shared"

**Backend Flow**: None yet (client-side only)

**Requirements**: REQ-BYOM-6.2, REQ-BYOM-6.4

---

#### Step 4: Test Connection
**Action**: User clicks "Test Connection"

**UI State**:
- Button shows spinner: "Testing..."
- Backend makes test API call with provided key

**Backend Flow**:
- POST /api/v1/users/me/llm-credentials/test
  ```json
  {
    "provider": "openai",
    "api_key": "sk-proj-...",
    "model": "gpt-4"
  }
  ```
- Backend attempts to instantiate LangChain OpenAI client
- Makes minimal test call (e.g., "Say hello")
- Returns success or error

**Success Case**:
- Green checkmark appears: "✅ Connection successful! GPT-4 is ready."
- "Save" button becomes enabled

**Failure Cases**:
- ❌ "Invalid API key format. Keys should start with 'sk-proj-' or 'sk-'."
- ❌ "Could not authenticate with OpenAI. Please check your key."
- ❌ "Rate limit exceeded. Please try again in 10 minutes."
- Each error includes link to OpenAI troubleshooting docs

**Requirements**: REQ-BYOM-6.5, REQ-BYOM-6.6

---

#### Step 5: Save Configuration
**Action**: User clicks "Save"

**UI State**:
- Button shows spinner: "Saving..."
- Success toast: "OpenAI API key saved successfully"
- Form closes
- Settings page now shows:
  - Active Provider: "OpenAI (GPT-4)"
  - Masked key: "sk-proj-***...xyz"
  - Buttons: "Edit", "Delete", "Test Connection"

**Backend Flow**:
- POST /api/v1/users/me/llm-credentials
  ```json
  {
    "provider": "openai",
    "model_name": "gpt-4",
    "api_key": "sk-proj-...",
    "is_default": true
  }
  ```
- Backend encrypts API key using AES-256
- Stores encrypted key in user_llm_credentials table
- Audit log created: "User {user_id} added OpenAI API key"

**Requirements**: REQ-BYOM-8.1, REQ-BYOM-8.6

---

#### Step 6: Use Custom Model in Session
**Action**: User starts new agent session and selects custom model

**UI State**:
- Lab session creation modal
- Model dropdown now shows:
  - "System Default (GPT-4o - Free)"
  - "My OpenAI Model (GPT-4)" ✨ NEW
- User selects "My OpenAI Model (GPT-4)"
- Estimated cost note: "Your API key will be used. Estimated cost: $0.03/request"

**Backend Flow**:
- Session creation includes model_config with user's credentials
- Agent orchestrator retrieves encrypted key
- Decrypts key and instantiates LangChain OpenAI client
- All agent operations use user's API key

**Requirements**: REQ-BYOM-7.1, REQ-BYOM-3.1, REQ-BYOM-3.2

---

### UI Touchpoints Summary
| Component | File Path | Requirement |
|-----------|-----------|-------------|
| Settings Page | `frontend/src/routes/_layout/settings.tsx` | REQ-BYOM-6.1 |
| LLM Settings Card | `frontend/src/components/UserSettings/LLMSettings.tsx` | REQ-BYOM-6.2 |
| Provider Selector | `frontend/src/components/UserSettings/ProviderSelector.tsx` | REQ-BYOM-001 |
| API Key Input | `frontend/src/components/UserSettings/APIKeyInput.tsx` | REQ-BYOM-6.3 |

### E2E Test Reference
**Test File**: `frontend/tests/e2e/byom_setup.spec.ts`

**Test Coverage**:
1. User navigates to Settings → AI Models
2. User clicks "Configure Your API Keys"
3. User selects OpenAI provider
4. User enters API key (test key from environment)
5. User clicks "Test Connection" → success
6. User clicks "Save" → key saved
7. User starts new session → custom model appears in dropdown
8. User selects custom model → session uses custom key

---

## Journey 3: The Lab Analysis Journey (Ad-Hoc Exploration)

**Persona**: Chris, Quantitative Researcher  
**Goal**: Explore cryptocurrency market data with AI assistance without predefined catalysts  
**Entry Point**: The Lab Home  
**Success Metric**: Completed exploratory analysis with data visualizations

### Journey Steps

#### Step 1: Start Blank Session
**Action**: User navigates to `/lab` and clicks "New Analysis Session"

**UI State**:
- Lab home page with:
  - Recent sessions list (if any)
  - Quick actions: "New Session", "Load Template", "View History"
- User clicks "New Session"
- Session creation modal appears (no pre-filled context)

**Backend Flow**: GET /api/v1/agent/sessions (retrieve recent sessions)

**Requirements**: REQ-AG-001

---

#### Step 2: Define Open-Ended Goal
**Action**: User enters exploratory goal

**UI State**:
- Session creation form:
  - Goal field: "Find hidden correlations between altcoin trading volumes and social media sentiment across 100+ coins"
  - Data sources checkboxes:
    - ✅ Glass Ledger (DeFi TVL)
    - ✅ Human Ledger (Social sentiment)
    - ❌ Catalyst Ledger (Events)
    - ✅ Exchange Ledger (Prices/volumes)
  - Time range: "Last 90 days"
  - Model: "System Default (GPT-4o)"
- Button: "Start Analysis"

**Requirements**: REQ-AG-001

---

#### Step 3: Agent Orchestration & Tool Selection
**Action**: Agent orchestrator plans analysis approach

**UI State (Agent Terminal)**:
```
🧠 Agent Thought: This requires multi-source data correlation. I'll break this into sub-tasks:
   1. Query trading volumes from Exchange Ledger for top 100 altcoins
   2. Retrieve social sentiment scores from Human Ledger for same period
   3. Perform correlation analysis and identify outliers
   4. Visualize findings

🔧 Tool Invocation: query_exchange_ledger(coins=top_100_by_volume, days=90)
⏳ Processing... (estimated 15s for large dataset)
```

**Backend Flow**:
- Agent orchestrator creates task plan
- Selects appropriate tools: ExchangeLedgerTool, HumanLedgerTool, StatisticalAnalysisTool, VisualizationTool
- Executes tasks sequentially with progress updates

**Requirements**: REQ-AG-002, REQ-AG-003

---

#### Step 4: Interactive Mid-Session Input
**Action**: Agent requests clarification from user

**UI State**:
```
✅ Tool Result: Retrieved 9000 volume records (100 coins × 90 days)
🧠 Agent Thought: I found 3 interesting correlations, but I need to decide how to filter the data.

❓ User Input Required:
Should I focus on:
A) Coins with consistent correlation (r > 0.7 for entire period)
B) Coins with sudden correlation shifts (breaking point analysis)
C) All correlations ranked by strength

[Input field for user response]
```

**Action**: User types "B" and presses Enter

**UI State**:
- User's response appears in terminal: `> User: B`
- Agent continues: "🧠 Agent Thought: Performing breaking point analysis..."

**Requirements**: REQ-AG-008 (human-in-the-loop)

---

#### Step 5: Data Visualization Generation
**Action**: Agent generates interactive charts

**UI State**:
- Left pane (60%) now shows:
  - Chart 1: Scatter plot of correlation strength vs. time
  - Chart 2: Heatmap of top 20 coins with highest correlation shifts
  - Chart 3: Timeline of sentiment spikes matched with volume changes
- Charts are interactive (zoom, pan, tooltip on hover)
- Button: "Export Data" (download as CSV)

**Backend Flow**:
- Agent uses VisualizationTool to generate Plotly/D3 JSON
- Frontend renders charts using recharts library
- Raw data stored in session results

**Requirements**: REQ-AG-007 (data export)

---

#### Step 6: Save Analysis for Later
**Action**: User saves session and exits

**UI State**:
- Button: "Save & Exit" in terminal header
- Modal: "Name this analysis session"
- User enters: "Altcoin Sentiment Correlation - Q1 2026"
- Button: "Save"
- User redirected to `/lab` home
- Saved session appears in "Recent Sessions" with timestamp

**Backend Flow**:
- PATCH /api/v1/agent/sessions/{session_id}
  ```json
  {
    "name": "Altcoin Sentiment Correlation - Q1 2026",
    "status": "saved"
  }
  ```

**Requirements**: REQ-AG-009

---

### UI Touchpoints Summary
| Component | File Path | Requirement |
|-----------|-----------|-------------|
| Lab Home | `frontend/src/routes/_layout/lab.tsx` | REQ-AG-001 |
| Session Creation Form | `frontend/src/components/Lab/SessionCreationModal.tsx` | REQ-AG-001 |
| Agent Terminal | `frontend/src/components/Lab/AgentTerminal.tsx` | REQ-AG-002 |
| Data Visualization Panel | `frontend/src/components/Lab/VisualizationPanel.tsx` | REQ-AG-007 |

### E2E Test Reference
**Test File**: `frontend/tests/e2e/lab_analysis.spec.ts`

**Test Coverage**:
1. User navigates to Lab home
2. User clicks "New Session"
3. User enters open-ended goal
4. Agent terminal streams messages (mocked)
5. Agent requests user input (mocked)
6. User responds to agent question
7. Visualizations appear in left pane
8. User saves session with custom name
9. User sees saved session in recent list

---

## Journey 4: Lab-to-Floor Promotion Journey

**Persona**: Jamie, Algorithmic Trader  
**Goal**: Promote a validated trading strategy from The Lab to The Floor for live execution  
**Entry Point**: Completed Lab session  
**Success Metric**: Algorithm deployed and first trade executed

### Journey Steps

#### Step 1: Complete Lab Backtesting
**Action**: User completes a Lab session with backtesting results

**UI State (Agent Terminal)**:
```
📊 Final Output:
---
Backtest Results for "BTC Mean Reversion Strategy"
- Period: 2023-01-01 to 2026-01-24 (3 years)
- Total Return: +42.3%
- Sharpe Ratio: 1.87
- Max Drawdown: -12.4%
- Win Rate: 67%
- Total Trades: 234

Risk Assessment: ✅ APPROVED
- Drawdown within acceptable limits
- Consistent performance across market cycles
- No overfitting detected (validated on out-of-sample data)
---

✅ Strategy Ready for Live Trading
```

**Backend Flow**:
- Agent backtesting tool runs simulation
- Results stored in agent_session_results table
- Risk assessment performed automatically

**Requirements**: REQ-AG-006 (sandboxed model training), REQ-FL-001

---

#### Step 2: Initiate Promotion
**Action**: User clicks "Promote to Floor" button

**UI State**:
- Modal: "Deploy to The Floor"
- Pre-filled strategy name: "BTC Mean Reversion Strategy"
- Configuration form:
  - **Position Sizing**:
    - Max position size: [__] AUD (default: 1000)
    - Max open positions: [__] (default: 3)
  - **Risk Management**:
    - Daily loss limit: [__] AUD (default: 500, 50% of max position)
    - Stop loss per trade: [__] % (default: 5%)
    - Take profit per trade: [__] % (default: 10%)
  - **Execution Settings**:
    - Trading hours: "24/7" or "Custom schedule" [dropdown]
    - Cooldown between trades: [__] minutes (default: 15)
- Warning banner: "⚠️ This will place real trades using your CoinSpot account"
- Checkbox: "I understand this strategy will use real funds"
- Button: "Deploy" (disabled until checkbox checked)

**Requirements**: REQ-FL-001, REQ-FL-005

---

#### Step 3: Confirm Trading Permissions
**Action**: User checks checkbox and clicks "Deploy"

**UI State**:
- Confirmation modal: "🔐 Trading API Key Required"
- Message: "To deploy algorithms, you must configure a CoinSpot Trading API Key with restricted permissions (no withdrawal access)"
- If key not configured:
  - Button: "Go to Settings" (redirects to Security → API Keys)
- If key configured:
  - Display: "Using API Key: ***...xyz"
  - Button: "Confirm Deployment"

**Backend Flow**:
- GET /api/v1/users/me/trading-credentials
- If no credentials: return 404, show setup prompt
- If credentials exist: validate key has required permissions

**Requirements**: REQ-FL-001, NFR-FL-S-001 (trading API key with restricted permissions)

---

#### Step 4: Algorithm Deployment
**Action**: Backend deploys algorithm to execution worker

**UI State**:
- Loading spinner: "Deploying algorithm..."
- Progress steps:
  - ✅ Validating strategy parameters
  - ✅ Creating execution worker
  - ✅ Subscribing to Exchange Ledger (real-time prices)
  - ✅ Initializing risk management system
  - ✅ Algorithm live!
- Success modal: "🚀 Algorithm Deployed"
- Message: "BTC Mean Reversion Strategy is now live. You will be redirected to The Floor to monitor execution."
- Button: "Go to Floor Dashboard"

**Backend Flow**:
- POST /api/v1/floor/deploy
  ```json
  {
    "session_id": "abc-123",
    "strategy_name": "BTC Mean Reversion Strategy",
    "config": {
      "max_position_size_aud": 1000,
      "max_open_positions": 3,
      "daily_loss_limit_aud": 500,
      "stop_loss_pct": 5,
      "take_profit_pct": 10
    }
  }
  ```
- Backend creates deployed_algorithms record
- Instantiates execution worker (background celery task)
- Worker subscribes to real-time price data via WebSocket

**Requirements**: REQ-FL-001, REQ-FL-002, DM-FL-001

---

#### Step 5: Monitor on The Floor
**Action**: User navigated to `/floor` dashboard

**UI State**:
- Top bar: P&L Ticker
  - Realized P&L: $0.00 | Unrealized P&L: $0.00 | Total: $0.00 | Drawdown: 0.0%
- Main grid (3 columns):
  - **Column 1: Algorithm Status**
    - Card: "BTC Mean Reversion Strategy"
    - Status: 🟢 ACTIVE
    - Uptime: 00:02:34
    - Signals generated: 0
    - Trades executed: 0
  - **Column 2: Active Positions**
    - Empty state: "No open positions yet"
  - **Column 3: Risk Metrics**
    - Daily loss limit: $0 / $500 (0%)
    - Max position usage: $0 / $1000 (0%)
    - Win rate: N/A (no trades yet)
- Bottom bar: Kill Switch (disabled, grayed out since no positions)

**Requirements**: REQ-FL-004, REQ-FL-008

---

#### Step 6: First Trade Execution
**Action**: Algorithm generates first buy signal

**UI State**:
- Algorithm Status card updates:
  - Signals generated: 1
  - Last signal: "BUY BTC at $94,500" (2 seconds ago)
  - Status: 🟡 EXECUTING TRADE...
- Toast notification: "🔔 New trade: Buying BTC at market price"
- Active Positions column shows pending order:
  - BTC | PENDING BUY | 0.0106 BTC | ~$1,000 AUD

**Backend Flow**:
- Algorithm generates signal: `{"action": "buy", "coin": "BTC", "size_aud": 1000}`
- Execution worker calls CoinSpot API:
  - POST /my/buy/now
    ```json
    {
      "cointype": "BTC",
      "amount": 1000,
      "amounttype": "aud"
    }
    ```
- Response: `{"order_id": "xyz-789", "status": "PENDING"}`
- Worker polls /my/orders every 2 seconds until status = "COMPLETE"

**Requirements**: REQ-FL-002, REQ-FL-003, NFR-FL-P-001 (signal-to-execution < 500ms)

---

#### Step 7: Trade Completion & P&L Update
**Action**: Order fills on CoinSpot

**UI State**:
- Active Positions updates:
  - BTC | OPEN | 0.0106 BTC | Entry: $94,500 | Current: $94,623 | P&L: +$1.30 (+0.13%)
- Algorithm Status:
  - Trades executed: 1
  - Last trade: "BOUGHT 0.0106 BTC at $94,500" (30s ago)
- P&L Ticker updates (green background):
  - Unrealized P&L: +$1.30 | Total: +$1.30 | Drawdown: 0.0%
- Kill Switch becomes active (solid red, enabled)

**Backend Flow**:
- Order status polling completes: "COMPLETE"
- trade_ledger record created:
  ```json
  {
    "algorithm_id": "abc-123",
    "order_id": "xyz-789",
    "action": "buy",
    "coin": "BTC",
    "amount": 0.0106,
    "price": 94500,
    "timestamp": "2026-01-24T16:45:23Z"
  }
  ```
- Real-time P&L calculation: (current_price - entry_price) × amount

**Requirements**: REQ-FL-003, REQ-FL-004, NFR-FL-I-001 (audit log)

---

### UI Touchpoints Summary
| Component | File Path | Requirement |
|-----------|-----------|-------------|
| Promotion Modal | `frontend/src/components/Lab/PromoteToFloorModal.tsx` | REQ-FL-001 |
| Floor Dashboard | `frontend/src/routes/_layout/floor.tsx` | REQ-FL-004 |
| Algorithm Status Card | `frontend/src/components/Floor/AlgorithmStatusCard.tsx` | REQ-FL-001 |
| Active Positions Table | `frontend/src/components/Floor/ActivePositionsTable.tsx` | REQ-FL-004 |
| P&L Ticker | `frontend/src/components/Floor/PLTicker.tsx` | REQ-FL-004 |
| Kill Switch | `frontend/src/components/Floor/KillSwitch.tsx` | REQ-FL-008 |

### E2E Test Reference
**Test File**: `frontend/tests/e2e/lab_to_floor_promotion.spec.ts`

**Test Coverage**:
1. Complete Lab session with approved backtest
2. Click "Promote to Floor"
3. Configure position sizing and risk limits
4. Confirm deployment (mocked trading API key check)
5. Algorithm deployed successfully
6. Navigate to Floor dashboard
7. Algorithm status shows ACTIVE
8. First trade signal generated (mocked)
9. Trade execution completes (mocked CoinSpot API)
10. P&L updates in real-time

---

## Journey 5: The Floor Monitoring & Risk Management Journey

**Persona**: Jordan, Risk Manager  
**Goal**: Monitor live trading algorithm and trigger emergency stop if necessary  
**Entry Point**: The Floor Dashboard with active algorithm  
**Success Metric**: Successfully halted algorithm during adverse conditions

### Journey Steps

#### Step 1: Daily Monitoring Routine
**Action**: User logs in and checks Floor dashboard

**UI State**:
- P&L Ticker (current state):
  - Realized P&L: +$124.50 | Unrealized P&L: -$32.10 | Total: +$92.40 | Drawdown: 2.1% ⚠️
- Algorithm Status:
  - BTC Mean Reversion Strategy: 🟢 ACTIVE (uptime: 2d 14h)
  - Signals: 18 | Trades: 18 | Win rate: 61%
- Active Positions:
  - BTC | 0.0106 BTC | Entry: $94,500 | Current: $94,123 | P&L: -$32.10 (-3.2%)
  - ETH | 0.45 ETH | Entry: $3,210 | Current: $3,287 | P&L: +$34.65 (+2.4%)

**Requirements**: REQ-FL-004

---

#### Step 2: Drawdown Warning Triggered
**Action**: Market moves against positions, drawdown increases

**UI State**:
- P&L Ticker background turns amber:
  - Drawdown: 5.8% ⚠️ (threshold: 5% warning)
- Toast notification: "⚠️ WARNING: Daily drawdown at 5.8%"
- Algorithm Status shows warning icon
- Risk Metrics column highlights:
  - Daily loss limit: $290 / $500 (58%) - Amber
  - Max position usage: $1,800 / $3,000 (60%)

**Backend Flow**:
- Real-time P&L calculator detects drawdown > 5%
- WebSocket message sent to frontend
- Audit log: "Drawdown warning triggered at 5.8%"

**Requirements**: REQ-FL-006 (emergency stop trigger)

---

#### Step 3: Critical Drawdown Auto-Trigger
**Action**: Drawdown exceeds 10% threshold

**UI State**:
- P&L Ticker background turns red:
  - Drawdown: 10.2% 🚨 (CRITICAL)
- Full-screen modal appears: "🚨 EMERGENCY STOP TRIGGERED"
- Message: "Daily drawdown limit exceeded (10.2% > 10.0%)"
- Automatic actions taken:
  - ✅ All algorithms paused
  - ✅ All open orders cancelled
  - ⏳ Liquidating positions to AUD...
- Loading spinner
- Button: "Acknowledge" (disabled until liquidation complete)

**Backend Flow**:
- Drawdown calculator detects > 10%
- Emergency stop triggered automatically:
  - POST /api/v1/floor/emergency-stop (internal call)
  - All deployed_algorithms set to status="stopped"
  - Execution workers receive SIGTERM
  - All open orders cancelled via CoinSpot API
  - Market sell orders placed for all positions

**Requirements**: REQ-FL-006, REQ-FL-007

---

#### Step 4: Position Liquidation Complete
**Action**: All positions closed

**UI State**:
- Modal updates:
  - ✅ All positions liquidated to AUD
  - Final P&L: -$102.34 (-10.2%)
  - Closed positions:
    - BTC: Sold 0.0106 BTC at $93,210 | Loss: -$136.74
    - ETH: Sold 0.45 ETH at $3,287 | Gain: +$34.40
- Button: "Acknowledge" (now enabled)
- User clicks "Acknowledge"
- Redirected to Floor dashboard (now empty)

**Backend Flow**:
- All sell orders complete
- trade_ledger updated with sell transactions
- Final realized P&L calculated and stored
- deployed_algorithms.status = "stopped_emergency"

**Requirements**: REQ-FL-007, NFR-FL-I-001

---

#### Step 5: Manual Kill Switch Test (Alternative Path)
**Action**: User manually triggers Kill Switch before auto-stop

**UI State (before trigger)**:
- Drawdown at 7.2% (below 10% threshold, but user wants to stop)
- User clicks Kill Switch button (bottom-right, red octagon)
- Confirmation modal appears:
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
- User types "STOP" (case-insensitive)
- "CONFIRM STOP" button becomes enabled
- User clicks "CONFIRM STOP"

**Backend Flow**:
- POST /api/v1/floor/emergency-stop (user-initiated)
- Same liquidation process as auto-trigger
- Audit log: "User {user_id} triggered manual emergency stop"

**Requirements**: REQ-FL-008

---

#### Step 6: Disconnected State Handling (Edge Case)
**Action**: WebSocket connection drops during trading

**UI State**:
- Red banner appears at top: "🔴 DISCONNECTED - Last updated 8 seconds ago"
- P&L Ticker shows stale data with timestamp
- Kill Switch label changes: "EMERGENCY STOP (Fallback Mode)"
- All real-time data stops updating
- Reconnection attempts shown: "Reconnecting... (attempt 4/∞)"

**Action**: User clicks Kill Switch during disconnection

**UI State**:
- Modal appears: "🔴 WEBSOCKET DISCONNECTED"
- Message: "Using REST API fallback for emergency stop"
- User types "STOP" to confirm
- Backend uses REST endpoint instead of WebSocket

**Backend Flow**:
- POST /api/v1/floor/emergency-stop (REST fallback)
- If REST also fails:
  - Modal shows: "❌ MANUAL INTERVENTION REQUIRED"
  - Display: "Call support: +61-XXX-XXX-XXX"
  - Display: "Or manually close positions on CoinSpot website"

**Requirements**: REQ-FL-DISC-001 (disconnected state handling)

---

#### Step 7: Post-Stop Review
**Action**: User reviews what happened

**UI State**:
- Floor dashboard (empty state):
  - Message: "No active algorithms"
  - Historical P&L summary:
    - Total realized P&L (all time): +$22.06
    - Today's P&L: -$102.34
    - Reason for stop: "Emergency stop - Drawdown limit exceeded"
  - Button: "View Full Trading History"
- User clicks "View Full Trading History"
- Redirected to `/floor/history`
- Trade log table:
  | Time | Algorithm | Action | Coin | Amount | Price | P&L | Status |
  |------|-----------|--------|------|--------|-------|-----|--------|
  | 16:45:23 | BTC Mean Rev | BUY | BTC | 0.0106 | $94,500 | - | FILLED |
  | 18:32:11 | BTC Mean Rev | SELL | BTC | 0.0106 | $93,210 | -$136.74 | FILLED |

**Requirements**: NFR-FL-I-001 (audit log)

---

### UI Touchpoints Summary
| Component | File Path | Requirement |
|-----------|-----------|-------------|
| Floor Dashboard | `frontend/src/routes/_layout/floor.tsx` | REQ-FL-004 |
| P&L Ticker | `frontend/src/components/Floor/PLTicker.tsx` | REQ-FL-004 |
| Kill Switch | `frontend/src/components/Floor/KillSwitch.tsx` | REQ-FL-008 |
| Emergency Stop Modal | `frontend/src/components/Floor/EmergencyStopModal.tsx` | REQ-FL-007 |
| Trading History | `frontend/src/routes/_layout/floor/history.tsx` | NFR-FL-I-001 |

### E2E Test Reference
**Test File**: `frontend/tests/e2e/floor_risk_management.spec.ts`

**Test Coverage**:
1. User logs in with active algorithm running
2. P&L updates in real-time (mocked WebSocket)
3. Drawdown increases to 5% → warning shown
4. Drawdown increases to 10% → emergency stop triggered automatically
5. Liquidation process completes
6. User acknowledges emergency stop
7. Alternative path: Manual kill switch test
8. User types "STOP" → confirms
9. Disconnected state test: WebSocket drops
10. Kill switch uses REST fallback
11. User views trading history

---

## Cross-Journey Integration Points

### Integration 1: 4 Ledgers → The Lab → The Floor
**Flow**: Discovery (Catalyst alert) → Analysis (Lab session) → Deployment (Floor algorithm)
- Data carried forward: Catalyst event context, analysis results, recommended strategy
- Requirement: Cross-module context preservation

### Integration 2: BYOM → All Agent Sessions
**Flow**: Configure API key in Settings → Use in Lab → Use in Floor algorithm agents
- Data carried forward: User's LLM credentials
- Requirement: Model selection available everywhere agents are used

### Integration 3: The Lab → Trading History Review
**Flow**: Backtest in Lab → Deploy to Floor → Review results → Adjust strategy in Lab
- Data carried forward: Historical trade data, P&L metrics
- Requirement: Feedback loop for strategy optimization

---

## E2E Test Suite Summary

| Test File | Journey | Status | Priority |
|-----------|---------|--------|----------|
| `discovery_flow.spec.ts` | Journey 1 | Not Started | HIGH |
| `byom_setup.spec.ts` | Journey 2 | Not Started | HIGH |
| `lab_analysis.spec.ts` | Journey 3 | Not Started | MEDIUM |
| `lab_to_floor_promotion.spec.ts` | Journey 4 | Not Started | HIGH |
| `floor_risk_management.spec.ts` | Journey 5 | Not Started | CRITICAL |

**Test Infrastructure**:
- Framework: Playwright
- Coverage target: 100% of happy paths, 80% of error cases
- Run frequency: On every PR to main
- Mocking strategy: WebSocket messages, CoinSpot API responses, LLM responses

---

## Document Maintenance

**Update Triggers**:
- New module added (update all relevant journeys)
- UI component redesign (update UI touchpoints)
- Backend API change (update backend flows)
- New requirement added (link to journey steps)

**Review Schedule**:
- Monthly: Product Manager reviews for UX accuracy
- Per Sprint: Update based on implementation changes
- Quarterly: Full journey re-validation with stakeholders

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-24  
**Next Review**: 2026-02-24  
**Maintained By**: Product Team
