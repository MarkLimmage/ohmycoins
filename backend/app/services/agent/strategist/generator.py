
import logging
import json
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from typing import Any

from sqlmodel import Session
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

from app.services.agent.llm_factory import LLMFactory
from app.services.backtesting.engine import BacktestService
from app.services.backtesting.schemas import BacktestConfig, BacktestResult

logger = logging.getLogger(__name__)

class StrategyParams(BaseModel):
    strategy_name: str = Field(description="Name of the strategy")
    fast_window: int = Field(description="Window size for the fast moving average")
    slow_window: int = Field(description="Window size for the slow moving average")

class StrategyGenerator:
    """
    Service for generating trading strategies using LLM and backtesting them.
    """
    def __init__(self, session: Session, user_id: UUID):
        self.session = session
        self.user_id = user_id
        self.backtest_service = BacktestService(session)
        self.llm = LLMFactory.create_llm(session=session, user_id=user_id)

    async def generate_and_backtest(
        self, 
        prompt: str, 
        coin_type: str, 
        start_date: datetime, 
        end_date: datetime, 
        initial_capital: Decimal = Decimal("10000.0")
    ) -> BacktestResult:
        """
        Generates strategy parameters from a prompt and runs a backtest.
        """
        logger.info(f"Generating strategy for: {prompt}")

        # 1. Define LLM Prompt
        parser = JsonOutputParser(pydantic_object=StrategyParams)
        
        system_prompt = """You are an expert quantitative strategist. 
        Your goal is to translate a user's trading idea into parameters for a Moving Average Crossover strategy.
        The Strategy Engine accepts:
        - fast_window (int): Short period MA. Must be > 0.
        - slow_window (int): Long period MA. Must be > fast_window.
        
        Interpret the user's intent. If they want 'aggressive', use tighter windows. If 'conservative', use wider windows.
        
        Output valid JSON only.
        """
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{query}\n\n{format_instructions}")
        ])

        chain = prompt_template | self.llm | parser

        # 2. Invoke LLM
        try:
            # Note: We use execute synchronously in this sprint context if async environment is tricky,
            # but usually LLM calls should be async. The standard `BacktestService.run_backtest` is sync.
            # So the wrapper method is async but calling sync backtest is fine.
            strategy_params = await chain.ainvoke({
                "query": prompt,
                "format_instructions": parser.get_format_instructions()
            })
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            # Fallback for resiliency
            strategy_params = {
                "strategy_name": "Fallback-Strategy",
                "fast_window": 10,
                "slow_window": 30
            }

        logger.info(f"Generated parameters: {strategy_params}")

        # Validate params
        fast = strategy_params.get("fast_window", 10)
        slow = strategy_params.get("slow_window", 30)
        
        if fast >= slow:
            # Fix invalid params
            slow = fast + 10

        # 3. Construct Config
        config = BacktestConfig(
            strategy_name=strategy_params.get("strategy_name", "LLM-Gen-Strategy"),
            coin_type=coin_type,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            parameters={
                "fast_window": fast,
                "slow_window": slow
            }
        )

        # 4. Run Backtest
        result = self.backtest_service.run_backtest(config)
        
        return result
