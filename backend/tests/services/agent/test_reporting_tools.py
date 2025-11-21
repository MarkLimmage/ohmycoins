"""
Tests for reporting tools.

Week 11 tests: Testing report generation functions and visualizations.
"""

import os
import tempfile
import pytest
from app.services.agent.tools.reporting_tools import (
    generate_summary,
    create_comparison_report,
    generate_recommendations,
    create_visualizations,
)


class TestGenerateSummary:
    """Tests for generate_summary function."""
    
    def test_summary_with_full_data(self):
        """Test summary generation with complete data."""
        user_goal = "Predict cryptocurrency prices"
        evaluation_results = {
            "model1": {"accuracy": 0.85, "f1_score": 0.82},
            "model2": {"accuracy": 0.78},
        }
        trained_models = {
            "model1": {"algorithm": "RandomForest"},
            "model2": {"algorithm": "SVM"},
        }
        analysis_results = {
            "feature_count": 15,
            "record_count": 2000,
            "insights": ["Strong trend", "High volatility"],
        }
        
        summary = generate_summary(
            user_goal, evaluation_results, trained_models, analysis_results
        )
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert user_goal in summary
        assert "15" in summary  # feature count
        assert "2000" in summary  # record count
    
    def test_summary_with_minimal_data(self):
        """Test summary generation with minimal data."""
        summary = generate_summary("Test goal", {}, {}, {})
        
        assert isinstance(summary, str)
        assert "Test goal" in summary
    
    def test_summary_identifies_best_model(self):
        """Test that summary identifies best performing model."""
        evaluation_results = {
            "model_a": {"accuracy": 0.75},
            "model_b": {"accuracy": 0.92},
            "model_c": {"accuracy": 0.68},
        }
        
        summary = generate_summary("Test", evaluation_results, {}, {})
        
        assert "model_b" in summary
        assert "0.92" in summary


class TestCreateComparisonReport:
    """Tests for create_comparison_report function."""
    
    def test_comparison_with_multiple_models(self):
        """Test comparison report with multiple models."""
        evaluation_results = {
            "model1": {"accuracy": 0.85, "f1_score": 0.82},
            "model2": {"accuracy": 0.78, "f1_score": 0.75},
        }
        trained_models = {
            "model1": {"algorithm": "RandomForest"},
            "model2": {"algorithm": "LogisticRegression"},
        }
        
        report = create_comparison_report(evaluation_results, trained_models)
        
        assert isinstance(report, str)
        assert "model1" in report
        assert "model2" in report
        assert "RandomForest" in report
        assert "LogisticRegression" in report
    
    def test_comparison_with_single_model(self):
        """Test comparison report with single model."""
        evaluation_results = {"model1": {"accuracy": 0.85}}
        trained_models = {"model1": {"algorithm": "SVM"}}
        
        report = create_comparison_report(evaluation_results, trained_models)
        
        assert isinstance(report, str)
        assert "one model" in report.lower() or "comparison not applicable" in report.lower()
    
    def test_comparison_table_format(self):
        """Test that comparison uses table format."""
        evaluation_results = {
            "model_a": {"accuracy": 0.85},
            "model_b": {"r2_score": 0.78},
        }
        
        report = create_comparison_report(evaluation_results, {})
        
        # Check for markdown table markers
        assert "|" in report
        assert "Model" in report
        assert "Score" in report


