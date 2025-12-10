"""
User repository for database operations.

Handles all database operations related to users.
"""

from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base import BaseRepository
from datetime import datetime


class UserRepository(BaseRepository):
    """Repository for user data operations."""

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize user repository.

        Args:
            database: MongoDB database instance
        """
        super().__init__(database, "users")

    async def create_user(self, user_data: Dict[str, Any]) -> str:
        """
        Create a new user.

        Args:
            user_data: User data including email, password_hash, name, etc.

        Returns:
            Created user ID
        """
        user_data["tier"] = user_data.get("tier", "free")
        user_data["preferences"] = user_data.get("preferences", {})
        user_data["last_login"] = None

        return await self.create(user_data)

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email address.

        Args:
            email: User email address

        Returns:
            User document or None
        """
        return await self.get_by_field("email", email)

    async def update_last_login(self, user_id: str) -> bool:
        """
        Update user's last login timestamp.

        Args:
            user_id: User ID

        Returns:
            True if updated successfully
        """
        return await self.update(user_id, {"last_login": datetime.utcnow()})

    async def update_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """
        Update user preferences.

        Args:
            user_id: User ID
            preferences: New preferences dict

        Returns:
            True if updated successfully
        """
        return await self.update(user_id, {"preferences": preferences})

    async def update_tier(self, user_id: str, tier: str) -> bool:
        """
        Update user's subscription tier.

        Args:
            user_id: User ID
            tier: New tier (free, premium, enterprise)

        Returns:
            True if updated successfully
        """
        return await self.update(user_id, {"tier": tier})
