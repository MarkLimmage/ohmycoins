"""
Tests for ArtifactManager.

Week 11-12 tests: Testing artifact storage, retrieval, and cleanup.
"""

import os
import tempfile
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
from sqlmodel import Session, create_engine, select
from sqlmodel.pool import StaticPool

from app.models import AgentArtifact, AgentSession, User
from app.services.agent.artifacts import ArtifactManager


@pytest.fixture(name="session")
def session_fixture():
    """Create a test database session."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create tables
    from app.models import SQLModel
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session


@pytest.fixture
def test_user(session: Session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password="hashed",
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def test_session(session: Session, test_user: User):
    """Create a test agent session."""
    agent_session = AgentSession(
        user_id=test_user.id,
        user_goal="Test goal",
        status="running",
    )
    session.add(agent_session)
    session.commit()
    session.refresh(agent_session)
    return agent_session


@pytest.fixture
def artifact_manager():
    """Create an ArtifactManager with temporary storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ArtifactManager(base_storage_path=tmpdir)
        yield manager


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Test content")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


class TestArtifactManagerInitialization:
    """Tests for ArtifactManager initialization."""
    
    def test_creates_storage_directory(self):
        """Test that storage directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "artifacts")
            manager = ArtifactManager(base_storage_path=storage_path)
            
            assert os.path.exists(storage_path)
            assert manager.base_storage_path == Path(storage_path)
    
    def test_default_storage_path(self):
        """Test default storage path."""
        manager = ArtifactManager()
        assert manager.base_storage_path == Path("/tmp/agent_artifacts")


class TestSaveArtifact:
    """Tests for save_artifact method."""
    
    def test_save_artifact_success(
        self, session: Session, test_session: AgentSession, artifact_manager: ArtifactManager, temp_file: str
    ):
        """Test successful artifact save."""
        artifact = artifact_manager.save_artifact(
            db=session,
            session_id=test_session.id,
            artifact_type="model",
            name="test_model.pkl",
            file_path=temp_file,
            description="Test model artifact",
        )
        
        assert artifact.id is not None
        assert artifact.session_id == test_session.id
        assert artifact.artifact_type == "model"
        assert artifact.name == "test_model.pkl"
        assert artifact.description == "Test model artifact"
        assert artifact.file_path is not None
        assert os.path.exists(artifact.file_path)
        assert artifact.size_bytes > 0
    
    def test_save_artifact_creates_session_directory(
        self, session: Session, test_session: AgentSession, artifact_manager: ArtifactManager, temp_file: str
    ):
        """Test that session-specific directory is created."""
        artifact = artifact_manager.save_artifact(
            db=session,
            session_id=test_session.id,
            artifact_type="plot",
            name="chart.png",
            file_path=temp_file,
        )
        
        session_dir = artifact_manager.base_storage_path / str(test_session.id)
        assert session_dir.exists()
        assert Path(artifact.file_path).parent == session_dir
    
    def test_save_artifact_invalid_session(
        self, session: Session, artifact_manager: ArtifactManager, temp_file: str
    ):
        """Test saving artifact with invalid session ID."""
        invalid_session_id = uuid.uuid4()
        
        with pytest.raises(ValueError, match="Session .* not found"):
            artifact_manager.save_artifact(
                db=session,
                session_id=invalid_session_id,
                artifact_type="model",
                name="test.pkl",
                file_path=temp_file,
            )
    
    def test_save_artifact_file_not_found(
        self, session: Session, test_session: AgentSession, artifact_manager: ArtifactManager
    ):
        """Test saving artifact with non-existent file."""
        with pytest.raises(FileNotFoundError):
            artifact_manager.save_artifact(
                db=session,
                session_id=test_session.id,
                artifact_type="model",
                name="test.pkl",
                file_path="/nonexistent/file.pkl",
            )
    
    def test_save_artifact_sets_mime_type(
        self, session: Session, test_session: AgentSession, artifact_manager: ArtifactManager
    ):
        """Test that MIME type is set correctly."""
        # Create temp files with different extensions
        extensions_and_types = [
            (".png", "image/png"),
            (".pdf", "application/pdf"),
            (".html", "text/html"),
            (".pkl", "application/octet-stream"),
        ]
        
        for ext, expected_mime in extensions_and_types:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                f.write(b"test")
                temp_path = f.name
            
            try:
                artifact = artifact_manager.save_artifact(
                    db=session,
                    session_id=test_session.id,
                    artifact_type="test",
                    name=f"test{ext}",
                    file_path=temp_path,
                )
                
                assert artifact.mime_type == expected_mime
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)


class TestGetArtifact:
    """Tests for get_artifact method."""
    
    def test_get_existing_artifact(
        self, session: Session, test_session: AgentSession, artifact_manager: ArtifactManager, temp_file: str
    ):
        """Test getting an existing artifact."""
        saved_artifact = artifact_manager.save_artifact(
            db=session,
            session_id=test_session.id,
            artifact_type="model",
            name="test.pkl",
            file_path=temp_file,
        )
        
        retrieved_artifact = artifact_manager.get_artifact(session, saved_artifact.id)
        
        assert retrieved_artifact is not None
        assert retrieved_artifact.id == saved_artifact.id
        assert retrieved_artifact.name == "test.pkl"
    
    def test_get_nonexistent_artifact(self, session: Session, artifact_manager: ArtifactManager):
        """Test getting a non-existent artifact."""
        artifact = artifact_manager.get_artifact(session, uuid.uuid4())
        assert artifact is None


class TestGetSessionArtifacts:
    """Tests for get_session_artifacts method."""
    
    def test_get_all_session_artifacts(
        self, session: Session, test_session: AgentSession, artifact_manager: ArtifactManager
    ):
        """Test getting all artifacts for a session."""
        # Create multiple artifacts
        for i in range(3):
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(b"test")
                temp_path = f.name
            
            try:
                artifact_manager.save_artifact(
                    db=session,
                    session_id=test_session.id,
                    artifact_type="model",
                    name=f"test_{i}.pkl",
                    file_path=temp_path,
                )
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        artifacts = artifact_manager.get_session_artifacts(session, test_session.id)
        
        assert len(artifacts) == 3
    
    def test_get_session_artifacts_by_type(
        self, session: Session, test_session: AgentSession, artifact_manager: ArtifactManager
    ):
        """Test filtering artifacts by type."""
        # Create artifacts of different types
        types = ["model", "plot", "report"]
        
        for artifact_type in types:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(b"test")
                temp_path = f.name
            
            try:
                artifact_manager.save_artifact(
                    db=session,
                    session_id=test_session.id,
                    artifact_type=artifact_type,
                    name=f"test.{artifact_type}",
                    file_path=temp_path,
                )
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        # Get only plot artifacts
        plot_artifacts = artifact_manager.get_session_artifacts(
            session, test_session.id, artifact_type="plot"
        )
        
        assert len(plot_artifacts) == 1
        assert plot_artifacts[0].artifact_type == "plot"


class TestDeleteArtifact:
    """Tests for delete_artifact method."""
    
    def test_delete_existing_artifact(
        self, session: Session, test_session: AgentSession, artifact_manager: ArtifactManager, temp_file: str
    ):
        """Test deleting an existing artifact."""
        artifact = artifact_manager.save_artifact(
            db=session,
            session_id=test_session.id,
            artifact_type="model",
            name="test.pkl",
            file_path=temp_file,
        )
        
        file_path = artifact.file_path
        assert os.path.exists(file_path)
        
        # Delete artifact
        result = artifact_manager.delete_artifact(session, artifact.id)
        
        assert result is True
        assert not os.path.exists(file_path)
        
        # Verify artifact is gone from database
        deleted_artifact = artifact_manager.get_artifact(session, artifact.id)
        assert deleted_artifact is None
    
    def test_delete_nonexistent_artifact(self, session: Session, artifact_manager: ArtifactManager):
        """Test deleting a non-existent artifact."""
        result = artifact_manager.delete_artifact(session, uuid.uuid4())
        assert result is False


class TestCleanupOldArtifacts:
    """Tests for cleanup_old_artifacts method."""
    
    def test_cleanup_old_artifacts(
        self, session: Session, test_session: AgentSession, artifact_manager: ArtifactManager
    ):
        """Test cleanup of old artifacts."""
        # Create an old artifact by manually setting created_at
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            temp_path = f.name
        
        try:
            artifact = artifact_manager.save_artifact(
                db=session,
                session_id=test_session.id,
                artifact_type="model",
                name="old_model.pkl",
                file_path=temp_path,
            )
            
            # Manually set created_at to 60 days ago
            old_date = datetime.now(timezone.utc) - timedelta(days=60)
            artifact.created_at = old_date
            session.add(artifact)
            session.commit()
            
            # Cleanup artifacts older than 30 days
            deleted_count = artifact_manager.cleanup_old_artifacts(session, retention_days=30)
            
            assert deleted_count == 1
            
            # Verify artifact is deleted
            deleted_artifact = artifact_manager.get_artifact(session, artifact.id)
            assert deleted_artifact is None
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestCleanupSessionArtifacts:
    """Tests for cleanup_session_artifacts method."""
    
    def test_cleanup_all_session_artifacts(
        self, session: Session, test_session: AgentSession, artifact_manager: ArtifactManager
    ):
        """Test cleanup of all artifacts for a session."""
        # Create multiple artifacts
        for i in range(3):
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(b"test")
                temp_path = f.name
            
            try:
                artifact_manager.save_artifact(
                    db=session,
                    session_id=test_session.id,
                    artifact_type="model",
                    name=f"model_{i}.pkl",
                    file_path=temp_path,
                )
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        # Cleanup all session artifacts
        deleted_count = artifact_manager.cleanup_session_artifacts(session, test_session.id)
        
        assert deleted_count == 3
        
        # Verify all artifacts are deleted
        remaining_artifacts = artifact_manager.get_session_artifacts(session, test_session.id)
        assert len(remaining_artifacts) == 0


class TestGetStorageStats:
    """Tests for get_storage_stats method."""
    
    def test_storage_stats(
        self, session: Session, test_session: AgentSession, artifact_manager: ArtifactManager
    ):
        """Test getting storage statistics."""
        # Create some artifacts
        types = ["model", "plot", "report"]
        
        for artifact_type in types:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(b"test content")
                temp_path = f.name
            
            try:
                artifact_manager.save_artifact(
                    db=session,
                    session_id=test_session.id,
                    artifact_type=artifact_type,
                    name=f"test.{artifact_type}",
                    file_path=temp_path,
                )
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        stats = artifact_manager.get_storage_stats(session)
        
        assert "total_artifacts" in stats
        assert stats["total_artifacts"] == 3
        assert "total_size_bytes" in stats
        assert stats["total_size_bytes"] > 0
        assert "total_size_mb" in stats
        assert "artifacts_by_type" in stats
        assert stats["artifacts_by_type"]["model"] == 1
        assert stats["artifacts_by_type"]["plot"] == 1
        assert stats["artifacts_by_type"]["report"] == 1
