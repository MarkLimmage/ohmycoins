# mypy: ignore-errors
"""
Clarification Node for Human-in-the-Loop workflow.

This node detects ambiguous inputs or data issues and generates
clarification questions for the user.
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


def clarification_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Detect ambiguous inputs and generate clarification questions.

    This node analyzes the current state to determine if clarification
    is needed from the user. Common scenarios include:
    - Ambiguous user goals (e.g., "predict prices" without specifying coins or timeframe)
    - Insufficient data for analysis
    - Multiple valid interpretations of the goal

    Args:
        state: Current workflow state

    Returns:
        Updated state with clarifications_needed and awaiting_clarification fields
    """
    logger.info("ClarificationNode: Analyzing state for ambiguities")

    user_goal = state.get("user_goal", "")
    retrieved_data = state.get("retrieved_data")
    clarifications_needed = []

    # Initialize LLM for clarification generation
    from app.services.agent.llm_factory import LLMFactory
    llm = LLMFactory._create_system_default_llm()

    # Check for ambiguous goal
    if _is_goal_ambiguous(user_goal):
        logger.info("ClarificationNode: User goal is ambiguous")

        # Generate clarification questions using LLM
        system_message = SystemMessage(
            content="""
You are an expert at identifying ambiguities in data science goals.
Analyze the user's goal and generate 2-3 specific, actionable clarification questions.
Focus on:
1. Which cryptocurrencies to analyze
2. Time period for analysis
3. Specific prediction or analysis type desired

Return questions in a simple list format, one per line.
"""
        )

        human_message = HumanMessage(content=f"User goal: {user_goal}")

        try:
            response = llm.invoke([system_message, human_message])
            questions = [q.strip() for q in response.content.split("\n") if q.strip()]
            clarifications_needed.extend(questions[:3])  # Max 3 questions
        except Exception as e:
            logger.error(f"ClarificationNode: Error generating questions: {e}")
            # Fallback to template-based questions
            clarifications_needed.extend(_generate_template_questions(user_goal))

    # Check for data quality issues
    if retrieved_data:
        data_issues = _check_data_quality(retrieved_data)
        if data_issues:
            logger.info(
                f"ClarificationNode: Data quality issues detected: {data_issues}"
            )
            clarifications_needed.extend(data_issues)

    # Update state
    state["clarifications_needed"] = clarifications_needed
    state["awaiting_clarification"] = len(clarifications_needed) > 0

    if clarifications_needed:
        logger.info(
            f"ClarificationNode: {len(clarifications_needed)} clarifications needed"
        )
        state["current_step"] = "awaiting_clarification"
        # Add to reasoning trace
        if "reasoning_trace" not in state or state["reasoning_trace"] is None:
            state["reasoning_trace"] = []
        state["reasoning_trace"].append(
            {
                "step": "clarification",
                "reasoning": f"Need clarification on {len(clarifications_needed)} points",
                "questions": clarifications_needed,
            }
        )
    else:
        logger.info("ClarificationNode: No clarifications needed, proceeding")
        state["awaiting_clarification"] = False

    return state


def _is_goal_ambiguous(goal: str) -> bool:
    """
    Determine if a user goal is ambiguous.

    Args:
        goal: User's stated goal

    Returns:
        True if goal is ambiguous and needs clarification
    """
    # Check for vague language
    vague_terms = ["predict", "analyze", "trading", "algorithm", "model"]
    specific_terms = [
        "bitcoin",
        "btc",
        "ethereum",
        "eth",
        "daily",
        "weekly",
        "month",
        "technical indicators",
        "sentiment analysis",
        "price movements",
    ]

    goal_lower = goal.lower()
    has_vague = any(term in goal_lower for term in vague_terms)
    has_specific = any(term in goal_lower for term in specific_terms)

    # If goal contains vague terms but lacks specifics, it's ambiguous
    # Also consider goals with < 10 words as potentially too short
    return has_vague and not has_specific and len(goal.split()) < 10


def _generate_template_questions(goal: str) -> list[str]:
    """
    Generate template-based clarification questions as fallback.

    Args:
        goal: User's stated goal

    Returns:
        List of clarification questions
    """
    questions = []

    goal_lower = goal.lower()

    # Coin selection
    if (
        "coin" not in goal_lower
        and "btc" not in goal_lower
        and "bitcoin" not in goal_lower
    ):
        questions.append(
            "Which cryptocurrency would you like to analyze? (e.g., Bitcoin, Ethereum)"
        )

    # Timeframe
    if not any(
        t in goal_lower for t in ["day", "week", "month", "year", "daily", "weekly"]
    ):
        questions.append(
            "What time period should I analyze? (e.g., last 30 days, last 3 months)"
        )

    # Analysis type
    if "predict" in goal_lower or "forecast" in goal_lower:
        questions.append(
            "What would you like to predict? (e.g., price direction, volatility, trading signals)"
        )

    return questions


