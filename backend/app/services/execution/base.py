from abc import ABC, abstractmethod
from typing import List, Tuple
from datetime import datetime
from decimal import Decimal

from .schemas import AlgoOrder

class ExecutionStrategy(ABC):
    def __init__(self, order: AlgoOrder):
        self.order = order
        
    @abstractmethod
    def generate_schedule(self) -> List[Tuple[datetime, Decimal]]:
        """
        Generates a schedule of child orders.
        Returns a list of (scheduled_time, quantity_to_execute).
        """
        pass
    
    def validate_parameters(self) -> bool:
        """
        Validates that the order parameters are sufficient for this strategy.
        """
        return True
