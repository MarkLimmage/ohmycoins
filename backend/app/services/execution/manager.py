# mypy: ignore-errors
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal

from .schemas import AlgoOrder, AlgoOrderCreate, AlgoOrderStatus, ExecutionStrategyType
from .twap import TWAPStrategy
from .vwap import VWAPStrategy
from .base import ExecutionStrategy

class AlgoOrderManager:
    """
    Manages the lifecycle of algorithmic orders.
    """
    def __init__(self):
        # In-memory storage for active orders
        self.orders: Dict[UUID, AlgoOrder] = {}
        self.strategies: Dict[UUID, ExecutionStrategy] = {}
        # Schedules: order_id -> List[(time, qty)]
        self.schedules: Dict[UUID, list] = {} 
        
    def submit_order(self, order_create: AlgoOrderCreate) -> AlgoOrder:
        """
        Submits a new algorithmic order.
        """
        # Convert AlgoOrderCreate to AlgoOrder
        # Using model_validate with update to add defaults
        order_data = order_create.model_dump()
        order = AlgoOrder(**order_data)
        
        self.orders[order.id] = order
        
        # Initialize strategy
        strategy: ExecutionStrategy
        if order.strategy == ExecutionStrategyType.TWAP:
            strategy = TWAPStrategy(order)
        elif order.strategy == ExecutionStrategyType.VWAP:
            strategy = VWAPStrategy(order)
        else:
            order.status = AlgoOrderStatus.FAILED
            raise ValueError(f"Unknown strategy: {order.strategy}")
            
        self.strategies[order.id] = strategy
        
        # Generate execution schedule
        try:
            schedule = strategy.generate_schedule()
            self.schedules[order.id] = schedule
            order.status = AlgoOrderStatus.RUNNING
        except Exception as e:
            order.status = AlgoOrderStatus.FAILED
            # Log error
            print(f"Failed to generate schedule for order {order.id}: {e}")
        
        return order
        
    def get_order(self, order_id: UUID) -> Optional[AlgoOrder]:
        return self.orders.get(order_id)
        
    def cancel_order(self, order_id: UUID) -> bool:
        order = self.orders.get(order_id)
        if order and order.status in [AlgoOrderStatus.PENDING, AlgoOrderStatus.RUNNING]:
            order.status = AlgoOrderStatus.CANCELLED
            return True
        return False
        
    def get_active_orders(self) -> List[AlgoOrder]:
        return [
            o for o in self.orders.values() 
            if o.status in [AlgoOrderStatus.PENDING, AlgoOrderStatus.RUNNING]
        ]

    def on_tick(self, current_time: datetime) -> List[Dict]:
        """
        Checks active orders and generates child orders if schedule permits.
        Returns a list of generated child order details.
        """
        orders_generated = []
        for order_id, order in self.orders.items():
            if order.status != AlgoOrderStatus.RUNNING:
                continue
                
            schedule = self.schedules.get(order_id)
            if not schedule:
                continue
                
            idx = order.next_schedule_index
            if idx >= len(schedule):
                order.status = AlgoOrderStatus.COMPLETED
                continue
                
            scheduled_time, qty = schedule[idx]
            
            # If current_time >= scheduled_time, execute
            # Note: We use >= and process sequentially. 
            # If we missed multiple, this loop might only process one per tick depending on logic,
            # but here we can stick to one per tick or use a while loop if needed.
            if current_time >= scheduled_time:
                # Execute logic
                child_order_id = str(uuid4()) # Mock ID
                orders_generated.append({
                    "parent_id": str(order.id),
                    "child_id": child_order_id,
                    "symbol": order.symbol,
                    "side": order.side,
                    "quantity": str(qty) # Decimal not JSON serializable usually, stringifying for safety
                })
                
                order.child_orders.append(child_order_id)
                order.filled_quantity += qty # Optimistic fill for now
                order.next_schedule_index += 1
                
                # Check for completion
                if order.next_schedule_index >= len(schedule):
                    order.status = AlgoOrderStatus.COMPLETED
                    
        return orders_generated
