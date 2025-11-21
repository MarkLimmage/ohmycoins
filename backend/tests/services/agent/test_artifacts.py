"""
Tests for ArtifactManager - Week 11 Implementation

Tests for the artifact management system.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import uuid
import json
from datetime import datetime, timedelta, timezone

from app.services.agent.artifacts import ArtifactManager


@pytest.fixture
def temp_base_dir():
    """Create and cleanup temporary base directory."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def artifact_manager(temp_base_dir):
    """Create ArtifactManager instance with temp directory."""
    return ArtifactManager(base_dir=str(temp_base_dir))


@pytest.fixture
def sample_session_id():
    """Generate sample session ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_artifact_file(temp_base_dir):
    """Create a sample artifact file."""
    test_file = temp_base_dir / "test_artifact.txt"
    test_file.write_text("Test artifact content")
    return test_file


class TestArtifactManagerInitialization:
    """Tests for ArtifactManager initialization."""

    def test_init_with_default_dir(self):
        """Test initialization with default base directory."""
        manager = ArtifactManager()
        
        assert manager.base_dir == Path("/tmp/agent_artifacts")
        assert manager.base_dir.exists()

    def test_init_with_custom_dir(self, temp_base_dir):
        """Test initialization with custom base directory."""
        manager = ArtifactManager(base_dir=str(temp_base_dir))
        
        assert manager.base_dir == temp_base_dir
        assert temp_base_dir.exists()


class TestSaveArtifact:
    """Tests for save_artifact method."""

    def test_save_artifact_success(self, artifact_manager, sample_session_id, sample_artifact_file):
        """Test successful artifact save."""
        artifact = artifact_manager.save_artifact(
            session_id=sample_session_id,
            artifact_type="report",
            name="Test Report",
            file_path=sample_artifact_file,
            description="Test artifact description",
            metadata={"key": "value"},
        )
        
        assert artifact.session_id == sample_session_id
        assert artifact.artifact_type == "report"
        assert artifact.name == "Test Report"
        assert artifact.description == "Test artifact description"
        assert artifact.file_path is not None
        assert Path(artifact.file_path).exists()
        assert artifact.size_bytes > 0
        assert artifact.mime_type == "text/plain"
        assert artifact.metadata_json is not None

    def test_save_artifact_creates_session_dir(self, artifact_manager, sample_session_id, sample_artifact_file, temp_base_dir):
        """Test that save_artifact creates session directory."""
        artifact_manager.save_artifact(
            session_id=sample_session_id,
            artifact_type="plot",
            name="Test Plot",
            file_path=sample_artifact_file,
        )
        
        session_dir = temp_base_dir / str(sample_session_id)
        assert session_dir.exists()
        assert session_dir.is_dir()

    def test_save_artifact_copies_file(self, artifact_manager, sample_session_id, sample_artifact_file, temp_base_dir):
        """Test that file is copied to managed location."""
        artifact = artifact_manager.save_artifact(
            session_id=sample_session_id,
            artifact_type="model",
            name="Test Model",
            file_path=sample_artifact_file,
        )
        
        copied_file = Path(artifact.file_path)
        assert copied_file.exists()
        assert copied_file.parent == temp_base_dir / str(sample_session_id)
        assert copied_file.read_text() == "Test artifact content"

    def test_save_artifact_file_not_found(self, artifact_manager, sample_session_id):
        """Test save_artifact raises error for non-existent file."""
        with pytest.raises(FileNotFoundError):
            artifact_manager.save_artifact(
                session_id=sample_session_id,
                artifact_type="report",
                name="Non-existent",
                file_path="/nonexistent/file.txt",
            )

    def test_save_artifact_mime_type_detection(self, artifact_manager, sample_session_id, temp_base_dir):
        """Test MIME type detection for different file types."""
        test_files = {
            "test.png": "image/png",
            "test.jpg": "image/jpeg",
            "test.pdf": "application/pdf",
            "test.md": "text/markdown",
            "test.json": "application/json",
        }
        
        for filename, expected_mime in test_files.items():
            test_file = temp_base_dir / filename
            test_file.write_text("test")
            
            artifact = artifact_manager.save_artifact(
                session_id=sample_session_id,
                artifact_type="test",
                name=filename,
                file_path=test_file,
            )
            
            assert artifact.mime_type == expected_mime


class TestListArtifacts:
    """Tests for list_artifacts method."""

    def test_list_artifacts_empty(self, artifact_manager, sample_session_id):
        """Test listing artifacts when none exist."""
        artifacts = artifact_manager.list_artifacts(
            session_id=sample_session_id,
            db_session=None,
        )
        
        assert artifacts == []

    def test_list_artifacts_no_db_session(self, artifact_manager, sample_session_id):
        """Test listing without database session."""
        artifacts = artifact_manager.list_artifacts(
            session_id=sample_session_id,
        )
        
        assert artifacts == []


class TestGetStorageStats:
    """Tests for get_storage_stats method."""

    def test_storage_stats_no_db_session(self, artifact_manager):
        """Test storage stats without database session."""
        stats = artifact_manager.get_storage_stats()
        
        assert stats["total_artifacts"] == 0
        assert stats["total_size_bytes"] == 0
        assert stats["artifacts_by_type"] == {}
        assert stats["artifacts_by_session"] == {}

    def test_storage_stats_structure(self, artifact_manager):
        """Test storage stats return structure."""
        stats = artifact_manager.get_storage_stats(db_session=None)
        
        assert "total_artifacts" in stats
        assert "total_size_bytes" in stats
        assert "artifacts_by_type" in stats
        assert "artifacts_by_session" in stats


class TestExportSessionArtifacts:
    """Tests for export_session_artifacts method."""

    def test_export_creates_directory(self, artifact_manager, sample_session_id, temp_base_dir):
        """Test that export creates output directory."""
        export_dir = temp_base_dir / "export"
        
        artifact_manager.export_session_artifacts(
            session_id=sample_session_id,
            export_dir=export_dir,
            db_session=None,
        )
        
        assert export_dir.exists()
        assert export_dir.is_dir()

    def test_export_creates_metadata_file(self, artifact_manager, sample_session_id, temp_base_dir):
        """Test that export creates metadata.json file."""
        export_dir = temp_base_dir / "export"
        
        artifact_manager.export_session_artifacts(
            session_id=sample_session_id,
            export_dir=export_dir,
            db_session=None,
        )
        
        metadata_file = export_dir / "metadata.json"
        assert metadata_file.exists()
        
        metadata = json.loads(metadata_file.read_text())
        assert metadata["session_id"] == str(sample_session_id)
        assert "export_date" in metadata
        assert "artifacts" in metadata


class TestMimeTypeDetection:
    """Tests for _get_mime_type method."""

    def test_mime_type_for_images(self, artifact_manager):
        """Test MIME type detection for image files."""
        assert artifact_manager._get_mime_type(Path("test.png")) == "image/png"
        assert artifact_manager._get_mime_type(Path("test.jpg")) == "image/jpeg"
        assert artifact_manager._get_mime_type(Path("test.jpeg")) == "image/jpeg"

    def test_mime_type_for_documents(self, artifact_manager):
        """Test MIME type detection for document files."""
        assert artifact_manager._get_mime_type(Path("test.pdf")) == "application/pdf"
        assert artifact_manager._get_mime_type(Path("test.md")) == "text/markdown"
        assert artifact_manager._get_mime_type(Path("test.html")) == "text/html"

    def test_mime_type_for_data_files(self, artifact_manager):
        """Test MIME type detection for data files."""
        assert artifact_manager._get_mime_type(Path("test.json")) == "application/json"
        assert artifact_manager._get_mime_type(Path("test.csv")) == "text/csv"

    def test_mime_type_for_model_files(self, artifact_manager):
        """Test MIME type detection for model files."""
        assert artifact_manager._get_mime_type(Path("model.pkl")) == "application/octet-stream"
        assert artifact_manager._get_mime_type(Path("model.joblib")) == "application/octet-stream"

    def test_mime_type_for_unknown(self, artifact_manager):
        """Test MIME type detection for unknown extensions."""
        assert artifact_manager._get_mime_type(Path("file.xyz")) == "application/octet-stream"


class TestCleanupOldArtifacts:
    """Tests for cleanup_old_artifacts method."""

    def test_cleanup_no_db_session(self, artifact_manager):
        """Test cleanup without database session."""
        count = artifact_manager.cleanup_old_artifacts(days=30)
        assert count == 0

    def test_cleanup_returns_count(self, artifact_manager):
        """Test cleanup returns deletion count."""
        count = artifact_manager.cleanup_old_artifacts(days=30, db_session=None)
        assert isinstance(count, int)
        assert count >= 0
