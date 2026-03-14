import dagger
import sys
import os
import shutil
from typing import Dict, Any, List, Optional

class DaggerExecutor:
    """
    Wrapper for Dagger execution engine.
    Runs Python scripts in a sandboxed container (python:3.11-slim).
    Captures stdout, stderr, and generated artifacts.
    """

    def __init__(self, image: str = "python:3.11-slim"):
        self.image = image
        # Standard dependencies for ML tasks
        self.dependencies = [
            "pandas",
            "pyarrow",
            "scikit-learn",
            "joblib",
            "numpy"
        ]

    async def execute_script(
        self,
        script_content: str,
        data_path: str,
        output_dir: str
    ) -> Dict[str, Any]:
        """
        Executes the provided Python script in a Dagger container.
        
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
        
        # Initialize Dagger client
        # Config log_output to stderr allows seeing Dagger internal logs in host stderr
        try:
            async with dagger.Connection(dagger.Config(log_output=sys.stderr)) as client:
                # 1. Define the base container
                container = (
                    client.container()
                    .from_(self.image)
                    .with_exec(["pip", "install"] + self.dependencies)
                    .with_workdir("/app")
                )
                
                # 2. Mount input files
                # script_content -> /app/algo_script.py
                # data_path (host) -> /app/training_data.parquet
                container = (
                    container
                    .with_new_file(f"/app/{script_filename}", contents=script_content)
                    .with_file(f"/app/{data_filename}", client.host().file(data_path))
                )
                
                # 3. Execute the script
                # We expect the script to read 'training_data.parquet' and output files to current dir
                container = container.with_exec(["python", script_filename])
                
                # 4. Capture outputs
                stdout = await container.stdout()
                stderr = await container.stderr()
                
                # 5. Export the working directory to host (artifacts)
                # This exports everything in /app, including inputs
                await container.directory("/app").export(output_dir)
                
            # 6. Post-processing: Clean up input files from the output directory
            # We only want artifacts (e.g., .pkl, .json, .csv)
            files_to_remove = [script_filename, data_filename]
            for f in files_to_remove:
                p = os.path.join(output_dir, f)
                if os.path.exists(p):
                    os.remove(p)
            
            # Remove __pycache__
            pycache = os.path.join(output_dir, "__pycache__")
            if os.path.exists(pycache):
                shutil.rmtree(pycache)

            return {
                "stdout": stdout,
                "stderr": stderr,
                "status": "success",
                "output_dir": output_dir
            }

        except dagger.DaggerError as e:
            # Handle Dagger execution errors (e.g., script failure)
            return {
                "stdout": "",
                "stderr": str(e),
                "status": "error",
                "output_dir": output_dir
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": f"Unexpected error: {str(e)}",
                "status": "error",
                "output_dir": output_dir
            }
