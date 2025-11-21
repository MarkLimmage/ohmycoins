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
    analysis_results: dict[str, Any],
    model_results: dict[str, Any],
    evaluation_results: dict[str, Any],
    user_goal: str,
) -> str:
    """
    Generate a natural language summary of the entire workflow.

    Args:
        analysis_results: Results from data analysis
        model_results: Results from model training
        evaluation_results: Results from model evaluation
        user_goal: Original user goal

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
            summary_lines.append(f"  - Indicators calculated: {len(indicators.columns) if hasattr(indicators, 'columns') else 'Multiple'}")
        
        if "sentiment_analysis" in analysis_results:
            sentiment = analysis_results["sentiment_analysis"]
            summary_lines.append(f"- **Sentiment Analysis:** {sentiment.get('overall_sentiment', 'N/A')}")
            summary_lines.append(f"  - Average sentiment score: {sentiment.get('avg_sentiment', 0):.2f}")
    else:
        summary_lines.append("- No analysis results available")
    
    # Model Training Summary
    summary_lines.append("\n## Model Training\n")
    if model_results:
        trained_models = model_results.get("trained_models", [])
        summary_lines.append(f"- **Models Trained:** {len(trained_models)}")
        for model in trained_models:
            summary_lines.append(f"  - {model.get('name', 'Unnamed Model')} ({model.get('algorithm', 'Unknown')})")
    else:
        summary_lines.append("- No models trained")
    
    # Model Evaluation Summary
    summary_lines.append("\n## Model Evaluation\n")
    if evaluation_results:
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
    model_results: dict[str, Any],
    evaluation_results: dict[str, Any],
) -> str:
    """
    Create a detailed comparison report of all trained models.

    Args:
        model_results: Results from model training
        evaluation_results: Results from model evaluation

    Returns:
        Comparison report as markdown string
    """
    report_lines = []
    
    # Header
    report_lines.append("# Model Comparison Report\n")
    report_lines.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
    # Get evaluations
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
    analysis_results: dict[str, Any],
    model_results: dict[str, Any],
    evaluation_results: dict[str, Any],
) -> list[str]:
    """
    Generate actionable recommendations based on results.

    Args:
        analysis_results: Results from data analysis
        model_results: Results from model training
        evaluation_results: Results from model evaluation

    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    # Check data quality
    if analysis_results:
        eda = analysis_results.get("exploratory_analysis", {}).get("price_eda", {})
        record_count = eda.get("record_count", 0)
        
        if record_count < 100:
            recommendations.append(
                "⚠️  Data Quality: Low sample size detected. Consider collecting more historical data "
                "for better model performance."
            )
        elif record_count < 1000:
            recommendations.append(
                "💡 Data Quality: Moderate sample size. Model performance could improve with additional data."
            )
    
    # Check model performance
    if evaluation_results:
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
    analysis_results: dict[str, Any],
    evaluation_results: dict[str, Any],
    output_dir: Path,
) -> dict[str, str]:
    """
    Create visualizations for analysis and model results.

    Args:
        analysis_results: Results from data analysis
        evaluation_results: Results from model evaluation
        output_dir: Directory to save plot files

    Returns:
        Dictionary mapping plot names to file paths
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    plots = {}
    
    # Set style
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (10, 6)
    
    # 1. Model Performance Comparison
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
        plots["model_comparison"] = str(plot_path)
    
    # 2. Feature Importance
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
            plots["feature_importance"] = str(plot_path)
    
    # 3. Technical Indicators (if available)
    if analysis_results.get("technical_indicators") is not None:
        indicators_df = analysis_results["technical_indicators"]
        if isinstance(indicators_df, pd.DataFrame) and len(indicators_df) > 0:
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
                plots["technical_indicators"] = str(plot_path)
    
    # 4. Confusion Matrix (if available)
    if evaluations:
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
            plots["confusion_matrix"] = str(plot_path)
    
    return plots
