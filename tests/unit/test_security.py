"""
Unit tests for Security Module.

Tests password hashing, JWT token creation/validation, and rate limiting.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user_id,
    RateLimiter
)


class TestPasswordHashing:
    """Tests for password hashing functionality."""

    def test_hash_password_returns_hash(self):
        """Test that hash_password returns a hashed string."""
        password = "TestPassword123"
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    def test_hash_password_different_for_same_input(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "TestPassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Bcrypt includes salt, so hashes should be different
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test that verify_password returns True for correct password."""
        password = "TestPassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) == True

    def test_verify_password_incorrect(self):
        """Test that verify_password returns False for incorrect password."""
        password = "TestPassword123"
        hashed = hash_password(password)

        assert verify_password("WrongPassword", hashed) == False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "TestPassword123"
        hashed = hash_password(password)

        assert verify_password("testpassword123", hashed) == False
        assert verify_password("TESTPASSWORD123", hashed) == False


class TestAccessToken:
    """Tests for JWT access token creation."""

    @patch('app.core.security.settings')
    def test_create_access_token_success(self, mock_settings):
        """Test creating an access token."""
        mock_settings.JWT_SECRET_KEY = "test-secret-key-12345"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        data = {"sub": "user123"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    @patch('app.core.security.settings')
    def test_create_access_token_with_custom_expiry(self, mock_settings):
        """Test creating an access token with custom expiration."""
        mock_settings.JWT_SECRET_KEY = "test-secret-key-12345"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        data = {"sub": "user123"}
        expires = timedelta(hours=2)
        token = create_access_token(data, expires_delta=expires)

        assert token is not None

    @patch('app.core.security.settings')
    def test_access_token_contains_correct_type(self, mock_settings):
        """Test that access token has type 'access' in payload."""
        mock_settings.JWT_SECRET_KEY = "test-secret-key-12345"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        data = {"sub": "user123"}
        token = create_access_token(data)
        payload = decode_token(token)

        assert payload["type"] == "access"


class TestRefreshToken:
    """Tests for JWT refresh token creation."""

    @patch('app.core.security.settings')
    def test_create_refresh_token_success(self, mock_settings):
        """Test creating a refresh token."""
        mock_settings.JWT_SECRET_KEY = "test-secret-key-12345"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7

        data = {"sub": "user123"}
        token = create_refresh_token(data)

        assert token is not None
        assert isinstance(token, str)

    @patch('app.core.security.settings')
    def test_refresh_token_contains_correct_type(self, mock_settings):
        """Test that refresh token has type 'refresh' in payload."""
        mock_settings.JWT_SECRET_KEY = "test-secret-key-12345"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7

        data = {"sub": "user123"}
        token = create_refresh_token(data)
        payload = decode_token(token)

        assert payload["type"] == "refresh"


class TestDecodeToken:
    """Tests for JWT token decoding."""

    @patch('app.core.security.settings')
    def test_decode_token_success(self, mock_settings):
        """Test decoding a valid token."""
        mock_settings.JWT_SECRET_KEY = "test-secret-key-12345"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)
        payload = decode_token(token)

        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"

    @patch('app.core.security.settings')
    def test_decode_token_contains_timestamps(self, mock_settings):
        """Test that decoded token contains exp and iat timestamps."""
        mock_settings.JWT_SECRET_KEY = "test-secret-key-12345"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        data = {"sub": "user123"}
        token = create_access_token(data)
        payload = decode_token(token)

        assert "exp" in payload
        assert "iat" in payload

    @patch('app.core.security.settings')
    def test_decode_invalid_token_raises_exception(self, mock_settings):
        """Test that decoding an invalid token raises HTTPException."""
        mock_settings.JWT_SECRET_KEY = "test-secret-key-12345"
        mock_settings.JWT_ALGORITHM = "HS256"

        with pytest.raises(HTTPException) as exc_info:
            decode_token("invalid.token.here")

        assert exc_info.value.status_code == 401

    @patch('app.core.security.settings')
    def test_decode_expired_token_raises_exception(self, mock_settings):
        """Test that decoding an expired token raises HTTPException."""
        mock_settings.JWT_SECRET_KEY = "test-secret-key-12345"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        data = {"sub": "user123"}
        # Create token with negative expiry (already expired)
        token = create_access_token(data, expires_delta=timedelta(seconds=-10))

        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)

        assert exc_info.value.status_code == 401

    @patch('app.core.security.settings')
    def test_decode_token_wrong_secret_raises_exception(self, mock_settings):
        """Test that decoding with wrong secret raises HTTPException."""
        mock_settings.JWT_SECRET_KEY = "test-secret-key-12345"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        data = {"sub": "user123"}
        token = create_access_token(data)

        # Change the secret
        mock_settings.JWT_SECRET_KEY = "different-secret-key"

        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)

        assert exc_info.value.status_code == 401


