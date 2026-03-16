"""Tests for Feature Store materialized views and training data retrieval."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest


class TestFeatureStoreViewConfig:
    """Test that view configuration is correct."""

    def test_mv_targets_in_list(self) -> None:
        from app.enrichment.views import FEATURE_STORE_VIEWS
        assert "mv_coin_targets_5min" in FEATURE_STORE_VIEWS

    def test_mv_sentiment_in_list(self) -> None:
        from app.enrichment.views import FEATURE_STORE_VIEWS
        assert "mv_sentiment_signals_1h" in FEATURE_STORE_VIEWS

    def test_mv_catalyst_in_list(self) -> None:
        from app.enrichment.views import FEATURE_STORE_VIEWS
        assert "mv_catalyst_impact_decay" in FEATURE_STORE_VIEWS

    def test_mv_training_set_in_list(self) -> None:
        from app.enrichment.views import FEATURE_STORE_VIEWS
        assert "mv_training_set_v1" in FEATURE_STORE_VIEWS

    def test_dependency_order(self) -> None:
        from app.enrichment.views import FEATURE_STORE_VIEWS
        assert FEATURE_STORE_VIEWS.index("mv_coin_targets_5min") < FEATURE_STORE_VIEWS.index("mv_training_set_v1")
        assert FEATURE_STORE_VIEWS.index("mv_sentiment_signals_1h") < FEATURE_STORE_VIEWS.index("mv_training_set_v1")
        assert FEATURE_STORE_VIEWS.index("mv_catalyst_impact_decay") < FEATURE_STORE_VIEWS.index("mv_training_set_v1")


class TestRefreshViews:
    def test_refresh_feature_store_views_calls_execute(self) -> None:
        from app.enrichment.views import refresh_feature_store_views
        mock_session = MagicMock()
        refresh_feature_store_views(mock_session)
        assert mock_session.execute.call_count == 4
        mock_session.commit.assert_called_once()

    def test_refresh_handles_missing_view(self) -> None:
        from app.enrichment.views import refresh_feature_store_views
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("relation does not exist")
        refresh_feature_store_views(mock_session)  # Should not raise

    def test_refresh_all_views_count(self) -> None:
        from app.enrichment.views import (
            ENRICHMENT_VIEWS,
            FEATURE_STORE_VIEWS,
            refresh_all_views,
        )
        mock_session = MagicMock()
        refresh_all_views(mock_session)
        expected = len(ENRICHMENT_VIEWS) + len(FEATURE_STORE_VIEWS)
        assert mock_session.execute.call_count == expected


class TestFetchTrainingData:
    @pytest.mark.asyncio
    async def test_view_not_exists_returns_error(self) -> None:
        from app.services.agent.tools.data_retrieval_tools import fetch_training_data
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception('relation "mv_training_set_v1" does not exist')
        result = await fetch_training_data(mock_session, coin_type="BTC")
        assert len(result) == 1
        assert "error" in result[0]

    @pytest.mark.asyncio
    async def test_returns_formatted_data(self) -> None:
        from app.services.agent.tools.data_retrieval_tools import fetch_training_data
        mock_row = (
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            "BTC", 0.015, 0.032, 150.5, 0.65, 5, 0.82,
        )
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result
        result = await fetch_training_data(mock_session, coin_type="BTC", limit=100)
        assert len(result) == 1
        assert result[0]["coin_type"] == "BTC"
        assert result[0]["target_return_1h"] == 0.015
        assert result[0]["sentiment_1h_lag"] == 0.65

    @pytest.mark.asyncio
    async def test_empty_results(self) -> None:
        from app.services.agent.tools.data_retrieval_tools import fetch_training_data
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result
        result = await fetch_training_data(mock_session)
        assert result == []
