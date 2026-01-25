# Trading Engine Services

## System Overview

The Trading Engine encapsulates the logic for executing orders, managing positions, and assessing risk. It interacts with the CoinSpot API for actual execution while maintaining local state in the database.

## Class Diagram

```mermaid
classDiagram
    class OrderRequest {
        +UUID user_id
        +String coin_type
        +String side
        +String order_type
        +Decimal quantity
        +Decimal price
        +UUID algorithm_id
    }

    class OrderResponse {
        +UUID id
        +String status
        +Decimal filled_quantity
        +DateTime created_at
        +DateTime updated_at
    }

    class Position {
        +UUID id
        +UUID user_id
        +String coin_type
        +Decimal quantity
        +Decimal average_price
        +Decimal total_cost
        +DateTime created_at
        +DateTime updated_at
    }

    class OrderExecutor {
        -Session session
        -CoinspotTradingClient client
        +place_order(order_request) OrderResponse
        +cancel_order(order_id) bool
        +process_queue()
    }

    class PositionManager {
        -Session session
        +get_position(user_id, coin) Position
        +update_position(user_id, coin, execution_details)
        +calculate_pnl(user_id) Decimal
    }

    class RiskManager {
        +check_order_risk(order_request, position) bool
        +validate_stop_loss(position)
    }

    OrderExecutor ..> OrderRequest : uses
    OrderExecutor ..> OrderResponse : returns
    OrderExecutor --> PositionManager : updates
    OrderExecutor --> RiskManager : validates
    PositionManager --> Position : manages
```
