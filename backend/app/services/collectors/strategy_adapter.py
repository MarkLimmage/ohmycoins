import logging
from typing import Any

from sqlmodel import Session

from app.core.collectors.base import ICollector
from app.services.collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class StrategyAdapterCollector(BaseCollector):
    """
    Adapter to run ICollector strategies within the BaseCollector orchestration framework.
    """

    def __init__(
        self,
        strategy: ICollector,
        ledger_name: str,
        default_config: dict[str, Any] | None = None,
    ):
        super().__init__(name=strategy.name, ledger=ledger_name)
        self.strategy = strategy
        self.default_config = default_config or {}

    async def collect(self) -> list[Any]:
        logger.info(f"Running strategy: {self.strategy.name}")
        # In a real impl, config would come from DB dynamically
        # For now, use default_config passed during initialization
        return await self.strategy.collect(self.default_config)

    async def validate_data(self, data: list[Any]) -> list[Any]:
        # Basic validation
        if not isinstance(data, list):
            logger.warning(
                f"Strategy {self.strategy.name} returned non-list data: {type(data)}"
            )
            return []
        return data

    async def store_data(self, data: list[Any], session: Session) -> int:
        if not data:
            return 0

        count = 0
        try:
            for item in data:
                # Check if item is a SQLModel instance or compatible
                if hasattr(item, "id"):
                    session.add(item)
                    count += 1
                else:
                    logger.warning(
                        f"Item {item} is not a valid model instance, skipping storage."
                    )

            # We let the caller (BaseCollector.run) commit the transaction
            # along with the run status update.
            return count
        except Exception as e:
            logger.error(
                f"Failed to prepare data storage for {self.strategy.name}: {e}"
            )
            raise e
