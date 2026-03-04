"""
Sample records retrieval for collector data tables.

Maps collector plugins to their corresponding data models and provides
utilities to fetch sample records for display in the UI.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlmodel import Session, desc, func, select

from app.models import (
    CatalystEvents,
    NewsItem,
    NewsKeywordMatch,
    NewsSentiment,
    OnChainMetrics,
    PriceData5Min,
    ProtocolFundamentals,
    SmartMoneyFlow,
    SocialSentiment,
)


class PluginDataConfig:
    """Configuration for mapping a plugin to its data model."""

    def __init__(
        self,
        model: type,
        order_by: str,
        display_columns: list[str],
        data_type_label: str,
    ) -> None:
        self.model = model
        self.order_by = order_by
        self.display_columns = display_columns
        self.data_type_label = data_type_label


PLUGIN_DATA_MAP: dict[str, PluginDataConfig] = {
    "glass_defillama": PluginDataConfig(
        model=ProtocolFundamentals,
        order_by="collected_at",
        display_columns=[
            "protocol",
            "tvl_usd",
            "fees_24h",
            "revenue_24h",
            "collected_at",
        ],
        data_type_label="Protocol Fundamentals",
    ),
    "GlassChainWalker": PluginDataConfig(
        model=OnChainMetrics,
        order_by="collected_at",
        display_columns=[
            "asset",
            "metric_name",
            "metric_value",
            "source",
            "collected_at",
        ],
        data_type_label="On-Chain Metrics",
    ),
    "glass_nansen": PluginDataConfig(
        model=SmartMoneyFlow,
        order_by="collected_at",
        display_columns=[
            "token",
            "net_flow_usd",
            "buying_wallet_count",
            "selling_wallet_count",
            "collected_at",
        ],
        data_type_label="Smart Money Flows",
    ),
    "news_cryptopanic": PluginDataConfig(
        model=NewsSentiment,
        order_by="collected_at",
        display_columns=[
            "title",
            "source",
            "sentiment",
            "sentiment_score",
            "total_votes",
            "published_at",
        ],
        data_type_label="News Sentiment",
    ),
    "human_newscatcher": PluginDataConfig(
        model=NewsSentiment,
        order_by="collected_at",
        display_columns=[
            "title",
            "source",
            "sentiment",
            "sentiment_score",
            "published_at",
        ],
        data_type_label="News Sentiment",
    ),
    "human_reddit": PluginDataConfig(
        model=SocialSentiment,
        order_by="posted_at",
        display_columns=[
            "platform",
            "content",
            "author",
            "score",
            "sentiment",
            "posted_at",
        ],
        data_type_label="Social Sentiment",
    ),
    "catalyst_sec": PluginDataConfig(
        model=CatalystEvents,
        order_by="detected_at",
        display_columns=[
            "event_type",
            "title",
            "source",
            "impact_score",
            "detected_at",
        ],
        data_type_label="Catalyst Events",
    ),
    "catalyst_coinspot_announcements": PluginDataConfig(
        model=CatalystEvents,
        order_by="detected_at",
        display_columns=[
            "event_type",
            "title",
            "source",
            "impact_score",
            "detected_at",
        ],
        data_type_label="Catalyst Events",
    ),
    "CoinspotExchange": PluginDataConfig(
        model=PriceData5Min,
        order_by="timestamp",
        display_columns=["coin_type", "bid", "ask", "last", "timestamp"],
        data_type_label="Price Data (5min)",
    ),
    # All RSS/news collectors → NewsItem table
    "HumanRSSCollector": PluginDataConfig(
        model=NewsItem,
        order_by="collected_at",
        display_columns=["title", "source", "link", "published_at", "collected_at"],
        data_type_label="News Items",
    ),
    "news_cointelegraph": PluginDataConfig(
        model=NewsItem,
        order_by="collected_at",
        display_columns=[
            "title",
            "source",
            "sentiment_label",
            "sentiment_score",
            "published_at",
            "collected_at",
        ],
        data_type_label="News Items (Enriched)",
    ),
    "news_coindesk": PluginDataConfig(
        model=NewsItem,
        order_by="collected_at",
        display_columns=[
            "title",
            "source",
            "sentiment_label",
            "sentiment_score",
            "published_at",
            "collected_at",
        ],
        data_type_label="News Items (Enriched)",
    ),
    "news_beincrypto": PluginDataConfig(
        model=NewsItem,
        order_by="collected_at",
        display_columns=[
            "title",
            "source",
            "sentiment_label",
            "sentiment_score",
            "published_at",
            "collected_at",
        ],
        data_type_label="News Items (Enriched)",
    ),
    "news_cryptoslate": PluginDataConfig(
        model=NewsItem,
        order_by="collected_at",
        display_columns=[
            "title",
            "source",
            "sentiment_label",
            "sentiment_score",
            "published_at",
            "collected_at",
        ],
        data_type_label="News Items (Enriched)",
    ),
    "news_cryptoslate_keywords": PluginDataConfig(
        model=NewsKeywordMatch,
        order_by="matched_at",
        display_columns=[
            "keyword",
            "category",
            "direction",
            "impact",
            "currencies",
            "temporal_signal",
            "matched_at",
        ],
        data_type_label="Keyword Matches",
    ),
    "news_decrypt": PluginDataConfig(
        model=NewsItem,
        order_by="collected_at",
        display_columns=[
            "title",
            "source",
            "sentiment_label",
            "sentiment_score",
            "published_at",
            "collected_at",
        ],
        data_type_label="News Items (Enriched)",
    ),
    "news_newsbtc": PluginDataConfig(
        model=NewsItem,
        order_by="collected_at",
        display_columns=[
            "title",
            "source",
            "sentiment_label",
            "sentiment_score",
            "published_at",
            "collected_at",
        ],
        data_type_label="News Items (Enriched)",
    ),
    "news_beincrypto_keywords": PluginDataConfig(
        model=NewsKeywordMatch,
        order_by="matched_at",
        display_columns=[
            "keyword",
            "category",
            "direction",
            "impact",
            "currencies",
            "temporal_signal",
            "matched_at",
        ],
        data_type_label="Keyword Matches",
    ),
    "news_cointelegraph_keywords": PluginDataConfig(
        model=NewsKeywordMatch,
        order_by="matched_at",
        display_columns=[
            "keyword",
            "category",
            "direction",
            "impact",
            "currencies",
            "temporal_signal",
            "matched_at",
        ],
        data_type_label="Keyword Matches",
    ),
    "news_newsbtc_keywords": PluginDataConfig(
        model=NewsKeywordMatch,
        order_by="matched_at",
        display_columns=[
            "keyword",
            "category",
            "direction",
            "impact",
            "currencies",
            "temporal_signal",
            "matched_at",
        ],
        data_type_label="Keyword Matches",
    ),
    "news_decrypt_keywords": PluginDataConfig(
        model=NewsKeywordMatch,
        order_by="matched_at",
        display_columns=[
            "keyword",
            "category",
            "direction",
            "impact",
            "currencies",
            "temporal_signal",
            "matched_at",
        ],
        data_type_label="Keyword Matches",
    ),
    "news_coindesk_keywords": PluginDataConfig(
        model=NewsKeywordMatch,
        order_by="matched_at",
        display_columns=[
            "keyword",
            "category",
            "direction",
            "impact",
            "currencies",
            "temporal_signal",
            "matched_at",
        ],
        data_type_label="Keyword Matches",
    ),
}


def get_sample_records(
    session: Session, plugin_name: str, limit: int = 10
) -> dict[str, Any] | None:
    """
    Fetch recent sample records from the data table associated with a plugin.

    Args:
        session: SQLModel session
        plugin_name: Name of the collector plugin
        limit: Maximum number of records to return (default 10)

    Returns:
        Dictionary with data_type, columns, records, and total_count, or None if plugin not found
    """
    config = PLUGIN_DATA_MAP.get(plugin_name)
    if config is None:
        return None

    model = config.model
    order_col = getattr(model, config.order_by)

    # Total count
    count_stmt = select(func.count()).select_from(model)
    total_count: int = session.exec(count_stmt).one()

    # Recent records
    stmt: Any = select(model).order_by(desc(order_col)).limit(limit)
    rows = session.exec(stmt).all()

    # Serialize to dicts filtered by display_columns
    records: list[dict[str, Any]] = []
    for row in rows:
        record: dict[str, Any] = {}
        for col in config.display_columns:
            val = getattr(row, col, None)
            # Convert non-JSON-serializable types
            if val is not None and hasattr(val, "isoformat"):
                val = val.isoformat()
            elif isinstance(val, Decimal):
                val = float(val)
            record[col] = val
        records.append(record)

    return {
        "data_type": config.data_type_label,
        "columns": config.display_columns,
        "records": records,
        "total_count": total_count,
    }
