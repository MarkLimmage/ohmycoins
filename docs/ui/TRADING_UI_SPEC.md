# Trading UI Specification - The Floor

**Version**: 1.0  
**Date**: 2026-01-24  
**Status**: ACTIVE  
**Purpose**: Define UI specifications for live trading controls (The Floor) with safety mechanisms

---

## Overview

The Floor is where validated Lab strategies go live. It's safety-critical: every UI element must prevent catastrophic losses while providing real-time monitoring.

**Core Principle**: Fail-safe by default. All actions require explicit confirmation.

**Disconnected State Requirement**: REQ-FL-DISC-001 (handle WebSocket disconnection gracefully)

---

## Page Layout - Command Center

### Desktop Layout (≥1280px)

```
┌──────────────────────────────────────────────────────────────┐
│ [🏠 Home] [📊 Ledgers] [🧪 Lab] [🏢 The Floor] [👤 Profile] │ ← Global Nav
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ P&L TICKER: +$1,234.56 (+2.3%) | Active: 3 | Paused: 1  │ │ ← Live P&L
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌────────────┬────────────┬────────────┬──────────────────┐ │
│ │ Algorithm  │  P&L       │ Status     │ Controls         │ │
│ ├────────────┼────────────┼────────────┼──────────────────┤ │
│ │ BTC Arb v2 │ +$542.30   │ ✅ ACTIVE  │ [⏸ Pause] [🛑]  │ │
│ │            │ +1.8%      │ 12m uptime │                  │ │
│ ├────────────┼────────────┼────────────┼──────────────────┤ │
│ │ ETH Grid   │ +$320.50   │ ✅ ACTIVE  │ [⏸ Pause] [🛑]  │ │
│ │            │ +0.9%      │ 45m uptime │                  │ │
│ ├────────────┼────────────┼────────────┼──────────────────┤ │
│ │ SOL MeanRev│ +$371.76   │ ⏸ PAUSED   │ [▶ Resume] [🛑] │ │
│ │            │ +1.2%      │ 8m pause   │                  │ │
│ └────────────┴────────────┴────────────┴──────────────────┘ │
│                                                              │
│                                    ┌──────────────────────┐  │
│                                    │  🆘 KILL SWITCH      │  │
│                                    │  [EMERGENCY STOP]    │  │
│                                    │  120px × 120px       │  │
│                                    └──────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Key Zones**:
1. **P&L Ticker** (top): Live portfolio metrics, always visible
2. **Algorithm Grid** (center): 3-column layout, scrollable
3. **Kill Switch** (bottom-right): Fixed position, always accessible

---

### Tablet Layout (768-1279px)

Same structure, slightly narrower. Algorithm grid reduces to 2 columns (P&L and Controls combined).

---

### Mobile Layout (< 768px)

**Phase 1 (MVP)**: Desktop-only  
**Phase 2**: Read-only mobile view
```
┌────────────────────────────┐
│ P&L: +$1,234.56 (+2.3%)    │
├────────────────────────────┤
│ ⚠️ Trading controls only   │
│ available on desktop       │
│                            │
│ [View Activity Log]        │
└────────────────────────────┘
```

---

## 1. P&L Ticker

**Purpose**: Real-time portfolio performance summary

### Visual Design

**Bar Height**: 60px  
**Background**: Linear gradient (#10b981 → #059669) if positive P&L, (#ef4444 → #dc2626) if negative  
**Text Color**: White, bold, 18px

**Layout**:
```
┌──────────────────────────────────────────────────────────┐
│ P&L: +$1,234.56 (+2.3%) | Active: 3 | Paused: 1 | 🔴 LIVE│
└──────────────────────────────────────────────────────────┘
```

**Segments**:
1. **Total P&L**: Dollar amount + percentage change (since session start)
2. **Active Algorithms**: Count of currently running strategies
3. **Paused Algorithms**: Count of temporarily halted strategies
4. **Connection Status**: 🔴 LIVE (green) or ⚪ DISCONNECTED (red) - see REQ-FL-DISC-001

### Data Update Frequency

**WebSocket**: Real-time updates (every trade)  
**Fallback**: REST API poll every 2 seconds if WebSocket disconnected

### Animation

**Number Changes**: 
- Increase: Flash green (200ms pulse)
- Decrease: Flash red (200ms pulse)
- Animation: `animate-pulse` utility class (Tailwind)

**Code Example**:
```typescript
interface PLTickerData {
  total_pnl: number;  // In AUD
  pnl_percentage: number;  // Decimal (0.023 = 2.3%)
  active_count: number;
  paused_count: number;
  is_connected: boolean;  // WebSocket connection status
  last_update: string;  // ISO 8601 timestamp
}

