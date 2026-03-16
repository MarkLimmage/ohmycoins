import os
from typing import Any

import mlflow
import pandas as pd  # type: ignore

from app.core.config import settings
from app.services.agent.execution import SandboxExecutor
from app.services.lab.pipeline_manager import PipelineManager


async def run_code_in_dagger(
    session_id: str,
    code: str,
    mv_name: str | None = None,
    data_path: str | None = None,
    run_name: str = "dagger_execution",
) -> dict[str, Any]:
    """
    Executes code in Dagger sandbox with MLflow tracking.
    Enforces Phase 5: Hardening (Timeout, Limits via Executor) and Phase 4: MLflow Logging.

    Args:
        session_id: Unique session identifier
        code: Python script content
        mv_name: Optional Materialized View to use as data source
        data_path: Optional direct path to parquet file (overrides mv_name if both provided)
        run_name: Name for MLflow run

    Returns:
        Dict with stdout, stderr, artifact_paths, status
    """

    # Configure MLflow
    mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)

    # 1. Data Pipeline
    pipeline = PipelineManager(session_id)
    final_data_path = None

    # Start MLflow run context
    # We wrap everything in a run to capture data failures too
    with mlflow.start_run(run_name=run_name):
        mlflow.log_param("session_id", session_id)
        if mv_name:
            mlflow.log_param("mv_name", mv_name)

        try:
            # Determine data source
            if data_path:
                final_data_path = data_path
            elif mv_name:
                final_data_path = pipeline.export_mv_to_parquet(mv_name)

            # Check for insufficient data if a path was resolved
            if final_data_path:
                if not os.path.exists(final_data_path) or os.path.getsize(final_data_path) == 0:
                    raise ValueError("Insufficient Data: Parquet file is empty or missing")

                # thorough check
                try:
                    df = pd.read_parquet(final_data_path)
                    if df.empty:
                        raise ValueError("Insufficient Data: DataFrame is empty")
                    mlflow.log_metric("input_rows", len(df))
                except Exception as e:
                    raise ValueError(f"Insufficient Data: Failed to read parquet: {e}")

        except Exception as e:
            # Critical Failure - Log and Return
            mlflow.set_tag("status", "FAILED_DATA_PIPELINE")
            try:
                 mlflow.log_text(str(e), "error.txt")
            except Exception:
                 pass # failed to log

            return {
                "status": "error",
                "message": f"Data Pipeline Failed: {str(e)}",
                "stdout": "",
                "stderr": str(e),
            }

        # 2. Execution (Phase 1 & 5)
        # SandboxExecutor uses DaggerExecutor which enforces 300s timeout (Phase 5.1)
        executor = SandboxExecutor()
        output_dir = os.path.join(pipeline.session_dir, "artifacts")

        try:
            result = await executor.execute_code(code, final_data_path, output_dir)

            # Log execution logs
            mlflow.log_text(result.get("stdout", ""), "stdout.txt")
            mlflow.log_text(result.get("stderr", ""), "stderr.txt")

            if result.get("status") == "success":
                mlflow.set_tag("status", "SUCCESS")
                # Log generated artifacts (Phase 1.3)
                artifact_paths = result.get("artifact_paths", [])
                for artifact in artifact_paths:
                    if os.path.exists(artifact):
                        mlflow.log_artifact(artifact)

                return result
            else:
                mlflow.set_tag("status", "FAILED_EXECUTION")
                mlflow.log_text(result.get("message", ""), "error.txt")
                return result

        except Exception as e:
            mlflow.set_tag("status", "FAILED_SYSTEM_ERROR")
            mlflow.log_text(str(e), "system_error.txt")
            return {
                "status": "error",
                "message": f"System Error: {str(e)}",
                "stdout": "",
                "stderr": str(e),
            }
