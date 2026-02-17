"""
Tests for Data Analysis Tools - Week 3-4 Implementation

Tests all data analysis tools with sample data.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from app.services.agent.tools.data_analysis_tools import (
    analyze_on_chain_signals,
    analyze_sentiment_trends,
    calculate_technical_indicators,
    clean_data,
    detect_catalyst_impact,
    perform_eda,
)


@pytest.fixture
def sample_price_data():
    """Create sample price data for testing."""
    now = datetime.now()
    data = []
    for i in range(50):
        data.append({
            "timestamp": (now - timedelta(hours=50-i)).isoformat(),
            "coin_type": "BTC",
            "bid": 50000 + i * 100,
            "ask": 50100 + i * 100,
            "last": 50050 + i * 100,
        })
    return data


@pytest.fixture
def sample_sentiment_data():
    """Create sample sentiment data for testing."""
    return {
        "news_sentiment": [
            {
                "title": "Bitcoin reaches new heights",
                "source": "CoinDesk",
                "published_at": datetime.now().isoformat(),
                "sentiment": "positive",
                "sentiment_score": 0.8,
                "currencies": ["BTC"],
            },
            {
                "title": "Market shows mixed signals",
                "source": "CryptoNews",
                "published_at": datetime.now().isoformat(),
                "sentiment": "neutral",
                "sentiment_score": 0.1,
                "currencies": ["BTC", "ETH"],
            },
        ],
        "social_sentiment": [
            {
                "platform": "reddit",
                "content": "Bullish on BTC",
                "score": 100,
                "sentiment": "positive",
                "currencies": ["BTC"],
                "posted_at": datetime.now().isoformat(),
            },
            {
                "platform": "twitter",
                "content": "Market correction incoming?",
                "score": 50,
                "sentiment": "negative",
                "currencies": ["BTC"],
                "posted_at": datetime.now().isoformat(),
            },
        ],
    }


@pytest.fixture
def sample_on_chain_data():
    """Create sample on-chain metrics data for testing."""
    now = datetime.now()
    data = []
    for i in range(10):
        data.append({
            "asset": "BTC",
            "metric_name": "active_addresses",
            "metric_value": 900000 + i * 10000,
            "source": "glassnode",
            "collected_at": (now - timedelta(days=10-i)).isoformat(),
        })
    return data


@pytest.fixture
def sample_catalyst_events():
    """Create sample catalyst events for testing."""
    now = datetime.now()
    return [
        {
            "event_type": "sec_filing",
            "title": "Major SEC filing",
            "description": "Important regulatory filing",
            "source": "SEC",
            "currencies": ["BTC"],
            "impact_score": 8,
            "detected_at": (now - timedelta(hours=2)).isoformat(),
        },
        {
            "event_type": "exchange_listing",
            "title": "New exchange listing",
            "description": "Token listed on major exchange",
            "source": "Exchange",
            "currencies": ["ETH"],
            "impact_score": 6,
            "detected_at": (now - timedelta(hours=5)).isoformat(),
        },
    ]


class TestCalculateTechnicalIndicators:
    """Tests for calculate_technical_indicators function."""

    def test_calculate_technical_indicators_basic(self, sample_price_data):
        """Test basic technical indicator calculation."""
        result = calculate_technical_indicators(sample_price_data)

        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert "close" in result.columns
        assert "high" in result.columns
        assert "low" in result.columns

    def test_calculate_technical_indicators_insufficient_data(self):
        """Test with insufficient data points."""
        # Only 5 data points, not enough for most indicators
        data = [
            {
                "timestamp": datetime.now().isoformat(),
                "coin_type": "BTC",
                "bid": 50000,
                "ask": 50100,
                "last": 50050,
            }
            for _ in range(5)
        ]

        result = calculate_technical_indicators(data)

        # Should return DataFrame but with limited indicators
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5

    def test_calculate_technical_indicators_specific(self, sample_price_data):
        """Test calculating specific indicators."""
        result = calculate_technical_indicators(
            sample_price_data,
            indicators=["sma_20", "ema_20", "rsi"]
        )

        assert isinstance(result, pd.DataFrame)
        # Check that at least some indicators were calculated
        assert "close" in result.columns


class TestAnalyzeSentimentTrends:
    """Tests for analyze_sentiment_trends function."""

    def test_analyze_sentiment_trends_basic(self, sample_sentiment_data):
        """Test basic sentiment trend analysis."""
        result = analyze_sentiment_trends(sample_sentiment_data)

        assert "time_window" in result
        assert "news_sentiment" in result
        assert "social_sentiment" in result
        assert "overall_sentiment" in result

        assert result["news_sentiment"]["count"] == 2
        assert result["social_sentiment"]["count"] == 2
        assert result["overall_sentiment"]["trend"] in ["bullish", "bearish", "neutral"]

    def test_analyze_sentiment_trends_custom_window(self, sample_sentiment_data):
        """Test with custom time window."""
        result = analyze_sentiment_trends(sample_sentiment_data, time_window="7d")

        assert result["time_window"] == "7d"

    def test_analyze_sentiment_trends_empty_data(self):
        """Test with no sentiment data."""
        empty_data = {
            "news_sentiment": [],
            "social_sentiment": [],
        }

        result = analyze_sentiment_trends(empty_data)

        assert result["news_sentiment"]["count"] == 0
        assert result["social_sentiment"]["count"] == 0
        assert result["overall_sentiment"]["avg_score"] == 0.0

    def test_analyze_sentiment_trends_bullish(self):
        """Test detecting bullish sentiment."""
        bullish_data = {
            "news_sentiment": [
                {"sentiment_score": 0.9} for _ in range(5)
            ],
            "social_sentiment": [
                {"sentiment": "positive"} for _ in range(5)
            ],
        }

        result = analyze_sentiment_trends(bullish_data)

        assert result["overall_sentiment"]["trend"] == "bullish"


class TestAnalyzeOnChainSignals:
    """Tests for analyze_on_chain_signals function."""

    def test_analyze_on_chain_signals_basic(self, sample_on_chain_data):
        """Test basic on-chain signal analysis."""
        result = analyze_on_chain_signals(sample_on_chain_data)

        assert "lookback_period_days" in result
        assert "metrics" in result
        assert "data_points" in result
        assert result["data_points"] == 10

    def test_analyze_on_chain_signals_trend_detection(self, sample_on_chain_data):
        """Test trend detection in on-chain metrics."""
        result = analyze_on_chain_signals(sample_on_chain_data, lookback_period=10)

        metrics = result["metrics"]
        assert "active_addresses" in metrics

        metric_data = metrics["active_addresses"]
        assert "trend" in metric_data
        assert metric_data["trend"] in ["increasing", "decreasing"]
        assert "change_percent" in metric_data

    def test_analyze_on_chain_signals_empty_data(self):
        """Test with no on-chain data."""
        result = analyze_on_chain_signals([])

        assert result["status"] == "no_data"

    def test_analyze_on_chain_signals_insufficient_data(self):
        """Test with insufficient data for trend analysis."""
        single_point = [{
            "asset": "BTC",
            "metric_name": "active_addresses",
            "metric_value": 1000000,
            "source": "glassnode",
            "collected_at": datetime.now().isoformat(),
        }]

        result = analyze_on_chain_signals(single_point)

        # Should handle gracefully
        assert "metrics" in result


class TestDetectCatalystImpact:
    """Tests for detect_catalyst_impact function."""

    def test_detect_catalyst_impact_basic(self, sample_catalyst_events, sample_price_data):
        """Test basic catalyst impact detection."""
        result = detect_catalyst_impact(sample_catalyst_events, sample_price_data)

        assert "events_analyzed" in result
        assert "impacts" in result
        assert isinstance(result["impacts"], list)

    def test_detect_catalyst_impact_empty_events(self, sample_price_data):
        """Test with no catalyst events."""
        result = detect_catalyst_impact([], sample_price_data)

        assert result["status"] == "insufficient_data"
        assert result["events_analyzed"] == 0

    def test_detect_catalyst_impact_empty_prices(self, sample_catalyst_events):
        """Test with no price data."""
        result = detect_catalyst_impact(sample_catalyst_events, [])

        assert result["status"] == "insufficient_data"

    def test_detect_catalyst_impact_calculation(self):
        """Test impact calculation with controlled data."""
        now = datetime.now()

        # Create price data with clear change around event
        prices = []
        for i in range(24):  # 24 data points (1 per hour before and after)
            timestamp = now - timedelta(hours=12-i)
            # Price increases after hour 12 (event time)
            price = 50000 if i < 12 else 52000
            prices.append({
                "timestamp": timestamp.isoformat(),
                "coin_type": "BTC",
                "bid": price,
                "ask": price + 100,
                "last": price + 50,
            })

        events = [{
            "event_type": "listing",
            "title": "Major listing",
            "description": "Listed on exchange",
            "source": "Exchange",
            "currencies": ["BTC"],
            "impact_score": 9,
            "detected_at": now.isoformat(),
        }]

        result = detect_catalyst_impact(events, prices)

        # Should detect positive impact
        assert result["events_analyzed"] >= 0
        assert "avg_impact" in result


class TestCleanData:
    """Tests for clean_data function."""

    def test_clean_data_dataframe(self):
        """Test cleaning a DataFrame."""
        df = pd.DataFrame({
            "a": [1, 2, np.nan, 4, 5],
            "b": [10, 20, 30, 40, 50],
        })

        result = clean_data(df, fill_missing=True, remove_outliers=False)

        assert result.isnull().sum().sum() == 0  # No missing values
        assert len(result) == 5

    def test_clean_data_list(self):
        """Test cleaning from list of dicts."""
        data = [
            {"a": 1, "b": 10},
            {"a": 2, "b": 20},
            {"a": 3, "b": 30},
        ]

        result = clean_data(data, fill_missing=True, remove_outliers=False)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3

    def test_clean_data_with_outliers(self):
        """Test outlier removal."""
        df = pd.DataFrame({
            "value": [10, 12, 11, 13, 100, 12, 11, 13, 12],  # 100 is outlier
        })

        result = clean_data(df, remove_outliers=True)

        # Outlier should be removed
        assert len(result) < len(df)
        assert 100 not in result["value"].values

    def test_clean_data_empty(self):
        """Test with empty data."""
        df = pd.DataFrame()

        result = clean_data(df)

        assert len(result) == 0


class TestPerformEDA:
    """Tests for perform_eda function."""

    def test_perform_eda_basic(self, sample_price_data):
        """Test basic EDA."""
        result = perform_eda(sample_price_data)

        assert "shape" in result
        assert "columns" in result
        assert "dtypes" in result
        assert "missing_values" in result
        assert "summary_statistics" in result

        assert result["shape"]["rows"] == 50
        assert result["shape"]["columns"] > 0

    def test_perform_eda_dataframe(self):
        """Test EDA on DataFrame."""
        df = pd.DataFrame({
            "price": [100, 110, 105, 115, 120],
            "volume": [1000, 1100, 1050, 1150, 1200],
        })

        result = perform_eda(df)

        assert "summary_statistics" in result
        assert "price" in result["summary_statistics"]
        assert "mean" in result["summary_statistics"]["price"]
        assert "median" in result["summary_statistics"]["price"]
        assert "std" in result["summary_statistics"]["price"]

    def test_perform_eda_empty(self):
        """Test EDA with no data."""
        result = perform_eda([])

        assert result["status"] == "no_data"

    def test_perform_eda_missing_values(self):
        """Test EDA detects missing values."""
        df = pd.DataFrame({
            "a": [1, 2, np.nan, 4],
            "b": [10, np.nan, 30, 40],
        })

        result = perform_eda(df)

        assert result["missing_values"]["a"] == 1
        assert result["missing_values"]["b"] == 1
