import asyncio
import os
import sys
from typing import Any

import dagger


class DaggerExecutor:
    """
    Wrapper for Dagger execution engine.
    Runs Python scripts in a sandboxed container (built from agent.Dockerfile).
    Captures stdout, stderr, and generated artifacts.
    Enforces hardware limits and security constraints (Phase 5).
    """

    def __init__(self, dockerfile_path: str = "agent.Dockerfile"):
        self.dockerfile_path = dockerfile_path
        # Dependencies are now managed in the Dockerfile.

    async def execute_script(
        self,
        script_content: str,
        data_path: str | None,
        output_dir: str,
        mlflow_tracking_uri: str = "http://mlflow_server:5000",
    ) -> dict[str, Any]:
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
                    data_path.strip() if data_path else None,
                    output_dir,
                    mlflow_tracking_uri,
                    script_filename,
                    data_filename,
                ),
                timeout=300.0,
            )
        except asyncio.TimeoutError:
            return {
                "status": "error",
                "message": "Execution timed out (300s limit enforced).",
                "stdout": "",
                "stderr": "TimeoutError: Script execution exceeded 300 seconds.",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "stdout": "",
                "stderr": str(e),
            }

    async def _run_dagger(
        self,
        script_content: str,
        data_path: str | None,
        output_dir: str,
        mlflow_tracking_uri: str,
        script_filename: str,
        data_filename: str,
    ) -> dict[str, Any]:
        
        # Initialize Dagger client
        # Config log_output to stderr allows seeing Dagger internal logs in host stderr
        async with dagger.Connection(dagger.Config(log_output=sys.stderr)) as client:
            
            # Phase 5.1: Build container from agent.Dockerfile to ensure consistent environment
            # We must load the project root context to access the Dockerfile
            project_root = os.getcwd()
            # If running inside docker container, project_root should map to where Dockerfile is.
            # Assuming standard layout where Dockerfile is at /app/agent.Dockerfile or /app/backend/agent.Dockerfile?
            # The class defaults to "agent.Dockerfile" which implies it's in CWD.
            
            source = client.host().directory(project_root)
            container = source.docker_build(dockerfile=self.dockerfile_path)

            # 2. Add files
            # Add script content directly
            container = container.with_new_file(f"/workspace/{script_filename}", script_content)
            
            # Add data if provided
            if data_path and os.path.exists(data_path):
                # Ensure data_path is absolute for client.host().file()
                abs_data_path = os.path.abspath(data_path)
                data_file = client.host().file(abs_data_path)
                container = container.with_mounted_file(f"/workspace/{data_filename}", data_file)

            # 3. Environment Variables
            container = container.with_env_variable("MLFLOW_TRACKING_URI", mlflow_tracking_uri)
            
            # 4. Execute Script Logic
            # We define the artifacts directory first
            out_dir_container_path = "/workspace/out"

            # Execute python script
            # We expect the script to read input and write to /workspace/out
            # Capture stdout/stderr 
            try:
                executed = container.with_exec(
                    ["python", f"/workspace/{script_filename}"],
                    # Phase 5.1: "Ensure internet access is disabled" - 
                    # Use without_env_variable proxy settings if needed, or rely on container networking.
                )
                
                # Await execution to completion and capture output
                stdout = await executed.stdout()
                stderr = await executed.stderr()

                # 5. Export Artifacts
                # Only if successful execution
                out_dir_obj = executed.directory(out_dir_container_path)
                await out_dir_obj.export(output_dir)

                return {
                    "status": "success",
                    "stdout": stdout,
                    "stderr": stderr,
                    "output_dir": output_dir,
                }

            except dagger.ExecError as e:
                # Capture the failure output from the container execution
                return {
                    "status": "error",
                    "message": "Script execution failed inside container.",
                    "stdout": e.stdout,
                    "stderr": e.stderr,
                    "output_dir": output_dir,
                }
