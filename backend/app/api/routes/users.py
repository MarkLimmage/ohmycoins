import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage
from sqlmodel import func, select

from app import crud
from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models import (
    Message,
    UpdatePassword,
    User,
    UserCreate,
    UserLLMCredentials,
    UserLLMCredentialsCreate,
    UserLLMCredentialsPublic,
    UserLLMCredentialsValidate,
    UserLLMCredentialsValidationResult,
    UserProfilePublic,
    UserProfileUpdate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from app.services.agent.llm_factory import LLMFactory
from app.services.encryption import encryption_service
from app.utils import generate_new_account_email, send_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """

    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()

    return UsersPublic(data=users, count=count)


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic
)
def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    """
    Create new user.
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = crud.create_user(session=session, user_create=user_in)
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """

    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.patch("/me/password", response_model=Message)
def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """
    Update own password.
    """
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    session.commit()
    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.get("/me/profile", response_model=UserProfilePublic)
def read_user_profile(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Get current user's full profile including OMC-specific fields.
    """
    # Check if user has Coinspot credentials
    from app.models import CoinspotCredentials

    credentials = session.exec(
        select(CoinspotCredentials).where(CoinspotCredentials.user_id == current_user.id)
    ).first()

    return UserProfilePublic(
        email=current_user.email,
        full_name=current_user.full_name,
        timezone=current_user.timezone or "UTC",
        preferred_currency=current_user.preferred_currency or "AUD",
        risk_tolerance=current_user.risk_tolerance or "medium",
        trading_experience=current_user.trading_experience or "beginner",
        has_coinspot_credentials=credentials is not None
    )


@router.patch("/me/profile", response_model=UserProfilePublic)
def update_user_profile(
    *, session: SessionDep, profile_in: UserProfileUpdate, current_user: CurrentUser
) -> Any:
    """
    Update current user's profile with OMC-specific fields.
    """
    # Update user fields
    profile_data = profile_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(profile_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    # Check credentials for response
    from app.models import CoinspotCredentials

    credentials = session.exec(
        select(CoinspotCredentials).where(CoinspotCredentials.user_id == current_user.id)
    ).first()

    return UserProfilePublic(
        email=current_user.email,
        full_name=current_user.full_name,
        timezone=current_user.timezone or "UTC",
        preferred_currency=current_user.preferred_currency or "AUD",
        risk_tolerance=current_user.risk_tolerance or "medium",
        trading_experience=current_user.trading_experience or "beginner",
        has_coinspot_credentials=credentials is not None
    )


@router.delete("/me", response_model=Message)
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(current_user)
    session.commit()
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user_create = UserCreate.model_validate(user_in)
    user = crud.create_user(session=session, user_create=user_create)
    return user


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    user = session.get(User, user_id)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """

    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )

    db_user = crud.update_user(session=session, db_user=db_user, user_in=user_in)
    return db_user


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    """
    Delete a user.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(user)
    session.commit()
    return Message(message="User deleted successfully")


# ============================================================================
# LLM Credentials Endpoints (BYOM Feature - Sprint 2.8)
# ============================================================================


@router.post("/me/llm-credentials", response_model=UserLLMCredentialsPublic)
def create_llm_credentials(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    credentials_in: UserLLMCredentialsCreate,
) -> Any:
    """
    Create new LLM API credentials for the current user (BYOM feature).

    Credentials are encrypted before storage using AES-256.
    Multiple credentials can be stored (one per provider).
    """
    # Check if user already has credentials for this provider
    existing = session.exec(
        select(UserLLMCredentials).where(
            UserLLMCredentials.user_id == current_user.id,
            UserLLMCredentials.provider == credentials_in.provider.lower(),
            UserLLMCredentials.is_active == True
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Active {credentials_in.provider} credentials already exist. Use PUT to update or DELETE first."
        )

    # Encrypt API key
    try:
        encrypted_api_key = encryption_service.encrypt_api_key(credentials_in.api_key)
    except Exception as e:
        logger.error(f"Failed to encrypt API key: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to encrypt API key"
        )

    # If this should be default, unset any existing defaults
    if credentials_in.is_default:
        existing_defaults = session.exec(
            select(UserLLMCredentials).where(
                UserLLMCredentials.user_id == current_user.id,
                UserLLMCredentials.is_default == True
            )
        ).all()
        for cred in existing_defaults:
            cred.is_default = False
            session.add(cred)

    # Create credentials record
    db_credentials = UserLLMCredentials(
        user_id=current_user.id,
        provider=credentials_in.provider.lower(),
        model_name=credentials_in.model_name,
        encrypted_api_key=encrypted_api_key,
        encryption_key_id="default",
        is_default=credentials_in.is_default,
        is_active=True
    )

    session.add(db_credentials)
    session.commit()
    session.refresh(db_credentials)

    # Audit log for credential creation
    logger.info(f"LLM credential created for user {current_user.id}, provider={credentials_in.provider}, credential_id={db_credentials.id}")

    # Return public view with masked API key
    api_key_masked = encryption_service.mask_api_key(credentials_in.api_key)

    return UserLLMCredentialsPublic(
        id=db_credentials.id,
        user_id=db_credentials.user_id,
        provider=db_credentials.provider,
        model_name=db_credentials.model_name,
        api_key_masked=api_key_masked,
        is_default=db_credentials.is_default,
        is_active=db_credentials.is_active,
        last_validated_at=db_credentials.last_validated_at,
        created_at=db_credentials.created_at,
        updated_at=db_credentials.updated_at
    )


@router.get("/me/llm-credentials", response_model=list[UserLLMCredentialsPublic])
def list_llm_credentials(
    *,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    List all LLM API credentials for the current user (BYOM feature).

    Returns masked credentials for security.
    Only returns active credentials by default.
    """
    credentials_list = session.exec(
        select(UserLLMCredentials).where(
            UserLLMCredentials.user_id == current_user.id,
            UserLLMCredentials.is_active == True
        )
    ).all()

    result = []
    for cred in credentials_list:
        # Decrypt API key to mask it
        try:
            api_key = encryption_service.decrypt_api_key(cred.encrypted_api_key)
            api_key_masked = encryption_service.mask_api_key(api_key)
        except Exception as e:
            logger.error(f"Failed to decrypt API key for masking: {e}")
            api_key_masked = "****"

        result.append(UserLLMCredentialsPublic(
            id=cred.id,
            user_id=cred.user_id,
            provider=cred.provider,
            model_name=cred.model_name,
            api_key_masked=api_key_masked,
            is_default=cred.is_default,
            is_active=cred.is_active,
            last_validated_at=cred.last_validated_at,
            created_at=cred.created_at,
            updated_at=cred.updated_at
        ))

    return result


@router.put("/me/llm-credentials/{credential_id}/default", response_model=UserLLMCredentialsPublic)
def set_default_llm_credential(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    credential_id: uuid.UUID,
) -> Any:
    """
    Set a specific LLM credential as the default for the user.

    Unsets any existing default credentials.
    """
    credential = session.get(UserLLMCredentials, credential_id)

    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")

    if credential.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this credential")

    if not credential.is_active:
        raise HTTPException(status_code=400, detail="Cannot set inactive credential as default")

    # Unset any existing defaults
    existing_defaults = session.exec(
        select(UserLLMCredentials).where(
            UserLLMCredentials.user_id == current_user.id,
            UserLLMCredentials.is_default == True
        )
    ).all()
    for cred in existing_defaults:
        cred.is_default = False
        session.add(cred)

    # Set this one as default
    credential.is_default = True
    session.add(credential)
    session.commit()
    session.refresh(credential)

    # Return with masked API key
    try:
        api_key = encryption_service.decrypt_api_key(credential.encrypted_api_key)
        api_key_masked = encryption_service.mask_api_key(api_key)
    except Exception as e:
        logger.error(f"Failed to decrypt API key for masking: {e}")
        api_key_masked = "****"

    return UserLLMCredentialsPublic(
        id=credential.id,
        user_id=credential.user_id,
        provider=credential.provider,
        model_name=credential.model_name,
        api_key_masked=api_key_masked,
        is_default=credential.is_default,
        is_active=credential.is_active,
        last_validated_at=credential.last_validated_at,
        created_at=credential.created_at,
        updated_at=credential.updated_at
    )


@router.delete("/me/llm-credentials/{credential_id}", response_model=Message)
def delete_llm_credential(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    credential_id: uuid.UUID,
) -> Any:
    """
    Delete (soft delete) an LLM credential.

    Sets is_active=False instead of actually deleting for audit purposes.
    """
    credential = session.get(UserLLMCredentials, credential_id)

    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")

    if credential.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this credential")

    # Soft delete
    credential.is_active = False
    credential.is_default = False  # Can't be default if inactive
    session.add(credential)
    session.commit()

    # Audit log for credential deletion
    logger.info(f"LLM credential deleted for user {current_user.id}, provider={credential.provider}, credential_id={credential_id}")

    return Message(message=f"{credential.provider} credentials deleted successfully")


@router.post("/me/llm-credentials/validate", response_model=UserLLMCredentialsValidationResult)
async def validate_llm_credential(
    *,
    _session: SessionDep,
    current_user: CurrentUser,
    validation_request: UserLLMCredentialsValidate,
) -> Any:
    """
    Validate an LLM API key before saving it.

    Tests the API key by making a simple request to the provider.
    Does NOT save the credential - use POST /me/llm-credentials to save.
    """
    provider = validation_request.provider.lower()
    api_key = validation_request.api_key
    model_name = validation_request.model_name

    try:
        # Create LLM instance to test the API key
        llm = LLMFactory.create_llm_from_api_key(
            provider=provider,
            api_key=api_key,
            model_name=model_name
        )

        # Test with a simple message
        test_message = HumanMessage(content="Hello, this is a test. Please respond with 'OK'.")

        # Invoke the LLM (this will fail if API key is invalid)
        response = await llm.ainvoke([test_message])

        # If we got here, the API key works
        logger.info(f"Successfully validated {provider} API key for user {current_user.id}")

        return UserLLMCredentialsValidationResult(
            is_valid=True,
            provider=provider,
            model_name=model_name or LLMFactory.get_provider_default_models()[provider],
            error_message=None,
            details={"message": "API key validated successfully", "test_response_length": len(response.content)}
        )

    except Exception as e:
        logger.warning(f"Failed to validate {provider} API key: {e}")

        error_message = str(e)
        if "authentication" in error_message.lower() or "unauthorized" in error_message.lower():
            error_message = "Invalid API key. Please check your credentials."
        elif "not found" in error_message.lower():
            error_message = f"Model '{model_name}' not found. Please check the model name."
        elif "quota" in error_message.lower() or "rate limit" in error_message.lower():
            error_message = "API quota exceeded or rate limit reached. Please try again later."
        else:
            error_message = f"Validation failed: {error_message}"

        return UserLLMCredentialsValidationResult(
            is_valid=False,
            provider=provider,
            model_name=model_name,
            error_message=error_message,
            details={"raw_error": str(e)}
        )
