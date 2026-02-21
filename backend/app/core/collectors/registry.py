import importlib
import logging
import pkgutil

from app.core.collectors.base import ICollector


class CollectorRegistry:
    """
    Registry for discovering and managing data collection strategies.
    Implementations are auto-discovered from backend/app/collectors/strategies.
    """

    _strategies: dict[str, type[ICollector]] = {}

    @classmethod
    def register(cls, strategy_class: type[ICollector]) -> None:
        """Register a new collector strategy."""
        if not issubclass(strategy_class, ICollector):
            raise TypeError(
                f"Strategies must inherit from ICollector. Got {strategy_class}"
            )

        instance = strategy_class()
        if not instance.name:
            raise ValueError(
                f"Strategy {strategy_class.__name__} must have a 'name' property."
            )

        cls._strategies[instance.name] = strategy_class
        logging.info(f"Registered collector strategy: {instance.name}")

    @classmethod
    def get_strategy(cls, name: str) -> type[ICollector] | None:
        """Retrieve a specific strategy implementation by name."""
        return cls._strategies.get(name)

    @classmethod
    def list_strategies(cls) -> dict[str, type[ICollector]]:
        """List all available strategies."""
        return cls._strategies.copy()

    @classmethod
    def discover_strategies(
        cls, package_path: str = "app.collectors.strategies"
    ) -> None:
        """
        Dynamically imports all modules in the strategies package
        to trigger registration.
        """
        try:
            # Resolving relative to this file inside the container
            # Expected structure:
            # /app/backend/app/core/collectors/registry.py -> registry
            # /app/backend/app/collectors/strategies -> strategies folder

            # Using importlib to find the package path
            logging.error(f"Discovering strategies in: {package_path}")
            module = importlib.import_module(package_path)
            path = module.__path__
            logging.error(f"Package path: {path}")

            for _, name, _ in pkgutil.iter_modules(path):
                logging.error(f"Found module: {name}")
                # Import the module so the class definitions are executed
                importlib.import_module(f"{package_path}.{name}")

        except ImportError as e:
            logging.error(f"Failed to discover strategies in {package_path}: {e}")
            logging.error(f"ImportError: {e}")
        except Exception as e:
            logging.error(f"Error during strategy discovery: {e}")
            logging.error(f"Exception: {e}")

    @classmethod
    def get_strategy_instance(cls, name: str) -> ICollector | None:
        """Returns an instance of the requested strategy."""
        strategy_cls = cls.get_strategy(name)
        if strategy_cls:
            return strategy_cls()
        return None
