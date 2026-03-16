# mypy: ignore-errors
"""
Model Training Tools - Week 5-6 Implementation (Updated Phase 5)

Tools for ModelTrainingAgent to train machine learning models on cryptocurrency data.
Phase 5: Rerouted to Dagger sandbox execution.
"""
import json
import logging
import os
import tempfile
from typing import Any, Literal

import joblib
import mlflow
import numpy as np
import pandas as pd
from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler

from app.core.config import settings
from app.services.dagger_wrapper import DaggerExecutor
from app.services.lab.mlflow_service import MLflowService
from app.services.lab.pipeline_manager import PipelineManager

logger = logging.getLogger(__name__)


async def _execute_training_in_dagger(
    task_type: Literal["classification", "regression"],
    session_id: str,
    training_data: pd.DataFrame | None,
    target_column: str,
    feature_columns: list[str] | None,
    model_type: str,
    hyperparameters: dict[str, Any] | None,
    test_size: float,
    random_state: int,
    scale_features: bool,
    validation_strategy: str,
    mv_name: str | None = None,
) -> dict[str, Any]:
    """
    Internal helper to execute training via Dagger.
    Uses PipelineManager for caching and MLflowService for lifecycle tagging.
    """
    # 1. Resolve Data Path (PipelineManager / Local Cache)
    pipeline = PipelineManager(session_id)
    data_path = None
    temp_file = None

    try:
        if mv_name:
            # Use cached parquet from Lab pipeline
            data_path = pipeline.export_mv_to_parquet(mv_name)
        elif training_data is not None:
            # Fallback for in-memory dataframe
            temp_file = tempfile.NamedTemporaryFile(suffix=".parquet", delete=False)
            training_data.to_parquet(temp_file.name, index=False)
            temp_file.close() # Close handle so others can read
            data_path = temp_file.name
        else:
            raise ValueError("No data provided (neither mv_name nor training_data)")

        if feature_columns is None:
            # Partial read to get columns if we don't have dataframe loaded
            # Avoiding full read for efficiency
            if training_data is not None:
                cols = training_data.columns
            else:
                # Read parquet schema/columns
                df_schema = pd.read_parquet(data_path, engine='pyarrow').columns
                cols = df_schema
            feature_columns = [col for col in cols if col != target_column]

        # 2. Construct the Training Script
        # We used json.dumps to safely serialize parameters into the script
        script_content = f"""
import json
import os
import joblib
import mlflow
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    mean_absolute_error, mean_squared_error, r2_score
)
from sklearn.ensemble import (
    GradientBoostingClassifier, GradientBoostingRegressor,
    RandomForestClassifier, RandomForestRegressor
)
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.svm import SVC, SVR
from xgboost import XGBClassifier, XGBRegressor

# Parameters
TARGET_COLUMN = "{target_column}"
FEATURE_COLUMNS = {json.dumps(feature_columns)}
MODEL_TYPE = "{model_type}"
HYPERPARAMETERS = {json.dumps(hyperparameters or {})}
TEST_SIZE = {test_size}
RANDOM_STATE = {random_state}
SCALE_FEATURES = {scale_features}
VALIDATION_STRATEGY = "{validation_strategy}"
TASK_TYPE = "{task_type}"

def train():
    print("Loading data...")
    # The file is mounted at /workspace/training_data.parquet by DaggerExecutor
    df = pd.read_parquet("/workspace/training_data.parquet")

    # Ensure columns exist
    missing_cols = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing feature columns: {{missing_cols}}")
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Missing target column: {{TARGET_COLUMN}}")

    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].copy()

    # Handle missing values - simple imputation
    X = X.fillna(0)

    # Split Data
    if VALIDATION_STRATEGY in ["time_series", "expanding_window"]:
        tscv = TimeSeriesSplit(n_splits=5)
        splits = list(tscv.split(X))
        train_idx, test_idx = splits[-1]
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    else:
        if TASK_TYPE == "classification":
            stratify = y
        else:
            stratify = None

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=stratify
        )

    # Scale
    scaler = None
    if SCALE_FEATURES:
        scaler = StandardScaler()
        X_train = pd.DataFrame(scaler.fit_transform(X_train), columns=FEATURE_COLUMNS)
        X_test = pd.DataFrame(scaler.transform(X_test), columns=FEATURE_COLUMNS)

    # Instantiate Model
    model = None
    if MODEL_TYPE == "random_forest":
        cls = RandomForestClassifier if TASK_TYPE == "classification" else RandomForestRegressor
        model = cls(random_state=RANDOM_STATE, **HYPERPARAMETERS)
    elif MODEL_TYPE == "xgboost":
        cls = XGBClassifier if TASK_TYPE == "classification" else XGBRegressor
        model = cls(random_state=RANDOM_STATE, **HYPERPARAMETERS)
    elif MODEL_TYPE == "gradient_boosting":
        cls = GradientBoostingClassifier if TASK_TYPE == "classification" else GradientBoostingRegressor
        model = cls(random_state=RANDOM_STATE, **HYPERPARAMETERS)
    elif MODEL_TYPE == "decision_tree":
        cls = DecisionTreeClassifier if TASK_TYPE == "classification" else DecisionTreeRegressor
        model = cls(random_state=RANDOM_STATE, **HYPERPARAMETERS)
    elif MODEL_TYPE == "svm":
        cls = SVC if TASK_TYPE == "classification" else SVR
        kwargs = {{"probability": True}} if TASK_TYPE == "classification" else {{}}
        model = cls(random_state=RANDOM_STATE, **kwargs, **HYPERPARAMETERS)
    elif MODEL_TYPE == "logistic_regression":
        model = LogisticRegression(random_state=RANDOM_STATE, **HYPERPARAMETERS)
    elif MODEL_TYPE == "linear_regression":
        model = LinearRegression(**HYPERPARAMETERS)
    elif MODEL_TYPE == "ridge":
        model = Ridge(**HYPERPARAMETERS)
    elif MODEL_TYPE == "lasso":
        model = Lasso(**HYPERPARAMETERS)
    else:
        raise ValueError(f"Unknown model type: {{MODEL_TYPE}}")

    print(f"Training {{MODEL_TYPE}} for {{TASK_TYPE}}...")
    model.fit(X_train, y_train)

    # Predict
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    # Metrics
    metrics = {{"train": {{}}, "test": {{}}}}

    if TASK_TYPE == "classification":
        metrics["train"]["accuracy"] = accuracy_score(y_train, y_pred_train)
        metrics["test"]["accuracy"] = accuracy_score(y_test, y_pred_test)

        # Calculate F1, Precision, Recall with zero_division=0 to avoid warnings
        metrics["test"]["f1"] = f1_score(y_test, y_pred_test, average="weighted", zero_division=0)
        metrics["train"]["f1"] = f1_score(y_train, y_pred_train, average="weighted", zero_division=0)

        metrics["test"]["precision"] = precision_score(y_test, y_pred_test, average="weighted", zero_division=0)
        metrics["train"]["precision"] = precision_score(y_train, y_pred_train, average="weighted", zero_division=0)

        metrics["test"]["recall"] = recall_score(y_test, y_pred_test, average="weighted", zero_division=0)
        metrics["train"]["recall"] = recall_score(y_train, y_pred_train, average="weighted", zero_division=0)

    else:
        metrics["train"]["rmse"] = np.sqrt(mean_squared_error(y_train, y_pred_train))
        metrics["test"]["rmse"] = np.sqrt(mean_squared_error(y_test, y_pred_test))
        metrics["test"]["r2"] = r2_score(y_test, y_pred_test)
        metrics["train"]["r2"] = r2_score(y_train, y_pred_train)
        metrics["test"]["mae"] = mean_absolute_error(y_test, y_pred_test)
        metrics["train"]["mae"] = mean_absolute_error(y_train, y_pred_train)

    # Save Artifacts
    if not os.path.exists("/workspace/out"):
        os.makedirs("/workspace/out")

    joblib.dump(model, "/workspace/out/model.joblib")
    if scaler:
        joblib.dump(scaler, "/workspace/out/scaler.joblib")

    with open("/workspace/out/metrics.json", "w") as f:
        json.dump(metrics, f)

    print("Training complete.")

if __name__ == "__main__":
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", ""))
    # Optional: Start MLflow run inside container
    train()
"""

        # 3. Request Dagger Execution
        # We pass data_filename="training_data.parquet" to match script expectation

        # MLflow Tracking Context
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)

        # Determine Run Name
        run_name = f"{task_type}_{model_type}_{session_id[:8]}"

        # Use context manager for auto-termination of runs
        with mlflow.start_run(run_name=run_name) as run:
            # Log Parameters
            mlflow.log_params({
                "task_type": task_type,
                "model_type": model_type,
                "test_size": test_size,
                "validation_strategy": validation_strategy,
                "session_id": session_id,
            })
            if hyperparameters:
                mlflow.log_params(hyperparameters)
            if mv_name:
                mlflow.log_param("mv_name", mv_name)

            with tempfile.TemporaryDirectory() as temp_dir:
                executor = DaggerExecutor()
                result = await executor.execute_script(
                    script_content=script_content,
                    data_path=data_path,
                    output_dir=temp_dir,
                    mlflow_tracking_uri=settings.MLFLOW_TRACKING_URI,
                )

                # Clean up temp data file ONLY if we created it (fallback mode)
                if temp_file and os.path.exists(data_path):
                    os.remove(data_path)

                if result.get("status") == "error":
                    logger.error(f"Dagger execution failed: {result.get('stderr')}")
                    mlflow.set_tag("status", "FAILED")
                    # Log execution log as artifact for debugging
                    with open(os.path.join(temp_dir, "dagger_error.log"), "w") as f:
                        f.write(result.get("stderr", ""))
                    mlflow.log_artifact(os.path.join(temp_dir, "dagger_error.log"))
                    raise RuntimeError(f"Model training failed in Dagger execution: {result.get('stderr')}")

                # 4. Load Artifacts & Metrics
                model_path = os.path.join(temp_dir, "model.joblib")
                scaler_path = os.path.join(temp_dir, "scaler.joblib")
                metrics_path = os.path.join(temp_dir, "metrics.json")

                if not os.path.exists(model_path):
                    mlflow.set_tag("status", "MISSING_ARTIFACTS")
                    raise FileNotFoundError("Model artifact not found after Dagger execution.")

                model = joblib.load(model_path)
                scaler = joblib.load(scaler_path) if os.path.exists(scaler_path) else None

                if os.path.exists(metrics_path):
                    with open(metrics_path) as f:
                        metrics = json.load(f)
                else:
                    metrics = {}

                # 5. Log Metrics & Tag Lifecycle (Phase 5 Requirement)
                # Flatten metrics for MLflow logging
                for split, split_metrics in metrics.items():
                    for name, value in split_metrics.items():
                        mlflow.log_metric(f"{split}_{name}", value)

                # Log key metrics at root level for Service check
                if "test" in metrics:
                    if "accuracy" in metrics["test"]:
                        mlflow.log_metric("accuracy", metrics["test"]["accuracy"])
                    if "f1" in metrics["test"]:
                        mlflow.log_metric("f1_score", metrics["test"]["f1"])

                # Use MLflowService to tag lifecycle based on rules
                mlflow_service = MLflowService()
                lifecycle_status = mlflow_service.tag_model_lifecycle(run.info.run_id)

                # Log artifacts to MLflow
                mlflow.log_artifact(model_path, artifact_path="model")
                if scaler and os.path.exists(scaler_path):
                    mlflow.log_artifact(scaler_path, artifact_path="scaler")

                return {
                    "model": model,
                    "scaler": scaler,
                    "feature_columns": feature_columns,
                    "metrics": metrics,
                    "model_type": model_type,
                    "hyperparameters": hyperparameters,
                    "validation_strategy": validation_strategy,
                    "run_id": run.info.run_id,
                    "lifecycle_status": lifecycle_status
                }
    except Exception as e:
        # Ensure we don't leave zombie runs if not handled by context manager
        # Context manager handles end_run, but we might want to log the exception
        logger.error(f"Error in MLflow run: {e}")
        raise e



