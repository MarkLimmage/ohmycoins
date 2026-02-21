# mypy: ignore-errors
"""
Choice Presentation Node for Human-in-the-Loop workflow.

This node presents multiple options to the user with pros/cons analysis,
allowing them to make informed decisions about model selection and parameters.
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


def choice_presentation_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Present model choices to the user with comparison analysis.

    This node is triggered when multiple models have been trained
    or when there are different hyperparameter configurations to choose from.

    Args:
        state: Current workflow state with trained_models or evaluation_results

    Returns:
        Updated state with choices_available and awaiting_choice fields
    """
    logger.info("ChoicePresentationNode: Analyzing models for comparison")

    trained_models = state.get("trained_models", {})
    evaluation_results = state.get("evaluation_results", {})

    if not trained_models or not evaluation_results:
        logger.info("ChoicePresentationNode: No models to compare, skipping")
        state["awaiting_choice"] = False
        return state

    # Generate choice comparison
    choices = _generate_model_choices(trained_models, evaluation_results)

    if len(choices) <= 1:
        logger.info(
            "ChoicePresentationNode: Only one model available, no choice needed"
        )
        state["awaiting_choice"] = False
        # Auto-select the single model
        if choices:
            state["selected_choice"] = choices[0]["model_name"]
        return state

    # Generate recommendations using LLM
    recommendation = _generate_recommendation(choices)

    # Update state
    state["choices_available"] = choices
    state["awaiting_choice"] = True
    state["current_step"] = "awaiting_choice"
    state["recommendation"] = recommendation

    # Add to reasoning trace
    if "reasoning_trace" not in state or state["reasoning_trace"] is None:
        state["reasoning_trace"] = []

    state["reasoning_trace"].append(
        {
            "step": "choice_presentation",
            "num_choices": len(choices),
            "recommendation": recommendation,
        }
    )

    logger.info(f"ChoicePresentationNode: Presenting {len(choices)} choices to user")

    return state


def _generate_model_choices(
    trained_models: dict[str, Any], evaluation_results: dict[str, Any]
) -> list[dict[str, Any]]:
    """
    Generate structured choices from trained models and their evaluations.

    Args:
        trained_models: Dictionary of trained models
        evaluation_results: Dictionary of evaluation metrics

    Returns:
        List of choice dictionaries with model info, metrics, and pros/cons
    """
    choices = []

    for model_name, model_info in trained_models.items():
        # Get evaluation metrics for this model
        metrics = evaluation_results.get(model_name, {})

        # Extract key metrics
        accuracy = metrics.get("accuracy", 0.0)
        training_time = metrics.get("training_time", 0.0)
        complexity = _estimate_model_complexity(model_name)

        # Generate pros and cons
        pros, cons = _generate_pros_cons(model_name, metrics)

        choice = {
            "model_name": model_name,
            "model_type": model_info.get("type", "unknown"),
            "accuracy": accuracy,
            "training_time": training_time,
            "complexity": complexity,
            "pros": pros,
            "cons": cons,
            "metrics": metrics,
            "parameters": model_info.get("parameters", {}),
        }

        choices.append(choice)

    # Sort by accuracy (descending)
    choices.sort(key=lambda x: x["accuracy"], reverse=True)

    return choices


def _estimate_model_complexity(model_name: str) -> str:
    """
    Estimate model complexity based on model type.

    Args:
        model_name: Name of the model

    Returns:
        Complexity level: "low", "medium", or "high"
    """
    model_lower = model_name.lower()

    if any(term in model_lower for term in ["logistic", "linear"]):
        return "low"
    elif any(term in model_lower for term in ["random_forest", "svm", "decision_tree"]):
        return "medium"
    elif any(term in model_lower for term in ["xgboost", "neural", "deep"]):
        return "high"
    else:
        return "medium"


def _generate_pros_cons(
    model_name: str, metrics: dict[str, Any]
) -> tuple[list[str], list[str]]:
    """
    Generate pros and cons for a model based on its characteristics and metrics.

    Args:
        model_name: Name of the model
        metrics: Evaluation metrics

    Returns:
        Tuple of (pros, cons) lists
    """
    pros = []
    cons = []

    model_lower = model_name.lower()
    accuracy = metrics.get("accuracy", 0.0)
    training_time = metrics.get("training_time", 0.0)

    # Performance-based pros/cons
    if accuracy > 0.85:
        pros.append(f"High accuracy ({accuracy:.2%})")
    elif accuracy < 0.70:
        cons.append(f"Lower accuracy ({accuracy:.2%})")

    if training_time < 5:
        pros.append(f"Fast training ({training_time:.1f}s)")
    elif training_time > 30:
        cons.append(f"Slow training ({training_time:.1f}s)")

    # Model-specific characteristics
    if "logistic" in model_lower or "linear" in model_lower:
        pros.append("Simple and interpretable")
        pros.append("Fast predictions")
        cons.append("Limited for complex patterns")

    elif "random_forest" in model_lower:
        pros.append("Handles non-linear relationships well")
        pros.append("Built-in feature importance")
        cons.append("Larger model size")

    elif "xgboost" in model_lower:
        pros.append("State-of-the-art performance")
        pros.append("Handles missing data well")
        cons.append("Requires careful tuning")
        cons.append("Longer training time")

    elif "svm" in model_lower:
        pros.append("Effective for high-dimensional data")
        cons.append("Sensitive to parameter tuning")
        cons.append("Slower with large datasets")

    # Fallback if no specific pros/cons identified
    if not pros:
        pros.append("Standard performance")
    if not cons:
        cons.append("No major drawbacks identified")

    return pros, cons


