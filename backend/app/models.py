from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from pydantic import EmailStr, field_validator
from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship, SQLModel, Column
from sqlalchemy import DECIMAL, DateTime, Index, JSON
from sqlalchemy.dialects import postgresql
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
    
    # Note: For SQLModel compatibility, we don't declare explicit back-populates here
    # Relationships are accessible via queries: session.exec(select(Position).where(Position.user_id == user.id))


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
    
    @field_validator('timezone')
    @classmethod
    def validate_timezone(cls, v: str | None) -> str | None:
        """Validate timezone field using pytz"""
        if v is not None:
            try:
                import pytz
                pytz.timezone(v)
            except pytz.exceptions.UnknownTimeZoneError:
                raise ValueError(f"Invalid timezone: {v}")
        return v
    
    @field_validator('preferred_currency')
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        """Validate currency field - must be 3-letter currency code"""
        if v is not None:
            # Common cryptocurrency and fiat currencies
            valid_currencies = {
                "AUD", "USD", "EUR", "GBP", "JPY", "CNY", "CAD", "NZD", "SGD",
                "BTC", "ETH", "USDT", "USDC", "BNB"
            }
            if v.upper() not in valid_currencies:
                raise ValueError(f"Invalid currency: {v}. Must be one of: {', '.join(sorted(valid_currencies))}")
        return v
    
    @field_validator('risk_tolerance')
    @classmethod
    def validate_risk_tolerance(cls, v: str | None) -> str | None:
        """Validate risk_tolerance field"""
        if v is not None and v not in ["low", "medium", "high"]:
            raise ValueError("risk_tolerance must be one of: low, medium, high")
        return v
    
    @field_validator('trading_experience')
    @classmethod
    def validate_trading_experience(cls, v: str | None) -> str | None:
        """Validate trading_experience field"""
        if v is not None and v not in ["beginner", "intermediate", "advanced"]:
            raise ValueError("trading_experience must be one of: beginner, intermediate, advanced")
        return v



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
    
    # Relationship to user (one-way, use queries to access from User)
    user: User = Relationship()


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


# ============================================================================
# User LLM Credentials Models (BYOM - Bring Your Own Model) - Sprint 2.8
# ============================================================================

class UserLLMCredentialsBase(SQLModel):
    """Base model for user LLM credentials"""
    provider: str = Field(max_length=20, nullable=False)  # openai, google, anthropic
    model_name: str | None = Field(default=None, max_length=100)  # gpt-4, gemini-1.5-pro, etc.
    is_default: bool = False  # Whether this is the user's default LLM
    is_active: bool = True  # Soft delete flag


# Database model for user LLM credentials
class UserLLMCredentials(UserLLMCredentialsBase, table=True):
    """
    Stores encrypted LLM API credentials for users (BYOM feature).
    
    Credentials are encrypted at rest using Fernet (AES-256).
    The api_key is stored as encrypted bytes.
    Users can configure multiple providers (OpenAI, Google Gemini, Anthropic Claude).
    """
    __tablename__ = "user_llm_credentials"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE", index=True
    )
    encrypted_api_key: bytes = Field(sa_column=Column(sa.LargeBinary, nullable=False))
    encryption_key_id: str | None = Field(default="default", max_length=50)  # For key rotation
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
    
    # Relationship to user (one-way, use queries to access from User)
    user: User = Relationship()


