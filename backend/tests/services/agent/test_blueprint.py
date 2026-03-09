"""Tests for ModelBlueprint and related schemas."""
import pytest
from pydantic import ValidationError

from app.services.agent.schemas import FeatureImportance, ModelBlueprint, TrainingMetric


class TestModelBlueprint:
    """Test ModelBlueprint schema."""

    def test_model_blueprint_valid(self) -> None:
        """Test creating a valid ModelBlueprint."""
        blueprint = ModelBlueprint(
            target="BTC_price",
            features=["volume", "market_cap", "sentiment"],
            model_type="random_forest",
            task_type="regression",
            hyperparameters={"n_estimators": 100, "max_depth": 10},
            rationale="Predict BTC price using technical indicators",
            estimated_training_time="15 minutes",
        )
        assert blueprint.target == "BTC_price"
        assert len(blueprint.features) == 3
        assert blueprint.model_type == "random_forest"

    def test_model_blueprint_missing_required_field(self) -> None:
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            ModelBlueprint(
                target="BTC_price",
                features=["volume", "market_cap"],
                # Missing model_type, task_type, hyperparameters, rationale
            )

    def test_model_blueprint_optional_training_time(self) -> None:
        """Test that estimated_training_time is optional."""
        blueprint = ModelBlueprint(
            target="ETH_price",
            features=["volume"],
            model_type="gradient_boosting",
            task_type="classification",
            hyperparameters={},
            rationale="Test blueprint",
        )
        assert blueprint.estimated_training_time is None

    def test_model_blueprint_hyperparameters_are_flexible(self) -> None:
        """Test that hyperparameters dict is flexible."""
        blueprint = ModelBlueprint(
            target="SOL_price",
            features=["price", "volume"],
            model_type="svm",
            task_type="regression",
            hyperparameters={"C": 1.0, "kernel": "rbf", "gamma": 0.1},
            rationale="Multi-parameter optimization",
        )
        assert blueprint.hyperparameters["C"] == 1.0
        assert blueprint.hyperparameters["kernel"] == "rbf"


class TestTrainingMetric:
    """Test TrainingMetric schema."""

    def test_training_metric_valid(self) -> None:
        """Test creating a valid TrainingMetric."""
        metric = TrainingMetric(
            metric_name="accuracy",
            metric_value=0.95,
            epoch=10,
            split="test",
        )
        assert metric.metric_name == "accuracy"
        assert metric.metric_value == 0.95
        assert metric.epoch == 10

    def test_training_metric_default_split(self) -> None:
        """Test that split defaults to 'test'."""
        metric = TrainingMetric(
            metric_name="f1_score",
            metric_value=0.88,
        )
        assert metric.split == "test"

    def test_training_metric_no_epoch(self) -> None:
        """Test that epoch is optional."""
        metric = TrainingMetric(
            metric_name="loss",
            metric_value=0.05,
            split="validation",
        )
        assert metric.epoch is None


class TestFeatureImportance:
    """Test FeatureImportance schema."""

    def test_feature_importance_valid(self) -> None:
        """Test creating a valid FeatureImportance."""
        fi = FeatureImportance(
            feature_name="volume",
            importance=0.35,
        )
        assert fi.feature_name == "volume"
        assert fi.importance == 0.35

    def test_feature_importance_low_importance(self) -> None:
        """Test FeatureImportance with low importance score."""
        fi = FeatureImportance(
            feature_name="noise_feature",
            importance=0.001,
        )
        assert fi.importance == 0.001

    def test_feature_importance_missing_field(self) -> None:
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            FeatureImportance(
                feature_name="volume",
                # Missing importance
            )
