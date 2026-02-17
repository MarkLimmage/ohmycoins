"""
API endpoints for Coinspot credential management

Provides CRUD operations for securely storing and managing Coinspot API credentials.
"""
import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.api.deps import CurrentUser, get_db
from app.models import (
    CoinspotCredentials,
    CoinspotCredentialsCreate,
    CoinspotCredentialsPublic,
    CoinspotCredentialsUpdate,
    Message,
)
from app.services.coinspot_auth import CoinspotAuthenticator
from app.services.encryption import encryption_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=CoinspotCredentialsPublic)
def create_credentials(
    *,
    session: Session = Depends(get_db),
    current_user: CurrentUser,
    credentials_in: CoinspotCredentialsCreate,
) -> Any:
    """
    Create new Coinspot API credentials for the current user.

    Credentials are encrypted before storage.
    """
    # Check if user already has credentials
    existing = session.exec(
        select(CoinspotCredentials).where(CoinspotCredentials.user_id == current_user.id)
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Coinspot credentials already exist. Use PUT to update them."
        )

    # Encrypt credentials
    try:
        api_key_encrypted = encryption_service.encrypt(credentials_in.api_key)
        api_secret_encrypted = encryption_service.encrypt(credentials_in.api_secret)
    except Exception as e:
        logger.error(f"Failed to encrypt credentials: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to encrypt credentials"
        )

    # Create credentials record
    db_credentials = CoinspotCredentials(
        user_id=current_user.id,
        api_key_encrypted=api_key_encrypted,
        api_secret_encrypted=api_secret_encrypted,
        is_validated=False
    )

    session.add(db_credentials)
    session.commit()
    session.refresh(db_credentials)

    # Return public view with masked API key
    api_key_masked = encryption_service.mask_api_key(credentials_in.api_key)

    return CoinspotCredentialsPublic(
        id=db_credentials.id,
        user_id=db_credentials.user_id,
        api_key_masked=api_key_masked,
        is_validated=db_credentials.is_validated,
        last_validated_at=db_credentials.last_validated_at,
        created_at=db_credentials.created_at,
        updated_at=db_credentials.updated_at
    )


@router.get("/", response_model=CoinspotCredentialsPublic)
def get_credentials(
    *,
    session: Session = Depends(get_db),
    current_user: CurrentUser,
) -> Any:
    """
    Get Coinspot API credentials for the current user.

    Returns masked credentials for security.
    """
    credentials = session.exec(
        select(CoinspotCredentials).where(CoinspotCredentials.user_id == current_user.id)
    ).first()

    if not credentials:
        raise HTTPException(
            status_code=404,
            detail="Coinspot credentials not found"
        )

    # Decrypt API key to mask it
    try:
        api_key = encryption_service.decrypt(credentials.api_key_encrypted)
        api_key_masked = encryption_service.mask_api_key(api_key)
    except Exception as e:
        logger.error(f"Failed to decrypt API key for masking: {e}")
        api_key_masked = "****"

    return CoinspotCredentialsPublic(
        id=credentials.id,
        user_id=credentials.user_id,
        api_key_masked=api_key_masked,
        is_validated=credentials.is_validated,
        last_validated_at=credentials.last_validated_at,
        created_at=credentials.created_at,
        updated_at=credentials.updated_at
    )


