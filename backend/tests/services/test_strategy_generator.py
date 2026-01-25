
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from app.services.agent.strategist.generator import StrategyGenerator
from app.models import PriceData5Min

@pytest.mark.asyncio
async def test_strategy_gen_flow(session):
    # 1. Setup Data
    start_ts = 1700000000
    for i in range(60):
        session.add(PriceData5Min(
            coin_type="BTC",
            timestamp=datetime.fromtimestamp(start_ts + i*300),
            last=Decimal(100.0 + (i * 1.0)), # Strong uptrend
            bid=Decimal(99.0 + (i * 1.0)),
            ask=Decimal(101.0 + (i * 1.0))
        ))
    session.commit()

    # 2. Mock Chain Construction
    mock_chain = AsyncMock()
    mock_chain.ainvoke.return_value = {
        "strategy_name": "Test Strat",
        "fast_window": 5,
        "slow_window": 15
    }

    with patch("app.services.agent.strategist.generator.ChatPromptTemplate") as MockPromptCls:
        # Mock the pipeline: prompt | llm | parser
        mock_prompt_instance = MagicMock()
        MockPromptCls.from_messages.return_value = mock_prompt_instance
        
        # prompt | llm
        mock_intermediate = MagicMock()
        mock_prompt_instance.__or__.return_value = mock_intermediate
        
        # (prompt | llm) | parser -> chain
        mock_intermediate.__or__.return_value = mock_chain
        
        # Initialize Service
        # We also need to patch LLMFactory to avoid attempts to load real creds/models
        with patch("app.services.agent.strategist.generator.LLMFactory") as MockFactory:
            MockFactory.create_llm.return_value = MagicMock()
            
            generator = StrategyGenerator(session, uuid4())
            
            # Execute
            result = await generator.generate_and_backtest(
                prompt="Make me rich",
                coin_type="BTC",
                start_date=datetime.fromtimestamp(start_ts),
                end_date=datetime.fromtimestamp(start_ts + 60*300)
            )
            
            # Assertions
            assert result.strategy_name == "Test Strat"
            # With purely uptrending price:
            # fast (5) > slow (15) eventually.
            # Should have at least one trade or hold position.
            # MA(5) of 0..4 = 2.0. MA(15) is undefined until 14.
            # Eventually fast > slow.
            assert result is not None
            assert mock_chain.ainvoke.called

