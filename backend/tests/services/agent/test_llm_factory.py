"""
Tests for LLM Factory (BYOM Feature - Sprint 2.8)

Tests the factory pattern for creating LLM instances from user credentials
or system defaults.
"""
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.models import User, UserLLMCredentials
from app.services.agent.llm_factory import LLMFactory, create_llm
from app.services.encryption import encryption_service


@pytest.fixture
def mock_user():
    """Create a mock user"""
    return User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User"
    )


@pytest.fixture
def mock_openai_credential(mock_user):
    """Create a mock OpenAI credential"""
    api_key = "sk-proj-test123456789"
    encrypted_key = encryption_service.encrypt_api_key(api_key)

    return UserLLMCredentials(
        id=uuid4(),
        user_id=mock_user.id,
        provider="openai",
        model_name="gpt-4",
        encrypted_api_key=encrypted_key,
        encryption_key_id="default",
        is_default=True,
        is_active=True
    )


@pytest.fixture
def mock_google_credential(mock_user):
    """Create a mock Google Gemini credential"""
    api_key = "AIzaSyTest123456789"
    encrypted_key = encryption_service.encrypt_api_key(api_key)

    return UserLLMCredentials(
        id=uuid4(),
        user_id=mock_user.id,
        provider="google",
        model_name="gemini-1.5-pro",
        encrypted_api_key=encrypted_key,
        encryption_key_id="default",
        is_default=False,
        is_active=True
    )


@pytest.fixture
def mock_anthropic_credential(mock_user):
    """Create a mock Anthropic Claude credential"""
    api_key = "sk-ant-test123456789"
    encrypted_key = encryption_service.encrypt_api_key(api_key)

    return UserLLMCredentials(
        id=uuid4(),
        user_id=mock_user.id,
        provider="anthropic",
        model_name="claude-3-sonnet-20240229",
        encrypted_api_key=encrypted_key,
        encryption_key_id="default",
        is_default=False,
        is_active=True
    )


class TestLLMFactoryBasicCreation:
    """Test basic LLM creation from API keys"""

    def test_create_openai_from_api_key(self):
        """Test creating OpenAI LLM directly from API key"""
        api_key = "sk-test-key"

        llm = LLMFactory.create_llm_from_api_key(
            provider="openai",
            api_key=api_key,
            model_name="gpt-4"
        )

        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "gpt-4"

    def test_create_google_from_api_key(self):
        """Test creating Google Gemini LLM directly from API key"""
        api_key = "AIzaSy-test-key"

        llm = LLMFactory.create_llm_from_api_key(
            provider="google",
            api_key=api_key,
            model_name="gemini-1.5-pro"
        )

        assert isinstance(llm, ChatGoogleGenerativeAI)
        assert llm.model.endswith("gemini-1.5-pro")  # Google prepends "models/" prefix
        # Verify Gemini-specific settings
        assert llm.convert_system_message_to_human is True

    def test_create_anthropic_from_api_key(self):
        """Test creating Anthropic Claude LLM directly from API key (Sprint 2.9)"""
        api_key = "sk-ant-test-key"

        llm = LLMFactory.create_llm_from_api_key(
            provider="anthropic",
            api_key=api_key,
            model_name="claude-3-sonnet-20240229"
        )

        assert isinstance(llm, ChatAnthropic)
        assert llm.model == "claude-3-sonnet-20240229"

    def test_create_unsupported_provider_raises_error(self):
        """Test that unsupported provider raises ValueError"""
        with pytest.raises(ValueError, match="Unsupported provider"):
            LLMFactory.create_llm_from_api_key(
                provider="unsupported",
                api_key="test-key"
            )

    def test_create_openai_with_default_model(self):
        """Test creating OpenAI LLM without specifying model (uses default)"""
        api_key = "sk-test-key"

        llm = LLMFactory.create_llm_from_api_key(
            provider="openai",
            api_key=api_key
        )

        assert isinstance(llm, ChatOpenAI)
        # Should use settings default
        assert llm.model_name is not None

    def test_create_google_with_default_model(self):
        """Test creating Google LLM without specifying model (uses default)"""
        api_key = "AIzaSy-test-key"

        llm = LLMFactory.create_llm_from_api_key(
            provider="google",
            api_key=api_key
        )

        assert isinstance(llm, ChatGoogleGenerativeAI)
        assert llm.model.endswith("gemini-1.5-pro")  # Default model (Google prepends "models/" prefix)

    def test_create_anthropic_with_default_model(self):
        """Test creating Anthropic LLM without specifying model (uses default)"""
        api_key = "sk-ant-test-key"

        llm = LLMFactory.create_llm_from_api_key(
            provider="anthropic",
            api_key=api_key
        )

        assert isinstance(llm, ChatAnthropic)
        assert llm.model == "claude-3-sonnet-20240229"  # Default model


