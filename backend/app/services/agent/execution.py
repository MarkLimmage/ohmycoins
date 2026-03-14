import sys
import os
from typing import Any, Dict, List, Optional
import glob

from app.services.dagger_wrapper import DaggerExecutor

class SandboxExecutor:
    """Executes Python code inside a Dagger container using DaggerExecutor."""

    def __init__(self) -> None:
        self.dagger_executor = DaggerExecutor()

    async def execute_code(
        self, 
        code: str, 
        data_path: Optional[str],
        output_dir: str = "/tmp/omc_artifacts"
    ) -> Dict[str, Any]:
        """
        Run code in sandbox via DaggerExecutor.
        Returns: {stdout, stderr, artifact_paths, status}
        """
        
        result = await self.dagger_executor.execute_script(
            script_content=code,
            data_path=data_path,
            output_dir=output_dir
        )
        
        # List generated artifacts
        artifacts = []
        if result.get("status") == "success":
            # List files in output_dir
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    artifacts.append(os.path.join(root, file))
        
        return {
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "artifact_paths": artifacts, # Changed from 'artifacts' list of dicts to list of paths
            "status": result.get("status", "error"),
            "message": result.get("message", "")
        }

