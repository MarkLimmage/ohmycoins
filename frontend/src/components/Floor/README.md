# Safety Button Components

Safety-critical UI components for Oh My Coins trading floor operations. These components implement WCAG 2.1 AA accessibility standards and include comprehensive safety features.

## Components

### SafetyButton (Base Component)

Generic safety button with confirmation flow, cooldown, and audit logging.

**Props:**
- `action`: 'kill' | 'confirm' | 'stop' - Action type
- `onConfirm`: () => Promise<void> - Async callback when confirmed
- `requireConfirmation`: boolean - Show confirmation modal
- `confirmationText?`: string - Required typed text (e.g., "STOP")
- `isDisabled?`: boolean - Disable button
- `cooldownSeconds?`: number - Cooldown duration (default: 5)
- `children?`: ReactNode - Button content
- `label?`: string - Accessibility label
- `description?`: string - Detailed aria-describedby text
- `buttonSize?`: string - Chakra size
- `colorScheme?`: string - Chakra color scheme

**Features:**
- ✅ Confirmation modal with focus trap
- ✅ Optional typed confirmation
- ✅ 5-second cooldown after use
- ✅ Loading spinner during async operations
- ✅ Success/error feedback
- ✅ Audit logging (console.log)
- ✅ Full keyboard navigation (Tab, Enter, Esc)
- ✅ ARIA live regions for alerts
- ✅ Focus indicators (2px outline)

**Example:**
```tsx
import { SafetyButton } from '@/components/Floor';

<SafetyButton
  action="confirm"
  onConfirm={async () => await executeTrade()}
  requireConfirmation={true}
  cooldownSeconds={5}
  label="Execute Trade"
>
  Execute
</SafetyButton>
```

---

### KillSwitch

Large emergency stop button with fixed positioning and keyboard shortcut.

**Props:**
- `onKill`: () => Promise<void> - Emergency stop callback
- `isDisabled?`: boolean - Disable button

**Features:**
- ✅ 120x120px red button
- ✅ Fixed bottom-right position (20px from edges)
- ✅ Keyboard shortcut: **Ctrl+Shift+K** (focuses button)
- ✅ Octagon-X icon (MdCancel from react-icons)
- ✅ "EMERGENCY STOP" label
- ✅ Requires confirmation before executing
- ✅ Detailed aria-describedby
- ✅ Always visible overlay (z-index: 9999)

**Accessibility:**
- ARIA live region for status updates
- Keyboard shortcut announced in description
- Focus trap in confirmation modal
- Assertive alerts for critical actions

**Example:**
```tsx
import { KillSwitch } from '@/components/Floor';

<KillSwitch
  onKill={async () => {
    await stopAllAlgorithms();
    await closeAllPositions();
  }}
/>
```

---

### ConfirmTrade

Two-step confirmation button for trade execution.

**Props:**
- `onConfirm`: () => Promise<void> - Trade execution callback
- `isDisabled?`: boolean - Disable button
- `tradeDetails?`: string - Optional trade description

**Features:**
- ✅ Amber/orange color scheme (warning)
- ✅ Standard button size
- ✅ Two-step modal confirmation
- ✅ 5-second cooldown
- ✅ Audit logging

**Example:**
```tsx
import { ConfirmTrade } from '@/components/Floor';

<ConfirmTrade
  onConfirm={async () => await placeTrade()}
  tradeDetails="BUY 100 BTC at $50,000"
/>
```

---

### EmergencyStop

Emergency stop with typed confirmation ("STOP").

**Props:**
- `onStop`: () => Promise<void> - Emergency stop callback
- `isDisabled?`: boolean - Disable button
- `consequences?`: string[] - List of consequences to display

**Features:**
- ✅ Large red button with cancel icon
- ✅ Requires typing "STOP" to confirm
- ✅ Shows list of consequences:
  - Cancel all pending orders
  - Liquidate all open positions
  - Disable all trading algorithms
  - Block new trade execution
- ✅ 5-second cooldown
- ✅ Prominent warning styling
- ✅ Auto-uppercase input

**Example:**
```tsx
import { EmergencyStop } from '@/components/Floor';

<EmergencyStop
  onStop={async () => {
    await cancelAllOrders();
    await liquidatePositions();
    await disableAlgorithms();
  }}
  consequences={[
    'Cancel all pending orders',
    'Liquidate all open positions',
    'Disable all trading algorithms',
  ]}
/>
```

---

## Safety Features

### Cooldown Mechanism
- 5-second default cooldown after each use
- Prevents accidental double-clicks
- Button shows "Wait Xs" during cooldown
- Configurable via `cooldownSeconds` prop

