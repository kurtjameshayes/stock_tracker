"""
Authentication API endpoints.

Handles user registration, login, and authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.user import (
    UserCreate, UserResponse, UserLogin, Token, UserUpdate, PasswordChange
)
from app.services.user_service import UserService
from app.api.dependencies import get_user_service
from app.core.security import get_current_user_id

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Register a new user.

    Creates a new user account with the provided credentials.
    """
    user = await user_service.register_user(user_data)
    return user


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    user_service: UserService = Depends(get_user_service)
):
    """
    Login and get access tokens.

    Authenticates user and returns JWT access and refresh tokens.
    """
    token = await user_service.authenticate_user(
        credentials.email,
        credentials.password
    )
    return token


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get current user profile.

    Returns the authenticated user's profile information.
    """
    user = await user_service.get_user_profile(current_user_id)
    return user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    update_data: UserUpdate,
    current_user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update user profile.

    Updates the authenticated user's profile information.
    """
    user = await user_service.update_user_profile(current_user_id, update_data)
    return user


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
):
    """
    Change user password.

    Changes the authenticated user's password.
    """
    success = await user_service.change_password(
        current_user_id,
        password_data.current_password,
        password_data.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to change password"
        )

    return {"message": "Password changed successfully"}
