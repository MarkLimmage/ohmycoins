from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel

class ICollector(ABC):
    """
    Abstract Base Class for all data collectors.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of the collector strategy."""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """A brief description of what this collector does."""
        pass
        
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """
        Returns the JSON schema for the configuration parameters required by this collector.
        This is used to generate the UI form.
        """
        pass
        
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validates the provided configuration against the schema.
        """
        pass
    
    @abstractmethod
    async def test_connection(self, config: Dict[str, Any]) -> bool:
        """
        Tests connectivity to the data source using the provided config.
        """
        pass
        
    @abstractmethod
    async def collect(self, config: Dict[str, Any]) -> List[Any]:
        """
        Executes the data collection logic.
        Returns a list of standardized data objects (Signal, NewsItem, etc).
        """
        pass
