import uuid
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import Algorithm, StrategyPromotion
from tests.utils.utils import get_superuser_token_headers
from tests.utils.user import authentication_token_from_email, create_random_user

def create_algorithm(session: Session, user_id: uuid.UUID) -> Algorithm:
    # Helper to create an algorithm
    algo = Algorithm(
        name="Test Algo",
        algorithm_type="rule_based",
        created_by=user_id,
        status="draft"
    )
    session.add(algo)
    session.commit()
    session.refresh(algo)
    return algo

def test_request_promotion(client: TestClient, session: Session, db: Session) -> None:
    # Create user and login
    user = create_random_user(db)
    user_token_headers = authentication_token_from_email(client=client, email=user.email, db=db)
    
    # Create algo
    algo = create_algorithm(session, user.id)
    
    data = {
        "algorithm_id": str(algo.id),
        "promotion_notes": "Please promote me",
        "performance_snapshot_json": "{}"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/promotions/", 
        headers=user_token_headers, 
        json=data
    )
    
    assert response.status_code == 200
    content = response.json()
    assert content["algorithm_id"] == str(algo.id)
    assert content["status"] == "pending"
    assert content["created_by"] == str(user.id)

def test_approve_promotion(client: TestClient, session: Session, db: Session) -> None:
    # Create user, algo, promotion
    user = create_random_user(db)
    user_token_headers = authentication_token_from_email(client=client, email=user.email, db=db)
    algo = create_algorithm(session, user.id)
    
    # Request promotion
    data = {"algorithm_id": str(algo.id)}
    client.post(
        f"{settings.API_V1_STR}/promotions/", 
        headers=user_token_headers, 
        json=data
    )
    
    # Get created promotion
    promo_stmt = select(StrategyPromotion).where(StrategyPromotion.algorithm_id == algo.id)
    promo = session.exec(promo_stmt).first()
    assert promo is not None
    
    # Login as superuser
    superuser_token_headers = get_superuser_token_headers(client)
    
    # Approve
    review_data = {"status": "approved"}
    response = client.patch(
        f"{settings.API_V1_STR}/promotions/{promo.id}",
        headers=superuser_token_headers,
        json=review_data
    )
    
    assert response.status_code == 200
    content = response.json()
    assert content["status"] == "approved"
    assert content["reviewed_by"] is not None
    
    # Check algo status
    session.refresh(algo)
    assert algo.status == "active"

def test_reject_promotion(client: TestClient, session: Session, db: Session) -> None:
     # Create user, algo, promotion
    user = create_random_user(db)
    user_token_headers = authentication_token_from_email(client=client, email=user.email, db=db)
    algo = create_algorithm(session, user.id)
    
    # Request promotion
    data = {"algorithm_id": str(algo.id)}
    client.post(
        f"{settings.API_V1_STR}/promotions/", 
        headers=user_token_headers, 
        json=data
    )
    
    # Get created promotion
    promo_stmt = select(StrategyPromotion).where(StrategyPromotion.algorithm_id == algo.id)
    promo = session.exec(promo_stmt).first()
    
    # Login as superuser
    superuser_token_headers = get_superuser_token_headers(client)
    
    # Reject
    review_data = {"status": "rejected", "rejection_reason": "Not good enough"}
    response = client.patch(
        f"{settings.API_V1_STR}/promotions/{promo.id}",
        headers=superuser_token_headers,
        json=review_data
    )
    
    assert response.status_code == 200
    content = response.json()
    assert content["status"] == "rejected"
    assert content["rejection_reason"] == "Not good enough"
    
    # Check algo status should still be draft
    session.refresh(algo)
    assert algo.status == "draft"
