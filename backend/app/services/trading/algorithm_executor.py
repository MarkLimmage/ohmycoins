"""
Algorithm Execution Service

This module executes deployed trading algorithms, generating and executing
trading signals based on real-time market data.
"""
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Protocol
from uuid import UUID

from sqlmodel import Session

from app.models import Order, User
from app.services.trading.client import CoinspotTradingClient
from app.services.trading.recorder import TradeRecorder, get_trade_recorder
from app.services.trading.safety import TradingSafetyManager, get_safety_manager, SafetyViolation
from app.services.trading.executor import OrderQueue, get_order_queue

logger = logging.getLogger(__name__)


class TradingAlgorithm(Protocol):
    """
    Protocol for trading algorithms
    
    Any algorithm must implement this interface to be executable.
    This will be fully implemented when Phase 3 (Agentic) or Phase 4 (Manual Lab) is complete.
    """
    
    def generate_signal(self, market_data: dict[str, Any]) -> dict[str, Any]:
        """
        Generate trading signal based on market data
        
        Args:
            market_data: Current market data including prices, volumes, etc.
            
        Returns:
            Dictionary with trading signal:
            {
                'action': 'buy' | 'sell' | 'hold',
                'coin_type': str,
                'quantity': Decimal,
                'confidence': float  # 0.0 to 1.0
            }
        """
        ...


class AlgorithmExecutionError(Exception):
    """Base exception for algorithm execution errors"""
    pass


