"""
Model Evaluator Agent - Evaluates and compares machine learning models.

Week 5-6 implementation: New agent for model evaluation and hyperparameter tuning.
"""

from typing import Any
import pandas as pd

from .base import BaseAgent
from ..tools import (
    evaluate_model,
    tune_hyperparameters,
    compare_models,
    calculate_feature_importance,
)


class ModelEvaluatorAgent(BaseAgent):
    """
    Agent responsible for evaluating and comparing machine learning models.
    
    Week 5-6 Implementation Tools:
    - evaluate_model: Evaluate a trained model on test data
    - tune_hyperparameters: Tune model hyperparameters using grid/random search
    - compare_models: Compare multiple models on the same test data
    - calculate_feature_importance: Calculate feature importance for interpretability
    """
    
    def __init__(self) -> None:
        """Initialize the model evaluator agent."""
        super().__init__(
            name="ModelEvaluatorAgent",
            description="Evaluates and compares machine learning models"
        )
    
    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute model evaluation based on trained models.
        
        Args:
            state: Current workflow state with trained_models
        
        Returns:
            Updated state with evaluation results
        """
        try:
            # Get trained models from previous agent
            trained_models = state.get("trained_models", {})
            
            if not trained_models:
                state["error"] = "No trained models available for evaluation"
                state["model_evaluated"] = False
                return state
            
            user_goal = state.get("user_goal", "")
            evaluation_params = state.get("evaluation_params", {})
            
            # Get test data for evaluation
            test_data = self._get_test_data(state, evaluation_params)
            
            if test_data is None or len(test_data) == 0:
                state["error"] = "No test data available for evaluation"
                state["model_evaluated"] = False
                return state
            
            # Initialize evaluation results
            evaluation_results: dict[str, Any] = {}
            
            # Evaluate primary model
            primary_model = trained_models.get("primary_model")
            if primary_model:
                task_type = primary_model.get("task_type", "classification")
                target_column = evaluation_params.get(
                    "target_column", 
                    self._infer_target_column(task_type)
                )
                
                # Evaluate the model
                model_evaluation = evaluate_model(
                    model=primary_model["model"],
                    test_data=test_data,
                    target_column=target_column,
                    feature_columns=primary_model["feature_columns"],
                    scaler=primary_model.get("scaler"),
                    task_type=task_type,
                )
                
                evaluation_results["primary_model_evaluation"] = model_evaluation
                
                # Calculate feature importance
                if evaluation_params.get("calculate_importance", True):
                    importance = calculate_feature_importance(
                        model=primary_model["model"],
                        feature_columns=primary_model["feature_columns"],
                        top_n=evaluation_params.get("top_n_features", 10),
                    )
                    evaluation_results["feature_importance"] = importance
                
                # Hyperparameter tuning if requested
                if evaluation_params.get("tune_hyperparameters", False):
                    training_data = self._prepare_training_data(state)
                    if training_data is not None:
                        tuning_result = tune_hyperparameters(
                            training_data=training_data,
                            target_column=target_column,
                            feature_columns=primary_model["feature_columns"],
                            model_type=self._get_tuning_model_type(
                                primary_model["model_type"],
                                task_type
                            ),
                            search_type=evaluation_params.get("search_type", "grid"),
                            cv_folds=evaluation_params.get("cv_folds", 5),
                        )
                        evaluation_results["hyperparameter_tuning"] = tuning_result
            
            # Compare multiple models if available
            if len(trained_models) > 1:
                comparison = compare_models(
                    models={
                        name: {"model": info["model"], "scaler": info.get("scaler")}
                        for name, info in trained_models.items()
                    },
                    test_data=test_data,
                    target_column=target_column,
                    feature_columns=primary_model["feature_columns"],
                    task_type=task_type,
                )
                evaluation_results["model_comparison"] = comparison
            
            # Generate evaluation insights
            insights = self._generate_evaluation_insights(evaluation_results, task_type)
            
            # Update state
            state["model_evaluated"] = True
            state["evaluation_results"] = evaluation_results
            state["evaluation_insights"] = insights
            
            # Add message about evaluation completion
            state["messages"].append({
                "role": "agent",
                "agent": self.name,
                "content": f"Model evaluation completed. Generated {len(insights)} insights.",
                "timestamp": pd.Timestamp.now().isoformat(),
            })
            
            return state
            
        except Exception as e:
            state["error"] = f"Model evaluation failed: {str(e)}"
            state["model_evaluated"] = False
            state["messages"].append({
                "role": "agent",
                "agent": self.name,
                "content": f"Model evaluation failed: {str(e)}",
                "timestamp": pd.Timestamp.now().isoformat(),
            })
            return state
    
    def _get_test_data(
        self, 
        state: dict[str, Any], 
        evaluation_params: dict[str, Any]
    ) -> pd.DataFrame | None:
        """Get test data for evaluation."""
        # Check if test data explicitly provided
        if "test_data" in evaluation_params:
            return evaluation_params["test_data"]
        
        # Use analysis results
        analysis_results = state.get("analysis_results", {})
        if "processed_data" in analysis_results:
            df = analysis_results["processed_data"]
            if isinstance(df, pd.DataFrame):
                # Split data for testing (use last 20%)
                split_idx = int(len(df) * 0.8)
                return df[split_idx:]
        
        # Fallback to retrieved price data
        retrieved_data = state.get("retrieved_data", {})
        if "price_data" in retrieved_data and retrieved_data["price_data"]:
            df = pd.DataFrame(retrieved_data["price_data"])
            split_idx = int(len(df) * 0.8)
            return df[split_idx:]
        
        return None
    
    def _prepare_training_data(self, state: dict[str, Any]) -> pd.DataFrame | None:
        """Prepare training data for hyperparameter tuning."""
        analysis_results = state.get("analysis_results", {})
        
        if "processed_data" in analysis_results:
            df = analysis_results["processed_data"]
            if isinstance(df, pd.DataFrame):
                return df
        
        retrieved_data = state.get("retrieved_data", {})
        if "price_data" in retrieved_data and retrieved_data["price_data"]:
            return pd.DataFrame(retrieved_data["price_data"])
        
        return None
    
    def _infer_target_column(self, task_type: str) -> str:
        """Infer the target column name based on task type."""
        if task_type == "classification":
            return "price_direction"
        else:  # regression
            return "future_price"
    
    def _get_tuning_model_type(self, model_type: str, task_type: str) -> str:
        """Convert model type to tuning compatible format."""
        if task_type == "classification":
            return "random_forest_classifier"
        else:  # regression
            return "random_forest_regressor"
    
    def _generate_evaluation_insights(
        self,
        evaluation_results: dict[str, Any],
        task_type: str
    ) -> list[str]:
        """Generate human-readable insights from evaluation results."""
        insights = []
        
        # Primary model evaluation insights
        if "primary_model_evaluation" in evaluation_results:
            eval_metrics = evaluation_results["primary_model_evaluation"]["metrics"]
            
            if task_type == "classification":
                accuracy = eval_metrics.get("accuracy", 0)
                f1 = eval_metrics.get("f1", 0)
                
                if accuracy > 0.7:
                    insights.append(
                        f"✓ Model shows strong performance with {accuracy:.1%} accuracy"
                    )
                elif accuracy > 0.5:
                    insights.append(
                        f"⚠ Model shows moderate performance with {accuracy:.1%} accuracy"
                    )
                else:
                    insights.append(
                        f"✗ Model shows poor performance with {accuracy:.1%} accuracy - consider different features or model type"
                    )
                
                if "roc_auc" in eval_metrics:
                    roc_auc = eval_metrics["roc_auc"]
                    if roc_auc > 0.8:
                        insights.append(
                            f"✓ Strong discriminative ability with ROC-AUC of {roc_auc:.3f}"
                        )
                    elif roc_auc < 0.6:
                        insights.append(
                            f"⚠ Weak discriminative ability with ROC-AUC of {roc_auc:.3f}"
                        )
            
            else:  # regression
                r2 = eval_metrics.get("r2", 0)
                rmse = eval_metrics.get("rmse", 0)
                
                if r2 > 0.7:
                    insights.append(
                        f"✓ Model explains {r2:.1%} of price variance"
                    )
                elif r2 > 0.4:
                    insights.append(
                        f"⚠ Model explains {r2:.1%} of price variance - moderate predictive power"
                    )
                else:
                    insights.append(
                        f"✗ Model explains only {r2:.1%} of price variance - consider more features"
                    )
                
                insights.append(f"Average prediction error (RMSE): {rmse:.4f}")
        
        # Feature importance insights
        if "feature_importance" in evaluation_results:
            importance_data = evaluation_results["feature_importance"]
            if "top_features" in importance_data and importance_data["top_features"]:
                top_3 = importance_data["top_features"][:3]
                insights.append(
                    f"Top predictive features: {', '.join(top_3)}"
                )
        
        # Hyperparameter tuning insights
        if "hyperparameter_tuning" in evaluation_results:
            tuning = evaluation_results["hyperparameter_tuning"]
            best_score = tuning.get("best_score", 0)
            insights.append(
                f"Hyperparameter tuning achieved best CV score of {abs(best_score):.4f}"
            )
        
        # Model comparison insights
        if "model_comparison" in evaluation_results:
            comparison = evaluation_results["model_comparison"]
            best_model = comparison.get("best_model")
            if best_model:
                insights.append(
                    f"Best performing model: {best_model}"
                )
        
        return insights
