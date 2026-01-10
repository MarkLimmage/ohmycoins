"""
Data Retrieval Tools - Week 3-4 Implementation

Tools for DataRetrievalAgent to fetch cryptocurrency data from the database.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_
from sqlmodel import Session, func, select

from app.models import (
    CatalystEvents,
    NewsSentiment,
    OnChainMetrics,
    Order,
    Position,
    PriceData5Min,
    SocialSentiment,
)


async def fetch_price_data(
    session: Session,
    coin_type: str,
    start_date: datetime,
    end_date: datetime | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch historical price data for a cryptocurrency.

    Args:
        session: Database session
        coin_type: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
        start_date: Start date for data retrieval
        end_date: End date for data retrieval (default: now)

    Returns:
        List of price data dictionaries
    """
    if end_date is None:
        end_date = datetime.now()

    statement = (
        select(PriceData5Min)
        .where(
            and_(
                PriceData5Min.coin_type == coin_type,
                PriceData5Min.timestamp >= start_date,
                PriceData5Min.timestamp <= end_date,
            )
        )
        .order_by(PriceData5Min.timestamp)
    )

    results = session.exec(statement).all()

    return [
        {
            "timestamp": result.timestamp.isoformat(),
            "coin_type": result.coin_type,
            "bid": float(result.bid),
            "ask": float(result.ask),
            "last": float(result.last),
        }
        for result in results
    ]


async def fetch_sentiment_data(
    session: Session,
    start_date: datetime,
    end_date: datetime | None = None,
    platform: str | None = None,
    currencies: list[str] | None = None,
) -> dict[str, Any]:
    """
    Fetch sentiment data from news and social media sources.

    Args:
        session: Database session
        start_date: Start date for data retrieval
        end_date: End date for data retrieval (default: now)
        platform: Optional filter by platform (e.g., 'reddit', 'twitter')
        currencies: Optional filter by currencies

    Returns:
        Dictionary with news and social sentiment data
    """
    if end_date is None:
        end_date = datetime.now()

    # Fetch news sentiment
    news_statement = select(NewsSentiment).where(
        and_(
            NewsSentiment.collected_at >= start_date,
            NewsSentiment.collected_at <= end_date,
        )
    )
    if currencies:
        # Filter news that mention any of the specified currencies
        news_statement = news_statement.where(
            NewsSentiment.currencies.overlap(currencies)
        )

    news_results = session.exec(news_statement).all()

    # Fetch social sentiment
    social_statement = select(SocialSentiment).where(
        and_(
            SocialSentiment.collected_at >= start_date,
            SocialSentiment.collected_at <= end_date,
        )
    )
    if platform:
        social_statement = social_statement.where(SocialSentiment.platform == platform)
    if currencies:
        social_statement = social_statement.where(
            SocialSentiment.currencies.overlap(currencies)
        )

    social_results = session.exec(social_statement).all()

    return {
        "news_sentiment": [
            {
                "title": news.title,
                "source": news.source,
                "published_at": news.published_at.isoformat()
                if news.published_at
                else None,
                "sentiment": news.sentiment,
                "sentiment_score": float(news.sentiment_score)
                if news.sentiment_score
                else None,
                "currencies": news.currencies,
            }
            for news in news_results
        ],
        "social_sentiment": [
            {
                "platform": social.platform,
                "content": social.content,
                "score": social.score,
                "sentiment": social.sentiment,
                "currencies": social.currencies,
                "posted_at": social.posted_at.isoformat() if social.posted_at else None,
            }
            for social in social_results
        ],
    }


