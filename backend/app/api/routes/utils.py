from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from pydantic.networks import EmailStr
from sqlmodel import select

from app.api.deps import SessionDep, get_current_active_superuser
from app.models import Message, PriceData5Min
from app.utils import generate_test_email, send_email

router = APIRouter(prefix="/utils", tags=["utils"])


class PriceDataPoint(BaseModel):
    """Price data point for charting"""

    timestamp: datetime
    coin_type: str
    price: float


class PriceDataResponse(BaseModel):
    """Response containing price data points"""

    data: list[PriceDataPoint]
    total_points: int


class AvailableCoinsResponse(BaseModel):
    """Available cryptocurrency symbols in the database"""

    coins: list[str]


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """
    Test emails.
    """
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.get("/health-check/")
async def health_check() -> bool:
    return True


@router.get("/available-coins/", response_model=AvailableCoinsResponse)
def get_available_coins(session: SessionDep) -> AvailableCoinsResponse:
    """
    Return distinct cryptocurrency symbols available in the price data.

    Used by the Data Explorer to populate the coin selection dropdown.
    """
    stmt = select(PriceData5Min.coin_type).distinct().order_by(PriceData5Min.coin_type)
    coins = list(session.exec(stmt).all())
    return AvailableCoinsResponse(coins=coins)


@router.get("/price-data/", response_model=PriceDataResponse)
def get_price_data(
    session: SessionDep,
    coin_type: str = Query(
        ..., description="Cryptocurrency symbol (e.g., 'BTC', 'ETH')"
    ),
    start_date: datetime | None = Query(None, description="Start date for price data"),
    end_date: datetime | None = Query(None, description="End date for price data"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    ledger: str | None = Query(
        None, description="Filter by ledger (glass, human, catalyst, exchange)"
    ),
) -> PriceDataResponse:
    """
    Fetch price data for a specific cryptocurrency within a date range.

    Returns price data points suitable for charting in the Data Explorer.
    """
    # Ledger filtering — currently only exchange ledger has price data
    if ledger is not None and ledger.lower() != "exchange":
        return PriceDataResponse(data=[], total_points=0)

    query = select(PriceData5Min).where(PriceData5Min.coin_type == coin_type.upper())

    if start_date:
        query = query.where(PriceData5Min.timestamp >= start_date)

    if end_date:
        query = query.where(PriceData5Min.timestamp <= end_date)

    # Order by timestamp ascending and limit
    query = query.order_by(PriceData5Min.timestamp).limit(limit)  # type: ignore[arg-type]

    records = session.exec(query).all()

    data_points = [
        PriceDataPoint(
            timestamp=record.timestamp,
            coin_type=record.coin_type,
            price=float(record.last),  # Use the 'last' traded price
        )
        for record in records
    ]

    return PriceDataResponse(data=data_points, total_points=len(data_points))
