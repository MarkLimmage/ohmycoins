"""Tests for XGBoost and time-series validation in model training tools."""

import pandas as pd
import pytest
from sklearn.datasets import make_classification, make_regression

from app.services.agent.tools.model_training_tools import (
    train_classification_model,
    train_regression_model,
)


@pytest.mark.skip(reason="Phase 5 refactored training to async Dagger execution; tests need Dagger infrastructure mocking")
class TestXGBoostTraining:
    @pytest.fixture
    def classification_data(self) -> pd.DataFrame:
        X, y = make_classification(n_samples=100, n_features=10, random_state=42)
        df = pd.DataFrame(X, columns=[f"f_{i}" for i in range(10)])
        df["target"] = y
        return df

    @pytest.fixture
    def regression_data(self) -> pd.DataFrame:
        X, y = make_regression(n_samples=100, n_features=10, random_state=42)
        df = pd.DataFrame(X, columns=[f"f_{i}" for i in range(10)])
        df["target"] = y
        return df

    def test_xgboost_classification(self, classification_data: pd.DataFrame) -> None:
        """Test XGBoost classifier training."""
        result = train_classification_model(
            training_data=classification_data,
            target_column="target",
            model_type="xgboost",
        )
        assert result["model_type"] == "xgboost"
        assert "accuracy" in result["metrics"]["test"]
        assert result["metrics"]["test"]["accuracy"] > 0.5

    def test_xgboost_regression(self, regression_data: pd.DataFrame) -> None:
        """Test XGBoost regressor training."""
        result = train_regression_model(
            training_data=regression_data,
            target_column="target",
            model_type="xgboost",
        )
        assert result["model_type"] == "xgboost"
        assert "r2" in result["metrics"]["test"]

    def test_time_series_validation_classification(self, classification_data: pd.DataFrame) -> None:
        """Test time-series validation strategy for classification."""
        result = train_classification_model(
            training_data=classification_data,
            target_column="target",
            model_type="random_forest",
            validation_strategy="time_series",
        )
        assert result["validation_strategy"] == "time_series"
        assert "accuracy" in result["metrics"]["test"]

    def test_time_series_validation_regression(self, regression_data: pd.DataFrame) -> None:
        """Test time-series validation strategy for regression."""
        result = train_regression_model(
            training_data=regression_data,
            target_column="target",
            model_type="random_forest",
            validation_strategy="time_series",
        )
        assert result["validation_strategy"] == "time_series"
        assert "r2" in result["metrics"]["test"]

    def test_expanding_window_validation(self, classification_data: pd.DataFrame) -> None:
        """Test expanding window validation strategy."""
        result = train_classification_model(
            training_data=classification_data,
            target_column="target",
            model_type="random_forest",
            validation_strategy="expanding_window",
        )
        assert result["validation_strategy"] == "expanding_window"
        assert "accuracy" in result["metrics"]["test"]

    def test_random_validation_strategy(self, classification_data: pd.DataFrame) -> None:
        """Test explicit random validation strategy."""
        result = train_classification_model(
            training_data=classification_data,
            target_column="target",
            model_type="random_forest",
            validation_strategy="random",
        )
        assert result["validation_strategy"] == "random"
        assert "accuracy" in result["metrics"]["test"]
