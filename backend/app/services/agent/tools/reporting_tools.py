"""
Reporting Tools - Week 11 Implementation

Tools for ReportingAgent to generate reports, summaries, and visualizations.
"""

from datetime import datetime
from typing import Any
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server-side plotting
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


def generate_summary(
    user_goal: str,
    evaluation_results: dict[str, Any],
    model_results: dict[str, Any],
    analysis_results: dict[str, Any],
) -> str:
    """
    Generate a natural language summary of the entire workflow.

    Args:
        user_goal: Original user goal
        evaluation_results: Results from model evaluation
        model_results: Results from model training
        analysis_results: Results from data analysis

    Returns:
        Natural language summary as markdown string
    """
    summary_lines = []
    
    # Header
    summary_lines.append("# Agent Workflow Summary\n")
    summary_lines.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    summary_lines.append(f"**User Goal:** {user_goal}\n")
    
    # Data Analysis Summary
    summary_lines.append("\n## Data Analysis\n")
    if analysis_results:
        # Handle simple dict format from tests
        if "feature_count" in analysis_results:
            summary_lines.append(f"- **Features:** {analysis_results['feature_count']}")
        if "record_count" in analysis_results:
            summary_lines.append(f"- **Records:** {analysis_results['record_count']}")
        if "insights" in analysis_results:
            summary_lines.append(f"- **Insights:** {', '.join(analysis_results['insights'])}")
        
        # Handle production format
        if "exploratory_analysis" in analysis_results:
            eda = analysis_results["exploratory_analysis"]
            if "price_eda" in eda:
                price_eda = eda["price_eda"]
                summary_lines.append(f"- **Records Analyzed:** {price_eda.get('record_count', 'N/A')}")
                summary_lines.append(f"- **Date Range:** {price_eda.get('date_range', 'N/A')}")
                summary_lines.append(f"- **Coins Analyzed:** {', '.join(price_eda.get('coins', []))}")
        
        if "technical_indicators" in analysis_results:
            summary_lines.append("- **Technical Analysis:** Completed")
            indicators = analysis_results["technical_indicators"]
            if isinstance(indicators, dict) and "columns" in indicators:
                summary_lines.append(f"  - Indicators calculated: {len(indicators['columns'])}")
            elif hasattr(indicators, 'columns'):
                summary_lines.append(f"  - Indicators calculated: {len(indicators.columns)}")
            else:
                summary_lines.append(f"  - Indicators calculated: Multiple")
        
        if "sentiment_analysis" in analysis_results:
            sentiment = analysis_results["sentiment_analysis"]
            summary_lines.append(f"- **Sentiment Analysis:** {sentiment.get('overall_sentiment', 'N/A')}")
            summary_lines.append(f"  - Average sentiment score: {sentiment.get('avg_sentiment', 0):.2f}")
    else:
        summary_lines.append("- No analysis results available")
    
    # Model Training Summary
    summary_lines.append("\n## Model Training\n")
    if model_results:
        # Handle simple dict format from tests (dict of model_name: {algorithm: X})
        if isinstance(model_results, dict) and not model_results.get("trained_models"):
            model_count = len(model_results)
            summary_lines.append(f"- **Models Trained:** {model_count}")
            for model_name, model_info in model_results.items():
                algorithm = model_info.get('algorithm', 'Unknown') if isinstance(model_info, dict) else 'Unknown'
                summary_lines.append(f"  - {model_name} ({algorithm})")
        else:
            # Handle production format
            trained_models = model_results.get("trained_models", [])
            summary_lines.append(f"- **Models Trained:** {len(trained_models)}")
            for model in trained_models:
                summary_lines.append(f"  - {model.get('name', 'Unnamed Model')} ({model.get('algorithm', 'Unknown')})")
    else:
        summary_lines.append("- No models trained")
    
    # Model Evaluation Summary
    summary_lines.append("\n## Model Evaluation\n")
    if evaluation_results:
        # Handle simple dict format from tests (dict of model_name: {accuracy: X, f1_score: Y})
        if isinstance(evaluation_results, dict) and not evaluation_results.get("evaluations"):
            if evaluation_results:
                # Find best model by accuracy
                best_model_name = max(evaluation_results, key=lambda x: evaluation_results[x].get("accuracy", 0))
                best_metrics = evaluation_results[best_model_name]
                summary_lines.append(f"- **Best Model:** {best_model_name}")
                summary_lines.append(f"  - Accuracy: {best_metrics.get('accuracy', 0):.4f}")
                if "f1_score" in best_metrics:
                    summary_lines.append(f"  - F1 Score: {best_metrics.get('f1_score', 0):.4f}")
                if "precision" in best_metrics:
                    summary_lines.append(f"  - Precision: {best_metrics.get('precision', 0):.4f}")
                if "recall" in best_metrics:
                    summary_lines.append(f"  - Recall: {best_metrics.get('recall', 0):.4f}")
        else:
            # Handle production format
            evaluations = evaluation_results.get("evaluations", [])
            if evaluations:
                best_model = max(evaluations, key=lambda x: x.get("metrics", {}).get("accuracy", 0))
                summary_lines.append(f"- **Best Model:** {best_model.get('model_name', 'N/A')}")
                metrics = best_model.get("metrics", {})
                summary_lines.append(f"  - Accuracy: {metrics.get('accuracy', 0):.4f}")
                summary_lines.append(f"  - Precision: {metrics.get('precision', 0):.4f}")
                summary_lines.append(f"  - Recall: {metrics.get('recall', 0):.4f}")
                summary_lines.append(f"  - F1 Score: {metrics.get('f1', 0):.4f}")
    else:
        summary_lines.append("- No evaluation results available")
    
    return "\n".join(summary_lines)


