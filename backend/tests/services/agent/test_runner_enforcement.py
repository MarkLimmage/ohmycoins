import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.agent.runner import AgentRunner


@pytest.mark.asyncio
async def test_runner_priority_node_action_request():
    """
    Verify F2/F5 Enforcement:
    If a node emits an action_request, the runner MUST use it and NOT overwrite it
    with a generic 'approve_{node}' request.
    """
    runner = AgentRunner()
    runner.session_manager = AsyncMock()
    runner._orchestrator = AsyncMock()
    runner._orchestrator.checkpointer = MagicMock()
    runner._publish = AsyncMock()
    runner._get_redis = AsyncMock()
    runner._get_checkpointer = AsyncMock()

    session_id = uuid.uuid4()
    mock_workflow = MagicMock()

    # Define a custom action request from the node
    node_action_request = {
        "event_type": "action_request",
        "stage": "MODELING",
        "sequence_id": 100, # Will be overwritten by runner logic but used for detection
        "payload": {
            "action_id": "custom_node_action_v1",
            "description": "Custom node request",
            "options": ["OPTION_A", "OPTION_B"]
        }
    }

    # Mock stream_execute to yield a state update with pending_events
    async def mock_stream_execute(initial_state, **kwargs):
        # Yield a state update for "train_model" node containing the event
        yield {
            "train_model": {
                "pending_events": [node_action_request],
                "current_step": "train_model"
            }
        }

    mock_workflow.stream_execute = mock_stream_execute
    mock_workflow.graph.aget_state = AsyncMock()
    # Simulate interrupt happening after this node
    mock_workflow.graph.aget_state.return_value.next = ("train_model",)

    with patch("app.services.agent.langgraph_workflow.LangGraphWorkflow", return_value=mock_workflow), \
         patch("app.services.agent.runner.DBSession") as mock_db_cls, \
         patch("app.services.agent.runner.engine"):

        mock_db = MagicMock()
        mock_db_cls.return_value.__enter__.return_value = mock_db

        # Mock add_message to return a message with a sequence_id
        mock_msg = MagicMock()
        mock_msg.sequence_id = 101
        mock_msg.created_at.isoformat.return_value = "2026-03-20T10:00:00Z"
        runner.session_manager.add_message.return_value = mock_msg

        # Mock sequence_id query
        mock_db.exec.return_value.one.return_value = 10

        # Mock session
        mock_session = MagicMock()
        mock_session.user_id = uuid.uuid4()
        runner.session_manager.get_session.return_value = mock_session

        await runner.run_session(session_id)

        # Verification:
        # The runner should have published the node's action request
        # AND when handling the interrupt, it should use the node's action details
        # instead of generating a generic "approve_train_model".

        # 1. Verify we did NOT publish a generic "approve_train_model" action
        for call in runner._publish.call_args_list:
            args = call.args
            if len(args) >= 3:
                msg = args[2]
                if msg.get("event_type") == "action_request":
                    # If this is the one from the loop (node emitted)
                    if msg["payload"]["action_id"] == "custom_node_action_v1":
                        continue

                    # If this is the one from the interrupt block
                    # It SHOULD be the same "custom_node_action_v1" if logic works
                    # OR it might be a duplicate publication if logic is "publish again".
                    # But CRITICALLY, it should NOT be "approve_train_model"

                    assert msg["payload"]["action_id"] != "approve_train_model", \
                        "Runner overwrote node action with generic 'approve_train_model'"

        # 2. Verify we published the custom action at least once
        custom_action_published = False
        for call in runner._publish.call_args_list:
            args = call.args
            msg = args[2]
            if msg.get("event_type") == "action_request" and \
               msg["payload"]["action_id"] == "custom_node_action_v1":
                custom_action_published = True

        assert custom_action_published, "Custom node action was not published"
