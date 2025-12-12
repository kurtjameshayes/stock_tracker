"""
Unit tests for User Service.

Tests user registration, authentication, and profile management.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from fastapi import HTTPException


@pytest.fixture
def mock_user_repo():
    """Create mock user repository."""
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def user_service(mock_user_repo):
    """Create user service with mocked dependencies."""
    return UserService(mock_user_repo)


@pytest.fixture
def sample_user_data():
    """Provide sample user data for testing."""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "password": "TestPass123",
        "tier": "free",
        "preferences": {}
    }


@pytest.fixture
def sample_user_doc():
    """Provide sample user document as returned from DB."""
    return {
        "_id": "user123",
        "email": "test@example.com",
        "name": "Test User",
        "password_hash": "$2b$12$hashedpassword",
        "tier": "free",
        "preferences": {},
        "created_at": datetime.utcnow()
    }


class TestRegisterUser:
    """Tests for user registration."""

    @pytest.mark.asyncio
    async def test_register_user_success(self, user_service, mock_user_repo, sample_user_data):
        """Test successful user registration."""
        mock_user_repo.get_by_email.return_value = None  # No existing user
        mock_user_repo.create_user.return_value = "user123"
        mock_user_repo.get_by_id.return_value = {
            "_id": "user123",
            "email": sample_user_data["email"],
            "name": sample_user_data["name"],
            "password_hash": "$2b$12$hashedpassword",
            "tier": "free"
        }

        user_create = MagicMock()
        user_create.email = sample_user_data["email"]
        user_create.name = sample_user_data["name"]
        user_create.password = sample_user_data["password"]
        user_create.model_dump.return_value = sample_user_data

        user = await user_service.register_user(user_create)

        assert user is not None
        assert user["email"] == sample_user_data["email"]
        assert user["name"] == sample_user_data["name"]
        assert user["tier"] == "free"
        mock_user_repo.create_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_hashes_password(self, user_service, mock_user_repo, sample_user_data):
        """Test that password is hashed during registration."""
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.create_user.return_value = "user123"
        mock_user_repo.get_by_id.return_value = {
            "_id": "user123",
            "email": sample_user_data["email"],
            "name": sample_user_data["name"],
            "password_hash": "$2b$12$hashedpassword",
            "tier": "free"
        }

        user_create = MagicMock()
        user_create.email = sample_user_data["email"]
        user_create.name = sample_user_data["name"]
        user_create.password = sample_user_data["password"]
        user_create.model_dump.return_value = sample_user_data

        await user_service.register_user(user_create)

        # Verify password_hash was set (not plain password)
        call_args = mock_user_repo.create_user.call_args[0][0]
        assert "password_hash" in call_args
        assert call_args["password_hash"] != sample_user_data["password"]

    @pytest.mark.asyncio
    async def test_register_duplicate_email_fails(self, user_service, mock_user_repo, sample_user_data, sample_user_doc):
        """Test registration with duplicate email fails."""
        mock_user_repo.get_by_email.return_value = sample_user_doc  # User exists

        user_create = MagicMock()
        user_create.email = sample_user_data["email"]
        user_create.name = sample_user_data["name"]
        user_create.password = sample_user_data["password"]

        with pytest.raises(HTTPException) as exc_info:
            await user_service.register_user(user_create)

        assert exc_info.value.status_code == 400
        assert "already registered" in str(exc_info.value.detail).lower()


class TestAuthenticateUser:
    """Tests for user authentication."""

    @pytest.mark.asyncio
    @patch('app.services.user_service.verify_password')
    async def test_authenticate_user_success(self, mock_verify, user_service, mock_user_repo, sample_user_doc):
        """Test successful user authentication."""
        mock_user_repo.get_by_email.return_value = sample_user_doc
        mock_verify.return_value = True
        mock_user_repo.update_last_login.return_value = True

        token = await user_service.authenticate_user("test@example.com", "TestPass123")

        assert token is not None
        assert token.access_token is not None
        assert token.refresh_token is not None
        assert token.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, user_service, mock_user_repo):
        """Test authentication with non-existent user fails."""
        mock_user_repo.get_by_email.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await user_service.authenticate_user("nonexistent@example.com", "password")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @patch('app.services.user_service.verify_password')
    async def test_authenticate_wrong_password(self, mock_verify, user_service, mock_user_repo, sample_user_doc):
        """Test authentication with wrong password fails."""
        mock_user_repo.get_by_email.return_value = sample_user_doc
        mock_verify.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await user_service.authenticate_user("test@example.com", "WrongPassword")

        assert exc_info.value.status_code == 401


class TestGetUserProfile:
    """Tests for getting user profile."""

    @pytest.mark.asyncio
    async def test_get_user_profile_success(self, user_service, mock_user_repo, sample_user_doc):
        """Test getting user profile successfully."""
        mock_user_repo.get_by_id.return_value = sample_user_doc

        profile = await user_service.get_user_profile("user123")

        assert profile is not None
        assert profile["email"] == sample_user_doc["email"]
        mock_user_repo.get_by_id.assert_called_once_with("user123")

    @pytest.mark.asyncio
    async def test_get_user_profile_not_found(self, user_service, mock_user_repo):
        """Test getting non-existent user profile fails."""
        mock_user_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await user_service.get_user_profile("nonexistent")

        assert exc_info.value.status_code == 404


class TestUpdateUserProfile:
    """Tests for updating user profile."""

    @pytest.mark.asyncio
    async def test_update_user_profile_success(self, user_service, mock_user_repo, sample_user_doc):
        """Test updating user profile successfully."""
        mock_user_repo.get_by_id.return_value = sample_user_doc
        mock_user_repo.update.return_value = True

        updated_doc = sample_user_doc.copy()
        updated_doc["name"] = "Updated Name"
        mock_user_repo.get_by_id.side_effect = [sample_user_doc, updated_doc]

        update_data = MagicMock()
        update_data.model_dump.return_value = {"name": "Updated Name"}

        updated_user = await user_service.update_user_profile("user123", update_data)

        assert updated_user["name"] == "Updated Name"
        mock_user_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_profile_not_found(self, user_service, mock_user_repo):
        """Test updating non-existent user fails."""
        mock_user_repo.get_by_id.return_value = None

        update_data = MagicMock()
        update_data.model_dump.return_value = {"name": "Updated Name"}

        with pytest.raises(HTTPException) as exc_info:
            await user_service.update_user_profile("nonexistent", update_data)

        assert exc_info.value.status_code == 404


class TestChangePassword:
    """Tests for password change."""

    @pytest.mark.asyncio
    @patch('app.services.user_service.verify_password')
    @patch('app.services.user_service.hash_password')
    async def test_change_password_success(self, mock_hash, mock_verify, user_service, mock_user_repo, sample_user_doc):
        """Test changing password successfully."""
        mock_user_repo.get_by_id.return_value = sample_user_doc
        mock_verify.return_value = True
        mock_hash.return_value = "$2b$12$newhash"
        mock_user_repo.update.return_value = True

        result = await user_service.change_password("user123", "OldPassword", "NewPassword123")

        assert result == True
        mock_user_repo.update.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.user_service.verify_password')
    async def test_change_password_wrong_current(self, mock_verify, user_service, mock_user_repo, sample_user_doc):
        """Test changing password with wrong current password fails."""
        mock_user_repo.get_by_id.return_value = sample_user_doc
        mock_verify.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await user_service.change_password("user123", "WrongPassword", "NewPassword123")

        assert exc_info.value.status_code == 400
