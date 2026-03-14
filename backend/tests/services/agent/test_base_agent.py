import pytest
from unittest.mock import AsyncMock, patch
from typing import Any
from app.services.agent.agents.base import BaseAgent

class MockAgent(BaseAgent):
    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        return state

@pytest.mark.asyncio
async def test_emit_event_sequence_and_timestamp():
    agent = MockAgent(name="Test", description="Test")
    state = {"session_id": "test_session", "sequence_id": 5}
    
    with patch("app.services.agent.agents.base.manager") as mock_manager:
        mock_manager.broadcast_json = AsyncMock()
        
        await agent.emit_event(state, "status_update", "TEST_STAGE", {"status": "ACTIVE"})
        
        # Verify sequence_id increment
        assert state["sequence_id"] == 6
        
        # Verify call
        mock_manager.broadcast_json.assert_called_once()
        call_args = mock_manager.broadcast_json.call_args
        event = call_args[0][0]
        channel_id = call_args[0][1]
        
        assert channel_id == "test_session"
        assert event["sequence_id"] == 6
        assert "timestamp" in event
        # Verify ISO format with Z
        assert event["timestamp"].endswith("Z")
        assert "T" in event["timestamp"]

@pytest.mark.asyncio
async def test_emit_event_mimetype_validation():
    agent = MockAgent(name="Test", description="Test")
    state = {"session_id": "test_session"}
    
    # Valid MimeType
    with patch("app.services.agent.agents.base.manager") as mock_manager:
        mock_manager.broadcast_json = AsyncMock()
        await agent.emit_event(state, "render_output", "TEST", {"mime_type": "text/markdown"})
        mock_manager.broadcast_json.assert_called_once()

    # Invalid MimeType
    with pytest.raises(ValueError, match="Invalid MimeType"):
        await agent.emit_event(state, "render_output", "TEST", {"mime_type": "invalid/type"})

@pytest.mark.asyncio
async def test_emit_event_no_session_id():
    agent = MockAgent(name="Test", description="Test")
    state = {} # No session_id
    
    with patch("app.services.agent.agents.base.manager") as mock_manager:
        mock_manager.broadcast_json = AsyncMock()
        await agent.emit_event(state, "status_update", "TEST", {})
        mock_manager.broadcast_json.assert_not_called()
