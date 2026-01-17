"""
Encryption Service for Coinspot API Credentials

This module provides utilities for encrypting and decrypting sensitive credentials
using Fernet (AES-256) symmetric encryption.
"""
import os
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)

# Get encryption key from environment variable
# In production, this should be stored in AWS Secrets Manager or similar
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    logger.warning("ENCRYPTION_KEY not set in environment. Generating a new key for development.")
    # Generate a key for development (DO NOT use in production)
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    logger.info(f"Generated encryption key: {ENCRYPTION_KEY}")
    logger.warning("Store this key securely if you want to decrypt data later!")


class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self, key: str | None = None):
        """
        Initialize the encryption service
        
        Args:
            key: Base64-encoded encryption key. If None, uses ENCRYPTION_KEY from environment.
        """
        self.key = key or ENCRYPTION_KEY
        if isinstance(self.key, str):
            self.key = self.key.encode()
        self.fernet = Fernet(self.key)
    
    def encrypt(self, plaintext: str) -> bytes:
        """
        Encrypt a plaintext string
        
        Args:
            plaintext: The string to encrypt
            
        Returns:
            Encrypted bytes
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty string")
        
        plaintext_bytes = plaintext.encode('utf-8')
        encrypted = self.fernet.encrypt(plaintext_bytes)
        return encrypted
    
    def decrypt(self, encrypted: bytes) -> str:
        """
        Decrypt encrypted bytes to string
        
        Args:
            encrypted: The encrypted bytes
            
        Returns:
            Decrypted plaintext string
        """
        if not encrypted:
            raise ValueError("Cannot decrypt empty bytes")
        
        decrypted_bytes = self.fernet.decrypt(encrypted)
        return decrypted_bytes.decode('utf-8')
    
    def mask_api_key(self, api_key: str) -> str:
        """
        Mask an API key for display, showing only last 4 characters
        
        Args:
            api_key: The API key to mask
            
        Returns:
            Masked API key (e.g., "****abcd")
        """
        if not api_key:
            return "****"
        
        if len(api_key) < 4:
            return "*" * len(api_key)
        
        visible_chars = 4
        masked_length = len(api_key) - visible_chars
        return "*" * masked_length + api_key[-visible_chars:]
    
    # ============================================================================
    # BYOM (Bring Your Own Model) - LLM API Key Methods (Sprint 2.8)
    # ============================================================================
    
    def encrypt_api_key(self, api_key: str) -> bytes:
        """
        Encrypt an LLM API key for secure storage (BYOM feature)
        
        This is a convenience wrapper around encrypt() to make it explicit
        that LLM API keys use the same encryption as Coinspot credentials.
        
        Args:
            api_key: The LLM API key to encrypt (OpenAI, Google, Anthropic)
            
        Returns:
            Encrypted bytes suitable for database storage
            
        Raises:
            ValueError: If api_key is empty
        """
        return self.encrypt(api_key)
    
    def decrypt_api_key(self, encrypted_api_key: bytes) -> str:
        """
        Decrypt an LLM API key from storage (BYOM feature)
        
        This is a convenience wrapper around decrypt() to make it explicit
        that LLM API keys use the same encryption as Coinspot credentials.
        
        Args:
            encrypted_api_key: The encrypted API key bytes from database
            
        Returns:
            Decrypted API key string
            
        Raises:
            ValueError: If encrypted_api_key is empty
            cryptography.fernet.InvalidToken: If decryption fails
        """
        return self.decrypt(encrypted_api_key)


# Singleton instance
encryption_service = EncryptionService()
