"""Tests for Optuna hyperparameter search tool."""
import pandas as pd
import pytest
from sklearn.datasets import make_classification, make_regression

from app.services.agent.tools.hyperparameter_search import hyperparameter_search


class TestHyperparameterSearch:
    """Test hyperparameter_search function."""

    @pytest.fixture
    def classification_data(self) -> pd.DataFrame:
        """Create a classification dataset."""
        X, y = make_classification(
            n_samples=100,
            n_features=10,
            n_informative=5,
            random_state=42,
        )
        df = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(10)])
        df["target"] = y
        return df

    @pytest.fixture
    def regression_data(self) -> pd.DataFrame:
        """Create a regression dataset."""
        X, y = make_regression(
            n_samples=100,
            n_features=10,
            n_informative=5,
            random_state=42,
        )
        df = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(10)])
        df["target"] = y
        return df

    def test_random_forest_classification(self, classification_data: pd.DataFrame) -> None:
        """Test hyperparameter search with Random Forest classifier."""
        result = hyperparameter_search(
            training_data=classification_data,
            target_column="target",
            model_type="random_forest",
            task_type="classification",
            n_trials=5,
            cv_folds=3,
        )

        # Verify result structure
        assert "best_params" in result
        assert "best_score" in result
        assert "n_trials" in result
        assert "model_type" in result
        assert "task_type" in result
        assert "scoring" in result

        # Verify values
        assert result["model_type"] == "random_forest"
        assert result["task_type"] == "classification"
        assert result["n_trials"] == 5
        assert result["scoring"] == "accuracy"
        assert isinstance(result["best_score"], float)
        assert 0 <= result["best_score"] <= 1

        # Verify best_params has expected hyperparameters
        assert "n_estimators" in result["best_params"]
        assert "max_depth" in result["best_params"]

    def test_gradient_boosting_classification(self, classification_data: pd.DataFrame) -> None:
        """Test hyperparameter search with Gradient Boosting classifier."""
        result = hyperparameter_search(
            training_data=classification_data,
            target_column="target",
            model_type="gradient_boosting",
            task_type="classification",
            n_trials=5,
            cv_folds=3,
        )

        # Verify result structure
        assert result["model_type"] == "gradient_boosting"
        assert result["task_type"] == "classification"
        assert result["scoring"] == "accuracy"

        # Verify hyperparameters
        assert "learning_rate" in result["best_params"]
        assert "n_estimators" in result["best_params"]

    def test_random_forest_regression(self, regression_data: pd.DataFrame) -> None:
        """Test hyperparameter search with Random Forest regressor."""
        result = hyperparameter_search(
            training_data=regression_data,
            target_column="target",
            model_type="random_forest",
            task_type="regression",
            n_trials=5,
            cv_folds=3,
        )

        # Verify result structure
        assert result["model_type"] == "random_forest"
        assert result["task_type"] == "regression"
        assert result["n_trials"] == 5
        assert result["scoring"] == "neg_mean_squared_error"
        assert isinstance(result["best_score"], float)

    def test_gradient_boosting_regression(self, regression_data: pd.DataFrame) -> None:
        """Test hyperparameter search with Gradient Boosting regressor."""
        result = hyperparameter_search(
            training_data=regression_data,
            target_column="target",
            model_type="gradient_boosting",
            task_type="regression",
            n_trials=5,
            cv_folds=3,
        )

        # Verify result structure
        assert result["model_type"] == "gradient_boosting"
        assert result["task_type"] == "regression"
        assert result["scoring"] == "neg_mean_squared_error"

        # Verify gradient boosting specific params
        assert "learning_rate" in result["best_params"]

    def test_invalid_model_type(self, classification_data: pd.DataFrame) -> None:
        """Test that invalid model_type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown model_type"):
            hyperparameter_search(
                training_data=classification_data,
                target_column="target",
                model_type="invalid_model",
                task_type="classification",
                n_trials=2,
            )

    def test_custom_trial_count(self, regression_data: pd.DataFrame) -> None:
        """Test with custom n_trials."""
        result = hyperparameter_search(
            training_data=regression_data,
            target_column="target",
            model_type="random_forest",
            task_type="regression",
            n_trials=3,
            cv_folds=2,
        )

        assert result["n_trials"] == 3