class TestLLMFactoryUserCredentials:
    """Test LLM creation from user credentials"""

    def test_create_from_specific_credential(self, mock_user, mock_openai_credential):
        """Test creating LLM from specific credential ID"""
        mock_session = MagicMock()
        mock_session.get.return_value = mock_openai_credential

        llm = LLMFactory.create_llm(
            session=mock_session,
            user_id=mock_user.id,
            credential_id=mock_openai_credential.id
        )

        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "gpt-4"
        mock_session.get.assert_called_once_with(UserLLMCredentials, mock_openai_credential.id)

    def test_create_from_default_credential(self, mock_user, mock_openai_credential):
        """Test creating LLM from user's default credential"""
        mock_session = MagicMock()
        mock_exec_result = MagicMock()
        mock_exec_result.first.return_value = mock_openai_credential
        mock_session.exec.return_value = mock_exec_result

        llm = LLMFactory.create_llm(
            session=mock_session,
            user_id=mock_user.id
        )

        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "gpt-4"

    def test_create_with_google_credential(self, mock_user, mock_google_credential):
        """Test creating Google LLM from credential"""
        mock_session = MagicMock()
        mock_session.get.return_value = mock_google_credential

        llm = LLMFactory.create_llm(
            session=mock_session,
            user_id=mock_user.id,
            credential_id=mock_google_credential.id
        )

        assert isinstance(llm, ChatGoogleGenerativeAI)
        assert llm.model.endswith("gemini-1.5-pro")  # Google prepends "models/" prefix

    def test_create_with_anthropic_credential(self, mock_user, mock_anthropic_credential):
        """Test creating Anthropic LLM from credential (Sprint 2.9)"""
        mock_session = MagicMock()
        mock_session.get.return_value = mock_anthropic_credential

        llm = LLMFactory.create_llm(
            session=mock_session,
            user_id=mock_user.id,
            credential_id=mock_anthropic_credential.id
        )

        assert isinstance(llm, ChatAnthropic)
        assert llm.model == "claude-3-sonnet-20240229"

    def test_create_credential_not_found_raises_error(self, mock_user):
        """Test that missing credential raises ValueError"""
        mock_session = MagicMock()
        mock_session.get.return_value = None

        fake_credential_id = uuid4()
        with pytest.raises(ValueError, match="not found"):
            LLMFactory.create_llm(
                session=mock_session,
                user_id=mock_user.id,
                credential_id=fake_credential_id
            )

    def test_create_credential_wrong_user_raises_error(self, mock_user, mock_openai_credential):
        """Test that credential from different user raises ValueError"""
        mock_session = MagicMock()
        mock_session.get.return_value = mock_openai_credential

        different_user_id = uuid4()
        with pytest.raises(ValueError, match="does not belong to user"):
            LLMFactory.create_llm(
                session=mock_session,
                user_id=different_user_id,
                credential_id=mock_openai_credential.id
            )

    def test_create_inactive_credential_raises_error(self, mock_user, mock_openai_credential):
        """Test that inactive credential raises ValueError"""
        mock_openai_credential.is_active = False
        mock_session = MagicMock()
        mock_session.get.return_value = mock_openai_credential

        with pytest.raises(ValueError, match="not active"):
            LLMFactory.create_llm(
                session=mock_session,
                user_id=mock_user.id,
                credential_id=mock_openai_credential.id
            )


class TestLLMFactorySystemDefault:
    """Test system default LLM creation"""

    @patch('app.services.agent.llm_factory.settings')
    def test_create_system_default_openai(self, mock_settings):
        """Test creating system default OpenAI LLM"""
        mock_settings.LLM_PROVIDER = "openai"
        mock_settings.OPENAI_API_KEY = "sk-system-key"
        mock_settings.OPENAI_MODEL = "gpt-4-turbo-preview"
        mock_settings.MAX_TOKENS_PER_REQUEST = 4000
        mock_settings.ENABLE_STREAMING = True

        llm = LLMFactory._create_system_default_llm()

        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "gpt-4-turbo-preview"

    @patch('app.services.agent.llm_factory.settings')
    def test_create_with_prefer_default_true(self, mock_settings, mock_user):
        """Test that prefer_default=True uses system default"""
        mock_settings.LLM_PROVIDER = "openai"
        mock_settings.OPENAI_API_KEY = "sk-system-key"
        mock_settings.OPENAI_MODEL = "gpt-4"
        mock_settings.MAX_TOKENS_PER_REQUEST = 4000
        mock_settings.ENABLE_STREAMING = True

        mock_session = MagicMock()

        llm = LLMFactory.create_llm(
            session=mock_session,
            user_id=mock_user.id,
            prefer_default=True
        )

        assert isinstance(llm, ChatOpenAI)
        # Should not query database when prefer_default=True
        mock_session.get.assert_not_called()
        mock_session.exec.assert_not_called()

    @patch('app.services.agent.llm_factory.settings')
    def test_create_no_user_credentials_uses_default(self, mock_settings, mock_user):
        """Test that missing user credentials falls back to system default"""
        mock_settings.LLM_PROVIDER = "openai"
        mock_settings.OPENAI_API_KEY = "sk-system-key"
        mock_settings.OPENAI_MODEL = "gpt-4"
        mock_settings.MAX_TOKENS_PER_REQUEST = 4000
        mock_settings.ENABLE_STREAMING = True

        mock_session = MagicMock()
        mock_exec_result = MagicMock()
        mock_exec_result.first.return_value = None  # No user credentials
        mock_session.exec.return_value = mock_exec_result

        llm = LLMFactory.create_llm(
            session=mock_session,
            user_id=mock_user.id
        )

        assert isinstance(llm, ChatOpenAI)

    @patch('app.services.agent.llm_factory.settings')
    def test_system_default_missing_api_key_raises_error(self, mock_settings, mock_user):
        """Test that missing system API key raises ValueError"""
        mock_settings.LLM_PROVIDER = "openai"
        mock_settings.OPENAI_API_KEY = None

        with pytest.raises(ValueError, match="not configured"):
            LLMFactory._create_system_default_llm()


