"""
Watchlist repository for database operations.

Handles all database operations related to watchlists and items.
"""

from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base import BaseRepository
from bson import ObjectId


class WatchlistRepository(BaseRepository):
    """Repository for watchlist data operations."""

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize watchlist repository.

        Args:
            database: MongoDB database instance
        """
        super().__init__(database, "watchlists")

    async def get_user_watchlists(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all watchlists for a user.

        Args:
            user_id: User ID

        Returns:
            List of watchlist documents
        """
        return await self.find_many(
            {"user_id": user_id},
            sort=[("is_default", -1), ("created_at", -1)]
        )

    async def get_default_watchlist(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user's default watchlist.

        Args:
            user_id: User ID

        Returns:
            Default watchlist document or None
        """
        watchlists = await self.find_many(
            {"user_id": user_id, "is_default": True},
            limit=1
        )
        return watchlists[0] if watchlists else None

    async def set_default(self, watchlist_id: str, user_id: str) -> bool:
        """
        Set a watchlist as default (unsets other defaults for user).

        Args:
            watchlist_id: Watchlist ID to set as default
            user_id: User ID

        Returns:
            True if successful
        """
        # First, unset all other defaults for this user
        await self.collection.update_many(
            {"user_id": user_id},
            {"$set": {"is_default": False}}
        )

        # Set this one as default
        return await self.update(watchlist_id, {"is_default": True})


class WatchlistItemRepository(BaseRepository):
    """Repository for watchlist item operations."""

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize watchlist item repository.

        Args:
            database: MongoDB database instance
        """
        super().__init__(database, "watchlist_items")

    async def get_watchlist_items(self, watchlist_id: str) -> List[Dict[str, Any]]:
        """
        Get all items in a watchlist.

        Args:
            watchlist_id: Watchlist ID

        Returns:
            List of watchlist item documents
        """
        return await self.find_many(
            {"watchlist_id": watchlist_id},
            sort=[("position", 1)]
        )

    async def add_stock(self, watchlist_id: str, stock_id: str, notes: Optional[str] = None) -> str:
        """
        Add a stock to watchlist.

        Args:
            watchlist_id: Watchlist ID
            stock_id: Stock ID
            notes: Optional notes

        Returns:
            Created item ID
        """
        # Check if already exists
        existing = await self.collection.find_one({
            "watchlist_id": watchlist_id,
            "stock_id": stock_id
        })

        if existing:
            return str(existing["_id"])

        # Get next position
        items = await self.get_watchlist_items(watchlist_id)
        position = len(items)

        item_data = {
            "watchlist_id": watchlist_id,
            "stock_id": stock_id,
            "position": position,
            "notes": notes,
            "added_at": None  # Will be set by create()
        }

        return await self.create(item_data)

    async def remove_stock(self, watchlist_id: str, stock_id: str) -> bool:
        """
        Remove a stock from watchlist.

        Args:
            watchlist_id: Watchlist ID
            stock_id: Stock ID

        Returns:
            True if removed
        """
        result = await self.collection.delete_one({
            "watchlist_id": watchlist_id,
            "stock_id": stock_id
        })
        return result.deleted_count > 0

    async def update_positions(self, updates: List[Dict[str, Any]]) -> bool:
        """
        Update positions of multiple items.

        Args:
            updates: List of {item_id, position} dicts

        Returns:
            True if successful
        """
        try:
            for update in updates:
                await self.update(update["item_id"], {"position": update["position"]})
            return True
        except Exception:
            return False