def _check_data_quality(retrieved_data: dict[str, Any]) -> list[str]:
    """
    Check retrieved data for quality issues.

    Args:
        retrieved_data: Data retrieved by DataRetrievalAgent

    Returns:
        List of data quality issues requiring user clarification
    """
    issues = []

    # Check if data is empty or insufficient
    if not retrieved_data or not any(retrieved_data.values()):
        issues.append(
            "No data was retrieved. Would you like to adjust the time period or data sources?"
        )
        return issues

    # Check each data type
    for data_type, data in retrieved_data.items():
        if data_type == "price_data":
            if isinstance(data, list) and len(data) < 10:
                issues.append(
                    f"Only {len(data)} price data points found. Would you like to expand the time range?"
                )

        elif data_type == "sentiment_data":
            if isinstance(data, list) and len(data) < 5:
                issues.append(
                    f"Limited sentiment data available ({len(data)} records). Should I proceed with price data only?"
                )

    return issues


def handle_clarification_response(
    state: dict[str, Any], responses: dict[str, str]
) -> dict[str, Any]:
    """
    Process user responses to clarification questions.

    Args:
        state: Current workflow state
        responses: Dict mapping question to user response

    Returns:
        Updated state with clarifications incorporated
    """
    logger.info("ClarificationNode: Processing user responses")

    # Handle Scope Confirmation (Phase 5)
    if state.get("awaiting_scope_confirmation"):
        state["scope_confirmed"] = True
        state["awaiting_scope_confirmation"] = False

        # If user provided adjustments, append to goal
        # responses might be {"adjustment": "Actually look at SOL too"}
        adjustment = responses.get("adjustment")
        if adjustment:
             state["user_goal"] = f"{state.get('user_goal', '')}. Adjustment: {adjustment}"
             logger.info(f"ScopeConfirmation: Goal adjusted: {adjustment}")

        # Add to reasoning trace
        if "reasoning_trace" not in state or state["reasoning_trace"] is None:
            state["reasoning_trace"] = []
        state["reasoning_trace"].append({
            "step": "scope_confirmed",
            "adjustment": adjustment
        })
        return state

    # Store responses in state
    if "clarifications_provided" not in state:
        state["clarifications_provided"] = {}

    state["clarifications_provided"].update(responses)

    # Update user goal with clarifications
    clarified_goal = _incorporate_clarifications(state.get("user_goal", ""), responses)

    state["user_goal"] = clarified_goal
    state["awaiting_clarification"] = False
    state["clarifications_needed"] = []
    state["current_step"] = "planning"

    # Add to reasoning trace
    if "reasoning_trace" not in state or state["reasoning_trace"] is None:
        state["reasoning_trace"] = []

    state["reasoning_trace"].append(
        {
            "step": "clarification_received",
            "responses": responses,
            "updated_goal": clarified_goal,
        }
    )

    logger.info(f"ClarificationNode: Updated goal: {clarified_goal}")

    return state


def _incorporate_clarifications(
    original_goal: str, clarifications: dict[str, str]
) -> str:
    """
    Incorporate user clarifications into the goal statement.

    Args:
        original_goal: Original user goal
        clarifications: User responses to clarification questions

    Returns:
        Enhanced goal statement
    """
    # Combine original goal with clarifications
    clarification_text = " ".join(
        [f"{response}" for response in clarifications.values()]
    )

    enhanced_goal = f"{original_goal}. {clarification_text}"

    return enhanced_goal


class ScopeInterpretation(BaseModel):
    assets: list[str] = Field(description="List of assets to analyze, e.g. ['BTC', 'ETH']")
    timeframe: str = Field(description="Timeframe for analysis, e.g. '30d'")
    analysis_type: str = Field(description="Type of analysis, e.g. 'trend_analysis', 'price_prediction'")
    indicators: list[str] = Field(description="List of technical indicators")
    modeling_target: str = Field(description="Target variable for modeling, e.g. 'price_direction_1h'")
    reasoning: str = Field(description="Explanation of why this scope was chosen")


