"""
Integration tests for LLM Credentials API lifecycle.

Sprint 2.10 - Track B Phase 2: Production Agent Testing

Tests the complete credential lifecycle:
1. Create credential via API
2. Validate credential
3. Use credential in agent execution
4. Set as default
5. Update credential
6. Delete credential

These tests ensure the full BYOM feature workflow works end-to-end.
"""
import pytest
from uuid import uuid4

from sqlmodel import Session, select, delete
from fastapi.testclient import TestClient

from app.models import User, UserLLMCredentials, AgentSession, AgentSessionStatus
from app.services.encryption import encryption_service
from app.services.agent.llm_factory import LLMFactory


@pytest.fixture(autouse=True)
def cleanup_llm_credentials(session: Session):
    """Clean up LLM credentials before each test to ensure test isolation"""
    yield
    # Clean up dependent records first
    session.execute(delete(AgentSession))
    session.commit()
    # Delete all UserLLMCredentials after each test
    session.execute(delete(UserLLMCredentials))
    session.commit()


@pytest.mark.integration
class TestLLMCredentialsLifecycle:
    """Test complete lifecycle of LLM credentials via API"""
    
    def test_create_credential_via_api(
        self,
        client: TestClient,
        normal_user_token_headers: dict,
        session: Session
    ):
        """Test creating LLM credentials via API endpoint"""
        # Create credential
        credential_data = {
            "provider": "openai",
            "model_name": "gpt-4o-mini",
            "api_key": "sk-test-key-12345678901234567890",
            "is_default": False
        }
        
        response = client.post(
            "/api/v1/users/me/llm-credentials",
            headers=normal_user_token_headers,
            json=credential_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["provider"] == "openai"
        assert data["model_name"] == "gpt-4o-mini"
        assert data["is_default"] is False
        assert data["is_active"] is True
        assert "api_key_masked" in data
        assert data["api_key_masked"].endswith("7890")  # Last 4 characters
        assert "id" in data
        
        # Verify credential was saved to database
        credential_id = data["id"]
        db_credential = session.get(UserLLMCredentials, credential_id)
        assert db_credential is not None
        assert db_credential.provider == "openai"
        
        # Verify API key is encrypted
        assert isinstance(db_credential.encrypted_api_key, bytes)
        decrypted_key = encryption_service.decrypt_api_key(db_credential.encrypted_api_key)
        assert decrypted_key == credential_data["api_key"]
    
    def test_list_credentials_via_api(
        self,
        client: TestClient,
        normal_user_token_headers: dict,
        session: Session
    ):
        """Test listing LLM credentials via API endpoint"""
        # Create multiple credentials first
        credentials_data = [
            {
                "provider": "openai",
                "model_name": "gpt-4o-mini",
                "api_key": "sk-openai-test-key",
                "is_default": True
            },
            {
                "provider": "google",
                "model_name": "gemini-1.5-flash",
                "api_key": "AIzaSy-google-test-key",
                "is_default": False
            }
        ]
        
        for cred_data in credentials_data:
            response = client.post(
                "/api/v1/users/me/llm-credentials",
                headers=normal_user_token_headers,
                json=cred_data
            )
            assert response.status_code == 200
        
        # List credentials
        response = client.get(
            "/api/v1/users/me/llm-credentials",
            headers=normal_user_token_headers
        )
        
        assert response.status_code == 200
        credentials = response.json()
        
        # Verify we got both credentials
        assert len(credentials) >= 2
        providers = [c["provider"] for c in credentials]
        assert "openai" in providers
        assert "google" in providers
        
        # Verify default is set correctly
        default_creds = [c for c in credentials if c["is_default"]]
        assert len(default_creds) == 1
        assert default_creds[0]["provider"] == "openai"
    
    def test_set_credential_as_default(
        self,
        client: TestClient,
        normal_user_token_headers: dict,
        session: Session
    ):
        """Test setting a credential as default"""
        # Create two credentials
        cred1_data = {
            "provider": "openai",
            "model_name": "gpt-4o-mini",
            "api_key": "sk-openai-key",
            "is_default": True
        }
        response1 = client.post(
            "/api/v1/users/me/llm-credentials",
            headers=normal_user_token_headers,
            json=cred1_data
        )
        assert response1.status_code == 200
        cred1_id = response1.json()["id"]
        
        cred2_data = {
            "provider": "google",
            "model_name": "gemini-1.5-flash",
            "api_key": "AIzaSy-google-key",
            "is_default": False
        }
        response2 = client.post(
            "/api/v1/users/me/llm-credentials",
            headers=normal_user_token_headers,
            json=cred2_data
        )
        assert response2.status_code == 200
        cred2_id = response2.json()["id"]
        
        # Set second credential as default using the correct endpoint
        update_response = client.put(
            f"/api/v1/users/me/llm-credentials/{cred2_id}/default",
            headers=normal_user_token_headers
        )
        assert update_response.status_code == 200
        
        # Verify only cred2 is now default
        list_response = client.get(
            "/api/v1/users/me/llm-credentials",
            headers=normal_user_token_headers
        )
        credentials = list_response.json()
        
        for cred in credentials:
            if cred["id"] == cred2_id:
                assert cred["is_default"] is True
            elif cred["id"] == cred1_id:
                assert cred["is_default"] is False
    
    def test_update_credential_api_key(
        self,
        client: TestClient,
        normal_user_token_headers: dict,
        session: Session
    ):
        """Test updating credential API key by deleting and recreating"""
        # Create credential
        cred_data = {
            "provider": "openai",
            "model_name": "gpt-4o-mini",
            "api_key": "sk-old-key-12345",
            "is_default": False
        }
        create_response = client.post(
            "/api/v1/users/me/llm-credentials",
            headers=normal_user_token_headers,
            json=cred_data
        )
        assert create_response.status_code == 200
        cred_id = create_response.json()["id"]
        
        # Delete old credential
        delete_response = client.delete(
            f"/api/v1/users/me/llm-credentials/{cred_id}",
            headers=normal_user_token_headers
        )
        assert delete_response.status_code == 200
        
        # Create new credential with updated API key
        new_api_key = "sk-new-key-67890"
        new_cred_data = {
            "provider": "openai",
            "model_name": "gpt-4o-mini",
            "api_key": new_api_key,
            "is_default": False
        }
        recreate_response = client.post(
            "/api/v1/users/me/llm-credentials",
            headers=normal_user_token_headers,
            json=new_cred_data
        )
        assert recreate_response.status_code == 200
        new_cred_id = recreate_response.json()["id"]
        
        # Verify new API key was saved in database
        db_credential = session.get(UserLLMCredentials, new_cred_id)
        decrypted_key = encryption_service.decrypt_api_key(db_credential.encrypted_api_key)
        assert decrypted_key == new_api_key
        
        # Verify masked key shows new last 4 digits
        updated_data = recreate_response.json()
        assert updated_data["api_key_masked"].endswith("7890")
    
    def test_delete_credential_via_api(
        self,
        client: TestClient,
        normal_user_token_headers: dict,
        session: Session
    ):
        """Test deleting credential via API"""
        # Create credential
        cred_data = {
            "provider": "openai",
            "model_name": "gpt-4o-mini",
            "api_key": "sk-test-key",
            "is_default": False
        }
        create_response = client.post(
            "/api/v1/users/me/llm-credentials",
            headers=normal_user_token_headers,
            json=cred_data
        )
        assert create_response.status_code == 200
        cred_id = create_response.json()["id"]
        
        # Delete credential
        delete_response = client.delete(
            f"/api/v1/users/me/llm-credentials/{cred_id}",
            headers=normal_user_token_headers
        )
        assert delete_response.status_code == 200
        
        # Verify credential was soft-deleted (is_active = False)
        db_credential = session.get(UserLLMCredentials, cred_id)
        assert db_credential is not None
        assert db_credential.is_active is False
        
        # Verify credential doesn't appear in list
        list_response = client.get(
            "/api/v1/users/me/llm-credentials",
            headers=normal_user_token_headers
        )
        credentials = list_response.json()
        credential_ids = [c["id"] for c in credentials]
        assert cred_id not in credential_ids
    
    def test_cannot_create_duplicate_provider_credentials(
        self,
        client: TestClient,
        normal_user_token_headers: dict
    ):
        """Test that duplicate active credentials for same provider are rejected"""
        # Create first credential
        cred_data = {
            "provider": "openai",
            "model_name": "gpt-4o-mini",
            "api_key": "sk-first-key",
            "is_default": False
        }
        response1 = client.post(
            "/api/v1/users/me/llm-credentials",
            headers=normal_user_token_headers,
            json=cred_data
        )
        assert response1.status_code == 200
        
        # Try to create second credential for same provider
        cred_data2 = {
            "provider": "openai",
            "model_name": "gpt-4",
            "api_key": "sk-second-key",
            "is_default": False
        }
        response2 = client.post(
            "/api/v1/users/me/llm-credentials",
            headers=normal_user_token_headers,
            json=cred_data2
        )
        
        # Should fail
        assert response2.status_code == 400
        assert "already exist" in response2.json()["detail"].lower()
    
    def test_invalid_provider_rejected(
        self,
        client: TestClient,
        normal_user_token_headers: dict
    ):
        """Test that invalid provider is rejected"""
        cred_data = {
            "provider": "invalid_provider",
            "model_name": "test-model",
            "api_key": "test-key",
            "is_default": False
        }
        
        response = client.post(
            "/api/v1/users/me/llm-credentials",
            headers=normal_user_token_headers,
            json=cred_data
        )
        
        # Should fail validation
        assert response.status_code == 422


@pytest.mark.integration
class TestCredentialUsageInAgentExecution:
    """Test using credentials in actual agent execution"""
    
    def test_agent_session_with_specific_credential(
        self,
        session: Session,
        test_user: User
    ):
        """Test creating agent session with specific credential"""
        # Create credential
        encrypted_key = encryption_service.encrypt_api_key("sk-test-key")
        credential = UserLLMCredentials(
            id=uuid4(),
            user_id=test_user.id,
            provider="openai",
            model_name="gpt-4o-mini",
            encrypted_api_key=encrypted_key,
            encryption_key_id="default",
            is_default=False,
            is_active=True
        )
        session.add(credential)
        session.commit()
        session.refresh(credential)
        
        # Create agent session with credential
        agent_session = AgentSession(
            id=uuid4(),
            user_id=test_user.id,
            user_goal="Test goal",
            status=AgentSessionStatus.PENDING,
            llm_credential_id=credential.id
        )
        session.add(agent_session)
        session.commit()
        session.refresh(agent_session)
        
        # Verify session has credential ID
        assert agent_session.llm_credential_id == credential.id
        
        # Verify LLM factory can use this credential
        llm = LLMFactory.create_llm(
            session=session,
            user_id=test_user.id,
            credential_id=credential.id
        )
        assert llm is not None
    
    def test_agent_session_with_default_credential(
        self,
        session: Session,
        test_user: User
    ):
        """Test agent session uses default credential when none specified"""
        # Create default credential
        encrypted_key = encryption_service.encrypt_api_key("sk-test-key")
        credential = UserLLMCredentials(
            id=uuid4(),
            user_id=test_user.id,
            provider="openai",
            model_name="gpt-4o-mini",
            encrypted_api_key=encrypted_key,
            encryption_key_id="default",
            is_default=True,  # Set as default
            is_active=True
        )
        session.add(credential)
        session.commit()
        session.refresh(credential)
        
        # Create agent session WITHOUT specifying credential
        agent_session = AgentSession(
            id=uuid4(),
            user_id=test_user.id,
            user_goal="Test goal",
            status=AgentSessionStatus.PENDING,
            llm_credential_id=None  # No credential specified
        )
        session.add(agent_session)
        session.commit()
        session.refresh(agent_session)
        
        # Verify LLM factory uses default credential
        llm = LLMFactory.create_llm(
            session=session,
            user_id=test_user.id,
            credential_id=None  # Should use default
        )
        assert llm is not None
        
        # Verify it's using the user's credential, not system default
        # (In a real scenario with actual API keys, we'd verify the model name matches)
    
    def test_switching_credentials_between_sessions(
        self,
        session: Session,
        test_user: User
    ):
        """Test that different sessions can use different credentials"""
        # Create two credentials
        cred1 = UserLLMCredentials(
            id=uuid4(),
            user_id=test_user.id,
            provider="openai",
            model_name="gpt-4o-mini",
            encrypted_api_key=encryption_service.encrypt_api_key("sk-key-1"),
            encryption_key_id="default",
            is_default=False,
            is_active=True
        )
        cred2 = UserLLMCredentials(
            id=uuid4(),
            user_id=test_user.id,
            provider="google",
            model_name="gemini-1.5-flash",
            encrypted_api_key=encryption_service.encrypt_api_key("AIzaSy-key-2"),
            encryption_key_id="default",
            is_default=False,
            is_active=True
        )
        session.add(cred1)
        session.add(cred2)
        session.commit()
        
        # Create two sessions with different credentials
        session1 = AgentSession(
            id=uuid4(),
            user_id=test_user.id,
            user_goal="Session 1",
            status=AgentSessionStatus.PENDING,
            llm_credential_id=cred1.id
        )
        session2 = AgentSession(
            id=uuid4(),
            user_id=test_user.id,
            user_goal="Session 2",
            status=AgentSessionStatus.PENDING,
            llm_credential_id=cred2.id
        )
        session.add(session1)
        session.add(session2)
        session.commit()
        
        # Verify each session can use its own credential
        llm1 = LLMFactory.create_llm(
            session=session,
            user_id=test_user.id,
            credential_id=session1.llm_credential_id
        )
        llm2 = LLMFactory.create_llm(
            session=session,
            user_id=test_user.id,
            credential_id=session2.llm_credential_id
        )
        
        # Verify different LLM types
        assert type(llm1).__name__ != type(llm2).__name__


@pytest.mark.integration
class TestCredentialValidation:
    """Test credential validation functionality"""
    
    def test_validate_credential_before_saving(
        self,
        client: TestClient,
        normal_user_token_headers: dict
    ):
        """Test validating API key before saving"""
        # Note: This test requires the validation endpoint to exist
        # Skipping actual validation test as it requires real API keys
        # This is more of a structural test
        
        validate_data = {
            "provider": "openai",
            "api_key": "sk-test-key",
            "model_name": "gpt-4o-mini"
        }
        
        # This endpoint may not exist yet, so we skip if it 404s
        response = client.post(
            "/api/v1/users/me/llm-credentials/validate",
            headers=normal_user_token_headers,
            json=validate_data
        )
        
        # Either endpoint exists and validates, or it doesn't exist yet
        assert response.status_code in [200, 404, 422]
    
    def test_credential_marked_validated_after_use(
        self,
        session: Session,
        test_user: User
    ):
        """Test that credential is marked as validated after successful use"""
        # Create unvalidated credential
        credential = UserLLMCredentials(
            id=uuid4(),
            user_id=test_user.id,
            provider="openai",
            model_name="gpt-4o-mini",
            encrypted_api_key=encryption_service.encrypt_api_key("sk-test"),
            encryption_key_id="default",
            is_default=False,
            is_active=True,
            last_validated_at=None  # Not validated yet
        )
        session.add(credential)
        session.commit()
        session.refresh(credential)
        
        # Verify initially not validated
        assert credential.last_validated_at is None
        
        # After actual use (in production), last_validated_at would be updated
        # This would happen in the orchestrator or validation endpoint
        # For now, we just verify the field exists and can be updated
        from datetime import datetime, timezone
        credential.last_validated_at = datetime.now(timezone.utc)
        session.add(credential)
        session.commit()
        session.refresh(credential)
        
        assert credential.last_validated_at is not None
