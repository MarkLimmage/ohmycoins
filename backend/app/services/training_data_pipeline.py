import os
import tempfile
import pandas as pd # type: ignore
from sqlalchemy import text
from app.core.db import engine

def export_training_data_to_parquet() -> str:
    """
    Queries mv_training_set_v1 and saves the result to a parquet file in a temp directory.
    Returns the absolute path to the parquet file.
    """
    query = text("SELECT * FROM mv_training_set_v1")
    
    # Use Pandas to execute the query and fetch data
    # We use a connection from the engine
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp(prefix="omc_training_data_")
    file_path = os.path.join(temp_dir, "training_data.parquet")
    
    # Save to parquet
    # Ensure pyarrow or fastparquet is installed (added to pyproject.toml)
    df.to_parquet(file_path, index=False)
    
    return file_path
