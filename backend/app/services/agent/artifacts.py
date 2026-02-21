# mypy: ignore-errors
"""
Artifact Management System - Week 11 Implementation

Service for managing agent-generated artifacts (models, plots, reports).
"""

import json
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlmodel import Session, select

from app.models import AgentArtifact


class ArtifactManager:
    """
    Manages storage, retrieval, and cleanup of agent artifacts.

    Supports:
    - Trained models (.pkl, .joblib)
    - Generated plots (.png, .jpg)
    - Reports (Markdown, HTML, PDF)
    - Code artifacts (.py)
    - Data artifacts (.csv, .json)
    """

    def __init__(self, base_dir: str = "/tmp/agent_artifacts"):
        """
        Initialize the artifact manager.

        Args:
            base_dir: Base directory for storing artifacts
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_artifact(
        self,
        session_id: uuid.UUID,
        artifact_type: str,
        name: str,
        file_path: str | Path,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
        db_session: Session | None = None,
    ) -> AgentArtifact:
        """
        Save an artifact to storage and database.

        Args:
            session_id: Agent session ID
            artifact_type: Type of artifact (model, plot, report, code, data)
            name: Artifact name
            file_path: Path to the artifact file
            description: Optional description
            metadata: Optional metadata dictionary
            db_session: Database session (if None, creates new one)

        Returns:
            Created AgentArtifact instance
        """
        file_path = Path(file_path)

        # Validate file exists
        if not file_path.exists():
            raise FileNotFoundError(f"Artifact file not found: {file_path}")

        # Create session directory
        session_dir = self.base_dir / str(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)

        # Copy file to managed location
        dest_path = session_dir / file_path.name
        shutil.copy2(file_path, dest_path)

        # Get file metadata
        file_size = dest_path.stat().st_size
        mime_type = self._get_mime_type(dest_path)

        # Create database record
        artifact = AgentArtifact(
            session_id=session_id,
            artifact_type=artifact_type,
            name=name,
            description=description,
            file_path=str(dest_path),
            mime_type=mime_type,
            size_bytes=file_size,
            metadata_json=json.dumps(metadata) if metadata else None,
        )

        if db_session:
            db_session.add(artifact)
            db_session.commit()
            db_session.refresh(artifact)

        return artifact

    def get_artifact(
        self,
        artifact_id: uuid.UUID,
        db_session: Session,
    ) -> AgentArtifact | None:
        """
        Retrieve an artifact by ID.

        Args:
            artifact_id: Artifact ID
            db_session: Database session

        Returns:
            AgentArtifact instance or None if not found
        """
        statement = select(AgentArtifact).where(AgentArtifact.id == artifact_id)
        return db_session.exec(statement).first()

    def list_artifacts(
        self,
        session_id: uuid.UUID,
        artifact_type: str | None = None,
        db_session: Session | None = None,
    ) -> list[AgentArtifact]:
        """
        List all artifacts for a session.

        Args:
            session_id: Agent session ID
            artifact_type: Optional filter by artifact type
            db_session: Database session

        Returns:
            List of AgentArtifact instances
        """
        if not db_session:
            return []

        statement = select(AgentArtifact).where(AgentArtifact.session_id == session_id)

        if artifact_type:
            statement = statement.where(AgentArtifact.artifact_type == artifact_type)

        artifacts = db_session.exec(statement).all()
        return list(artifacts)

    def delete_artifact(
        self,
        artifact_id: uuid.UUID,
        db_session: Session,
    ) -> bool:
        """
        Delete an artifact from storage and database.

        Args:
            artifact_id: Artifact ID
            db_session: Database session

        Returns:
            True if deleted, False if not found
        """
        artifact = self.get_artifact(artifact_id, db_session)

        if not artifact:
            return False

        # Delete file if it exists
        if artifact.file_path:
            file_path = Path(artifact.file_path)
            if file_path.exists():
                try:
                    file_path.unlink()
                except Exception:
                    pass  # Continue even if file deletion fails

        # Delete database record
        db_session.delete(artifact)
        db_session.commit()

        return True

    def cleanup_session_artifacts(
        self,
        session_id: uuid.UUID,
        db_session: Session,
    ) -> int:
        """
        Delete all artifacts for a session.

        Args:
            session_id: Agent session ID
            db_session: Database session

        Returns:
            Number of artifacts deleted
        """
        artifacts = self.list_artifacts(session_id, db_session=db_session)
        count = 0

        for artifact in artifacts:
            if self.delete_artifact(artifact.id, db_session):
                count += 1

        # Delete session directory
        session_dir = self.base_dir / str(session_id)
        if session_dir.exists():
            try:
                shutil.rmtree(session_dir)
            except Exception:
                pass  # Continue even if directory deletion fails

        return count

    def cleanup_old_artifacts(
        self,
        days: int = 30,
        db_session: Session | None = None,
    ) -> int:
        """
        Delete artifacts older than specified days.

        Args:
            days: Number of days to retain artifacts
            db_session: Database session

        Returns:
            Number of artifacts deleted
        """
        if not db_session:
            return 0

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Find old artifacts
        statement = select(AgentArtifact).where(AgentArtifact.created_at < cutoff_date)
        old_artifacts = db_session.exec(statement).all()

        count = 0
        for artifact in old_artifacts:
            if self.delete_artifact(artifact.id, db_session):
                count += 1

        return count

    def get_storage_stats(self, db_session: Session | None = None) -> dict[str, Any]:
        """
        Get storage statistics.

        Args:
            db_session: Database session

        Returns:
            Dictionary with storage statistics
        """
        stats = {
            "total_artifacts": 0,
            "total_size_bytes": 0,
            "artifacts_by_type": {},
            "artifacts_by_session": {},
        }

        if not db_session:
            return stats

        # Get all artifacts
        statement = select(AgentArtifact)
        artifacts = db_session.exec(statement).all()

        stats["total_artifacts"] = len(artifacts)

        for artifact in artifacts:
            # Total size
            if artifact.size_bytes:
                stats["total_size_bytes"] += artifact.size_bytes

            # By type
            if artifact.artifact_type not in stats["artifacts_by_type"]:
                stats["artifacts_by_type"][artifact.artifact_type] = {
                    "count": 0,
                    "total_size_bytes": 0,
                }
            stats["artifacts_by_type"][artifact.artifact_type]["count"] += 1
            if artifact.size_bytes:
                stats["artifacts_by_type"][artifact.artifact_type][
                    "total_size_bytes"
                ] += artifact.size_bytes

            # By session
            session_key = str(artifact.session_id)
            if session_key not in stats["artifacts_by_session"]:
                stats["artifacts_by_session"][session_key] = {
                    "count": 0,
                    "total_size_bytes": 0,
                }
            stats["artifacts_by_session"][session_key]["count"] += 1
            if artifact.size_bytes:
                stats["artifacts_by_session"][session_key]["total_size_bytes"] += (
                    artifact.size_bytes
                )

        return stats

    def _get_mime_type(self, file_path: Path) -> str:
        """
        Determine MIME type from file extension.

        Args:
            file_path: Path to file

        Returns:
            MIME type string
        """
        extension = file_path.suffix.lower()

        mime_types = {
            ".pkl": "application/octet-stream",
            ".joblib": "application/octet-stream",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".md": "text/markdown",
            ".html": "text/html",
            ".pdf": "application/pdf",
            ".py": "text/x-python",
            ".csv": "text/csv",
            ".json": "application/json",
            ".txt": "text/plain",
        }

        return mime_types.get(extension, "application/octet-stream")

    def export_session_artifacts(
        self,
        session_id: uuid.UUID,
        export_dir: str | Path,
        db_session: Session,
    ) -> Path:
        """
        Export all artifacts for a session to a directory.

        Args:
            session_id: Agent session ID
            export_dir: Directory to export to
            db_session: Database session

        Returns:
            Path to export directory
        """
        export_dir = Path(export_dir)
        export_dir.mkdir(parents=True, exist_ok=True)

        artifacts = self.list_artifacts(session_id, db_session=db_session)

        for artifact in artifacts:
            if artifact.file_path:
                src_path = Path(artifact.file_path)
                if src_path.exists():
                    dest_path = export_dir / src_path.name
                    shutil.copy2(src_path, dest_path)

        # Create metadata file
        metadata = {
            "session_id": str(session_id),
            "export_date": datetime.utcnow().isoformat(),
            "artifacts": [
                {
                    "id": str(artifact.id),
                    "type": artifact.artifact_type,
                    "name": artifact.name,
                    "description": artifact.description,
                    "filename": Path(artifact.file_path).name
                    if artifact.file_path
                    else None,
                    "size_bytes": artifact.size_bytes,
                    "created_at": artifact.created_at.isoformat()
                    if artifact.created_at
                    else None,
                }
                for artifact in artifacts
            ],
        }

        metadata_path = export_dir / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2))

        return export_dir