def _generate_recommendation(choices: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Generate a recommendation for which model to use.

    Args:
        choices: List of model choices with metrics

    Returns:
        Recommendation dictionary with selected model and reasoning
    """
    if not choices:
        return {
            "recommended_model": None,
            "reasoning": "No models available for recommendation",
            "confidence": 0.0,
        }

    # Initialize LLM for recommendation
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY,
    )

    # Prepare comparison data
    comparison_text = _format_choices_for_llm(choices)

    system_message = SystemMessage(
        content="""
You are an expert machine learning consultant. Analyze the model comparison
and provide a recommendation. Consider:
1. Accuracy (most important for production)
2. Training time (important for iteration speed)
3. Model complexity (simpler is better if accuracy is similar)
4. Pros and cons

Provide your recommendation in this format:
RECOMMENDED: [model_name]
REASONING: [brief explanation]
CONFIDENCE: [0.0-1.0]
"""
    )

    human_message = HumanMessage(content=comparison_text)

    try:
        response = llm.invoke([system_message, human_message])
        recommendation = _parse_llm_recommendation(response.content, choices)
    except Exception as e:
        logger.error(f"ChoicePresentationNode: Error generating recommendation: {e}")
        # Fallback to simple heuristic
        recommendation = _simple_recommendation(choices)

    return recommendation


def _format_choices_for_llm(choices: list[dict[str, Any]]) -> str:
    """Format choices for LLM analysis."""
    lines = ["Model Comparison:"]
    for i, choice in enumerate(choices, 1):
        lines.append(f"\n{i}. {choice['model_name']}")
        lines.append(f"   Accuracy: {choice['accuracy']:.2%}")
        lines.append(f"   Training Time: {choice['training_time']:.1f}s")
        lines.append(f"   Complexity: {choice['complexity']}")
        lines.append(f"   Pros: {', '.join(choice['pros'])}")
        lines.append(f"   Cons: {', '.join(choice['cons'])}")

    return "\n".join(lines)


def _parse_llm_recommendation(
    llm_response: str, _choices: list[dict[str, Any]]
) -> dict[str, Any]:
    """Parse LLM recommendation response."""
    lines = llm_response.strip().split("\n")

    recommended_model = None
    reasoning = ""
    confidence = 0.8  # Default

    for line in lines:
        if line.startswith("RECOMMENDED:"):
            recommended_model = line.split(":", 1)[1].strip()
        elif line.startswith("REASONING:"):
            reasoning = line.split(":", 1)[1].strip()
        elif line.startswith("CONFIDENCE:"):
            try:
                confidence = float(line.split(":", 1)[1].strip())
            except ValueError:
                confidence = 0.8

    return {
        "recommended_model": recommended_model,
        "reasoning": reasoning,
        "confidence": confidence,
    }


def _simple_recommendation(choices: list[dict[str, Any]]) -> dict[str, Any]:
    """Simple heuristic-based recommendation as fallback."""
    # Choose model with highest accuracy
    best_model = max(choices, key=lambda x: x["accuracy"])

    return {
        "recommended_model": best_model["model_name"],
        "reasoning": f"Highest accuracy ({best_model['accuracy']:.2%}) with {best_model['complexity']} complexity",
        "confidence": 0.7,
    }


def handle_choice_selection(
    state: dict[str, Any], selected_model: str
) -> dict[str, Any]:
    """
    Process user's model selection.

    Args:
        state: Current workflow state
        selected_model: Name of the model selected by user

    Returns:
        Updated state with selected_choice
    """
    logger.info(f"ChoicePresentationNode: User selected {selected_model}")

    state["selected_choice"] = selected_model
    state["awaiting_choice"] = False
    state["choices_available"] = []
    state["current_step"] = "model_selected"

    # Add to reasoning trace
    if "reasoning_trace" not in state or state["reasoning_trace"] is None:
        state["reasoning_trace"] = []

    state["reasoning_trace"].append(
        {"step": "choice_selected", "selected_model": selected_model}
    )

    return state
