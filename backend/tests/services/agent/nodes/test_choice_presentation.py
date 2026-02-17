"""Tests for choice presentation node."""

from app.services.agent.nodes.choice_presentation import (
    _estimate_model_complexity,
    _generate_model_choices,
    _generate_pros_cons,
    choice_presentation_node,
    handle_choice_selection,
)


class TestChoicePresentationNode:
    """Tests for choice_presentation_node function."""

    def test_choice_presentation_with_multiple_models(self):
        """Test that choice node presents multiple models."""
        state = {
            "trained_models": {
                "random_forest": {"type": "RandomForest", "parameters": {}},
                "logistic_regression": {"type": "LogisticRegression", "parameters": {}}
            },
            "evaluation_results": {
                "random_forest": {"accuracy": 0.85, "training_time": 10.0},
                "logistic_regression": {"accuracy": 0.82, "training_time": 2.0}
            }
        }

        result = choice_presentation_node(state)

        assert result["awaiting_choice"] is True
        assert len(result["choices_available"]) == 2
        assert "recommendation" in result

    def test_choice_presentation_with_single_model(self):
        """Test that single model is auto-selected."""
        state = {
            "trained_models": {
                "random_forest": {"type": "RandomForest", "parameters": {}}
            },
            "evaluation_results": {
                "random_forest": {"accuracy": 0.85, "training_time": 10.0}
            }
        }

        result = choice_presentation_node(state)

        assert result["awaiting_choice"] is False
        assert result.get("selected_choice") == "random_forest"

    def test_choice_presentation_with_no_models(self):
        """Test that no models results in no choice needed."""
        state = {
            "trained_models": {},
            "evaluation_results": {}
        }

        result = choice_presentation_node(state)

        assert result["awaiting_choice"] is False


class TestGenerateModelChoices:
    """Tests for _generate_model_choices helper function."""

    def test_generates_choices_for_all_models(self):
        """Test that choices are generated for all trained models."""
        trained_models = {
            "model1": {"type": "RandomForest", "parameters": {}},
            "model2": {"type": "LogisticRegression", "parameters": {}}
        }
        evaluation_results = {
            "model1": {"accuracy": 0.85, "training_time": 10.0},
            "model2": {"accuracy": 0.80, "training_time": 2.0}
        }

        choices = _generate_model_choices(trained_models, evaluation_results)

        assert len(choices) == 2
        assert all("model_name" in c for c in choices)
        assert all("pros" in c for c in choices)
        assert all("cons" in c for c in choices)

    def test_sorts_choices_by_accuracy(self):
        """Test that choices are sorted by accuracy descending."""
        trained_models = {
            "low_acc": {"type": "Model1", "parameters": {}},
            "high_acc": {"type": "Model2", "parameters": {}}
        }
        evaluation_results = {
            "low_acc": {"accuracy": 0.70, "training_time": 5.0},
            "high_acc": {"accuracy": 0.90, "training_time": 15.0}
        }

        choices = _generate_model_choices(trained_models, evaluation_results)

        assert choices[0]["model_name"] == "high_acc"
        assert choices[1]["model_name"] == "low_acc"

    def test_includes_complexity_estimate(self):
        """Test that complexity is estimated for each model."""
        trained_models = {
            "model1": {"type": "RandomForest", "parameters": {}}
        }
        evaluation_results = {
            "model1": {"accuracy": 0.85, "training_time": 10.0}
        }

        choices = _generate_model_choices(trained_models, evaluation_results)

        assert "complexity" in choices[0]
        assert choices[0]["complexity"] in ["low", "medium", "high"]


