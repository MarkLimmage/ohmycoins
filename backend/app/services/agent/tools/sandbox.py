from app.services.agent.pipeline import PipelineManager
from app.services.agent.execution import SandboxExecutor

async def execute_sandbox_code(session_id: str, code: str, mv_name: str = None) -> dict:
    """
    Orchestrates data pipeline and code execution.
    """
    data_path = None
    if mv_name:
        pipeline = PipelineManager(session_id)
        data_path = pipeline.export_mv_to_parquet(mv_name)
    
    executor = SandboxExecutor()
    result = await executor.execute_code(code, data_path)
    
    return result