def create_comparison_report(
    evaluation_results: dict[str, Any],
    model_results: dict[str, Any],
) -> str:
    """
    Create a detailed comparison report of all trained models.

    Args:
        evaluation_results: Results from model evaluation
        model_results: Results from model training

    Returns:
        Comparison report as markdown string
    """
    report_lines = []
    
    # Header
    report_lines.append("# Model Comparison Report\n")
    report_lines.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
    # Handle simple dict format from tests
    if evaluation_results and "evaluations" not in evaluation_results:
        if len(evaluation_results) == 0:
            report_lines.append("No models to compare.")
            return "\n".join(report_lines)
        
        # Check for single model
        if len(evaluation_results) == 1:
            report_lines.append("\n**Note:** Only one model was trained. Comparison not applicable.\n")
        
        # Create comparison table for test format
        report_lines.append("## Performance Comparison\n")
        report_lines.append("| Model | Algorithm | Accuracy | F1 Score |")
        report_lines.append("|-------|-----------|----------|----------|")
        
        for model_name in evaluation_results:
            metrics = evaluation_results[model_name]
            algorithm = model_results.get(model_name, {}).get('algorithm', 'Unknown') if model_results else 'Unknown'
            accuracy = metrics.get('accuracy', 0)
            f1_score = metrics.get('f1_score', metrics.get('f1', 0))
            report_lines.append(f"| {model_name} | {algorithm} | {accuracy:.4f} | {f1_score:.4f} |")
        
        return "\n".join(report_lines)
    
    # Handle production format
    evaluations = evaluation_results.get("evaluations", [])
    
    if not evaluations:
        report_lines.append("No models to compare.")
        return "\n".join(report_lines)
    
    # Create comparison table
    report_lines.append("## Performance Comparison\n")
    report_lines.append("| Model | Algorithm | Accuracy | Precision | Recall | F1 Score |")
    report_lines.append("|-------|-----------|----------|-----------|--------|----------|")
    
    for eval_result in evaluations:
        model_name = eval_result.get("model_name", "Unknown")
        algorithm = eval_result.get("algorithm", "Unknown")
        metrics = eval_result.get("metrics", {})
        
        report_lines.append(
            f"| {model_name} | {algorithm} | "
            f"{metrics.get('accuracy', 0):.4f} | "
            f"{metrics.get('precision', 0):.4f} | "
            f"{metrics.get('recall', 0):.4f} | "
            f"{metrics.get('f1', 0):.4f} |"
        )
    
    # Best model section
    report_lines.append("\n## Best Model\n")
    best_model = max(evaluations, key=lambda x: x.get("metrics", {}).get("accuracy", 0))
    report_lines.append(f"**Model:** {best_model.get('model_name', 'N/A')}")
    report_lines.append(f"**Algorithm:** {best_model.get('algorithm', 'N/A')}")
    
    metrics = best_model.get("metrics", {})
    report_lines.append("\n**Metrics:**")
    for metric_name, metric_value in metrics.items():
        report_lines.append(f"- {metric_name}: {metric_value:.4f}")
    
    # Feature importance if available
    if "feature_importance" in best_model:
        report_lines.append("\n## Feature Importance (Top 10)\n")
        importance = best_model["feature_importance"]
        sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]
        
        for i, (feature, importance_val) in enumerate(sorted_features, 1):
            report_lines.append(f"{i}. {feature}: {importance_val:.4f}")
    
    return "\n".join(report_lines)


