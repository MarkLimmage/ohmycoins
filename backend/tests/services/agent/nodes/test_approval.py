"""Tests for approval node."""

import pytest
from app.services.agent.nodes.approval import (
    approval_node,
    handle_approval_granted,
    handle_approval_rejected,
    _determine_approval_type,
    _requires_approval,
)


class TestApprovalNode:
    """Tests for approval_node function."""
    
    def test_approval_for_data_retrieval(self):
        """Test that data retrieval requires approval in manual mode."""
        state = {
            "current_step": "data_retrieval",
            "approval_mode": "manual",
            "approval_gates": ["before_data_fetch"]
        }
        
        result = approval_node(state)
        
        assert result["approval_needed"] is True
        assert len(result["pending_approvals"]) == 1
        assert result["pending_approvals"][0]["approval_type"] == "before_data_fetch"
    
    def test_approval_for_training(self):
        """Test that training requires approval when configured."""
        state = {
            "current_step": "model_training",
            "approval_mode": "manual",
            "approval_gates": ["before_training"]
        }
        
        result = approval_node(state)
        
        assert result["approval_needed"] is True
        assert result["pending_approvals"][0]["approval_type"] == "before_training"
    
    def test_deployment_always_requires_approval(self):
        """Test that deployment always requires approval."""
        state = {
            "current_step": "deployment",
            "approval_mode": "auto",  # Even in auto mode
            "approval_gates": []
        }
        
        result = approval_node(state)
        
        assert result["approval_needed"] is True
        assert result["pending_approvals"][0]["approval_type"] == "before_deployment"
    
    def test_auto_approval_mode(self):
        """Test that auto mode skips approvals except deployment."""
        state = {
            "current_step": "model_training",
            "approval_mode": "auto",
            "approval_gates": ["before_training"]
        }
        
        result = approval_node(state)
        
        assert result["approval_needed"] is False
        assert "approvals_granted" in result
    
    def test_no_approval_needed_for_analysis(self):
        """Test that data analysis doesn't require approval by default."""
        state = {
            "current_step": "data_analysis",
            "approval_mode": "manual",
            "approval_gates": []
        }
        
        result = approval_node(state)
        
        assert result["approval_needed"] is False


class TestDetermineApprovalType:
    """Tests for _determine_approval_type helper function."""
    
    def test_data_retrieval_step(self):
        """Test that data_retrieval step maps to before_data_fetch."""
        assert _determine_approval_type("data_retrieval") == "before_data_fetch"
    
    def test_model_training_step(self):
        """Test that model_training step maps to before_training."""
        assert _determine_approval_type("model_training") == "before_training"
    
    def test_deployment_step(self):
        """Test that deployment step maps to before_deployment."""
        assert _determine_approval_type("deployment") == "before_deployment"
    
    def test_unknown_step(self):
        """Test that unknown step returns None."""
        assert _determine_approval_type("unknown_step") is None
    
    def test_partial_match(self):
        """Test that partial match works."""
        assert _determine_approval_type("awaiting_model_training") == "before_training"


class TestRequiresApproval:
    """Tests for _requires_approval helper function."""
    
    def test_deployment_always_requires(self):
        """Test that deployment always requires approval."""
        assert _requires_approval("before_deployment", [], "auto") is True
        assert _requires_approval("before_deployment", [], "manual") is True
    
    def test_auto_mode_skips_non_deployment(self):
        """Test that auto mode skips non-deployment approvals."""
        assert _requires_approval("before_training", ["before_training"], "auto") is False
    
    def test_manual_mode_checks_gates(self):
        """Test that manual mode checks approval gates."""
        assert _requires_approval("before_training", ["before_training"], "manual") is True
        assert _requires_approval("before_training", [], "manual") is False
    
    def test_gate_not_in_list(self):
        """Test that approval not in gates is not required."""
        assert _requires_approval("before_data_fetch", ["before_training"], "manual") is False


class TestHandleApprovalGranted:
    """Tests for handle_approval_granted function."""
    
    def test_grants_approval(self):
        """Test that approval is granted and recorded."""
        state = {
            "approval_needed": True,
            "pending_approvals": [{"approval_type": "before_training"}]
        }
        
        result = handle_approval_granted(state, "before_training")
        
        assert result["approval_needed"] is False
        assert result["pending_approvals"] == []
        assert len(result["approvals_granted"]) > 0
        assert result["approvals_granted"][0]["approval_type"] == "before_training"
    
    def test_updates_current_step(self):
        """Test that current step is updated after approval."""
        state = {
            "approval_needed": True,
            "pending_approvals": [{"approval_type": "before_training"}]
        }
        
        result = handle_approval_granted(state, "before_training")
        
        assert result["current_step"] == "model_training"
    
    def test_updates_reasoning_trace(self):
        """Test that approval is recorded in reasoning trace."""
        state = {
            "approval_needed": True,
            "reasoning_trace": []
        }
        
        result = handle_approval_granted(state, "before_data_fetch")
        
        assert "reasoning_trace" in result
        assert len(result["reasoning_trace"]) > 0
        assert result["reasoning_trace"][-1]["step"] == "approval_granted"


class TestHandleApprovalRejected:
    """Tests for handle_approval_rejected function."""
    
    def test_rejects_approval(self):
        """Test that approval rejection stops workflow."""
        state = {
            "approval_needed": True,
            "pending_approvals": [{"approval_type": "before_training"}]
        }
        
        result = handle_approval_rejected(state, "before_training", "User decided not to proceed")
        
        assert result["approval_needed"] is False
        assert result["status"] == "stopped"
        assert result["current_step"] == "stopped_by_user"
        assert "User decided not to proceed" in result["error"]
    
    def test_records_reason(self):
        """Test that rejection reason is recorded."""
        state = {
            "approval_needed": True,
            "pending_approvals": [{"approval_type": "before_deployment"}]
        }
        
        reason = "Model accuracy too low"
        result = handle_approval_rejected(state, "before_deployment", reason)
        
        assert reason in result["error"]
    
    def test_updates_reasoning_trace(self):
        """Test that rejection is recorded in reasoning trace."""
        state = {
            "approval_needed": True,
            "reasoning_trace": []
        }
        
        result = handle_approval_rejected(state, "before_training", "Not ready")
        
        assert "reasoning_trace" in result
        assert len(result["reasoning_trace"]) > 0
        assert result["reasoning_trace"][-1]["step"] == "approval_rejected"
        assert result["reasoning_trace"][-1]["reason"] == "Not ready"
    
    def test_clears_pending_approvals(self):
        """Test that pending approvals are cleared on rejection."""
        state = {
            "approval_needed": True,
            "pending_approvals": [{"approval_type": "before_training"}]
        }
        
        result = handle_approval_rejected(state, "before_training")
        
        assert result["pending_approvals"] == []
