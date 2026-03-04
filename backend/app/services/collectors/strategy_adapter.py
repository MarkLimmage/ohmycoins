import logging
from typing import Any

from sqlalchemy.exc import IntegrityError
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
        for item in data:
            if not hasattr(item, "id"):
                logger.warning(
                    f"Item {item} is not a valid model instance, skipping storage."
                )
                continue

            try:
                nested = session.begin_nested()
                session.add(item)
                session.flush()
                count += 1
            except IntegrityError:
                nested.rollback()
                logger.debug(
                    f"Duplicate item skipped for {self.strategy.name}: "
                    f"{getattr(item, 'link', '?')}"
                )
            except Exception as e:
                nested.rollback()
                logger.error(f"Failed to store item for {self.strategy.name}: {e}")

        return count
