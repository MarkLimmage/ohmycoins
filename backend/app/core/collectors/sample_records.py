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
    NewsEnrichment,
    NewsItem,
    NewsKeywordMatch,
    OnChainMetrics,
    PriceData5Min,
    ProtocolFundamentals,
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
        source_filter: str | None = None,
        source_column: str = "source",
    ) -> None:
        self.model = model
        self.order_by = order_by
        self.display_columns = display_columns
        self.data_type_label = data_type_label
        self.source_filter = source_filter
        self.source_column = source_column


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
            "currencies",
            "impact_score",
            "detected_at",
        ],
        data_type_label="Catalyst Events",
        source_filter="SEC EDGAR",
    ),
    "catalyst_coinspot_announcements": PluginDataConfig(
        model=CatalystEvents,
        order_by="detected_at",
        display_columns=[
            "event_type",
            "title",
            "currencies",
            "impact_score",
            "detected_at",
        ],
        data_type_label="Catalyst Events",
        source_filter="CoinSpot",
    ),
    "CoinspotExchange": PluginDataConfig(
        model=PriceData5Min,
        order_by="timestamp",
        display_columns=["coin_type", "bid", "ask", "last", "timestamp"],
        data_type_label="Price Data (5min)",
    ),
    # All RSS/news collectors → NewsItem table, filtered by source
    "news_cointelegraph": PluginDataConfig(
        model=NewsItem,
        order_by="collected_at",
        display_columns=[
            "title",
            "sentiment_label",
            "sentiment_score",
            "currencies",
            "published_at",
        ],
        data_type_label="News Items (Enriched)",
        source_filter="CoinTelegraph",
    ),
    "news_coindesk": PluginDataConfig(
        model=NewsItem,
        order_by="collected_at",
        display_columns=[
            "title",
            "sentiment_label",
            "sentiment_score",
            "currencies",
            "published_at",
        ],
        data_type_label="News Items (Enriched)",
        source_filter="CoinDesk",
    ),
    "news_cryptoslate": PluginDataConfig(
        model=NewsItem,
        order_by="collected_at",
        display_columns=[
            "title",
            "sentiment_label",
            "sentiment_score",
            "currencies",
            "published_at",
        ],
        data_type_label="News Items (Enriched)",
        source_filter="CryptoSlate",
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
        source_filter="news_cryptoslate",
        source_column="source_collector",
    ),
    "news_decrypt": PluginDataConfig(
        model=NewsItem,
        order_by="collected_at",
        display_columns=[
            "title",
            "sentiment_label",
            "sentiment_score",
            "currencies",
            "published_at",
        ],
        data_type_label="News Items (Enriched)",
        source_filter="Decrypt",
    ),
    "news_newsbtc": PluginDataConfig(
        model=NewsItem,
        order_by="collected_at",
        display_columns=[
            "title",
            "sentiment_label",
            "sentiment_score",
            "currencies",
            "published_at",
        ],
        data_type_label="News Items (Enriched)",
        source_filter="NewsBTC",
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
        source_filter="news_beincrypto",
        source_column="source_collector",
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
        source_filter="news_cointelegraph",
        source_column="source_collector",
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
        source_filter="news_newsbtc",
        source_column="source_collector",
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
        source_filter="news_decrypt",
        source_column="source_collector",
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
        source_filter="news_coindesk",
        source_column="source_collector",
    ),
    "news_enrichment": PluginDataConfig(
        model=NewsEnrichment,
        order_by="enriched_at",
        display_columns=[
            "enricher_name",
            "enrichment_type",
            "confidence",
            "currencies",
            "enriched_at",
        ],
        data_type_label="Enrichment Data",
    ),
}


def _get_currencies_for_news_items(
    session: Session,
    links: list[str],
) -> dict[str, list[str]]:
    """Look up aggregated currencies from NewsKeywordMatch for a batch of news links."""
    if not links:
        return {}
    # fmt: off
    stmt: Any = (
        select(NewsKeywordMatch.news_item_link, NewsKeywordMatch.currencies).where(
            NewsKeywordMatch.news_item_link.in_(links)  # type: ignore[attr-defined]
        )
    )
    # fmt: on
    rows = session.exec(stmt).all()
    result: dict[str, set[str]] = {}
    for link, currencies in rows:
        if currencies:
            result.setdefault(link, set()).update(currencies)
    return {k: sorted(v) for k, v in result.items()}


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

    # Build source filter condition
    source_condition = None
    if config.source_filter:
        source_col = getattr(model, config.source_column)
        source_condition = source_col == config.source_filter

    # Total count
    count_stmt: Any = select(func.count()).select_from(model)
    if source_condition is not None:
        count_stmt = count_stmt.where(source_condition)
    total_count: int = session.exec(count_stmt).one()

    # Recent records
    stmt: Any = select(model).order_by(desc(order_col)).limit(limit)
    if source_condition is not None:
        stmt = stmt.where(source_condition)
    rows = session.exec(stmt).all()

    # For NewsItem models, look up currencies from keyword matches
    currencies_map: dict[str, list[str]] = {}
    needs_currencies = model is NewsItem and "currencies" in config.display_columns
    if needs_currencies and rows:
        links = [row.link for row in rows]
        currencies_map = _get_currencies_for_news_items(session, links)

    # Serialize to dicts filtered by display_columns
    records: list[dict[str, Any]] = []
    for row in rows:
        record: dict[str, Any] = {}
        for col in config.display_columns:
            if col == "currencies" and needs_currencies:
                val: Any = currencies_map.get(row.link, [])
            else:
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
