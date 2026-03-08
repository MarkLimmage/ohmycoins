"""Tests for the GeminiSentimentProvider."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlmodel import Session

from app.enrichment.providers.gemini import GeminiSentimentProvider


@pytest.mark.asyncio
async def test_gemini_provider_parses_json_response() -> None:
    """Test that provider parses JSON response correctly."""
    # Create a mock LLM
    mock_llm_response = MagicMock()
    mock_llm_response.content = json.dumps(
        {
            "coins": [
                {"symbol": "BTC", "sentiment": "bullish", "confidence": 0.9, "rationale": "Strong support"}
            ],
            "overall_sentiment": "bullish",
            "event_type": "technical",
        }
    )

    provider = GeminiSentimentProvider(MagicMock(spec=Session))
    provider._llm = MagicMock()
    provider._llm.ainvoke = AsyncMock(return_value=mock_llm_response)

    results = await provider.analyse("Bitcoin surge", "BTC is surging")

    assert len(results) == 1
    assert results[0].coin == "BTC"
    assert results[0].direction == "bullish"
    assert results[0].confidence == 0.9


@pytest.mark.asyncio
async def test_gemini_provider_handles_multiple_coins() -> None:
    """Test that provider handles multiple coins in response."""
    mock_llm_response = MagicMock()
    mock_llm_response.content = json.dumps(
        {
            "coins": [
                {"symbol": "BTC", "sentiment": "bullish", "confidence": 0.85, "rationale": "Strong momentum"},
                {"symbol": "ETH", "sentiment": "neutral", "confidence": 0.5, "rationale": "Awaiting clarity"},
                {"symbol": "XRP", "sentiment": "bearish", "confidence": 0.7, "rationale": "Regulatory pressure"},
            ],
            "overall_sentiment": "mixed",
            "event_type": "regulatory",
        }
    )

    provider = GeminiSentimentProvider(MagicMock(spec=Session))
    provider._llm = MagicMock()
    provider._llm.ainvoke = AsyncMock(return_value=mock_llm_response)

    results = await provider.analyse("Crypto news", "Mixed crypto market")

    assert len(results) == 3
    coins = {r.coin for r in results}
    assert coins == {"BTC", "ETH", "XRP"}


@pytest.mark.asyncio
async def test_gemini_provider_handles_markdown_code_blocks() -> None:
    """Test that provider extracts JSON from markdown code blocks."""
    json_data = {
        "coins": [{"symbol": "BTC", "sentiment": "bullish", "confidence": 0.9, "rationale": "Test"}],
        "overall_sentiment": "bullish",
        "event_type": "technical",
    }

    mock_llm_response = MagicMock()
    mock_llm_response.content = f"```json\n{json.dumps(json_data)}\n```"

    provider = GeminiSentimentProvider(MagicMock(spec=Session))
    provider._llm = MagicMock()
    provider._llm.ainvoke = AsyncMock(return_value=mock_llm_response)

    results = await provider.analyse("Test", "Test")

    assert len(results) == 1
    assert results[0].coin == "BTC"


@pytest.mark.asyncio
async def test_gemini_provider_handles_malformed_json() -> None:
    """Test that provider handles malformed JSON gracefully."""
    mock_llm_response = MagicMock()
    mock_llm_response.content = "This is not JSON at all"

    provider = GeminiSentimentProvider(MagicMock(spec=Session))
    provider._llm = MagicMock()
    provider._llm.ainvoke = AsyncMock(return_value=mock_llm_response)

    results = await provider.analyse("Test", "Test")

    # Should return empty list instead of crashing
    assert len(results) == 0


@pytest.mark.asyncio
async def test_gemini_provider_normalizes_sentiment() -> None:
    """Test that provider normalizes sentiment direction to lowercase."""
    mock_llm_response = MagicMock()
    mock_llm_response.content = json.dumps(
        {
            "coins": [
                {"symbol": "BTC", "sentiment": "BULLISH", "confidence": 0.9, "rationale": "Test"}
            ],
            "overall_sentiment": "bullish",
            "event_type": "technical",
        }
    )

    provider = GeminiSentimentProvider(MagicMock(spec=Session))
    provider._llm = MagicMock()
    provider._llm.ainvoke = AsyncMock(return_value=mock_llm_response)

    results = await provider.analyse("Test", "Test")

    assert results[0].direction == "bullish"  # Should be lowercase


@pytest.mark.asyncio
async def test_gemini_provider_skips_malformed_coins() -> None:
    """Test that provider skips malformed coin entries."""
    mock_llm_response = MagicMock()
    mock_llm_response.content = json.dumps(
        {
            "coins": [
                {"symbol": "BTC", "sentiment": "bullish", "confidence": 0.9, "rationale": "Good"},
                {"symbol": "ETH"},  # Missing fields
                {"symbol": "XRP", "sentiment": "bearish", "confidence": 0.8, "rationale": "Bad"},
            ],
            "overall_sentiment": "mixed",
            "event_type": "technical",
        }
    )

    provider = GeminiSentimentProvider(MagicMock(spec=Session))
    # Provider should use the loaded LLM
    provider._llm = MagicMock()
    provider._llm.ainvoke = AsyncMock(return_value=mock_llm_response)

    results = await provider.analyse("Test", "Test")

    # Should have BTC and XRP but not ETH (missing required fields)
    coins = {r.coin for r in results}
    assert coins == {"BTC", "XRP"}
    assert len(results) == 2
