"""
Tests for the encryption service

Tests encryption, decryption, and API key masking functionality.
"""
import pytest
from cryptography.fernet import Fernet

from app.services.encryption import EncryptionService


class TestEncryptionService:
    """Tests for EncryptionService class"""

    @pytest.fixture
    def encryption_service(self):
        """Create a test encryption service with a known key"""
        test_key = Fernet.generate_key()
        return EncryptionService(key=test_key.decode())

    def test_encrypt_decrypt_roundtrip(self, encryption_service):
        """Test that encryption and decryption work correctly"""
        plaintext = "test_api_key_12345"
        
        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)
        
        assert decrypted == plaintext
        assert isinstance(encrypted, bytes)

    def test_encrypt_empty_string_raises_error(self, encryption_service):
        """Test that encrypting empty string raises ValueError"""
        with pytest.raises(ValueError, match="Cannot encrypt empty string"):
            encryption_service.encrypt("")

    def test_decrypt_empty_bytes_raises_error(self, encryption_service):
        """Test that decrypting empty bytes raises ValueError"""
        with pytest.raises(ValueError, match="Cannot decrypt empty bytes"):
            encryption_service.decrypt(b"")

    def test_encrypt_produces_different_output_each_time(self, encryption_service):
        """Test that encrypting the same plaintext produces different ciphertext"""
        plaintext = "test_value"
        
        encrypted1 = encryption_service.encrypt(plaintext)
        encrypted2 = encryption_service.encrypt(plaintext)
        
        # Ciphertext should be different due to IV/nonce
        assert encrypted1 != encrypted2
        
        # But both should decrypt to the same plaintext
        assert encryption_service.decrypt(encrypted1) == plaintext
        assert encryption_service.decrypt(encrypted2) == plaintext

    def test_decrypt_with_wrong_key_raises_error(self):
        """Test that decrypting with wrong key raises error"""
        service1 = EncryptionService(key=Fernet.generate_key().decode())
        service2 = EncryptionService(key=Fernet.generate_key().decode())
        
        plaintext = "secret_data"
        encrypted = service1.encrypt(plaintext)
        
        # Attempting to decrypt with different key should raise error
        with pytest.raises(Exception):
            service2.decrypt(encrypted)

    def test_mask_api_key_shows_last_4_chars(self, encryption_service):
        """Test that API key masking shows only last 4 characters"""
        api_key = "abcdefghij1234"
        masked = encryption_service.mask_api_key(api_key)
        
        assert masked == "**********1234"
        assert len(masked) == len(api_key)

    def test_mask_api_key_short_key(self, encryption_service):
        """Test masking of short API keys"""
        api_key = "abc"
        masked = encryption_service.mask_api_key(api_key)
        
        assert masked == "***"
        assert len(masked) == len(api_key)

    def test_mask_api_key_4_chars(self, encryption_service):
        """Test masking of exactly 4 character key"""
        api_key = "abcd"
        masked = encryption_service.mask_api_key(api_key)
        
        assert masked == "abcd"

    def test_mask_api_key_empty_string(self, encryption_service):
        """Test masking of empty API key"""
        masked = encryption_service.mask_api_key("")
        assert masked == "****"

    def test_encrypt_unicode_characters(self, encryption_service):
        """Test encryption of unicode characters"""
        plaintext = "test_€_£_¥_😀"
        
        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)
        
        assert decrypted == plaintext

    def test_encrypt_long_string(self, encryption_service):
        """Test encryption of long strings"""
        plaintext = "x" * 10000
        
        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)
        
        assert decrypted == plaintext
        assert len(decrypted) == 10000
