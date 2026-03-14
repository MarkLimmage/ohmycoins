import sys
from typing import Any

import dagger


class SandboxExecutor:
    """Executes Python code inside a Dagger container."""

    async def execute_code(
        self, code: str, data_path: str | None = None
    ) -> dict[str, Any]:
        """
        Run code in sandbox.
        Returns: {stdout, stderr, artifacts}
        """
        async with dagger.Connection(dagger.Config(log_output=sys.stderr)) as client:
            # Load base image
            container = client.container().from_("omc-agent-base:latest")

            # Mount data if provided
            if data_path:
                container = container.with_mounted_file(
                    "/workspace/data.parquet", client.host().file(data_path)
                )

            # Run code
            # We wrap the user code in a script
            script_content = f"""
import pandas as pd
if os.path.exists('/workspace/data.parquet'):
    df = pd.read_parquet('/workspace/data.parquet')
{code}
            """

            container = container.with_new_file(
                "/workspace/script.py", contents=script_content
            ).with_exec(["python3", "/workspace/script.py"])

            # Capture output
            stdout = await container.stdout()
            stderr = await container.stderr()

            # Artifact extraction (mock for now, real implementation would export files)
            artifacts: list[dict[str, Any]] = []

            return {"stdout": stdout, "stderr": stderr, "artifacts": artifacts}