def generate_recommendations(
    user_goal: str,
    evaluation_results: dict[str, Any],
    model_results: dict[str, Any],
    analysis_results: dict[str, Any],
) -> list[str]:
    """
    Generate actionable recommendations based on results.

    Args:
        user_goal: Original user goal
        evaluation_results: Results from model evaluation
        model_results: Results from model training
        analysis_results: Results from data analysis

    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    # Check data quality
    if analysis_results:
        # Handle test format
        if "record_count" in analysis_results:
            record_count = analysis_results["record_count"]
        else:
            # Handle production format
            eda = analysis_results.get("exploratory_analysis", {}).get("price_eda", {})
            record_count = eda.get("record_count", 0)
        
        if record_count and record_count < 100:
            recommendations.append(
                "⚠️  Data Quality: Low sample size detected. Consider collecting more historical data "
                "for better model performance."
            )
        elif record_count and record_count < 1000:
            recommendations.append(
                "💡 Data Quality: Moderate sample size. Model performance could improve with additional data."
            )
        
        # Check for data quality flags in test format
        if "data_quality" in analysis_results:
            recommendations.append("⚠️  Data quality issues detected. Review and clean your data.")
        
        # Check quality_checks for quality_grade
        if "quality_checks" in analysis_results:
            quality_grade = analysis_results["quality_checks"].get("quality_grade")
            if quality_grade == "poor":
                recommendations.append(
                    "⚠️  Data Quality: Poor data quality detected. Consider collecting more data "
                    "or improving data collection processes."
                )
    
    # Check model performance
    if evaluation_results:
        # Handle test format (simple dict)
        if isinstance(evaluation_results, dict) and not evaluation_results.get("evaluations"):
            if evaluation_results:
                # Find best accuracy
                best_accuracy = max((metrics.get("accuracy", 0) for metrics in evaluation_results.values()), default=0)
                
                if best_accuracy < 0.6:
                    recommendations.append(
                        "⚠️  Model Performance: Low accuracy detected. Consider trying different algorithms, "
                        "more data, or feature engineering."
                    )
                elif best_accuracy < 0.75:
                    recommendations.append(
                        "💡 Model Performance: Moderate accuracy. Try hyperparameter tuning to improve performance."
                    )
                else:
                    recommendations.append(
                        "✅ Model Performance: Good accuracy achieved. Consider deploying this model."
                    )
        else:
            # Handle production format
            evaluations = evaluation_results.get("evaluations", [])
            if evaluations:
                best_model = max(evaluations, key=lambda x: x.get("metrics", {}).get("accuracy", 0))
                accuracy = best_model.get("metrics", {}).get("accuracy", 0)
                
                if accuracy < 0.6:
                    recommendations.append(
                        "⚠️  Model Performance: Low accuracy detected. Consider:\n"
                        "  - Feature engineering to create more predictive features\n"
                        "  - Trying different algorithms or ensemble methods\n"
                        "  - Collecting additional data sources (sentiment, on-chain metrics)"
                    )
                elif accuracy < 0.75:
                    recommendations.append(
                        "💡 Model Performance: Moderate accuracy. To improve:\n"
                        "  - Hyperparameter tuning\n"
                        "  - Feature selection to reduce noise\n"
                        "  - Cross-validation to ensure generalization"
                    )
                else:
                    recommendations.append(
                        "✅ Model Performance: Good accuracy achieved. Ready for further testing."
                    )
                
                # Check precision/recall balance
                precision = best_model.get("metrics", {}).get("precision", 0)
                recall = best_model.get("metrics", {}).get("recall", 0)
                
                if abs(precision - recall) > 0.15:
                    recommendations.append(
                        "⚠️  Precision-Recall Imbalance: Consider adjusting classification threshold "
                        "or using different class weights."
                    )
    
    # Check for multiple models (ensemble opportunity)
    if model_results:
        # Handle test format
        if isinstance(model_results, dict) and not model_results.get("trained_models"):
            model_count = len(model_results)
        else:
            # Handle production format
            model_count = len(model_results.get("trained_models", []))
        
        if model_count >= 3:
            recommendations.append(
                "💡 Ensemble Method: Multiple models trained. Consider creating an ensemble "
                "to improve prediction accuracy and robustness."
            )
    
    # Check for missing analysis
    if not analysis_results.get("sentiment_analysis"):
        recommendations.append(
            "💡 Data Enhancement: Sentiment analysis not performed. Consider integrating "
            "news and social media sentiment for improved predictions."
        )
    
    if not analysis_results.get("on_chain_analysis"):
        recommendations.append(
            "💡 Data Enhancement: On-chain analysis not performed. Consider adding blockchain "
            "metrics (active addresses, TVL) for better insights."
        )
    
    # Next steps
    recommendations.append(
        "\n📋 Next Steps:\n"
        "  1. Review model performance on validation data\n"
        "  2. Test algorithm with paper trading\n"
        "  3. Set up monitoring for production deployment\n"
        "  4. Define risk management parameters (position limits, stop-loss)"
    )
    
    return recommendations


def create_visualizations(
    evaluation_results: dict[str, Any],
    model_results: dict[str, Any],
    analysis_results: dict[str, Any],
    output_dir: Path,
) -> list[dict[str, str]]:
    """
    Create visualizations for analysis and model results.

    Args:
        evaluation_results: Results from model evaluation
        model_results: Results from model training
        analysis_results: Results from data analysis
        output_dir: Directory to save plot files

    Returns:
        List of dictionaries with visualization metadata (file_path, title)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    plots = []
    
    # Set style
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (10, 6)
    
    # Initialize evaluations variable for later use
    evaluations = []
    
    # Helper function to create plot metadata
    def create_plot_metadata(plot_path: Path, title: str) -> dict[str, str]:
        """Create standardized plot metadata dictionary."""
        return {
            "file_path": str(plot_path),
            "filename": plot_path.name,
            "title": title,
            "type": "visualization"
        }
    
    # 1. Model Performance Comparison
    # Handle test format (simple dict)
    if evaluation_results and not evaluation_results.get("evaluations"):
        if len(evaluation_results) > 0:
            fig, ax = plt.subplots()
            
            models = list(evaluation_results.keys())
            accuracies = [evaluation_results[m].get("accuracy", 0) for m in models]
            
            ax.bar(models, accuracies)
            ax.set_xlabel('Model')
            ax.set_ylabel('Accuracy')
            ax.set_title('Model Performance Comparison')
            ax.set_ylim([0, 1])
            
            plt.tight_layout()
            plot_path = output_dir / "model_comparison.png"
            plt.savefig(plot_path, dpi=100, bbox_inches='tight')
            plt.close()
            plots.append(create_plot_metadata(plot_path, "Model Performance Comparison"))
    else:
        # Handle production format
        evaluations = evaluation_results.get("evaluations", [])
        if evaluations:
            fig, ax = plt.subplots()
            
            models = [e.get("model_name", "Unknown") for e in evaluations]
            metrics_to_plot = ["accuracy", "precision", "recall", "f1"]
            
            # Prepare data for grouped bar chart
            x = np.arange(len(models))
            width = 0.2
            
            for i, metric in enumerate(metrics_to_plot):
                values = [e.get("metrics", {}).get(metric, 0) for e in evaluations]
                ax.bar(x + i * width, values, width, label=metric.capitalize())
            
            ax.set_xlabel('Model')
            ax.set_ylabel('Score')
            ax.set_title('Model Performance Comparison')
            ax.set_xticks(x + width * 1.5)
            ax.set_xticklabels(models, rotation=45, ha='right')
            ax.legend()
            ax.set_ylim([0, 1])
            
            plt.tight_layout()
            plot_path = output_dir / "model_comparison.png"
            plt.savefig(plot_path, dpi=100, bbox_inches='tight')
            plt.close()
            plots.append(create_plot_metadata(plot_path, "Model Performance Comparison"))
    
    # 2. Feature Importance
    # Handle test format
    if analysis_results and "feature_importance" in analysis_results:
        importance = analysis_results["feature_importance"]
        sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]
        
        features, importance_values = zip(*sorted_features)
        
        fig, ax = plt.subplots()
        ax.barh(range(len(features)), importance_values)
        ax.set_yticks(range(len(features)))
        ax.set_yticklabels(features)
        ax.set_xlabel('Importance')
        ax.set_title('Feature Importance')
        ax.invert_yaxis()
        
        plt.tight_layout()
        plot_path = output_dir / "feature_importance.png"
        plt.savefig(plot_path, dpi=100, bbox_inches='tight')
        plt.close()
        plots.append(create_plot_metadata(plot_path, "Feature Importance"))
    elif evaluation_results.get("evaluations"):
        # Handle production format
        evaluations = evaluation_results.get("evaluations", [])
        if evaluations:
            best_model = max(evaluations, key=lambda x: x.get("metrics", {}).get("accuracy", 0))
            if "feature_importance" in best_model:
                importance = best_model["feature_importance"]
                sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]
                
                features, importance_values = zip(*sorted_features)
                
                fig, ax = plt.subplots()
                ax.barh(range(len(features)), importance_values)
                ax.set_yticks(range(len(features)))
                ax.set_yticklabels(features)
                ax.set_xlabel('Importance')
                ax.set_title('Top 10 Feature Importance')
                ax.invert_yaxis()
                
                plt.tight_layout()
                plot_path = output_dir / "feature_importance.png"
                plt.savefig(plot_path, dpi=100, bbox_inches='tight')
                plt.close()
                plots.append(create_plot_metadata(plot_path, "Feature Importance"))
    
    # 3. Technical Indicators (if available)
    indicators_df = analysis_results.get("technical_indicators")
    if indicators_df is not None and isinstance(indicators_df, pd.DataFrame) and len(indicators_df) > 0:
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        
        # Price and moving averages
        if "timestamp" in indicators_df.columns and "close" in indicators_df.columns:
            ax = axes[0]
            ax.plot(indicators_df["timestamp"], indicators_df["close"], label="Price", linewidth=2)
            
            if "sma_20" in indicators_df.columns:
                ax.plot(indicators_df["timestamp"], indicators_df["sma_20"], 
                       label="SMA 20", alpha=0.7)
            if "ema_20" in indicators_df.columns:
                ax.plot(indicators_df["timestamp"], indicators_df["ema_20"], 
                       label="EMA 20", alpha=0.7)
            
            ax.set_xlabel('Date')
            ax.set_ylabel('Price')
            ax.set_title('Price and Moving Averages')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # RSI
            ax = axes[1]
            if "rsi" in indicators_df.columns:
                ax.plot(indicators_df["timestamp"], indicators_df["rsi"], 
                       label="RSI", color='purple', linewidth=2)
                ax.axhline(y=70, color='r', linestyle='--', alpha=0.5, label='Overbought')
                ax.axhline(y=30, color='g', linestyle='--', alpha=0.5, label='Oversold')
                ax.set_xlabel('Date')
                ax.set_ylabel('RSI')
                ax.set_title('Relative Strength Index (RSI)')
                ax.legend()
                ax.grid(True, alpha=0.3)
                ax.set_ylim([0, 100])
            
            plt.tight_layout()
            plot_path = output_dir / "technical_indicators.png"
            plt.savefig(plot_path, dpi=100, bbox_inches='tight')
            plt.close()
            plots.append(create_plot_metadata(plot_path, "Technical Indicators"))
    
    # 4. Confusion Matrix (if available)
    # Handle test format
    if evaluation_results and not evaluation_results.get("evaluations"):
        # Check if any model has confusion_matrix in test format
        for model_name, metrics in evaluation_results.items():
            if "confusion_matrix" in metrics:
                cm = np.array(metrics["confusion_matrix"])
                
                fig, ax = plt.subplots()
                sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax)
                ax.set_xlabel('Predicted')
                ax.set_ylabel('Actual')
                ax.set_title(f'Confusion Matrix - {model_name}')
                
                plt.tight_layout()
                plot_path = output_dir / f"confusion_matrix_{model_name}.png"
                plt.savefig(plot_path, dpi=100, bbox_inches='tight')
                plt.close()
                plots.append(create_plot_metadata(plot_path, f"Confusion Matrix - {model_name}"))
                break  # Only create one confusion matrix plot
    elif evaluations:
        best_model = max(evaluations, key=lambda x: x.get("metrics", {}).get("accuracy", 0))
        if "confusion_matrix" in best_model:
            cm = np.array(best_model["confusion_matrix"])
            
            fig, ax = plt.subplots()
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax)
            ax.set_xlabel('Predicted')
            ax.set_ylabel('Actual')
            ax.set_title('Confusion Matrix')
            
            plt.tight_layout()
            plot_path = output_dir / "confusion_matrix.png"
            plt.savefig(plot_path, dpi=100, bbox_inches='tight')
            plt.close()
            plots.append(create_plot_metadata(plot_path, "Confusion Matrix"))
    
    return plots
