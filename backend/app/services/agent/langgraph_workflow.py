# mypy: ignore-errors
"""
LangGraph Workflow for Agent Orchestration.

This module implements the LangGraph state machine that coordinates
specialized agents to accomplish user goals.

Week 1-2 implementation: Basic workflow foundation using existing price data.
Week 3-4 enhancement: Added DataAnalystAgent node for comprehensive analysis.
Week 5-6 enhancement: Added ModelTrainingAgent and ModelEvaluatorAgent nodes for ML pipeline.
Week 7-8 enhancement: Added ReAct loop with reasoning, conditional routing, and error recovery.
"""

import logging
import uuid
from typing import Any, Literal, TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from sqlmodel import Session

from app.core.config import settings
from app.services.agent.agents.data_analyst import DataAnalystAgent
from app.services.agent.agents.data_retrieval import DataRetrievalAgent
from app.services.agent.agents.model_evaluator import ModelEvaluatorAgent
from app.services.agent.agents.model_training import ModelTrainingAgent
from app.services.agent.agents.reporting import ReportingAgent
from app.services.agent.llm_factory import LLMFactory

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """
    State dictionary for the agent workflow.

    This state is passed between nodes in the LangGraph workflow.

    Week 3-4 additions: retrieved_data, analysis_results, insights
    Week 5-6 additions: trained_models, evaluation_results, training_summary, evaluation_insights
    Week 7-8 additions: ReAct loop fields (reasoning_trace, decision_history, retry_count, etc.)
    Week 9-10 additions: HiTL fields (clarifications, choices, approvals, overrides)
    Week 11 additions: Reporting fields (report_generated, report_data)
    """

    session_id: str
    user_goal: str
    status: str
    current_step: str
    iteration: int
    data_retrieved: bool
    analysis_completed: bool
    messages: list[dict[str, str]]
    result: str | None
    error: str | None
    # Week 3-4 additions
    retrieved_data: dict[str, Any] | None
    analysis_results: dict[str, Any] | None
    insights: list[str] | None
    retrieval_params: dict[str, Any] | None
    analysis_params: dict[str, Any] | None
    # Week 5-6 additions
    model_trained: bool
    model_evaluated: bool
    trained_models: dict[str, Any] | None
    evaluation_results: dict[str, Any] | None
    training_params: dict[str, Any] | None
    evaluation_params: dict[str, Any] | None
    training_summary: str | None
    evaluation_insights: list[str] | None
    # Week 7-8 additions - ReAct loop
    reasoning_trace: list[dict[str, str]] | None  # Track reasoning at each step
    decision_history: list[dict[str, Any]] | None  # Track routing decisions
    retry_count: int  # Track retries for error recovery
    max_retries: int  # Maximum retry attempts
    skip_analysis: bool  # Conditional flag: skip analysis if not needed
    skip_training: bool  # Conditional flag: skip training if not needed
    needs_more_data: bool  # Flag indicating if more data is needed
    quality_checks: dict[str, Any] | None  # Quality validation results
    # Week 9-10 additions - Human-in-the-Loop
    clarifications_needed: list[str] | None  # Questions to ask user
    clarifications_provided: dict[str, str] | None  # User responses
    awaiting_clarification: bool  # Workflow paused for user input
    choices_available: list[dict[str, Any]] | None  # Available options
    selected_choice: str | None  # User selection
    awaiting_choice: bool  # Workflow paused for user choice
    recommendation: dict[str, Any] | None  # System recommendation
    overrides_applied: list[dict[str, Any]] | None  # History of overrides
    can_override: dict[str, bool] | None  # Override points available
    approval_gates: list[str] | None  # Gates requiring approval
    approvals_granted: list[dict[str, Any]] | None  # Granted approvals
    approval_mode: str  # "auto" or "manual"
    approval_needed: bool  # Workflow paused for approval
    pending_approvals: list[dict[str, Any]] | None  # Pending approval requests
    # Week 11 additions - Reporting
    reporting_completed: bool  # Flag indicating reporting is complete
    reporting_results: dict[str, Any] | None  # Report generation results


