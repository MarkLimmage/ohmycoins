"""
Agent service module for Phase 3 Agentic Data Science Capability.

This module contains the autonomous multi-agent system for algorithm development.
"""

from .orchestrator import AgentOrchestrator
from .session_manager import SessionManager

__all__ = ["SessionManager", "AgentOrchestrator"]
