# mypy: ignore-errors
"""
Model Training Agent - Trains machine learning models on cryptocurrency data.

Week 5-6 implementation: New agent for model training and cross-validation.
"""

from typing import Any

import pandas as pd

from ..tools import (
    cross_validate_model,
    train_classification_model,
    train_regression_model,
)
from .base import BaseAgent


class ModelTrainingAgent(BaseAgent):
    """
    Agent responsible for training machine learning models.

    Week 5-6 Implementation Tools:
    - train_classification_model: Train classification models (e.g., price direction prediction)
    - train_regression_model: Train regression models (e.g., price prediction)
    - cross_validate_model: Perform cross-validation to estimate model performance
    """

    def __init__(self) -> None:
        """Initialize the model training agent."""
        super().__init__(
            name="ModelTrainingAgent",
            description="Trains machine learning models on cryptocurrency data",
        )

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute model training based on analyzed data and user goal.

        Args:
            state: Current workflow state with analysis_results

        Returns:
            Updated state with trained models
        """
        # Initialize pending events for this execution step
        state["pending_events"] = []

        try:
            await self.emit_event(
                state,
                "status_update",
                "MODELING",
                {"status": "ACTIVE", "message": "Initializing model training..."},
            )

            # Get analysis results from previous agent
            analysis_results = state.get("analysis_results", {})

            if not analysis_results:
                state["error"] = "No analysis results available for model training"
                state["model_trained"] = False
                await self.emit_event(
                    state,
                    "error",
                    "MODELING",
                    {"error": "No analysis results available"},
                )
                return state

            user_goal = state.get("user_goal", "")
            training_params = state.get("training_params", {})

            # Determine task type from user goal
            task_type = self._determine_task_type(user_goal, training_params)

            # Get MV Name if available (Phase 5: Parquet Caching)
            mv_name = state.get("mv_name") or analysis_results.get("mv_name")

            # Prepare training data
            training_data = self._prepare_training_data(analysis_results, state)

            if not mv_name and (training_data is None or len(training_data) == 0):
                state["error"] = "Insufficient data for model training"
                state["model_trained"] = False
                await self.emit_event(
                    state,
                    "error",
                    "MODELING",
                    {"error": "Insufficient data"},
                )
                return state

            # Get training configuration
            target_column = training_params.get(
                "target_column", self._infer_target_column(task_type)
            )
            feature_columns = training_params.get("feature_columns", None)
            model_type = training_params.get("model_type", "random_forest")
            hyperparameters = training_params.get("hyperparameters", None)
            test_size = training_params.get("test_size", 0.2)
            scale_features = training_params.get("scale_features", True)

            await self.emit_event(
                state,
                "stream_chat",
                "MODELING",
                {"message": f"I'm training a {model_type} model for this {task_type} task..."},
            )

            await self.emit_event(
                state,
                "status_update",
                "MODELING",
                {
                    "status": "ACTIVE",
                    "message": f"Training {model_type} ({task_type})...",
                    "task_id": "train_models"
                },
            )

            # Train the model
            session_id = state.get("session_id", "unknown_session")
            if task_type == "classification":
                model_result = await train_classification_model(
                    session_id=session_id,
                    target_column=target_column,
                    training_data=training_data,
                    mv_name=mv_name,
                    feature_columns=feature_columns,
                    model_type=model_type,
                    hyperparameters=hyperparameters,
                    test_size=test_size,
                    scale_features=scale_features,
                )
            else:  # regression
                model_result = await train_regression_model(
                    session_id=session_id,
                    target_column=target_column,
                    training_data=training_data,
                    mv_name=mv_name,
                    feature_columns=feature_columns,
                    model_type=model_type,
                    hyperparameters=hyperparameters,
                    test_size=test_size,
                    scale_features=scale_features,
                )

            # Perform cross-validation if requested
            cv_results = None
            if training_params.get("perform_cv", True):
                cv_model_type = self._get_cv_model_type(model_type, task_type)
                cv_results = cross_validate_model(
                    training_data=training_data,
                    target_column=target_column,
                    feature_columns=feature_columns,
                    model_type=cv_model_type,
                    cv_folds=training_params.get("cv_folds", 5),
                    scale_features=scale_features,
                )

            # Update state with training results
            state["model_trained"] = True
            state["trained_models"] = {
                "primary_model": {
                    "model": model_result["model"],
                    "scaler": model_result["scaler"],
                    "feature_columns": model_result["feature_columns"],
                    "metrics": model_result["metrics"],
                    "model_type": model_result["model_type"],
                    "task_type": task_type,
                }
            }

            if cv_results:
                state["trained_models"]["primary_model"]["cv_results"] = cv_results

            # Emit training metrics
            metrics_data = {
                "metrics": model_result["metrics"],
                "model_type": model_result["model_type"],
                "task_type": task_type,
                "cv_results": cv_results,
            }

            await self.emit_event(
                state,
                "render_output",
                "MODELING",
                {
                    "mime_type": "application/json+tearsheet",
                    "content": {
                        "metric_type": "training_metrics",
                        "data": metrics_data,
                    },
                },
            )

            # Generate training summary
            state["training_summary"] = self._generate_training_summary(
                model_result, cv_results, task_type
            )

            await self.emit_event(
                state,
                "stream_chat",
                "MODELING",
                {"message": f"Training complete. The model achieved a score of {model_result['metrics'].get('score', 'N/A')}. Let's evaluate it against our baseline."},
            )

            # Add message about training completion
            state["messages"].append(
                {
                    "role": "agent",
                    "agent": self.name,
                    "content": f"Model training completed. Task type: {task_type}, Model: {model_type}",
                    "timestamp": pd.Timestamp.now().isoformat(),
                }
            )

            return state

        except Exception as e:
            state["error"] = f"Model training failed: {str(e)}"
            state["model_trained"] = False
            await self.emit_event(state, "error", "MODELING", {"error": str(e)})
            state["messages"].append(
                {
                    "role": "agent",
                    "agent": self.name,
                    "content": f"Model training failed: {str(e)}",
                    "timestamp": pd.Timestamp.now().isoformat(),
                }
            )
            return state

    def _determine_task_type(
        self, user_goal: str, training_params: dict[str, Any]
    ) -> str:
        """Determine whether this is a classification or regression task."""
        if "task_type" in training_params:
            return training_params["task_type"]

        # Infer from user goal
        user_goal_lower = user_goal.lower()

        classification_keywords = [
            "classify",
            "classification",
            "predict direction",
            "binary",
            "category",
        ]
        regression_keywords = [
            "regress",
            "regression",
            "predict price",
            "predict value",
            "forecast",
        ]

        if any(keyword in user_goal_lower for keyword in classification_keywords):
            return "classification"
        elif any(keyword in user_goal_lower for keyword in regression_keywords):
            return "regression"

        # Default to classification for cryptocurrency price direction prediction
        return "classification"

    def _prepare_training_data(
        self, analysis_results: dict[str, Any], state: dict[str, Any]
    ) -> pd.DataFrame | None:
        """Prepare training data from analysis results."""
        # Check if we have a processed DataFrame with features
        if "processed_data" in analysis_results:
            df = analysis_results["processed_data"]
            if isinstance(df, pd.DataFrame):
                return df

        # Check for price data with technical indicators
        if "technical_indicators" in analysis_results:
            indicator_data = analysis_results["technical_indicators"]
            if isinstance(indicator_data, pd.DataFrame):
                return indicator_data

        # Fallback to retrieved price data
        retrieved_data = state.get("retrieved_data", {})
        if "price_data" in retrieved_data and retrieved_data["price_data"]:
            return pd.DataFrame(retrieved_data["price_data"])

        return None

    def _infer_target_column(self, task_type: str) -> str:
        """Infer the target column name based on task type."""
        if task_type == "classification":
            return "price_direction"  # Binary: up (1) or down (0)
        else:  # regression
            return "future_price"  # Continuous price value

    def _get_cv_model_type(self, model_type: str, task_type: str) -> str:
        """Convert model type to cross-validation compatible format."""
        if task_type == "classification":
            if "random_forest" in model_type:
                return "random_forest_classifier"
            elif "logistic" in model_type:
                return "logistic_regression"
            else:
                return "random_forest_classifier"
        else:  # regression
            if "random_forest" in model_type:
                return "random_forest_regressor"
            elif "linear" in model_type:
                return "linear_regression"
            else:
                return "random_forest_regressor"

    def _generate_training_summary(
        self,
        model_result: dict[str, Any],
        cv_results: dict[str, Any] | None,
        task_type: str,
    ) -> str:
        """Generate a human-readable training summary."""
        summary_lines = []

        summary_lines.append(f"Task Type: {task_type.title()}")
        summary_lines.append(f"Model Type: {model_result['model_type']}")
        summary_lines.append(f"Training Samples: {model_result['train_size']}")
        summary_lines.append(f"Test Samples: {model_result['test_size']}")
        summary_lines.append("")

        # Add metrics
        if task_type == "classification":
            test_metrics = model_result["metrics"]["test"]
            summary_lines.append("Test Set Performance:")
            summary_lines.append(f"  Accuracy: {test_metrics['accuracy']:.4f}")
            summary_lines.append(f"  Precision: {test_metrics['precision']:.4f}")
            summary_lines.append(f"  Recall: {test_metrics['recall']:.4f}")
            summary_lines.append(f"  F1 Score: {test_metrics['f1']:.4f}")
            if "roc_auc" in test_metrics:
                summary_lines.append(f"  ROC-AUC: {test_metrics['roc_auc']:.4f}")
        else:  # regression
            test_metrics = model_result["metrics"]["test"]
            summary_lines.append("Test Set Performance:")
            summary_lines.append(f"  RMSE: {test_metrics['rmse']:.4f}")
            summary_lines.append(f"  MAE: {test_metrics['mae']:.4f}")
            summary_lines.append(f"  R²: {test_metrics['r2']:.4f}")

        # Add cross-validation results if available
        if cv_results:
            summary_lines.append("")
            summary_lines.append(f"Cross-Validation ({cv_results['cv_folds']}-Fold):")
            summary_lines.append(f"  Mean Score: {cv_results['mean_score']:.4f}")
            summary_lines.append(f"  Std Score: {cv_results['std_score']:.4f}")

        return "\n".join(summary_lines)
