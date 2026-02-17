# mypy: ignore-errors
"""
Model Training Tools - Week 5-6 Implementation

Tools for ModelTrainingAgent to train machine learning models on cryptocurrency data.
"""

from datetime import datetime
from typing import Any, Literal
import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.svm import SVC, SVR
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


def train_classification_model(
    training_data: pd.DataFrame,
    target_column: str,
    feature_columns: list[str] | None = None,
    model_type: Literal[
        "random_forest", 
        "logistic_regression", 
        "decision_tree", 
        "gradient_boosting",
        "svm"
    ] = "random_forest",
    hyperparameters: dict[str, Any] | None = None,
    test_size: float = 0.2,
    random_state: int = 42,
    scale_features: bool = True,
) -> dict[str, Any]:
    """
    Train a classification model on cryptocurrency data.
    
    Args:
        training_data: DataFrame containing features and target
        target_column: Name of the target column to predict
        feature_columns: List of feature column names. If None, uses all except target
        model_type: Type of classification model to train
        hyperparameters: Optional dictionary of model hyperparameters
        test_size: Fraction of data to use for testing (0.0-1.0)
        random_state: Random seed for reproducibility
        scale_features: Whether to scale features using StandardScaler
    
    Returns:
        Dictionary containing:
        - model: Trained model object
        - scaler: StandardScaler object if scale_features=True, else None
        - feature_columns: List of feature columns used
        - metrics: Dictionary of performance metrics
        - train_size: Number of training samples
        - test_size: Number of test samples
    """
    # Prepare features and target
    if feature_columns is None:
        feature_columns = [col for col in training_data.columns if col != target_column]
    
    X = training_data[feature_columns].copy()
    y = training_data[target_column].copy()
    
    # Handle missing values
    X = X.fillna(X.mean())
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    # Scale features if requested
    scaler = None
    if scale_features:
        scaler = StandardScaler()
        X_train = pd.DataFrame(
            scaler.fit_transform(X_train),
            columns=feature_columns,
            index=X_train.index
        )
        X_test = pd.DataFrame(
            scaler.transform(X_test),
            columns=feature_columns,
            index=X_test.index
        )
    
    # Initialize model with hyperparameters
    hyperparams = hyperparameters or {}
    
    if model_type == "random_forest":
        model = RandomForestClassifier(
            random_state=random_state,
            n_estimators=hyperparams.get("n_estimators", 100),
            max_depth=hyperparams.get("max_depth", None),
            min_samples_split=hyperparams.get("min_samples_split", 2),
            min_samples_leaf=hyperparams.get("min_samples_leaf", 1),
            **{k: v for k, v in hyperparams.items() if k not in [
                "n_estimators", "max_depth", "min_samples_split", "min_samples_leaf"
            ]}
        )
    elif model_type == "logistic_regression":
        model = LogisticRegression(
            random_state=random_state,
            max_iter=hyperparams.get("max_iter", 1000),
            C=hyperparams.get("C", 1.0),
            **{k: v for k, v in hyperparams.items() if k not in ["max_iter", "C"]}
        )
    elif model_type == "decision_tree":
        model = DecisionTreeClassifier(
            random_state=random_state,
            max_depth=hyperparams.get("max_depth", None),
            min_samples_split=hyperparams.get("min_samples_split", 2),
            **{k: v for k, v in hyperparams.items() if k not in ["max_depth", "min_samples_split"]}
        )
    elif model_type == "gradient_boosting":
        model = GradientBoostingClassifier(
            random_state=random_state,
            n_estimators=hyperparams.get("n_estimators", 100),
            learning_rate=hyperparams.get("learning_rate", 0.1),
            max_depth=hyperparams.get("max_depth", 3),
            **{k: v for k, v in hyperparams.items() if k not in [
                "n_estimators", "learning_rate", "max_depth"
            ]}
        )
    elif model_type == "svm":
        model = SVC(
            random_state=random_state,
            C=hyperparams.get("C", 1.0),
            kernel=hyperparams.get("kernel", "rbf"),
            probability=True,
            **{k: v for k, v in hyperparams.items() if k not in ["C", "kernel"]}
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    # Train model
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    # Get probability predictions for ROC-AUC (if binary classification)
    try:
        y_pred_proba_test = model.predict_proba(X_test)[:, 1]
        roc_auc = roc_auc_score(y_test, y_pred_proba_test)
    except (AttributeError, IndexError):
        roc_auc = None
    
    # Calculate metrics
    metrics = {
        "train": {
            "accuracy": float(accuracy_score(y_train, y_pred_train)),
            "precision": float(precision_score(y_train, y_pred_train, average="weighted", zero_division=0)),
            "recall": float(recall_score(y_train, y_pred_train, average="weighted", zero_division=0)),
            "f1": float(f1_score(y_train, y_pred_train, average="weighted", zero_division=0)),
        },
        "test": {
            "accuracy": float(accuracy_score(y_test, y_pred_test)),
            "precision": float(precision_score(y_test, y_pred_test, average="weighted", zero_division=0)),
            "recall": float(recall_score(y_test, y_pred_test, average="weighted", zero_division=0)),
            "f1": float(f1_score(y_test, y_pred_test, average="weighted", zero_division=0)),
        },
    }
    
    if roc_auc is not None:
        metrics["test"]["roc_auc"] = float(roc_auc)
    
    return {
        "model": model,
        "scaler": scaler,
        "feature_columns": feature_columns,
        "metrics": metrics,
        "train_size": len(X_train),
        "test_size": len(X_test),
        "model_type": model_type,
        "hyperparameters": hyperparams,
    }


def train_regression_model(
    training_data: pd.DataFrame,
    target_column: str,
    feature_columns: list[str] | None = None,
    model_type: Literal[
        "random_forest",
        "linear_regression",
        "ridge",
        "lasso",
        "decision_tree",
        "gradient_boosting",
        "svr"
    ] = "random_forest",
    hyperparameters: dict[str, Any] | None = None,
    test_size: float = 0.2,
    random_state: int = 42,
    scale_features: bool = True,
) -> dict[str, Any]:
    """
    Train a regression model on cryptocurrency data.
    
    Args:
        training_data: DataFrame containing features and target
        target_column: Name of the target column to predict
        feature_columns: List of feature column names. If None, uses all except target
        model_type: Type of regression model to train
        hyperparameters: Optional dictionary of model hyperparameters
        test_size: Fraction of data to use for testing (0.0-1.0)
        random_state: Random seed for reproducibility
        scale_features: Whether to scale features using StandardScaler
    
    Returns:
        Dictionary containing:
        - model: Trained model object
        - scaler: StandardScaler object if scale_features=True, else None
        - feature_columns: List of feature columns used
        - metrics: Dictionary of performance metrics
        - train_size: Number of training samples
        - test_size: Number of test samples
    """
    # Prepare features and target
    if feature_columns is None:
        feature_columns = [col for col in training_data.columns if col != target_column]
    
    X = training_data[feature_columns].copy()
    y = training_data[target_column].copy()
    
    # Handle missing values
    X = X.fillna(X.mean())
    y = y.fillna(y.mean())
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    # Scale features if requested
    scaler = None
    if scale_features:
        scaler = StandardScaler()
        X_train = pd.DataFrame(
            scaler.fit_transform(X_train),
            columns=feature_columns,
            index=X_train.index
        )
        X_test = pd.DataFrame(
            scaler.transform(X_test),
            columns=feature_columns,
            index=X_test.index
        )
    
    # Initialize model with hyperparameters
    hyperparams = hyperparameters or {}
    
    if model_type == "random_forest":
        model = RandomForestRegressor(
            random_state=random_state,
            n_estimators=hyperparams.get("n_estimators", 100),
            max_depth=hyperparams.get("max_depth", None),
            min_samples_split=hyperparams.get("min_samples_split", 2),
            min_samples_leaf=hyperparams.get("min_samples_leaf", 1),
            **{k: v for k, v in hyperparams.items() if k not in [
                "n_estimators", "max_depth", "min_samples_split", "min_samples_leaf"
            ]}
        )
    elif model_type == "linear_regression":
        model = LinearRegression(
            **hyperparams
        )
    elif model_type == "ridge":
        model = Ridge(
            random_state=random_state,
            alpha=hyperparams.get("alpha", 1.0),
            **{k: v for k, v in hyperparams.items() if k != "alpha"}
        )
    elif model_type == "lasso":
        model = Lasso(
            random_state=random_state,
            alpha=hyperparams.get("alpha", 1.0),
            **{k: v for k, v in hyperparams.items() if k != "alpha"}
        )
    elif model_type == "decision_tree":
        model = DecisionTreeRegressor(
            random_state=random_state,
            max_depth=hyperparams.get("max_depth", None),
            min_samples_split=hyperparams.get("min_samples_split", 2),
            **{k: v for k, v in hyperparams.items() if k not in ["max_depth", "min_samples_split"]}
        )
    elif model_type == "gradient_boosting":
        model = GradientBoostingRegressor(
            random_state=random_state,
            n_estimators=hyperparams.get("n_estimators", 100),
            learning_rate=hyperparams.get("learning_rate", 0.1),
            max_depth=hyperparams.get("max_depth", 3),
            **{k: v for k, v in hyperparams.items() if k not in [
                "n_estimators", "learning_rate", "max_depth"
            ]}
        )
    elif model_type == "svr":
        model = SVR(
            C=hyperparams.get("C", 1.0),
            kernel=hyperparams.get("kernel", "rbf"),
            **{k: v for k, v in hyperparams.items() if k not in ["C", "kernel"]}
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    # Train model
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    # Calculate metrics
    metrics = {
        "train": {
            "mse": float(mean_squared_error(y_train, y_pred_train)),
            "rmse": float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
            "mae": float(mean_absolute_error(y_train, y_pred_train)),
            "r2": float(r2_score(y_train, y_pred_train)),
        },
        "test": {
            "mse": float(mean_squared_error(y_test, y_pred_test)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
            "mae": float(mean_absolute_error(y_test, y_pred_test)),
            "r2": float(r2_score(y_test, y_pred_test)),
        },
    }
    
    return {
        "model": model,
        "scaler": scaler,
        "feature_columns": feature_columns,
        "metrics": metrics,
        "train_size": len(X_train),
        "test_size": len(X_test),
        "model_type": model_type,
        "hyperparameters": hyperparams,
    }


def cross_validate_model(
    training_data: pd.DataFrame,
    target_column: str,
    feature_columns: list[str] | None = None,
    model_type: Literal[
        "random_forest_classifier",
        "random_forest_regressor",
        "logistic_regression",
        "linear_regression",
    ] = "random_forest_classifier",
    cv_folds: int = 5,
    scoring: str | None = None,
    random_state: int = 42,
    scale_features: bool = True,
) -> dict[str, Any]:
    """
    Perform cross-validation on a model to estimate performance.
    
    Args:
        training_data: DataFrame containing features and target
        target_column: Name of the target column to predict
        feature_columns: List of feature column names. If None, uses all except target
        model_type: Type of model to cross-validate
        cv_folds: Number of cross-validation folds
        scoring: Scoring metric (e.g., 'accuracy', 'f1', 'roc_auc', 'neg_mean_squared_error')
                If None, uses default for model type
        random_state: Random seed for reproducibility
        scale_features: Whether to scale features using StandardScaler
    
    Returns:
        Dictionary containing:
        - scores: Array of cross-validation scores
        - mean_score: Mean cross-validation score
        - std_score: Standard deviation of cross-validation scores
        - cv_folds: Number of folds used
    """
    # Prepare features and target
    if feature_columns is None:
        feature_columns = [col for col in training_data.columns if col != target_column]
    
    X = training_data[feature_columns].copy()
    y = training_data[target_column].copy()
    
    # Handle missing values
    X = X.fillna(X.mean())
    if "regressor" in model_type or model_type == "linear_regression":
        y = y.fillna(y.mean())
    
    # Scale features if requested
    if scale_features:
        scaler = StandardScaler()
        X = pd.DataFrame(
            scaler.fit_transform(X),
            columns=feature_columns,
            index=X.index
        )
    
    # Initialize model
    if model_type == "random_forest_classifier":
        model = RandomForestClassifier(random_state=random_state, n_estimators=100)
        default_scoring = "accuracy"
    elif model_type == "random_forest_regressor":
        model = RandomForestRegressor(random_state=random_state, n_estimators=100)
        default_scoring = "neg_mean_squared_error"
    elif model_type == "logistic_regression":
        model = LogisticRegression(random_state=random_state, max_iter=1000)
        default_scoring = "accuracy"
    elif model_type == "linear_regression":
        model = LinearRegression()
        default_scoring = "neg_mean_squared_error"
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    scoring = scoring or default_scoring
    
    # Perform cross-validation
    scores = cross_val_score(model, X, y, cv=cv_folds, scoring=scoring)
    
    return {
        "scores": scores.tolist(),
        "mean_score": float(np.mean(scores)),
        "std_score": float(np.std(scores)),
        "cv_folds": cv_folds,
        "scoring": scoring,
        "model_type": model_type,
    }
