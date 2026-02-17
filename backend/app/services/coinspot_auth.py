"""
Coinspot API Authentication Utilities

This module provides utilities for authenticating with the Coinspot private API
using HMAC-SHA512 signatures.
"""
import hashlib
import hmac
import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class CoinspotAuthenticator:
    """Handles Coinspot API authentication using HMAC-SHA512"""

    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize authenticator with API credentials

        Args:
            api_key: Coinspot API key
            api_secret: Coinspot API secret
        """
        self.api_key = api_key
        self.api_secret = api_secret

    def generate_nonce(self) -> int:
        """
        Generate a nonce (number used once) for API requests

        Returns:
            Current timestamp in milliseconds
        """
        return int(time.time() * 1000)

    def sign_request(self, payload: dict[str, Any]) -> str:
        """
        Generate HMAC-SHA512 signature for a request payload

        Args:
            payload: Request payload dictionary (must include nonce)

        Returns:
            Hex-encoded signature string
        """
        # Convert payload to JSON string
        message = json.dumps(payload, separators=(',', ':')).encode('utf-8')

        # Generate HMAC-SHA512 signature
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message,
            hashlib.sha512
        ).hexdigest()

        return signature

    def get_headers(self, payload: dict[str, Any]) -> dict[str, str]:
        """
        Generate complete headers for Coinspot API request

        Args:
            payload: Request payload dictionary

        Returns:
            Dictionary of headers including signature and API key
        """
        # Ensure payload has a nonce
        if 'nonce' not in payload:
            payload['nonce'] = self.generate_nonce()

        signature = self.sign_request(payload)

        return {
            'sign': signature,
            'key': self.api_key,
            'Content-Type': 'application/json'
        }

    def prepare_request(self, endpoint_data: dict[str, Any] | None = None) -> tuple[dict[str, str], dict[str, Any]]:
        """
        Prepare headers and payload for a Coinspot API request

        Args:
            endpoint_data: Additional data for the endpoint (e.g., cointype, amount)

        Returns:
            Tuple of (headers, payload)
        """
        payload = {'nonce': self.generate_nonce()}

        if endpoint_data:
            payload.update(endpoint_data)

        headers = self.get_headers(payload)

        return headers, payload


def verify_coinspot_signature(payload: dict[str, Any], signature: str, api_secret: str) -> bool:
    """
    Verify a Coinspot API signature

    Args:
        payload: Request payload
        signature: Signature to verify
        api_secret: API secret to verify against

    Returns:
        True if signature is valid, False otherwise
    """
    message = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    expected_signature = hmac.new(
        api_secret.encode('utf-8'),
        message,
        hashlib.sha512
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)
