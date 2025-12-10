"""
Alert service for managing price alerts.

Handles alert creation, evaluation, and notification triggering.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
from app.repositories.alert_repository import AlertRepository, AlertHistoryRepository
from app.repositories.stock_repository import StockPriceRepository
from app.schemas.alert import AlertCreate, AlertUpdate, AlertTestRequest
from app.models.enums import AlertType, NotificationChannel
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class AlertService:
    """Service for alert management and evaluation."""

    def __init__(
        self,
        alert_repository: AlertRepository,
        history_repository: AlertHistoryRepository,
        price_repository: StockPriceRepository
    ):
        """
        Initialize alert service.

        Args:
            alert_repository: Alert repository instance
            history_repository: Alert history repository instance
            price_repository: Stock price repository instance
        """
        self.alert_repo = alert_repository
        self.history_repo = history_repository
        self.price_repo = price_repository

    async def create_alert(self, user_id: str, alert_data: AlertCreate) -> Dict[str, Any]:
        """
        Create a new alert.

        Args:
            user_id: User ID
            alert_data: Alert creation data

        Returns:
            Created alert document
        """
        alert_doc = alert_data.model_dump()
        alert_doc["user_id"] = user_id
        alert_doc["triggered_at"] = None

        # Convert condition to dict
        if "condition" in alert_doc:
            alert_doc["condition"] = alert_doc["condition"] if isinstance(alert_doc["condition"], dict) else alert_doc["condition"].model_dump()

        alert_id = await self.alert_repo.create(alert_doc)
        alert = await self.alert_repo.get_by_id(alert_id)

        logger.info(f"Created alert {alert_id} for user {user_id}")

        return alert

    async def get_user_alerts(self, user_id: str, active_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get all alerts for a user.

        Args:
            user_id: User ID
            active_only: If True, only return active alerts

        Returns:
            List of alert documents
        """
        return await self.alert_repo.get_user_alerts(user_id, active_only)

    async def get_alert(self, alert_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get alert by ID.

        Args:
            alert_id: Alert ID
            user_id: User ID (for authorization)

        Returns:
            Alert document

        Raises:
            HTTPException: If alert not found or unauthorized
        """
        alert = await self.alert_repo.get_by_id(alert_id)

        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )

        if alert["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this alert"
            )

        return alert

    async def update_alert(
        self,
        alert_id: str,
        user_id: str,
        update_data: AlertUpdate
    ) -> Dict[str, Any]:
        """
        Update an alert.

        Args:
            alert_id: Alert ID
            user_id: User ID (for authorization)
            update_data: Update data

        Returns:
            Updated alert document
        """
        # Check authorization
        await self.get_alert(alert_id, user_id)

        update_dict = update_data.model_dump(exclude_unset=True)

        if "condition" in update_dict and update_dict["condition"]:
            update_dict["condition"] = update_dict["condition"].model_dump()

        await self.alert_repo.update(alert_id, update_dict)

        return await self.alert_repo.get_by_id(alert_id)

    async def delete_alert(self, alert_id: str, user_id: str) -> bool:
        """
        Delete an alert.

        Args:
            alert_id: Alert ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted
        """
        # Check authorization
        await self.get_alert(alert_id, user_id)

        return await self.alert_repo.delete(alert_id)

    async def evaluate_alert(
        self,
        alert: Dict[str, Any],
        current_price: Decimal
    ) -> bool:
        """
        Evaluate if an alert should be triggered.

        Args:
            alert: Alert document
            current_price: Current stock price

        Returns:
            True if alert should trigger
        """
        alert_type = AlertType(alert["type"])
        condition = alert["condition"]

        try:
            if alert_type == AlertType.PRICE_ABOVE:
                threshold = Decimal(str(condition.get("threshold", 0)))
                return current_price > threshold

            elif alert_type == AlertType.PRICE_BELOW:
                threshold = Decimal(str(condition.get("threshold", 0)))
                return current_price < threshold

            elif alert_type == AlertType.PERCENT_CHANGE_UP:
                percentage = Decimal(str(condition.get("percentage", 0)))
                # Would need to compare with previous price
                # Simplified for now
                return False

            elif alert_type == AlertType.PERCENT_CHANGE_DOWN:
                percentage = Decimal(str(condition.get("percentage", 0)))
                # Would need to compare with previous price
                # Simplified for now
                return False

            else:
                # Other alert types not yet implemented
                return False

        except Exception as e:
            logger.error(f"Error evaluating alert {alert['_id']}: {e}")
            return False

    async def trigger_alert(
        self,
        alert: Dict[str, Any],
        triggered_value: Decimal
    ) -> None:
        """
        Trigger an alert and log to history.

        Args:
            alert: Alert document
            triggered_value: Value that triggered the alert
        """
        # Mark alert as triggered
        await self.alert_repo.mark_triggered(alert["_id"])

        # Log to history
        history_data = {
            "alert_id": alert["_id"],
            "stock_id": alert["stock_id"],
            "triggered_value": float(triggered_value),
            "condition": alert["condition"],
            "notifications_sent": alert["notification_channels"]
        }

        await self.history_repo.log_trigger(history_data)

        # Here you would send actual notifications (email, SMS, etc.)
        logger.info(f"Alert {alert['_id']} triggered at {triggered_value}")

    async def check_alerts_for_stock(self, stock_id: str, current_price: Decimal) -> int:
        """
        Check all active alerts for a stock and trigger if needed.

        Args:
            stock_id: Stock ID
            current_price: Current stock price

        Returns:
            Number of alerts triggered
        """
        active_alerts = await self.alert_repo.get_active_alerts_for_stock(stock_id)
        triggered_count = 0

        for alert in active_alerts:
            if await self.evaluate_alert(alert, current_price):
                await self.trigger_alert(alert, current_price)
                triggered_count += 1

        return triggered_count

    async def get_alert_history(self, alert_id: str, user_id: str) -> List[Dict[str, Any]]:
        """
        Get trigger history for an alert.

        Args:
            alert_id: Alert ID
            user_id: User ID (for authorization)

        Returns:
            List of history entries
        """
        # Check authorization
        await self.get_alert(alert_id, user_id)

        return await self.history_repo.get_alert_history(alert_id)
