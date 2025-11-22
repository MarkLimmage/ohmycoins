"""
Reporting Agent - Week 11 Implementation

Agent responsible for generating comprehensive reports and visualizations.
"""

from typing import Any
from pathlib import Path
from datetime import datetime
import uuid

from .base import BaseAgent
from ..tools.reporting_tools import (
    generate_summary,
    create_comparison_report,
    generate_recommendations,
    create_visualizations,
)


class ReportingAgent(BaseAgent):
    """
    Agent responsible for generating reports and visualizations.

    Week 11 Implementation Tools:
    - generate_summary: Create natural language summaries
    - create_comparison_report: Compare multiple model runs
    - generate_recommendations: Generate actionable next steps
    - create_visualizations: Create plots and charts
    """

    def __init__(self, artifacts_dir: str = "/tmp/agent_artifacts") -> None:
        """
        Initialize the reporting agent.

        Args:
            artifacts_dir: Directory to store generated artifacts
        """
        super().__init__(
            name="ReportingAgent",
            description="Generates comprehensive reports and visualizations from workflow results"
        )
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute report generation based on workflow results.

        Args:
            state: Current workflow state with analysis, training, and evaluation results

        Returns:
            Updated state with generated reports and visualizations
        """
        try:
            # Get results from previous agents
            analysis_results = state.get("analysis_results")
            # Support both model_results (new) and trained_models (old) for backward compatibility
            model_results = state.get("model_results") or state.get("trained_models")
            evaluation_results = state.get("evaluation_results")
            user_goal = state.get("user_goal", "")
            session_id = state.get("session_id", str(uuid.uuid4()))
            
            # Check if any result keys are present (even if empty)
            # If none of the keys exist at all, we can't generate a report
            if analysis_results is None and model_results is None and evaluation_results is None:
                raise ValueError("No results available for report generation")
            
            # Default empty dicts for missing results (but at least one key was present)
            analysis_results = analysis_results if analysis_results is not None else {}
            model_results = model_results if model_results is not None else {}
            evaluation_results = evaluation_results if evaluation_results is not None else {}
            
            # Create session-specific artifact directory
            session_artifacts_dir = self.artifacts_dir / session_id
            session_artifacts_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize reporting results
            reporting_results: dict[str, Any] = {
                "summary": "",
                "comparison_report": "",
                "recommendations": [],
                "visualizations": {},
                "artifacts_dir": str(session_artifacts_dir),
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            # 1. Generate natural language summary
            reporting_results["summary"] = generate_summary(
                user_goal=user_goal,
                evaluation_results=evaluation_results,
                model_results=model_results,
                analysis_results=analysis_results,
            )
            
            # Save summary to file
            summary_path = session_artifacts_dir / "summary.md"
            summary_path.write_text(reporting_results["summary"])
            
            # 2. Create model comparison report
            if model_results and evaluation_results:
                reporting_results["comparison_report"] = create_comparison_report(
                    evaluation_results=evaluation_results,
                    model_results=model_results,
                )
                
                # Save comparison report to file
                comparison_path = session_artifacts_dir / "model_comparison.md"
                comparison_path.write_text(reporting_results["comparison_report"])
            
            # 3. Generate recommendations
            reporting_results["recommendations"] = generate_recommendations(
                user_goal=user_goal,
                evaluation_results=evaluation_results,
                model_results=model_results,
                analysis_results=analysis_results,
            )
            
            # Save recommendations to file
            recommendations_path = session_artifacts_dir / "recommendations.md"
            recommendations_text = "# Recommendations\n\n" + "\n\n".join(reporting_results["recommendations"])
            recommendations_path.write_text(recommendations_text)
            
            # 4. Create visualizations
            visualizations = create_visualizations(
                evaluation_results=evaluation_results,
                model_results=model_results,
                analysis_results=analysis_results,
                output_dir=session_artifacts_dir,
            )
            
            # Convert visualizations to dict format for backward compatibility
            # New format is list[dict], old format is dict[str, str]
            if isinstance(visualizations, list):
                reporting_results["visualizations"] = {
                    viz.get("title", viz.get("filename", f"viz_{i}")): viz.get("file_path", "")
                    for i, viz in enumerate(visualizations)
                }
                reporting_results["visualizations_list"] = visualizations  # Keep new format too
            else:
                reporting_results["visualizations"] = visualizations
            
            # 5. Create complete report combining all components
            complete_report = self._create_complete_report(
                summary=reporting_results["summary"],
                comparison_report=reporting_results["comparison_report"],
                recommendations=reporting_results["recommendations"],
                visualizations=visualizations,  # Pass original format to _create_complete_report
            )
            
            # Save complete report
            complete_report_path = session_artifacts_dir / "complete_report.md"
            complete_report_path.write_text(complete_report)
            reporting_results["complete_report_path"] = str(complete_report_path)
            
            # Update state
            state["reporting_results"] = reporting_results
            state["reporting_completed"] = True
            state["report_generated"] = True  # Backward compatibility
            # Add backward compatible field names
            report_data_compat = reporting_results.copy()
            report_data_compat["comparison"] = reporting_results.get("comparison_report")  # Alias
            # Use the list format for visualizations in report_data
            if "visualizations_list" in reporting_results:
                report_data_compat["visualizations"] = reporting_results["visualizations_list"]
            state["report_data"] = report_data_compat  # Backward compatibility
            state["error"] = None
            
            # Add message for user
            if "messages" not in state:
                state["messages"] = []
            state["messages"].append({
                "role": "agent",
                "agent_name": self.name,
                "content": f"Report generation completed. Generated summary, comparison report, "
                          f"{len(reporting_results['recommendations'])} recommendations, and "
                          f"{len(reporting_results['visualizations'])} visualizations.",
                "timestamp": datetime.utcnow().isoformat(),
            })
            
            return state
            
        except Exception as e:
            state["error"] = f"ReportingAgent error: {str(e)}"
            state["reporting_completed"] = False
            state["report_generated"] = False  # Backward compatibility
            state["report_data"] = {}  # Backward compatibility
            
            if "messages" not in state:
                state["messages"] = []
            state["messages"].append({
                "role": "agent",
                "agent_name": self.name,
                "content": f"Error generating report: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            })
            
            return state

    def _create_complete_report(
        self,
        summary: str,
        comparison_report: str,
        recommendations: list[str],
        visualizations: dict[str, str],
    ) -> str:
        """
        Create a complete report combining all components.

        Args:
            summary: Generated summary
            comparison_report: Model comparison report
            recommendations: List of recommendations
            visualizations: Dictionary of visualization paths

        Returns:
            Complete report as markdown string
        """
        report_lines = []
        
        # Title
        report_lines.append("# Oh My Coins - Agentic Workflow Complete Report")
        report_lines.append(f"\n**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        report_lines.append("---\n")
        
        # Summary
        report_lines.append(summary)
        report_lines.append("\n---\n")
        
        # Model Comparison
        if comparison_report:
            report_lines.append(comparison_report)
            report_lines.append("\n---\n")
        
        # Visualizations
        if visualizations:
            report_lines.append("## Visualizations\n")
            # Handle both list format (new) and dict format (old)
            if isinstance(visualizations, list):
                for viz in visualizations:
                    plot_filename = Path(viz["file_path"]).name
                    plot_title = viz.get("title", plot_filename)
                    report_lines.append(f"### {plot_title}\n")
                    report_lines.append(f"![{plot_title}]({plot_filename})\n")
            else:
                # Old dict format for backward compatibility
                for plot_name, plot_path in visualizations.items():
                    plot_filename = Path(plot_path).name
                    report_lines.append(f"### {plot_name.replace('_', ' ').title()}\n")
                    report_lines.append(f"![{plot_name}]({plot_filename})\n")
            report_lines.append("\n---\n")
        
        # Recommendations
        if recommendations:
            report_lines.append("## Recommendations\n")
            for rec in recommendations:
                report_lines.append(rec)
            report_lines.append("\n---\n")
        
        # Footer
        report_lines.append("\n## About This Report\n")
        report_lines.append(
            "This report was automatically generated by the Oh My Coins Agentic Data Science system. "
            "The system analyzed your data, trained machine learning models, evaluated their performance, "
            "and generated this comprehensive report with actionable recommendations.\n"
        )
        report_lines.append("\n**Next Steps:**")
        report_lines.append("1. Review the model performance metrics")
        report_lines.append("2. Examine the recommendations")
        report_lines.append("3. Test the best model with paper trading")
        report_lines.append("4. Deploy to production when satisfied with performance")
        
        return "\n".join(report_lines)
