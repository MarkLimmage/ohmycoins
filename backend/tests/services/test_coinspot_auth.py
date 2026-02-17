"""
Tests for Coinspot authentication utilities

Tests HMAC-SHA512 signature generation and request preparation.
"""
import hashlib
import hmac
import json
import time

import pytest

from app.services.coinspot_auth import CoinspotAuthenticator, verify_coinspot_signature


class TestCoinspotAuthenticator:
    """Tests for CoinspotAuthenticator class"""

    @pytest.fixture
    def authenticator(self):
        """Create a test authenticator with known credentials"""
        return CoinspotAuthenticator(
            api_key="test_api_key",
            api_secret="test_api_secret"
        )

    def test_generate_nonce(self, authenticator):
        """Test that nonce generation produces valid timestamps"""
        nonce1 = authenticator.generate_nonce()
        time.sleep(0.01)  # Small delay
        nonce2 = authenticator.generate_nonce()

        # Nonces should be integers
        assert isinstance(nonce1, int)
        assert isinstance(nonce2, int)

        # Second nonce should be greater than first
        assert nonce2 > nonce1

        # Nonce should be reasonable timestamp in milliseconds
        current_time_ms = int(time.time() * 1000)
        assert abs(nonce2 - current_time_ms) < 1000  # Within 1 second

    def test_sign_request(self, authenticator):
        """Test request signing produces correct signature"""
        payload = {
            "nonce": 1234567890000,
            "cointype": "BTC"
        }

        signature = authenticator.sign_request(payload)

        # Signature should be hex string
        assert isinstance(signature, str)
        assert len(signature) == 128  # SHA512 produces 64 bytes = 128 hex chars

        # Verify signature is correct
        message = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        expected_signature = hmac.new(
            b"test_api_secret",
            message,
            hashlib.sha512
        ).hexdigest()

        assert signature == expected_signature

    def test_sign_request_deterministic(self, authenticator):
        """Test that same payload produces same signature"""
        payload = {"nonce": 1234567890000}

        signature1 = authenticator.sign_request(payload)
        signature2 = authenticator.sign_request(payload)

        assert signature1 == signature2

    def test_sign_request_different_payloads(self, authenticator):
        """Test that different payloads produce different signatures"""
        payload1 = {"nonce": 1234567890000}
        payload2 = {"nonce": 1234567890001}

        signature1 = authenticator.sign_request(payload1)
        signature2 = authenticator.sign_request(payload2)

        assert signature1 != signature2

    def test_get_headers(self, authenticator):
        """Test header generation"""
        payload = {"nonce": 1234567890000}

        headers = authenticator.get_headers(payload)

        assert "sign" in headers
        assert "key" in headers
        assert "Content-Type" in headers

        assert headers["key"] == "test_api_key"
        assert headers["Content-Type"] == "application/json"
        assert len(headers["sign"]) == 128

    def test_get_headers_adds_nonce_if_missing(self, authenticator):
        """Test that get_headers adds nonce if not present"""
        payload = {}

        headers = authenticator.get_headers(payload)

        # Payload should now have nonce
        assert "nonce" in payload
        assert isinstance(payload["nonce"], int)

        # Headers should be generated
        assert "sign" in headers
        assert "key" in headers

    def test_prepare_request_without_endpoint_data(self, authenticator):
        """Test request preparation without additional data"""
        headers, payload = authenticator.prepare_request()

        # Should have nonce
        assert "nonce" in payload
        assert isinstance(payload["nonce"], int)

        # Should have proper headers
        assert headers["key"] == "test_api_key"
        assert "sign" in headers
        assert len(headers["sign"]) == 128

    def test_prepare_request_with_endpoint_data(self, authenticator):
        """Test request preparation with additional endpoint data"""
        endpoint_data = {"cointype": "BTC", "amount": 100}

        headers, payload = authenticator.prepare_request(endpoint_data)

        # Should have nonce
        assert "nonce" in payload

        # Should have endpoint data
        assert payload["cointype"] == "BTC"
        assert payload["amount"] == 100

        # Should have proper headers
        assert headers["key"] == "test_api_key"
        assert "sign" in headers

    def test_different_secrets_produce_different_signatures(self):
        """Test that different API secrets produce different signatures"""
        auth1 = CoinspotAuthenticator("key", "secret1")
        auth2 = CoinspotAuthenticator("key", "secret2")

        payload = {"nonce": 1234567890000}

        sig1 = auth1.sign_request(payload)
        sig2 = auth2.sign_request(payload)

        assert sig1 != sig2


class TestVerifyCoinspotSignature:
    """Tests for verify_coinspot_signature function"""

    def test_verify_valid_signature(self):
        """Test verification of valid signature"""
        api_secret = "test_secret"
        payload = {"nonce": 1234567890000, "data": "test"}

        # Generate valid signature
        message = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        signature = hmac.new(
            api_secret.encode('utf-8'),
            message,
            hashlib.sha512
        ).hexdigest()

        # Verify it
        assert verify_coinspot_signature(payload, signature, api_secret) is True

    def test_verify_invalid_signature(self):
        """Test verification of invalid signature"""
        api_secret = "test_secret"
        payload = {"nonce": 1234567890000}
        invalid_signature = "0" * 128

        assert verify_coinspot_signature(payload, invalid_signature, api_secret) is False

    def test_verify_signature_wrong_secret(self):
        """Test verification fails with wrong secret"""
        payload = {"nonce": 1234567890000}

        # Generate signature with one secret
        message = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        signature = hmac.new(
            b"secret1",
            message,
            hashlib.sha512
        ).hexdigest()

        # Try to verify with different secret
        assert verify_coinspot_signature(payload, signature, "secret2") is False

    def test_verify_signature_modified_payload(self):
        """Test verification fails when payload is modified"""
        api_secret = "test_secret"
        payload = {"nonce": 1234567890000}

        # Generate signature
        message = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        signature = hmac.new(
            api_secret.encode('utf-8'),
            message,
            hashlib.sha512
        ).hexdigest()

        # Modify payload
        payload["nonce"] = 9999999999999

        # Verification should fail
        assert verify_coinspot_signature(payload, signature, api_secret) is False
