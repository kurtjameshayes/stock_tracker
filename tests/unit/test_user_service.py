"""
Unit tests for User Service.

Tests user registration, authentication, and profile management.
"""

import pytest
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_register_user(test_db, sample_user_data):
    """Test user registration."""
    user_repo = UserRepository(test_db)
    user_service = UserService(user_repo)

    user_create = UserCreate(
        email=sample_user_data["email"],
        name=sample_user_data["name"],
        password=sample_user_data["password"]
    )

    user = await user_service.register_user(user_create)

    assert user is not None
    assert user["email"] == sample_user_data["email"]
    assert user["name"] == sample_user_data["name"]
    assert "password_hash" in user
    assert user["tier"] == "free"


@pytest.mark.asyncio
async def test_register_duplicate_email(test_db, sample_user_data):
    """Test registration with duplicate email fails."""
    user_repo = UserRepository(test_db)
    user_service = UserService(user_repo)

    user_create = UserCreate(
        email=sample_user_data["email"],
        name=sample_user_data["name"],
        password=sample_user_data["password"]
    )

    # Register first time
    await user_service.register_user(user_create)

    # Try to register again with same email
    with pytest.raises(HTTPException) as exc_info:
        await user_service.register_user(user_create)

    assert exc_info.value.status_code == 400
    assert "already registered" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_authenticate_user(test_db, sample_user_data):
    """Test user authentication."""
    user_repo = UserRepository(test_db)
    user_service = UserService(user_repo)

    # Register user
    user_create = UserCreate(
        email=sample_user_data["email"],
        name=sample_user_data["name"],
        password=sample_user_data["password"]
    )
    await user_service.register_user(user_create)

    # Authenticate
    token = await user_service.authenticate_user(
        sample_user_data["email"],
        sample_user_data["password"]
    )

    assert token is not None
    assert token.access_token is not None
    assert token.refresh_token is not None
    assert token.token_type == "bearer"


@pytest.mark.asyncio
async def test_authenticate_wrong_password(test_db, sample_user_data):
    """Test authentication with wrong password fails."""
    user_repo = UserRepository(test_db)
    user_service = UserService(user_repo)

    # Register user
    user_create = UserCreate(
        email=sample_user_data["email"],
        name=sample_user_data["name"],
        password=sample_user_data["password"]
    )
    await user_service.register_user(user_create)

    # Try to authenticate with wrong password
    with pytest.raises(HTTPException) as exc_info:
        await user_service.authenticate_user(
            sample_user_data["email"],
            "WrongPassword123"
        )

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_update_user_profile(test_db, sample_user_data):
    """Test updating user profile."""
    user_repo = UserRepository(test_db)
    user_service = UserService(user_repo)

    # Register user
    user_create = UserCreate(
        email=sample_user_data["email"],
        name=sample_user_data["name"],
        password=sample_user_data["password"]
    )
    user = await user_service.register_user(user_create)

    # Update profile
    update_data = UserUpdate(name="Updated Name")
    updated_user = await user_service.update_user_profile(user["_id"], update_data)

    assert updated_user["name"] == "Updated Name"
    assert updated_user["email"] == sample_user_data["email"]
