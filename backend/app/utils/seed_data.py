"""
Synthetic data generation for Oh My Coins development environment.

This module provides utilities to populate the database with realistic data
for all system components, enabling comprehensive end-to-end testing.

For publicly available data (prices, news, etc.), we collect REAL data.
For private/user-specific data (users, positions, orders), we generate synthetic data.

Usage:
    # Generate full dataset
    python -m app.utils.seed_data --all

    # Generate specific data types
    python -m app.utils.seed_data --users 10 --collect-prices --days 7

    # Clear all data
    python -m app.utils.seed_data --clear
"""

import argparse
import asyncio
import logging
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import aiohttp
from faker import Faker
from sqlmodel import Session, delete, select

from app.core.config import settings
from app.core.db import engine
from app.core.security import get_password_hash
from app.models import (
    AgentArtifact,
    AgentSession,
    AgentSessionMessage,
    AgentSessionStatus,
    Algorithm,
    AuditLog,
    CatalystEvents,
    CoinspotCredentials,
    CollectorRuns,
    DeployedAlgorithm,
    NewsSentiment,
    OnChainMetrics,
    Order,
    Position,
    PriceData5Min,
    ProtocolFundamentals,
    SmartMoneyFlow,
    SocialSentiment,
    StrategyPromotion,
    User,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

fake = Faker()
Faker.seed(42)  # For reproducibility
random.seed(42)

# Cryptocurrency data
COINS = ["BTC", "ETH", "ADA", "DOT", "LINK", "UNI", "AAVE", "SOL", "MATIC", "DOGE"]

# Approximate fallback prices for coins (used when no real data is available)
FALLBACK_COIN_PRICES = {
    "BTC": Decimal("65000.00"),
    "ETH": Decimal("3500.00"),
    "ADA": Decimal("0.50"),
    "DOT": Decimal("7.50"),
    "LINK": Decimal("15.00"),
    "UNI": Decimal("8.00"),
    "AAVE": Decimal("95.00"),
    "SOL": Decimal("140.00"),
    "MATIC": Decimal("0.75"),
    "DOGE": Decimal("0.12"),
}


def generate_users(session: Session, count: int = 10) -> list[User]:
    """Generate synthetic user accounts with realistic profiles."""
    logger.info(f"Generating {count} users...")
    users = []

    # Check if superuser already exists
    existing_superuser = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()

    if existing_superuser:
        logger.info(f"Superuser already exists: {settings.FIRST_SUPERUSER}")
        users.append(existing_superuser)
        start_index = 1  # Skip creating superuser
    else:
        start_index = 0  # Create superuser as first user

    for i in range(start_index, count):
        is_superuser = (
            i == 0 and not existing_superuser
        )  # First user is superuser only if doesn't exist
        user = User(
            email=f"user{i}_{uuid.uuid4()}@example.com"
            if not is_superuser
            else settings.FIRST_SUPERUSER,
            hashed_password=get_password_hash(
                "TestPassword123!"
                if not is_superuser
                else settings.FIRST_SUPERUSER_PASSWORD
            ),
            full_name=fake.name(),
            is_active=True,
            is_superuser=is_superuser,
            timezone=random.choice(
                ["UTC", "Australia/Sydney", "America/New_York", "Europe/London"]
            ),
            preferred_currency=random.choice(["AUD", "USD", "EUR", "BTC"]),
            risk_tolerance=random.choice(["low", "medium", "high"]),
            trading_experience=random.choice(["beginner", "intermediate", "advanced"]),
            created_at=datetime.now(timezone.utc)
            - timedelta(days=random.randint(1, 365)),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(user)
        users.append(user)

    session.commit()
    for user in users:
        session.refresh(user)

    logger.info(
        f"Created {len(users) - (1 if existing_superuser else 0)} new users (total: {len(users)})"
    )
    return users


async def collect_real_price_data(session: Session, _hours: int = 24) -> int:
    """
    Collect REAL price data from Coinspot API.

    Since we can only get current prices from the public API,
    we'll collect real-time data and store it with timestamps.
    For historical data, we would need to run this over time or use a paid API.
    """
    logger.info("Collecting real price data from Coinspot...")

    url = "https://www.coinspot.com.au/pubapi/v2/latest"
    count = 0

    try:
        async with aiohttp.ClientSession() as client_session:
            async with client_session.get(
                url, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    if data.get("status") == "ok" and "prices" in data:
                        current_time = datetime.now(timezone.utc)

                        for coin_type, price_data in data["prices"].items():
                            # Skip if not in our tracked coins
                            coin_upper = coin_type.upper()

                            try:
                                bid = Decimal(str(price_data.get("bid", "0")))
                                ask = Decimal(str(price_data.get("ask", "0")))
                                last = Decimal(str(price_data.get("last", "0")))

                                # Only add if we have valid price data
                                if last > 0:
                                    price_record = PriceData5Min(
                                        timestamp=current_time,
                                        coin_type=coin_upper,
                                        bid=bid,
                                        ask=ask,
                                        last=last,
                                        created_at=datetime.now(timezone.utc),
                                    )
                                    session.add(price_record)
                                    count += 1
                            except (ValueError, KeyError, TypeError) as e:
                                logger.warning(
                                    f"Failed to process price for {coin_type}: {e}"
                                )
                                continue

                        session.commit()
                        logger.info(
                            f"✅ Collected {count} real price records from Coinspot"
                        )
                    else:
                        logger.error(f"Invalid response from Coinspot API: {data}")
                else:
                    logger.error(
                        f"Failed to fetch prices from Coinspot: HTTP {response.status}"
                    )

    except Exception as e:
        logger.error(f"Error collecting real price data: {e}")
        session.rollback()

    return count


async def collect_real_defi_data(session: Session) -> int:
    """
    Collect REAL DeFi protocol data from DeFiLlama API.
    """
    logger.info("Collecting real DeFi protocol data from DeFiLlama...")

    protocols_url = "https://api.llama.fi/protocols"
    count = 0

    try:
        async with aiohttp.ClientSession() as client_session:
            async with client_session.get(
                protocols_url, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    protocols = await response.json()
                    current_time = datetime.now(timezone.utc)

                    # Get top 10 protocols by TVL
                    top_protocols = sorted(
                        protocols, key=lambda x: x.get("tvl", 0), reverse=True
                    )[:10]

                    for protocol_data in top_protocols:
                        try:
                            protocol_name = protocol_data.get("name", "Unknown")
                            tvl = Decimal(str(protocol_data.get("tvl", 0)))

                            # Note: DeFiLlama doesn't provide fees/revenue in the summary endpoint
                            # We would need to use protocol-specific endpoints for that

                            fundamental = ProtocolFundamentals(
                                protocol=protocol_name,
                                tvl_usd=tvl,
                                fees_24h=None,  # Not available in this endpoint
                                revenue_24h=None,  # Not available in this endpoint
                                collected_at=current_time,
                            )
                            session.add(fundamental)
                            count += 1
                        except (ValueError, KeyError, TypeError) as e:
                            logger.warning(f"Failed to process protocol data: {e}")
                            continue

                    session.commit()
                    logger.info(f"✅ Collected {count} real DeFi protocol records")
                else:
                    logger.error(f"Failed to fetch DeFi data: HTTP {response.status}")

    except Exception as e:
        logger.error(f"Error collecting DeFi data: {e}")
        session.rollback()

    return count


async def collect_real_news_data(session: Session, days: int = 7) -> int:
    """
    Collect REAL cryptocurrency news from CryptoPanic API (free tier).

    Note: CryptoPanic offers a free tier with limited requests.
    For production, you would need an API key set in CRYPTOPANIC_API_KEY env var.
    """
    logger.info(f"Collecting real news data from CryptoPanic (last {days} days)...")

    # CryptoPanic API - use env var if available, otherwise use free tier
    api_key = os.getenv("CRYPTOPANIC_API_KEY", "free")
    url = "https://cryptopanic.com/api/v1/posts/"
    params = {
        "auth_token": api_key,
        "public": "true",
        "kind": "news",
    }

    count = 0

    try:
        async with aiohttp.ClientSession() as client_session:
            async with client_session.get(
                url, params=params, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    if "results" in data:
                        for article in data["results"][:50]:  # Limit to 50 articles
                            try:
                                # Extract currencies mentioned
                                currencies = []
                                if "currencies" in article:
                                    currencies = [
                                        c["code"] for c in article["currencies"]
                                    ]

                                # Parse published time
                                published_str = article.get("published_at")
                                published_at = (
                                    datetime.fromisoformat(
                                        published_str.replace("Z", "+00:00")
                                    )
                                    if published_str
                                    else None
                                )

                                # Map votes to sentiment
                                votes = article.get("votes", {})
                                positive = votes.get("positive", 0)
                                negative = votes.get("negative", 0)
                                total_votes = positive + negative

                                if total_votes > 0:
                                    sentiment_score = Decimal(
                                        (positive - negative) / total_votes
                                    )
                                    if sentiment_score > 0.2:
                                        sentiment = "positive"
                                    elif sentiment_score < -0.2:
                                        sentiment = "negative"
                                    else:
                                        sentiment = "neutral"
                                else:
                                    sentiment = "neutral"
                                    sentiment_score = Decimal("0")

                                news = NewsSentiment(
                                    title=article.get("title", ""),
                                    source=article.get("source", {}).get(
                                        "title", "CryptoPanic"
                                    ),
                                    url=article.get("url", ""),
                                    published_at=published_at,
                                    sentiment=sentiment,
                                    sentiment_score=sentiment_score,
                                    currencies=currencies if currencies else None,
                                    collected_at=datetime.now(timezone.utc),
                                )
                                session.add(news)
                                count += 1
                            except (ValueError, KeyError, TypeError) as e:
                                logger.warning(f"Failed to process news article: {e}")
                                continue

                        session.commit()
                        logger.info(f"✅ Collected {count} real news articles")
                    else:
                        logger.warning("No results in CryptoPanic response")
                else:
                    logger.error(f"Failed to fetch news: HTTP {response.status}")

    except Exception as e:
        logger.error(f"Error collecting news data: {e}")
        session.rollback()

    return count


def generate_agent_sessions(
    session: Session, users: list[User], count: int = 20
) -> int:
    """Generate synthetic agent session data (user-specific, cannot be collected)."""
    logger.info(f"Generating {count} agent sessions...")

    goals = [
        "Predict Bitcoin price movements over the next hour",
        "Identify profitable trading opportunities for Ethereum",
        "Analyze correlation between BTC and ETH prices",
        "Build a machine learning model to predict altcoin trends",
        "Backtest a moving average crossover strategy",
    ]

    created_count = 0
    for _ in range(count):
        user = random.choice(users)
        status = random.choice(
            [
                AgentSessionStatus.COMPLETED,
                AgentSessionStatus.COMPLETED,
                AgentSessionStatus.COMPLETED,
                AgentSessionStatus.FAILED,
                AgentSessionStatus.RUNNING,
            ]
        )

        created_at = datetime.now(timezone.utc) - timedelta(
            hours=random.randint(1, 720)
        )

        agent_session = AgentSession(
            user_id=user.id,
            user_goal=random.choice(goals),
            status=status,
            error_message=fake.sentence()
            if status == AgentSessionStatus.FAILED
            else None,
            result_summary=fake.text(max_nb_chars=200)
            if status == AgentSessionStatus.COMPLETED
            else None,
            created_at=created_at,
            updated_at=datetime.now(timezone.utc),
            completed_at=created_at + timedelta(minutes=random.randint(5, 60))
            if status == AgentSessionStatus.COMPLETED
            else None,
        )
        session.add(agent_session)
        session.flush()

        # Add messages for this session
        if status != AgentSessionStatus.PENDING:
            for i in range(random.randint(3, 10)):
                message = AgentSessionMessage(
                    session_id=agent_session.id,
                    role=random.choice(["user", "assistant", "system"]),
                    content=fake.sentence(nb_words=15),
                    agent_name=random.choice(
                        ["data_retrieval", "data_analyst", "model_trainer", "evaluator"]
                    ),
                    created_at=created_at + timedelta(minutes=i),
                )
                session.add(message)

        # Add artifacts for completed sessions
        if status == AgentSessionStatus.COMPLETED:
            artifact_extensions = {"model": "pkl", "plot": "png", "report": "html"}
            artifact_mimes = {
                "model": "application/octet-stream",
                "plot": "image/png",
                "report": "text/html",
            }

            for artifact_type in ["model", "plot", "report"]:
                extension = artifact_extensions[artifact_type]
                mime_type = artifact_mimes[artifact_type]

                artifact = AgentArtifact(
                    session_id=agent_session.id,
                    artifact_type=artifact_type,
                    name=f"{artifact_type}_{fake.word()}.{extension}",
                    description=fake.sentence(),
                    file_path=f"/artifacts/{agent_session.id}/{artifact_type}_{str(fake.uuid4())}.{extension}",
                    mime_type=mime_type,
                    size_bytes=random.randint(1024, 1024000),
                    created_at=agent_session.completed_at,
                )
                session.add(artifact)

        created_count += 1

    session.commit()
    logger.info(f"Created {created_count} agent sessions with messages and artifacts")
    return created_count


def generate_algorithms(
    session: Session, users: list[User], count: int = 15
) -> list[Algorithm]:
    """Generate synthetic trading algorithms (user-specific)."""
    logger.info(f"Generating {count} algorithms...")

    algorithm_types = ["ml_model", "rule_based", "reinforcement_learning"]
    algorithms = []

    for i in range(count):
        user = random.choice(users)
        algo_type = random.choice(algorithm_types)
        status = random.choice(["draft", "active", "paused", "archived"])

        algorithm = Algorithm(
            created_by=user.id,
            name=f"{algo_type.replace('_', ' ').title()} Strategy {i+1}",
            description=fake.text(max_nb_chars=200),
            algorithm_type=algo_type,
            version=f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
            status=status,
            configuration_json='{"param1": 0.5, "param2": 100}',
            default_execution_frequency=random.choice([60, 300, 900, 3600]),
            default_position_limit=Decimal(random.randint(1000, 10000)),
            performance_metrics_json='{"sharpe_ratio": 1.5, "max_drawdown": 0.15, "win_rate": 0.65}',
            created_at=datetime.now(timezone.utc)
            - timedelta(days=random.randint(1, 180)),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(algorithm)
        algorithms.append(algorithm)

    session.commit()
    for algo in algorithms:
        session.refresh(algo)

    logger.info(f"Created {len(algorithms)} algorithms")
    return algorithms


def generate_positions_and_orders(
    session: Session, users: list[User], algorithms: list[Algorithm]
) -> int:
    """Generate synthetic trading positions and orders (user-specific)."""
    logger.info("Generating positions and orders...")

    # Get current prices for calculations
    latest_prices = {}
    for coin in COINS:
        result = session.exec(
            select(PriceData5Min)
            .where(PriceData5Min.coin_type == coin)
            .order_by(PriceData5Min.timestamp.desc())  # type: ignore
            .limit(1)
        ).first()
        if result:
            latest_prices[coin] = result.last
        else:
            # Use realistic fallback prices based on coin type
            latest_prices[coin] = FALLBACK_COIN_PRICES.get(coin, Decimal("100.00"))

    position_count = 0
    order_count = 0

    for user in users[:5]:  # Only first 5 users have positions
        # Generate 2-5 positions per user
        user_coins = random.sample(
            [c for c in COINS if c in latest_prices], k=min(5, len(latest_prices))
        )

        for coin in user_coins:
            quantity = Decimal(random.uniform(0.01, 10))
            avg_price = latest_prices[coin] * Decimal(random.uniform(0.9, 1.1))

            position = Position(
                user_id=user.id,
                coin_type=coin,
                quantity=quantity,
                average_price=avg_price,
                total_cost=quantity * avg_price,
                created_at=datetime.now(timezone.utc)
                - timedelta(days=random.randint(1, 90)),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(position)
            position_count += 1

            # Generate 3-8 orders for this position
            for _ in range(random.randint(3, 8)):
                order_side = random.choice(["buy", "sell"])
                order_quantity = Decimal(random.uniform(0.001, float(quantity)))
                order_price = latest_prices[coin] * Decimal(random.uniform(0.95, 1.05))

                order = Order(
                    user_id=user.id,
                    algorithm_id=random.choice(algorithms).id
                    if algorithms and random.random() < 0.7
                    else None,
                    coin_type=coin,
                    side=order_side,
                    order_type=random.choice(["market", "limit"]),
                    quantity=order_quantity,
                    price=order_price,
                    filled_quantity=order_quantity
                    if random.random() < 0.9
                    else Decimal("0"),
                    status=random.choice(
                        ["filled", "filled", "filled", "cancelled", "failed"]
                    ),
                    coinspot_order_id=f"CS{str(fake.uuid4())[:8]}",
                    created_at=datetime.now(timezone.utc)
                    - timedelta(hours=random.randint(1, 2160)),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(order)
                order_count += 1

    session.commit()
    logger.info(f"Created {position_count} positions and {order_count} orders")
    return position_count + order_count


def generate_deployed_algorithms(
    session: Session, users: list[User], algorithms: list[Algorithm], count: int = 10
) -> int:
    """Generate deployed algorithm instances (user-specific)."""
    logger.info(f"Generating {count} deployed algorithms...")

    active_algos = [a for a in algorithms if a.status == "active"]
    if not active_algos:
        logger.warning("No active algorithms to deploy")
        return 0

    deployed_count = 0
    for _ in range(count):
        user = random.choice(users)
        algorithm = random.choice(active_algos)

        deployed = DeployedAlgorithm(
            user_id=user.id,
            algorithm_id=algorithm.id,
            deployment_name=f"{algorithm.name} - Deployment {deployed_count + 1}",
            is_active=random.choice([True, False]),
            execution_frequency=algorithm.default_execution_frequency,
            position_limit=algorithm.default_position_limit,
            daily_loss_limit=Decimal(random.randint(500, 5000)),
            parameters_json='{"custom_param": 123}',
            created_at=datetime.now(timezone.utc)
            - timedelta(days=random.randint(1, 60)),
            updated_at=datetime.now(timezone.utc),
            activated_at=datetime.now(timezone.utc)
            - timedelta(days=random.randint(0, 30)),
            total_profit_loss=Decimal(random.uniform(-1000, 5000)),
            total_trades=random.randint(10, 500),
        )
        session.add(deployed)
        deployed_count += 1

    session.commit()
    logger.info(f"Created {deployed_count} deployed algorithms")
    return deployed_count


def clear_all_data(session: Session, commit: bool = True) -> None:
    """Clear all data from the database (except superuser)."""
    logger.warning("Clearing all data from database...")

    tables = [
        AuditLog,  # Clear first due to FK to User
        DeployedAlgorithm,
        StrategyPromotion,
        Order,
        Position,
        Algorithm,
        AgentArtifact,
        AgentSessionMessage,
        AgentSession,
        CollectorRuns,
        CatalystEvents,
        SocialSentiment,
        NewsSentiment,
        OnChainMetrics,
        ProtocolFundamentals,
        PriceData5Min,
        CoinspotCredentials,
        SmartMoneyFlow,
    ]

    for table in tables:
        session.exec(delete(table))  # type: ignore
        logger.info(f"Cleared {table.__tablename__}")

    # Clear users except superuser
    session.exec(delete(User).where(User.email != settings.FIRST_SUPERUSER))  # type: ignore
    logger.info("Cleared users (except superuser)")

    if commit:
        session.commit()
    else:
        session.flush()
    logger.info("All data cleared")


async def seed_all_async(
    session: Session,
    user_count: int = 10,
    collect_real_data: bool = True,
    agent_session_count: int = 20,
    algorithm_count: int = 15,
) -> None:
    """Seed the database with real and synthetic data."""
    logger.info("Starting comprehensive data seeding...")

    # Generate users first (synthetic - user-specific data)
    users = generate_users(session, user_count)

    # Collect REAL publicly available data
    if collect_real_data:
        logger.info("📡 Collecting real data from public APIs...")
        await collect_real_price_data(session)
        await collect_real_defi_data(session)
        await collect_real_news_data(session)

    # Generate synthetic user-specific data
    logger.info("🎭 Generating synthetic user-specific data...")
    generate_agent_sessions(session, users, agent_session_count)
    algorithms = generate_algorithms(session, users, algorithm_count)
    generate_deployed_algorithms(session, users, algorithms, 10)
    generate_positions_and_orders(session, users, algorithms)

    logger.info("✅ Comprehensive data seeding completed!")


def main() -> None:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Seed data for Oh My Coins (mix of real and synthetic)"
    )
    parser.add_argument("--all", action="store_true", help="Generate all data types")
    parser.add_argument("--clear", action="store_true", help="Clear all data")
    parser.add_argument(
        "--users", type=int, default=10, help="Number of users to generate"
    )
    parser.add_argument(
        "--no-real-data", action="store_true", help="Skip collecting real data"
    )
    parser.add_argument(
        "--algorithms", type=int, default=15, help="Number of algorithms"
    )
    parser.add_argument(
        "--agent-sessions", type=int, default=20, help="Number of agent sessions"
    )

    args = parser.parse_args()

    with Session(engine) as session:
        if args.clear:
            clear_all_data(session)
            return

        # Run async seeding
        asyncio.run(
            seed_all_async(
                session,
                user_count=args.users,
                collect_real_data=not args.no_real_data,
                agent_session_count=args.agent_sessions,
                algorithm_count=args.algorithms,
            )
        )


if __name__ == "__main__":
    main()
