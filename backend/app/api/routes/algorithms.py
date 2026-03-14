import json
import logging
from typing import Any

import mlflow
from fastapi import APIRouter, Depends, HTTPException
from mlflow.exceptions import RestException
from mlflow.tracking import MlflowClient
from pydantic import BaseModel
from sqlmodel import Session

from app.api.deps import get_current_active_user, get_db
from app.models import Algorithm, User

router = APIRouter()
logger = logging.getLogger(__name__)

# Schema for Request Body
class PromotionRequest(BaseModel):
    mlflow_run_id: str
    algorithm_name: str
    signal_type: str

# Schema for Response Data
class AlgorithmDataResponse(BaseModel):
    algorithm_id: str
    name: str
    state: str

class PromotionResponse(BaseModel):
    status: str
    message: str
    data: AlgorithmDataResponse

@router.post("/promote", response_model=PromotionResponse, status_code=201)
def promote_algorithm(
    request: PromotionRequest,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Promote an algorithm from Lab (MLflow Run) to Floor (Algorithm Registry).
    """
    # Configure MLflow
    # In production, this URI should come from settings
    mlflow_tracking_uri = "http://localhost:5000"
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    client = MlflowClient()
    
    # 1. Validate MLflow Run exists
    try:
        run = client.get_run(request.mlflow_run_id)
        if not run:
             raise HTTPException(status_code=404, detail=f"MLflow run_id {request.mlflow_run_id} not found in local registry.")
    except RestException as e:
        if e.error_code == "RESOURCE_DOES_NOT_EXIST":
             raise HTTPException(status_code=404, detail=f"MLflow run_id {request.mlflow_run_id} not found in local registry.")
        logger.error(f"MLflow RestException: {e}")
        # If MLflow is down, we should probably fail 500
        raise HTTPException(status_code=503, detail="MLflow Tracking Server unavailable.")
    except Exception as e:
        logger.error(f"Error connecting to MLflow: {e}")
        # Identify if it's a connection error
        if "connection refused" in str(e).lower() or "max retries exceeded" in str(e).lower():
             raise HTTPException(status_code=503, detail="MLflow Tracking Server unavailable.")
        raise HTTPException(status_code=404, detail=f"MLflow run_id {request.mlflow_run_id} not found or error accessing registry. {str(e)}")

    # 2. Register Model in MLflow Registry
    # We attempt to register the model artifact. 
    # Standard Dagger/Lab workflow should log model to "model" path.
    model_uri = f"runs:/{request.mlflow_run_id}/model"
    
    try:
        # Register model
        logger.info(f"Registering model {request.algorithm_name} from {model_uri}")
        model_version = mlflow.register_model(model_uri, request.algorithm_name)
        
        # Transition to Staging
        client.transition_model_version_stage(
            name=request.algorithm_name,
            version=model_version.version,
            stage="Staging"
        )
    except Exception as e:
        logger.warning(f"MLflow Registration Warning: {e}")
        # We proceed even if registration fails (e.g. model already exists or artifact missing), 
        # but we log it. The main goal is creating the Algorithm record.
        # However, if 'model' artifact is missing, maybe we should warn better.

    # 3. Create Algorithm Record in Postgres
    
    # Check if algorithm name already used by this user? 
    # Providing strict contract implies we just create it. 
    
    config = {
        "mlflow_run_id": request.mlflow_run_id,
        "signal_type": request.signal_type,
        "source": "lab_promotion",
        "mlflow_uri": model_uri
    }
    
    new_algo = Algorithm(
        name=request.algorithm_name,
        algorithm_type="ml_model",
        version="1.0.0", 
        status="inactive", 
        configuration_json=json.dumps(config),
        created_by=current_user.id
    )
    
    session.add(new_algo)
    session.commit()
    session.refresh(new_algo)
    
    return {
        "status": "success",
        "message": "Algorithm successfully registered to the Floor.",
        "data": {
            "algorithm_id": str(new_algo.id),
            "name": new_algo.name,
            "state": "INACTIVE"
        }
    }
