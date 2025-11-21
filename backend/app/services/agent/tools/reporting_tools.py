"""
Reporting tools for the ReportingAgent.

Week 11 implementation: Tools for generating summaries, comparisons, recommendations, and visualizations.
"""

from typing import Any
import os
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server-side plotting
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime

# Set seaborn style for better-looking plots
sns.set_style("whitegrid")


def generate_summary(
    user_goal: str,
    evaluation_results: dict[str, Any],
    trained_models: dict[str, Any],
    analysis_results: dict[str, Any],
) -> str:
    """
    Generate a natural language summary of the workflow results.
    
    Args:
        user_goal: Original user goal
        evaluation_results: Model evaluation metrics
        trained_models: Trained models information
        analysis_results: Data analysis results
    
    Returns:
        Natural language summary as string
    """
    summary_parts = []
    
    # Add user goal
    summary_parts.append(f"**Goal:** {user_goal}\n")
    
    # Summarize data analysis
    if analysis_results:
        summary_parts.append("\n**Data Analysis:**")
        if "feature_count" in analysis_results:
            summary_parts.append(f"- Analyzed {analysis_results['feature_count']} features")
        if "record_count" in analysis_results:
            summary_parts.append(f"- Processed {analysis_results['record_count']} records")
        if "insights" in analysis_results:
            insights = analysis_results["insights"]
            if isinstance(insights, list):
                for insight in insights[:3]:  # Top 3 insights
                    summary_parts.append(f"- {insight}")
    
    # Summarize trained models
    if trained_models:
        summary_parts.append("\n**Models Trained:**")
        for model_name, model_data in trained_models.items():
            if isinstance(model_data, dict):
                algorithm = model_data.get("algorithm", "Unknown")
                summary_parts.append(f"- {model_name}: {algorithm}")
    
    # Summarize evaluation results
    if evaluation_results:
        summary_parts.append("\n**Performance:**")
        
        # Find best model
        best_model = None
        best_score = -float('inf')
        
        for model_name, metrics in evaluation_results.items():
            if isinstance(metrics, dict):
                # Try to find a primary metric (accuracy, r2_score, etc.)
                score = (
                    metrics.get("accuracy") or 
                    metrics.get("r2_score") or 
                    metrics.get("f1_score") or 
                    0
                )
                if score > best_score:
                    best_score = score
                    best_model = model_name
        
        if best_model:
            summary_parts.append(f"- Best model: {best_model}")
            if best_score > 0:
                summary_parts.append(f"- Best score: {best_score:.4f}")
        
        # Add metrics for best model
        if best_model and best_model in evaluation_results:
            metrics = evaluation_results[best_model]
            if isinstance(metrics, dict):
                for metric_name, metric_value in metrics.items():
                    if isinstance(metric_value, (int, float)):
                        summary_parts.append(f"  - {metric_name}: {metric_value:.4f}")
    
    return "\n".join(summary_parts)


def create_comparison_report(
    evaluation_results: dict[str, Any],
    trained_models: dict[str, Any],
) -> str:
    """
    Create a comparison report for multiple models.
    
    Args:
        evaluation_results: Model evaluation metrics
        trained_models: Trained models information
    
    Returns:
        Comparison report as string
    """
    if not evaluation_results or len(evaluation_results) < 2:
        return "Only one model trained, comparison not applicable."
    
    report_parts = []
    
    # Create a comparison table
    report_parts.append("| Model | Algorithm | Primary Metric | Score |")
    report_parts.append("|-------|-----------|----------------|-------|")
    
    for model_name, metrics in evaluation_results.items():
        if isinstance(metrics, dict):
            algorithm = "Unknown"
            if model_name in trained_models:
                model_data = trained_models[model_name]
                if isinstance(model_data, dict):
                    algorithm = model_data.get("algorithm", "Unknown")
            
            # Get primary metric
            primary_metric = "accuracy" if "accuracy" in metrics else list(metrics.keys())[0] if metrics else "N/A"
            score = metrics.get(primary_metric, 0) if isinstance(metrics, dict) else 0
            
            report_parts.append(f"| {model_name} | {algorithm} | {primary_metric} | {score:.4f} |")
    
    return "\n".join(report_parts)


