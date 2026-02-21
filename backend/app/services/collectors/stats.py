
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from sqlmodel import Session, select, func, col
from app.models import CollectorRuns, Collector

class CollectorStatsService:
    """
    Service to aggregate and report statistics on collector performance.
    Used for the Operations Dashboard and Signal Pipeline monitoring.
    """
    
    def __init__(self, session: Session):
        self.session = session

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Returns a high-level summary for the dashboard:
        - Active Collectors count
        - Total Items Collected (last 24h)
        - Error Rate (last 24h)
        - Sparkline data (Items/Minute for last 60 mins)
        """
        now = datetime.now(timezone.utc)
        start_24h = now - timedelta(hours=24)
        
        # 1. Active Collectors
        total_collectors = self.session.exec(select(func.count(Collector.id)).where(Collector.is_enabled == True)).one()
        
        # 2. Total Items (24h)
        total_items = self.session.exec(
            select(func.sum(CollectorRuns.records_collected))
            .where(CollectorRuns.started_at >= start_24h)
        ).one() or 0
        
        # 3. Error Rate (24h)
        total_runs = self.session.exec(
            select(func.count(CollectorRuns.id))
            .where(CollectorRuns.started_at >= start_24h)
        ).one()
        
        failed_runs = self.session.exec(
            select(func.count(CollectorRuns.id))
            .where(CollectorRuns.started_at >= start_24h)
            .where(CollectorRuns.status != "success")
        ).one()
        
        error_rate = (failed_runs / total_runs * 100) if total_runs > 0 else 0
        
        # 4. Sparkline Data (Last 60 mins, grouped by minute)
        sparkline = self._get_throughput_sparkline()
        
        return {
            "active_collectors": total_collectors,
            "total_items_24h": total_items,
            "error_rate_24h": round(error_rate, 2),
            "sparkline": sparkline
        }

    def _get_throughput_sparkline(self) -> List[Dict[str, Any]]:
        """
        Returns records collected per minute for the last 60 minutes.
        """
        now = datetime.now(timezone.utc)
        start_60m = now - timedelta(minutes=60)
        
        # Define the truncated date expression
        minute_trunc = func.date_trunc('minute', CollectorRuns.completed_at)
        
        query = (
            select(
                minute_trunc.label('minute'),
                func.sum(func.coalesce(CollectorRuns.records_collected, 0)).label('count')
            )
            .where(CollectorRuns.completed_at >= start_60m)
            .group_by(minute_trunc)
            .order_by(minute_trunc)
        )
        
        results = self.session.exec(query).all()
        
        # Format for frontend
        data = [{"time": r.minute.isoformat(), "value": r.count} for r in results if r.minute]
        
        # Fill gaps with 0? Or let frontend handle it. 
        # Let's return sparse data for now.
        return data

    def get_collector_health(self) -> List[Dict[str, Any]]:

        """
        Returns a list of all collectors with their current health status.
        Status: 'healthy', 'warning', 'error', 'disabled'
        """
        collectors = self.session.exec(select(Collector)).all()
        results = []
        
        for collector in collectors:
            if not collector.is_enabled:
                health = "disabled"
            elif collector.status == "error":
                health = "error"
            else:
                # Check last run
                last_run = self.session.exec(
                    select(CollectorRuns)
                    .where(CollectorRuns.collector_name == collector.name)
                    .order_by(CollectorRuns.started_at.desc())
                    .limit(1)
                ).first()
                
                if last_run and last_run.status == "failed":
                    health = "error"
                else:
                    health = "healthy"
            
            results.append({
                "name": collector.name,
                "plugin_name": collector.plugin_name,
                "status": health,
                "last_run": collector.last_run_at,
                "schedule": collector.schedule_cron
            })
            
        return results

    def get_throughput_stats(self, time_window_minutes: int = 60) -> dict:
        """
        Returns the total number of items collected across all collectors
        in the last `time_window_minutes`.
        """
        # This requires querying the actual data tables (NewsItem, Signal, etc.)
        # OR relying on CollectorRuns.records_collected if populated reliably.
        # Phase 2.5 architecture suggests relying on CollectorRuns metadata.
        
        # Calculate start time
        # timestamp = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        # However, SQLModel func.sum might be easier.
        
        # Sum records_collected from successful runs
        
        # ... implementation to be refined based on exact dashboard needs
        pass
        
    def get_recent_runs(self, limit: int = 50) -> List[CollectorRuns]:
        """Returns the most recent collector execution logs."""
        statement = select(CollectorRuns).order_by(CollectorRuns.started_at.desc()).limit(limit)
        return self.session.exec(statement).all()
