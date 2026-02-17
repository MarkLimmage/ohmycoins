# mypy: ignore-errors
"""
Model Evaluation Tools - Week 5-6 Implementation

Tools for ModelEvaluatorAgent to evaluate and compare machine learning models.
"""

from typing import Any, Literal

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV


def evaluate_model(
    model: Any,
    test_data: pd.DataFrame,
    target_column: str,
    feature_columns: list[str],
    scaler: Any | None = None,
    task_type: Literal["classification", "regression"] = "classification",
) -> dict[str, Any]:
    """
    Evaluate a trained model on test data.
    
    Args:
        model: Trained model object
        test_data: DataFrame containing test features and target
        target_column: Name of the target column
        feature_columns: List of feature column names
        scaler: Optional StandardScaler for feature scaling
        task_type: Type of task ('classification' or 'regression')
    
    Returns:
        Dictionary containing:
        - metrics: Dictionary of performance metrics
        - predictions: Array of predictions
        - confusion_matrix: Confusion matrix (for classification only)
        - classification_report: Classification report (for classification only)
    """
    # Prepare features and target
    X_test = test_data[feature_columns].copy()
    y_test = test_data[target_column].copy()

    # Handle missing values
    X_test = X_test.fillna(X_test.mean())
    if task_type == "regression":
        y_test = y_test.fillna(y_test.mean())

    # Scale features if scaler provided
    if scaler is not None:
        X_test = pd.DataFrame(
            scaler.transform(X_test),
            columns=feature_columns,
            index=X_test.index
        )

    # Make predictions
    y_pred = model.predict(X_test)

    result = {
        "predictions": y_pred.tolist(),
    }

    if task_type == "classification":
        # Classification metrics
        metrics = {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred, average="weighted", zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, average="weighted", zero_division=0)),
            "f1": float(f1_score(y_test, y_pred, average="weighted", zero_division=0)),
        }

        # ROC-AUC for binary classification
        try:
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            metrics["roc_auc"] = float(roc_auc_score(y_test, y_pred_proba))
        except (AttributeError, IndexError):
            pass

        result["metrics"] = metrics
        result["confusion_matrix"] = confusion_matrix(y_test, y_pred).tolist()
        result["classification_report"] = classification_report(y_test, y_pred, output_dict=True)

    else:  # regression
        # Regression metrics
        mse = mean_squared_error(y_test, y_pred)
        metrics = {
            "mse": float(mse),
            "rmse": float(np.sqrt(mse)),
            "mae": float(mean_absolute_error(y_test, y_pred)),
            "r2": float(r2_score(y_test, y_pred)),
        }
        result["metrics"] = metrics

    return result


def tune_hyperparameters(
    training_data: pd.DataFrame,
    target_column: str,
    feature_columns: list[str] | None = None,
    model_type: Literal[
        "random_forest_classifier",
        "random_forest_regressor"
    ] = "random_forest_classifier",
    param_grid: dict[str, list[Any]] | None = None,
    search_type: Literal["grid", "random"] = "grid",
    cv_folds: int = 5,
    n_iter: int = 10,
    scoring: str | None = None,
    random_state: int = 42,
) -> dict[str, Any]:
    """
    Tune hyperparameters for a model using grid search or random search.
    
    Args:
        training_data: DataFrame containing features and target
        target_column: Name of the target column
        feature_columns: List of feature column names. If None, uses all except target
        model_type: Type of model to tune
        param_grid: Dictionary of hyperparameters to search
                   If None, uses default grid for model type
        search_type: Type of search ('grid' or 'random')
        cv_folds: Number of cross-validation folds
        n_iter: Number of iterations for random search
        scoring: Scoring metric (e.g., 'accuracy', 'f1', 'neg_mean_squared_error')
        random_state: Random seed for reproducibility
    
    Returns:
        Dictionary containing:
        - best_params: Best hyperparameters found
        - best_score: Best cross-validation score
        - best_model: Trained model with best parameters
        - cv_results: Detailed cross-validation results
    """
    # Prepare features and target
    if feature_columns is None:
        feature_columns = [col for col in training_data.columns if col != target_column]

    X = training_data[feature_columns].copy()
    y = training_data[target_column].copy()

    # Handle missing values
    X = X.fillna(X.mean())
    if "regressor" in model_type:
        y = y.fillna(y.mean())

    # Initialize model and parameter grid
    if model_type == "random_forest_classifier":
        base_model = RandomForestClassifier(random_state=random_state)
        default_param_grid = {
            "n_estimators": [50, 100, 200],
            "max_depth": [None, 10, 20, 30],
            "min_samples_split": [2, 5, 10],
            "min_samples_leaf": [1, 2, 4],
        }
        default_scoring = scoring or "accuracy"
    elif model_type == "random_forest_regressor":
        base_model = RandomForestRegressor(random_state=random_state)
        default_param_grid = {
            "n_estimators": [50, 100, 200],
            "max_depth": [None, 10, 20, 30],
            "min_samples_split": [2, 5, 10],
            "min_samples_leaf": [1, 2, 4],
        }
        default_scoring = scoring or "neg_mean_squared_error"
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    param_grid = param_grid or default_param_grid

    # Perform hyperparameter search
    if search_type == "grid":
        search = GridSearchCV(
            base_model,
            param_grid,
            cv=cv_folds,
            scoring=default_scoring,
            n_jobs=-1,
            verbose=0
        )
    else:  # random
        search = RandomizedSearchCV(
            base_model,
            param_grid,
            n_iter=n_iter,
            cv=cv_folds,
            scoring=default_scoring,
            random_state=random_state,
            n_jobs=-1,
            verbose=0
        )

    search.fit(X, y)

    return {
        "best_params": search.best_params_,
        "best_score": float(search.best_score_),
        "best_model": search.best_estimator_,
        "cv_results": {
            "mean_test_score": search.cv_results_["mean_test_score"].tolist(),
            "std_test_score": search.cv_results_["std_test_score"].tolist(),
            "params": search.cv_results_["params"],
        },
        "search_type": search_type,
        "cv_folds": cv_folds,
    }


