import os
import time

import pandas as pd  # type: ignore[import-untyped]
from sqlmodel import Session, text

from app.core.db import engine

CACHE_DIR = "/tmp/omc_data_cache"
CACHE_EXPIRY = 3600  # 1 hour


class PipelineManager:
    """Manages data export from Materialized Views/DataFrames to Parquet files for Dagger execution."""

    BASE_DIR = "/tmp/omc_lab_sessions"

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_dir = os.path.join(self.BASE_DIR, session_id)
        os.makedirs(self.session_dir, exist_ok=True)
        os.makedirs(CACHE_DIR, exist_ok=True)

    def export_mv_to_parquet(
        self, mv_name: str, limit: int = 1000, force_refresh: bool = False
    ) -> str:
        """Query a Materialized View and save result as parquet with caching."""
        cache_path = os.path.join(CACHE_DIR, f"{mv_name}.parquet")

        is_valid = False
        if os.path.exists(cache_path) and not force_refresh:
            if time.time() - os.path.getmtime(cache_path) < CACHE_EXPIRY:
                is_valid = True

        if is_valid:
            return cache_path

        query = text(f"SELECT * FROM {mv_name} LIMIT {limit}")

        with Session(engine) as session:
            # Use connection.execute for raw SQL text
            result = session.connection().execute(query)
            # Use mappings for cleaner df creation or fetchall + keys
            df = pd.DataFrame(result.fetchall(), columns=result.keys())

        df.to_parquet(cache_path, index=False)
        return cache_path

    def save_dataframe(self, df: pd.DataFrame, name: str) -> str:
        """Save a DataFrame to the session directory for Dagger use."""
        file_path = os.path.join(self.session_dir, f"{name}.parquet")
        df.to_parquet(file_path, index=False)
        return file_path
