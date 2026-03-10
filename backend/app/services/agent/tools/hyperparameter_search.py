# mypy: ignore-errors
"""Hyperparameter search tool for agent-driven model optimization."""

from typing import Any

import optuna
import pandas as pd
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.model_selection import cross_val_score
from xgboost import XGBClassifier, XGBRegressor

# Silence Optuna logging
optuna.logging.set_verbosity(optuna.logging.WARNING)


def hyperparameter_search(
    training_data: pd.DataFrame,
    target_column: str,
    model_type: str,
    task_type: str,
    n_trials: int = 10,
    cv_folds: int = 5,
) -> dict[str, Any]:
    """
    Search for optimal hyperparameters using Optuna.

    Args:
        training_data: DataFrame with features and target
        target_column: Name of target column
        model_type: "random_forest" or "gradient_boosting"
        task_type: "classification" or "regression"
        n_trials: Number of trials to run
        cv_folds: Number of CV folds

    Returns:
        Dictionary with: best_params, best_score, n_trials, model_type, task_type, scoring
    """
    # Prepare features and target
    X = training_data.drop(columns=[target_column])
    y = training_data[target_column]

    # Handle missing values
    X = X.fillna(X.mean())
    if task_type == "regression":
        y = y.fillna(y.mean())

    # Define scoring metric
    if task_type == "classification":
        scoring = "accuracy"
    else:
        scoring = "neg_mean_squared_error"

    # Objective function
    def objective(trial: optuna.Trial) -> float:
        """Objective function for hyperparameter optimization."""
        if model_type == "random_forest":
            n_estimators = trial.suggest_int("n_estimators", 10, 200)
            max_depth = trial.suggest_int("max_depth", 2, 20)
            min_samples_split = trial.suggest_int("min_samples_split", 2, 10)
            min_samples_leaf = trial.suggest_int("min_samples_leaf", 1, 5)

            if task_type == "classification":
                model = RandomForestClassifier(
                    n_estimators=n_estimators,
                    max_depth=max_depth,
                    min_samples_split=min_samples_split,
                    min_samples_leaf=min_samples_leaf,
                    random_state=42,
                    n_jobs=-1,
                )
            else:
                model = RandomForestRegressor(
                    n_estimators=n_estimators,
                    max_depth=max_depth,
                    min_samples_split=min_samples_split,
                    min_samples_leaf=min_samples_leaf,
                    random_state=42,
                    n_jobs=-1,
                )

        elif model_type == "gradient_boosting":
            learning_rate = trial.suggest_float("learning_rate", 0.01, 0.3)
            n_estimators = trial.suggest_int("n_estimators", 10, 200)
            max_depth = trial.suggest_int("max_depth", 2, 10)
            subsample = trial.suggest_float("subsample", 0.5, 1.0)

            if task_type == "classification":
                model = GradientBoostingClassifier(
                    learning_rate=learning_rate,
                    n_estimators=n_estimators,
                    max_depth=max_depth,
                    subsample=subsample,
                    random_state=42,
                )
            else:
                model = GradientBoostingRegressor(
                    learning_rate=learning_rate,
                    n_estimators=n_estimators,
                    max_depth=max_depth,
                    subsample=subsample,
                    random_state=42,
                )

        elif model_type == "xgboost":
            learning_rate = trial.suggest_float("learning_rate", 0.01, 0.3)
            n_estimators = trial.suggest_int("n_estimators", 10, 200)
            max_depth = trial.suggest_int("max_depth", 2, 10)
            subsample = trial.suggest_float("subsample", 0.5, 1.0)
            colsample_bytree = trial.suggest_float("colsample_bytree", 0.5, 1.0)
            reg_alpha = trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True)
            reg_lambda = trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True)

            if task_type == "classification":
                model = XGBClassifier(
                    learning_rate=learning_rate,
                    n_estimators=n_estimators,
                    max_depth=max_depth,
                    subsample=subsample,
                    colsample_bytree=colsample_bytree,
                    reg_alpha=reg_alpha,
                    reg_lambda=reg_lambda,
                    use_label_encoder=False,
                    eval_metric="logloss",
                    random_state=42,
                    n_jobs=-1,
                )
            else:
                model = XGBRegressor(
                    learning_rate=learning_rate,
                    n_estimators=n_estimators,
                    max_depth=max_depth,
                    subsample=subsample,
                    colsample_bytree=colsample_bytree,
                    reg_alpha=reg_alpha,
                    reg_lambda=reg_lambda,
                    random_state=42,
                    n_jobs=-1,
                )

        else:
            raise ValueError(f"Unknown model_type: {model_type}")

        # Cross-validation score
        scores = cross_val_score(model, X, y, cv=cv_folds, scoring=scoring, n_jobs=-1)
        return float(scores.mean())

    # Run Optuna study
    sampler = TPESampler(seed=42)
    pruner = MedianPruner()
    study = optuna.create_study(
        direction="maximize",
        sampler=sampler,
        pruner=pruner,
    )
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    return {
        "best_params": study.best_params,
        "best_score": float(study.best_value),
        "n_trials": n_trials,
        "model_type": model_type,
        "task_type": task_type,
        "scoring": scoring,
    }
