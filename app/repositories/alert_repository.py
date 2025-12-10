"""
Alert repository for database operations.

Handles all database operations related to alerts and alert history.
"""

from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base import BaseRepository
from bson import ObjectId
from datetime import datetime


class AlertRepository(BaseRepository):
    """Repository for alert data operations."""

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize alert repository.

        Args:
            database: MongoDB database instance
        """
        super().__init__(database, "alerts")

    async def get_user_alerts(self, user_id: str, active_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get all alerts for a user.

        Args:
            user_id: User ID
            active_only: If True, only return active alerts

        Returns:
            List of alert documents
        """
        filter_dict = {"user_id": user_id}

        if active_only:
            filter_dict["is_active"] = True

        return await self.find_many(filter_dict, sort=[("created_at", -1)])

    async def get_active_alerts_for_stock(self, stock_id: str) -> List[Dict[str, Any]]:
        """
        Get all active alerts for a specific stock.

        Args:
            stock_id: Stock ID

        Returns:
            List of active alert documents
        """
        filter_dict = {
            "stock_id": stock_id,
            "is_active": True
        }

        return await self.find_many(filter_dict)

    async def mark_triggered(self, alert_id: str) -> bool:
        """
        Mark an alert as triggered.

        Args:
            alert_id: Alert ID

        Returns:
            True if updated successfully
        """
        return await self.update(
            alert_id,
            {
                "triggered_at": datetime.utcnow(),
                "is_active": False  # Deactivate after trigger (can be re-enabled by user)
            }
        )

    async def reactivate(self, alert_id: str) -> bool:
        """
        Reactivate a triggered alert.

        Args:
            alert_id: Alert ID

        Returns:
            True if updated successfully
        """
        return await self.update(
            alert_id,
            {
                "is_active": True,
                "triggered_at": None
            }
        )


class AlertHistoryRepository(BaseRepository):
    """Repository for alert history operations."""

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize alert history repository.

        Args:
            database: MongoDB database instance
        """
        super().__init__(database, "alert_history")

    async def log_trigger(self, history_data: Dict[str, Any]) -> str:
        """
        Log an alert trigger event.

        Args:
            history_data: Alert trigger data

        Returns:
            Created history entry ID
        """
        history_data["timestamp"] = datetime.utcnow()
        return await self.create(history_data)

    async def get_alert_history(self, alert_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get trigger history for an alert.

        Args:
            alert_id: Alert ID
            limit: Maximum results to return

        Returns:
            List of history documents
        """
        return await self.find_many(
            {"alert_id": alert_id},
            limit=limit,
            sort=[("timestamp", -1)]
        )
