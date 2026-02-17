# mypy: ignore-errors
"""
Clarification Node for Human-in-the-Loop workflow.

This node detects ambiguous inputs or data issues and generates 
clarification questions for the user.
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings

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
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=0.3,  # Lower temperature for more focused questions
        api_key=settings.OPENAI_API_KEY,
    )

    # Check for ambiguous goal
    if _is_goal_ambiguous(user_goal):
        logger.info("ClarificationNode: User goal is ambiguous")

        # Generate clarification questions using LLM
        system_message = SystemMessage(content="""
You are an expert at identifying ambiguities in data science goals.
Analyze the user's goal and generate 2-3 specific, actionable clarification questions.
Focus on:
1. Which cryptocurrencies to analyze
2. Time period for analysis
3. Specific prediction or analysis type desired

Return questions in a simple list format, one per line.
""")

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
            logger.info(f"ClarificationNode: Data quality issues detected: {data_issues}")
            clarifications_needed.extend(data_issues)

    # Update state
    state["clarifications_needed"] = clarifications_needed
    state["awaiting_clarification"] = len(clarifications_needed) > 0

    if clarifications_needed:
        logger.info(f"ClarificationNode: {len(clarifications_needed)} clarifications needed")
        state["current_step"] = "awaiting_clarification"
        # Add to reasoning trace
        if "reasoning_trace" not in state or state["reasoning_trace"] is None:
            state["reasoning_trace"] = []
        state["reasoning_trace"].append({
            "step": "clarification",
            "reasoning": f"Need clarification on {len(clarifications_needed)} points",
            "questions": clarifications_needed
        })
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
        "bitcoin", "btc", "ethereum", "eth", "daily", "weekly", "month",
        "technical indicators", "sentiment analysis", "price movements"
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
    if "coin" not in goal_lower and "btc" not in goal_lower and "bitcoin" not in goal_lower:
        questions.append("Which cryptocurrency would you like to analyze? (e.g., Bitcoin, Ethereum)")

    # Timeframe
    if not any(t in goal_lower for t in ["day", "week", "month", "year", "daily", "weekly"]):
        questions.append("What time period should I analyze? (e.g., last 30 days, last 3 months)")

    # Analysis type
    if "predict" in goal_lower or "forecast" in goal_lower:
        questions.append("What would you like to predict? (e.g., price direction, volatility, trading signals)")

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
        issues.append("No data was retrieved. Would you like to adjust the time period or data sources?")
        return issues

    # Check each data type
    for data_type, data in retrieved_data.items():
        if data_type == "price_data":
            if isinstance(data, list) and len(data) < 10:
                issues.append(f"Only {len(data)} price data points found. Would you like to expand the time range?")

        elif data_type == "sentiment_data":
            if isinstance(data, list) and len(data) < 5:
                issues.append(f"Limited sentiment data available ({len(data)} records). Should I proceed with price data only?")

    return issues


def handle_clarification_response(
    state: dict[str, Any],
    responses: dict[str, str]
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

    # Store responses in state
    if "clarifications_provided" not in state:
        state["clarifications_provided"] = {}

    state["clarifications_provided"].update(responses)

    # Update user goal with clarifications
    clarified_goal = _incorporate_clarifications(
        state.get("user_goal", ""),
        responses
    )

    state["user_goal"] = clarified_goal
    state["awaiting_clarification"] = False
    state["clarifications_needed"] = []
    state["current_step"] = "planning"

    # Add to reasoning trace
    if "reasoning_trace" not in state or state["reasoning_trace"] is None:
        state["reasoning_trace"] = []

    state["reasoning_trace"].append({
        "step": "clarification_received",
        "responses": responses,
        "updated_goal": clarified_goal
    })

    logger.info(f"ClarificationNode: Updated goal: {clarified_goal}")

    return state


def _incorporate_clarifications(
    original_goal: str,
    clarifications: dict[str, str]
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
    clarification_text = " ".join([
        f"{response}" for response in clarifications.values()
    ])

    enhanced_goal = f"{original_goal}. {clarification_text}"

    return enhanced_goal