class LangGraphWorkflow:
    """
    LangGraph-based workflow for coordinating multiple agents.

    This implements a state machine that routes between specialized agents
    based on the current state and user goal.

    Week 3-4: Enhanced with DataAnalystAgent for comprehensive data analysis.
    Week 5-6: Enhanced with ModelTrainingAgent and ModelEvaluatorAgent for ML pipeline.
    Week 11: Enhanced with ReportingAgent for report generation.
    """

    def __init__(
        self,
        session: Session | None = None,
        user_id: uuid.UUID | None = None,
        credential_id: uuid.UUID | None = None,
    ) -> None:
        """
        Initialize the LangGraph workflow with agents and state graph.

        Args:
            session: Optional database session for agents
            user_id: Optional user ID for BYOM (Bring Your Own Model) support
            credential_id: Optional specific LLM credential ID to use
        """
        self.session = session
        self.user_id = user_id
        self.credential_id = credential_id
        self.graph = self._build_graph()
        self.data_retrieval_agent = DataRetrievalAgent(session=session)
        self.data_analyst_agent = DataAnalystAgent()
        self.model_training_agent = ModelTrainingAgent()
        self.model_evaluator_agent = ModelEvaluatorAgent()
        self.reporting_agent = ReportingAgent()

        # Initialize LLM for reasoning using LLM Factory (Sprint 2.9)
        self.llm = None
        if session and user_id:
            # Use BYOM - user's configured LLM or system default
            try:
                self.llm = LLMFactory.create_llm(
                    session=session, user_id=user_id, credential_id=credential_id
                )
            except Exception as e:
                logger.warning(
                    f"Failed to create LLM via factory: {e}. Falling back to system default."
                )
                # Fallback to system default if BYOM fails
                if settings.OPENAI_API_KEY:
                    self.llm = ChatOpenAI(
                        model=settings.OPENAI_MODEL,
                        api_key=settings.OPENAI_API_KEY,
                        max_tokens=settings.MAX_TOKENS_PER_REQUEST,
                        streaming=settings.ENABLE_STREAMING,
                    )
        elif settings.OPENAI_API_KEY:
            # No BYOM context - use system default OpenAI
            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                api_key=settings.OPENAI_API_KEY,
                max_tokens=settings.MAX_TOKENS_PER_REQUEST,
                streaming=settings.ENABLE_STREAMING,
            )

    def set_session(self, session: Session) -> None:
        """
        Set the database session for agents.

        Args:
            session: Database session
        """
        self.session = session
        self.data_retrieval_agent.set_session(session)

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state machine with ReAct loop.

        Week 3-4: Added analyze_data node between retrieve_data and finalize.
        Week 5-6: Added train_model and evaluate_model nodes for ML pipeline.
        Week 7-8: Enhanced with conditional routing, reasoning nodes, and error recovery.
        Week 11: Added generate_report node for comprehensive reporting.

        Returns:
            Configured state graph with conditional edges
        """
        # Create the state graph
        workflow = StateGraph(AgentState)

        # Add reasoning/planning node (ReAct: Reason phase)
        workflow.add_node("reason", self._reason_node)

        # Add nodes for different stages (ReAct: Act phase)
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("retrieve_data", self._retrieve_data_node)
        workflow.add_node("validate_data", self._validate_data_node)
        workflow.add_node("analyze_data", self._analyze_data_node)
        workflow.add_node("train_model", self._train_model_node)
        workflow.add_node("evaluate_model", self._evaluate_model_node)
        workflow.add_node("generate_report", self._generate_report_node)
        workflow.add_node("finalize", self._finalize_node)

        # Add error recovery node
        workflow.add_node("handle_error", self._handle_error_node)

        # Define edges with conditional routing
        workflow.set_entry_point("initialize")

        # After initialization, always reason first
        workflow.add_edge("initialize", "reason")

        # Conditional routing from reason node
        workflow.add_conditional_edges(
            "reason",
            self._route_after_reasoning,
            {
                "retrieve": "retrieve_data",
                "analyze": "analyze_data",
                "train": "train_model",
                "evaluate": "evaluate_model",
                "report": "generate_report",
                "finalize": "finalize",
                "error": "handle_error",
            },
        )

        # After data retrieval, validate the data
        workflow.add_edge("retrieve_data", "validate_data")

        # Conditional routing after validation
        workflow.add_conditional_edges(
            "validate_data",
            self._route_after_validation,
            {
                "analyze": "analyze_data",
                "retry": "retrieve_data",
                "reason": "reason",
                "error": "handle_error",
            },
        )

        # After analysis, decide next step
        workflow.add_conditional_edges(
            "analyze_data",
            self._route_after_analysis,
            {
                "train": "train_model",
                "finalize": "finalize",
                "reason": "reason",
                "error": "handle_error",
            },
        )

        # After training, evaluate
        workflow.add_conditional_edges(
            "train_model",
            self._route_after_training,
            {
                "evaluate": "evaluate_model",
                "reason": "reason",
                "error": "handle_error",
            },
        )

        # After evaluation, generate report or retry
        workflow.add_conditional_edges(
            "evaluate_model",
            self._route_after_evaluation,
            {
                "report": "generate_report",
                "retrain": "train_model",
                "reason": "reason",
                "error": "handle_error",
            },
        )

        # After report generation, finalize
        workflow.add_edge("generate_report", "finalize")

        # Error handling routes back to reason or ends
        workflow.add_conditional_edges(
            "handle_error",
            self._route_after_error,
            {
                "retry": "reason",
                "end": "finalize",
            },
        )

        # Finalize always ends
        workflow.add_edge("finalize", END)

        return workflow.compile()

    async def _initialize_node(self, state: AgentState) -> AgentState:
        """
        Initialize the workflow with ReAct loop fields.

        Week 7-8: Enhanced with ReAct loop initialization.

        Args:
            state: Current workflow state

        Returns:
            Updated state
        """
        state["current_step"] = "initialization"
        state["messages"] = state.get("messages", [])
        state["analysis_completed"] = False
        state["model_trained"] = False
        state["model_evaluated"] = False
        state["reporting_completed"] = False

        # Week 7-8: Initialize ReAct loop fields
        state["reasoning_trace"] = []
        state["decision_history"] = []
        state["retry_count"] = 0
        state["max_retries"] = 3
        state["skip_analysis"] = False
        state["skip_training"] = False
        state["needs_more_data"] = False
        state["quality_checks"] = {}

        # Week 11: Initialize reporting fields
        state["report_generated"] = False
        state["report_data"] = None

        state["messages"].append(
            {
                "role": "system",
                "content": "Agent workflow initialized with ReAct loop. Starting reasoning phase...",
            }
        )

        logger.info(f"Workflow initialized for session {state.get('session_id')}")
        return state

    async def _reason_node(self, state: AgentState) -> AgentState:
        """
        ReAct Reasoning phase: Determine the next action based on current state.

        Week 7-8: New node for ReAct loop reasoning.
        Uses LLM to reason about what to do next based on:
        - User goal
        - Current state (what's been done)
        - Previous errors/failures
        - Data quality

        Args:
            state: Current workflow state

        Returns:
            Updated state with reasoning decision
        """
        state["current_step"] = "reasoning"

        # Build context for reasoning
        context_parts = [f"User Goal: {state.get('user_goal', 'Unknown')}"]

        # Add what's been completed
        completed_steps = []
        if state.get("data_retrieved"):
            completed_steps.append("✓ Data retrieved")
        if state.get("analysis_completed"):
            completed_steps.append("✓ Data analyzed")
        if state.get("model_trained"):
            completed_steps.append("✓ Model trained")
        if state.get("model_evaluated"):
            completed_steps.append("✓ Model evaluated")

        if completed_steps:
            context_parts.append(f"Completed: {', '.join(completed_steps)}")

        # Add error context if any
        if state.get("error"):
            context_parts.append(f"Previous Error: {state.get('error')}")
            context_parts.append(
                f"Retry Count: {state.get('retry_count', 0)}/{state.get('max_retries', 3)}"
            )

        # Add quality check results if any
        quality_checks = state.get("quality_checks", {})
        if quality_checks:
            context_parts.append(
                f"Data Quality: {quality_checks.get('overall', 'Unknown')}"
            )

        context = "\n".join(context_parts)

        # Perform reasoning (simplified version without LLM if no API key)
        reasoning = self._determine_next_action(state)

        # Store reasoning trace
        reasoning_entry = {
            "step": state.get("iteration", 0),
            "context": context,
            "decision": reasoning,
            "timestamp": state.get("current_step", "unknown"),
        }

        reasoning_trace = state.get("reasoning_trace", [])
        reasoning_trace.append(reasoning_entry)
        state["reasoning_trace"] = reasoning_trace

        state["messages"].append(
            {"role": "system", "content": f"Reasoning: {reasoning}"}
        )

        logger.info(f"Reasoning completed: {reasoning}")
        return state

    def _determine_next_action(self, state: AgentState) -> str:
        """
        Determine the next action based on current state.

        This is a rule-based system that can be enhanced with LLM reasoning.

        Args:
            state: Current workflow state

        Returns:
            Next action decision
        """
        # Check for errors that need handling
        if state.get("error") and state.get("retry_count", 0) < state.get(
            "max_retries", 3
        ):
            return "Will retry the failed step after error recovery"
        elif state.get("error") and state.get("retry_count", 0) >= state.get(
            "max_retries", 3
        ):
            return "Max retries reached, will finalize with partial results"

        # Normal flow
        if not state.get("data_retrieved"):
            return "Need to retrieve data first"
        elif state.get("needs_more_data"):
            return "Need to retrieve additional data"
        elif not state.get("analysis_completed") and not state.get("skip_analysis"):
            return "Data ready, will analyze next"
        elif not state.get("model_trained") and not state.get("skip_training"):
            # Check if user goal requires modeling
            user_goal = state.get("user_goal", "").lower()
            if any(
                keyword in user_goal
                for keyword in ["predict", "model", "forecast", "train", "ml"]
            ):
                return "Analysis complete, will train model next"
            else:
                return "Analysis complete, modeling not needed for this goal"
        elif state.get("model_trained") and not state.get("model_evaluated"):
            return "Model trained, will evaluate next"
        else:
            return "All steps complete, will finalize results"

    async def _retrieve_data_node(self, state: AgentState) -> AgentState:
        """
        Execute data retrieval agent.

        Week 3-4: Enhanced to retrieve comprehensive data (price, sentiment, on-chain, catalysts).

        Args:
            state: Current workflow state

        Returns:
            Updated state with retrieved data
        """
        state["current_step"] = "data_retrieval"

        try:
            # Execute data retrieval agent
            updated_state = await self.data_retrieval_agent.execute(state)

            # Add message about data retrieval
            data_types = updated_state.get("retrieval_metadata", {}).get(
                "data_types", []
            )
            updated_state["messages"].append(
                {
                    "role": "assistant",
                    "content": f"Data retrieval completed. Retrieved: {', '.join(data_types)}",
                }
            )

            return updated_state
        except Exception as e:
            logger.error(f"Error in data retrieval: {str(e)}")
            state["error"] = f"Data retrieval failed: {str(e)}"
            return state

    async def _validate_data_node(self, state: AgentState) -> AgentState:
        """
        Validate retrieved data quality.

        Week 7-8: New node for data quality validation.
        Checks if retrieved data is sufficient and of good quality.

        Args:
            state: Current workflow state

        Returns:
            Updated state with quality check results
        """
        state["current_step"] = "data_validation"

        retrieved_data = state.get("retrieved_data", {})
        quality_checks = {}

        # Check if we have data
        has_data = bool(retrieved_data)
        quality_checks["has_data"] = has_data

        # Check data completeness
        if has_data:
            data_types = []
            if "price_data" in retrieved_data and retrieved_data["price_data"]:
                data_types.append("price")
            if "sentiment_data" in retrieved_data and retrieved_data["sentiment_data"]:
                data_types.append("sentiment")
            if "on_chain_data" in retrieved_data and retrieved_data["on_chain_data"]:
                data_types.append("on-chain")
            if "catalyst_data" in retrieved_data and retrieved_data["catalyst_data"]:
                data_types.append("catalysts")

            quality_checks["data_types_available"] = data_types
            quality_checks["completeness"] = len(data_types) >= 1  # At least one type

            # Check data size (for price data, main requirement)
            price_data = retrieved_data.get("price_data", [])
            quality_checks["price_records"] = len(price_data)
            quality_checks["sufficient_records"] = (
                len(price_data) >= 30
            )  # At least 30 records

            # Overall quality assessment
            if quality_checks["completeness"] and quality_checks["sufficient_records"]:
                quality_checks["overall"] = "good"
            elif quality_checks["completeness"] or quality_checks["sufficient_records"]:
                quality_checks["overall"] = "fair"
            else:
                quality_checks["overall"] = "poor"
        else:
            quality_checks["overall"] = "no_data"

        state["quality_checks"] = quality_checks

        # Log validation results
        logger.info(f"Data validation: {quality_checks['overall']}")

        state["messages"].append(
            {
                "role": "system",
                "content": f"Data validation complete. Quality: {quality_checks['overall']}",
            }
        )

        return state

    async def _analyze_data_node(self, state: AgentState) -> AgentState:
        """
        Execute data analyst agent.

        Week 3-4: New node for comprehensive data analysis.

        Args:
            state: Current workflow state

        Returns:
            Updated state with analysis results
        """
        state["current_step"] = "data_analysis"

        try:
            # Execute data analyst agent
            updated_state = await self.data_analyst_agent.execute(state)

            # Add message about analysis
            insights = updated_state.get("insights", [])
            insight_summary = (
                "; ".join(insights[:3]) if insights else "Analysis complete"
            )
            updated_state["messages"].append(
                {
                    "role": "assistant",
                    "content": f"Data analysis completed. Key insights: {insight_summary}",
                }
            )

            return updated_state
        except Exception as e:
            logger.error(f"Error in data analysis: {str(e)}")
            state["error"] = f"Data analysis failed: {str(e)}"
            return state

    async def _train_model_node(self, state: AgentState) -> AgentState:
        """
        Execute model training agent.

        Week 5-6: New node for training machine learning models.

        Args:
            state: Current workflow state

        Returns:
            Updated state with trained models
        """
        state["current_step"] = "model_training"

        try:
            # Execute model training agent
            updated_state = await self.model_training_agent.execute(state)

            # Add message about training
            if updated_state.get("model_trained"):
                training_summary = updated_state.get(
                    "training_summary", "Model training completed"
                )
                updated_state["messages"].append(
                    {
                        "role": "assistant",
                        "content": f"Model training completed. {training_summary.split(chr(10))[0]}",
                    }
                )

            return updated_state
        except Exception as e:
            logger.error(f"Error in model training: {str(e)}")
            state["error"] = f"Model training failed: {str(e)}"
            return state

    async def _evaluate_model_node(self, state: AgentState) -> AgentState:
        """
        Execute model evaluator agent.

        Week 5-6: New node for evaluating and comparing models.

        Args:
            state: Current workflow state

        Returns:
            Updated state with evaluation results
        """
        state["current_step"] = "model_evaluation"

        try:
            # Execute model evaluator agent
            updated_state = await self.model_evaluator_agent.execute(state)

            # Add message about evaluation
            if updated_state.get("model_evaluated"):
                insights = updated_state.get("evaluation_insights", [])
                insight_summary = (
                    insights[0] if insights else "Model evaluation completed"
                )
                updated_state["messages"].append(
                    {
                        "role": "assistant",
                        "content": f"Model evaluation completed. {insight_summary}",
                    }
                )

            return updated_state
        except Exception as e:
            logger.error(f"Error in model evaluation: {str(e)}")
            state["error"] = f"Model evaluation failed: {str(e)}"
            return state

    async def _generate_report_node(self, state: AgentState) -> AgentState:
        """
        Execute reporting agent to generate comprehensive reports.

        Week 11: New node for generating reports and visualizations.

        Args:
            state: Current workflow state

        Returns:
            Updated state with reporting results
        """
        state["current_step"] = "report_generation"

        try:
            # Execute reporting agent
            updated_state = await self.reporting_agent.execute(state)

            # Add message about reporting
            if updated_state.get("reporting_completed"):
                reporting_results = updated_state.get("reporting_results", {})
                viz_count = len(reporting_results.get("visualizations", {}))
                rec_count = len(reporting_results.get("recommendations", []))

                updated_state["messages"].append(
                    {
                        "role": "assistant",
                        "content": (
                            f"Report generation completed. Generated {viz_count} visualizations "
                            f"and {rec_count} recommendations. Complete report available."
                        ),
                    }
                )

            return updated_state
        except Exception as e:
            logger.error(f"Error in report generation: {str(e)}")
            state["error"] = f"Report generation failed: {str(e)}"
            # Continue to finalize even if reporting fails
            state["reporting_completed"] = False
            return state

    async def _finalize_node(self, state: AgentState) -> AgentState:
        """
        Finalize the workflow and prepare results.

        Week 3-4: Enhanced to include analysis results and insights in final result.
        Week 5-6: Enhanced to include training and evaluation results.

        Args:
            state: Current workflow state

        Returns:
            Final state with results
        """
        state["current_step"] = "finalization"
        state["status"] = "completed"

        # Build comprehensive result message
        result_parts = ["Workflow completed successfully."]

        # Add analysis insights
        insights = state.get("insights", [])
        if insights:
            result_parts.append("\n\nData Analysis Insights:")
            result_parts.extend([f"- {insight}" for insight in insights[:5]])

        # Add training summary
        training_summary = state.get("training_summary")
        if training_summary:
            result_parts.append("\n\nModel Training Summary:")
            result_parts.append(training_summary)

        # Add evaluation insights
        eval_insights = state.get("evaluation_insights", [])
        if eval_insights:
            result_parts.append("\n\nModel Evaluation Insights:")
            result_parts.extend([f"- {insight}" for insight in eval_insights])

        state["result"] = "\n".join(result_parts)

        state["messages"].append(
            {
                "role": "assistant",
                "content": "Workflow completed successfully. All results prepared.",
            }
        )

        return state

    async def _handle_error_node(self, state: AgentState) -> AgentState:
        """
        Handle errors with recovery logic.

        Week 7-8: New node for error recovery.
        Implements retry logic and determines if recovery is possible.

        Args:
            state: Current workflow state

        Returns:
            Updated state with error handling
        """
        state["current_step"] = "error_handling"

        error = state.get("error", "Unknown error")
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 3)

        logger.warning(f"Handling error: {error}, retry {retry_count}/{max_retries}")

        # Increment retry count
        state["retry_count"] = retry_count + 1

        # Record error in decision history
        decision_history = state.get("decision_history", [])
        decision_history.append(
            {
                "step": "error_handling",
                "error": error,
                "retry_count": state["retry_count"],
                "action": "retry" if state["retry_count"] <= max_retries else "abort",
            }
        )
        state["decision_history"] = decision_history

        if state["retry_count"] <= max_retries:
            state["messages"].append(
                {
                    "role": "system",
                    "content": f"Error encountered: {error}. Attempting recovery (retry {state['retry_count']}/{max_retries})...",
                }
            )
            # Clear error to allow retry
            state["error"] = None
        else:
            state["messages"].append(
                {
                    "role": "system",
                    "content": "Max retries reached. Finalizing with partial results.",
                }
            )
            state["status"] = "completed_with_errors"

        return state

    # Routing Functions for Conditional Edges

    def _route_after_reasoning(
        self, state: AgentState
    ) -> Literal[
        "retrieve", "analyze", "train", "evaluate", "report", "finalize", "error"
    ]:
        """
        Route after reasoning based on current state.

        Week 11: Added report routing option.

        Args:
            state: Current workflow state

        Returns:
            Next node to execute
        """
        # Check for errors
        if state.get("error"):
            return "error"

        # Normal flow based on completion status
        if not state.get("data_retrieved"):
            return "retrieve"
        elif state.get("needs_more_data"):
            return "retrieve"
        elif not state.get("analysis_completed") and not state.get("skip_analysis"):
            return "analyze"
        elif not state.get("model_trained") and not state.get("skip_training"):
            # Check if modeling is needed
            user_goal = state.get("user_goal", "").lower()
            if any(
                keyword in user_goal
                for keyword in ["predict", "model", "forecast", "train", "ml"]
            ):
                return "train"
            else:
                # Skip training for non-ML goals
                state["skip_training"] = True
                return "finalize"
        elif state.get("model_trained") and not state.get("model_evaluated"):
            return "evaluate"
        elif state.get("model_evaluated") and not state.get("report_generated"):
            return "report"
        else:
            return "finalize"

    def _route_after_validation(
        self, state: AgentState
    ) -> Literal["analyze", "retry", "reason", "error"]:
        """
        Route after data validation.

        Args:
            state: Current workflow state

        Returns:
            Next node to execute
        """
        quality_checks = state.get("quality_checks", {})
        overall_quality = quality_checks.get("overall", "unknown")

        if overall_quality == "no_data":
            # No data retrieved, check retry count
            retry_count = state.get("retry_count", 0)
            max_retries = state.get("max_retries", 3)

            if retry_count < max_retries:
                # Increment retry count and retry
                state["retry_count"] = retry_count + 1
                logger.warning(
                    f"No data retrieved, retry {retry_count + 1}/{max_retries}"
                )
                return "retry"
            else:
                # Max retries exceeded
                state["error"] = "Failed to retrieve data after maximum retries"
                logger.error("Max retries exceeded for data retrieval")
                return "error"
        elif overall_quality == "poor":
            # Poor quality, might need more data
            state["needs_more_data"] = True
            return "reason"  # Go back to reasoning to decide
        elif overall_quality in ["fair", "good"]:
            # Data is acceptable, proceed to analysis
            return "analyze"
        else:
            # Unknown quality, increment retry and try reason
            retry_count = state.get("retry_count", 0)
            if retry_count >= state.get("max_retries", 3):
                state["error"] = "Data validation failed repeatedly"
                return "error"
            state["retry_count"] = retry_count + 1
            return "reason"

    def _route_after_analysis(
        self, state: AgentState
    ) -> Literal["train", "finalize", "reason", "error"]:
        """
        Route after data analysis.

        Args:
            state: Current workflow state

        Returns:
            Next node to execute
        """
        # Check if analysis succeeded
        if not state.get("analysis_completed"):
            state["error"] = "Analysis failed to complete"
            return "error"

        # Check if training is needed
        user_goal = state.get("user_goal", "").lower()
        if any(
            keyword in user_goal
            for keyword in ["predict", "model", "forecast", "train", "ml"]
        ):
            return "train"
        else:
            # No training needed, finalize
            return "finalize"

    def _route_after_training(
        self, state: AgentState
    ) -> Literal["evaluate", "reason", "error"]:
        """
        Route after model training.

        Args:
            state: Current workflow state

        Returns:
            Next node to execute
        """
        if not state.get("model_trained"):
            state["error"] = "Model training failed"
            return "error"

        return "evaluate"

    def _route_after_evaluation(
        self, state: AgentState
    ) -> Literal["report", "retrain", "reason", "error"]:
        """
        Route after model evaluation.

        Week 11: Updated to route to report generation instead of finalize.

        Args:
            state: Current workflow state

        Returns:
            Next node to execute
        """
        if not state.get("model_evaluated"):
            state["error"] = "Model evaluation failed"
            return "error"

        # Check if model performance is acceptable
        evaluation_results = state.get("evaluation_results", {})

        # Simple check: if we have results, generate report
        # In future, could check metrics and decide to retrain
        if evaluation_results:
            return "report"
        else:
            return "report"

    def _route_after_error(self, state: AgentState) -> Literal["retry", "end"]:
        """
        Route after error handling.

        Args:
            state: Current workflow state

        Returns:
            Next node to execute
        """
        if state.get("retry_count", 0) <= state.get("max_retries", 3):
            return "retry"
        else:
            return "end"

    async def execute(self, initial_state: AgentState) -> AgentState:
        """
        Execute the workflow from start to finish.

        Args:
            initial_state: Initial workflow state

        Returns:
            Final workflow state
        """
        # Execute the graph with the initial state
        final_state = await self.graph.ainvoke(initial_state)
        return final_state

    async def stream_execute(self, initial_state: AgentState):
        """
        Execute the workflow with streaming for real-time updates.

        Args:
            initial_state: Initial workflow state

        Yields:
            State updates as the workflow progresses
        """
        async for state in self.graph.astream(initial_state):
            yield state