// WebSocket: wss://api.ohmycoins.com/ws/floor/pnl?token={jwt}
// REST Fallback: GET /api/v1/trading/floor/summary
```

**Accessibility**:
- ARIA live region: `aria-live="polite"` (announce P&L changes to screen readers)
- Text: "Portfolio profit and loss: plus $1,234.56, up 2.3%"

---

## 2. Algorithm Control Cards

**Purpose**: Individual algorithm monitoring and control

### Card Layout

**Size**: Width 100% (fills column), Height auto  
**Border**: 2px solid #d1d5db (gray-300), rounded-lg  
**Shadow**: shadow-md on hover (subtle elevation)

**Structure**:
```
┌──────────────────────────────────────────┐
│ BTC Arbitrage v2.1                       │ ← Algorithm Name (bold, 16px)
├──────────────────────────────────────────┤
│ P&L: +$542.30 (+1.8%)                   │ ← Current P&L (large, 20px)
│ Uptime: 12m 34s                         │ ← How long running
│ Trades: 23 (15 wins, 8 losses)          │ ← Trade statistics
│ Win Rate: 65.2%                         │
│                                          │
│ Status: ✅ ACTIVE                        │ ← Visual status indicator
│                                          │
│ [⏸️ Pause]  [🛑 Stop]  [⚙️ Settings]    │ ← Action buttons
└──────────────────────────────────────────┘
```

---

### Status Indicators

**Visual States**:

1. **✅ ACTIVE** (Green #10b981)
   - Border: 2px solid green
   - Badge: Solid green circle (10px)
   - Text: "ACTIVE"
   - Behavior: Trades executing in real-time

2. **⏸️ PAUSED** (Amber #f59e0b)
   - Border: 2px solid amber
   - Badge: Amber circle (10px)
   - Text: "PAUSED (8m 12s)" (shows pause duration)
   - Behavior: No new trades, existing positions held

3. **🛑 STOPPED** (Red #ef4444)
   - Border: 2px solid red
   - Badge: Red square (10px)
   - Text: "STOPPED"
   - Behavior: All positions closed, algorithm off

4. **⚠️ ERROR** (Red #ef4444, blinking animation)
   - Border: 2px solid red, pulsing
   - Badge: Red triangle with exclamation (10px)
   - Text: "ERROR - [Error message]"
   - Behavior: Algorithm halted, requires manual intervention
   - Example: "ERROR - Insufficient funds to execute trade"

5. **⚙️ INITIALIZING** (Blue #3b82f6)
   - Border: 2px solid blue
   - Badge: Blue spinner (10px, rotating animation)
   - Text: "INITIALIZING..."
   - Behavior: Algorithm starting, not yet trading

---

### Action Buttons

**Layout**: Horizontal row, equal width, 12px gap

#### Pause Button

**Appearance**:
- Icon: ⏸️ (pause symbol)
- Label: "Pause"
- Color: Amber (#f59e0b)
- Size: 100px × 36px
- Border: 2px solid amber
- Hover: Background amber (#f59e0b / 10% opacity)

**Behavior**:
- Click: Show confirmation modal
  ```
  ┌─────────────────────────────┐
  │ Pause Algorithm?            │
  ├─────────────────────────────┤
  │ BTC Arbitrage v2.1          │
  │                             │
  │ This will:                  │
  │ • Stop opening new trades   │
  │ • Keep existing positions   │
  │ • Resume anytime            │
  │                             │
  │ [Cancel]    [⏸️ Pause]      │
  └─────────────────────────────┘
  ```
- On confirm: 
  - Send POST /api/v1/trading/floor/algorithms/{id}/pause
  - Disable button (show "Pausing..." with spinner)
  - On success: Update status to PAUSED, change button to "Resume"
  - On error: Show toast notification "Failed to pause algorithm: [error]"

**Resume State** (when paused):
- Icon: ▶️ (play symbol)
- Label: "Resume"
- Color: Green (#10b981)
- Same confirmation modal

---

#### Stop Button

**Appearance**:
- Icon: 🛑 (stop sign)
- Label: "Stop"
- Color: Red (#ef4444)
- Size: 100px × 36px
- Border: 2px solid red
- Hover: Background red (#ef4444 / 10% opacity)

**Behavior**:
- Click: Show strict confirmation modal (typed confirmation)
  ```
  ┌───────────────────────────────────┐
  │ ⚠️ STOP ALGORITHM?                │
  ├───────────────────────────────────┤
  │ BTC Arbitrage v2.1                │
  │                                   │
  │ This will:                        │
  │ • Close all open positions        │
  │ • Stop the algorithm permanently  │
  │ • Cannot be undone                │
  │                                   │
  │ Type "STOP" to confirm:           │
  │ [________________]                │
  │                                   │
  │ [Cancel]    [🛑 Stop Algorithm]   │
  │               (disabled until     │
  │                "STOP" typed)      │
  └───────────────────────────────────┘
  ```
- Validation: Button only enabled when input text === "STOP" (case-sensitive)
- On confirm:
  - Send POST /api/v1/trading/floor/algorithms/{id}/stop
  - Show loading spinner in modal: "Closing positions..."
  - On success: Update status to STOPPED, remove card from active list (move to history)
  - On error: Show error message "Failed to stop: [error]. Try Emergency Stop."

**Safety Timeout**:
- If stop takes > 10 seconds, show warning: "Positions taking longer than expected to close. Consider using Kill Switch."

---

#### Settings Button

**Appearance**:
- Icon: ⚙️ (gear)
- Label: "Settings"
- Color: Gray (#6b7280)
- Size: 100px × 36px
- Border: 2px solid gray

**Behavior**:
- Click: Open settings modal (read-only in v1)
  ```
  ┌───────────────────────────────────┐
  │ Algorithm Settings                │
  ├───────────────────────────────────┤
  │ Name: BTC Arbitrage v2.1          │
  │ Strategy: Arbitrage               │
  │ Max Position Size: $500           │
  │ Stop Loss: 2%                     │
  │ Take Profit: 5%                   │
  │                                   │
  │ Risk Limits:                      │
  │ • Max daily loss: $200            │
  │ • Max trades/hour: 10             │
  │                                   │
  │ ℹ️ Settings locked while active   │
  │                                   │
  │ [View Full Config]  [Close]       │
  └───────────────────────────────────┘
  ```
- **v2 Feature**: Allow editing settings for paused algorithms

---

## 3. Kill Switch (Emergency Stop)

**Purpose**: Immediately stop ALL trading and close ALL positions

### Visual Design

**Size**: 120px × 120px octagon  
**Position**: Fixed bottom-right corner, 24px from edges  
**Color**: Red (#dc2626), glowing border (drop-shadow-2xl)  
**Shape**: CSS clip-path octagon

**Icon**: 🛑 (stop sign emoji) or custom SVG  
**Label**: "EMERGENCY STOP" (white text, 12px, bold, uppercase)

**Visual States**:
1. **Ready**: Solid red, subtle pulse animation (1.5s loop)
2. **Hover**: Brightness increase, shadow glow intensifies
3. **Active/Cooldown**: Gray (#6b7280), disabled, countdown timer

**CSS**:
```css
.kill-switch {
  width: 120px;
  height: 120px;
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  clip-path: polygon(30% 0%, 70% 0%, 100% 30%, 100% 70%, 70% 100%, 30% 100%, 0% 70%, 0% 30%);
  box-shadow: 0 0 20px rgba(220, 38, 38, 0.6);
  cursor: pointer;
  animation: pulse 1.5s infinite;
}

