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
            analysis_results = state.get("analysis_results", {})
            model_results = state.get("model_results", {})
            evaluation_results = state.get("evaluation_results", {})
            user_goal = state.get("user_goal", "")
            session_id = state.get("session_id", str(uuid.uuid4()))
            
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
                analysis_results=analysis_results,
                model_results=model_results,
                evaluation_results=evaluation_results,
                user_goal=user_goal,
            )
            
            # Save summary to file
            summary_path = session_artifacts_dir / "summary.md"
            summary_path.write_text(reporting_results["summary"])
            
            # 2. Create model comparison report
            if model_results and evaluation_results:
                reporting_results["comparison_report"] = create_comparison_report(
                    model_results=model_results,
                    evaluation_results=evaluation_results,
                )
                
                # Save comparison report to file
                comparison_path = session_artifacts_dir / "model_comparison.md"
                comparison_path.write_text(reporting_results["comparison_report"])
            
            # 3. Generate recommendations
            reporting_results["recommendations"] = generate_recommendations(
                analysis_results=analysis_results,
                model_results=model_results,
                evaluation_results=evaluation_results,
            )
            
            # Save recommendations to file
            recommendations_path = session_artifacts_dir / "recommendations.md"
            recommendations_text = "# Recommendations\n\n" + "\n\n".join(reporting_results["recommendations"])
            recommendations_path.write_text(recommendations_text)
            
            # 4. Create visualizations
            reporting_results["visualizations"] = create_visualizations(
                analysis_results=analysis_results,
                evaluation_results=evaluation_results,
                output_dir=session_artifacts_dir,
            )
            
            # 5. Create complete report combining all components
            complete_report = self._create_complete_report(
                summary=reporting_results["summary"],
                comparison_report=reporting_results["comparison_report"],
                recommendations=reporting_results["recommendations"],
                visualizations=reporting_results["visualizations"],
            )
            
            # Save complete report
            complete_report_path = session_artifacts_dir / "complete_report.md"
            complete_report_path.write_text(complete_report)
            reporting_results["complete_report_path"] = str(complete_report_path)
            
            # Update state
            state["reporting_results"] = reporting_results
            state["reporting_completed"] = True
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
            for plot_name, plot_path in visualizations.items():
                # Create relative path for markdown
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
