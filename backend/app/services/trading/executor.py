"""
Order Execution Service

This module provides queue-based order execution with retry logic
and order status tracking.
"""
import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models import Order, Position
from app.core.config import settings
from app.services.websocket_manager import manager
from app.services.trading.client import CoinspotTradingClient, CoinspotAPIError, CoinspotTradingError
from fastapi.encoders import jsonable_encoder
from app.services.trading.exceptions import OrderExecutionError
from app.services.trading.safety import TradingSafetyManager, SafetyViolation

logger = logging.getLogger(__name__)


class OrderExecutor:
    """
    Executes trading orders with queue management and retry logic
    
    Features:
    - Queue-based order submission
    - Exponential backoff retry logic
    - Order status tracking
    - Position updates after execution
    - Risk management checks
    - Support for Ghost Mode (paper trading)
    """
    
    def __init__(
        self,
        session: Session,
        api_key: str,
        api_secret: str,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize order executor
        
        Args:
            session: Database session
            api_key: Coinspot API key
            api_secret: Coinspot API secret
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Initial retry delay in seconds (default: 1.0)
        """
        self.session = session
        self.api_key = api_key
        self.api_secret = api_secret
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._queue: asyncio.Queue[UUID] = asyncio.Queue()
        self._running = False
        self.safety_manager = TradingSafetyManager(session)
    
    async def submit_order(self, order_id: UUID) -> None:
        """
        Add an order to the execution queue
        
        Args:
            order_id: UUID of the order to execute
        """
        logger.info(f"Submitting order {order_id} to execution queue")
        await self._queue.put(order_id)
    
    async def start(self) -> None:
        """Start the order execution worker"""
        if self._running:
            logger.warning("Order executor is already running")
            return
        
        self._running = True
        logger.info("Starting order executor")
        
        try:
            while self._running:
                try:
                    # Get next order from queue with timeout
                    order_id = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=1.0
                    )
                    
                    # Execute the order
                    await self._execute_order(order_id)
                    
                    # Mark task as done
                    self._queue.task_done()
                    
                except asyncio.TimeoutError:
                    # No orders in queue, continue waiting
                    continue
                except Exception as e:
                    logger.error(f"Error in order executor main loop: {e}", exc_info=True)
        finally:
            self._running = False
            logger.info("Order executor stopped")
    
    async def stop(self) -> None:
        """Stop the order execution worker"""
        logger.info("Stopping order executor")
        self._running = False
        
        # Wait for queue to be empty
        await self._queue.join()
    
    async def _execute_order(self, order_id: UUID) -> None:
        """
        Execute a single order with retry logic
        
        Args:
            order_id: UUID of the order to execute
        """
        # Load order from database
        order = self.session.get(Order, order_id)
        if not order:
            logger.error(f"Order {order_id} not found in database")
            return
        
        # Check if order is already processed
        if order.status in ['filled', 'cancelled', 'failed']:
            logger.warning(f"Order {order_id} already processed with status {order.status}")
            return
        
        logger.info(f"Executing order {order_id}: {order.side} {order.quantity} {order.coin_type}")
        
        # Safety Check
        try:
            # Determine estimated price for validation
            # For market buy (amount is AUD), price is effectively 1 (as quantity is Value)
            # For limit orders, use the limit price
            estimated_price = order.price if order.price else Decimal('1.0') 
            
            await self.safety_manager.validate_trade(
                user_id=order.user_id,
                coin_type=order.coin_type,
                side=order.side,
                quantity=order.quantity,
                estimated_price=estimated_price,
                algorithm_id=order.algorithm_id
            )
        except SafetyViolation as e:
            logger.error(f"Safety violation for order {order_id}: {e}")
            order.status = 'failed'
            order.error_message = f"Safety violation: {str(e)}"
            order.updated_at = datetime.now(timezone.utc)
            self.session.add(order)
            self.session.commit()
            self.session.refresh(order)

            # Broadcast update
            await manager.broadcast_json(
                {"type": "order_update", "data": self._order_to_dict(order)},
                f"trading_{order.user_id}"
            )
            return

        # Execute with retry logic
        for attempt in range(self.max_retries):
            try:
                # Update order status to submitted
                if attempt == 0:
                    order.status = 'submitted'
                    order.submitted_at = datetime.now(timezone.utc)
                    order.updated_at = datetime.now(timezone.utc)
                    self.session.add(order)
                    self.session.commit()
                    self.session.refresh(order)
                    
                    # Broadcast update
                    await manager.broadcast_json(
                        {"type": "order_update", "data": self._order_to_dict(order)},
                        f"trading_{order.user_id}"
                    )
                
                # Execute the trade
                result = await self._execute_trade(order)
                
                # Update order with results
                order.status = 'filled'
                order.filled_quantity = order.quantity
                order.filled_at = datetime.now(timezone.utc)
                order.updated_at = datetime.now(timezone.utc)
                order.coinspot_order_id = result.get('id')
                
                # Store execution price if available
                if 'rate' in result:
                    order.price = Decimal(str(result['rate']))
                
                self.session.add(order)
                self.session.commit()
                self.session.refresh(order)
                
                # Broadcast update
                await manager.broadcast_json(
                    {"type": "order_update", "data": self._order_to_dict(order)},
                    f"trading_{order.user_id}"
                )
                
                # Update position
                await self._update_position(order, result)
                
                logger.info(f"Order {order_id} executed successfully: {order.coinspot_order_id}")
                return
                
            except CoinspotAPIError as e:
                logger.error(f"API error executing order {order_id} (attempt {attempt + 1}/{self.max_retries}): {e}")
                
                # Update order with error
                order.error_message = str(e)
                order.updated_at = datetime.now(timezone.utc)
                
                if attempt < self.max_retries - 1:
                    # Retry with exponential backoff
                    delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying order {order_id} in {delay} seconds")
                    self.session.add(order)
                    self.session.commit()
                    await asyncio.sleep(delay)
                else:
                    # Max retries reached
                    order.status = 'failed'
                    self.session.add(order)
                    self.session.commit()
                    self.session.refresh(order)
                    
                    # Broadcast update
                    await manager.broadcast_json(
                        {"type": "order_update", "data": self._order_to_dict(order)},
                        f"trading_{order.user_id}"
                    )
                    
                    logger.error(f"Order {order_id} failed after {self.max_retries} attempts")
                    
            except Exception as e:
                logger.error(f"Unexpected error executing order {order_id}: {e}", exc_info=True)
                order.status = 'failed'
                order.error_message = str(e)
                self.session.refresh(order)
                order.updated_at = datetime.now(timezone.utc)
                self.session.add(order)
                self.session.commit()

                # Broadcast update
                await manager.broadcast_json(
                    {"type": "order_update", "data": self._order_to_dict(order)},
                    f"trading_{order.user_id}"
                )
                return
    
    async def _execute_trade(self, order: Order) -> dict[str, Any]:
        """
        Execute the actual trade on Coinspot
        
        Args:
            order: Order to execute
            
        Returns:
            Coinspot API response
            
        Raises:
            CoinspotAPIError: If API returns an error
        """
        # Ghost Mode Check
        if settings.TRADING_MODE == 'paper':
            logger.info(f"Ghost Mode: Simulating execution for order {order.id}")
            # Mock successful response
            mock_price = order.price if order.price else Decimal('1000.0')
            
            # Helper to calculate expected coin amount for buy (AUD quantity) or sell (Coin quantity)
            if order.side == 'buy':
                # Quantity is AUD
                mock_coins = order.quantity / mock_price
            else:
                # Quantity is Coins
                mock_coins = order.quantity

            return {
                'status': 'ok',
                'id': f'ghost-{order.id}',
                'rate': str(mock_price),
                'amount': str(mock_coins), # Coins amount
                'total': str(order.quantity * mock_price) if order.side == 'sell' else str(order.quantity) # AUD total
            }

        async with CoinspotTradingClient(self.api_key, self.api_secret) as client:
            if order.side == 'buy':
                if order.order_type == 'limit':
                    if not order.price:
                        # Should have been caught by validation or set
                        raise OrderExecutionError("Limit buy order requires price")
                    result = await client.limit_buy(order.coin_type, order.quantity, order.price)
                else:
                    # Market buy: quantity is AUD amount
                    result = await client.market_buy(order.coin_type, order.quantity)
            elif order.side == 'sell':
                if order.order_type == 'limit':
                    if not order.price:
                        raise OrderExecutionError("Limit sell order requires price")
                    result = await client.limit_sell(order.coin_type, order.quantity, order.price)
                else:
                    # Market sell: quantity is Coin amount
                    result = await client.market_sell(order.coin_type, order.quantity)
            else:
                raise OrderExecutionError(f"Invalid order side: {order.side}")
            
            return result
    
    async def _update_position(self, order: Order, result: dict[str, Any] | None = None) -> None:
        """
        Update user's position after order execution
        
        Args:
            order: Executed order
            result: Execution result from API (optional)
        """
        # Get existing position
        statement = select(Position).where(
            Position.user_id == order.user_id,
            Position.coin_type == order.coin_type
        )
        position = self.session.exec(statement).first()
        
        # Determine coins bought/sold and cost
        coins_delta = Decimal('0')
        cost_delta = Decimal('0')
        
        if result and 'amount' in result:
             # If result provides amount (coins), use it.
             coins_delta = Decimal(str(result['amount']))

        if order.side == 'buy':
            # Buy Order
            # Determine cost delta (AUD spent)
            if result and 'total' in result:
                cost_delta = Decimal(str(result['total']))
            else:
                 # Fallback: For market buy, quantity is AUD. For limit buy, it might be AUD too in Coinspot if 'amount' param was used as funds.
                 # But CoinSpot limit buy via client uses coins? No, wait. 
                 # CoinSpot limit buy: client code I wrote used 'amount' (AUD) parameter.
                 # So order.quantity is AUD for both Limit and Market Buy if relying on my client impl.
                 cost_delta = order.filled_quantity 

            if coins_delta == 0:
                # Calculate from cost and price
                if order.price and order.price > 0:
                    coins_delta = cost_delta / order.price
                else:
                    logger.error(f"Cannot calculate coins bought for order {order.id}: no price")
                    return

            if position:
                # Update existing position
                total_quantity = position.quantity + coins_delta
                total_cost = position.total_cost + cost_delta
                
                position.quantity = total_quantity
                position.total_cost = total_cost
                if total_quantity > 0:
                    position.average_price = total_cost / total_quantity
                position.updated_at = datetime.now(timezone.utc)
            else:
                # Create new position
                average_price = cost_delta / coins_delta if coins_delta > 0 else (order.price if order.price else Decimal('0'))
                position = Position(
                    user_id=order.user_id,
                    coin_type=order.coin_type,
                    quantity=coins_delta,
                    average_price=average_price,
                    total_cost=cost_delta,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
            
            self.session.add(position)
            
        elif order.side == 'sell':
            if coins_delta == 0:
                coins_delta = order.filled_quantity

            if position:
                # Reduce position
                position.quantity -= coins_delta
                
                if position.quantity <= 0.00000001: # Epsilon check for near zero
                    # Position closed
                    self.session.delete(position)
                else:
                    # Reduce total cost proportionally
                    position.total_cost = position.quantity * position.average_price
                    position.updated_at = datetime.now(timezone.utc)
                    self.session.add(position)
            else:
                logger.warning(f"Sell order {order.id} executed but no position found for {order.coin_type}")
        
        self.session.commit()

        # Broadcast position update
        if position:
            self.session.refresh(position)
            await manager.broadcast_json(
                {"type": "position_update", "data": jsonable_encoder(position)},
                f"trading_{order.user_id}"
            )
        
        logger.info(f"Position updated for {order.user_id}, {order.coin_type}")

    def _order_to_dict(self, order: Order) -> dict:
        """Helper to serialize order to dict manually to avoid encoder issues"""
        return {
            "id": str(order.id),
            "user_id": str(order.user_id),
            "coin_type": order.coin_type,
            "side": order.side,
            "quantity": float(order.quantity),
            "price": float(order.price) if order.price is not None else None,
            "order_type": order.order_type,
            "status": order.status,
            "filled_quantity": float(order.filled_quantity) if order.filled_quantity is not None else 0.0,
            "filled_at": order.filled_at.isoformat() if order.filled_at else None,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None,
            "coinspot_order_id": order.coinspot_order_id,
            "error_message": order.error_message
        }


class OrderQueue:
    """
    Singleton queue manager for order execution
    
    Provides a global queue for managing order execution across the application.
    """
    
    _instance: "OrderQueue | None" = None
    _executor: OrderExecutor | None = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(
        self,
        session: Session,
        api_key: str,
        api_secret: str,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> None:
        """
        Initialize the order executor
        
        Args:
            session: Database session
            api_key: Coinspot API key
            api_secret: Coinspot API secret
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay
        """
        if self._executor is None:
            self._executor = OrderExecutor(
                session=session,
                api_key=api_key,
                api_secret=api_secret,
                max_retries=max_retries,
                retry_delay=retry_delay
            )
    
    async def submit(self, order_id: UUID) -> None:
        """Submit an order for execution"""
        if self._executor is None:
            raise OrderExecutionError("OrderQueue not initialized")
        await self._executor.submit_order(order_id)
    
    async def start(self) -> None:
        """Start the executor worker"""
        if self._executor is None:
            raise OrderExecutionError("OrderQueue not initialized")
        await self._executor.start()
    
    async def stop(self) -> None:
        """Stop the executor worker"""
        if self._executor is not None:
            await self._executor.stop()


def get_order_queue() -> OrderQueue:
    """Get the global order queue instance"""
    return OrderQueue()
