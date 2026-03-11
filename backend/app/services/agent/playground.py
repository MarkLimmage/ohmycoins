# mypy: ignore-errors
"""Model Playground Service — load and run predictions on saved models."""

import json
import uuid
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sqlmodel import Session

from .artifacts import ArtifactManager


class ModelPlaygroundService:
    def __init__(self, base_dir: str = "/data/agent_artifacts"):
        self.artifact_manager = ArtifactManager(base_dir=base_dir)

    def load_model(self, artifact_id: uuid.UUID, db: Session) -> tuple[Any, Any, dict]:
        """Load model, optional scaler, and metadata from disk."""
        artifact = self.artifact_manager.get_artifact(artifact_id, db)
        if not artifact or not artifact.file_path:
            raise FileNotFoundError(f"Artifact {artifact_id} not found or has no file path")

        model_path = Path(artifact.file_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        model = joblib.load(model_path)

        # Try loading scaler
        scaler = None
        scaler_path = model_path.parent / f"{model_path.stem}_scaler.joblib"
        if scaler_path.exists():
            scaler = joblib.load(scaler_path)

        # Try loading metadata
        metadata: dict[str, Any] = {}
        meta_path = model_path.parent / f"{model_path.stem}_metadata.json"
        if meta_path.exists():
            metadata = json.loads(meta_path.read_text())

        return model, scaler, metadata

    def predict(self, model: Any, scaler: Any, feature_values: dict[str, float], metadata: dict) -> dict:
        """Run prediction on a single sample."""
        feature_columns = metadata.get("feature_columns", list(feature_values.keys()))

        # Build DataFrame with correct column order
        df = pd.DataFrame([{col: feature_values.get(col, 0.0) for col in feature_columns}])

        # Apply scaler if present
        if scaler is not None:
            df = pd.DataFrame(scaler.transform(df), columns=feature_columns)

        # Predict
        prediction = model.predict(df)[0]

        result: dict[str, Any] = {
            "prediction": float(prediction) if isinstance(prediction, int | float | np.integer | np.floating) else str(prediction),
            "model_type": type(model).__name__,
            "task_type": metadata.get("task_type", "unknown"),
            "feature_columns_used": feature_columns,
        }

        # Classification probabilities
        if hasattr(model, "predict_proba"):
            try:
                probas = model.predict_proba(df)[0]
                classes = model.classes_
                result["probabilities"] = {str(c): float(p) for c, p in zip(classes, probas, strict=False)}
                result["prediction_label"] = str(prediction)
            except Exception:
                pass

        return result

    def predict_with_explanation(
        self, model: Any, scaler: Any, feature_values: dict[str, float], metadata: dict
    ) -> dict:
        """Run prediction with optional SHAP explanation."""
        from .explainability import ExplainabilityService

        result = self.predict(model, scaler, feature_values, metadata)

        explainability = ExplainabilityService()
        shap_result = explainability.compute_prediction_shap(model, scaler, feature_values, metadata)

        if shap_result:
            result["shap_values"] = shap_result["shap_values"]
            result["shap_base_value"] = shap_result["base_value"]
        else:
            result["shap_values"] = None
            result["shap_base_value"] = None

        return result

    def get_model_info(self, artifact_id: uuid.UUID, db: Session) -> dict:
        """Return metadata about the model for the playground UI."""
        artifact = self.artifact_manager.get_artifact(artifact_id, db)
        if not artifact or not artifact.file_path:
            raise FileNotFoundError(f"Artifact {artifact_id} not found")

        model_path = Path(artifact.file_path)
        metadata: dict[str, Any] = {}
        meta_path = model_path.parent / f"{model_path.stem}_metadata.json"
        if meta_path.exists():
            metadata = json.loads(meta_path.read_text())

        return {
            "artifact_id": str(artifact_id),
            "model_type": metadata.get("model_type", "unknown"),
            "task_type": metadata.get("task_type", "unknown"),
            "feature_columns": metadata.get("feature_columns", []),
            "training_metrics": metadata.get("metrics"),
            "created_at": str(artifact.created_at) if artifact.created_at else None,
        }
