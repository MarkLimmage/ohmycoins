"""
Reporting Agent - Generates comprehensive reports and visualizations.

Week 11 implementation: New agent for generating summaries, comparisons, recommendations, and visualizations.
"""

from typing import Any
import json

from .base import BaseAgent
from ..tools.reporting_tools import (
    generate_summary,
    create_comparison_report,
    generate_recommendations,
    create_visualizations,
)


class ReportingAgent(BaseAgent):
    """
    Agent responsible for generating reports, visualizations, and recommendations.
    
    Week 11 Implementation Tools:
    - generate_summary: Create natural language summaries of results
    - create_comparison_report: Compare multiple model runs or algorithms
    - generate_recommendations: Provide actionable next steps
    - create_visualizations: Generate plots and charts
    """
    
    def __init__(self) -> None:
        """Initialize the reporting agent."""
        super().__init__(
            name="ReportingAgent",
            description="Generates comprehensive reports, visualizations, and recommendations"
        )
    
    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute report generation based on workflow results.
        
        Args:
            state: Current workflow state with evaluation results
        
        Returns:
            Updated state with report artifacts
        """
        try:
            # Get evaluation results from previous agents
            evaluation_results = state.get("evaluation_results", {})
            trained_models = state.get("trained_models", {})
            analysis_results = state.get("analysis_results", {})
            
            if not evaluation_results and not trained_models:
                state["error"] = "No results available for reporting"
                state["report_generated"] = False
                return state
            
            user_goal = state.get("user_goal", "")
            
            # Initialize report data
            report_data: dict[str, Any] = {
                "summary": None,
                "comparison": None,
                "recommendations": None,
                "visualizations": [],
            }
            
            # Generate natural language summary
            summary = generate_summary(
                user_goal=user_goal,
                evaluation_results=evaluation_results,
                trained_models=trained_models,
                analysis_results=analysis_results,
            )
            report_data["summary"] = summary
            
            # Create comparison report if multiple models exist
            if trained_models and len(trained_models) > 1:
                comparison = create_comparison_report(
                    evaluation_results=evaluation_results,
                    trained_models=trained_models,
                )
                report_data["comparison"] = comparison
            
            # Generate actionable recommendations
            recommendations = generate_recommendations(
                user_goal=user_goal,
                evaluation_results=evaluation_results,
                trained_models=trained_models,
                state=state,
            )
            report_data["recommendations"] = recommendations
            
            # Create visualizations
            visualizations = create_visualizations(
                evaluation_results=evaluation_results,
                trained_models=trained_models,
                analysis_results=analysis_results,
            )
            report_data["visualizations"] = visualizations
            
            # Update state with report data
            state["report_data"] = report_data
            state["report_generated"] = True
            state["error"] = None
            
            # Add message about report generation
            if "messages" not in state:
                state["messages"] = []
            
            state["messages"].append({
                "role": "assistant",
                "content": f"Report generated successfully. Created {len(visualizations)} visualizations.",
                "agent_name": self.name,
            })
            
            return state
            
        except Exception as e:
            state["error"] = f"Error in reporting: {str(e)}"
            state["report_generated"] = False
            return state
    
    def _format_report_as_markdown(self, report_data: dict[str, Any]) -> str:
        """
        Format report data as Markdown.
        
        Args:
            report_data: Report data dictionary
        
        Returns:
            Formatted Markdown string
        """
        markdown_parts = []
        
        # Add summary
        if report_data.get("summary"):
            markdown_parts.append("## Summary\n")
            markdown_parts.append(report_data["summary"])
            markdown_parts.append("\n\n")
        
        # Add comparison
        if report_data.get("comparison"):
            markdown_parts.append("## Model Comparison\n")
            markdown_parts.append(report_data["comparison"])
            markdown_parts.append("\n\n")
        
        # Add recommendations
        if report_data.get("recommendations"):
            markdown_parts.append("## Recommendations\n")
            for i, rec in enumerate(report_data["recommendations"], 1):
                markdown_parts.append(f"{i}. {rec}\n")
            markdown_parts.append("\n")
        
        # Add visualizations section
        if report_data.get("visualizations"):
            markdown_parts.append("## Visualizations\n")
            for viz in report_data["visualizations"]:
                markdown_parts.append(f"- {viz.get('title', 'Untitled')}: {viz.get('file_path', 'N/A')}\n")
            markdown_parts.append("\n")
        
        return "".join(markdown_parts)
    
    def _format_report_as_html(self, report_data: dict[str, Any]) -> str:
        """
        Format report data as HTML.
        
        Args:
            report_data: Report data dictionary
        
        Returns:
            Formatted HTML string
        """
        html_parts = [
            "<!DOCTYPE html>",
            "<html><head>",
            "<title>Agent Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "h2 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 5px; }",
            ".summary { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }",
            ".recommendation { margin: 10px 0; padding-left: 20px; }",
            "img { max-width: 100%; height: auto; margin: 10px 0; }",
            "</style>",
            "</head><body>",
        ]
        
        # Add summary
        if report_data.get("summary"):
            html_parts.append("<h2>Summary</h2>")
            html_parts.append(f"<div class='summary'>{report_data['summary']}</div>")
        
        # Add comparison
        if report_data.get("comparison"):
            html_parts.append("<h2>Model Comparison</h2>")
            html_parts.append(f"<div class='summary'>{report_data['comparison']}</div>")
        
        # Add recommendations
        if report_data.get("recommendations"):
            html_parts.append("<h2>Recommendations</h2>")
            html_parts.append("<ol>")
            for rec in report_data["recommendations"]:
                html_parts.append(f"<li class='recommendation'>{rec}</li>")
            html_parts.append("</ol>")
        
        # Add visualizations
        if report_data.get("visualizations"):
            html_parts.append("<h2>Visualizations</h2>")
            for viz in report_data["visualizations"]:
                if viz.get("file_path"):
                    html_parts.append(f"<h3>{viz.get('title', 'Untitled')}</h3>")
                    html_parts.append(f"<img src='{viz['file_path']}' alt='{viz.get('title', '')}' />")
        
        html_parts.append("</body></html>")
        
        return "\n".join(html_parts)
