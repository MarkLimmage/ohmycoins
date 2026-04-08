"""Gemini-based sentiment analysis provider."""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.exceptions import LangChainException
from sqlmodel import Session, select

from app.enrichment.providers.base import (
    CoinSentiment,
    ISentimentProvider,
    SentimentResult,
    TextInput,
)
from app.models import UserLLMCredentials
from app.services.agent.llm_factory import LLMFactory
from app.services.encryption import encryption_service

logger = logging.getLogger(__name__)

# Default batch size for analyse_batch
BATCH_SIZE = 5
MAX_BATCH_SIZE = 10


def _extract_text(content: Any) -> str:
    """Extract text from LangChain response content.

    langchain-google-genai 4.x returns content as a list of parts
    (e.g. [{'type': 'text', 'text': '...', 'extras': {...}}]) rather
    than a plain string.  Handle both formats.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            p["text"]
            for p in content
            if isinstance(p, dict) and p.get("type") == "text" and "text" in p
        ]
        return "\n".join(parts)
    logger.warning("Unexpected LLM content type: %s", type(content).__name__)
    return str(content)


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
            UserLLMCredentials.is_active == True,  # noqa: E712
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
            content = _extract_text(
                response.content if hasattr(response, "content") else str(response)
            )

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
                        logger.warning("Skipping malformed coin entry: missing symbol")
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

    async def analyse_batch(self, inputs: list[TextInput]) -> list[CoinSentiment]:
        """
        Batch analysis of multiple text inputs in a single Gemini call.

        Groups inputs into batches of BATCH_SIZE, builds a batched prompt,
        and parses per-item, per-coin results. Falls back to single-item
        on JSON parse failure.
        """
        await self._ensure_llm_loaded()

        all_results: list[CoinSentiment] = []

        # Process in batches
        for i in range(0, len(inputs), BATCH_SIZE):
            batch = inputs[i : i + BATCH_SIZE]
            try:
                batch_results = await self._analyse_batch_chunk(batch)
                all_results.extend(batch_results)
            except Exception as e:
                logger.warning(f"Batch analysis failed, falling back to single: {e}")
                # Fallback: process each item individually
                for single_input in batch:
                    try:
                        single_results = await self._analyse_batch_chunk([single_input])
                        all_results.extend(single_results)
                    except Exception as e2:
                        logger.error(
                            f"Single-item fallback failed for source_id={single_input.source_id}: {e2}"
                        )

        return all_results

    async def _analyse_batch_chunk(
        self, inputs: list[TextInput]
    ) -> list[CoinSentiment]:
        """Analyze a single batch chunk via Gemini."""
        prompt = self._build_batch_prompt(inputs)

        response = await self._llm.ainvoke(prompt)
        content = _extract_text(
            response.content if hasattr(response, "content") else str(response)
        )

        return self._parse_batch_response(content, inputs)

    def _build_batch_prompt(self, inputs: list[TextInput]) -> str:
        """Build a batched prompt for multiple text inputs."""
        items_text = ""
        for idx, inp in enumerate(inputs):
            meta = inp.metadata
            items_text += f"\n--- ITEM {idx + 1} (source_id: {inp.source_id}) ---\n"
            items_text += f"Text: {inp.text}\n"
            if meta.get("score") is not None:
                items_text += f"Engagement score: {meta['score']}\n"
            if meta.get("comment_count") is not None:
                items_text += f"Comment count: {meta['comment_count']}\n"
            if meta.get("platform"):
                items_text += f"Platform: {meta['platform']}\n"

        return f"""Analyze the following {len(inputs)} social media posts about cryptocurrency for sentiment and per-coin impact.

{items_text}

For each item, extract sentiment for each mentioned cryptocurrency. Return ONLY valid JSON in this format:
{{
  "results": [
    {{
      "source_id": 123,
      "coins": [
        {{"symbol": "BTC", "score": 0.7, "confidence": 0.85, "rationale": "Strong bullish signals"}},
        {{"symbol": "ETH", "score": -0.3, "confidence": 0.6, "rationale": "Bearish due to sell pressure"}}
      ]
    }}
  ]
}}

Rules:
- score: -1.0 (max bearish) to 1.0 (max bullish), 0.0 = neutral
- confidence: 0.0 to 1.0
- symbol: standard crypto ticker (BTC, ETH, SOL, etc.)
- Only include cryptocurrencies actually mentioned or clearly implied
- If no crypto is mentioned, return empty coins array for that item
- source_id MUST match the source_id from the input

Return ONLY the JSON object, no additional text."""

    def _parse_batch_response(
        self, content: str, inputs: list[TextInput]
    ) -> list[CoinSentiment]:
        """Parse batch response from Gemini into CoinSentiment results."""
        try:
            json_str = content.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            data = json.loads(json_str)

            results: list[CoinSentiment] = []
            # Build source_id lookup for validation
            valid_source_ids = {inp.source_id for inp in inputs}

            if isinstance(data, dict) and "results" in data:
                for item_result in data["results"]:
                    source_id = item_result.get("source_id")
                    if source_id not in valid_source_ids:
                        logger.warning(
                            f"Skipping result with unknown source_id: {source_id}"
                        )
                        continue

                    for coin_data in item_result.get("coins", []):
                        symbol = coin_data.get("symbol", "").upper()
                        if not symbol:
                            continue

                        try:
                            results.append(
                                CoinSentiment(
                                    coin=symbol,
                                    score=max(-1.0, min(1.0, float(coin_data.get("score", 0.0)))),
                                    confidence=max(0.0, min(1.0, float(coin_data.get("confidence", 0.0)))),
                                    rationale=coin_data.get("rationale", ""),
                                    source_id=source_id,
                                )
                            )
                        except (ValueError, TypeError):
                            logger.warning(f"Skipping malformed coin entry: {coin_data}")

            return results

        except json.JSONDecodeError:
            logger.error(
                f"Could not parse batch Gemini response as JSON: {content[:200]}"
            )
            raise  # Let caller handle fallback to single-item