class TestEstimateModelComplexity:
    """Tests for _estimate_model_complexity helper function."""

    def test_logistic_regression_is_low(self):
        """Test that logistic regression is classified as low complexity."""
        assert _estimate_model_complexity("logistic_regression") == "low"

    def test_linear_model_is_low(self):
        """Test that linear models are classified as low complexity."""
        assert _estimate_model_complexity("linear_regression") == "low"

    def test_random_forest_is_medium(self):
        """Test that random forest is classified as medium complexity."""
        assert _estimate_model_complexity("random_forest") == "medium"

    def test_svm_is_medium(self):
        """Test that SVM is classified as medium complexity."""
        assert _estimate_model_complexity("svm_classifier") == "medium"

    def test_xgboost_is_high(self):
        """Test that XGBoost is classified as high complexity."""
        assert _estimate_model_complexity("xgboost_model") == "high"

    def test_neural_net_is_high(self):
        """Test that neural networks are classified as high complexity."""
        assert _estimate_model_complexity("neural_network") == "high"

    def test_unknown_model_is_medium(self):
        """Test that unknown models default to medium complexity."""
        assert _estimate_model_complexity("unknown_model") == "medium"


class TestGenerateProsCons:
    """Tests for _generate_pros_cons helper function."""

    def test_high_accuracy_generates_pro(self):
        """Test that high accuracy generates a pro."""
        pros, cons = _generate_pros_cons("model1", {"accuracy": 0.90, "training_time": 10.0})

        assert any("high accuracy" in p.lower() for p in pros)

    def test_low_accuracy_generates_con(self):
        """Test that low accuracy generates a con."""
        pros, cons = _generate_pros_cons("model1", {"accuracy": 0.65, "training_time": 10.0})

        assert any("accuracy" in c.lower() for c in cons)

    def test_fast_training_generates_pro(self):
        """Test that fast training generates a pro."""
        pros, cons = _generate_pros_cons("model1", {"accuracy": 0.80, "training_time": 3.0})

        assert any("fast" in p.lower() for p in pros)

    def test_slow_training_generates_con(self):
        """Test that slow training generates a con."""
        pros, cons = _generate_pros_cons("model1", {"accuracy": 0.80, "training_time": 50.0})

        assert any("slow" in c.lower() or "training" in c.lower() for c in cons)

    def test_logistic_regression_characteristics(self):
        """Test that logistic regression has expected pros/cons."""
        pros, cons = _generate_pros_cons("logistic_regression", {"accuracy": 0.80, "training_time": 5.0})

        assert any("simple" in p.lower() or "interpretable" in p.lower() for p in pros)
        assert any("limited" in c.lower() or "complex" in c.lower() for c in cons)

    def test_random_forest_characteristics(self):
        """Test that random forest has expected pros/cons."""
        pros, cons = _generate_pros_cons("random_forest", {"accuracy": 0.85, "training_time": 15.0})

        assert any("non-linear" in p.lower() or "feature importance" in p.lower() for p in pros)

    def test_xgboost_characteristics(self):
        """Test that XGBoost has expected pros/cons."""
        pros, cons = _generate_pros_cons("xgboost", {"accuracy": 0.88, "training_time": 25.0})

        assert any("state-of-the-art" in p.lower() or "performance" in p.lower() for p in pros)
        assert any("tuning" in c.lower() or "training time" in c.lower() for c in cons)


class TestHandleChoiceSelection:
    """Tests for handle_choice_selection function."""

    def test_records_selected_choice(self):
        """Test that selected choice is recorded in state."""
        state = {
            "awaiting_choice": True,
            "choices_available": [
                {"model_name": "model1"},
                {"model_name": "model2"}
            ]
        }

        result = handle_choice_selection(state, "model1")

        assert result["selected_choice"] == "model1"
        assert result["awaiting_choice"] is False

    def test_updates_reasoning_trace(self):
        """Test that choice is recorded in reasoning trace."""
        state = {
            "awaiting_choice": True,
            "reasoning_trace": []
        }

        result = handle_choice_selection(state, "model1")

        assert "reasoning_trace" in result
        assert len(result["reasoning_trace"]) > 0
        assert result["reasoning_trace"][-1]["step"] == "choice_selected"
        assert result["reasoning_trace"][-1]["selected_model"] == "model1"

    def test_clears_choices_available(self):
        """Test that choices are cleared after selection."""
        state = {
            "awaiting_choice": True,
            "choices_available": [{"model_name": "model1"}]
        }

        result = handle_choice_selection(state, "model1")

        assert result["choices_available"] == []
