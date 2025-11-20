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
from app.services.trading.client import CoinspotTradingClient, CoinspotAPIError, CoinspotTradingError

logger = logging.getLogger(__name__)


class OrderExecutionError(Exception):
    """Base exception for order execution errors"""
    pass


class OrderExecutor:
    """
    Executes trading orders with queue management and retry logic
    
    Features:
    - Queue-based order submission
    - Exponential backoff retry logic
    - Order status tracking
    - Position updates after execution
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
                
                # Update position
                await self._update_position(order)
                
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
                    logger.error(f"Order {order_id} failed after {self.max_retries} attempts")
                    
            except Exception as e:
                logger.error(f"Unexpected error executing order {order_id}: {e}", exc_info=True)
                order.status = 'failed'
                order.error_message = str(e)
                order.updated_at = datetime.now(timezone.utc)
                self.session.add(order)
                self.session.commit()
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
        async with CoinspotTradingClient(self.api_key, self.api_secret) as client:
            if order.side == 'buy':
                # For buy orders, quantity is in AUD
                result = await client.market_buy(order.coin_type, order.quantity)
            elif order.side == 'sell':
                # For sell orders, quantity is in cryptocurrency
                result = await client.market_sell(order.coin_type, order.quantity)
            else:
                raise OrderExecutionError(f"Invalid order side: {order.side}")
            
            return result
    
    async def _update_position(self, order: Order) -> None:
        """
        Update user's position after order execution
        
        Args:
            order: Executed order
        """
        # Get existing position
        statement = select(Position).where(
            Position.user_id == order.user_id,
            Position.coin_type == order.coin_type
        )
        position = self.session.exec(statement).first()
        
        if order.side == 'buy':
            if position:
                # Update existing position (average price calculation)
                total_quantity = position.quantity + order.filled_quantity
                total_cost = position.total_cost + (order.filled_quantity * order.price)
                position.quantity = total_quantity
                position.total_cost = total_cost
                position.average_price = total_cost / total_quantity
                position.updated_at = datetime.now(timezone.utc)
            else:
                # Create new position
                position = Position(
                    user_id=order.user_id,
                    coin_type=order.coin_type,
                    quantity=order.filled_quantity,
                    average_price=order.price,
                    total_cost=order.filled_quantity * order.price,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
            
            self.session.add(position)
            
        elif order.side == 'sell':
            if position:
                # Reduce position
                position.quantity -= order.filled_quantity
                
                if position.quantity <= 0:
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
        logger.info(f"Position updated for {order.user_id}, {order.coin_type}")


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
