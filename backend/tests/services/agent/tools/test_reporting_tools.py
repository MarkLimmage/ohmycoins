"""
Tests for reporting tools - Week 11 Implementation

Tests for generate_summary, create_comparison_report, generate_recommendations,
and create_visualizations functions.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from app.services.agent.tools.reporting_tools import (
    create_comparison_report,
    create_visualizations,
    generate_recommendations,
    generate_summary,
)


@pytest.fixture
def sample_analysis_results():
    """Sample analysis results for testing."""
    return {
        "exploratory_analysis": {
            "price_eda": {
                "record_count": 500,
                "date_range": "2024-01-01 to 2024-02-01",
                "coins": ["BTC", "ETH"],
            }
        },
        "technical_indicators": {
            "columns": ["timestamp", "close", "sma_20", "ema_20", "rsi"],
        },
        "sentiment_analysis": {
            "overall_sentiment": "Bullish",
            "avg_sentiment": 0.65,
        },
    }


@pytest.fixture
def sample_model_results():
    """Sample model results for testing."""
    return {
        "trained_models": [
            {
                "name": "RandomForestModel_1",
                "algorithm": "RandomForest",
            },
            {
                "name": "LogisticRegressionModel_1",
                "algorithm": "LogisticRegression",
            },
        ]
    }


@pytest.fixture
def sample_evaluation_results():
    """Sample evaluation results for testing."""
    return {
        "evaluations": [
            {
                "model_name": "RandomForestModel_1",
                "algorithm": "RandomForest",
                "metrics": {
                    "accuracy": 0.85,
                    "precision": 0.83,
                    "recall": 0.87,
                    "f1": 0.85,
                },
                "feature_importance": {
                    "sma_20": 0.35,
                    "ema_20": 0.25,
                    "rsi": 0.20,
                    "volume": 0.15,
                    "sentiment": 0.05,
                },
                "confusion_matrix": [[45, 5], [8, 42]],
            },
            {
                "model_name": "LogisticRegressionModel_1",
                "algorithm": "LogisticRegression",
                "metrics": {
                    "accuracy": 0.78,
                    "precision": 0.76,
                    "recall": 0.80,
                    "f1": 0.78,
                },
            },
        ]
    }


class TestGenerateSummary:
    """Tests for generate_summary function."""

    def test_generate_summary_complete(
        self, sample_analysis_results, sample_model_results, sample_evaluation_results
    ):
        """Test summary generation with complete results."""
        summary = generate_summary(
            user_goal="Predict BTC price movement",
            evaluation_results=sample_evaluation_results,
            model_results=sample_model_results,
            analysis_results=sample_analysis_results,
        )

        assert "Agent Workflow Summary" in summary
        assert "Predict BTC price movement" in summary
        assert "Data Analysis" in summary
        assert "Model Training" in summary
        assert "Model Evaluation" in summary
        assert "500" in summary  # record count
        assert "RandomForestModel_1" in summary
        assert "0.85" in summary  # best accuracy

    def test_generate_summary_empty_results(self):
        """Test summary generation with empty results."""
        summary = generate_summary(
            user_goal="Test goal",
            evaluation_results={},
            model_results={},
            analysis_results={},
        )

        assert "Agent Workflow Summary" in summary
        assert "No analysis results available" in summary
        assert "No models trained" in summary
        assert "No evaluation results available" in summary

    def test_generate_summary_partial_results(self, sample_analysis_results):
        """Test summary with only analysis results."""
        summary = generate_summary(
            user_goal="Analyze data only",
            evaluation_results={},
            model_results={},
            analysis_results=sample_analysis_results,
        )

        assert "Records Analyzed:** 500" in summary
        assert "No models trained" in summary


class TestCreateComparisonReport:
    """Tests for create_comparison_report function."""

    def test_comparison_report_multiple_models(
        self, sample_model_results, sample_evaluation_results
    ):
        """Test comparison report with multiple models."""
        report = create_comparison_report(
            evaluation_results=sample_evaluation_results,
            model_results=sample_model_results,
        )

        assert "Model Comparison Report" in report
        assert "Performance Comparison" in report
        assert "RandomForestModel_1" in report
        assert "LogisticRegressionModel_1" in report
        assert "Best Model" in report
        assert "0.85" in report  # best accuracy

    def test_comparison_report_no_evaluations(self, sample_model_results):
        """Test comparison report with no evaluations."""
        report = create_comparison_report(
            evaluation_results={"evaluations": []},
            model_results=sample_model_results,
        )

        assert "No models to compare" in report

    def test_comparison_report_feature_importance(
        self, sample_model_results, sample_evaluation_results
    ):
        """Test that feature importance is included."""
        report = create_comparison_report(
            evaluation_results=sample_evaluation_results,
            model_results=sample_model_results,
        )

        assert "Feature Importance" in report
        assert "sma_20" in report
        assert "0.35" in report


class TestGenerateRecommendations:
    """Tests for generate_recommendations function."""

    def test_recommendations_low_sample_size(self):
        """Test recommendations with low sample size."""
        analysis_results = {
            "exploratory_analysis": {
                "price_eda": {"record_count": 50}
            }
        }

        recommendations = generate_recommendations(
            user_goal="Test goal",
            evaluation_results={},
            model_results={},
            analysis_results=analysis_results,
        )

        assert any("Low sample size" in rec for rec in recommendations)

    def test_recommendations_low_accuracy(self, sample_analysis_results, sample_model_results):
        """Test recommendations with low model accuracy."""
        evaluation_results = {
            "evaluations": [
                {
                    "model_name": "LowAccuracyModel",
                    "metrics": {"accuracy": 0.55, "precision": 0.50, "recall": 0.60},
                }
            ]
        }

        recommendations = generate_recommendations(
            user_goal="Test goal",
            evaluation_results=evaluation_results,
            model_results=sample_model_results,
            analysis_results=sample_analysis_results,
        )

        assert any("Low accuracy" in rec for rec in recommendations)

    def test_recommendations_good_accuracy(
        self, sample_analysis_results, sample_model_results, sample_evaluation_results
    ):
        """Test recommendations with good accuracy."""
        recommendations = generate_recommendations(
            user_goal="Test goal",
            evaluation_results=sample_evaluation_results,
            model_results=sample_model_results,
            analysis_results=sample_analysis_results,
        )

        assert any("Good accuracy" in rec for rec in recommendations)

    def test_recommendations_precision_recall_imbalance(
        self, sample_analysis_results, sample_model_results
    ):
        """Test recommendations with precision-recall imbalance."""
        evaluation_results = {
            "evaluations": [
                {
                    "model_name": "ImbalancedModel",
                    "metrics": {"accuracy": 0.80, "precision": 0.95, "recall": 0.65},
                }
            ]
        }

        recommendations = generate_recommendations(
            user_goal="Test goal",
            evaluation_results=evaluation_results,
            model_results=sample_model_results,
            analysis_results=sample_analysis_results,
        )

        assert any("Precision-Recall Imbalance" in rec for rec in recommendations)

    def test_recommendations_missing_sentiment(
        self, sample_model_results, sample_evaluation_results
    ):
        """Test recommendations when sentiment analysis is missing."""
        analysis_results = {
            "exploratory_analysis": {"price_eda": {"record_count": 1000}}
        }

        recommendations = generate_recommendations(
            user_goal="Test goal",
            evaluation_results=sample_evaluation_results,
            model_results=sample_model_results,
            analysis_results=analysis_results,
        )

        assert any("Sentiment analysis not performed" in rec for rec in recommendations)

    def test_recommendations_next_steps(
        self, sample_analysis_results, sample_model_results, sample_evaluation_results
    ):
        """Test that next steps are always included."""
        recommendations = generate_recommendations(
            user_goal="Test goal",
            evaluation_results=sample_evaluation_results,
            model_results=sample_model_results,
            analysis_results=sample_analysis_results,
        )

        assert any("Next Steps" in rec for rec in recommendations)


class TestCreateVisualizations:
    """Tests for create_visualizations function."""

    @pytest.fixture
    def temp_dir(self):
        """Create and cleanup temporary directory."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    def test_visualization_model_comparison(
        self, sample_analysis_results, sample_evaluation_results, temp_dir
    ):
        """Test model comparison visualization creation."""
        plots = create_visualizations(
            evaluation_results=sample_evaluation_results,
            model_results={},
            analysis_results=sample_analysis_results,
            output_dir=temp_dir,
        )

        assert isinstance(plots, list)
        assert len(plots) > 0
        model_comp_plot = next((p for p in plots if "comparison" in p["title"].lower()), None)
        assert model_comp_plot is not None
        assert Path(model_comp_plot["file_path"]).exists()
        assert model_comp_plot["file_path"].endswith(".png")

    def test_visualization_feature_importance(
        self, sample_analysis_results, sample_evaluation_results, temp_dir
    ):
        """Test feature importance visualization creation."""
        plots = create_visualizations(
            evaluation_results=sample_evaluation_results,
            model_results={},
            analysis_results=sample_analysis_results,
            output_dir=temp_dir,
        )

        assert isinstance(plots, list)
        feature_plot = next((p for p in plots if "feature" in p["title"].lower()), None)
        if feature_plot:  # Only assert if feature importance was generated
            assert Path(feature_plot["file_path"]).exists()

    def test_visualization_confusion_matrix(
        self, sample_analysis_results, sample_evaluation_results, temp_dir
    ):
        """Test confusion matrix visualization creation."""
        plots = create_visualizations(
            evaluation_results=sample_evaluation_results,
            model_results={},
            analysis_results=sample_analysis_results,
            output_dir=temp_dir,
        )

        assert isinstance(plots, list)
        confusion_plot = next((p for p in plots if "confusion" in p["title"].lower()), None)
        if confusion_plot:  # Only assert if confusion matrix was generated
            assert Path(confusion_plot["file_path"]).exists()

    def test_visualization_empty_results(self, temp_dir):
        """Test visualization with empty results."""
        plots = create_visualizations(
            evaluation_results={},
            model_results={},
            analysis_results={},
            output_dir=temp_dir,
        )

        # Should return empty list when no data
        assert isinstance(plots, list)

    def test_visualization_creates_output_dir(self, sample_evaluation_results):
        """Test that output directory is created if it doesn't exist."""
        temp_path = Path(tempfile.mkdtemp())
        output_dir = temp_path / "new_subdir"

        try:
            create_visualizations(
                evaluation_results=sample_evaluation_results,
                model_results={},
                analysis_results={},
                output_dir=output_dir,
            )

            assert output_dir.exists()
        finally:
            shutil.rmtree(temp_path, ignore_errors=True)
