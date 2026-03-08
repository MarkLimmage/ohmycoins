"""Gemini-based sentiment analysis provider."""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.exceptions import LangChainException
from sqlmodel import Session, select

from app.enrichment.providers.base import ISentimentProvider, SentimentResult
from app.models import UserLLMCredentials
from app.services.agent.llm_factory import LLMFactory
from app.services.encryption import encryption_service

logger = logging.getLogger(__name__)


class GeminiSentimentProvider(ISentimentProvider):
    """Gemini-based sentiment analysis using LLMFactory credentials."""

    def __init__(self, session: Session):
        """Initialize with database session to load credentials."""
        self.session = session
        self._llm: Any = None

    async def _ensure_llm_loaded(self) -> None:
        """Load LLM instance from database credentials."""
        if self._llm is not None:
            return

        # Load active Google credential from database
        statement = select(UserLLMCredentials).where(
            UserLLMCredentials.provider == "google",
            UserLLMCredentials.is_active is True,
        )
        credential = self.session.exec(statement).first()

        if not credential:
            raise ValueError(
                "No active Google credential found. "
                "Please configure a Gemini API key in the system."
            )

        # Decrypt API key and create LLM instance
        api_key = encryption_service.decrypt_api_key(credential.encrypted_api_key)
        self._llm = LLMFactory.create_llm_from_api_key(
            provider="google", api_key=api_key, model_name=credential.model_name
        )
        logger.info(f"Loaded Gemini provider with model {credential.model_name}")

    async def analyse(self, title: str, summary: str) -> list[SentimentResult]:
        """
        Analyze sentiment from title and summary using Gemini.

        Returns per-coin sentiment results extracted from LLM response.
        """
        await self._ensure_llm_loaded()

        # Build the prompt for sentiment analysis
        prompt = self._build_prompt(title, summary)

        try:
            # Call Gemini LLM
            response = await self._llm.ainvoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)

            # Parse JSON response
            results = self._parse_response(content)
            logger.debug(f"Gemini analysis: {len(results)} coins found")
            return results

        except LangChainException as e:
            logger.error(f"Gemini API error: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            return []

    def _build_prompt(self, title: str, summary: str) -> str:
        """Build the sentiment analysis prompt for Gemini."""
        return f"""Analyze the following crypto news for sentiment and per-coin impact.

Title: {title}
Summary: {summary}

Extract sentiment for each mentioned cryptocurrency as valid JSON. Return ONLY valid JSON in this format:
{{
  "coins": [
    {{"symbol": "BTC", "sentiment": "bullish", "confidence": 0.85, "rationale": "Bitcoin shows strong support levels"}},
    {{"symbol": "ETH", "sentiment": "neutral", "confidence": 0.5, "rationale": "Ethereum awaiting regulatory clarity"}}
  ],
  "overall_sentiment": "mixed",
  "event_type": "regulatory"
}}

Possible sentiment values: "bullish", "bearish", "neutral"
Confidence: 0.0 to 1.0
event_type: one of "regulatory", "technical", "macro", "fundamental"

Return ONLY the JSON object, no additional text."""

    def _parse_response(self, content: str) -> list[SentimentResult]:
        """
        Parse JSON response from Gemini.

        Handles malformed JSON gracefully.
        """
        try:
            # Try to extract JSON from response
            json_str = content.strip()

            # If response contains markdown code blocks, extract JSON
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            data = json.loads(json_str)

            # Extract coin results
            results: list[SentimentResult] = []
            if isinstance(data, dict) and "coins" in data:
                for coin_data in data.get("coins", []):
                    # Skip entries missing required fields
                    if not coin_data.get("symbol"):
                        logger.warning(f"Skipping malformed coin entry: missing symbol")
                        continue
                    # Skip entries missing sentiment (core field for sentiment analysis)
                    if not coin_data.get("sentiment"):
                        logger.warning(
                            f"Skipping malformed coin entry {coin_data.get('symbol')}: missing sentiment"
                        )
                        continue

                    try:
                        result = SentimentResult(
                            coin=coin_data.get("symbol", "UNKNOWN").upper(),
                            direction=coin_data.get("sentiment", "neutral").lower(),
                            confidence=float(coin_data.get("confidence", 0.0)),
                            rationale=coin_data.get("rationale", ""),
                        )
                        results.append(result)
                    except (KeyError, ValueError, TypeError):
                        logger.warning(f"Skipping malformed coin entry: {coin_data}")

            return results

        except json.JSONDecodeError:
            logger.error(f"Could not parse Gemini response as JSON: {content[:200]}")
            return []