# Properties to receive via API on creation
class UserLLMCredentialsCreate(SQLModel):
    """Schema for creating user LLM credentials"""
    provider: str = Field(min_length=1, max_length=20, description="LLM provider: openai, google, anthropic")
    model_name: str | None = Field(default=None, max_length=100, description="Model name (e.g., gpt-4, gemini-1.5-pro)")
    api_key: str = Field(min_length=1, max_length=500, description="API key from the provider")
    is_default: bool = Field(default=False, description="Set as default LLM for this user")
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate provider field"""
        valid_providers = {"openai", "google", "anthropic"}
        if v.lower() not in valid_providers:
            raise ValueError(f"Provider must be one of: {', '.join(sorted(valid_providers))}")
        return v.lower()


# Properties to receive via API on update
class UserLLMCredentialsUpdate(SQLModel):
    """Schema for updating user LLM credentials"""
    model_name: str | None = Field(default=None, max_length=100)
    api_key: str | None = Field(default=None, min_length=1, max_length=500)
    is_default: bool | None = Field(default=None)
    is_active: bool | None = Field(default=None)


# Properties to return via API (masked for security)
class UserLLMCredentialsPublic(UserLLMCredentialsBase):
    """Schema for returning user LLM credentials via API (with masked API key)"""
    id: uuid.UUID
    user_id: uuid.UUID
    api_key_masked: str = Field(description="Masked API key (last 4 characters visible)")
    last_validated_at: datetime | None
    created_at: datetime
    updated_at: datetime


# Validation request/response models
class UserLLMCredentialsValidate(SQLModel):
    """Schema for validating an API key before saving"""
    provider: str = Field(description="LLM provider: openai, google, anthropic")
    api_key: str = Field(description="API key to validate")
    model_name: str | None = Field(default=None, description="Optional model name to test")
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate provider field"""
        valid_providers = {"openai", "google", "anthropic"}
        if v.lower() not in valid_providers:
            raise ValueError(f"Provider must be one of: {', '.join(sorted(valid_providers))}")
        return v.lower()


class UserLLMCredentialsValidationResult(SQLModel):
    """Response for API key validation"""
    is_valid: bool
    provider: str
    model_name: str | None = None
    error_message: str | None = None
    details: dict | None = None


# ============================================================================
# Comprehensive Data Collection Models (Phase 2.5 - The 4 Ledgers)
# ============================================================================

# Glass Ledger: Protocol Fundamentals
class ProtocolFundamentals(SQLModel, table=True):
    """
    Stores fundamental data for DeFi protocols (TVL, fees, revenue).
    Data source: DeFiLlama API
    """
    __tablename__ = "protocol_fundamentals"
    
    id: int | None = Field(default=None, primary_key=True)
    protocol: str = Field(max_length=50, nullable=False, index=True)
    tvl_usd: Decimal | None = Field(default=None, sa_column=Column(DECIMAL(precision=20, scale=2)))
    fees_24h: Decimal | None = Field(default=None, sa_column=Column(DECIMAL(precision=20, scale=2)))
    revenue_24h: Decimal | None = Field(default=None, sa_column=Column(DECIMAL(precision=20, scale=2)))
    collected_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
        description="UTC timestamp when data was collected"
    )
    
    __table_args__ = (
        # Unique constraint: one entry per protocol per day
        Index('uq_protocol_fundamentals_protocol_date', 
              'protocol', 
              sa.text("(collected_at::date)"),
              unique=True),
    )


# Glass Ledger: On-Chain Metrics
class OnChainMetrics(SQLModel, table=True):
    """
    Stores on-chain metrics (active addresses, transaction volumes, etc.).
    Data sources: Glassnode, Santiment (scraped from public dashboards)
    """
    __tablename__ = "on_chain_metrics"
    
    id: int | None = Field(default=None, primary_key=True)
    asset: str = Field(max_length=10, nullable=False, index=True)
    metric_name: str = Field(max_length=50, nullable=False, index=True)
    metric_value: Decimal = Field(sa_column=Column(DECIMAL(precision=30, scale=8)))
    source: str = Field(max_length=50, nullable=False)
    collected_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
        description="UTC timestamp when data was collected"
    )
    
    __table_args__ = (
        Index('ix_on_chain_metrics_asset_metric_time', 'asset', 'metric_name', 'collected_at'),
    )


# Human Ledger: News Sentiment
class NewsSentiment(SQLModel, table=True):
    """
    Stores cryptocurrency news articles with sentiment analysis.
    Data sources: CryptoPanic API, Newscatcher API
    """
    __tablename__ = "news_sentiment"
    
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(sa_column=Column(sa.Text, nullable=False))
    source: str | None = Field(default=None, max_length=100)
    url: str | None = Field(default=None, sa_column=Column(sa.Text, unique=True))
    published_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True))
    )
    sentiment: str | None = Field(default=None, max_length=20)
    sentiment_score: Decimal | None = Field(
        default=None,
        sa_column=Column(DECIMAL(precision=5, scale=4))
    )
    currencies: list[str] | None = Field(
        default=None,
        sa_column=Column(postgresql.ARRAY(sa.String()))
    )
    collected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True)
    )
    
    __table_args__ = (
        Index('ix_news_sentiment_published_at', 'published_at'),
    )