def compare_models(
    models: dict[str, dict[str, Any]],
    test_data: pd.DataFrame,
    target_column: str,
    feature_columns: list[str],
    task_type: Literal["classification", "regression"] = "classification",
    primary_metric: str | None = None,
) -> dict[str, Any]:
    """
    Compare multiple trained models on the same test data.
    
    Args:
        models: Dictionary mapping model names to model info dicts
               Each model info dict should contain:
               - 'model': the trained model
               - 'scaler': optional scaler
        test_data: DataFrame containing test features and target
        target_column: Name of the target column
        feature_columns: List of feature column names
        task_type: Type of task ('classification' or 'regression')
        primary_metric: Primary metric for comparison
                       If None, uses 'accuracy' for classification or 'r2' for regression
    
    Returns:
        Dictionary containing:
        - comparisons: Dictionary mapping model names to their metrics
        - best_model: Name of the best performing model
        - rankings: Dictionary ranking models by each metric
    """
    if task_type == "classification":
        default_primary_metric = "accuracy"
    else:  # regression
        default_primary_metric = "r2"

    primary_metric = primary_metric or default_primary_metric

    # Evaluate each model
    comparisons = {}
    for model_name, model_info in models.items():
        model = model_info.get("model")
        scaler = model_info.get("scaler")

        if model is None:
            continue

        evaluation = evaluate_model(
            model=model,
            test_data=test_data,
            target_column=target_column,
            feature_columns=feature_columns,
            scaler=scaler,
            task_type=task_type,
        )

        comparisons[model_name] = evaluation["metrics"]

    # Find best model based on primary metric
    if comparisons:
        if task_type == "regression" and primary_metric in ["mse", "rmse", "mae"]:
            # Lower is better for these metrics
            best_model = min(comparisons.items(), key=lambda x: x[1][primary_metric])[0]
        else:
            # Higher is better for other metrics
            best_model = max(comparisons.items(), key=lambda x: x[1][primary_metric])[0]
    else:
        best_model = None

    # Create rankings for each metric
    rankings = {}
    if comparisons:
        metrics = list(next(iter(comparisons.values())).keys())
        for metric in metrics:
            if task_type == "regression" and metric in ["mse", "rmse", "mae"]:
                # Lower is better
                ranked = sorted(comparisons.items(), key=lambda x: x[1][metric])
            else:
                # Higher is better
                ranked = sorted(comparisons.items(), key=lambda x: x[1][metric], reverse=True)
            rankings[metric] = [model_name for model_name, _ in ranked]

    return {
        "comparisons": comparisons,
        "best_model": best_model,
        "rankings": rankings,
        "primary_metric": primary_metric,
        "task_type": task_type,
    }


def calculate_feature_importance(
    model: Any,
    feature_columns: list[str],
    top_n: int = 10,
) -> dict[str, Any]:
    """
    Calculate and rank feature importance for a trained model.
    
    Args:
        model: Trained model with feature_importances_ attribute
        feature_columns: List of feature column names
        top_n: Number of top features to return
    
    Returns:
        Dictionary containing:
        - feature_importances: Dictionary mapping features to importance scores
        - top_features: List of top N most important features
        - feature_importance_list: List of tuples (feature, importance) sorted by importance
    """
    # Check if model has feature_importances_ attribute
    if not hasattr(model, "feature_importances_"):
        return {
            "error": "Model does not support feature importance calculation",
            "feature_importances": {},
            "top_features": [],
            "feature_importance_list": [],
        }

    # Get feature importances
    importances = model.feature_importances_

    # Create dictionary mapping features to importances
    feature_importance_dict = {
        feature: float(importance)
        for feature, importance in zip(feature_columns, importances, strict=False)
    }

    # Sort by importance (descending)
    sorted_features = sorted(
        feature_importance_dict.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # Get top N features
    top_features = [feature for feature, _ in sorted_features[:top_n]]

    return {
        "feature_importances": feature_importance_dict,
        "top_features": top_features,
        "feature_importance_list": sorted_features[:top_n],
        "total_features": len(feature_columns),
    }