class TestGetCurrentUserId:
    """Tests for get_current_user_id dependency."""

    @pytest.mark.asyncio
    @patch('app.core.security.settings')
    async def test_get_current_user_id_success(self, mock_settings):
        """Test extracting user ID from valid token."""
        mock_settings.JWT_SECRET_KEY = "test-secret-key-12345"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        data = {"sub": "user123"}
        token = create_access_token(data)

        credentials = MagicMock()
        credentials.credentials = token

        user_id = await get_current_user_id(credentials)

        assert user_id == "user123"

    @pytest.mark.asyncio
    @patch('app.core.security.settings')
    async def test_get_current_user_id_missing_sub_raises_exception(self, mock_settings):
        """Test that missing sub in token raises HTTPException."""
        mock_settings.JWT_SECRET_KEY = "test-secret-key-12345"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        # Create token without 'sub' field
        data = {"email": "test@example.com"}  # No 'sub'
        token = create_access_token(data)

        credentials = MagicMock()
        credentials.credentials = token

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_id(credentials)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @patch('app.core.security.settings')
    async def test_get_current_user_id_refresh_token_rejected(self, mock_settings):
        """Test that refresh token is rejected for user ID extraction."""
        mock_settings.JWT_SECRET_KEY = "test-secret-key-12345"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7

        data = {"sub": "user123"}
        # Create refresh token instead of access token
        token = create_refresh_token(data)

        credentials = MagicMock()
        credentials.credentials = token

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_id(credentials)

        assert exc_info.value.status_code == 401
        assert "invalid token type" in str(exc_info.value.detail).lower()


class TestRateLimiter:
    """Tests for rate limiting functionality."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        return AsyncMock()

    @pytest.fixture
    def rate_limiter(self, mock_redis):
        """Create rate limiter with mock Redis."""
        return RateLimiter(mock_redis)

    @pytest.mark.asyncio
    async def test_check_rate_limit_first_request(self, rate_limiter, mock_redis):
        """Test first request is allowed and counter is set."""
        mock_redis.get.return_value = None  # No existing key

        result = await rate_limiter.check_rate_limit("user123", limit=10, window=60)

        assert result == True
        mock_redis.setex.assert_called_once_with("rate_limit:user123", 60, 1)

    @pytest.mark.asyncio
    async def test_check_rate_limit_under_limit(self, rate_limiter, mock_redis):
        """Test request under limit is allowed."""
        mock_redis.get.return_value = b"5"  # 5 requests so far

        result = await rate_limiter.check_rate_limit("user123", limit=10, window=60)

        assert result == True
        mock_redis.incr.assert_called_once_with("rate_limit:user123")

    @pytest.mark.asyncio
    async def test_check_rate_limit_at_limit(self, rate_limiter, mock_redis):
        """Test request at limit is denied."""
        mock_redis.get.return_value = b"10"  # Already at limit

        result = await rate_limiter.check_rate_limit("user123", limit=10, window=60)

        assert result == False
        mock_redis.incr.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_rate_limit_over_limit(self, rate_limiter, mock_redis):
        """Test request over limit is denied."""
        mock_redis.get.return_value = b"15"  # Over limit

        result = await rate_limiter.check_rate_limit("user123", limit=10, window=60)

        assert result == False

    @pytest.mark.asyncio
    async def test_check_rate_limit_redis_error_allows_request(self, rate_limiter, mock_redis):
        """Test that Redis errors fail open (allow request)."""
        mock_redis.get.side_effect = Exception("Redis connection error")

        result = await rate_limiter.check_rate_limit("user123", limit=10, window=60)

        # Should fail open - allow request when rate limiter has issues
        assert result == True

    @pytest.mark.asyncio
    async def test_check_rate_limit_different_keys(self, rate_limiter, mock_redis):
        """Test that different keys have independent limits."""
        mock_redis.get.return_value = None

        await rate_limiter.check_rate_limit("user123", limit=10, window=60)
        await rate_limiter.check_rate_limit("user456", limit=10, window=60)

        # Should have called setex for both different keys
        calls = mock_redis.setex.call_args_list
        assert len(calls) == 2
        assert calls[0][0][0] == "rate_limit:user123"
        assert calls[1][0][0] == "rate_limit:user456"

    @pytest.mark.asyncio
    async def test_check_rate_limit_custom_window(self, rate_limiter, mock_redis):
        """Test rate limiting with custom window size."""
        mock_redis.get.return_value = None

        await rate_limiter.check_rate_limit("user123", limit=100, window=3600)

        mock_redis.setex.assert_called_once_with("rate_limit:user123", 3600, 1)