class TestLLMFactoryHelpers:
    """Test helper methods"""

    def test_get_supported_providers(self):
        """Test getting list of supported providers"""
        providers = LLMFactory.get_supported_providers()

        assert isinstance(providers, list)
        assert "openai" in providers
        assert "google" in providers
        assert "anthropic" in providers

    def test_get_provider_default_models(self):
        """Test getting default models for providers"""
        defaults = LLMFactory.get_provider_default_models()

        assert isinstance(defaults, dict)
        assert "openai" in defaults
        assert "google" in defaults
        assert "anthropic" in defaults
        assert defaults["openai"] == "gpt-4-turbo-preview"
        assert defaults["google"] == "gemini-1.5-pro"
        assert defaults["anthropic"] == "claude-3-sonnet-20240229"

    def test_convenience_function_create_llm(self, mock_user, mock_openai_credential):
        """Test convenience function works same as LLMFactory.create_llm"""
        mock_session = MagicMock()
        mock_session.get.return_value = mock_openai_credential

        llm = create_llm(
            session=mock_session,
            user_id=mock_user.id,
            credential_id=mock_openai_credential.id
        )

        assert isinstance(llm, ChatOpenAI)


class TestLLMFactoryProviderSpecific:
    """Test provider-specific configurations"""

    def test_openai_custom_parameters(self):
        """Test OpenAI LLM with custom parameters"""
        api_key = "sk-test-key"

        llm = LLMFactory.create_llm_from_api_key(
            provider="openai",
            api_key=api_key,
            model_name="gpt-3.5-turbo",
            max_tokens=2000,
            streaming=False,
            temperature=0.7
        )

        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "gpt-3.5-turbo"
        assert llm.max_tokens == 2000
        assert llm.streaming is False
        assert llm.temperature == 0.7

    def test_google_gemini_system_message_conversion(self):
        """Test that Google Gemini has system message conversion enabled"""
        api_key = "AIzaSy-test-key"

        llm = LLMFactory.create_llm_from_api_key(
            provider="google",
            api_key=api_key,
            model_name="gemini-pro"
        )

        assert isinstance(llm, ChatGoogleGenerativeAI)
        # Verify Gemini-specific workaround is applied
        assert llm.convert_system_message_to_human is True

    def test_anthropic_custom_parameters(self):
        """Test Anthropic LLM with custom parameters (Sprint 2.9)"""
        api_key = "sk-ant-test-key"

        llm = LLMFactory.create_llm_from_api_key(
            provider="anthropic",
            api_key=api_key,
            model_name="claude-3-opus-20240229",
            max_tokens=3000,
            temperature=0.5
        )

        assert isinstance(llm, ChatAnthropic)
        assert llm.model == "claude-3-opus-20240229"
        assert llm.max_tokens == 3000
        assert llm.temperature == 0.5

    def test_provider_case_insensitive(self):
        """Test that provider names are case-insensitive"""
        api_key = "sk-test-key"

        llm1 = LLMFactory.create_llm_from_api_key(provider="OpenAI", api_key=api_key)
        llm2 = LLMFactory.create_llm_from_api_key(provider="OPENAI", api_key=api_key)
        llm3 = LLMFactory.create_llm_from_api_key(provider="openai", api_key=api_key)

        assert isinstance(llm1, ChatOpenAI)
        assert isinstance(llm2, ChatOpenAI)
        assert isinstance(llm3, ChatOpenAI)
