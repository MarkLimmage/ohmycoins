import uuid
from typing import Any
import datetime
from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    StrategyPromotion,
    StrategyPromotionCreate,
    StrategyPromotionUpdate,
    StrategyPromotionPublic,
    Algorithm
)

router = APIRouter()

@router.post("/", response_model=StrategyPromotionPublic)
def request_promotion(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    promotion_in: StrategyPromotionCreate
) -> Any:
    """
    Request promotion of a strategy (Algorithm) from Lab to Floor.
    """
    # Verify algorithm exists and belongs to user (or user is superuser)
    algorithm = session.get(Algorithm, promotion_in.algorithm_id)
    if not algorithm:
         raise HTTPException(status_code=404, detail="Algorithm not found")
    
    # Check if user owns the algorithm
    if algorithm.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")

    # Check for existing pending promotion
    statement = select(StrategyPromotion).where(
        StrategyPromotion.algorithm_id == promotion_in.algorithm_id,
        StrategyPromotion.status == "pending"
    )
    existing_promotion = session.exec(statement).first()
    if existing_promotion:
        raise HTTPException(status_code=400, detail="A pending promotion request already exists for this algorithm")

    promotion = StrategyPromotion.model_validate(
        promotion_in, 
        update={"created_by": current_user.id}
    )
    session.add(promotion)
    session.commit()
    session.refresh(promotion)
    return promotion

@router.get("/", response_model=list[StrategyPromotionPublic])
def list_promotions(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    List strategy promotion requests.
    """
    if current_user.is_superuser:
        statement = select(StrategyPromotion)
    else:
        statement = select(StrategyPromotion).where(StrategyPromotion.created_by == current_user.id)
    
    if status:
         statement = statement.where(StrategyPromotion.status == status)

    statement = statement.offset(skip).limit(limit)
    promotions = session.exec(statement).all()
    return promotions

@router.get("/{id}", response_model=StrategyPromotionPublic)
def get_promotion(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID
) -> Any:
    """
    Get a specific promotion request.
    """
    promotion = session.get(StrategyPromotion, id)
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion request not found")
    
    if not current_user.is_superuser and promotion.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough privileges")
        
    return promotion

@router.patch("/{id}", response_model=StrategyPromotionPublic)
def review_promotion(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    review_in: StrategyPromotionUpdate
) -> Any:
    """
    Review a promotion request (Approve/Reject).
    Requires Architect (Superuser) privileges.
    """
    # Authorization check - strict: only superusers can approve/reject
    if not current_user.is_superuser:
         raise HTTPException(status_code=403, detail="Only the Architect can review promotions")

    promotion = session.get(StrategyPromotion, id)
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion request not found")

    if promotion.status != "pending":
         raise HTTPException(status_code=400, detail="Can only review pending requests")

    update_data = review_in.model_dump(exclude_unset=True)
    update_data["reviewed_by"] = current_user.id
    update_data["reviewed_at"] = datetime.datetime.now(timezone.utc)
    
    promotion.sqlmodel_update(update_data)
    session.add(promotion)
    session.commit()
    session.refresh(promotion)
    
    # If approved, update the Algorithm status
    if promotion.status == "approved":
        algorithm = session.get(Algorithm, promotion.algorithm_id)
        if algorithm:
            algorithm.status = "active" 
            session.add(algorithm)
            session.commit()

    return promotion