.kill-switch:hover {
  filter: brightness(1.2);
  box-shadow: 0 0 30px rgba(220, 38, 38, 0.8);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}
```

---

### Interaction Flow

**Step 1: Click**
- Show full-screen modal (blocks all other interactions)
  ```
  ┌─────────────────────────────────────────┐
  │                                         │
  │        ⚠️ EMERGENCY STOP ⚠️              │
  │                                         │
  │  This will IMMEDIATELY:                 │
  │  • Close ALL open positions             │
  │  • Stop ALL active algorithms           │
  │  • Cancel ALL pending orders            │
  │                                         │
  │  Type "STOP" to confirm:                │
  │  [_________________________]            │
  │                                         │
  │  [Cancel]        [🛑 EMERGENCY STOP]   │
  │                    (disabled)           │
  │                                         │
  └─────────────────────────────────────────┘
  ```

**Step 2: Typed Confirmation**
- User types "STOP" (case-sensitive, exact match)
- Button becomes enabled (red, glowing)

**Step 3: Execution**
- On confirm:
  - Send POST /api/v1/trading/floor/emergency-stop
  - Modal updates:
    ```
    ┌─────────────────────────────────────────┐
    │                                         │
    │        🛑 STOPPING ALL TRADING...       │
    │                                         │
    │  [▓▓▓▓▓▓▓░░░░░░░░] 50%                 │
    │                                         │
    │  Closing positions: 3/5 complete        │
    │  Canceling orders: 12/12 complete       │
    │                                         │
    │  Please wait...                         │
    │                                         │
    └─────────────────────────────────────────┘
    ```
  - Show real-time progress (WebSocket updates from backend)

**Step 4: Completion**
- On success:
  ```
  ┌─────────────────────────────────────────┐
  │                                         │
  │        ✅ ALL TRADING STOPPED            │
  │                                         │
  │  • 5 positions closed                   │
  │  • 3 algorithms stopped                 │
  │  • 12 orders canceled                   │
  │                                         │
  │  Final P&L: +$1,234.56 (+2.3%)         │
  │                                         │
  │  [View Activity Log]  [Close]           │
  │                                         │
  └─────────────────────────────────────────┘
  ```
- On error:
  ```
  ┌─────────────────────────────────────────┐
  │                                         │
  │        ⚠️ EMERGENCY STOP PARTIAL        │
  │                                         │
  │  Some positions failed to close:        │
  │  • BTC/AUD: Order rejected by exchange  │
  │  • ETH/AUD: Insufficient liquidity      │
  │                                         │
  │  [Manual Intervention Required]         │
  │  [Contact Support]  [Retry]             │
  │                                         │
  └─────────────────────────────────────────┘
  ```

---

### Cooldown Period

**Duration**: 5 seconds after successful stop

**Visual**: 
- Kill Switch grayed out
- Countdown timer: "Cooldown: 4s..." (text overlays button)
- Progress ring animation around octagon

**Purpose**: Prevent accidental double-clicks, allow user to process what happened

---

### Audit Logging

**All Kill Switch activations logged**:
```json
{
  "event": "emergency_stop",
  "user_id": "user-123",
  "timestamp": "2026-01-24T16:45:32Z",
  "positions_closed": 5,
  "algorithms_stopped": 3,
  "orders_canceled": 12,
  "final_pnl": 1234.56,
  "errors": []
}
```

**Log Storage**: PostgreSQL `audit_log` table + CloudWatch Logs (AWS)

**Requirements**: REQ-FL-007 (emergency stop)

---

## 4. Disconnected State (REQ-FL-DISC-001)

**Purpose**: Handle WebSocket disconnection gracefully, provide fallback UI

### Disconnection Detection

**Trigger Conditions**:
1. WebSocket connection closed unexpectedly
2. No heartbeat received for 10 seconds
3. Server sends explicit "maintenance" message

**Immediate UI Response**:
- P&L Ticker: Change 🔴 LIVE to ⚪ DISCONNECTED (red badge)
- Show banner notification at top:
  ```
  ┌───────────────────────────────────────────────────────┐
  │ ⚠️ CONNECTION LOST - Attempting to reconnect...       │
  │ Last update: 3 seconds ago | [Retry Now] [Manual Mode]│
  └───────────────────────────────────────────────────────┘
  ```

---

### Fallback Mechanisms

**Level 1: REST API Polling** (0-60 seconds disconnected)
- Switch from WebSocket to REST API
- Poll frequency: Every 2 seconds
- Endpoint: GET /api/v1/trading/floor/summary
- UI Update: Show "⏱ DELAYED" badge (data may be 2 seconds old)

**Level 2: Degraded Mode** (60-300 seconds disconnected)
- Increase poll interval to 5 seconds (reduce server load)
- Disable real-time animations (no flashing numbers)
- Show warning:
  ```
  ┌───────────────────────────────────────────────────────┐
  │ ⚠️ DEGRADED MODE - Live trading data unavailable     │
  │ Last successful update: 2 minutes ago                 │
  │                                                       │
  │ Your algorithms are still running, but UI updates    │
  │ are delayed. Use Emergency Stop if concerned.        │
  │                                                       │
  │ [🛑 Emergency Stop]  [Contact Support]  [Retry]      │
  └───────────────────────────────────────────────────────┘
  ```

**Level 3: Manual Intervention Required** (> 300 seconds disconnected)
- Show critical alert:
  ```
  ┌───────────────────────────────────────────────────────┐
  │ 🆘 CRITICAL: CONNECTION LOST FOR 5+ MINUTES          │
  │                                                       │
  │ We cannot confirm if your algorithms are running.    │
  │                                                       │
  │ RECOMMENDED ACTIONS:                                 │
  │ 1. Use Emergency Stop to halt all trading            │
  │ 2. Contact support immediately                       │
  │ 3. Check exchange accounts directly                  │
  │                                                       │
  │ [🛑 EMERGENCY STOP]  [Call Support: 1800-XXX-XXXX]   │
  └───────────────────────────────────────────────────────┘
  ```

---

### Reconnection Handling

**Auto-Retry Strategy**:
1. Immediate retry (after 1 second)
2. Exponential backoff: 2s, 4s, 8s, 16s, 30s (max)
3. Max retries: Unlimited (keep trying)

**Successful Reconnection**:
- Close disconnection banner
- Show success toast: "✅ Connection restored"
- Resume WebSocket updates
- Fetch full state sync: GET /api/v1/trading/floor/sync (ensure no missed data)

**Code Example**:
```typescript
const reconnectWebSocket = () => {
  let retryDelay = 1000;  // Start at 1 second
  const maxDelay = 30000;  // Cap at 30 seconds

  const attemptReconnect = () => {
    wsClient.connect()
      .then(() => {
        console.log('WebSocket reconnected');
        showToast('Connection restored', 'success');
        fetchFullStateSync();  // Catch up on missed updates
      })
      .catch(() => {
        console.log(`Reconnect failed, retrying in ${retryDelay}ms`);
        setTimeout(attemptReconnect, retryDelay);
        retryDelay = Math.min(retryDelay * 2, maxDelay);  // Exponential backoff
      });
  };

  attemptReconnect();
};
```

---

### Data Staleness Indicators

**Visual Cues**:
- Show "Last updated: X seconds ago" below each metric
- If > 10 seconds old, show amber warning icon ⚠️
- If > 60 seconds old, show red error icon 🔴

**Example** (Algorithm Card):
```
┌──────────────────────────────────────────┐
│ BTC Arbitrage v2.1                       │
│ P&L: +$542.30 (+1.8%)                   │
│ ⚠️ Last updated: 12 seconds ago          │ ← Staleness warning
│                                          │
│ Status: ✅ ACTIVE (unconfirmed)          │
└──────────────────────────────────────────┘
```

---

## 5. Error Handling

### Error Types and UI Responses

**Error 1: Insufficient Funds**
```
┌───────────────────────────────────┐
│ ⚠️ Trade Failed                   │
├───────────────────────────────────┤
│ Algorithm: BTC Arbitrage v2.1     │
│ Error: Insufficient funds         │
│                                   │
│ Available: $123.45                │
│ Required: $500.00                 │
│                                   │
│ Algorithm auto-paused.            │
│                                   │
│ [Add Funds]  [Stop Algorithm]     │
└───────────────────────────────────┘
```

**Error 2: Exchange API Failure**
```
┌───────────────────────────────────┐
│ ⚠️ Exchange Connection Error      │
├───────────────────────────────────┤
│ Binance API not responding        │
│                                   │
│ Your algorithms have been paused  │
│ to prevent losses.                │
│                                   │
│ [Retry Connection]  [Stop All]    │
└───────────────────────────────────┘
```

**Error 3: Rate Limit Exceeded**
```
┌───────────────────────────────────┐
│ ⚠️ Rate Limit Exceeded            │
├───────────────────────────────────┤
│ Too many requests to exchange API │
│                                   │
│ Algorithm paused for 60 seconds.  │
│ Countdown: 47s...                 │
│                                   │
│ [OK]                              │
└───────────────────────────────────┘
```

---

## 6. Performance Requirements

**Target Metrics**:
- **P&L Update Latency**: < 500ms from trade execution to UI update
- **Kill Switch Response**: < 2 seconds from click to API call sent
- **Chart Render**: < 100ms for P&L chart update
- **Memory Usage**: < 100MB for entire Floor page (long sessions)

**Monitoring**:
- Frontend: React DevTools Profiler
- Backend: CloudWatch metrics (API latency)
- Real User Monitoring (RUM): DataDog or New Relic

---

## 7. Accessibility

### Keyboard Shortcuts

- **Cmd/Ctrl+Shift+K**: Focus Kill Switch (confirm with Enter)
- **Cmd/Ctrl+Shift+P**: Pause all algorithms
- **Cmd/Ctrl+Shift+R**: Resume all paused algorithms
- **Tab**: Navigate between algorithm cards
- **Space**: Activate selected button

### Screen Reader Support

**ARIA Labels**:
```html
<button
  aria-label="Emergency stop all trading. Warning: This will close all positions immediately."
  role="button"
  aria-describedby="kill-switch-description"
