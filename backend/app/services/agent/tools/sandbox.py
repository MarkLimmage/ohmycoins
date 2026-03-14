from typing import Any

from app.services.agent.execution import SandboxExecutor
from app.services.agent.pipeline import PipelineManager


async def execute_sandbox_code(
    session_id: str, code: str, mv_name: str | None = None
) -> dict[str, Any]:
    """
    Orchestrates data pipeline and code execution.
    """
    data_path = None
    if mv_name:
        pipeline = PipelineManager(session_id)
        data_path = pipeline.export_mv_to_parquet(mv_name)

    executor = SandboxExecutor()
    # If data_path is None, executor.execute_code should handle it (or strict hint issue)
    result = await executor.execute_code(code, data_path)

    return result
