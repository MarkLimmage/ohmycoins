import os
import time
import pandas as pd
from sqlalchemy import text
from app.core.db import engine
import logging

logger = logging.getLogger(__name__)

CACHE_DIR = "/tmp/omc_lab_cache"

class PipelineManager:
    """
    Manages data pipeline for the Lab using Parquet caching based on row counts.
    Scope: Parquet Row-Count Caching
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR, exist_ok=True)

    def export_mv_to_parquet(self, mv_name: str, force_refresh: bool = False) -> str:
        """
        Exports a Materialized View to a Parquet file, using row-count validation for caching.
        
        Args:
            mv_name: Name of the materialized view (e.g., 'mv_training_set_v1')
            force_refresh: Ignore cache if True
            
        Returns:
            Absolute path to the cached Parquet file
        """
        cache_path = os.path.join(CACHE_DIR, f"{mv_name}.parquet")
        
        # 1. Get current row count from DB
        try:
            with engine.connect() as conn:
                count_query = text(f"SELECT COUNT(*) FROM {mv_name}")
                current_count = conn.execute(count_query).scalar()
        except Exception as e:
            logger.error(f"Failed to get row count for {mv_name}: {e}")
            # If we utilize fallback or error out depends on strictness. 
            # For now, let's assume we need DB access.
            raise e

        # 2. Check cache validity
        is_valid = False
        if os.path.exists(cache_path) and not force_refresh:
            try:
                # Read metadata only to get row count (fast)
                # pyarrow.parquet.read_metadata is faster but requires pyarrow
                # pandas read_parquet with columns=[] might still read data?
                # Let's just use os.path.getsize > 0 as a rough check and verify row count
                # Ideally we store metadata in a sidecar file or rely on Parquet metadata
                
                # Reading just the metadata using pandas (engine='pyarrow')
                # But to be safe and simple: read the file and check len? 
                # No, that defeats the purpose of "fast check".
                # A sidecar file with row count is safer.
                meta_path = cache_path + ".meta"
                if os.path.exists(meta_path):
                    with open(meta_path, "r") as f:
                        cached_count = int(f.read().strip())
                    
                    if current_count == cached_count:
                        is_valid = True
                        logger.info(f"Cache HIT for {mv_name} (rows={current_count})")
            except Exception as e:
                logger.warning(f"Cache check failed for {mv_name}: {e}")

        if is_valid:
            return cache_path

        # 3. Regenerate Cache
        logger.info(f"Cache MISS or INVALID for {mv_name}. Regenerating...")
        try:
            query = text(f"SELECT * FROM {mv_name}")
            df = pd.read_sql(query, engine)
            
            # Save Parquet
            df.to_parquet(cache_path, index=False)
            
            # Save Metadata (Row Count)
            with open(cache_path + ".meta", "w") as f:
                f.write(str(len(df)))
                
            logger.info(f"Cached {mv_name} to {cache_path} (rows={len(df)})")
            return cache_path
        except Exception as e:
            logger.error(f"Failed to export {mv_name}: {e}")
            raise e
