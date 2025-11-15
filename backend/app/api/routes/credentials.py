"""
API endpoints for Coinspot credential management

Provides CRUD operations for securely storing and managing Coinspot API credentials.
"""
from typing import Any
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.api.deps import CurrentUser, get_db
from app.models import (
    CoinspotCredentials,
    CoinspotCredentialsCreate,
    CoinspotCredentialsUpdate,
    CoinspotCredentialsPublic,
    Message,
)
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
