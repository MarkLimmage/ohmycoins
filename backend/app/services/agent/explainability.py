# mypy: ignore-errors
"""SHAP Explainability Service — compute and cache model explanations."""

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import shap

from .artifacts import ArtifactManager
from .playground import ModelPlaygroundService

logger = logging.getLogger(__name__)


class ExplainabilityService:
    """Compute SHAP explanations for trained models."""

    TREE_MODELS = {
        "RandomForestClassifier",
        "RandomForestRegressor",
        "GradientBoostingClassifier",
        "GradientBoostingRegressor",
        "DecisionTreeClassifier",
        "DecisionTreeRegressor",
        "XGBClassifier",
        "XGBRegressor",
    }
    LINEAR_MODELS = {"LogisticRegression", "LinearRegression", "Ridge", "Lasso"}
    UNSUPPORTED_MODELS = {"SVC", "SVR"}

    def __init__(self, base_dir: str = "/data/agent_artifacts"):
        self.playground = ModelPlaygroundService(base_dir=base_dir)
        self.artifact_manager = ArtifactManager(base_dir=base_dir)

    def is_supported(self, model: Any) -> bool:
        model_type = type(model).__name__
        return model_type not in self.UNSUPPORTED_MODELS and (
            model_type in self.TREE_MODELS or model_type in self.LINEAR_MODELS
        )

    def get_explainer_type(self, model: Any) -> str | None:
        model_type = type(model).__name__
        if model_type in self.TREE_MODELS:
            return "tree"
        if model_type in self.LINEAR_MODELS:
            return "linear"
        return None

    def _get_shap_cache_path(self, model_path: Path) -> Path:
        return model_path.parent / f"{model_path.stem}_shap.json"

    def _get_plot_path(self, model_path: Path) -> Path:
        return model_path.parent / f"{model_path.stem}_shap_summary.png"

    def _normalize_shap_values(self, shap_values: Any) -> np.ndarray:
        """Normalize SHAP values to a 2D array (n_samples, n_features).

        Handles list-of-arrays (per-class) and 3D arrays from classification models.
        For classification, uses the last class (positive class for binary).
        """
        if isinstance(shap_values, list):
            # Per-class arrays — use last class (positive class for binary)
            sv = np.array(shap_values[-1])
        else:
            sv = np.array(shap_values)

        # If 3D (n_samples, n_features, n_classes), take last class along axis 2
        if sv.ndim == 3:
            sv = sv[:, :, -1]

        return sv

    def _generate_background_data(
        self, metadata: dict, n_samples: int = 100
    ) -> np.ndarray:
        feature_columns = metadata.get("feature_columns", [])
        n_features = len(feature_columns)
        if n_features == 0:
            raise ValueError("No feature columns in metadata")
        rng = np.random.RandomState(42)
        return rng.randn(n_samples, n_features)

    def compute_global_shap(
        self, artifact_id: Any, db: Any, max_samples: int = 100
    ) -> dict[str, Any]:
        import uuid as uuid_mod

        if isinstance(artifact_id, str):
            artifact_id = uuid_mod.UUID(artifact_id)

        model, scaler, metadata = self.playground.load_model(artifact_id, db)
        model_type = type(model).__name__

        if not self.is_supported(model):
            return {
                "supported": False,
                "reason": f"Model type {model_type} not supported for SHAP explanation",
                "model_type": model_type,
            }

        artifact = self.artifact_manager.get_artifact(artifact_id, db)
        if not artifact or not artifact.file_path:
            raise FileNotFoundError(f"Artifact {artifact_id} not found")

        model_path = Path(artifact.file_path)
        cache_path = self._get_shap_cache_path(model_path)

        if cache_path.exists():
            cached = json.loads(cache_path.read_text())
            return {
                "supported": True,
                "feature_importance": cached["feature_importance"],
                "model_type": model_type,
                "shap_base_value": cached.get("base_value"),
                "plot_path": cached.get("plot_path"),
                "cached": True,
            }

        feature_columns = metadata.get("feature_columns", [])
        explainer_type = self.get_explainer_type(model)

        background = self._generate_background_data(metadata, max_samples)
        if scaler is not None:
            bg_df = pd.DataFrame(background, columns=feature_columns)
            background = scaler.transform(bg_df)

        if explainer_type == "tree":
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(background)
        elif explainer_type == "linear":
            explainer = shap.LinearExplainer(model, background)
            shap_values = explainer.shap_values(background)
        else:
            return {
                "supported": False,
                "reason": f"No explainer for {model_type}",
                "model_type": model_type,
            }

        sv = self._normalize_shap_values(shap_values)

        mean_abs_shap = np.mean(np.abs(sv), axis=0)
        feature_importance = [
            {"feature_name": name, "importance": float(imp)}
            for name, imp in sorted(
                zip(feature_columns, mean_abs_shap, strict=False),
                key=lambda x: x[1],
                reverse=True,
            )
        ]

        base_value = (
            float(explainer.expected_value)
            if isinstance(
                explainer.expected_value, int | float | np.integer | np.floating
            )
            else float(explainer.expected_value[0])
            if hasattr(explainer.expected_value, "__len__")
            else None
        )

        plot_path = self._get_plot_path(model_path)
        try:
            self._generate_summary_plot(sv, feature_columns, str(plot_path))
        except Exception as e:
            logger.warning("Failed to generate SHAP summary plot: %s", e)
            plot_path = None

        cache_data = {
            "feature_importance": feature_importance,
            "base_value": base_value,
            "model_type": model_type,
            "plot_path": str(plot_path) if plot_path else None,
        }
        cache_path.write_text(json.dumps(cache_data, indent=2))

        return {
            "supported": True,
            "feature_importance": feature_importance,
            "model_type": model_type,
            "shap_base_value": base_value,
            "plot_path": str(plot_path) if plot_path else None,
            "cached": False,
        }

    def compute_prediction_shap(
        self, model: Any, scaler: Any, feature_values: dict[str, float], metadata: dict
    ) -> dict[str, Any] | None:
        if not self.is_supported(model):
            return None

        feature_columns = metadata.get("feature_columns", list(feature_values.keys()))
        df = pd.DataFrame(
            [{col: feature_values.get(col, 0.0) for col in feature_columns}]
        )

        if scaler is not None:
            df_scaled = pd.DataFrame(scaler.transform(df), columns=feature_columns)
        else:
            df_scaled = df

        explainer_type = self.get_explainer_type(model)

        if explainer_type == "tree":
            explainer = shap.TreeExplainer(model)
            sv = explainer.shap_values(df_scaled.values)
        elif explainer_type == "linear":
            background = self._generate_background_data(metadata, 50)
            if scaler is not None:
                bg_df = pd.DataFrame(background, columns=feature_columns)
                background = scaler.transform(bg_df)
            explainer = shap.LinearExplainer(model, background)
            sv = explainer.shap_values(df_scaled.values)
        else:
            return None

        sv_arr = self._normalize_shap_values(sv)

        prediction_shap = sv_arr[0] if sv_arr.ndim > 1 else sv_arr

        base_value = (
            float(explainer.expected_value)
            if isinstance(
                explainer.expected_value, int | float | np.integer | np.floating
            )
            else float(explainer.expected_value[0])
            if hasattr(explainer.expected_value, "__len__")
            else 0.0
        )

        return {
            "shap_values": {
                name: float(val)
                for name, val in zip(feature_columns, prediction_shap, strict=False)
            },
            "base_value": base_value,
        }

    def _generate_summary_plot(
        self, shap_values: np.ndarray, feature_names: list[str], save_path: str
    ) -> None:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        mean_abs = np.mean(np.abs(shap_values), axis=0)
        sorted_idx = np.argsort(mean_abs)

        fig, ax = plt.subplots(figsize=(10, max(4, len(feature_names) * 0.3)))
        sorted_names = [feature_names[i] for i in sorted_idx]
        sorted_vals = mean_abs[sorted_idx]

        ax.barh(range(len(sorted_names)), sorted_vals, color="#1f77b4")
        ax.set_yticks(range(len(sorted_names)))
        ax.set_yticklabels(sorted_names)
        ax.set_xlabel("Mean |SHAP value|")
        ax.set_title("Feature Importance (SHAP)")
        plt.tight_layout()
        plt.savefig(save_path, dpi=100, bbox_inches="tight")
        plt.close(fig)