# Human Ledger: Social Sentiment
class SocialSentiment(SQLModel, table=True):
    """
    Stores social media sentiment data (Reddit, Twitter/X).
    Data sources: Reddit API, X scraper
    """
    __tablename__ = "social_sentiment"
    
    id: int | None = Field(default=None, primary_key=True)
    platform: str = Field(max_length=50, nullable=False, index=True)
    content: str | None = Field(default=None, sa_column=Column(sa.Text))
    author: str | None = Field(default=None, max_length=100)
    score: int | None = Field(default=None)
    sentiment: str | None = Field(default=None, max_length=20)
    currencies: list[str] | None = Field(
        default=None,
        sa_column=Column(postgresql.ARRAY(sa.String()))
    )
    posted_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True))
    )
    collected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True)
    )
    
    __table_args__ = (
        Index('ix_social_sentiment_platform_posted', 'platform', 'posted_at'),
    )


# Catalyst Ledger: Catalyst Events
class CatalystEvents(SQLModel, table=True):
    """
    Stores high-impact market events (SEC filings, exchange listings, etc.).
    Data sources: SEC API, CoinSpot announcements scraper
    """
    __tablename__ = "catalyst_events"
    
    id: int | None = Field(default=None, primary_key=True)
    event_type: str = Field(max_length=50, nullable=False, index=True)
    title: str = Field(sa_column=Column(sa.Text, nullable=False))
    description: str | None = Field(default=None, sa_column=Column(sa.Text))
    source: str | None = Field(default=None, max_length=100)
    currencies: list[str] | None = Field(
        default=None,
        sa_column=Column(postgresql.ARRAY(sa.String()))
    )
    impact_score: int | None = Field(
        default=None,
        sa_column=Column(sa.Integer, sa.CheckConstraint('impact_score >= 1 AND impact_score <= 10'))
    )
    detected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True)
    )
    url: str | None = Field(default=None, max_length=500)
    collected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    
    __table_args__ = (
        Index('ix_catalyst_events_type_detected', 'event_type', 'detected_at'),
    )


# Collector Metadata
class CollectorRuns(SQLModel, table=True):
    """
    Tracks collector execution history for monitoring and debugging.
    """
    __tablename__ = "collector_runs"
    
    id: int | None = Field(default=None, primary_key=True)
    collector_name: str = Field(max_length=100, nullable=False, index=True)
    status: str = Field(max_length=20, nullable=False, index=True)
    started_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    completed_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True))
    )
    records_collected: int | None = Field(default=None)
    error_message: str | None = Field(default=None, sa_column=Column(sa.Text))
    
    __table_args__ = (
        Index('ix_collector_runs_name_started', 'collector_name', 'started_at'),
    )


# API Response Models for Phase 2.5

class ProtocolFundamentalsPublic(SQLModel):
    """Public schema for protocol fundamentals"""
    id: int
    protocol: str
    tvl_usd: Decimal | None
    fees_24h: Decimal | None
    revenue_24h: Decimal | None
    collected_at: datetime


class OnChainMetricsPublic(SQLModel):
    """Public schema for on-chain metrics"""
    id: int
    asset: str
    metric_name: str
    metric_value: Decimal
    source: str
    collected_at: datetime


class NewsSentimentPublic(SQLModel):
    """Public schema for news sentiment"""
    id: int
    title: str
    source: str | None
    url: str | None
    published_at: datetime | None
    sentiment: str | None
    sentiment_score: Decimal | None
    currencies: list[str] | None
    collected_at: datetime


class SocialSentimentPublic(SQLModel):
    """Public schema for social sentiment"""
    id: int
    platform: str
    content: str | None
    author: str | None
    score: int | None
    sentiment: str | None
    currencies: list[str] | None
    posted_at: datetime | None
    collected_at: datetime


class CatalystEventsPublic(SQLModel):
    """Public schema for catalyst events"""
    id: int
    event_type: str
    title: str
    description: str | None
    source: str | None
    currencies: list[str] | None
    impact_score: int | None
    detected_at: datetime
    url: str | None
    collected_at: datetime