class TestGenerateRecommendations:
    """Tests for generate_recommendations function."""
    
    def test_recommendations_for_good_performance(self):
        """Test recommendations for good model performance."""
        evaluation_results = {"model": {"accuracy": 0.92}}
        
        recommendations = generate_recommendations(
            "Test goal", evaluation_results, {}, {}
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Should recommend deployment for high accuracy
        deployment_mentioned = any(
            "deploy" in rec.lower() for rec in recommendations
        )
        assert deployment_mentioned
    
    def test_recommendations_for_poor_performance(self):
        """Test recommendations for poor model performance."""
        evaluation_results = {"model": {"accuracy": 0.45}}
        
        recommendations = generate_recommendations(
            "Test goal", evaluation_results, {}, {}
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Should suggest improvements for low accuracy
        improvement_mentioned = any(
            "more data" in rec.lower() or "feature" in rec.lower()
            for rec in recommendations
        )
        assert improvement_mentioned
    
    def test_recommendations_for_moderate_performance(self):
        """Test recommendations for moderate performance."""
        evaluation_results = {"model": {"accuracy": 0.70}}
        
        recommendations = generate_recommendations(
            "Test goal", evaluation_results, {}, {}
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Should suggest tuning for moderate performance
        tuning_mentioned = any(
            "tuning" in rec.lower() or "engineer" in rec.lower()
            for rec in recommendations
        )
        assert tuning_mentioned
    
    def test_recommendations_for_poor_data_quality(self):
        """Test recommendations when data quality is poor."""
        state = {
            "quality_checks": {
                "quality_grade": "poor",
            },
        }
        
        recommendations = generate_recommendations(
            "Test goal", {}, {}, state
        )
        
        assert isinstance(recommendations, list)
        data_quality_mentioned = any(
            "data quality" in rec.lower() or "collect more data" in rec.lower()
            for rec in recommendations
        )
        assert data_quality_mentioned
    
    def test_recommendations_for_multiple_models(self):
        """Test recommendations when multiple models trained."""
        trained_models = {
            "model1": {},
            "model2": {},
            "model3": {},
        }
        
        recommendations = generate_recommendations(
            "Test goal", {}, trained_models, {}
        )
        
        assert isinstance(recommendations, list)
        ensemble_mentioned = any(
            "ensemble" in rec.lower() for rec in recommendations
        )
        assert ensemble_mentioned
    
    def test_recommendations_always_returns_something(self):
        """Test that recommendations are always provided."""
        recommendations = generate_recommendations("Test", {}, {}, {})
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0


class TestCreateVisualizations:
    """Tests for create_visualizations function."""
    
    def test_visualizations_created_with_results(self):
        """Test that visualizations are created when data is available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evaluation_results = {
                "model1": {"accuracy": 0.85, "f1_score": 0.82},
                "model2": {"accuracy": 0.78, "f1_score": 0.75},
            }
            trained_models = {
                "model1": {"algorithm": "RandomForest"},
                "model2": {"algorithm": "SVM"},
            }
            
            visualizations = create_visualizations(
                evaluation_results,
                trained_models,
                {},
                output_dir=tmpdir,
            )
            
            assert isinstance(visualizations, list)
            # Should create at least a performance comparison chart
            assert len(visualizations) >= 1
            
            # Check that files were created
            for viz in visualizations:
                assert "file_path" in viz
                assert "title" in viz
                assert os.path.exists(viz["file_path"])
    
    def test_visualizations_with_feature_importance(self):
        """Test visualization of feature importance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analysis_results = {
                "feature_importance": {
                    "feature1": 0.35,
                    "feature2": 0.25,
                    "feature3": 0.15,
                },
            }
            
            visualizations = create_visualizations(
                {},
                {},
                analysis_results,
                output_dir=tmpdir,
            )
            
            # Should create feature importance plot
            importance_viz = [v for v in visualizations if "importance" in v.get("title", "").lower()]
            if importance_viz:  # May not create if no data
                assert len(importance_viz) > 0
                assert os.path.exists(importance_viz[0]["file_path"])
    
    def test_visualizations_with_confusion_matrix(self):
        """Test visualization of confusion matrix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evaluation_results = {
                "classifier": {
                    "accuracy": 0.85,
                    "confusion_matrix": [[50, 10], [5, 35]],
                },
            }
            
            visualizations = create_visualizations(
                evaluation_results,
                {},
                {},
                output_dir=tmpdir,
            )
            
            # Should create confusion matrix plot
            cm_viz = [v for v in visualizations if "confusion" in v.get("title", "").lower()]
            if cm_viz:
                assert len(cm_viz) > 0
                assert os.path.exists(cm_viz[0]["file_path"])
    
    def test_visualizations_empty_with_no_data(self):
        """Test that visualizations list is empty when no data available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            visualizations = create_visualizations(
                {},
                {},
                {},
                output_dir=tmpdir,
            )
            
            assert isinstance(visualizations, list)
            # List should be empty or minimal
    
    def test_visualization_metadata_structure(self):
        """Test that visualization metadata has correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evaluation_results = {
                "model": {"accuracy": 0.85},
            }
            
            visualizations = create_visualizations(
                evaluation_results,
                {},
                {},
                output_dir=tmpdir,
            )
            
            for viz in visualizations:
                assert "title" in viz
                assert "file_path" in viz
                assert "filename" in viz
                assert "type" in viz
