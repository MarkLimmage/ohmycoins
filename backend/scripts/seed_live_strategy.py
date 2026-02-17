import logging
import sys
import uuid
from decimal import Decimal
from datetime import datetime
from sqlmodel import Session, select

# Add /app to path to allow imports
sys.path.append('/app')

from app.core.db import engine
from app.models import User, Algorithm, DeployedAlgorithm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_live_strategy() -> None:
    session = Session(engine)
    try:
        # 1. Get Strategist User
        user = session.exec(select(User).where(User.email == "strategist@omc.local")).first()
        if not user:
            logger.error("User strategist@omc.local not found. Run initial_data.py first.")
            return

        logger.info(f"Found User: {user.id}")

        # 2. Get or Create Algorithm Definition
        algo_name = "MA Crossover Beta"
        algo = session.exec(select(Algorithm).where(Algorithm.name == algo_name)).first()
        
        if not algo:
            logger.info("Creating Algorithm Definition...")
            algo = Algorithm(
                name=algo_name,
                description="Simple Moving Average Crossover for Live Beta Test",
                algorithm_type="rule_based",
                created_by=user.id,
                status="active",
                default_execution_frequency=60, # Run every 1 minute for test
                default_position_limit=Decimal("10.00") # $10 AUD limit
            )
            session.add(algo)
            session.commit()
            session.refresh(algo)
            logger.info(f"Created Algorithm: {algo.id}")
        else:
            logger.info(f"Found Algorithm: {algo.id}")

        # 3. Deploy Algorithm for User
        deployment = session.exec(
            select(DeployedAlgorithm)
            .where(DeployedAlgorithm.user_id == user.id)
            .where(DeployedAlgorithm.algorithm_id == algo.id)
        ).first()

        if not deployment:
            logger.info("Deploying Algorithm to 'Live' Status...")
            deployment = DeployedAlgorithm(
                user_id=user.id,
                algorithm_id=algo.id,
                deployment_name="Live Beta Deployment",
                is_active=True,
                execution_frequency=60, # 1 minute
                position_limit=Decimal("10.00"),
                daily_loss_limit=Decimal("5.00"),
                parameters_json='{"short_window": 5, "long_window": 10, "coin_type": "DOGE"}' 
            )
            session.add(deployment)
            session.commit()
            logger.info(f"Deployed Algorithm: {deployment.id}")
        else:
            if not deployment.is_active:
                logger.info("Activating existing deployment...")
                deployment.is_active = True
                session.add(deployment)
                session.commit()
            logger.info(f"Deployment {deployment.id} is active.")

    except Exception as e:
        logger.error(f"Seeding failed: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_live_strategy()
