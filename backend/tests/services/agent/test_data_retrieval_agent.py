"""
Tests for Enhanced DataRetrievalAgent - Week 3-4 Implementation

Tests the enhanced DataRetrievalAgent with comprehensive data retrieval capabilities.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.services.agent.agents.data_retrieval import DataRetrievalAgent


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    return Mock()


@pytest.fixture
def data_retrieval_agent(mock_session):
    """Create a DataRetrievalAgent with mock session."""
    agent = DataRetrievalAgent(session=mock_session)
    return agent


@pytest.fixture
def basic_state():
    """Create a basic workflow state."""
    return {
        "session_id": "test-session-123",
        "user_goal": "Analyze Bitcoin price data",
        "status": "running",
        "current_step": "data_retrieval",
        "iteration": 0,
        "data_retrieved": False,
        "messages": [],
        "retrieval_params": {
            "coin_type": "BTC",
            "days": 7,
            "include_price": True,
        },
    }


class TestDataRetrievalAgentInitialization:
    """Tests for agent initialization."""
    
    def test_agent_creation(self):
        """Test creating an agent."""
        agent = DataRetrievalAgent()
        
        assert agent.name == "DataRetrievalAgent"
        assert "cryptocurrency data" in agent.description.lower()
        assert agent.session is None
    
    def test_agent_with_session(self, mock_session):
        """Test creating an agent with session."""
        agent = DataRetrievalAgent(session=mock_session)
        
        assert agent.session == mock_session
    
    def test_set_session(self, mock_session):
        """Test setting session after creation."""
        agent = DataRetrievalAgent()
        agent.set_session(mock_session)
        
        assert agent.session == mock_session


class TestDataRetrievalAgentExecution:
    """Tests for agent execution."""
    
    @pytest.mark.asyncio
    async def test_execute_without_session(self, basic_state):
        """Test execution fails without session."""
        agent = DataRetrievalAgent()
        
        result = await agent.execute(basic_state)
        
        assert result["error"] == "Database session not configured"
        assert result["data_retrieved"] is False
    
    @pytest.mark.asyncio
    @patch("app.services.agent.agents.data_retrieval.get_available_coins")
    @patch("app.services.agent.agents.data_retrieval.get_data_statistics")
    @patch("app.services.agent.agents.data_retrieval.fetch_price_data")
    async def test_execute_basic_price_data(
        self, mock_fetch_price, mock_stats, mock_coins,
        data_retrieval_agent, basic_state
    ):
        """Test basic execution fetching price data."""
        # Setup mocks
        mock_coins.return_value = ["BTC", "ETH", "ADA"]
        mock_stats.return_value = {"price_data": {"total_records": 1000}}
        mock_fetch_price.return_value = [
            {
                "timestamp": datetime.now().isoformat(),
                "coin_type": "BTC",
                "bid": 50000.0,
                "ask": 50100.0,
                "last": 50050.0,
            }
        ]
        
        # Execute
        result = await data_retrieval_agent.execute(basic_state)
        
        # Verify
        assert result["data_retrieved"] is True
        assert "retrieved_data" in result
        assert "price_data" in result["retrieved_data"]
        assert "available_coins" in result["retrieved_data"]
        assert "data_statistics" in result["retrieved_data"]
        assert result["message"] == "Successfully retrieved data for BTC"
    
    @pytest.mark.asyncio
    @patch("app.services.agent.agents.data_retrieval.get_available_coins")
    @patch("app.services.agent.agents.data_retrieval.get_data_statistics")
    @patch("app.services.agent.agents.data_retrieval.fetch_price_data")
    @patch("app.services.agent.agents.data_retrieval.fetch_sentiment_data")
    async def test_execute_with_sentiment(
        self, mock_sentiment, mock_price, mock_stats, mock_coins,
        data_retrieval_agent
    ):
        """Test execution with sentiment data request."""
        state = {
            "user_goal": "Analyze Bitcoin price and sentiment",
            "retrieval_params": {
                "coin_type": "BTC",
                "include_sentiment": True,
            },
        }
        
        # Setup mocks
        mock_coins.return_value = ["BTC"]
        mock_stats.return_value = {"price_data": {}}
        mock_price.return_value = []
        mock_sentiment.return_value = {
            "news_sentiment": [],
            "social_sentiment": [],
        }
        
        # Execute
        result = await data_retrieval_agent.execute(state)
        
        # Verify sentiment was fetched
        assert result["data_retrieved"] is True
        assert "sentiment_data" in result["retrieved_data"]
        mock_sentiment.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("app.services.agent.agents.data_retrieval.get_available_coins")
    @patch("app.services.agent.agents.data_retrieval.get_data_statistics")
    @patch("app.services.agent.agents.data_retrieval.fetch_price_data")
    @patch("app.services.agent.agents.data_retrieval.fetch_on_chain_metrics")
    async def test_execute_with_onchain(
        self, mock_onchain, mock_price, mock_stats, mock_coins,
        data_retrieval_agent
    ):
        """Test execution with on-chain metrics request."""
        state = {
            "user_goal": "Analyze on-chain metrics for Bitcoin",
            "retrieval_params": {
                "coin_type": "BTC",
            },
        }
        
        # Setup mocks
        mock_coins.return_value = ["BTC"]
        mock_stats.return_value = {}
        mock_price.return_value = []
        mock_onchain.return_value = []
        
        # Execute
        result = await data_retrieval_agent.execute(state)
        
        # Verify on-chain was fetched (because "on-chain" in goal)
        assert result["data_retrieved"] is True
        assert "on_chain_metrics" in result["retrieved_data"]
        mock_onchain.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("app.services.agent.agents.data_retrieval.get_available_coins")
    @patch("app.services.agent.agents.data_retrieval.get_data_statistics")
    @patch("app.services.agent.agents.data_retrieval.fetch_price_data")
    @patch("app.services.agent.agents.data_retrieval.fetch_catalyst_events")
    async def test_execute_with_catalysts(
        self, mock_catalysts, mock_price, mock_stats, mock_coins,
        data_retrieval_agent
    ):
        """Test execution with catalyst events request."""
        state = {
            "user_goal": "Analyze catalyst events impact",
            "retrieval_params": {
                "coin_type": "BTC",
            },
        }
        
        # Setup mocks
        mock_coins.return_value = ["BTC"]
        mock_stats.return_value = {}
        mock_price.return_value = []
        mock_catalysts.return_value = []
        
        # Execute
        result = await data_retrieval_agent.execute(state)
        
        # Verify catalysts were fetched (because "catalyst" in goal)
        assert result["data_retrieved"] is True
        assert "catalyst_events" in result["retrieved_data"]
        mock_catalysts.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("app.services.agent.agents.data_retrieval.get_available_coins")
    async def test_execute_with_exception(
        self, mock_coins, data_retrieval_agent, basic_state
    ):
        """Test execution handles exceptions gracefully."""
        # Make mock raise exception
        mock_coins.side_effect = Exception("Database error")
        
        # Execute
        result = await data_retrieval_agent.execute(basic_state)
        
        # Verify error handling
        assert result["data_retrieved"] is False
        assert "error" in result
        assert "Database error" in result["error"]
    
    @pytest.mark.asyncio
    @patch("app.services.agent.agents.data_retrieval.get_available_coins")
    @patch("app.services.agent.agents.data_retrieval.get_data_statistics")
    @patch("app.services.agent.agents.data_retrieval.fetch_price_data")
    async def test_execute_metadata(
        self, mock_price, mock_stats, mock_coins,
        data_retrieval_agent, basic_state
    ):
        """Test that metadata is properly populated."""
        # Setup mocks
        mock_coins.return_value = ["BTC"]
        mock_stats.return_value = {}
        mock_price.return_value = []
        
        # Execute
        result = await data_retrieval_agent.execute(basic_state)
        
        # Verify metadata
        assert "retrieval_metadata" in result
        metadata = result["retrieval_metadata"]
        assert "coin_type" in metadata
        assert "start_date" in metadata
        assert "end_date" in metadata
        assert "data_types" in metadata
        assert metadata["coin_type"] == "BTC"
    
    @pytest.mark.asyncio
    @patch("app.services.agent.agents.data_retrieval.get_available_coins")
    @patch("app.services.agent.agents.data_retrieval.get_data_statistics")
    @patch("app.services.agent.agents.data_retrieval.fetch_price_data")
    async def test_execute_custom_timerange(
        self, mock_price, mock_stats, mock_coins,
        data_retrieval_agent
    ):
        """Test execution with custom time range."""
        state = {
            "user_goal": "Get recent data",
            "retrieval_params": {
                "coin_type": "ETH",
                "days": 14,  # Custom 14 days
            },
        }
        
        # Setup mocks
        mock_coins.return_value = ["ETH"]
        mock_stats.return_value = {}
        mock_price.return_value = []
        
        # Execute
        result = await data_retrieval_agent.execute(state)
        
        # Verify custom parameters were used
        assert result["data_retrieved"] is True
        metadata = result["retrieval_metadata"]
        assert metadata["coin_type"] == "ETH"
        
        # Verify fetch_price_data was called with correct dates
        call_args = mock_price.call_args
        start_date = call_args[0][2]  # Third argument
        end_date = call_args[0][3]    # Fourth argument
        
        # Time difference should be approximately 14 days
        time_diff = end_date - start_date
        assert 13 <= time_diff.days <= 15  # Allow small variance
