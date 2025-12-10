"""
Watchlist service for managing stock watchlists.

Handles watchlist creation, stock management, and queries.
"""

from typing import List, Dict, Any
from app.repositories.watchlist_repository import WatchlistRepository, WatchlistItemRepository
from app.schemas.watchlist import WatchlistCreate, WatchlistUpdate, WatchlistItemCreate
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class WatchlistService:
    """Service for watchlist management."""

    def __init__(
        self,
        watchlist_repository: WatchlistRepository,
        item_repository: WatchlistItemRepository
    ):
        """
        Initialize watchlist service.

        Args:
            watchlist_repository: Watchlist repository instance
            item_repository: Watchlist item repository instance
        """
        self.watchlist_repo = watchlist_repository
        self.item_repo = item_repository

    async def create_watchlist(
        self,
        user_id: str,
        watchlist_data: WatchlistCreate
    ) -> Dict[str, Any]:
        """
        Create a new watchlist.

        Args:
            user_id: User ID
            watchlist_data: Watchlist creation data

        Returns:
            Created watchlist document
        """
        watchlist_doc = watchlist_data.model_dump()
        watchlist_doc["user_id"] = user_id

        # If this is the first watchlist, make it default
        existing = await self.watchlist_repo.get_user_watchlists(user_id)
        if not existing:
            watchlist_doc["is_default"] = True

        watchlist_id = await self.watchlist_repo.create(watchlist_doc)
        watchlist = await self.watchlist_repo.get_by_id(watchlist_id)

        logger.info(f"Created watchlist {watchlist_id} for user {user_id}")

        return watchlist

    async def get_user_watchlists(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all watchlists for a user.

        Args:
            user_id: User ID

        Returns:
            List of watchlist documents
        """
        return await self.watchlist_repo.get_user_watchlists(user_id)

    async def get_watchlist(
        self,
        watchlist_id: str,
        user_id: str,
        include_items: bool = True
    ) -> Dict[str, Any]:
        """
        Get watchlist by ID.

        Args:
            watchlist_id: Watchlist ID
            user_id: User ID (for authorization)
            include_items: Whether to include watchlist items

        Returns:
            Watchlist document with items

        Raises:
            HTTPException: If watchlist not found or unauthorized
        """
        watchlist = await self.watchlist_repo.get_by_id(watchlist_id)

        if not watchlist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Watchlist not found"
            )

        if watchlist["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this watchlist"
            )

        if include_items:
            items = await self.item_repo.get_watchlist_items(watchlist_id)
            watchlist["items"] = items

        return watchlist

    async def update_watchlist(
        self,
        watchlist_id: str,
        user_id: str,
        update_data: WatchlistUpdate
    ) -> Dict[str, Any]:
        """
        Update a watchlist.

        Args:
            watchlist_id: Watchlist ID
            user_id: User ID (for authorization)
            update_data: Update data

        Returns:
            Updated watchlist document
        """
        # Check authorization
        await self.get_watchlist(watchlist_id, user_id, include_items=False)

        update_dict = update_data.model_dump(exclude_unset=True)

        # If setting as default, unset other defaults
        if update_dict.get("is_default"):
            await self.watchlist_repo.set_default(watchlist_id, user_id)
            update_dict.pop("is_default", None)

        if update_dict:
            await self.watchlist_repo.update(watchlist_id, update_dict)

        return await self.watchlist_repo.get_by_id(watchlist_id)

    async def delete_watchlist(self, watchlist_id: str, user_id: str) -> bool:
        """
        Delete a watchlist.

        Args:
            watchlist_id: Watchlist ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted
        """
        # Check authorization
        await self.get_watchlist(watchlist_id, user_id, include_items=False)

        # Delete all items first
        items = await self.item_repo.get_watchlist_items(watchlist_id)
        for item in items:
            await self.item_repo.delete(item["_id"])

        # Delete watchlist
        return await self.watchlist_repo.delete(watchlist_id)

    async def add_stock_to_watchlist(
        self,
        watchlist_id: str,
        user_id: str,
        item_data: WatchlistItemCreate
    ) -> Dict[str, Any]:
        """
        Add a stock to watchlist.

        Args:
            watchlist_id: Watchlist ID
            user_id: User ID (for authorization)
            item_data: Item data

        Returns:
            Created item document
        """
        # Check authorization
        await self.get_watchlist(watchlist_id, user_id, include_items=False)

        item_id = await self.item_repo.add_stock(
            watchlist_id,
            item_data.stock_id,
            item_data.notes
        )

        item = await self.item_repo.get_by_id(item_id)

        logger.info(f"Added stock {item_data.stock_id} to watchlist {watchlist_id}")

        return item

    async def remove_stock_from_watchlist(
        self,
        watchlist_id: str,
        stock_id: str,
        user_id: str
    ) -> bool:
        """
        Remove a stock from watchlist.

        Args:
            watchlist_id: Watchlist ID
            stock_id: Stock ID
            user_id: User ID (for authorization)

        Returns:
            True if removed
        """
        # Check authorization
        await self.get_watchlist(watchlist_id, user_id, include_items=False)

        success = await self.item_repo.remove_stock(watchlist_id, stock_id)

        if success:
            logger.info(f"Removed stock {stock_id} from watchlist {watchlist_id}")

        return success
