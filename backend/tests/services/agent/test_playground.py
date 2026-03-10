"""Tests for ModelPlaygroundService."""

import json
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.agent.playground import ModelPlaygroundService


@pytest.fixture
def playground():
    return ModelPlaygroundService(base_dir="/tmp/test_artifacts")


@pytest.fixture
def mock_artifact():
    artifact = MagicMock()
    artifact.id = uuid.uuid4()
    artifact.session_id = uuid.uuid4()
    artifact.file_path = "/tmp/test_artifacts/session1/model.joblib"
    artifact.created_at = None
    return artifact


class TestLoadModel:
    def test_load_model_not_found(self, playground):
        db = MagicMock()
        with patch.object(playground.artifact_manager, "get_artifact", return_value=None):
            with pytest.raises(FileNotFoundError):
                playground.load_model(uuid.uuid4(), db)

    @patch("app.services.agent.playground.joblib")
    def test_load_model_success(self, mock_joblib, playground, mock_artifact, tmp_path):
        # Create mock files
        model_dir = tmp_path / "session1"
        model_dir.mkdir()
        model_file = model_dir / "model.joblib"
        model_file.write_bytes(b"fake")
        mock_artifact.file_path = str(model_file)

        mock_joblib.load.return_value = MagicMock()  # mock model
        db = MagicMock()

        with patch.object(playground.artifact_manager, "get_artifact", return_value=mock_artifact):
            model, scaler, metadata = playground.load_model(mock_artifact.id, db)

        assert model is not None
        assert scaler is None  # no scaler file
        assert metadata == {}  # no metadata file

    @patch("app.services.agent.playground.joblib")
    def test_load_model_with_scaler_and_metadata(self, mock_joblib, playground, mock_artifact, tmp_path):
        model_dir = tmp_path / "session1"
        model_dir.mkdir()
        model_file = model_dir / "model.joblib"
        model_file.write_bytes(b"fake")
        scaler_file = model_dir / "model_scaler.joblib"
        scaler_file.write_bytes(b"fake_scaler")
        meta_file = model_dir / "model_metadata.json"
        meta_file.write_text(json.dumps({"model_type": "RandomForest", "feature_columns": ["a", "b"]}))
        mock_artifact.file_path = str(model_file)

        mock_joblib.load.side_effect = [MagicMock(), MagicMock()]  # model, scaler
        db = MagicMock()

        with patch.object(playground.artifact_manager, "get_artifact", return_value=mock_artifact):
            model, scaler, metadata = playground.load_model(mock_artifact.id, db)

        assert model is not None
        assert scaler is not None
        assert metadata["model_type"] == "RandomForest"


class TestPredict:
    def test_predict_regression(self, playground):
        import numpy as np
        model = MagicMock()
        model.predict.return_value = np.array([42.5])
        model.predict_proba = None  # no proba for regression
        # Remove predict_proba attribute
        del model.predict_proba

        metadata = {"task_type": "regression", "feature_columns": ["x1", "x2"]}
        result = playground.predict(model, None, {"x1": 1.0, "x2": 2.0}, metadata)

        assert result["prediction"] == 42.5
        assert result["task_type"] == "regression"
        assert "probabilities" not in result or result.get("probabilities") is None

    def test_predict_classification(self, playground):
        import numpy as np
        model = MagicMock()
        model.predict.return_value = np.array([1])
        model.predict_proba.return_value = np.array([[0.3, 0.7]])
        model.classes_ = np.array([0, 1])

        metadata = {"task_type": "classification", "feature_columns": ["x1"]}
        result = playground.predict(model, None, {"x1": 1.0}, metadata)

        assert result["prediction_label"] == "1"
        assert result["probabilities"] is not None
        assert "0" in result["probabilities"]
        assert "1" in result["probabilities"]


class TestGetModelInfo:
    def test_get_model_info_not_found(self, playground):
        db = MagicMock()
        with patch.object(playground.artifact_manager, "get_artifact", return_value=None):
            with pytest.raises(FileNotFoundError):
                playground.get_model_info(uuid.uuid4(), db)

    def test_get_model_info_success(self, playground, mock_artifact, tmp_path):
        model_dir = tmp_path / "session1"
        model_dir.mkdir()
        model_file = model_dir / "model.joblib"
        model_file.write_bytes(b"fake")
        meta_file = model_dir / "model_metadata.json"
        meta_file.write_text(json.dumps({
            "model_type": "GradientBoosting",
            "task_type": "classification",
            "feature_columns": ["price", "volume"],
            "metrics": {"accuracy": 0.85},
        }))
        mock_artifact.file_path = str(model_file)
        db = MagicMock()

        with patch.object(playground.artifact_manager, "get_artifact", return_value=mock_artifact):
            info = playground.get_model_info(mock_artifact.id, db)

        assert info["model_type"] == "GradientBoosting"
        assert info["feature_columns"] == ["price", "volume"]
        assert info["training_metrics"]["accuracy"] == 0.85
