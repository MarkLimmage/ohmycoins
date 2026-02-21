from app.services.collectors.metrics import get_metrics_tracker
from datetime import datetime, timezone
from typing import Any

class CollectorStatsService:
    """
    Aggregates collector metrics for the dashboard.
    """
    
    def get_dashboard_stats(self) -> dict[str, Any]:

        tracker = get_metrics_tracker()
        metrics = tracker.get_all_metrics()
        
        system = metrics["system"]
        uptime_seconds = system["uptime_seconds"]
        uptime_minutes = uptime_seconds / 60.0
        
        collector_stats = []
        for name, data in metrics["collectors"].items():
            total_items = data.get("total_records_collected", 0)
            items_per_min = total_items / uptime_minutes if uptime_minutes > 0.1 else 0.0
            
            collector_stats.append({
                "name": name,
                "items_per_minute": round(items_per_min, 2),
                "error_count": data.get("failed_runs", 0),
                "last_run": data.get("last_run_at"),
                "success_rate": data.get("success_rate", 0.0)
            })
            
        return {
            "system_uptime_seconds": uptime_seconds,
            "collectors": collector_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