### Audit Logging
All clicks are logged to console (MVP):
```
[AUDIT] 2025-01-26T10:30:15.123Z - SafetyButton - kill - User: current-user
[AUDIT] 2025-01-26T10:30:18.456Z - SafetyButton-Confirmed - kill - User: current-user
```

Production systems should integrate with backend audit service.

### Confirmation Flows
1. **Simple Confirmation**: Modal with "Are you sure?"
2. **Typed Confirmation**: Requires typing specific text (e.g., "STOP")
3. **No Confirmation**: Direct execution (use with caution)

### Error Handling
- All errors caught and displayed in modal
- Errors logged to audit trail
- User-friendly error messages
- Does not close modal on error (allows retry)

---

## Accessibility (WCAG 2.1 AA Compliance)

### Keyboard Navigation
- **Tab**: Navigate between elements
- **Enter/Space**: Activate buttons
- **Esc**: Close modals
- **Ctrl+Shift+K**: Focus Kill Switch (global)

### Screen Reader Support
- ARIA labels on all interactive elements
- aria-describedby for detailed descriptions
- ARIA live regions with assertive priority for alerts
- Focus trap in modals (prevents focus escape)
- Visually hidden descriptions (position: absolute, left: -9999px)

### Focus Indicators
- 2px solid outline on all focusable elements
- Blue color (blue.500) for high contrast
- 2px outlineOffset for visibility

### Requirements Coverage
- ✅ **REQ-UX-004**: Keyboard shortcuts (Ctrl+Shift+K)
- ✅ **REQ-UX-005**: Focus indicators (2px outline)
- ✅ **REQ-UX-007**: ARIA live regions (aria-live="assertive")
- ✅ **REQ-UX-009**: Detailed descriptions (aria-describedby)
- ✅ **REQ-FL-008**: Audit logging

---

## Performance

- **Interaction Latency**: <50ms (async callbacks prevent UI blocking)
- **Bundle Size**: ~8KB minified (including react-icons)
- **Re-renders**: Optimized with useCallback hooks
- **Memory**: Cleanup of timers and event listeners

---

## Styling

Uses Chakra UI v3 components exclusively:
- `Button`: Primary interactive element
- `Modal`: Confirmation dialogs
- `Input`: Typed confirmation
- `Box`, `Text`: Layout and typography
- `Spinner`: Loading states

Color schemes:
- **Red (#dc2626)**: Emergency/kill actions
- **Amber (#f59e0b)**: Warning/confirm actions
- **Gray (#9ca3af)**: Disabled state
- **Blue (#3b82f6)**: Focus indicators

---

## Integration Example

```tsx
import { KillSwitch, ConfirmTrade, EmergencyStop } from '@/components/Floor';

function TradingFloor() {
  return (
    <>
      {/* Fixed emergency button - always visible */}
      <KillSwitch
        onKill={async () => {
          await api.emergencyStop();
        }}
      />

      {/* Trade confirmation in form */}
      <ConfirmTrade
        onConfirm={async () => {
          await api.executeTrade(tradeData);
        }}
        tradeDetails={`${action} ${amount} ${symbol}`}
      />

      {/* Emergency stop in settings */}
      <EmergencyStop
        onStop={async () => {
          await api.stopAllTrading();
        }}
      />
    </>
  );
}
```

---

## Testing Recommendations

1. **Keyboard Navigation**
   - Tab through all elements
   - Activate with Enter/Space
   - Close modals with Esc
   - Test Ctrl+Shift+K shortcut

2. **Screen Readers**
   - Test with NVDA/JAWS/VoiceOver
   - Verify announcements
   - Check live region updates

3. **Error Scenarios**
   - Network failures
   - API timeouts
   - Validation errors
   - Verify error display and logging

4. **Cooldown**
   - Rapid clicking
   - Timer accuracy
   - State persistence

5. **Typed Confirmation**
   - Case sensitivity
   - Whitespace handling
   - Input focus on open

---

## Security Considerations

- Audit logs should be sent to backend (not just console)
- User identity should come from auth context (not hardcoded)
- Rate limiting should be enforced server-side
- Confirmation text should be validated server-side
- All destructive actions require backend authorization

---

## Future Enhancements

- [ ] Backend audit integration
- [ ] Real user identity from auth context
- [ ] Configurable keyboard shortcuts
- [ ] Sound effects for critical actions
- [ ] Animation on cooldown timer
- [ ] Biometric confirmation for kill switch
- [ ] Multi-language support
- [ ] Theme customization
- [ ] Analytics integration
