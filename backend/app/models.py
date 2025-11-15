import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel, Column
from sqlalchemy import DECIMAL, DateTime, Index


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


# ============================================================================
# Price Data Models (The Collector)
# ============================================================================

# Shared properties for price data
class PriceDataBase(SQLModel):
    """Base model for cryptocurrency price data from Coinspot API"""
    coin_type: str = Field(index=True, max_length=20)
    bid: Decimal = Field(sa_column=Column(DECIMAL(precision=18, scale=8)))
    ask: Decimal = Field(sa_column=Column(DECIMAL(precision=18, scale=8)))
    last: Decimal = Field(sa_column=Column(DECIMAL(precision=18, scale=8)))


# Database model for 5-minute price data
class PriceData5Min(PriceDataBase, table=True):
    """
    Stores cryptocurrency price data collected every 5 minutes from Coinspot.
    
    This table serves as the foundation for backtesting and algorithm development
    in The Lab.
    """
    __tablename__ = "price_data_5min"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    timestamp: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
        description="UTC timestamp when data was collected"
    )
    
    __table_args__ = (
        # Composite index for efficient time-series queries
        Index('ix_price_data_5min_coin_timestamp', 'coin_type', 'timestamp'),
        # Unique constraint to prevent duplicate entries
        Index('uq_price_data_5min_coin_timestamp', 'coin_type', 'timestamp', unique=True),
    )


# Properties to receive via API on creation
class PriceData5MinCreate(PriceDataBase):
    """Schema for creating new price data entries"""
    timestamp: datetime


# Properties to return via API
class PriceData5MinPublic(PriceDataBase):
    """Schema for returning price data via API"""
    id: uuid.UUID
    timestamp: datetime


# List response
class PriceData5MinList(SQLModel):
    """Paginated list of price data"""
    data: list[PriceData5MinPublic]
    count: int

