"""Tests for clarification node."""

import pytest
from app.services.agent.nodes.clarification import (
    clarification_node,
    handle_clarification_response,
    _is_goal_ambiguous,
    _generate_template_questions,
    _check_data_quality,
)


class TestClarificationNode:
    """Tests for clarification_node function."""
    
    def test_clarification_node_with_ambiguous_goal(self):
        """Test that clarification node detects ambiguous goals."""
        state = {
            "user_goal": "predict prices",  # Ambiguous - no coin or timeframe
            "retrieved_data": None,
        }
        
        result = clarification_node(state)
        
        assert result["awaiting_clarification"] is True
        assert len(result["clarifications_needed"]) > 0
        assert "reasoning_trace" in result
    
    def test_clarification_node_with_specific_goal(self):
        """Test that clarification node accepts specific goals."""
        state = {
            "user_goal": "predict Bitcoin prices for the next 30 days using daily data",
            "retrieved_data": None,
        }
        
        result = clarification_node(state)
        
        # Should not need clarification for specific goal
        assert result.get("awaiting_clarification", False) is False
    
    def test_clarification_node_with_data_quality_issues(self):
        """Test that clarification node detects data quality issues."""
        state = {
            "user_goal": "predict Bitcoin prices",
            "retrieved_data": {
                "price_data": []  # Empty data - quality issue
            },
        }
        
        result = clarification_node(state)
        
        assert result["awaiting_clarification"] is True
        assert any("data" in q.lower() for q in result["clarifications_needed"])


class TestIsGoalAmbiguous:
    """Tests for _is_goal_ambiguous helper function."""
    
    def test_ambiguous_goal_predict(self):
        """Test that vague 'predict' goal is ambiguous."""
        assert _is_goal_ambiguous("predict prices") is True
    
    def test_ambiguous_goal_analyze(self):
        """Test that vague 'analyze' goal is ambiguous."""
        assert _is_goal_ambiguous("analyze trading") is True
    
    def test_specific_goal_with_coin(self):
        """Test that goal with specific coin is not ambiguous."""
        assert _is_goal_ambiguous("predict Bitcoin prices") is False
    
    def test_specific_goal_with_timeframe(self):
        """Test that goal with timeframe is not ambiguous."""
        assert _is_goal_ambiguous("predict daily prices") is False
    
    def test_long_descriptive_goal(self):
        """Test that long, descriptive goal is not ambiguous."""
        goal = "I want to predict cryptocurrency price movements using technical indicators and sentiment analysis"
        assert _is_goal_ambiguous(goal) is False


class TestGenerateTemplateQuestions:
    """Tests for _generate_template_questions helper function."""
    
    def test_generates_coin_question(self):
        """Test that coin question is generated when no coin specified."""
        questions = _generate_template_questions("predict prices")
        
        assert any("cryptocurrency" in q.lower() or "coin" in q.lower() for q in questions)
    
    def test_generates_timeframe_question(self):
        """Test that timeframe question is generated when no timeframe specified."""
        questions = _generate_template_questions("predict Bitcoin")
        
        assert any("time" in q.lower() or "period" in q.lower() for q in questions)
    
    def test_generates_prediction_type_question(self):
        """Test that prediction type question is generated for predict goal."""
        questions = _generate_template_questions("predict prices")
        
        assert any("predict" in q.lower() for q in questions)


class TestCheckDataQuality:
    """Tests for _check_data_quality helper function."""
    
    def test_empty_data(self):
        """Test that empty data is flagged."""
        issues = _check_data_quality({})
        
        assert len(issues) > 0
        assert any("no data" in issue.lower() for issue in issues)
    
    def test_insufficient_price_data(self):
        """Test that insufficient price data is flagged."""
        issues = _check_data_quality({
            "price_data": [1, 2, 3]  # Only 3 points, less than 10 minimum
        })
        
        assert len(issues) > 0
        assert any("price" in issue.lower() for issue in issues)
    
    def test_limited_sentiment_data(self):
        """Test that limited sentiment data is flagged."""
        issues = _check_data_quality({
            "price_data": list(range(20)),  # Sufficient price data
            "sentiment_data": [1, 2]  # Only 2 points, less than 5 minimum
        })
        
        assert len(issues) > 0
        assert any("sentiment" in issue.lower() for issue in issues)
    
    def test_sufficient_data(self):
        """Test that sufficient data has no issues."""
        issues = _check_data_quality({
            "price_data": list(range(100)),
            "sentiment_data": list(range(20))
        })
        
        assert len(issues) == 0


class TestHandleClarificationResponse:
    """Tests for handle_clarification_response function."""
    
    def test_incorporates_clarifications(self):
        """Test that clarifications are incorporated into state."""
        state = {
            "user_goal": "predict prices",
            "awaiting_clarification": True,
            "clarifications_needed": ["Which coin?", "What timeframe?"],
        }
        
        responses = {
            "Which coin?": "Bitcoin",
            "What timeframe?": "Next 30 days"
        }
        
        result = handle_clarification_response(state, responses)
        
        assert result["awaiting_clarification"] is False
        assert result["clarifications_needed"] == []
        assert "Bitcoin" in result["user_goal"]
        assert "30 days" in result["user_goal"]
    
    def test_updates_reasoning_trace(self):
        """Test that clarification response is recorded in reasoning trace."""
        state = {
            "user_goal": "predict prices",
            "awaiting_clarification": True,
            "reasoning_trace": [],
        }
        
        responses = {"Which coin?": "Bitcoin"}
        
        result = handle_clarification_response(state, responses)
        
        assert "reasoning_trace" in result
        assert len(result["reasoning_trace"]) > 0
        assert result["reasoning_trace"][-1]["step"] == "clarification_received"
    
    def test_stores_clarifications_provided(self):
        """Test that clarifications are stored in state."""
        state = {
            "user_goal": "predict prices",
            "awaiting_clarification": True,
        }
        
        responses = {"Which coin?": "Ethereum"}
        
        result = handle_clarification_response(state, responses)
        
        assert "clarifications_provided" in result
        assert result["clarifications_provided"]["Which coin?"] == "Ethereum"
