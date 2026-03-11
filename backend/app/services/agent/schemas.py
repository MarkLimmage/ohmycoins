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


class PromoteArtifactRequest(BaseModel):
    """Request to promote an artifact to a Floor algorithm."""

    algorithm_name: str
    description: str = ""
    position_limit: float = 100.0
    daily_loss_limit: float = 5.0
    execution_frequency: int = 14400  # 4 hours in seconds


class PredictionRequest(BaseModel):
    """Request to run a prediction on a saved model."""

    feature_values: dict[str, float]
    include_explanation: bool = False


class PredictionResponse(BaseModel):
    """Response from a model prediction."""

    prediction: float | str
    prediction_label: str | None = None
    probabilities: dict[str, float] | None = None
    model_type: str
    task_type: str
    feature_columns_used: list[str]
    shap_values: dict[str, float] | None = None
    shap_base_value: float | None = None


class ModelInfo(BaseModel):
    """Model metadata for the playground UI."""

    artifact_id: str
    model_type: str
    task_type: str
    feature_columns: list[str]
    training_metrics: dict[str, Any] | None = None
    created_at: str | None = None


class ExplanationResponse(BaseModel):
    """Response from model explanation."""

    supported: bool
    reason: str | None = None
    feature_importance: list[FeatureImportance] | None = None
    plot_artifact_id: str | None = None
    plot_path: str | None = None
    model_type: str
    shap_base_value: float | None = None
    cached: bool = False
