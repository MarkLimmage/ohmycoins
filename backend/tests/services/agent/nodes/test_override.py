"""Tests for override mechanism."""

import pytest

from app.services.agent.override import (
    OverrideManager,
    apply_user_override,
    get_override_points,
)


class TestOverrideManager:
    """Tests for OverrideManager class."""

    def test_model_selection_override(self):
        """Test that model selection override works."""
        manager = OverrideManager()
        state = {
            "trained_models": {
                "model1": {},
                "model2": {}
            },
            "selected_choice": "model1"
        }

        override_data = {"model_name": "model2"}
        result = manager.apply_override(state, "model_selection", override_data)

        assert result["selected_choice"] == "model2"
        assert result["awaiting_choice"] is False
        assert len(result["overrides_applied"]) == 1

    def test_hyperparameters_override(self):
        """Test that hyperparameters override works."""
        manager = OverrideManager()
        state = {
            "trained_models": {"model1": {}},
            "training_params": {}
        }

        override_data = {
            "model_name": "model1",
            "hyperparameters": {"n_estimators": 200, "max_depth": 10}
        }
        result = manager.apply_override(state, "hyperparameters", override_data)

        assert "model_hyperparameters" in result["training_params"]
        assert result["training_params"]["model_hyperparameters"]["model1"]["n_estimators"] == 200
        assert result["model_trained"] is False  # Needs retraining

    def test_preprocessing_override(self):
        """Test that preprocessing override works."""
        manager = OverrideManager()
        state = {
            "analysis_params": {},
            "analysis_completed": True
        }

        override_data = {
            "preprocessing_steps": ["normalize", "remove_outliers"]
        }
        result = manager.apply_override(state, "data_preprocessing", override_data)

        assert result["analysis_params"]["preprocessing_steps"] == ["normalize", "remove_outliers"]
        assert result["analysis_completed"] is False  # Needs reanalysis

    def test_workflow_step_override(self):
        """Test that workflow step restart works."""
        manager = OverrideManager()
        state = {
            "current_step": "model_evaluation",
            "data_retrieved": True,
            "analysis_completed": True,
            "model_trained": True,
            "model_evaluated": True
        }

        override_data = {"restart_step": "model_training"}
        result = manager.apply_override(state, "workflow_step", override_data)

        assert result["current_step"] == "model_training"
        assert result["model_trained"] is False
        assert result["model_evaluated"] is False
        assert result["analysis_completed"] is True  # Should remain true

    def test_invalid_override_type(self):
        """Test that invalid override type raises error."""
        manager = OverrideManager()
        state = {}

        with pytest.raises(ValueError, match="Invalid override type"):
            manager.apply_override(state, "invalid_type", {})

    def test_validation_model_not_found(self):
        """Test that validation fails for non-existent model."""
        manager = OverrideManager()
        state = {
            "trained_models": {"model1": {}}
        }

        override_data = {"model_name": "model2"}

        with pytest.raises(ValueError, match="Model model2 not found"):
            manager.apply_override(state, "model_selection", override_data)

    def test_validation_missing_model_name(self):
        """Test that validation fails without model_name."""
        manager = OverrideManager()
        state = {}

        with pytest.raises(ValueError, match="model_name is required"):
            manager.apply_override(state, "model_selection", {})

    def test_validation_invalid_hyperparameters(self):
        """Test that validation fails for invalid hyperparameters."""
        manager = OverrideManager()
        state = {"trained_models": {"model1": {}}}

        override_data = {
            "model_name": "model1",
            "hyperparameters": "invalid"  # Should be dict
        }

        with pytest.raises(ValueError, match="must be a dictionary"):
            manager.apply_override(state, "hyperparameters", override_data)

    def test_validation_invalid_preprocessing_steps(self):
        """Test that validation fails for invalid preprocessing steps."""
        manager = OverrideManager()
        state = {}

        override_data = {"preprocessing_steps": "invalid"}  # Should be list

        with pytest.raises(ValueError, match="must be a list"):
            manager.apply_override(state, "data_preprocessing", override_data)

    def test_validation_invalid_restart_step(self):
        """Test that validation fails for invalid restart step."""
        manager = OverrideManager()
        state = {}

        override_data = {"restart_step": "invalid_step"}

        with pytest.raises(ValueError, match="must be one of"):
            manager.apply_override(state, "workflow_step", override_data)

    def test_updates_reasoning_trace(self):
        """Test that override is recorded in reasoning trace."""
        manager = OverrideManager()
        state = {
            "trained_models": {"model1": {}},
            "reasoning_trace": []
        }

        override_data = {"model_name": "model1"}
        result = manager.apply_override(state, "model_selection", override_data)

        assert len(result["reasoning_trace"]) > 0
        assert result["reasoning_trace"][-1]["step"] == "override_applied"


class TestGetAvailableOverridePoints:
    """Tests for get_available_override_points method."""

    def test_model_selection_available_with_models(self):
        """Test that model selection is available when models exist."""
        manager = OverrideManager()
        state = {
            "trained_models": {"model1": {}},
            "evaluation_results": {"model1": {}}
        }

        points = manager.get_available_override_points(state)

        assert points["model_selection"] is True

    def test_model_selection_unavailable_without_models(self):
        """Test that model selection is unavailable without models."""
        manager = OverrideManager()
        state = {}

        points = manager.get_available_override_points(state)

        assert points["model_selection"] is False

    def test_hyperparameters_available_with_models(self):
        """Test that hyperparameters override is available with models."""
        manager = OverrideManager()
        state = {"trained_models": {"model1": {}}}

        points = manager.get_available_override_points(state)

        assert points["hyperparameters"] is True

    def test_preprocessing_available_with_data(self):
        """Test that preprocessing override is available with data."""
        manager = OverrideManager()
        state = {"retrieved_data": {"price_data": []}}

        points = manager.get_available_override_points(state)

        assert points["data_preprocessing"] is True

    def test_workflow_restart_available_after_start(self):
        """Test that workflow restart is available after workflow starts."""
        manager = OverrideManager()
        state = {"current_step": "data_analysis"}

        points = manager.get_available_override_points(state)

        assert points["workflow_restart"] is True

    def test_all_unavailable_at_init(self):
        """Test that all overrides are unavailable at initialization."""
        manager = OverrideManager()
        state = {"current_step": "initialized"}

        points = manager.get_available_override_points(state)

        assert points["model_selection"] is False
        assert points["hyperparameters"] is False
        assert points["data_preprocessing"] is False
        assert points["workflow_restart"] is False


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_apply_user_override(self):
        """Test that apply_user_override convenience function works."""
        state = {
            "trained_models": {"model1": {}, "model2": {}},
            "selected_choice": "model1"
        }

        override_data = {"model_name": "model2"}
        result = apply_user_override(state, "model_selection", override_data)

        assert result["selected_choice"] == "model2"

    def test_get_override_points(self):
        """Test that get_override_points convenience function works."""
        state = {
            "trained_models": {"model1": {}},
            "evaluation_results": {"model1": {}}
        }

        points = get_override_points(state)

        assert points["model_selection"] is True
