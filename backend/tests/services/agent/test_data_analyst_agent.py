"""
Tests for DataAnalystAgent - Week 3-4 Implementation

Tests the new DataAnalystAgent with comprehensive data analysis capabilities.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, Mock

from app.services.agent.agents.data_analyst import DataAnalystAgent


@pytest.fixture
def data_analyst_agent():
    """Create a DataAnalystAgent."""
    return DataAnalystAgent()


@pytest.fixture
def state_with_price_data():
    """Create a state with price data."""
    return {
        "user_goal": "Analyze Bitcoin price trends",
        "retrieved_data": {
            "price_data": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "coin_type": "BTC",
                    "bid": 50000.0,
                    "ask": 50100.0,
                    "last": 50050.0,
                }
                for _ in range(50)
            ],
        },
        "analysis_params": {},
    }


@pytest.fixture
def state_with_sentiment_data():
    """Create a state with sentiment data."""
    return {
        "user_goal": "Analyze market sentiment",
        "retrieved_data": {
            "sentiment_data": {
                "news_sentiment": [
                    {
                        "sentiment_score": 0.8,
                    }
                ],
                "social_sentiment": [
                    {
                        "sentiment": "positive",
                    }
                ],
            },
        },
        "analysis_params": {},
    }


@pytest.fixture
def state_with_all_data():
    """Create a state with comprehensive data."""
    return {
        "user_goal": "Comprehensive analysis",
        "retrieved_data": {
            "price_data": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "coin_type": "BTC",
                    "bid": 50000.0 + i * 100,
                    "ask": 50100.0 + i * 100,
                    "last": 50050.0 + i * 100,
                }
                for i in range(50)
            ],
            "sentiment_data": {
                "news_sentiment": [{"sentiment_score": 0.8}],
                "social_sentiment": [{"sentiment": "positive"}],
            },
            "on_chain_metrics": [
                {
                    "asset": "BTC",
                    "metric_name": "active_addresses",
                    "metric_value": 1000000.0,
                    "source": "glassnode",
                    "collected_at": datetime.now().isoformat(),
                }
            ],
            "catalyst_events": [
                {
                    "event_type": "listing",
                    "title": "Major listing",
                    "description": "Listed on exchange",
                    "source": "Exchange",
                    "currencies": ["BTC"],
                    "impact_score": 8,
                    "detected_at": datetime.now().isoformat(),
                }
            ],
        },
        "analysis_params": {},
    }


class TestDataAnalystAgentInitialization:
    """Tests for agent initialization."""
    
    def test_agent_creation(self):
        """Test creating an agent."""
        agent = DataAnalystAgent()
        
        assert agent.name == "DataAnalystAgent"
        assert "analyzes" in agent.description.lower()


class TestDataAnalystAgentExecution:
    """Tests for agent execution."""
    
    @pytest.mark.asyncio
    async def test_execute_no_data(self, data_analyst_agent):
        """Test execution with no retrieved data."""
        state = {
            "user_goal": "Analyze data",
            "retrieved_data": {},
        }
        
        result = await data_analyst_agent.execute(state)
        
        assert result["analysis_completed"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    @patch("app.services.agent.agents.data_analyst.perform_eda")
    @patch("app.services.agent.agents.data_analyst.calculate_technical_indicators")
    async def test_execute_price_data_analysis(
        self, mock_calc_indicators, mock_eda,
        data_analyst_agent, state_with_price_data
    ):
        """Test analysis with price data."""
        # Setup mocks
        mock_eda.return_value = {"shape": {"rows": 50}}
        mock_df = Mock()
        mock_df.columns = ["close", "rsi", "sma_20"]
        mock_df.select_dtypes.return_value.columns = ["close", "rsi", "sma_20"]
        mock_df.__len__ = Mock(return_value=50)
        mock_df.iloc = Mock()
        mock_df.iloc.__getitem__ = Mock(return_value=Mock(to_dict=Mock(return_value={"rsi": 55.0})))
        
        # Setup mean and std mocks
        series_mock = Mock()
        series_mock.mean.return_value = 50.0
        series_mock.std.return_value = 5.0
        mock_df.__getitem__ = Mock(return_value=series_mock)
        
        mock_calc_indicators.return_value = mock_df
        
        # Execute
        result = await data_analyst_agent.execute(state_with_price_data)
        
        # Verify
        assert result["analysis_completed"] is True
        assert "analysis_results" in result
        assert "technical_indicators" in result["analysis_results"]
        assert "insights" in result
        mock_calc_indicators.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("app.services.agent.agents.data_analyst.analyze_sentiment_trends")
    async def test_execute_sentiment_analysis(
        self, mock_sentiment_analysis,
        data_analyst_agent, state_with_sentiment_data
    ):
        """Test analysis with sentiment data."""
        # Setup mock
        mock_sentiment_analysis.return_value = {
            "overall_sentiment": {
                "trend": "bullish",
                "avg_score": 0.7,
            },
            "news_sentiment": {"count": 1},
            "social_sentiment": {"count": 1},
        }
        
        # Execute
        result = await data_analyst_agent.execute(state_with_sentiment_data)
        
        # Verify
        assert result["analysis_completed"] is True
        assert "sentiment_analysis" in result["analysis_results"]
        mock_sentiment_analysis.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("app.services.agent.agents.data_analyst.perform_eda")
    @patch("app.services.agent.agents.data_analyst.calculate_technical_indicators")
    @patch("app.services.agent.agents.data_analyst.analyze_sentiment_trends")
    @patch("app.services.agent.agents.data_analyst.analyze_on_chain_signals")
    @patch("app.services.agent.agents.data_analyst.detect_catalyst_impact")
    async def test_execute_comprehensive_analysis(
        self, mock_catalyst, mock_onchain, mock_sentiment,
        mock_indicators, mock_eda,
        data_analyst_agent, state_with_all_data
    ):
        """Test comprehensive analysis with all data types."""
        # Setup mocks
        mock_eda.return_value = {"shape": {}}
        
        mock_df = Mock()
        mock_df.columns = ["close"]
        mock_df.select_dtypes.return_value.columns = ["close"]
        mock_df.__len__ = Mock(return_value=50)
        mock_df.iloc = Mock()
        mock_df.iloc.__getitem__ = Mock(return_value=Mock(to_dict=Mock(return_value={})))
        series_mock = Mock()
        series_mock.mean.return_value = 50.0
        series_mock.std.return_value = 5.0
        mock_df.__getitem__ = Mock(return_value=series_mock)
        mock_indicators.return_value = mock_df
        
        mock_sentiment.return_value = {"overall_sentiment": {"trend": "bullish"}}
        mock_onchain.return_value = {"metrics": {}}
        mock_catalyst.return_value = {"events_analyzed": 1, "avg_impact": 2.5}
        
        # Execute
        result = await data_analyst_agent.execute(state_with_all_data)
        
        # Verify all analyses were performed
        assert result["analysis_completed"] is True
        assert "technical_indicators" in result["analysis_results"]
        assert "sentiment_analysis" in result["analysis_results"]
        assert "on_chain_signals" in result["analysis_results"]
        assert "catalyst_impact" in result["analysis_results"]
        
        # Verify all mocks were called
        mock_indicators.assert_called_once()
        mock_sentiment.assert_called_once()
        mock_onchain.assert_called_once()
        mock_catalyst.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("app.services.agent.agents.data_analyst.perform_eda")
    async def test_execute_with_exception(
        self, mock_eda, data_analyst_agent, state_with_price_data
    ):
        """Test execution handles exceptions gracefully."""
        # Make mock raise exception
        mock_eda.side_effect = Exception("Analysis error")
        
        # Execute
        result = await data_analyst_agent.execute(state_with_price_data)
        
        # Verify error handling
        assert result["analysis_completed"] is False
        assert "error" in result
        assert "Analysis error" in result["error"]
    
    @pytest.mark.asyncio
    @patch("app.services.agent.agents.data_analyst.perform_eda")
    @patch("app.services.agent.agents.data_analyst.calculate_technical_indicators")
    async def test_execute_generates_insights(
        self, mock_indicators, mock_eda,
        data_analyst_agent, state_with_price_data
    ):
        """Test that insights are generated."""
        # Setup mocks
        mock_eda.return_value = {}
        
        mock_df = Mock()
        mock_df.columns = ["close", "rsi"]
        mock_df.select_dtypes.return_value.columns = ["close", "rsi"]
        mock_df.__len__ = Mock(return_value=50)
        mock_df.iloc = Mock()
        mock_df.iloc.__getitem__ = Mock(return_value=Mock(to_dict=Mock(return_value={"rsi": 75.0})))  # Overbought
        series_mock = Mock()
        series_mock.mean.return_value = 50.0
        series_mock.std.return_value = 5.0
        mock_df.__getitem__ = Mock(return_value=series_mock)
        mock_indicators.return_value = mock_df
        
        # Execute
        result = await data_analyst_agent.execute(state_with_price_data)
        
        # Verify insights were generated
        assert "insights" in result
        assert isinstance(result["insights"], list)
        assert len(result["insights"]) > 0


class TestDataAnalystAgentInsightGeneration:
    """Tests for insight generation logic."""
    
    def test_generate_insights_rsi_overbought(self, data_analyst_agent):
        """Test RSI overbought insight."""
        analysis_results = {
            "technical_indicators": {
                "latest_values": {"rsi": 75.0}
            }
        }
        
        insights = data_analyst_agent._generate_insights(
            analysis_results, "analyze price"
        )
        
        assert len(insights) > 0
        assert any("overbought" in insight.lower() for insight in insights)
    
    def test_generate_insights_rsi_oversold(self, data_analyst_agent):
        """Test RSI oversold insight."""
        analysis_results = {
            "technical_indicators": {
                "latest_values": {"rsi": 25.0}
            }
        }
        
        insights = data_analyst_agent._generate_insights(
            analysis_results, "analyze price"
        )
        
        assert len(insights) > 0
        assert any("oversold" in insight.lower() for insight in insights)
    
    def test_generate_insights_sentiment_bullish(self, data_analyst_agent):
        """Test bullish sentiment insight."""
        analysis_results = {
            "sentiment_analysis": {
                "overall_sentiment": {"trend": "bullish"}
            }
        }
        
        insights = data_analyst_agent._generate_insights(
            analysis_results, "analyze sentiment"
        )
        
        assert len(insights) > 0
        assert any("bullish" in insight.lower() for insight in insights)
    
    def test_generate_insights_sentiment_bearish(self, data_analyst_agent):
        """Test bearish sentiment insight."""
        analysis_results = {
            "sentiment_analysis": {
                "overall_sentiment": {"trend": "bearish"}
            }
        }
        
        insights = data_analyst_agent._generate_insights(
            analysis_results, "analyze sentiment"
        )
        
        assert len(insights) > 0
        assert any("bearish" in insight.lower() for insight in insights)
    
    def test_generate_insights_onchain_trend(self, data_analyst_agent):
        """Test on-chain trend insight."""
        analysis_results = {
            "on_chain_signals": {
                "metrics": {
                    "active_addresses": {
                        "trend": "increasing",
                        "change_percent": 25.0
                    }
                }
            }
        }
        
        insights = data_analyst_agent._generate_insights(
            analysis_results, "analyze on-chain"
        )
        
        assert len(insights) > 0
        assert any("active_addresses" in insight for insight in insights)
        assert any("increasing" in insight for insight in insights)
    
    def test_generate_insights_catalyst_impact(self, data_analyst_agent):
        """Test catalyst impact insight."""
        analysis_results = {
            "catalyst_impact": {
                "events_analyzed": 3,
                "avg_impact": 6.5
            }
        }
        
        insights = data_analyst_agent._generate_insights(
            analysis_results, "analyze catalysts"
        )
        
        assert len(insights) > 0
        assert any("catalyst" in insight.lower() for insight in insights)
    
    def test_generate_insights_no_patterns(self, data_analyst_agent):
        """Test default insight when no patterns detected."""
        analysis_results = {}
        
        insights = data_analyst_agent._generate_insights(
            analysis_results, "analyze"
        )
        
        assert len(insights) == 1
        assert "no significant patterns" in insights[0].lower()
