import logging

import mlflow

from app.core.config import settings

logger = logging.getLogger(__name__)

class MLflowService:
    """
    Service for managing MLflow interactions and lifecycle tagging.
    Scope: MLflow Lifecycle Tagging
    """

    def __init__(self):
        self.client = mlflow.tracking.MlflowClient(tracking_uri=settings.MLFLOW_TRACKING_URI)

    def tag_model_lifecycle(self, run_id: str) -> str:
        """
        Tags a model run as 'valid' or 'discarded' based on performance metrics.

        Rules:
        - Accuracy < 0.5 OR F1 < 0.3 => lifecycle: discarded
        - Otherwise => lifecycle: valid
        """
        try:
            run = self.client.get_run(run_id)
            metrics = run.data.metrics

            # Default to 0 if metric is missing
            accuracy = metrics.get("accuracy", 0.0)
            f1 = metrics.get("f1_score", 0.0)

            status = "valid"
            if accuracy < 0.5 or f1 < 0.3:
                status = "discarded"

            self.client.set_tag(run_id, "lifecycle", status)
            logger.info(f"Tagged run {run_id} as lifecycle: {status} (acc={accuracy}, f1={f1})")
            return status

        except Exception as e:
            logger.error(f"Failed to tag lifecycle for run {run_id}: {e}")
            return "unknown"
