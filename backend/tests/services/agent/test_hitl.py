import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models import AgentSessionStatus
from app.services.agent.runner import AgentRunner

# We don't import LangGraphWorkflow to avoid side effects, we mock it

@pytest.mark.asyncio
async def test_runner_interrupt_detection():
    runner = AgentRunner()
    runner.session_manager = AsyncMock()
    runner.orchestrator = AsyncMock()
    runner.orchestrator.checkpointer = MagicMock()
    runner._publish = AsyncMock()
    runner._get_redis = AsyncMock()

    session_id = uuid.uuid4()

    mock_workflow = MagicMock()

    # Mock stream_execute to yield nothing (simulate immediate interrupt or end)
    async def mock_stream_execute(initial_state, **kwargs):
        if False: yield {}

    mock_workflow.stream_execute = mock_stream_execute
    mock_workflow.graph.aget_state = AsyncMock()
    mock_workflow.graph.aget_state.return_value.next = ("train_model",)

    # We patch the class where it is defined, because runner imports it locally
    with patch("app.services.agent.langgraph_workflow.LangGraphWorkflow", return_value=mock_workflow), \
         patch("app.services.agent.runner.DBSession") as mock_db_cls, \
         patch("app.services.agent.runner.engine"):

        mock_db = MagicMock()
        mock_db_cls.return_value.__enter__.return_value = mock_db

        # Mock sequence_id query
        mock_db.exec.return_value.one.return_value = 10

        # Mock session
        mock_session = MagicMock()
        mock_session.user_id = uuid.uuid4()
        mock_session.llm_credential_id = None
        mock_session.user_goal = "test"
        runner.session_manager.get_session.return_value = mock_session

        await runner.run_session(session_id)

        # assertions
        runner.session_manager.update_session_status.assert_called_with(
            mock_db,
            session_id,
            AgentSessionStatus.AWAITING_APPROVAL,
            result_summary="Waiting for approval at train_model",
        )

        # Verify action request published
        # We need to check the calls to _publish
        assert runner._publish.called

        # Check if one of the calls was for action_request
        found = False
        for call in runner._publish.call_args_list:
            args = call.args
            if len(args) >= 3:
                msg = args[2]
                if msg.get("event_type") == "action_request":
                    found = True
                    assert msg["payload"]["action_id"] == "approve_train_model"
                    break
        assert found, "action_request event not found in publisher calls"