def generate_recommendations(
    user_goal: str,
    evaluation_results: dict[str, Any],
    trained_models: dict[str, Any],
    state: dict[str, Any],
) -> list[str]:
    """
    Generate actionable recommendations based on results.
    
    Args:
        user_goal: Original user goal
        evaluation_results: Model evaluation metrics
        trained_models: Trained models information
        state: Current workflow state
    
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    # Check if model performance is good
    if evaluation_results:
        best_score = 0.0
        for metrics in evaluation_results.values():
            if isinstance(metrics, dict):
                score = (
                    metrics.get("accuracy") or 
                    metrics.get("r2_score") or 
                    metrics.get("f1_score") or 
                    0
                )
                best_score = max(best_score, score)
        
        if best_score < 0.6:
            recommendations.append(
                "Model performance is below 60%. Consider collecting more data or trying different features."
            )
        elif best_score < 0.8:
            recommendations.append(
                "Model performance is moderate. Consider hyperparameter tuning or feature engineering."
            )
        else:
            recommendations.append(
                "Model performance is good! Consider deploying this model to production."
            )
    
    # Check data quality
    quality_checks = state.get("quality_checks", {})
    if quality_checks:
        quality_grade = quality_checks.get("quality_grade", "unknown")
        if quality_grade in ["poor", "no_data"]:
            recommendations.append(
                "Data quality is poor. Collect more data or improve data collection process."
            )
        elif quality_grade == "fair":
            recommendations.append(
                "Data quality is fair. Additional data might improve model performance."
            )
    
    # Check if multiple models were trained
    if trained_models and len(trained_models) > 1:
        recommendations.append(
            "Multiple models were trained. Consider ensemble methods to combine their predictions."
        )
    
    # Check for errors
    if state.get("error"):
        recommendations.append(
            "Errors occurred during the workflow. Review error messages and fix data quality issues."
        )
    
    # General recommendation
    if not recommendations:
        recommendations.append(
            "Continue monitoring model performance and retrain periodically with new data."
        )
    
    return recommendations


def create_visualizations(
    evaluation_results: dict[str, Any],
    trained_models: dict[str, Any],
    analysis_results: dict[str, Any],
    output_dir: str = "/tmp/agent_artifacts",
) -> list[dict[str, Any]]:
    """
    Create visualizations for the report.
    
    Args:
        evaluation_results: Model evaluation metrics
        trained_models: Trained models information
        analysis_results: Data analysis results
        output_dir: Directory to save visualizations
    
    Returns:
        List of visualization metadata dictionaries
    """
    visualizations = []
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Model Performance Comparison
    if evaluation_results and len(evaluation_results) > 0:
        try:
            viz = _create_performance_comparison(
                evaluation_results, output_dir, timestamp
            )
            if viz:
                visualizations.append(viz)
        except Exception as e:
            print(f"Error creating performance comparison: {e}")
    
    # 2. Feature Importance (if available)
    if analysis_results and "feature_importance" in analysis_results:
        try:
            viz = _create_feature_importance_plot(
                analysis_results["feature_importance"], output_dir, timestamp
            )
            if viz:
                visualizations.append(viz)
        except Exception as e:
            print(f"Error creating feature importance plot: {e}")
    
    # 3. Confusion Matrix (if available)
    for model_name, metrics in evaluation_results.items():
        if isinstance(metrics, dict) and "confusion_matrix" in metrics:
            try:
                viz = _create_confusion_matrix(
                    metrics["confusion_matrix"], model_name, output_dir, timestamp
                )
                if viz:
                    visualizations.append(viz)
            except Exception as e:
                print(f"Error creating confusion matrix for {model_name}: {e}")
    
    return visualizations


def _create_performance_comparison(
    evaluation_results: dict[str, Any],
    output_dir: str,
    timestamp: str,
) -> dict[str, Any] | None:
    """Create a bar chart comparing model performance."""
    try:
        # Extract metrics for comparison
        models = []
        scores = []
        
        for model_name, metrics in evaluation_results.items():
            if isinstance(metrics, dict):
                # Get primary metric
                score = (
                    metrics.get("accuracy") or 
                    metrics.get("r2_score") or 
                    metrics.get("f1_score") or 
                    0
                )
                models.append(model_name)
                scores.append(score)
        
        if not models:
            return None
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(models, scores, color=sns.color_palette("husl", len(models)))
        
        # Customize plot
        ax.set_xlabel("Model", fontsize=12, fontweight='bold')
        ax.set_ylabel("Score", fontsize=12, fontweight='bold')
        ax.set_title("Model Performance Comparison", fontsize=14, fontweight='bold')
        ax.set_ylim(0, 1.0)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height,
                f'{height:.3f}',
                ha='center',
                va='bottom',
                fontsize=10
            )
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save plot
        filename = f"performance_comparison_{timestamp}.png"
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        return {
            "title": "Model Performance Comparison",
            "file_path": filepath,
            "filename": filename,
            "type": "bar_chart",
        }
    
    except Exception as e:
        print(f"Error in _create_performance_comparison: {e}")
        return None


def _create_feature_importance_plot(
    feature_importance: dict[str, float],
    output_dir: str,
    timestamp: str,
) -> dict[str, Any] | None:
    """Create a horizontal bar chart of feature importance."""
    try:
        if not feature_importance:
            return None
        
        # Sort by importance
        sorted_features = sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Take top 15 features
        top_features = sorted_features[:15]
        features = [f[0] for f in top_features]
        importance = [f[1] for f in top_features]
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 8))
        bars = ax.barh(features, importance, color=sns.color_palette("viridis", len(features)))
        
        # Customize plot
        ax.set_xlabel("Importance", fontsize=12, fontweight='bold')
        ax.set_ylabel("Feature", fontsize=12, fontweight='bold')
        ax.set_title("Top 15 Feature Importance", fontsize=14, fontweight='bold')
        
        # Reverse y-axis so highest importance is at top
        ax.invert_yaxis()
        
        plt.tight_layout()
        
        # Save plot
        filename = f"feature_importance_{timestamp}.png"
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        return {
            "title": "Feature Importance",
            "file_path": filepath,
            "filename": filename,
            "type": "bar_chart",
        }
    
    except Exception as e:
        print(f"Error in _create_feature_importance_plot: {e}")
        return None


def _create_confusion_matrix(
    confusion_matrix: list[list[int]] | Any,
    model_name: str,
    output_dir: str,
    timestamp: str,
) -> dict[str, Any] | None:
    """Create a heatmap visualization of confusion matrix."""
    try:
        # Convert to numpy array if needed
        if isinstance(confusion_matrix, list):
            cm = np.array(confusion_matrix)
        else:
            cm = confusion_matrix
        
        # Create plot
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(
            cm,
            annot=True,
            fmt='d',
            cmap='Blues',
            ax=ax,
            cbar_kws={'label': 'Count'}
        )
        
        # Customize plot
        ax.set_xlabel("Predicted Label", fontsize=12, fontweight='bold')
        ax.set_ylabel("True Label", fontsize=12, fontweight='bold')
        ax.set_title(f"Confusion Matrix - {model_name}", fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        # Save plot
        filename = f"confusion_matrix_{model_name}_{timestamp}.png"
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        return {
            "title": f"Confusion Matrix - {model_name}",
            "file_path": filepath,
            "filename": filename,
            "type": "heatmap",
        }
    
    except Exception as e:
        print(f"Error in _create_confusion_matrix: {e}")
        return None
