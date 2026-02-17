# mypy: ignore-errors
"""
Override mechanism for Human-in-the-Loop workflow.

This module allows users to override agent decisions at key points,
providing flexibility while maintaining the benefits of automation.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class OverrideManager:
    """
    Manages user overrides in the agentic workflow.
    
    Allows users to:
    - Override model selection
    - Override hyperparameters
    - Override data preprocessing steps
    - Restart from specific workflow steps
    """

    def __init__(self):
        """Initialize the override manager."""
        self.valid_override_types = [
            "model_selection",
            "hyperparameters",
            "data_preprocessing",
            "workflow_step",
        ]

    def apply_override(
        self,
        state: dict[str, Any],
        override_type: str,
        override_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Apply a user override to the workflow state.
        
        Args:
            state: Current workflow state
            override_type: Type of override being applied
            override_data: Override parameters
            
        Returns:
            Updated state with override applied
            
        Raises:
            ValueError: If override_type is invalid or override_data is malformed
        """
        logger.info(f"OverrideManager: Applying {override_type} override")

        # Validate override type
        if override_type not in self.valid_override_types:
            raise ValueError(
                f"Invalid override type: {override_type}. "
                f"Must be one of {self.valid_override_types}"
            )

        # Validate override data
        validation_error = self._validate_override(override_type, override_data, state)
        if validation_error:
            raise ValueError(f"Invalid override data: {validation_error}")

        # Apply the override based on type
        if override_type == "model_selection":
            state = self._apply_model_selection_override(state, override_data)
        elif override_type == "hyperparameters":
            state = self._apply_hyperparameters_override(state, override_data)
        elif override_type == "data_preprocessing":
            state = self._apply_preprocessing_override(state, override_data)
        elif override_type == "workflow_step":
            state = self._apply_workflow_step_override(state, override_data)

        # Record the override
        if "overrides_applied" not in state:
            state["overrides_applied"] = []

        state["overrides_applied"].append({
            "override_type": override_type,
            "override_data": override_data,
            "timestamp": None,  # Will be set by API
        })

        # Add to reasoning trace
        if "reasoning_trace" not in state or state["reasoning_trace"] is None:
            state["reasoning_trace"] = []

        state["reasoning_trace"].append({
            "step": "override_applied",
            "override_type": override_type,
            "override_data": override_data
        })

        logger.info(f"OverrideManager: Successfully applied {override_type} override")

        return state

    def _validate_override(
        self,
        override_type: str,
        override_data: dict[str, Any],
        state: dict[str, Any]
    ) -> str | None:
        """
        Validate override data based on type.
        
        Args:
            override_type: Type of override
            override_data: Override parameters
            state: Current workflow state
            
        Returns:
            Error message if validation fails, None otherwise
        """
        if override_type == "model_selection":
            model_name = override_data.get("model_name")
            if not model_name:
                return "model_name is required"

            # Check if model exists in trained models
            trained_models = state.get("trained_models", {})
            if model_name not in trained_models:
                available = list(trained_models.keys())
                return f"Model {model_name} not found. Available: {available}"

        elif override_type == "hyperparameters":
            model_name = override_data.get("model_name")
            hyperparameters = override_data.get("hyperparameters")

            if not model_name:
                return "model_name is required"
            if not hyperparameters or not isinstance(hyperparameters, dict):
                return "hyperparameters must be a dictionary"

            # Validate hyperparameter values are safe
            for key, value in hyperparameters.items():
                if not isinstance(value, (int, float, str, bool)):
                    return f"Hyperparameter {key} has invalid type {type(value)}"

        elif override_type == "data_preprocessing":
            steps = override_data.get("preprocessing_steps")
            if not steps or not isinstance(steps, list):
                return "preprocessing_steps must be a list"

        elif override_type == "workflow_step":
            step = override_data.get("restart_step")
            valid_steps = [
                "data_retrieval",
                "data_analysis",
                "model_training",
                "model_evaluation",
            ]
            if step not in valid_steps:
                return f"restart_step must be one of {valid_steps}"

        return None

    def _apply_model_selection_override(
        self,
        state: dict[str, Any],
        override_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply model selection override."""
        model_name = override_data["model_name"]

        state["selected_choice"] = model_name
        state["awaiting_choice"] = False
        state["current_step"] = "model_selected"

        logger.info(f"OverrideManager: Selected model {model_name}")

        return state

    def _apply_hyperparameters_override(
        self,
        state: dict[str, Any],
        override_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply hyperparameters override."""
        model_name = override_data["model_name"]
        hyperparameters = override_data["hyperparameters"]

        # Update training parameters
        if "training_params" not in state:
            state["training_params"] = {}

        if "model_hyperparameters" not in state["training_params"]:
            state["training_params"]["model_hyperparameters"] = {}

        state["training_params"]["model_hyperparameters"][model_name] = hyperparameters

        # Flag that model needs retraining
        state["model_trained"] = False
        state["current_step"] = "model_training"

        logger.info(f"OverrideManager: Updated hyperparameters for {model_name}")

        return state

    def _apply_preprocessing_override(
        self,
        state: dict[str, Any],
        override_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply data preprocessing override."""
        preprocessing_steps = override_data["preprocessing_steps"]

        # Update analysis parameters
        if "analysis_params" not in state:
            state["analysis_params"] = {}

        state["analysis_params"]["preprocessing_steps"] = preprocessing_steps

        # Flag that analysis needs to be redone
        state["analysis_completed"] = False
        state["current_step"] = "data_analysis"

        logger.info("OverrideManager: Updated preprocessing steps")

        return state

    def _apply_workflow_step_override(
        self,
        state: dict[str, Any],
        override_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply workflow step restart override."""
        restart_step = override_data["restart_step"]

        # Reset state for the specified step
        state["current_step"] = restart_step

        # Reset relevant flags based on step
        if restart_step == "data_retrieval":
            state["data_retrieved"] = False
            state["analysis_completed"] = False
            state["model_trained"] = False
            state["model_evaluated"] = False
        elif restart_step == "data_analysis":
            state["analysis_completed"] = False
            state["model_trained"] = False
            state["model_evaluated"] = False
        elif restart_step == "model_training":
            state["model_trained"] = False
            state["model_evaluated"] = False
        elif restart_step == "model_evaluation":
            state["model_evaluated"] = False

        logger.info(f"OverrideManager: Restarting from step {restart_step}")

        return state

    def get_available_override_points(self, state: dict[str, Any]) -> dict[str, bool]:
        """
        Get available override points based on current state.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary of override points and their availability
        """
        override_points = {
            "model_selection": False,
            "hyperparameters": False,
            "data_preprocessing": False,
            "workflow_restart": False,
        }

        # Model selection available if models have been trained
        if state.get("trained_models") and state.get("evaluation_results"):
            override_points["model_selection"] = True

        # Hyperparameters always available if models exist
        if state.get("trained_models"):
            override_points["hyperparameters"] = True

        # Data preprocessing available if data has been retrieved
        if state.get("retrieved_data"):
            override_points["data_preprocessing"] = True

        # Workflow restart always available if workflow has started
        if state.get("current_step") != "initialized":
            override_points["workflow_restart"] = True

        return override_points


# Global override manager instance
override_manager = OverrideManager()


def apply_user_override(
    state: dict[str, Any],
    override_type: str,
    override_data: dict[str, Any]
) -> dict[str, Any]:
    """
    Convenience function to apply a user override.
    
    Args:
        state: Current workflow state
        override_type: Type of override
        override_data: Override parameters
        
    Returns:
        Updated state with override applied
    """
    return override_manager.apply_override(state, override_type, override_data)


def get_override_points(state: dict[str, Any]) -> dict[str, bool]:
    """
    Convenience function to get available override points.
    
    Args:
        state: Current workflow state
        
    Returns:
        Dictionary of available override points
    """
    return override_manager.get_available_override_points(state)