>
  🛑 EMERGENCY STOP
</button>

<div id="kill-switch-description" class="sr-only">
  Press to stop all active trading algorithms and close all open positions. 
  This action requires confirmation.
</div>
```

**Live Regions**:
```html
<div aria-live="assertive" aria-atomic="true">
  <!-- Critical alerts (disconnection, errors) -->
  Connection lost. Attempting to reconnect.
</div>

<div aria-live="polite" aria-atomic="true">
  <!-- P&L updates -->
  Portfolio profit: $1,234.56, up 2.3%
</div>
```

---

## 8. Testing Strategy

### E2E Tests (Playwright)

**Test Case 1: Normal Trading Flow**
```typescript
test('should display active algorithms and update P&L', async ({ page }) => {
  await page.goto('/floor');
  
  // Verify P&L ticker visible
  await expect(page.locator('[data-testid="pnl-ticker"]')).toBeVisible();
  
  // Verify algorithms list
  const algorithms = page.locator('[data-testid="algorithm-card"]');
  await expect(algorithms).toHaveCount(3);
  
  // Verify status indicators
  await expect(algorithms.nth(0).locator('.status-badge')).toHaveText('ACTIVE');
});
```

**Test Case 2: Pause Algorithm**
```typescript
test('should pause algorithm with confirmation', async ({ page }) => {
  await page.goto('/floor');
  
  // Click pause button
  await page.click('[data-testid="algorithm-card"]:first-child >> text=Pause');
  
  // Verify confirmation modal
  await expect(page.locator('text=Pause Algorithm?')).toBeVisible();
  
  // Confirm pause
  await page.click('text=⏸️ Pause');
  
  // Verify status change
  await expect(page.locator('[data-testid="algorithm-card"]:first-child .status-badge'))
    .toHaveText('PAUSED');
});
```

**Test Case 3: Kill Switch Activation**
```typescript
test('should activate kill switch with typed confirmation', async ({ page }) => {
  await page.goto('/floor');
  
  // Click kill switch
  await page.click('[data-testid="kill-switch"]');
  
  // Verify modal
  await expect(page.locator('text=EMERGENCY STOP')).toBeVisible();
  
  // Type "STOP" (button should be disabled until typed)
  const stopButton = page.locator('text=🛑 EMERGENCY STOP');
  await expect(stopButton).toBeDisabled();
  
  await page.fill('input[type="text"]', 'STOP');
  await expect(stopButton).toBeEnabled();
  
  // Confirm
  await stopButton.click();
  
  // Verify progress modal
  await expect(page.locator('text=STOPPING ALL TRADING')).toBeVisible();
  
  // Wait for completion
  await expect(page.locator('text=ALL TRADING STOPPED')).toBeVisible({ timeout: 15000 });
});
```

**Test Case 4: Disconnected State**
```typescript
test('should handle WebSocket disconnection', async ({ page, context }) => {
  await page.goto('/floor');
  
  // Simulate WebSocket close
  await page.evaluate(() => {
    window.wsClient.close();
  });
  
  // Verify disconnection banner
  await expect(page.locator('text=CONNECTION LOST')).toBeVisible();
  
  // Verify P&L ticker shows disconnected state
  await expect(page.locator('[data-testid="pnl-ticker"] >> text=DISCONNECTED'))
    .toBeVisible();
  
  // Verify fallback to REST API (check for "DELAYED" badge)
  await expect(page.locator('text=DELAYED')).toBeVisible();
});
```

---

### Visual Regression Tests (Chromatic)

**Storybook Stories**:
```typescript
// Kill Switch states
export const KillSwitchReady = () => <KillSwitch state="ready" />;
export const KillSwitchHover = () => <KillSwitch state="hover" />;
export const KillSwitchCooldown = () => <KillSwitch state="cooldown" countdown={3} />;

// Algorithm card states
export const AlgorithmActive = () => <AlgorithmCard status="active" pnl={542.30} />;
export const AlgorithmPaused = () => <AlgorithmCard status="paused" pnl={320.50} />;
export const AlgorithmError = () => <AlgorithmCard status="error" error="Insufficient funds" />;

// Disconnected state
export const FloorDisconnected = () => <FloorPage isConnected={false} />;
```

---

## 9. Document Maintenance

**Update Triggers**:
- New safety mechanism added (e.g., circuit breaker)
- Exchange API change (new error types)
- User feedback on Kill Switch UX

**Review Schedule**:
- Per Sprint: Add new features from sprint work
- Monthly: Safety audit (Frontend + Backend leads)
- Quarterly: User testing session (Product team)

**Ownership**:
- Frontend Lead: UI implementation
- Backend Lead: API contracts and safety mechanisms
- Product Manager: User experience and safety requirements

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-24  
**Next Review**: 2026-02-24  
**Related Docs**: DESIGN_SYSTEM.md, API_CONTRACTS.md, SYSTEM_REQUIREMENTS.md (REQ-FL-DISC-001)
