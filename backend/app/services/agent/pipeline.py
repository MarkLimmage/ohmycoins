import os
import uuid
import pandas as pd
from datetime import datetime
from sqlmodel import Session, text
from app.core.db import engine

class PipelineManager:
    """Manages data export from Materialized Views to Parquet files for Dagger execution."""
    
    BASE_DIR = "/tmp/omc_lab_sessions"

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_dir = os.path.join(self.BASE_DIR, session_id)
        os.makedirs(self.session_dir, exist_ok=True)

    def export_mv_to_parquet(self, mv_name: str, limit: int = 1000) -> str:
        """Query a Materialized View and save result as parquet."""
        query = text(f"SELECT * FROM {mv_name} LIMIT {limit}")
        
        with Session(engine) as session:
            result = session.exec(query)
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        
        file_path = os.path.join(self.session_dir, f"{mv_name}.parquet")
        df.to_parquet(file_path)
        return file_path
