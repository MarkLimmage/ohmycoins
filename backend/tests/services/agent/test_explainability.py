# mypy: ignore-errors
"""Tests for ExplainabilityService."""

import json
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.services.agent.explainability import ExplainabilityService


@pytest.fixture
def service():
    return ExplainabilityService(base_dir="/tmp/test_artifacts")


@pytest.fixture
def mock_artifact(tmp_path):
    artifact = MagicMock()
    artifact.id = uuid.uuid4()
    artifact.session_id = uuid.uuid4()
    model_file = tmp_path / "model.joblib"
    model_file.write_bytes(b"fake")
    artifact.file_path = str(model_file)
    artifact.created_at = None
    return artifact


class TestExplainerSelection:
    def test_tree_model_supported(self, service):
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(n_estimators=5, random_state=42)
        X = np.random.randn(20, 3)
        y = (X[:, 0] > 0).astype(int)
        model.fit(X, y)
        assert service.is_supported(model) is True
        assert service.get_explainer_type(model) == "tree"

    def test_linear_model_supported(self, service):
        from sklearn.linear_model import LogisticRegression
        model = LogisticRegression(random_state=42)
        X = np.random.randn(20, 3)
        y = (X[:, 0] > 0).astype(int)
        model.fit(X, y)
        assert service.is_supported(model) is True
        assert service.get_explainer_type(model) == "linear"

    def test_svc_unsupported(self, service):
        from sklearn.svm import SVC
        model = SVC()
        assert service.is_supported(model) is False
        assert service.get_explainer_type(model) is None

    def test_svr_unsupported(self, service):
        from sklearn.svm import SVR
        model = SVR()
        assert service.is_supported(model) is False

    def test_gradient_boosting_tree(self, service):
        from sklearn.ensemble import GradientBoostingClassifier
        model = GradientBoostingClassifier(n_estimators=5, random_state=42)
        X = np.random.randn(20, 3)
        y = (X[:, 0] > 0).astype(int)
        model.fit(X, y)
        assert service.get_explainer_type(model) == "tree"

    def test_decision_tree(self, service):
        from sklearn.tree import DecisionTreeClassifier
        model = DecisionTreeClassifier(random_state=42)
        assert service.get_explainer_type(model) == "tree"

    def test_ridge_linear(self, service):
        from sklearn.linear_model import Ridge
        model = Ridge()
        assert service.get_explainer_type(model) == "linear"


class TestGlobalShap:
    def test_global_shap_tree_model(self, service, mock_artifact, tmp_path):
        from sklearn.ensemble import RandomForestClassifier

        model = RandomForestClassifier(n_estimators=5, random_state=42)
        X = np.random.randn(50, 3)
        y = (X[:, 0] > 0).astype(int)
        model.fit(X, y)

        metadata = {"feature_columns": ["f1", "f2", "f3"], "model_type": "RandomForestClassifier"}
        db = MagicMock()

        with (
            patch.object(service.playground, "load_model", return_value=(model, None, metadata)),
            patch.object(service.artifact_manager, "get_artifact", return_value=mock_artifact),
        ):
            result = service.compute_global_shap(mock_artifact.id, db, max_samples=20)

        assert result["supported"] is True
        assert len(result["feature_importance"]) == 3
        assert result["feature_importance"][0]["feature_name"] in ("f1", "f2", "f3")
        assert result["feature_importance"][0]["importance"] >= 0
        assert result["model_type"] == "RandomForestClassifier"
        assert result["cached"] is False

    def test_global_shap_linear_model(self, service, mock_artifact, tmp_path):
        from sklearn.linear_model import LogisticRegression

        model = LogisticRegression(random_state=42, max_iter=200)
        X = np.random.randn(50, 2)
        y = (X[:, 0] > 0).astype(int)
        model.fit(X, y)

        metadata = {"feature_columns": ["a", "b"], "model_type": "LogisticRegression"}
        db = MagicMock()

        with (
            patch.object(service.playground, "load_model", return_value=(model, None, metadata)),
            patch.object(service.artifact_manager, "get_artifact", return_value=mock_artifact),
        ):
            result = service.compute_global_shap(mock_artifact.id, db, max_samples=20)

        assert result["supported"] is True
        assert len(result["feature_importance"]) == 2

    def test_global_shap_unsupported_model(self, service):
        from sklearn.svm import SVC

        model = SVC()
        metadata = {"feature_columns": ["x"]}
        db = MagicMock()

        with patch.object(service.playground, "load_model", return_value=(model, None, metadata)):
            result = service.compute_global_shap(uuid.uuid4(), db)

        assert result["supported"] is False
        assert "not supported" in result["reason"]

    def test_global_shap_caching(self, service, mock_artifact, tmp_path):
        from sklearn.ensemble import RandomForestClassifier

        model = RandomForestClassifier(n_estimators=5, random_state=42)
        X = np.random.randn(50, 3)
        y = (X[:, 0] > 0).astype(int)
        model.fit(X, y)

        metadata = {"feature_columns": ["f1", "f2", "f3"]}
        db = MagicMock()

        with (
            patch.object(service.playground, "load_model", return_value=(model, None, metadata)),
            patch.object(service.artifact_manager, "get_artifact", return_value=mock_artifact),
        ):
            result1 = service.compute_global_shap(mock_artifact.id, db, max_samples=20)
            assert result1["cached"] is False

            result2 = service.compute_global_shap(mock_artifact.id, db, max_samples=20)
            assert result2["cached"] is True
            assert result2["feature_importance"] == result1["feature_importance"]


class TestPredictionShap:
    def test_prediction_shap_tree(self, service):
        from sklearn.ensemble import RandomForestClassifier

        model = RandomForestClassifier(n_estimators=5, random_state=42)
        X = np.random.randn(50, 3)
        y = (X[:, 0] > 0).astype(int)
        model.fit(X, y)

        metadata = {"feature_columns": ["f1", "f2", "f3"]}
        feature_values = {"f1": 1.0, "f2": -0.5, "f3": 0.3}

        result = service.compute_prediction_shap(model, None, feature_values, metadata)

        assert result is not None
        assert "shap_values" in result
        assert "base_value" in result
        assert len(result["shap_values"]) == 3
        assert all(k in result["shap_values"] for k in ("f1", "f2", "f3"))

    def test_prediction_shap_unsupported(self, service):
        from sklearn.svm import SVC

        model = SVC()
        metadata = {"feature_columns": ["x"]}
        result = service.compute_prediction_shap(model, None, {"x": 1.0}, metadata)
        assert result is None

    def test_prediction_shap_with_scaler(self, service):
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler

        X = np.random.randn(50, 2)
        y = (X[:, 0] > 0).astype(int)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        model = RandomForestClassifier(n_estimators=5, random_state=42)
        model.fit(X_scaled, y)

        metadata = {"feature_columns": ["a", "b"]}
        result = service.compute_prediction_shap(model, scaler, {"a": 1.0, "b": -1.0}, metadata)

        assert result is not None
        assert len(result["shap_values"]) == 2


class TestSummaryPlot:
    def test_summary_plot_generated(self, service, tmp_path):
        shap_values = np.random.randn(20, 3)
        feature_names = ["feat_a", "feat_b", "feat_c"]
        plot_path = str(tmp_path / "test_shap_plot.png")

        service._generate_summary_plot(shap_values, feature_names, plot_path)

        assert Path(plot_path).exists()
        assert Path(plot_path).stat().st_size > 0
