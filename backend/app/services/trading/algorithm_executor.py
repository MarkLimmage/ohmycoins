"""
Algorithm Executor Service

Executes deployed trading algorithms by:
1. Loading algorithm artifacts (trained ML models)
2. Fetching real-time market data
3. Generating trading signals (buy/sell/hold)
4. Submitting trades via OrderQueue
5. Tracking execution state and results

Phase 6, Weeks 3-4
"""
import asyncio
import json
import logging
import pickle
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models import (
    Algorithm,
    DeployedAlgorithm,
    AgentArtifact,
    Order,
    OrderCreate,
    PriceData5Min,
)
from app.services.trading.executor import OrderQueue
from app.services.trading.safety import SafetyManager

logger = logging.getLogger(__name__)


class AlgorithmExecutionError(Exception):
    """Exception raised when algorithm execution fails"""
    pass


class AlgorithmExecutor:
    """
    Executes trading algorithms with safety checks and error handling
    
    Responsible for:
    - Loading algorithm artifacts from database
    - Deserializing ML models (if artifact-based)
    - Fetching real-time data for algorithm input
    - Generating trading signals
    - Submitting orders with safety checks
    - Tracking execution state
    """
    
    def __init__(
        self,
        db_session: Session,
        safety_manager: SafetyManager | None = None,
        order_queue: OrderQueue | None = None,
    ):
        """
        Initialize algorithm executor
        
        Args:
            db_session: Database session for queries
            safety_manager: Safety manager for pre-trade checks (optional)
            order_queue: Order queue for trade execution (optional, uses global if None)
        """
        self.db = db_session
        self.safety_manager = safety_manager or SafetyManager(db_session)
        self.order_queue = order_queue or OrderQueue()
        self._loaded_algorithms: dict[UUID, Any] = {}  # Cache loaded models
    
    async def execute_algorithm(
        self,
        deployment_id: UUID,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Execute a deployed algorithm once
        
        Args:
            deployment_id: UUID of the DeployedAlgorithm to execute
            dry_run: If True, generate signals but don't submit orders
            
        Returns:
            Dict with execution results:
            {
                "deployment_id": UUID,
                "signals": [{"action": "buy"|"sell"|"hold", "coin": str, "quantity": Decimal, "confidence": float}],
                "orders_submitted": int,
                "errors": [str],
                "execution_time_ms": float
            }
            
        Raises:
            AlgorithmExecutionError: If algorithm fails to execute
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # 1. Load deployment and algorithm
            deployment = await self._load_deployment(deployment_id)
            if not deployment.is_active:
                raise AlgorithmExecutionError(
                    f"Deployment {deployment_id} is not active"
                )
            
            algorithm = await self._load_algorithm(deployment.algorithm_id)
            
            # 2. Load algorithm model/logic
            algo_model = await self._load_algorithm_model(algorithm)
            
            # 3. Fetch real-time market data
            market_data = await self._fetch_market_data(deployment.user_id)
            
            # 4. Generate trading signals
            signals = await self._generate_signals(
                algo_model,
                market_data,
                deployment,
            )
            
            # 5. Execute signals (if not dry run)
            orders_submitted = 0
            errors = []
            
            if not dry_run:
                for signal in signals:
                    try:
                        if signal["action"] in ["buy", "sell"]:
                            await self._execute_signal(signal, deployment)
                            orders_submitted += 1
                    except Exception as e:
                        error_msg = f"Failed to execute signal {signal}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
            
            # 6. Update deployment last_executed_at
            deployment.last_executed_at = datetime.now(timezone.utc)
            self.db.add(deployment)
            self.db.commit()
            
            # 7. Calculate execution time
            end_time = datetime.now(timezone.utc)
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            result = {
                "deployment_id": str(deployment_id),
                "signals": signals,
                "orders_submitted": orders_submitted,
                "errors": errors,
                "execution_time_ms": execution_time_ms,
                "dry_run": dry_run,
            }
            
            logger.info(
                f"Algorithm execution complete: deployment={deployment_id}, "
                f"signals={len(signals)}, orders={orders_submitted}, "
                f"time={execution_time_ms:.2f}ms"
            )
            
            return result
            
        except Exception as e:
            logger.exception(f"Algorithm execution failed: {str(e)}")
            raise AlgorithmExecutionError(f"Execution failed: {str(e)}") from e
    
    async def _load_deployment(self, deployment_id: UUID) -> DeployedAlgorithm:
        """Load deployment from database"""
        statement = select(DeployedAlgorithm).where(DeployedAlgorithm.id == deployment_id)
        deployment = self.db.exec(statement).first()
        
        if not deployment:
            raise AlgorithmExecutionError(f"Deployment {deployment_id} not found")
        
        return deployment
    
    async def _load_algorithm(self, algorithm_id: UUID) -> Algorithm:
        """Load algorithm from database"""
        statement = select(Algorithm).where(Algorithm.id == algorithm_id)
        algorithm = self.db.exec(statement).first()
        
        if not algorithm:
            raise AlgorithmExecutionError(f"Algorithm {algorithm_id} not found")
        
        if algorithm.status not in ["active", "draft"]:
            raise AlgorithmExecutionError(
                f"Algorithm {algorithm_id} has invalid status: {algorithm.status}"
            )
        
        return algorithm
    
    async def _load_algorithm_model(self, algorithm: Algorithm) -> Any:
        """
        Load and deserialize algorithm model
        
        For ML-based algorithms (linked to AgentArtifacts), this loads the
        pickled model. For rule-based algorithms, this returns the algorithm
        configuration.
        
        Returns:
            The loaded model or configuration dict
        """
        # Check cache first
        if algorithm.id in self._loaded_algorithms:
            return self._loaded_algorithms[algorithm.id]
        
        if algorithm.artifact_id:
            # Load from AgentArtifact
            statement = select(AgentArtifact).where(AgentArtifact.id == algorithm.artifact_id)
            artifact = self.db.exec(statement).first()
            
            if not artifact:
                raise AlgorithmExecutionError(
                    f"Artifact {algorithm.artifact_id} not found for algorithm {algorithm.id}"
                )
            
            if artifact.artifact_type != "model":
                raise AlgorithmExecutionError(
                    f"Artifact {artifact.id} is not a model (type: {artifact.artifact_type})"
                )
            
            # Load pickled model from file
            if not artifact.file_path:
                raise AlgorithmExecutionError(
                    f"Artifact {artifact.id} has no file_path"
                )
            
            model_path = Path(artifact.file_path)
            if not model_path.exists():
                raise AlgorithmExecutionError(
                    f"Model file not found: {artifact.file_path}"
                )
            
            with open(model_path, "rb") as f:
                model = pickle.load(f)
            
            logger.info(f"Loaded model from artifact {artifact.id}: {model_path}")
            
        else:
            # Rule-based algorithm - use configuration
            if algorithm.configuration_json:
                model = json.loads(algorithm.configuration_json)
            else:
                model = {}
            
            logger.info(f"Using rule-based algorithm configuration for {algorithm.id}")
        
        # Cache the model
        self._loaded_algorithms[algorithm.id] = model
        
        return model
    
    async def _fetch_market_data(self, user_id: UUID) -> dict[str, Any]:
        """
        Fetch real-time market data for algorithm input
        
        Returns latest price data for all available coins
        """
        # Get latest price data (last 5 minutes)
        statement = (
            select(PriceData5Min)
            .order_by(PriceData5Min.timestamp.desc())
            .limit(100)
        )
        prices = self.db.exec(statement).all()
        
        # Organize by coin_type
        market_data = {}
        for price in prices:
            if price.coin_type not in market_data:
                market_data[price.coin_type] = {
                    "coin": price.coin_type,
                    "last": float(price.last),
                    "bid": float(price.bid),
                    "ask": float(price.ask),
                    "timestamp": price.timestamp.isoformat(),
                }
        
        return market_data
    
    async def _generate_signals(
        self,
        model: Any,
        market_data: dict[str, Any],
        deployment: DeployedAlgorithm,
    ) -> list[dict[str, Any]]:
        """
        Generate trading signals using the algorithm
        
        Args:
            model: The loaded algorithm model or configuration
            market_data: Current market data
            deployment: Deployment configuration
            
        Returns:
            List of signals: [{"action": "buy"|"sell"|"hold", "coin": str, "quantity": Decimal, "confidence": float}]
        """
        signals = []
        
        # Parse deployment parameters
        params = {}
        if deployment.parameters_json:
            params = json.loads(deployment.parameters_json)
        
        # For ML models with predict() method
        if hasattr(model, "predict"):
            # Feature extraction from market data would go here
            # For now, return empty signals - actual ML integration in Phase 3 completion
            logger.warning("ML model prediction not yet implemented - skipping signal generation")
            return signals
        
        # For rule-based strategies (configuration dict)
        elif isinstance(model, dict):
            strategy_type = model.get("strategy_type", "simple_ma")
            
            if strategy_type == "simple_ma":
                # Simple moving average crossover strategy
                for coin, data in market_data.items():
                    # Simplified logic - buy if price is rising
                    # In production, this would calculate actual moving averages
                    signals.append({
                        "action": "hold",  # Conservative default
                        "coin": coin,
                        "quantity": Decimal("0"),
                        "confidence": 0.5,
                        "reason": "Simple MA strategy (placeholder)",
                    })
            
            else:
                logger.warning(f"Unknown strategy type: {strategy_type}")
        
        else:
            logger.warning(f"Unknown model type: {type(model)}")
        
        return signals
    
    async def _execute_signal(
        self,
        signal: dict[str, Any],
        deployment: DeployedAlgorithm,
    ) -> None:
        """
        Execute a trading signal by submitting an order
        
        Args:
            signal: Trading signal with action, coin, quantity, etc.
            deployment: Deployment configuration
            
        Raises:
            AlgorithmExecutionError: If signal execution fails
        """
        action = signal["action"]
        coin = signal["coin"]
        quantity = Decimal(str(signal["quantity"]))
        
        if action == "hold" or quantity == 0:
            return  # No trade needed
        
        # Create order
        order = OrderCreate(
            coin_type=coin,
            side=action,
            order_type="market",
            quantity=quantity,
            algorithm_id=deployment.algorithm_id,
        )
        
        # Safety check
        is_safe, reason = await self.safety_manager.check_trade_safety(
            user_id=deployment.user_id,
            order=order,
            deployment=deployment,
        )
        
        if not is_safe:
            raise AlgorithmExecutionError(f"Trade rejected by safety check: {reason}")
        
        # Submit to order queue
        await self.order_queue.submit(
            user_id=deployment.user_id,
            order=order,
        )
        
        logger.info(
            f"Submitted order: {action} {quantity} {coin} for deployment {deployment.id}"
        )


# Global executor instance (optional)
_executor_instance: AlgorithmExecutor | None = None


def get_algorithm_executor(
    db_session: Session,
    safety_manager: SafetyManager | None = None,
) -> AlgorithmExecutor:
    """
    Get or create algorithm executor instance
    
    Args:
        db_session: Database session
        safety_manager: Optional safety manager
        
    Returns:
        AlgorithmExecutor instance
    """
    return AlgorithmExecutor(
        db_session=db_session,
        safety_manager=safety_manager,
    )