async def fetch_on_chain_metrics(
    session: Session,
    asset: str,
    start_date: datetime,
    end_date: datetime | None = None,
    metric_names: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch on-chain metrics for a cryptocurrency.

    Args:
        session: Database session
        asset: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
        start_date: Start date for data retrieval
        end_date: End date for data retrieval (default: now)
        metric_names: Optional list of specific metrics to fetch

    Returns:
        List of on-chain metric dictionaries
    """
    if end_date is None:
        end_date = datetime.now()

    statement = select(OnChainMetrics).where(
        and_(
            OnChainMetrics.asset == asset,
            OnChainMetrics.collected_at >= start_date,
            OnChainMetrics.collected_at <= end_date,
        )
    )

    if metric_names:
        statement = statement.where(OnChainMetrics.metric_name.in_(metric_names))

    results = session.exec(statement.order_by(OnChainMetrics.collected_at)).all()

    return [
        {
            "asset": result.asset,
            "metric_name": result.metric_name,
            "metric_value": float(result.metric_value),
            "source": result.source,
            "collected_at": result.collected_at.isoformat(),
        }
        for result in results
    ]


async def fetch_catalyst_events(
    session: Session,
    start_date: datetime,
    end_date: datetime | None = None,
    event_types: list[str] | None = None,
    currencies: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch catalyst events (SEC filings, listings, etc.).

    Args:
        session: Database session
        start_date: Start date for data retrieval
        end_date: End date for data retrieval (default: now)
        event_types: Optional filter by event types
        currencies: Optional filter by currencies

    Returns:
        List of catalyst event dictionaries
    """
    if end_date is None:
        end_date = datetime.now()

    statement = select(CatalystEvents).where(
        and_(
            CatalystEvents.detected_at >= start_date,
            CatalystEvents.detected_at <= end_date,
        )
    )

    if event_types:
        statement = statement.where(CatalystEvents.event_type.in_(event_types))

    if currencies:
        # Since currencies is now JSON type (not ARRAY), we need to filter results after query
        # For now, we'll fetch all and filter in Python
        pass

    results = session.exec(statement.order_by(CatalystEvents.detected_at)).all()

    # Filter by currencies if specified (post-query filtering for JSON field)
    if currencies:
        results = [
            r
            for r in results
            if r.currencies and any(c in r.currencies for c in currencies)
        ]

    return [
        {
            "event_type": result.event_type,
            "title": result.title,
            "description": result.description,
            "source": result.source,
            "currencies": result.currencies,
            "impact_score": result.impact_score,
            "detected_at": result.detected_at.isoformat(),
        }
        for result in results
    ]


async def get_available_coins(session: Session) -> list[str]:
    """
    Get list of all available cryptocurrencies in the database.

    Args:
        session: Database session

    Returns:
        List of cryptocurrency symbols
    """
    statement = select(PriceData5Min.coin_type).distinct()
    results = session.exec(statement).all()
    return sorted(results)


async def get_data_statistics(
    session: Session,
    coin_type: str | None = None,
) -> dict[str, Any]:
    """
    Get statistics about data coverage and availability.

    Args:
        session: Database session
        coin_type: Optional cryptocurrency symbol to get specific stats

    Returns:
        Dictionary with data statistics
    """
    stats: dict[str, Any] = {}

    # Price data statistics
    if coin_type:
        price_statement = select(
            func.min(PriceData5Min.timestamp).label("earliest"),
            func.max(PriceData5Min.timestamp).label("latest"),
            func.count(PriceData5Min.id).label("total_records"),
        ).where(PriceData5Min.coin_type == coin_type)
    else:
        price_statement = select(
            func.min(PriceData5Min.timestamp).label("earliest"),
            func.max(PriceData5Min.timestamp).label("latest"),
            func.count(PriceData5Min.id).label("total_records"),
        )

    price_stats = session.exec(price_statement).one()
    stats["price_data"] = {
        "earliest_timestamp": price_stats.earliest.isoformat()
        if price_stats.earliest
        else None,
        "latest_timestamp": price_stats.latest.isoformat()
        if price_stats.latest
        else None,
        "total_records": price_stats.total_records,
    }

    # Sentiment data statistics
    news_count = session.exec(select(func.count(NewsSentiment.id))).one()
    social_count = session.exec(select(func.count(SocialSentiment.id))).one()
    stats["sentiment_data"] = {
        "news_articles": news_count,
        "social_posts": social_count,
    }

    # On-chain metrics statistics
    onchain_count = session.exec(select(func.count(OnChainMetrics.id))).one()
    stats["on_chain_metrics"] = {
        "total_metrics": onchain_count,
    }

    # Catalyst events statistics
    catalyst_count = session.exec(select(func.count(CatalystEvents.id))).one()
    stats["catalyst_events"] = {
        "total_events": catalyst_count,
    }

    return stats


async def fetch_order_history(
    session: Session,
    user_id: uuid.UUID,
    coin_type: str | None = None,
    status: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch order history from Exchange ledger.

    Args:
        session: Database session
        user_id: User ID to fetch orders for
        coin_type: Optional filter by cryptocurrency symbol
        status: Optional filter by order status (pending, submitted, filled, etc.)
        start_date: Start date for data retrieval
        end_date: End date for data retrieval (default: now)

    Returns:
        List of order dictionaries
    """
    if end_date is None:
        end_date = datetime.now()

    if start_date is None:
        # Default to last 30 days
        start_date = end_date - timedelta(days=30)

    statement = select(Order).where(
        and_(
            Order.user_id == user_id,
            Order.created_at >= start_date,
            Order.created_at <= end_date,
        )
    )

    if coin_type:
        statement = statement.where(Order.coin_type == coin_type)

    if status:
        statement = statement.where(Order.status == status)

    results = session.exec(statement.order_by(Order.created_at.desc())).all()

    return [
        {
            "id": str(result.id),
            "coin_type": result.coin_type,
            "side": result.side,
            "order_type": result.order_type,
            "quantity": float(result.quantity),
            "price": float(result.price) if result.price else None,
            "filled_quantity": float(result.filled_quantity),
            "status": result.status,
            "created_at": result.created_at.isoformat(),
            "filled_at": result.filled_at.isoformat() if result.filled_at else None,
        }
        for result in results
    ]


async def fetch_user_positions(
    session: Session,
    user_id: uuid.UUID,
    coin_type: str | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch current positions from Exchange ledger.

    Args:
        session: Database session
        user_id: User ID to fetch positions for
        coin_type: Optional filter by cryptocurrency symbol

    Returns:
        List of position dictionaries
    """
    statement = select(Position).where(Position.user_id == user_id)

    if coin_type:
        statement = statement.where(Position.coin_type == coin_type)

    results = session.exec(statement).all()

    return [
        {
            "coin_type": result.coin_type,
            "quantity": float(result.quantity),
            "average_price": float(result.average_price),
            "total_cost": float(result.total_cost),
            "created_at": result.created_at.isoformat(),
            "updated_at": result.updated_at.isoformat(),
        }
        for result in results
    ]
