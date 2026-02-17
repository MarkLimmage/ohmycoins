"""
API collector base class for HTTP API-based data sources.

This module provides a base class for collectors that fetch data from HTTP APIs,
with built-in retry logic, rate limiting, and error handling.
"""

import asyncio
import logging
from typing import Any, cast

import aiohttp
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .base import BaseCollector

logger = logging.getLogger(__name__)


class APICollector(BaseCollector):
    """
    Base class for API-based collectors with retry logic and rate limiting.

    Provides:
    - Async HTTP client with proper connection management
    - Exponential backoff retry logic
    - Rate limiting support
    - Request timeout handling
    - Common HTTP error handling
    """

    def __init__(
        self,
        name: str,
        ledger: str,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_delay: float = 0.0,
    ):
        """
        Initialize the API collector.

        Args:
            name: Unique name for this collector
            ledger: The ledger this collector belongs to
            base_url: Base URL for the API (e.g., "https://api.example.com")
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retry attempts (default: 3)
            rate_limit_delay: Minimum delay between requests in seconds (default: 0)
        """
        super().__init__(name, ledger)
        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time: float | None = None

    async def _enforce_rate_limit(self) -> None:
        """
        Enforce rate limiting by waiting if necessary.

        Ensures minimum delay between requests based on rate_limit_delay.
        """
        if self.rate_limit_delay > 0 and self._last_request_time:
            elapsed = asyncio.get_event_loop().time() - self._last_request_time
            if elapsed < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - elapsed)

        self._last_request_time = asyncio.get_event_loop().time()

    async def fetch_json(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """
        Fetch JSON data from an API endpoint with retry logic.

        Args:
            endpoint: API endpoint path (e.g., "/v1/protocols")
            params: Query parameters to include in the request
            headers: Additional HTTP headers

        Returns:
            Parsed JSON response (dict or list)

        Raises:
            aiohttp.ClientError: If the request fails after all retries
            ValueError: If the response is not valid JSON
        """
        url = f"{self.base_url}{endpoint}" if endpoint.startswith("/") else f"{self.base_url}/{endpoint}"

        await self._enforce_rate_limit()

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type(
                (aiohttp.ClientError, asyncio.TimeoutError)
            ),
            reraise=True,
        ):
            with attempt:
                logger.debug(
                    f"{self.name}: Fetching {url} "
                    f"(attempt {attempt.retry_state.attempt_number}/{self.max_retries})"
                )

                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.get(
                        url, params=params, headers=headers
                    ) as response:
                        response.raise_for_status()
                        data = await response.json()

                        logger.debug(
                            f"{self.name}: Successfully fetched data from {url}"
                        )

                        return cast(dict[str, Any] | list[Any], data)

        # This should never be reached due to reraise=True, but satisfy type checker
        raise RuntimeError("Retry logic failed unexpectedly")

    async def fetch_text(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        """
        Fetch text data from an API endpoint with retry logic.

        Args:
            endpoint: API endpoint path
            params: Query parameters to include in the request
            headers: Additional HTTP headers

        Returns:
            Response text content

        Raises:
            aiohttp.ClientError: If the request fails after all retries
        """
        url = f"{self.base_url}{endpoint}" if endpoint.startswith("/") else f"{self.base_url}/{endpoint}"

        await self._enforce_rate_limit()

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type(
                (aiohttp.ClientError, asyncio.TimeoutError)
            ),
            reraise=True,
        ):
            with attempt:
                logger.debug(
                    f"{self.name}: Fetching {url} "
                    f"(attempt {attempt.retry_state.attempt_number}/{self.max_retries})"
                )

                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.get(
                        url, params=params, headers=headers
                    ) as response:
                        response.raise_for_status()
                        text = await response.text()

                        logger.debug(
                            f"{self.name}: Successfully fetched text from {url}"
                        )

                        return text

        raise RuntimeError("Retry logic failed unexpectedly")