def scope_confirmation_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Parse user goal and emit scope confirmation request.
    MANDATORY step for every session.
    """
    logger.info("ScopeConfirmationNode: Parsing user goal")
    user_goal = state.get("user_goal", "")

    # Check if we already have a confirmed scope (re-entry)
    if state.get("scope_confirmed"):
        return {"current_step": "scope_confirmed"}

    from app.services.agent.llm_factory import LLMFactory
    llm = LLMFactory._create_system_default_llm()

    # 1. Parse Scope
    structured_llm = llm.with_structured_output(ScopeInterpretation)
    system_msg = SystemMessage(content="You are a trading strategy expert. Parse the user's goal into a structured scope.")
    human_msg = HumanMessage(content=f"User goal: {user_goal}")

    try:
        scope = structured_llm.invoke([system_msg, human_msg])

        # 2. Generate Events (Success Path)
        events = []

        # Stream Chat (Explanation)
        events.append({
            "event_type": "stream_chat",
            "stage": "BUSINESS_UNDERSTANDING",
            "payload": {
                "message": f"I've analyzed your request: '{user_goal}'. {scope.reasoning}",
                "sender": "assistant"
            }
        })

        # Action Request (Scope Confirmation)
        events.append({
            "event_type": "action_request",
            "stage": "BUSINESS_UNDERSTANDING",
            "action_id": "scope_confirmation_v1",
            "payload": {
                "action_id": "scope_confirmation_v1",
                "description": "Please confirm the analysis scope.",
                "interpretation": {
                    "assets": scope.assets,
                    "timeframe": scope.timeframe,
                    "analysis_type": scope.analysis_type,
                    "indicators": scope.indicators,
                    "modeling_target": scope.modeling_target
                },
                "questions": ["Is this the correct set of assets?", "Is the timeframe appropriate?"],
                "options": ["CONFIRM_SCOPE", "ADJUST_SCOPE"]
            }
        })

        # Plan Established
        # Generate tasks based on analysis type (simple logic for now)
        tasks = [
             { "stage": "BUSINESS_UNDERSTANDING", "tasks": [{ "task_id": "scope_confirmation", "label": "Confirm Scope", "status": "in_progress" }] },
             { "stage": "DATA_ACQUISITION", "tasks": [{ "task_id": "fetch_price_data", "label": f"Fetch OHLCV for {', '.join(scope.assets)}" }] },
             { "stage": "PREPARATION", "tasks": [{ "task_id": "validate_quality", "label": "Run data quality checks" }] },
             { "stage": "EXPLORATION", "tasks": [{ "task_id": "compute_indicators", "label": f"Calculate {', '.join(scope.indicators)}" }] },
        ]

        if "predict" in scope.analysis_type:
             tasks.append({ "stage": "MODELING", "tasks": [{ "task_id": "train_models", "label": f"Train model for {scope.modeling_target}" }] })
             tasks.append({ "stage": "EVALUATION", "tasks": [{ "task_id": "evaluate_model", "label": "Evaluate model performance" }] })

        tasks.append({ "stage": "DEPLOYMENT", "tasks": [{ "task_id": "generate_report", "label": "Generate final report" }] })

        events.append({
            "event_type": "plan_established",
            "stage": "BUSINESS_UNDERSTANDING",
            "payload": { "plan": tasks }
        })

        return {
            "current_step": "scope_confirmation",
            "pending_events": events,
            "scope_interpretation": scope.model_dump(),
            # We rely on interrupt logic, but this flag helps track state
            "awaiting_scope_confirmation": True
        }

    except Exception as e:
        logger.error(f"Error parsing scope: {e}")

        # F1: Circuit Breaker Escalation
        circuit_breaker_event = {
            "event_type": "action_request",
            "stage": "BUSINESS_UNDERSTANDING",
            "payload": {
                "action_id": "circuit_breaker_v1",
                "description": "I encountered an error while analyzing your request. I need your guidance to proceed.",
                "stage": "BUSINESS_UNDERSTANDING",
                "attempts": 1,
                "last_error": str(e),
                "suggestions": [
                    "Check your LLM API key in Settings → LLM Credentials",
                    "Try a different LLM provider (Google Gemini, Anthropic)",
                    "Retry the session after updating credentials"
                ],
                "options": ["CHOOSE_SUGGESTION", "PROVIDE_GUIDANCE", "ABORT_SESSION"]
            }
        }

        # F4: Plan Established Fallback
        plan_established_event = {
            "event_type": "plan_established",
            "stage": "BUSINESS_UNDERSTANDING",
            "payload": {
                "plan": [
                    {"stage": "DATA_ACQUISITION", "tasks": [
                        {"task_id": "fetch_price_data", "label": "Fetch OHLCV price data"},
                        {"task_id": "fetch_sentiment", "label": "Fetch sentiment scores"}
                    ]},
                    {"stage": "PREPARATION", "tasks": [
                        {"task_id": "validate_quality", "label": "Run data quality checks"}
                    ]},
                    {"stage": "EXPLORATION", "tasks": [
                        {"task_id": "compute_technical_indicators", "label": "Calculate technical indicators"},
                        {"task_id": "perform_eda", "label": "Exploratory data analysis"}
                    ]},
                    {"stage": "MODELING", "tasks": [
                        {"task_id": "train_models", "label": "Train ML models"}
                    ]},
                    {"stage": "EVALUATION", "tasks": [
                        {"task_id": "evaluate_metrics", "label": "Compute evaluation metrics"},
                        {"task_id": "compare_models", "label": "Compare model performance"}
                    ]},
                    {"stage": "DEPLOYMENT", "tasks": [
                        {"task_id": "generate_report", "label": "Generate final report"}
                    ]}
                ]
            }
        }

        return {
            "current_step": "scope_confirmation",
            "pending_events": [circuit_breaker_event, plan_established_event],
            "awaiting_scope_confirmation": True
        }

