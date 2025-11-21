"""
Artifact Management Service - Manages generated artifacts (models, plots, reports).

Week 11-12 implementation: Storage, retrieval, and cleanup of agent-generated artifacts.
"""

import os
import shutil
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from sqlmodel import Session, select

from app.models import AgentArtifact, AgentSession


class ArtifactManager:
    """
    Manages storage and retrieval of agent artifacts.
    
    Artifacts can be:
    - Trained models (.pkl, .joblib)
    - Visualizations (.png)
    - Reports (.md, .html, .pdf)
    - Data files (.csv, .json)
    - Code files (.py)
    """
    
    def __init__(self, base_storage_path: str = "/tmp/agent_artifacts"):
        """
        Initialize the artifact manager.
        
        Args:
            base_storage_path: Base directory for storing artifacts
        """
        self.base_storage_path = Path(base_storage_path)
        self.base_storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_artifact(
        self,
        db: Session,
        session_id: uuid.UUID,
        artifact_type: str,
        name: str,
        file_path: str,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentArtifact:
        """
        Save an artifact to the database and filesystem.
        
        Args:
            db: Database session
            session_id: Session ID the artifact belongs to
            artifact_type: Type of artifact (model, plot, report, code, data)
            name: Artifact name
            file_path: Current file path (will be moved to managed storage)
            description: Optional description
            metadata: Optional metadata dictionary
        
        Returns:
            Created artifact record
        """
        # Get session to verify it exists
        session = db.get(AgentSession, session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Create session-specific directory
        session_dir = self.base_storage_path / str(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_extension = Path(file_path).suffix
        unique_filename = f"{artifact_type}_{uuid.uuid4()}{file_extension}"
        target_path = session_dir / unique_filename
        
        # Copy or move file to managed storage
        if os.path.exists(file_path):
            shutil.copy2(file_path, target_path)
        else:
            raise FileNotFoundError(f"Source file not found: {file_path}")
        
        # Get file metadata
        file_size = os.path.getsize(target_path)
        mime_type = self._get_mime_type(file_extension)
        
        # Create artifact record
        artifact = AgentArtifact(
            session_id=session_id,
            artifact_type=artifact_type,
            name=name,
            description=description,
            file_path=str(target_path),
            mime_type=mime_type,
            size_bytes=file_size,
            metadata_json=str(metadata) if metadata else None,
        )
        
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        
        return artifact
    
    def get_artifact(self, db: Session, artifact_id: uuid.UUID) -> AgentArtifact | None:
        """
        Get an artifact by ID.
        
        Args:
            db: Database session
            artifact_id: Artifact ID
        
        Returns:
            Artifact record or None if not found
        """
        return db.get(AgentArtifact, artifact_id)
    
    def get_session_artifacts(
        self,
        db: Session,
        session_id: uuid.UUID,
        artifact_type: str | None = None,
    ) -> list[AgentArtifact]:
        """
        Get all artifacts for a session.
        
        Args:
            db: Database session
            session_id: Session ID
            artifact_type: Optional filter by artifact type
        
        Returns:
            List of artifacts
        """
        query = select(AgentArtifact).where(AgentArtifact.session_id == session_id)
        
        if artifact_type:
            query = query.where(AgentArtifact.artifact_type == artifact_type)
        
        return list(db.exec(query).all())
    
    def delete_artifact(self, db: Session, artifact_id: uuid.UUID) -> bool:
        """
        Delete an artifact from database and filesystem.
        
        Args:
            db: Database session
            artifact_id: Artifact ID
        
        Returns:
            True if deleted, False if not found
        """
        artifact = db.get(AgentArtifact, artifact_id)
        
        if not artifact:
            return False
        
        # Delete file from filesystem
        if artifact.file_path and os.path.exists(artifact.file_path):
            try:
                os.remove(artifact.file_path)
            except Exception as e:
                print(f"Warning: Could not delete file {artifact.file_path}: {e}")
        
        # Delete from database
        db.delete(artifact)
        db.commit()
        
        return True
    
    def cleanup_old_artifacts(
        self,
        db: Session,
        retention_days: int = 30,
    ) -> int:
        """
        Clean up artifacts older than retention period.
        
        Args:
            db: Database session
            retention_days: Number of days to retain artifacts
        
        Returns:
            Number of artifacts deleted
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        
        # Find old artifacts
        query = select(AgentArtifact).where(AgentArtifact.created_at < cutoff_date)
        old_artifacts = db.exec(query).all()
        
        deleted_count = 0
        
        for artifact in old_artifacts:
            if self.delete_artifact(db, artifact.id):
                deleted_count += 1
        
        return deleted_count
    
    def cleanup_session_artifacts(self, db: Session, session_id: uuid.UUID) -> int:
        """
        Clean up all artifacts for a session.
        
        Args:
            db: Database session
            session_id: Session ID
        
        Returns:
            Number of artifacts deleted
        """
        artifacts = self.get_session_artifacts(db, session_id)
        deleted_count = 0
        
        for artifact in artifacts:
            if self.delete_artifact(db, artifact.id):
                deleted_count += 1
        
        # Try to delete session directory if empty
        session_dir = self.base_storage_path / str(session_id)
        if session_dir.exists():
            try:
                session_dir.rmdir()  # Will only work if directory is empty
            except OSError:
                pass  # Directory not empty or other error
        
        return deleted_count
    
    def get_artifact_file_path(self, db: Session, artifact_id: uuid.UUID) -> str | None:
        """
        Get the file path for an artifact.
        
        Args:
            db: Database session
            artifact_id: Artifact ID
        
        Returns:
            File path or None if artifact not found
        """
        artifact = db.get(AgentArtifact, artifact_id)
        return artifact.file_path if artifact else None
    
    def _get_mime_type(self, file_extension: str) -> str:
        """
        Get MIME type from file extension.
        
        Args:
            file_extension: File extension (including dot)
        
        Returns:
            MIME type string
        """
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".pdf": "application/pdf",
            ".html": "text/html",
            ".md": "text/markdown",
            ".txt": "text/plain",
            ".json": "application/json",
            ".csv": "text/csv",
            ".pkl": "application/octet-stream",
            ".joblib": "application/octet-stream",
            ".py": "text/x-python",
        }
        
        return mime_types.get(file_extension.lower(), "application/octet-stream")
    
    def get_storage_stats(self, db: Session) -> dict[str, Any]:
        """
        Get storage statistics.
        
        Args:
            db: Database session
        
        Returns:
            Dictionary with storage statistics
        """
        # Count artifacts by type
        all_artifacts = db.exec(select(AgentArtifact)).all()
        
        total_count = len(all_artifacts)
        total_size = sum(a.size_bytes or 0 for a in all_artifacts)
        
        type_counts: dict[str, int] = {}
        for artifact in all_artifacts:
            type_counts[artifact.artifact_type] = type_counts.get(artifact.artifact_type, 0) + 1
        
        return {
            "total_artifacts": total_count,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "artifacts_by_type": type_counts,
            "storage_path": str(self.base_storage_path),
        }
