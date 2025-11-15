from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel, Column
from sqlalchemy import DECIMAL, DateTime, Index
import sqlalchemy as sa


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)
    # OMC-specific profile fields
    timezone: str | None = Field(default="UTC", max_length=50)
    preferred_currency: str | None = Field(default="AUD", max_length=10)
    risk_tolerance: str | None = Field(default="medium", max_length=20)  # low, medium, high
    trading_experience: str | None = Field(default="beginner", max_length=20)  # beginner, intermediate, advanced


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
    # OMC-specific profile updates
    timezone: str | None = Field(default=None, max_length=50)
    preferred_currency: str | None = Field(default=None, max_length=10)
    risk_tolerance: str | None = Field(default=None, max_length=20)
    trading_experience: str | None = Field(default=None, max_length=20)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    coinspot_credentials: "CoinspotCredentials" | None = Relationship(
        back_populates="user", sa_relationship_kwargs={"uselist": False}
    )


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# ============================================================================
# User Profile Models (Phase 2) - Extended profile with trading preferences
# ============================================================================

class UserProfilePublic(SQLModel):
    """Public user profile response with OMC-specific fields"""
    email: str
    full_name: str | None = None
    timezone: str
    preferred_currency: str
    risk_tolerance: str
    trading_experience: str
    has_coinspot_credentials: bool = False


class UserProfileUpdate(SQLModel):
    """User profile update request with validation"""
    full_name: str | None = Field(default=None, max_length=255)
    timezone: str | None = Field(default=None, max_length=50)
    preferred_currency: str | None = Field(default=None, max_length=10)
    risk_tolerance: str | None = Field(default=None, max_length=20)
    trading_experience: str | None = Field(default=None, max_length=20)
    
    @property
    def validate_fields(self) -> None:
        """Validate profile fields"""
        if self.risk_tolerance and self.risk_tolerance not in ["low", "medium", "high"]:
            raise ValueError("risk_tolerance must be one of: low, medium, high")
        if self.trading_experience and self.trading_experience not in ["beginner", "intermediate", "advanced"]:
            raise ValueError("trading_experience must be one of: beginner, intermediate, advanced")


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
    bid: Decimal = Field(sa_column=Column(DECIMAL(precision=20, scale=8)))
    ask: Decimal = Field(sa_column=Column(DECIMAL(precision=20, scale=8)))
    last: Decimal = Field(sa_column=Column(DECIMAL(precision=20, scale=8)))


# Database model for 5-minute price data
class PriceData5Min(PriceDataBase, table=True):
    """
    Stores cryptocurrency price data collected every 5 minutes from Coinspot.
    
    This table serves as the foundation for backtesting and algorithm development
    in The Lab.
    """
    __tablename__ = "price_data_5min"
    
    id: int | None = Field(default=None, primary_key=True)
    timestamp: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
        description="UTC timestamp when data was collected"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Timestamp when record was inserted into database"
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
    id: int
    timestamp: datetime
    created_at: datetime


# List response
class PriceData5MinList(SQLModel):
    """Paginated list of price data"""
    data: list[PriceData5MinPublic]
    count: int


# ============================================================================
# Coinspot Credentials Models (Phase 2)
# ============================================================================

# Shared properties for Coinspot credentials
class CoinspotCredentialsBase(SQLModel):
    """Base model for Coinspot API credentials"""
    is_validated: bool = False


# Database model for Coinspot credentials
class CoinspotCredentials(CoinspotCredentialsBase, table=True):
    """
    Stores encrypted Coinspot API credentials for users.
    
    Credentials are encrypted at rest using Fernet (AES-256).
    The api_key and api_secret are stored as encrypted bytes.
    """
    __tablename__ = "coinspot_credentials"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE", unique=True
    )
    api_key_encrypted: bytes = Field(sa_column=Column(sa.LargeBinary, nullable=False))
    api_secret_encrypted: bytes = Field(sa_column=Column(sa.LargeBinary, nullable=False))
    last_validated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    
    # Relationships
    user: User = Relationship(back_populates="coinspot_credentials")


# Properties to receive via API on creation
class CoinspotCredentialsCreate(SQLModel):
    """Schema for creating Coinspot credentials"""
    api_key: str = Field(min_length=1, max_length=255)
    api_secret: str = Field(min_length=1, max_length=255)


# Properties to receive via API on update
class CoinspotCredentialsUpdate(SQLModel):
    """Schema for updating Coinspot credentials"""
    api_key: str | None = Field(default=None, min_length=1, max_length=255)
    api_secret: str | None = Field(default=None, min_length=1, max_length=255)


# Properties to return via API (masked for security)
class CoinspotCredentialsPublic(CoinspotCredentialsBase):
    """Schema for returning Coinspot credentials via API (with masked values)"""
    id: uuid.UUID
    user_id: uuid.UUID
    api_key_masked: str = Field(description="Masked API key (last 4 characters visible)")
    is_validated: bool
    last_validated_at: datetime | None
    created_at: datetime
    updated_at: datetime

