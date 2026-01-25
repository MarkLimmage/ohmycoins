# Execution Algorithms Service

This service implements standard execution algorithms to break down large "Parent Orders" into smaller "Child Orders" to minimize market impact and optimize execution price.

## Overview

The Execution Service manages the lifecycle of algorithmic orders (`AlgoOrder`), handling the slicing and scheduling of child orders based on the selected strategy.

## Supported Algorithms

### 1. TWAP (Time-Weighted Average Price)

The TWAP strategy splits a large order into equal-sized chunks to be executed at regular time intervals over a specified duration.

**Logic:**
- **Total Quantity ($S$):** The total size of the parent order.
- **Duration ($T$):** The time window for execution.
- **Number of Slices ($N$):** Computed based on minimum order size or specified interval.
- **Slice Size:** $S / N$
- **Interval:** $T / N$

**Use Case:**
- Reducing market impact for large orders.
- Executing orders over a fixed time horizon without regard to volume profile.

### 2. VWAP (Volume-Weighted Average Price)

The VWAP strategy executes the order in proportion to the historical volume profile of the asset. It aims to achieve an execution price close to the market's VWAP over the execution window.

**Logic:**
- **Historical Profile:** Uses `PriceData5Min` to determine the average volume distribution for the specific time of day.
- **Slicing:** Allocates larger child orders during periods of high historical volume and smaller orders during low volume periods.

**Use Case:**
- Minimizing slippage by liquidity seeking.
- Benchmarking execution against the market VWAP.

## Architecture

- **AlgoOrderManager:** Orchestrates the lifecycle of parent orders.
- **Strategy Implementations:** `TWAPStrategy` and `VWAPStrategy` classes inheriting from a base `ExecutionStrategy`.
- **State Management:** Tracks `filled_quantity`, `remaining_quantity`, and `status` of parent orders.

## Usage

```python
# Pseudo-code example
algo_order = AlgoOrderCreate(
    symbol="BTC/AUD",
    side=OrderSide.BUY,
    total_quantity=Decimal("1.0"),
    strategy=ExecutionStrategyType.TWAP,
    parameters={"duration_minutes": 60, "interval_minutes": 5}
)

manager = AlgoOrderManager()
order = manager.submit_order(algo_order)

# Simulation loop
import time
from datetime import datetime
while order.status == AlgoOrderStatus.RUNNING:
    current_time = datetime.now()
    child_orders = manager.on_tick(current_time)
    for child in child_orders:
        print(f"Executing child order: {child}")
        # Send to OrderExecutor...
    time.sleep(1)
```