async def train_classification_model(
    session_id: str,
    target_column: str,
    training_data: pd.DataFrame | None = None,
    mv_name: str | None = None,
    feature_columns: list[str] | None = None,
    model_type: Literal[
        "random_forest",
        "logistic_regression",
        "decision_tree",
        "gradient_boosting",
        "svm",
        "xgboost",
    ] = "random_forest",
    hyperparameters: dict[str, Any] | None = None,
    test_size: float = 0.2,
    random_state: int = 42,
    scale_features: bool = True,
    validation_strategy: Literal[
        "random", "time_series", "expanding_window"
    ] = "random",
) -> dict[str, Any]:
    """
    Train a classification model using Dagger sandbox.
    Phase 5: Supports Parquet Row-Count Caching via mv_name.
    """
    return await _execute_training_in_dagger(
        task_type="classification",
        session_id=session_id,
        training_data=training_data,
        mv_name=mv_name,
        target_column=target_column,
        feature_columns=feature_columns,
        model_type=model_type,
        hyperparameters=hyperparameters,
        test_size=test_size,
        random_state=random_state,
        scale_features=scale_features,
        validation_strategy=validation_strategy,
    )


async def train_regression_model(
    session_id: str,
    target_column: str,
    training_data: pd.DataFrame | None = None,
    mv_name: str | None = None,
    feature_columns: list[str] | None = None,
    model_type: Literal[
        "random_forest",
        "linear_regression",
        "ridge",
        "lasso",
        "decision_tree",
        "gradient_boosting",
        "svr",
        "xgboost",
    ] = "random_forest",
    hyperparameters: dict[str, Any] | None = None,
    test_size: float = 0.2,
    random_state: int = 42,
    scale_features: bool = True,
    validation_strategy: Literal[
        "random", "time_series", "expanding_window"
    ] = "random",
) -> dict[str, Any]:
    """
    Train a regression model using Dagger sandbox.
    Phase 5: Supports Parquet Row-Count Caching via mv_name.
    """
    return await _execute_training_in_dagger(
        task_type="regression",
        session_id=session_id,
        training_data=training_data,
        mv_name=mv_name,
        target_column=target_column,
        feature_columns=feature_columns,
        model_type=model_type,
        hyperparameters=hyperparameters,
        test_size=test_size,
        random_state=random_state,
        scale_features=scale_features,
        validation_strategy=validation_strategy,
    )


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

    NOTE: Currently runs locally. Future consideration: move to Dagger.

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
            scaler.fit_transform(X), columns=feature_columns, index=X.index
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


def serialize_model_to_disk(
    model: Any,
    session_id: str,
    model_name: str,
    scaler: Any | None = None,
    metadata: dict[str, Any] | None = None,
    base_dir: str = "/data/agent_artifacts",
) -> dict[str, str]:
    """Serialize a trained model to disk using joblib."""
    import json
    from pathlib import Path

    import joblib

    artifact_dir = Path(base_dir) / session_id
    artifact_dir.mkdir(parents=True, exist_ok=True)

    model_path = artifact_dir / f"{model_name}.joblib"
    joblib.dump(model, model_path)

    result = {"model_path": str(model_path)}

    if scaler is not None:
        scaler_path = artifact_dir / f"{model_name}_scaler.joblib"
        joblib.dump(scaler, scaler_path)
        result["scaler_path"] = str(scaler_path)

    if metadata:
        meta_path = artifact_dir / f"{model_name}_metadata.json"
        meta_path.write_text(json.dumps(metadata, default=str))
        result["metadata_path"] = str(meta_path)

    return result