class CollectorRunsPublic(SQLModel):
    """Public schema for collector runs"""
    id: int
    collector_name: str
    status: str
    started_at: datetime
    completed_at: datetime | None
    records_collected: int | None
    error_message: str | None
# Agent Session Models (Phase 3) - Agentic Data Science Capability
# ============================================================================

class AgentSessionStatus(str):
    """Enum for agent session status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentSessionBase(SQLModel):
    """Base model for agent sessions"""
    user_goal: str = Field(description="Natural language trading goal from user")
    status: str = Field(default=AgentSessionStatus.PENDING, max_length=20)


class AgentSession(AgentSessionBase, table=True):
    """Database model for agent sessions"""
    __tablename__ = "agent_sessions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    user_goal: str = Field(description="Natural language trading goal from user")
    status: str = Field(default=AgentSessionStatus.PENDING, max_length=20)
    error_message: str | None = Field(default=None, description="Error message if failed")
    result_summary: str | None = Field(default=None, description="Natural language summary of results")
    # BYOM fields (Sprint 2.8) - Track which LLM configuration was used
    llm_provider: str | None = Field(default=None, max_length=20, description="LLM provider used: openai, google, anthropic, or system_default")
    llm_model: str | None = Field(default=None, max_length=100, description="Specific model used (e.g., gpt-4, gemini-1.5-pro)")
    llm_credential_id: uuid.UUID | None = Field(default=None, foreign_key="user_llm_credentials.id", description="User LLM credential used (null if system default)")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    completed_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )


class AgentSessionMessage(SQLModel, table=True):
    """Database model for agent session messages (conversation history)"""
    __tablename__ = "agent_session_messages"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    session_id: uuid.UUID = Field(foreign_key="agent_sessions.id", nullable=False)
    role: str = Field(max_length=20, description="user, assistant, system, function")
    content: str = Field(description="Message content")
    agent_name: str | None = Field(default=None, max_length=100, description="Name of agent that sent message")
    metadata_json: str | None = Field(default=None, description="JSON metadata for message")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    # Relationship to session (one-way, query from AgentSession)
    session: AgentSession = Relationship()


class AgentArtifact(SQLModel, table=True):
    """Database model for agent artifacts (models, plots, reports)"""
    __tablename__ = "agent_artifacts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    session_id: uuid.UUID = Field(foreign_key="agent_sessions.id", nullable=False)
    artifact_type: str = Field(max_length=50, description="model, plot, report, code, data")
    name: str = Field(max_length=255, description="Artifact name")
    description: str | None = Field(default=None, description="Artifact description")
    file_path: str | None = Field(default=None, max_length=500, description="Path to artifact file")
    mime_type: str | None = Field(default=None, max_length=100, description="MIME type of artifact")
    size_bytes: int | None = Field(default=None, description="File size in bytes")
    metadata_json: str | None = Field(default=None, description="JSON metadata for artifact")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    # Relationship to session (one-way, query from AgentSession)
    session: AgentSession = Relationship()


# API response models for agent sessions
class AgentSessionCreate(SQLModel):
    """Schema for creating a new agent session"""
    user_goal: str = Field(min_length=1, max_length=5000, description="Natural language trading goal")


class AgentSessionPublic(AgentSessionBase):
    """Schema for returning agent session via API"""
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    error_message: str | None
    result_summary: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class AgentSessionsPublic(SQLModel):
    """Schema for returning multiple agent sessions"""
    data: list[AgentSessionPublic]
    count: int


class AgentSessionMessagePublic(SQLModel):
    """Schema for returning agent session message via API"""
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    agent_name: str | None
    created_at: datetime


class AgentArtifactPublic(SQLModel):
    """Schema for returning agent artifact via API"""
    id: uuid.UUID
    session_id: uuid.UUID
    artifact_type: str
    name: str
    description: str | None
    file_path: str | None
    mime_type: str | None
    size_bytes: int | None
    created_at: datetime


# =============================================================================
# Phase 6: Trading System Models
# =============================================================================


class PositionBase(SQLModel):
    """Base model for trading positions"""
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    coin_type: str = Field(max_length=20, index=True)  # e.g., 'BTC', 'ETH'
    quantity: Decimal = Field(
        sa_column=Column(DECIMAL(precision=20, scale=10), nullable=False)
    )
    average_price: Decimal = Field(
        sa_column=Column(DECIMAL(precision=20, scale=8), nullable=False)
    )
    total_cost: Decimal = Field(
        sa_column=Column(DECIMAL(precision=20, scale=2), nullable=False)
    )


class Position(PositionBase, table=True):
    """
    Trading position record
    
    Tracks the current position (holdings) for each user and coin type.
    Updated when orders are executed.
    """
    __tablename__ = "positions"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=lambda: datetime.now(timezone.utc))
    )
    
    # Relationships
    user: User = Relationship()
    
    __table_args__ = (
        Index('idx_position_user_coin', 'user_id', 'coin_type', unique=True),
    )


class PositionPublic(PositionBase):
    """Schema for returning position via API"""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    current_value: Decimal | None = None  # Calculated field
    unrealized_pnl: Decimal | None = None  # Calculated field


class OrderBase(SQLModel):
    """Base model for trading orders"""
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    algorithm_id: uuid.UUID | None = Field(default=None, index=True)  # NULL for manual orders
    coin_type: str = Field(max_length=20, index=True)
    side: str = Field(max_length=10)  # 'buy' or 'sell'
    order_type: str = Field(max_length=20, default='market')  # 'market' or 'limit'
    quantity: Decimal = Field(
        sa_column=Column(DECIMAL(precision=20, scale=10), nullable=False)
    )
    price: Decimal | None = Field(
        default=None,
        sa_column=Column(DECIMAL(precision=20, scale=8), nullable=True)
    )
    filled_quantity: Decimal = Field(
        default=Decimal('0'),
        sa_column=Column(DECIMAL(precision=20, scale=10), nullable=False)
    )
    status: str = Field(max_length=20, default='pending', index=True)  # pending, submitted, filled, partial, cancelled, failed
    error_message: str | None = Field(default=None, max_length=500)
    coinspot_order_id: str | None = Field(default=None, max_length=100, index=True)


class Order(OrderBase, table=True):
    """
    Trading order record
    
    Tracks all trading orders (buy/sell) including their execution status.
    Updated as orders progress through their lifecycle.
    """
    __tablename__ = "orders"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=lambda: datetime.now(timezone.utc))
    )
    submitted_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    filled_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    
    # Relationships
    user: User = Relationship()
    
    __table_args__ = (
        Index('idx_order_user_status', 'user_id', 'status'),
        Index('idx_order_created', 'created_at'),
    )


class OrderCreate(SQLModel):
    """Schema for creating an order"""
    coin_type: str = Field(max_length=20)
    side: str = Field(max_length=10)
    order_type: str = Field(max_length=20, default='market')
    quantity: Decimal
    price: Decimal | None = None
    algorithm_id: uuid.UUID | None = None


class OrderPublic(OrderBase):
    """Schema for returning order via API"""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None
    filled_at: datetime | None


# =============================================================================
# Phase 5/6: Algorithm Deployment Models
# =============================================================================

class AlgorithmBase(SQLModel):
    """Base model for trading algorithms"""
    name: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    algorithm_type: str = Field(max_length=50)  # 'ml_model', 'rule_based', 'reinforcement_learning'
    version: str = Field(max_length=50, default='1.0.0')
    artifact_id: uuid.UUID | None = Field(
        default=None, 
        foreign_key="agent_artifacts.id",
        description="Link to AgentArtifact for ML models from Phase 3"
    )
    status: str = Field(max_length=20, default='draft', index=True)  # draft, active, paused, archived
    configuration_json: str | None = Field(
        default=None,
        description="JSON configuration for algorithm parameters"
    )
    default_execution_frequency: int = Field(
        default=300,
        description="Default execution frequency in seconds (e.g., 300 = 5 minutes)"
    )
    default_position_limit: Decimal | None = Field(
        default=None,
        sa_column=Column(DECIMAL(precision=20, scale=2), nullable=True),
        description="Default maximum position size in AUD"
    )
    performance_metrics_json: str | None = Field(
        default=None,
        description="JSON metrics: sharpe_ratio, max_drawdown, win_rate, etc."
    )


class Algorithm(AlgorithmBase, table=True):
    """
    Algorithm definition
    
    Represents a trading algorithm that can be deployed by users.
    Can be linked to AgentArtifacts (Phase 3 models) or be standalone.
    """
    __tablename__ = "algorithms"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_by: uuid.UUID = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=lambda: datetime.now(timezone.utc))
    )
    last_executed_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    
    # Relationships (one-way, query DeployedAlgorithm to access)
    
    __table_args__ = (
        Index('idx_algorithm_status', 'status'),
        Index('idx_algorithm_created_by', 'created_by'),
    )


class AlgorithmPublic(AlgorithmBase):
    """Schema for returning algorithm via API"""
    id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    last_executed_at: datetime | None


class AlgorithmCreate(SQLModel):
    """Schema for creating an algorithm"""
    name: str = Field(max_length=255)
    description: str | None = None
    algorithm_type: str = Field(max_length=50)
    version: str = Field(max_length=50, default='1.0.0')
    artifact_id: uuid.UUID | None = None
    configuration_json: str | None = None
    default_execution_frequency: int = 300
    default_position_limit: Decimal | None = None


class AlgorithmUpdate(SQLModel):
    """Schema for updating an algorithm"""
    name: str | None = None
    description: str | None = None
    status: str | None = None
    configuration_json: str | None = None
    default_execution_frequency: int | None = None
    default_position_limit: Decimal | None = None
    performance_metrics_json: str | None = None


class DeployedAlgorithmBase(SQLModel):
    """Base model for deployed algorithms (user-specific deployments)"""
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    algorithm_id: uuid.UUID = Field(foreign_key="algorithms.id", index=True)
    deployment_name: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=False, index=True)
    execution_frequency: int = Field(
        default=300,
        description="Execution frequency in seconds (overrides algorithm default)"
    )
    position_limit: Decimal | None = Field(
        default=None,
        sa_column=Column(DECIMAL(precision=20, scale=2), nullable=True),
        description="Maximum position size in AUD (overrides algorithm default)"
    )
    daily_loss_limit: Decimal | None = Field(
        default=None,
        sa_column=Column(DECIMAL(precision=20, scale=2), nullable=True),
        description="Maximum daily loss in AUD"
    )
    parameters_json: str | None = Field(
        default=None,
        description="User-specific algorithm parameters"
    )


class DeployedAlgorithm(DeployedAlgorithmBase, table=True):
    """
    Deployed algorithm instance
    
    Represents a user's deployment of an algorithm with custom parameters.
    Multiple users can deploy the same algorithm with different settings.
    """
    __tablename__ = "deployed_algorithms"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=lambda: datetime.now(timezone.utc))
    )
    activated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    deactivated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    last_executed_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    total_profit_loss: Decimal = Field(
        default=Decimal('0'),
        sa_column=Column(DECIMAL(precision=20, scale=2), nullable=False),
        description="Cumulative P&L for this deployment"
    )
    total_trades: int = Field(default=0, description="Total number of trades executed")
    
    # Relationships
    algorithm: Algorithm = Relationship()
    
    __table_args__ = (
        Index('idx_deployed_algorithm_user_active', 'user_id', 'is_active'),
        Index('idx_deployed_algorithm_algorithm', 'algorithm_id'),
    )


class DeployedAlgorithmPublic(DeployedAlgorithmBase):
    """Schema for returning deployed algorithm via API"""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    activated_at: datetime | None
    deactivated_at: datetime | None
    last_executed_at: datetime | None
    total_profit_loss: Decimal
    total_trades: int


class DeployedAlgorithmCreate(SQLModel):
    """Schema for creating a deployed algorithm"""
    algorithm_id: uuid.UUID
    deployment_name: str | None = None
    execution_frequency: int = 300
    position_limit: Decimal | None = None
    daily_loss_limit: Decimal | None = None
    parameters_json: str | None = None


class DeployedAlgorithmUpdate(SQLModel):
    """Schema for updating a deployed algorithm"""
    deployment_name: str | None = None
    is_active: bool | None = None
    execution_frequency: int | None = None
    position_limit: Decimal | None = None
    daily_loss_limit: Decimal | None = None
    parameters_json: str | None = None


# Update User model to include relationships
User.model_rebuild()

