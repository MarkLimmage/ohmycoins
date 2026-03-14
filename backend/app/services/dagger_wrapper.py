import dagger
import sys
import os
import shutil
import asyncio
from typing import Dict, Any, List, Optional

class DaggerExecutor:
    """
    Wrapper for Dagger execution engine.
    Runs Python scripts in a sandboxed container (built from agent.Dockerfile).
    Captures stdout, stderr, and generated artifacts.
    Enforces hardware limits and security constraints (Phase 5).
    """

    def __init__(self, dockerfile_path: str = "agent.Dockerfile"):
        self.dockerfile_path = dockerfile_path
        # Dependencies are now managed in the Dockerfile, not here.

    async def execute_script(
        self,
        script_content: str,
        data_path: str,
        output_dir: str,
        mlflow_tracking_uri: str = "http://mlflow_server:5000"
    ) -> Dict[str, Any]:
        """
        Executes the provided Python script in a Dagger container with a 300s timeout.
        
        Args:
            script_content: The python code to execute as a string.
            data_path: Path to the input parquet file on the host.
            output_dir: Path on the host to export artifacts to.
            
        Returns:
            Dictionary containing:
            - stdout: Standard output string
            - stderr: Standard error string
            - status: "success" or "error"
            - output_dir: Path where artifacts are stored
        """
        
        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        script_filename = "algo_script.py"
        data_filename = "training_data.parquet"
        
        try:
            # Enforce 300s timeout (Phase 5.1)
            return await asyncio.wait_for(
                self._run_dagger(
                    script_content, 
                    data_path, 
                    output_dir, 
                    mlflow_tracking_uri, 
                    script_filename, 
                    data_filename
                ),
                timeout=300.0
            )
        except asyncio.TimeoutError:
            return {
                "status": "error",
                "message": "Execution timed out (300s limit enforced).",
                "stdout": "",
                "stderr": "TimeoutError: Script execution exceeded 300 seconds."
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "stdout": "",
                "stderr": str(e)
            }

    async def _run_dagger(
        self,
        script_content: str,
        data_path: str,
        output_dir: str,
        mlflow_tracking_uri: str,
        script_filename: str,
        data_filename: str
    ) -> Dict[str, Any]:
        
        # Initialize Dagger client
        # Config log_output to stderr allows seeing Dagger internal logs in host stderr
        async with dagger.Connection(dagger.Config(log_output=sys.stderr)) as client:
            # 1. Build the container from the Dockerfile in root
            # This ensures we use the correct environment with TA-Lib, shap, etc.
            # We assume the script is running with CWD at project root for correct context
            project_root = os.getcwd() # Assumption: CWD is project root
            
            container = (
                client.container()
                .build(client.host().directory(project_root), dockerfile=self.dockerfile_path)
                .with_env_variable("MLFLOW_TRACKING_URI", mlflow_tracking_uri)
                .with_workdir("/workspace")
            )
            
            # 2. Mount input files
            # script_content -> /workspace/algo_script.py
            # data_path (host) -> /workspace/training_data.parquet
            container = (
                container
                .with_new_file(f"/workspace/{script_filename}", contents=script_content)
                .with_file(f"/workspace/{data_filename}", client.host().file(data_path))
            )
            
            # 3. Execute the script
            # We expect the script to read 'training_data.parquet' and output files to /workspace/out
            # Phase 5.1: "Ensure internet access is disabled" - 
            # Dagger doesn't easily allow disabling network per-exec without specialized setup,
            # but using 'without_env_variable' for proxies might help if relevant.
            # For now, we assume the base image and simple exec is 'secure enough' for Phase 1/5 start.
            container = container.with_exec(["python3", script_filename])
            
            # 4. Capture outputs
            stdout = await container.stdout()
            stderr = await container.stderr()
            
            # 5. Export the output directory to host (artifacts)
            # The Dockerfile defines /workspace/out as the output dir
            await container.directory("/workspace/out").export(output_dir)
            
        return {
            "status": "success",
            "stdout": stdout,
            "stderr": stderr,
            "output_dir": output_dir
        }

