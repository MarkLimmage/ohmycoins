"""
Base Agent class for all specialized agents.

This provides common functionality for all agent types.
"""

from typing import Any


class BaseAgent:
    """
    Base class for all specialized agents in the system.

    Each agent has a specific responsibility in the data science workflow.
    """

    def __init__(self, name: str, description: str) -> None:
        """
        Initialize the base agent.

        Args:
            name: Agent name
            description: Agent description
        """
        self.name = name
        self.description = description

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the agent's primary function.

        Args:
            state: Current workflow state

        Returns:
            Updated state after agent execution
        """
        raise NotImplementedError("Subclasses must implement execute method")
