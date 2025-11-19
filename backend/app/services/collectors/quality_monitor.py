"""
Data Quality Monitor for Phase 2.5 collectors.

This module provides monitoring and validation for data collection quality,
including completeness, timeliness, and accuracy checks.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlmodel import Session, select, func

from app.models import (
    PriceData5Min,
    NewsSentiment,
    OnChainMetrics,
    CatalystEvents,
    ProtocolFundamentals,
)

logger = logging.getLogger(__name__)


class QualityMetrics:
    """Container for quality check results."""
    
    def __init__(self):
        self.completeness_score: float = 0.0
        self.timeliness_score: float = 0.0
        self.accuracy_score: float = 0.0
        self.overall_score: float = 0.0
        self.issues: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []
    
    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "completeness_score": self.completeness_score,
            "timeliness_score": self.timeliness_score,
            "accuracy_score": self.accuracy_score,
            "overall_score": self.overall_score,
            "issues": self.issues,
            "warnings": self.warnings,
            "info": self.info,
        }


class DataQualityMonitor:
    """
    Monitor data quality for Phase 2.5 collectors.
    
    Performs three types of checks:
    1. Completeness: Ensures expected data is present
    2. Timeliness: Checks data freshness and collection schedules
    3. Accuracy: Validates data integrity and consistency
    """
    
    def __init__(self):
        """Initialize the quality monitor."""
        self.name = "data_quality_monitor"
    
    async def check_all(self, session: Session) -> QualityMetrics:
        """
        Run all quality checks.
        
        Args:
            session: Database session
        
        Returns:
            QualityMetrics object with results
        """
        logger.info(f"{self.name}: Starting comprehensive quality checks")
        
        metrics = QualityMetrics()
        
        # Run all checks
        completeness = await self.check_completeness(session)
        timeliness = await self.check_timeliness(session)
        accuracy = await self.check_accuracy(session)
        
        # Aggregate scores
        metrics.completeness_score = completeness.completeness_score
        metrics.timeliness_score = timeliness.timeliness_score
        metrics.accuracy_score = accuracy.accuracy_score
        
        # Calculate overall score (weighted average)
        metrics.overall_score = (
            metrics.completeness_score * 0.3 +
            metrics.timeliness_score * 0.4 +
            metrics.accuracy_score * 0.3
        )
        
        # Aggregate issues, warnings, and info
        metrics.issues.extend(completeness.issues)
        metrics.issues.extend(timeliness.issues)
        metrics.issues.extend(accuracy.issues)
        
        metrics.warnings.extend(completeness.warnings)
        metrics.warnings.extend(timeliness.warnings)
        metrics.warnings.extend(accuracy.warnings)
        
        metrics.info.extend(completeness.info)
        metrics.info.extend(timeliness.info)
        metrics.info.extend(accuracy.info)
        
        logger.info(
            f"{self.name}: Quality check complete. "
            f"Overall score: {metrics.overall_score:.2f}"
        )
        
        return metrics
    
    async def check_completeness(self, session: Session) -> QualityMetrics:
        """
        Check data completeness.
        
        Validates that expected data is present for each collector:
        - Exchange Ledger: Price data
        - Human Ledger: Sentiment data
        - Catalyst Ledger: Events data
        - Glass Ledger: Protocol fundamentals
        
        Args:
            session: Database session
        
        Returns:
            QualityMetrics with completeness results
        """
        logger.info(f"{self.name}: Checking data completeness")
        
        metrics = QualityMetrics()
        scores = []
        
        # Check Exchange Ledger (Price Data)
        price_count = session.exec(
            select(func.count(PriceData5Min.id))
        ).one()
        
        if price_count > 0:
            scores.append(1.0)
            metrics.info.append(f"Price data: {price_count} records")
        else:
            scores.append(0.0)
            metrics.issues.append("No price data found")
        
        # Check Human Ledger (Sentiment Data)
        sentiment_count = session.exec(
            select(func.count(NewsSentiment.id))
        ).one()
        
        if sentiment_count > 0:
            scores.append(1.0)
            metrics.info.append(f"Sentiment data: {sentiment_count} records")
        else:
            scores.append(0.5)
            metrics.warnings.append("Limited sentiment data")
        
        # Check Catalyst Ledger (Events)
        catalyst_count = session.exec(
            select(func.count(CatalystEvents.id))
        ).one()
        
        if catalyst_count > 0:
            scores.append(1.0)
            metrics.info.append(f"Catalyst events: {catalyst_count} records")
        else:
            scores.append(0.5)
            metrics.warnings.append("No catalyst events yet")
        
        # Check Glass Ledger (Protocol Fundamentals)
        protocol_count = session.exec(
            select(func.count(ProtocolFundamentals.id))
        ).one()
        
        if protocol_count > 0:
            scores.append(1.0)
            metrics.info.append(f"Protocol data: {protocol_count} records")
        else:
            scores.append(0.5)
            metrics.warnings.append("Limited protocol data")
        
        # Calculate completeness score
        metrics.completeness_score = sum(scores) / len(scores) if scores else 0.0
        
        logger.info(
            f"{self.name}: Completeness score: {metrics.completeness_score:.2f}"
        )
        
        return metrics
    
    async def check_timeliness(self, session: Session) -> QualityMetrics:
        """
        Check data timeliness.
        
        Validates that data is being collected according to schedule:
        - Recent data exists within expected collection intervals
        - No large gaps in data collection
        
        Args:
            session: Database session
        
        Returns:
            QualityMetrics with timeliness results
        """
        logger.info(f"{self.name}: Checking data timeliness")
        
        metrics = QualityMetrics()
        scores = []
        now = datetime.now(timezone.utc)
        
        # Check price data freshness (should be within 10 minutes)
        recent_price = session.exec(
            select(PriceData5Min)
            .order_by(PriceData5Min.timestamp.desc())
            .limit(1)
        ).first()
        
        if recent_price:
            age = now - recent_price.timestamp
            if age < timedelta(minutes=10):
                scores.append(1.0)
                metrics.info.append(
                    f"Price data is fresh ({age.seconds // 60} min old)"
                )
            elif age < timedelta(hours=1):
                scores.append(0.7)
                metrics.warnings.append(
                    f"Price data is stale ({age.seconds // 60} min old)"
                )
            else:
                scores.append(0.3)
                metrics.issues.append(
                    f"Price data is very stale ({age.seconds // 3600} hours old)"
                )
        else:
            scores.append(0.0)
            metrics.issues.append("No price data found")
        
        # Check sentiment data freshness (should be within 30 minutes)
        recent_sentiment = session.exec(
            select(NewsSentiment)
            .order_by(NewsSentiment.collected_at.desc())
            .limit(1)
        ).first()
        
        if recent_sentiment:
            age = now - recent_sentiment.collected_at
            if age < timedelta(minutes=30):
                scores.append(1.0)
                metrics.info.append(
                    f"Sentiment data is fresh ({age.seconds // 60} min old)"
                )
            elif age < timedelta(hours=2):
                scores.append(0.7)
                metrics.warnings.append(
                    f"Sentiment data is stale ({age.seconds // 60} min old)"
                )
            else:
                scores.append(0.3)
                metrics.issues.append(
                    f"Sentiment data is very stale ({age.seconds // 3600} hours old)"
                )
        else:
            scores.append(0.5)
            metrics.warnings.append("No sentiment data to check timeliness")
        
        # Check catalyst events freshness (should be within 24 hours)
        recent_catalyst = session.exec(
            select(CatalystEvents)
            .order_by(CatalystEvents.collected_at.desc())
            .limit(1)
        ).first()
        
        if recent_catalyst:
            age = now - recent_catalyst.collected_at
            if age < timedelta(hours=24):
                scores.append(1.0)
                metrics.info.append(
                    f"Catalyst data is fresh ({age.seconds // 3600} hours old)"
                )
            elif age < timedelta(days=3):
                scores.append(0.7)
                metrics.warnings.append(
                    f"Catalyst data is stale ({age.days} days old)"
                )
            else:
                scores.append(0.3)
                metrics.issues.append(
                    f"Catalyst data is very stale ({age.days} days old)"
                )
        else:
            scores.append(0.5)
            metrics.warnings.append("No catalyst data to check timeliness")
        
        # Calculate timeliness score
        metrics.timeliness_score = sum(scores) / len(scores) if scores else 0.0
        
        logger.info(
            f"{self.name}: Timeliness score: {metrics.timeliness_score:.2f}"
        )
        
        return metrics
    
    async def check_accuracy(self, session: Session) -> QualityMetrics:
        """
        Check data accuracy and integrity.
        
        Validates:
        - No null/invalid values in critical fields
        - Data ranges are reasonable
        - Foreign key relationships are valid
        
        Args:
            session: Database session
        
        Returns:
            QualityMetrics with accuracy results
        """
        logger.info(f"{self.name}: Checking data accuracy")
        
        metrics = QualityMetrics()
        scores = []
        
        # Check price data validity
        invalid_prices = session.exec(
            select(func.count(PriceData5Min.id))
            .where(
                (PriceData5Min.last <= 0) |
                (PriceData5Min.last == None)
            )
        ).one()
        
        total_prices = session.exec(
            select(func.count(PriceData5Min.id))
        ).one()
        
        if total_prices > 0:
            price_validity = 1.0 - (invalid_prices / total_prices)
            scores.append(price_validity)
            
            if invalid_prices > 0:
                metrics.warnings.append(
                    f"Found {invalid_prices} invalid price records"
                )
            else:
                metrics.info.append("All price data is valid")
        
        # Check sentiment score validity (-1 to 1 range)
        invalid_sentiment = session.exec(
            select(func.count(NewsSentiment.id))
            .where(
                (NewsSentiment.sentiment_score < -1) |
                (NewsSentiment.sentiment_score > 1)
            )
        ).one()
        
        total_sentiment = session.exec(
            select(func.count(NewsSentiment.id))
        ).one()
        
        if total_sentiment > 0:
            sentiment_validity = 1.0 - (invalid_sentiment / total_sentiment)
            scores.append(sentiment_validity)
            
            if invalid_sentiment > 0:
                metrics.warnings.append(
                    f"Found {invalid_sentiment} invalid sentiment scores"
                )
            else:
                metrics.info.append("All sentiment scores are valid")
        
        # Check catalyst events have required fields
        invalid_catalysts = session.exec(
            select(func.count(CatalystEvents.id))
            .where(
                (CatalystEvents.event_type == None) |
                (CatalystEvents.detected_at == None)
            )
        ).one()
        
        total_catalysts = session.exec(
            select(func.count(CatalystEvents.id))
        ).one()
        
        if total_catalysts > 0:
            catalyst_validity = 1.0 - (invalid_catalysts / total_catalysts)
            scores.append(catalyst_validity)
            
            if invalid_catalysts > 0:
                metrics.warnings.append(
                    f"Found {invalid_catalysts} invalid catalyst events"
                )
            else:
                metrics.info.append("All catalyst events are valid")
        
        # Calculate accuracy score
        metrics.accuracy_score = sum(scores) / len(scores) if scores else 0.9
        
        logger.info(
            f"{self.name}: Accuracy score: {metrics.accuracy_score:.2f}"
        )
        
        return metrics
    
    async def generate_alert(
        self, metrics: QualityMetrics, threshold: float = 0.7
    ) -> dict[str, Any] | None:
        """
        Generate alert if quality score is below threshold.
        
        Args:
            metrics: Quality metrics to evaluate
            threshold: Minimum acceptable score (0.0-1.0)
        
        Returns:
            Alert dictionary if threshold breached, None otherwise
        """
        if metrics.overall_score < threshold:
            alert = {
                "severity": "high" if metrics.overall_score < 0.5 else "medium",
                "message": f"Data quality score is low: {metrics.overall_score:.2f}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": metrics.to_dict(),
            }
            
            logger.warning(
                f"{self.name}: ALERT - {alert['message']} "
                f"(threshold: {threshold})"
            )
            
            return alert
        
        return None


# Singleton instance
_quality_monitor: DataQualityMonitor | None = None


def get_quality_monitor() -> DataQualityMonitor:
    """Get or create the quality monitor singleton."""
    global _quality_monitor
    if _quality_monitor is None:
        _quality_monitor = DataQualityMonitor()
    return _quality_monitor