class AlgorithmExecutor:
    """
    Executes trading algorithms and manages their lifecycle
    
    Features:
    - Load and execute deployed algorithms
    - Fetch real-time market data
    - Generate trading signals
    - Execute trades via Coinspot API
    - Manage algorithm state and performance
    - Apply safety checks before execution
    """
    
    def __init__(
        self,
        session: Session,
        api_key: str,
        api_secret: str,
        safety_manager: TradingSafetyManager | None = None,
        trade_recorder: TradeRecorder | None = None
    ):
        """
        Initialize algorithm executor
        
        Args:
            session: Database session
            api_key: Coinspot API key
            api_secret: Coinspot API secret
            safety_manager: Safety manager instance (optional, will create if not provided)
            trade_recorder: Trade recorder instance (optional, will create if not provided)
        """
        self.session = session
        self.api_key = api_key
        self.api_secret = api_secret
        self.safety_manager = safety_manager or get_safety_manager(session)
        self.trade_recorder = trade_recorder or get_trade_recorder(session)
        self.order_queue = get_order_queue()
    
    async def execute_algorithm(
        self,
        user_id: UUID,
        algorithm_id: UUID,
        algorithm: TradingAlgorithm,
        market_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute a trading algorithm
        
        Args:
            user_id: User ID
            algorithm_id: Algorithm ID
            algorithm: Algorithm implementation
            market_data: Current market data
            
        Returns:
            Dictionary with execution results
            
        Raises:
            AlgorithmExecutionError: If execution fails
        """
        logger.info(f"Executing algorithm {algorithm_id} for user {user_id}")
        
        try:
            # Generate trading signal
            signal = algorithm.generate_signal(market_data)
            
            # Check if signal recommends action
            action = signal.get('action')
            if action == 'hold' or not action:
                logger.info(f"Algorithm {algorithm_id} recommends holding, no action taken")
                return {
                    'executed': False,
                    'reason': 'hold_signal',
                    'signal': signal
                }
            
            # Extract trade parameters
            coin_type = signal.get('coin_type')
            quantity = Decimal(str(signal.get('quantity', 0)))
            confidence = signal.get('confidence', 0.0)
            
            if not coin_type or quantity <= 0:
                logger.warning(f"Invalid signal from algorithm {algorithm_id}: {signal}")
                return {
                    'executed': False,
                    'reason': 'invalid_signal',
                    'signal': signal
                }
            
            # Get estimated price
            estimated_price = self._get_estimated_price(market_data, coin_type)
            
            # Validate trade with safety checks
            try:
                validation = await self.safety_manager.validate_trade(
                    user_id=user_id,
                    coin_type=coin_type,
                    side=action,
                    quantity=quantity,
                    estimated_price=estimated_price,
                    algorithm_id=algorithm_id
                )
            except SafetyViolation as e:
                logger.warning(f"Safety check failed for algorithm {algorithm_id}: {e}")
                return {
                    'executed': False,
                    'reason': 'safety_violation',
                    'error': str(e),
                    'signal': signal
                }
            
            # Log trade attempt
            order = self.trade_recorder.log_trade_attempt(
                user_id=user_id,
                coin_type=coin_type,
                side=action,
                quantity=quantity,
                algorithm_id=algorithm_id
            )
            
            # Submit order to execution queue
            await self.order_queue.submit(order.id)
            
            logger.info(
                f"Algorithm {algorithm_id} submitted order {order.id}: "
                f"{action} {quantity} {coin_type} (confidence: {confidence:.2f})"
            )
            
            return {
                'executed': True,
                'order_id': str(order.id),
                'signal': signal,
                'validation': validation
            }
            
        except Exception as e:
            logger.error(f"Error executing algorithm {algorithm_id}: {e}", exc_info=True)
            raise AlgorithmExecutionError(f"Algorithm execution failed: {e}")
    
    def _get_estimated_price(
        self,
        market_data: dict[str, Any],
        coin_type: str
    ) -> Decimal:
        """
        Get estimated execution price from market data
        
        Args:
            market_data: Market data
            coin_type: Coin type
            
        Returns:
            Estimated price
        """
        # Extract price from market data
        # Market data should contain current prices for all coins
        prices = market_data.get('prices', {})
        coin_data = prices.get(coin_type, {})
        
        # Use last price, or average of bid/ask
        last_price = coin_data.get('last')
        if last_price:
            return Decimal(str(last_price))
        
        bid = coin_data.get('bid', 0)
        ask = coin_data.get('ask', 0)
        
        if bid and ask:
            return Decimal(str((bid + ask) / 2))
        
        # Fallback to a default if no price available
        logger.warning(f"No price data available for {coin_type}, using 0")
        return Decimal('0')
    
    async def execute_multiple_algorithms(
        self,
        user_id: UUID,
        algorithms: list[tuple[UUID, TradingAlgorithm]],
        market_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Execute multiple algorithms for a user
        
        Args:
            user_id: User ID
            algorithms: List of (algorithm_id, algorithm) tuples
            market_data: Current market data
            
        Returns:
            List of execution results
        """
        results = []
        
        for algorithm_id, algorithm in algorithms:
            try:
                result = await self.execute_algorithm(
                    user_id=user_id,
                    algorithm_id=algorithm_id,
                    algorithm=algorithm,
                    market_data=market_data
                )
                results.append({
                    'algorithm_id': str(algorithm_id),
                    'result': result
                })
            except Exception as e:
                logger.error(f"Error executing algorithm {algorithm_id}: {e}")
                results.append({
                    'algorithm_id': str(algorithm_id),
                    'error': str(e)
                })
        
        return results
    
    def get_algorithm_performance(
        self,
        algorithm_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> dict[str, Any]:
        """
        Get performance metrics for an algorithm
        
        Args:
            algorithm_id: Algorithm ID
            start_date: Start date (optional)
            end_date: End date (optional)
            
        Returns:
            Dictionary with performance metrics
        """
        # Get trade history for this algorithm
        # Note: This requires user_id, which we'll need to add to the signature
        # For now, we'll return a placeholder
        # TODO: Update when full algorithm system is implemented
        
        logger.warning("Algorithm performance tracking not fully implemented yet")
        
        return {
            'algorithm_id': str(algorithm_id),
            'metrics': {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0.0,
                'win_rate': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0
            },
            'note': 'Full implementation pending Phase 3/4 completion'
        }


def get_algorithm_executor(
    session: Session,
    api_key: str,
    api_secret: str
) -> AlgorithmExecutor:
    """
    Get an algorithm executor instance
    
    Args:
        session: Database session
        api_key: Coinspot API key
        api_secret: Coinspot API secret
        
    Returns:
        AlgorithmExecutor instance
    """
    return AlgorithmExecutor(
        session=session,
        api_key=api_key,
        api_secret=api_secret
    )
