import logging
import os
import time

import mlflow
import pandas as pd  # type: ignore
from sqlalchemy import text

from app.core.config import settings
from app.core.db import engine

logger = logging.getLogger(__name__)

# Cache configuration
CACHE_DIR = "/tmp/omc_cache"
CACHE_FILE = os.path.join(CACHE_DIR, "training_data.parquet")
CACHE_EXPIRY = 3600  # 1 hour


def export_training_data_to_parquet(force_refresh: bool = False, mlflow_run_id: str | None = None) -> str:
    """
    Queries mv_training_set_v1 and saves the result to a parquet file.
    Implements caching mechanism.
    Tracks generation in MLflow if run_id provided.

    Args:
        force_refresh: If True, ignore cache and regenerate.
        mlflow_run_id: Optional MLflow run ID to log the dataset to.

    Returns:
        The absolute path to the parquet file.
    """
    # 1. Setup Cache Directory
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    cache_valid = False
    if os.path.exists(CACHE_FILE) and not force_refresh:
        # Check staleness
        mod_time = os.path.getmtime(CACHE_FILE)
        if time.time() - mod_time < CACHE_EXPIRY:
            cache_valid = True

    if cache_valid:
        # Keep it simple for logs
        logger.info("Using cached training data from %s", CACHE_FILE)
    else:
        logger.info("Regenerating training data...")
        # Query the database
        # Use a more robust query that handles potential NULLs or type issues if needed
        query = text("SELECT * FROM mv_training_set_v1")

        with engine.connect() as conn:
            df = pd.read_sql(query, conn)

        # Save to parquet
        # Ensure pyarrow or fastparquet is installed (added to pyproject.toml)
        df.to_parquet(CACHE_FILE, index=False)
        logger.info("Saved training data to %s", CACHE_FILE)

    # 2. Log to MLflow if requested
    if mlflow_run_id:
        try:
            # Check if run_id is valid active run or just an ID
            # We assume it's a valid ID passed from a context manager
            client = mlflow.MlflowClient(tracking_uri=settings.MLFLOW_TRACKING_URI)

            # Log the artifact
            client.log_artifact(mlflow_run_id, CACHE_FILE, artifact_path="data")

            # Log params about the dataset
            file_stats = os.stat(CACHE_FILE)
            client.log_param(mlflow_run_id, "training_data_size_bytes", str(file_stats.st_size))
            client.log_param(mlflow_run_id, "training_data_path", CACHE_FILE)

        except Exception as e:
            logger.warning("Failed to log to MLflow: %s", e)

    return os.path.abspath(CACHE_FILE)

