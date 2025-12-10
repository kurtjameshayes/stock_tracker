"""
User service for business logic.

Handles user registration, authentication, and profile management.
"""

from typing import Optional, Dict, Any
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.schemas.user import UserCreate, UserUpdate, Token
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class UserService:
    """Service for user-related business logic."""

    def __init__(self, user_repository: UserRepository):
        """
        Initialize user service.

        Args:
            user_repository: User repository instance
        """
        self.user_repo = user_repository

    async def register_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """
        Register a new user.

        Args:
            user_data: User registration data

        Returns:
            Created user document

        Raises:
            HTTPException: If email already exists
        """
        # Check if email already exists
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Hash password
        password_hash = hash_password(user_data.password)

        # Create user document
        user_doc = {
            "email": user_data.email,
            "name": user_data.name,
            "password_hash": password_hash,
            "tier": "free",
            "preferences": {}
        }

        user_id = await self.user_repo.create_user(user_doc)
        user = await self.user_repo.get_by_id(user_id)

        logger.info(f"New user registered: {user_data.email}")

        return user

    async def authenticate_user(self, email: str, password: str) -> Token:
        """
        Authenticate user and generate tokens.

        Args:
            email: User email
            password: User password

        Returns:
            Authentication tokens

        Raises:
            HTTPException: If credentials are invalid
        """
        user = await self.user_repo.get_by_email(email)

        if not user or not verify_password(password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Update last login
        await self.user_repo.update_last_login(user["_id"])

        # Generate tokens
        access_token = create_access_token(data={"sub": user["_id"]})
        refresh_token = create_refresh_token(data={"sub": user["_id"]})

        logger.info(f"User authenticated: {email}")

        return Token(
            access_token=access_token,
            refresh_token=refresh_token
        )

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Get user profile.

        Args:
            user_id: User ID

        Returns:
            User profile data

        Raises:
            HTTPException: If user not found
        """
        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Remove sensitive data
        user.pop("password_hash", None)

        return user

    async def update_user_profile(self, user_id: str, update_data: UserUpdate) -> Dict[str, Any]:
        """
        Update user profile.

        Args:
            user_id: User ID
            update_data: Update data

        Returns:
            Updated user profile

        Raises:
            HTTPException: If update fails
        """
        update_dict = update_data.model_dump(exclude_unset=True)

        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided"
            )

        success = await self.user_repo.update(user_id, update_dict)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update profile"
            )

        return await self.get_user_profile(user_id)

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """
        Change user password.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            True if successful

        Raises:
            HTTPException: If current password is incorrect
        """
        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify current password
        if not verify_password(current_password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Hash and update new password
        new_password_hash = hash_password(new_password)
        success = await self.user_repo.update(user_id, {"password_hash": new_password_hash})

        if success:
            logger.info(f"Password changed for user: {user['email']}")

        return success
