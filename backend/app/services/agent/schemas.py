"""Agent schemas for Sprint 2.45 — Blueprint + structured events."""

from typing import Any

from pydantic import BaseModel


class ModelBlueprint(BaseModel):
    """Blueprint card for user approval before training."""

    target: str
    features: list[str]
    model_type: str
    task_type: str
    hyperparameters: dict[str, Any]
    rationale: str
    estimated_training_time: str | None = None


class TrainingMetric(BaseModel):
    """Structured training metric event."""

    metric_name: str
    metric_value: float
    epoch: int | None = None
    split: str = "test"


class FeatureImportance(BaseModel):
    """Feature importance from a trained model."""

    feature_name: str
    importance: float
