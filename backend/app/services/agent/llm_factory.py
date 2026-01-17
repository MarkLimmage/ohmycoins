"""
LLM Factory for BYOM (Bring Your Own Model) Feature

This module provides a factory pattern for dynamically creating LLM instances
based on user credentials or system defaults. Supports multiple providers:
- OpenAI (gpt-4, gpt-3.5-turbo, etc.)
- Google Gemini (gemini-1.5-pro, gemini-pro)
- Anthropic Claude (claude-3-opus, claude-3-sonnet, etc.)

The factory handles:
1. Retrieving user credentials from database
2. Decrypting API keys
3. Instantiating appropriate LangChain LLM wrapper
4. Falling back to system default if user has no credentials

Sprint 2.8: Phase 3 - Initial implementation with OpenAI and Google support
"""
import logging
from typing import Optional
from uuid import UUID

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlmodel import Session, select

from app.core.config import settings
from app.models import UserLLMCredentials
from app.services.encryption import encryption_service

logger = logging.getLogger(__name__)


class LLMFactory:
    """
    Factory for creating LLM instances based on user configuration or system defaults.
    
    This factory supports the BYOM (Bring Your Own Model) feature by allowing
    users to configure their own API keys for various LLM providers.
    
    Example usage:
        # System default LLM (from environment variables)
        llm = LLMFactory.create_llm(session=db_session, user_id=user.id)
        
        # User-specific LLM (uses their configured credentials)
        llm = LLMFactory.create_llm(
            session=db_session,
            user_id=user.id,
            credential_id=credential.id
        )
        
        # Specific provider override
        llm = LLMFactory.create_llm_from_api_key(
            provider="google",
            api_key="AIzaSy...",
            model_name="gemini-1.5-pro"
        )
    """
    
    @staticmethod
    def create_llm(
        session: Session,
        user_id: UUID,
        credential_id: Optional[UUID] = None,
        prefer_default: bool = False
    ):
        """
        Create an LLM instance based on user configuration or system default.
        
        Decision logic:
        1. If credential_id provided: Use that specific credential
        2. If prefer_default=True: Use system default (ignore user credentials)
        3. Otherwise: Use user's default credential if exists, else system default
        
        Args:
            session: Database session
            user_id: User ID to retrieve credentials for
            credential_id: Optional specific credential ID to use
            prefer_default: If True, always use system default regardless of user credentials
            
        Returns:
            LangChain LLM instance (ChatOpenAI, ChatGoogleGenerativeAI, etc.)
            
        Raises:
            ValueError: If credential_id provided but not found or not owned by user
        """
        # Option 1: System default requested explicitly
        if prefer_default:
            logger.info(f"Using system default LLM for user {user_id} (prefer_default=True)")
            return LLMFactory._create_system_default_llm()
        
        # Option 2: Specific credential ID provided
        if credential_id:
            credential = session.get(UserLLMCredentials, credential_id)
            if not credential:
                raise ValueError(f"Credential {credential_id} not found")
            if credential.user_id != user_id:
                raise ValueError(f"Credential {credential_id} does not belong to user {user_id}")
            if not credential.is_active:
                raise ValueError(f"Credential {credential_id} is not active")
            
            logger.info(
                f"Using specific credential {credential_id} "
                f"({credential.provider}/{credential.model_name}) for user {user_id}"
            )
            return LLMFactory._create_llm_from_credential(credential)
        
        # Option 3: Find user's default credential
        statement = select(UserLLMCredentials).where(
            UserLLMCredentials.user_id == user_id,
            UserLLMCredentials.is_default == True,
            UserLLMCredentials.is_active == True
        )
        default_credential = session.exec(statement).first()
        
        if default_credential:
            logger.info(
                f"Using default credential {default_credential.id} "
                f"({default_credential.provider}/{default_credential.model_name}) for user {user_id}"
            )
            return LLMFactory._create_llm_from_credential(default_credential)
        
        # Option 4: No user credentials, use system default
        logger.info(f"No user credentials found for user {user_id}, using system default")
        return LLMFactory._create_system_default_llm()
    
    @staticmethod
    def _create_llm_from_credential(credential: UserLLMCredentials):
        """
        Create an LLM instance from a UserLLMCredentials record.
        
        Args:
            credential: UserLLMCredentials database record
            
        Returns:
            LangChain LLM instance
        """
        # Decrypt the API key
        api_key = encryption_service.decrypt_api_key(credential.encrypted_api_key)
        
        # Determine model name (use credential's model or provider default)
        model_name = credential.model_name
        
        return LLMFactory.create_llm_from_api_key(
            provider=credential.provider,
            api_key=api_key,
            model_name=model_name
        )
    
    @staticmethod
    def create_llm_from_api_key(
        provider: str,
        api_key: str,
        model_name: Optional[str] = None,
        **kwargs
    ):
        """
        Create an LLM instance directly from provider and API key.
        
        This method is useful for:
        1. Testing API keys before saving them
        2. One-off LLM creation without database
        3. Integration tests
        
        Args:
            provider: LLM provider ("openai", "google", "anthropic")
            api_key: API key for the provider
            model_name: Optional model name (uses provider default if not specified)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LangChain LLM instance
            
        Raises:
            ValueError: If provider is not supported
        """
        provider = provider.lower()
        
        if provider == "openai":
            return LLMFactory._create_openai_llm(api_key, model_name, **kwargs)
        elif provider == "google":
            return LLMFactory._create_google_llm(api_key, model_name, **kwargs)
        elif provider == "anthropic":
            raise NotImplementedError(
                "Anthropic Claude support will be added in Sprint 2.9. "
                "Please use OpenAI or Google for now."
            )
        else:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Supported providers: openai, google, anthropic (coming in Sprint 2.9)"
            )
    
    @staticmethod
    def _create_system_default_llm():
        """
        Create system default LLM from environment configuration.
        
        Returns:
            LangChain LLM instance configured from settings
        """
        provider = settings.LLM_PROVIDER.lower()
        
        if provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not configured in environment")
            return LLMFactory._create_openai_llm(
                api_key=settings.OPENAI_API_KEY,
                model_name=settings.OPENAI_MODEL
            )
        elif provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not configured in environment")
            # Anthropic support coming in Sprint 2.9
            raise NotImplementedError("Anthropic system default will be added in Sprint 2.9")
        else:
            # Default to OpenAI if provider not recognized
            logger.warning(
                f"Unrecognized system LLM_PROVIDER '{provider}', falling back to OpenAI"
            )
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not configured for fallback")
            return LLMFactory._create_openai_llm(
                api_key=settings.OPENAI_API_KEY,
                model_name=settings.OPENAI_MODEL
            )
    
    @staticmethod
    def _create_openai_llm(
        api_key: str,
        model_name: Optional[str] = None,
        **kwargs
    ) -> ChatOpenAI:
        """
        Create OpenAI LLM instance.
        
        Args:
            api_key: OpenAI API key
            model_name: Model name (defaults to gpt-4-turbo-preview)
            **kwargs: Additional ChatOpenAI parameters
            
        Returns:
            ChatOpenAI instance
        """
        model = model_name or settings.OPENAI_MODEL
        max_tokens = kwargs.pop('max_tokens', settings.MAX_TOKENS_PER_REQUEST)
        streaming = kwargs.pop('streaming', settings.ENABLE_STREAMING)
        
        logger.debug(f"Creating OpenAI LLM with model={model}")
        
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            max_tokens=max_tokens,
            streaming=streaming,
            **kwargs
        )
    
    @staticmethod
    def _create_google_llm(
        api_key: str,
        model_name: Optional[str] = None,
        **kwargs
    ) -> ChatGoogleGenerativeAI:
        """
        Create Google Gemini LLM instance.
        
        Args:
            api_key: Google API key
            model_name: Model name (defaults to gemini-1.5-pro)
            **kwargs: Additional ChatGoogleGenerativeAI parameters
            
        Returns:
            ChatGoogleGenerativeAI instance
        """
        model = model_name or "gemini-1.5-pro"
        max_tokens = kwargs.pop('max_tokens', settings.MAX_TOKENS_PER_REQUEST)
        
        logger.debug(f"Creating Google Gemini LLM with model={model}")
        
        # Note: Google Gemini has different parameter names than OpenAI
        # - max_output_tokens instead of max_tokens
        # - convert_system_message_to_human=True (Gemini limitation)
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            max_output_tokens=max_tokens,
            convert_system_message_to_human=True,  # Required for Gemini
            **kwargs
        )
    
    @staticmethod
    def get_supported_providers() -> list[str]:
        """
        Get list of supported LLM providers.
        
        Returns:
            List of provider names
        """
        return ["openai", "google", "anthropic"]
    
    @staticmethod
    def get_provider_default_models() -> dict[str, str]:
        """
        Get default model names for each provider.
        
        Returns:
            Dict mapping provider name to default model
        """
        return {
            "openai": "gpt-4-turbo-preview",
            "google": "gemini-1.5-pro",
            "anthropic": "claude-3-sonnet-20240229"
        }


# Convenience function for quick LLM creation
def create_llm(
    session: Session,
    user_id: UUID,
    credential_id: Optional[UUID] = None,
    prefer_default: bool = False
):
    """
    Convenience function for creating LLM instances.
    
    This is a shorthand for LLMFactory.create_llm().
    
    Args:
        session: Database session
        user_id: User ID
        credential_id: Optional specific credential ID
        prefer_default: If True, use system default
        
    Returns:
        LangChain LLM instance
    """
    return LLMFactory.create_llm(
        session=session,
        user_id=user_id,
        credential_id=credential_id,
        prefer_default=prefer_default
    )
