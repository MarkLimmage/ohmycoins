from datetime import datetime, timezone

from pydantic import BaseModel, Field


class APIResponseBase(BaseModel):
    """
    Base model for all API responses supporting UI loading states.
    Follows API_CONTRACTS.md Global Patterns.
    """

    is_loading: bool = Field(
        default=False,
        description="Indicates if the data is currently being refreshed or computed.",
    )
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the data was last updated.",
    )
    data_staleness_seconds: float = Field(
        default=0.0, description="Number of seconds since the data was last updated."
    )