@router.put("/", response_model=CoinspotCredentialsPublic)
def update_credentials(
    *,
    session: Session = Depends(get_db),
    current_user: CurrentUser,
    credentials_in: CoinspotCredentialsUpdate,
) -> Any:
    """
    Update Coinspot API credentials for the current user.
    """
    credentials = session.exec(
        select(CoinspotCredentials).where(CoinspotCredentials.user_id == current_user.id)
    ).first()

    if not credentials:
        raise HTTPException(
            status_code=404,
            detail="Coinspot credentials not found. Use POST to create them."
        )

    # Update credentials if provided
    update_data = credentials_in.model_dump(exclude_unset=True)
    api_key_masked = None

    if "api_key" in update_data and update_data["api_key"]:
        try:
            credentials.api_key_encrypted = encryption_service.encrypt(update_data["api_key"])
            api_key_masked = encryption_service.mask_api_key(update_data["api_key"])
            # Reset validation status when credentials change
            credentials.is_validated = False
            credentials.last_validated_at = None
        except Exception as e:
            logger.error(f"Failed to encrypt API key: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to encrypt API key"
            )

    if "api_secret" in update_data and update_data["api_secret"]:
        try:
            credentials.api_secret_encrypted = encryption_service.encrypt(update_data["api_secret"])
            # Reset validation status when credentials change
            credentials.is_validated = False
            credentials.last_validated_at = None
        except Exception as e:
            logger.error(f"Failed to encrypt API secret: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to encrypt API secret"
            )

    session.add(credentials)
    session.commit()
    session.refresh(credentials)

    # Get masked API key if not already set
    if not api_key_masked:
        try:
            api_key = encryption_service.decrypt(credentials.api_key_encrypted)
            api_key_masked = encryption_service.mask_api_key(api_key)
        except Exception as e:
            logger.error(f"Failed to decrypt API key for masking: {e}")
            api_key_masked = "****"

    return CoinspotCredentialsPublic(
        id=credentials.id,
        user_id=credentials.user_id,
        api_key_masked=api_key_masked,
        is_validated=credentials.is_validated,
        last_validated_at=credentials.last_validated_at,
        created_at=credentials.created_at,
        updated_at=credentials.updated_at
    )


@router.delete("/", response_model=Message)
def delete_credentials(
    *,
    session: Session = Depends(get_db),
    current_user: CurrentUser,
) -> Any:
    """
    Delete Coinspot API credentials for the current user.
    """
    credentials = session.exec(
        select(CoinspotCredentials).where(CoinspotCredentials.user_id == current_user.id)
    ).first()

    if not credentials:
        raise HTTPException(
            status_code=404,
            detail="Coinspot credentials not found"
        )

    session.delete(credentials)
    session.commit()

    return Message(message="Coinspot credentials deleted successfully")


@router.post("/validate", response_model=Message)
async def validate_credentials(
    *,
    session: Session = Depends(get_db),
    current_user: CurrentUser,
) -> Any:
    """
    Validate Coinspot API credentials by testing them against the Coinspot API.

    Tests credentials by calling the Coinspot read-only balance endpoint.
    Updates the validation status in the database if successful.
    """
    # Get user's credentials
    credentials = session.exec(
        select(CoinspotCredentials).where(CoinspotCredentials.user_id == current_user.id)
    ).first()

    if not credentials:
        raise HTTPException(
            status_code=404,
            detail="Coinspot credentials not found. Please add credentials first."
        )

    # Decrypt credentials
    try:
        api_key = encryption_service.decrypt(credentials.api_key_encrypted)
        api_secret = encryption_service.decrypt(credentials.api_secret_encrypted)
    except Exception as e:
        logger.error(f"Failed to decrypt credentials: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to decrypt credentials"
        )

    # Test credentials with Coinspot API
    authenticator = CoinspotAuthenticator(api_key, api_secret)

    # Use the read-only balance endpoint to test credentials
    # This endpoint doesn't require a specific coin type and won't affect the account
    coinspot_url = "https://www.coinspot.com.au/api/v2/ro/my/balances"

    try:
        headers, payload = authenticator.prepare_request()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                coinspot_url,
                headers=headers,
                json=payload
            )

            response.raise_for_status()
            data = response.json()

            # Check if the response indicates success
            if data.get("status") == "ok":
                # Update validation status
                credentials.is_validated = True
                credentials.last_validated_at = datetime.now(timezone.utc)
                session.add(credentials)
                session.commit()

                logger.info(f"Successfully validated credentials for user {current_user.id}")
                return Message(message="Credentials validated successfully")
            else:
                # API returned error status
                error_message = data.get("message", "Unknown error")
                logger.warning(f"Coinspot API returned error: {error_message}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Credentials validation failed: {error_message}"
                )

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error validating credentials: {e.response.status_code}")
        if e.response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials. Please check your API key and secret."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate credentials: HTTP {e.response.status_code}"
        )
    except httpx.TimeoutException:
        logger.error("Timeout validating credentials")
        raise HTTPException(
            status_code=504,
            detail="Request to Coinspot API timed out. Please try again."
        )
    except httpx.RequestError as e:
        logger.error(f"Request error validating credentials: {e}")
        raise HTTPException(
            status_code=503,
            detail="Failed to connect to Coinspot API. Please try again later."
        )
    except Exception as e:
        logger.error(f"Unexpected error validating credentials: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during validation"
        )
