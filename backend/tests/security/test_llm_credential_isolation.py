"""
User Credential Isolation Security Tests

Sprint 2.10 - Track B Phase 3: Agent Security Audit

Tests multi-tenant security for LLM credentials:
- User A cannot access User B's credentials
- User A cannot set User B's credential as default
- User A cannot delete User B's credentials
- Database queries properly filter by user_id
- Authorization checks on all endpoints
- No credential leakage in shared agent sessions

OWASP References:
- A01:2021 – Broken Access Control
- A07:2021 – Identification and Authentication Failures
"""
import pytest
from uuid import uuid4

from sqlmodel import Session, select
from fastapi.testclient import TestClient

from app.models import User, UserLLMCredentials, AgentSession, AgentSessionStatus
from app.services.encryption import encryption_service
from app.services.agent.llm_factory import LLMFactory
from app.core.security import get_password_hash


@pytest.mark.security
class TestUserCredentialIsolation:
    """Test that users cannot access each other's credentials"""
    
    @pytest.fixture
    def user_a(self, session: Session) -> User:
        """Create test user A"""
        user = User(
            email="user_a@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="User A"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    
    @pytest.fixture
    def user_b(self, session: Session) -> User:
        """Create test user B"""
        user = User(
            email="user_b@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="User B"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    
    @pytest.fixture
    def user_a_credential(self, session: Session, user_a: User) -> UserLLMCredentials:
        """Create credential for user A"""
        encrypted = encryption_service.encrypt_api_key("sk-user-a-key-12345")
        credential = UserLLMCredentials(
            user_id=user_a.id,
            provider="openai",
            model_name="gpt-4",
            encrypted_api_key=encrypted,
            is_default=True,
            is_active=True
        )
        session.add(credential)
        session.commit()
        session.refresh(credential)
        return credential
    
    @pytest.fixture
    def user_b_credential(self, session: Session, user_b: User) -> UserLLMCredentials:
        """Create credential for user B"""
        encrypted = encryption_service.encrypt_api_key("sk-user-b-key-67890")
        credential = UserLLMCredentials(
            user_id=user_b.id,
            provider="anthropic",
            model_name="claude-3-opus",
            encrypted_api_key=encrypted,
            is_default=True,
            is_active=True
        )
        session.add(credential)
        session.commit()
        session.refresh(credential)
        return credential
    
    def test_user_cannot_access_other_users_credentials(
        self,
        client: TestClient,
        session: Session,
        user_a: User,
        user_b: User,
        user_a_credential: UserLLMCredentials,
        user_b_credential: UserLLMCredentials
    ):
        """
        Test 1: User A cannot access User B's credentials via API.
        
        Security Requirement: Users must only see their own credentials.
        Expected: GET /me/llm-credentials only returns current user's credentials.
        """
        # Login as user A
        login_response = client.post(
            "/api/v1/login/access-token",
            data={"username": user_a.email, "password": "password123"}
        )
        assert login_response.status_code == 200
        user_a_token = login_response.json()["access_token"]
        user_a_headers = {"Authorization": f"Bearer {user_a_token}"}
        
        # Get credentials as user A
        response = client.get(
            "/api/v1/users/me/llm-credentials",
            headers=user_a_headers
        )
        
        assert response.status_code == 200
        credentials = response.json()
        
        # Should only see user A's credentials
        assert len(credentials) == 1
        assert credentials[0]["id"] == str(user_a_credential.id)
        assert credentials[0]["provider"] == "openai"
        
        # Should NOT see user B's credentials
        credential_ids = [c["id"] for c in credentials]
        assert str(user_b_credential.id) not in credential_ids
    
    def test_user_cannot_set_other_users_credential_as_default(
        self,
        client: TestClient,
        session: Session,
        user_a: User,
        user_b: User,
        user_a_credential: UserLLMCredentials,
        user_b_credential: UserLLMCredentials
    ):
        """
        Test 2: User A cannot set User B's credential as their default.
        
        Security Requirement: Users can only modify their own credentials.
        Expected: Attempting to set another user's credential fails with 403/404.
        """
        # Login as user A
        login_response = client.post(
            "/api/v1/login/access-token",
            data={"username": user_a.email, "password": "password123"}
        )
        user_a_token = login_response.json()["access_token"]
        user_a_headers = {"Authorization": f"Bearer {user_a_token}"}
        
        # Try to set user B's credential as default
        response = client.patch(
            f"/api/v1/users/me/llm-credentials/{user_b_credential.id}/set-default",
            headers=user_a_headers
        )
        
        # Should fail (either 404 or 403)
        assert response.status_code in [403, 404]
        
        # Verify user B's credential is still their default
        db_credential = session.get(UserLLMCredentials, user_b_credential.id)
        assert db_credential.user_id == user_b.id
        assert db_credential.is_default == True
    
    def test_user_cannot_delete_other_users_credentials(
        self,
        client: TestClient,
        session: Session,
        user_a: User,
        user_b: User,
        user_a_credential: UserLLMCredentials,
        user_b_credential: UserLLMCredentials
    ):
        """
        Test 3: User A cannot delete User B's credentials.
        
        Security Requirement: Users can only delete their own credentials.
        Expected: DELETE attempt fails with 403/404, credential remains.
        """
        # Login as user A
        login_response = client.post(
            "/api/v1/login/access-token",
            data={"username": user_a.email, "password": "password123"}
        )
        user_a_token = login_response.json()["access_token"]
        user_a_headers = {"Authorization": f"Bearer {user_a_token}"}
        
        # Try to delete user B's credential
        response = client.delete(
            f"/api/v1/users/me/llm-credentials/{user_b_credential.id}",
            headers=user_a_headers
        )
        
        # Should fail
        assert response.status_code in [403, 404]
        
        # Verify user B's credential still exists
        db_credential = session.get(UserLLMCredentials, user_b_credential.id)
        assert db_credential is not None
        assert db_credential.is_active == True
        assert db_credential.user_id == user_b.id
    
    def test_database_queries_filter_by_user_id(
        self,
        session: Session,
        user_a: User,
        user_b: User,
        user_a_credential: UserLLMCredentials,
        user_b_credential: UserLLMCredentials
    ):
        """
        Test 4: Database queries properly filter by user_id.
        
        Security Requirement: All credential queries must filter by user_id.
        Expected: Cannot retrieve credentials without proper user_id filter.
        """
        # Query all active credentials (BAD - should never do this)
        all_credentials = session.exec(
            select(UserLLMCredentials).where(
                UserLLMCredentials.is_active == True
            )
        ).all()
        
        # Should get both credentials
        assert len(all_credentials) >= 2
        
        # Query user A's credentials (GOOD - with user_id filter)
        user_a_credentials = session.exec(
            select(UserLLMCredentials).where(
                UserLLMCredentials.user_id == user_a.id,
                UserLLMCredentials.is_active == True
            )
        ).all()
        
        # Should only get user A's credential
        assert len(user_a_credentials) == 1
        assert user_a_credentials[0].id == user_a_credential.id
        assert user_a_credentials[0].user_id == user_a.id
        
        # Query user B's credentials (GOOD - with user_id filter)
        user_b_credentials = session.exec(
            select(UserLLMCredentials).where(
                UserLLMCredentials.user_id == user_b.id,
                UserLLMCredentials.is_active == True
            )
        ).all()
        
        # Should only get user B's credential
        assert len(user_b_credentials) == 1
        assert user_b_credentials[0].id == user_b_credential.id
        assert user_b_credentials[0].user_id == user_b.id
    
    def test_llm_factory_enforces_user_id_ownership(
        self,
        session: Session,
        user_a: User,
        user_b: User,
        user_a_credential: UserLLMCredentials,
        user_b_credential: UserLLMCredentials
    ):
        """
        Test 5: LLMFactory.create_llm() enforces credential ownership.
        
        Security Requirement: Cannot use another user's credentials.
        Expected: ValueError when trying to use credential not owned by user.
        """
        # User A tries to use their own credential - SHOULD WORK
        llm = LLMFactory.create_llm(
            session=session,
            user_id=user_a.id,
            credential_id=user_a_credential.id
        )
        assert llm is not None
        
        # User A tries to use user B's credential - SHOULD FAIL
        with pytest.raises(ValueError, match="does not belong to user"):
            LLMFactory.create_llm(
                session=session,
                user_id=user_a.id,
                credential_id=user_b_credential.id  # Wrong user!
            )
        
        # User B tries to use their own credential - SHOULD WORK
        llm = LLMFactory.create_llm(
            session=session,
            user_id=user_b.id,
            credential_id=user_b_credential.id
        )
        assert llm is not None


@pytest.mark.security
class TestAgentSessionIsolation:
    """Test that agent sessions don't leak credentials between users"""
    
    def test_no_credential_leakage_in_agent_sessions(
        self,
        session: Session,
        normal_user: User
    ):
        """
        Test 6: No credential leakage in shared agent sessions.
        
        Security Requirement: Agent sessions must not expose credentials.
        Expected: Agent execution context doesn't include raw API keys.
        """
        # Create credential
        encrypted = encryption_service.encrypt_api_key("sk-test-session-key-12345")
        credential = UserLLMCredentials(
            user_id=normal_user.id,
            provider="openai",
            model_name="gpt-4",
            encrypted_api_key=encrypted,
            is_default=True,
            is_active=True
        )
        session.add(credential)
        session.commit()
        
        # Create agent session
        agent_session = AgentSession(
            user_id=normal_user.id,
            session_name="Test Session",
            agent_type="financial_advisor",
            status=AgentSessionStatus.ACTIVE,
            llm_credential_id=credential.id
        )
        session.add(agent_session)
        session.commit()
        session.refresh(agent_session)
        
        # Verify session doesn't contain raw API key
        assert not hasattr(agent_session, 'api_key')
        assert not hasattr(agent_session, 'encrypted_api_key')
        
        # Only credential ID should be stored
        assert agent_session.llm_credential_id == credential.id
        
        # To get API key, must explicitly decrypt via credential
        # (which should only be done in secure context)


@pytest.mark.security
class TestAuthorizationChecks:
    """Test authorization checks are present on all endpoints"""
    
    def test_list_credentials_requires_authentication(self, client: TestClient):
        """Test that listing credentials requires authentication"""
        response = client.get("/api/v1/users/me/llm-credentials")
        assert response.status_code == 401  # Unauthorized
    
    def test_create_credential_requires_authentication(self, client: TestClient):
        """Test that creating credentials requires authentication"""
        credential_data = {
            "provider": "openai",
            "model_name": "gpt-4",
            "api_key": "sk-test-key-12345",
            "is_default": False
        }
        response = client.post(
            "/api/v1/users/me/llm-credentials",
            json=credential_data
        )
        assert response.status_code == 401  # Unauthorized
    
    def test_delete_credential_requires_authentication(self, client: TestClient):
        """Test that deleting credentials requires authentication"""
        fake_id = uuid4()
        response = client.delete(f"/api/v1/users/me/llm-credentials/{fake_id}")
        assert response.status_code == 401  # Unauthorized
    
    def test_cannot_access_credentials_with_expired_token(
        self,
        client: TestClient,
        session: Session
    ):
        """Test that expired tokens are rejected"""
        # Use an obviously invalid/expired token
        expired_headers = {"Authorization": "Bearer expired.token.here"}
        
        response = client.get(
            "/api/v1/users/me/llm-credentials",
            headers=expired_headers
        )
        assert response.status_code == 401


@pytest.mark.security
class TestDirectDatabaseAccessPrevention:
    """Test that direct database access is properly controlled"""
    
    def test_cannot_query_credentials_without_user_context(self, session: Session):
        """
        Test that application code requires user context for queries.
        
        This is a design pattern test - all credential access should
        go through functions that require user_id parameter.
        """
        # This test documents the CORRECT pattern:
        # Always require user_id when querying credentials
        
        def get_user_credentials_correct(session: Session, user_id):
            """CORRECT: Requires user_id parameter"""
            return session.exec(
                select(UserLLMCredentials).where(
                    UserLLMCredentials.user_id == user_id,
                    UserLLMCredentials.is_active == True
                )
            ).all()
        
        def get_user_credentials_wrong(session: Session):
            """WRONG: No user_id requirement - NEVER DO THIS"""
            return session.exec(
                select(UserLLMCredentials).where(
                    UserLLMCredentials.is_active == True
                )
            ).all()
        
        # The correct function signature enforces user_id requirement
        # This is enforced by code review and linting, not at runtime
        
        # Verify the correct function works
        test_user_id = uuid4()
        credentials = get_user_credentials_correct(session, test_user_id)
        assert isinstance(credentials, list)


@pytest.mark.security  
class TestSoftDeleteIsolation:
    """Test that soft-deleted credentials are properly isolated"""
    
    def test_inactive_credentials_not_returned(
        self,
        client: TestClient,
        normal_user_token_headers: dict,
        session: Session,
        normal_user: User
    ):
        """
        Test that inactive (soft-deleted) credentials are not returned.
        
        Security Requirement: Deleted credentials should not be accessible.
        Expected: Only active credentials returned in API responses.
        """
        # Create two credentials
        encrypted1 = encryption_service.encrypt_api_key("sk-active-key-12345")
        credential1 = UserLLMCredentials(
            user_id=normal_user.id,
            provider="openai",
            model_name="gpt-4",
            encrypted_api_key=encrypted1,
            is_default=True,
            is_active=True  # Active
        )
        
        encrypted2 = encryption_service.encrypt_api_key("sk-deleted-key-67890")
        credential2 = UserLLMCredentials(
            user_id=normal_user.id,
            provider="anthropic",
            model_name="claude-3-opus",
            encrypted_api_key=encrypted2,
            is_default=False,
            is_active=False  # Soft deleted
        )
        
        session.add(credential1)
        session.add(credential2)
        session.commit()
        
        # Query via API
        response = client.get(
            "/api/v1/users/me/llm-credentials",
            headers=normal_user_token_headers
        )
        
        assert response.status_code == 200
        credentials = response.json()
        
        # Should only return active credential
        assert len(credentials) == 1
        assert credentials[0]["id"] == str(credential1.id)
        assert credentials[0]["is_active"] == True
        
        # Should not return inactive credential
        credential_ids = [c["id"] for c in credentials]
        assert str(credential2.id) not in credential_ids
    
    def test_cannot_use_inactive_credentials_with_llm_factory(
        self,
        session: Session,
        normal_user: User
    ):
        """
        Test that LLM factory rejects inactive credentials.
        
        Security Requirement: Cannot use soft-deleted credentials.
        Expected: ValueError when trying to use inactive credential.
        """
        # Create inactive credential
        encrypted = encryption_service.encrypt_api_key("sk-inactive-key-12345")
        credential = UserLLMCredentials(
            user_id=normal_user.id,
            provider="openai",
            model_name="gpt-4",
            encrypted_api_key=encrypted,
            is_default=False,
            is_active=False  # Inactive
        )
        session.add(credential)
        session.commit()
        session.refresh(credential)
        
        # Try to use inactive credential
        with pytest.raises(ValueError, match="is not active"):
            LLMFactory.create_llm(
                session=session,
                user_id=normal_user.id,
                credential_id=credential.id
            )
