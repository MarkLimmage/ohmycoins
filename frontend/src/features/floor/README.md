# The Floor - Component Hierarchy

## Directory Structure
```
src/features/floor/
├── components/
│   ├── AlgorithmCard.tsx    # Individual algorithm control card
│   ├── AlgorithmGrid.tsx    # Grid layout for algorithms
│   ├── KillSwitch.tsx       # Emergency stop button wrapper
│   ├── PLTicker.tsx         # Real-time P&L top bar
│   └── FloorLayout.tsx      # Main dashboard layout
├── hooks/
│   ├── useFloorWebSocket.ts # WebSocket integration
│   └── useTradingControls.ts# Button handlers (pause, stop)
└── types/
    └── index.ts             # TS interfaces (Algo, P&L)
```

## Component Details

### 1. FloorLayout
- **Role**: Container for the entire Floor experience
- **Children**: PLTicker, AlgorithmGrid, KillSwitch
- **State**: Global disconnection status

### 2. PLTicker
- **Role**: Displays live portfolio metrics
- **Props**: `data: PLTickerData`
- **Features**: 
  - Real-time animate-pulse on updates
  - Color-coded background based on P&L

### 3. AlgorithmGrid
- **Role**: Responsive grid for algorithm cards
- **Layout**: 
  - Desktop: 3 columns
  - Tablet: 2 columns
  - Mobile: Hidden (Desktop only warning)

### 4. AlgorithmCard
- **Role**: Control unit for a single strategy
- **Props**: `algorithm: AlgorithmData`
- **Actions**: Pause, Resume, Stop (using SafetyButton)

### 5. KillSwitch
- **Role**: Global emergency stop
- **Implementation**: Uses `SafetyButton` with `type="kill"`
- **Position**: Fixed bottom-right `fixed bottom-8 right-8`
