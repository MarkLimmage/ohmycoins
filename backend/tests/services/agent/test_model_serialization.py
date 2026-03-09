"""Tests for model serialization functionality."""
import json
from pathlib import Path

import joblib
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from app.services.agent.tools.model_training_tools import serialize_model_to_disk


class TestModelSerialization:
    """Test serialize_model_to_disk function."""

    def test_serialize_model_only(self, tmp_path: Path) -> None:
        """Test serializing a model without scaler or metadata."""
        # Create a simple model
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit([[1, 2], [3, 4], [5, 6]], [0, 1, 0])

        # Serialize
        result = serialize_model_to_disk(
            model=model,
            session_id="test_session_1",
            model_name="test_model",
            base_dir=str(tmp_path),
        )

        # Verify result
        assert "model_path" in result
        assert "scaler_path" not in result
        assert "metadata_path" not in result

        # Verify file exists
        model_path = Path(result["model_path"])
        assert model_path.exists()

        # Load and verify model works
        loaded_model = joblib.load(model_path)
        assert loaded_model.n_estimators == 10

    def test_serialize_model_with_scaler(self, tmp_path: Path) -> None:
        """Test serializing model with scaler."""
        # Create model and scaler
        scaler = StandardScaler()
        X = [[1, 2], [3, 4], [5, 6]]
        scaler.fit(X)

        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, [0, 1, 0])

        # Serialize with scaler
        result = serialize_model_to_disk(
            model=model,
            session_id="test_session_2",
            model_name="model_with_scaler",
            scaler=scaler,
            base_dir=str(tmp_path),
        )

        # Verify result
        assert "model_path" in result
        assert "scaler_path" in result
        assert "metadata_path" not in result

        # Verify scaler file exists and loads
        scaler_path = Path(result["scaler_path"])
        assert scaler_path.exists()
        loaded_scaler = joblib.load(scaler_path)
        assert hasattr(loaded_scaler, "mean_")

    def test_serialize_model_with_metadata(self, tmp_path: Path) -> None:
        """Test serializing model with metadata."""
        model = RandomForestClassifier(n_estimators=5, random_state=42)
        model.fit([[1, 2], [3, 4]], [0, 1])

        metadata = {
            "model_type": "random_forest",
            "accuracy": 0.95,
            "features": ["feature_1", "feature_2"],
        }

        # Serialize with metadata
        result = serialize_model_to_disk(
            model=model,
            session_id="test_session_3",
            model_name="model_with_meta",
            metadata=metadata,
            base_dir=str(tmp_path),
        )

        # Verify result
        assert "model_path" in result
        assert "metadata_path" in result

        # Verify metadata file exists and contains correct data
        metadata_path = Path(result["metadata_path"])
        assert metadata_path.exists()
        loaded_meta = json.loads(metadata_path.read_text())
        assert loaded_meta["model_type"] == "random_forest"
        assert loaded_meta["accuracy"] == 0.95

    def test_serialize_model_full(self, tmp_path: Path) -> None:
        """Test serializing model with scaler and metadata."""
        scaler = StandardScaler()
        X = [[1, 2], [3, 4], [5, 6]]
        scaler.fit(X)

        model = RandomForestClassifier(n_estimators=15, random_state=42)
        model.fit(X, [0, 1, 0])

        metadata = {
            "version": "1.0",
            "training_samples": 3,
            "features": ["feat1", "feat2"],
        }

        # Serialize everything
        result = serialize_model_to_disk(
            model=model,
            session_id="test_session_4",
            model_name="full_model",
            scaler=scaler,
            metadata=metadata,
            base_dir=str(tmp_path),
        )

        # Verify all three files
        assert "model_path" in result
        assert "scaler_path" in result
        assert "metadata_path" in result

        assert Path(result["model_path"]).exists()
        assert Path(result["scaler_path"]).exists()
        assert Path(result["metadata_path"]).exists()

    def test_directory_creation(self, tmp_path: Path) -> None:
        """Test that serialize_model_to_disk creates directories."""
        model = RandomForestClassifier(n_estimators=5, random_state=42)
        model.fit([[1, 2]], [0])

        base_dir = tmp_path / "nested" / "path" / "artifacts"
        session_id = "deep_session"

        result = serialize_model_to_disk(
            model=model,
            session_id=session_id,
            model_name="nested_model",
            base_dir=str(base_dir),
        )

        # Verify nested directory was created
        model_path = Path(result["model_path"])
        assert model_path.parent.name == session_id
        assert model_path.exists()
