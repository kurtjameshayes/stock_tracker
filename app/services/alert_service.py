"""
Alert service for managing price alerts.

Handles alert creation, evaluation, and notification triggering.
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime, timedelta
from decimal import Decimal
from app.repositories.alert_repository import AlertRepository, AlertHistoryRepository
from app.repositories.stock_repository import StockPriceRepository
from app.schemas.alert import AlertCreate, AlertUpdate, AlertTestRequest
from app.models.enums import AlertType, NotificationChannel
from fastapi import HTTPException, status
import logging

if TYPE_CHECKING:
    from app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)


class AlertService:
    """Service for alert management and evaluation."""

    def __init__(
        self,
        alert_repository: AlertRepository,
        history_repository: AlertHistoryRepository,
        price_repository: StockPriceRepository,
        analytics_service: Optional["AnalyticsService"] = None
    ):
        """
        Initialize alert service.

        Args:
            alert_repository: Alert repository instance
            history_repository: Alert history repository instance
            price_repository: Stock price repository instance
            analytics_service: Analytics service instance for technical alerts
        """
        self.alert_repo = alert_repository
        self.history_repo = history_repository
        self.price_repo = price_repository
        self.analytics_service = analytics_service

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
        stock_id = alert["stock_id"]

        try:
            if alert_type == AlertType.PRICE_ABOVE:
                threshold = Decimal(str(condition.get("threshold", 0)))
                return current_price > threshold

            elif alert_type == AlertType.PRICE_BELOW:
                threshold = Decimal(str(condition.get("threshold", 0)))
                return current_price < threshold

            elif alert_type == AlertType.PERCENT_CHANGE_UP:
                percentage = Decimal(str(condition.get("percentage", 0)))
                base_price = await self._get_base_price(stock_id, condition)
                if base_price:
                    change = ((current_price - base_price) / base_price) * 100
                    return change >= percentage
                return False

            elif alert_type == AlertType.PERCENT_CHANGE_DOWN:
                percentage = Decimal(str(condition.get("percentage", 0)))
                base_price = await self._get_base_price(stock_id, condition)
                if base_price:
                    change = ((base_price - current_price) / base_price) * 100
                    return change >= percentage
                return False

            elif alert_type == AlertType.VOLUME_ABOVE:
                threshold = int(condition.get("threshold", 0))
                current_volume = await self._get_current_volume(stock_id)
                return current_volume > threshold if current_volume else False

            elif alert_type == AlertType.VOLUME_BELOW:
                threshold = int(condition.get("threshold", 0))
                current_volume = await self._get_current_volume(stock_id)
                return current_volume < threshold if current_volume else False

            elif alert_type == AlertType.RSI_ABOVE:
                return await self._evaluate_rsi_alert(stock_id, condition, above=True)

            elif alert_type == AlertType.RSI_BELOW:
                return await self._evaluate_rsi_alert(stock_id, condition, above=False)

            elif alert_type == AlertType.MACD_CROSS_UP:
                return await self._evaluate_macd_crossover(stock_id, bullish=True)

            elif alert_type == AlertType.MACD_CROSS_DOWN:
                return await self._evaluate_macd_crossover(stock_id, bullish=False)

            elif alert_type == AlertType.MOVING_AVERAGE_CROSS_UP:
                return await self._evaluate_ma_crossover(stock_id, condition, bullish=True)

            elif alert_type == AlertType.MOVING_AVERAGE_CROSS_DOWN:
                return await self._evaluate_ma_crossover(stock_id, condition, bullish=False)

            elif alert_type == AlertType.SUPPORT_BREAK:
                return await self._evaluate_support_resistance_break(
                    stock_id, current_price, is_support=True
                )

            elif alert_type == AlertType.RESISTANCE_BREAK:
                return await self._evaluate_support_resistance_break(
                    stock_id, current_price, is_support=False
                )

            else:
                logger.warning(f"Unknown alert type: {alert_type}")
                return False

        except Exception as e:
            logger.error(f"Error evaluating alert {alert['_id']}: {e}")
            return False

    async def _get_base_price(
        self,
        stock_id: str,
        condition: Dict[str, Any]
    ) -> Optional[Decimal]:
        """Get base price for percentage change calculation."""
        lookback_days = condition.get("lookback_days", 1)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_days + 1)

        prices = await self.price_repo.get_price_history(stock_id, start_date, end_date)
        if prices and len(prices) > 1:
            return Decimal(str(prices[0].get("close", 0)))
        return None

    async def _get_current_volume(self, stock_id: str) -> Optional[int]:
        """Get current volume for a stock."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=1)

        prices = await self.price_repo.get_price_history(stock_id, start_date, end_date)
        if prices:
            return int(prices[-1].get("volume", 0))
        return None

    async def _evaluate_rsi_alert(
        self,
        stock_id: str,
        condition: Dict[str, Any],
        above: bool
    ) -> bool:
        """Evaluate RSI-based alert."""
        if not self.analytics_service:
            logger.warning("Analytics service not available for RSI alert")
            return False

        threshold = Decimal(str(condition.get("threshold", 70 if above else 30)))
        momentum = await self.analytics_service.get_momentum_indicators(stock_id)

        if momentum.rsi is None:
            return False

        if above:
            return momentum.rsi > threshold
        else:
            return momentum.rsi < threshold

    async def _evaluate_macd_crossover(self, stock_id: str, bullish: bool) -> bool:
        """Evaluate MACD crossover alert."""
        if not self.analytics_service:
            logger.warning("Analytics service not available for MACD alert")
            return False

        # Get price data for crossover detection
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=50)

        prices = await self.price_repo.get_price_history(stock_id, start_date, end_date)
        if not prices or len(prices) < 30:
            return False

        df = self.analytics_service._prices_to_dataframe(prices)
        macd_data = self.analytics_service.calculate_macd(df)

        if macd_data["macd"].empty or macd_data["signal"].empty or len(df) < 2:
            return False

        latest_idx = df.index[-1]
        prev_idx = df.index[-2]

        macd_current = macd_data["macd"].loc[latest_idx]
        signal_current = macd_data["signal"].loc[latest_idx]
        macd_prev = macd_data["macd"].loc[prev_idx]
        signal_prev = macd_data["signal"].loc[prev_idx]

        if bullish:
            # Bullish crossover: MACD crosses above signal line
            return macd_prev < signal_prev and macd_current > signal_current
        else:
            # Bearish crossover: MACD crosses below signal line
            return macd_prev > signal_prev and macd_current < signal_current

    async def _evaluate_ma_crossover(
        self,
        stock_id: str,
        condition: Dict[str, Any],
        bullish: bool
    ) -> bool:
        """Evaluate moving average crossover alert."""
        if not self.analytics_service:
            logger.warning("Analytics service not available for MA crossover alert")
            return False

        fast_period = condition.get("fast_period", 50)
        slow_period = condition.get("slow_period", 200)

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=slow_period + 10)

        prices = await self.price_repo.get_price_history(stock_id, start_date, end_date)
        if not prices or len(prices) < slow_period:
            return False

        df = self.analytics_service._prices_to_dataframe(prices)
        fast_ma = self.analytics_service.calculate_sma(df, fast_period)
        slow_ma = self.analytics_service.calculate_sma(df, slow_period)

        if fast_ma.empty or slow_ma.empty or len(df) < 2:
            return False

        latest_idx = df.index[-1]
        prev_idx = df.index[-2]

        fast_current = fast_ma.loc[latest_idx]
        slow_current = slow_ma.loc[latest_idx]
        fast_prev = fast_ma.loc[prev_idx]
        slow_prev = slow_ma.loc[prev_idx]

        if bullish:
            # Golden cross: fast MA crosses above slow MA
            return fast_prev < slow_prev and fast_current > slow_current
        else:
            # Death cross: fast MA crosses below slow MA
            return fast_prev > slow_prev and fast_current < slow_current

    async def _evaluate_support_resistance_break(
        self,
        stock_id: str,
        current_price: Decimal,
        is_support: bool
    ) -> bool:
        """Evaluate support/resistance break alert."""
        if not self.analytics_service:
            logger.warning("Analytics service not available for support/resistance alert")
            return False

        sr_data = await self.analytics_service.get_support_resistance(stock_id)

        if is_support:
            # Check if price broke below any support level
            for support in sr_data.support_levels:
                if current_price < support:
                    return True
        else:
            # Check if price broke above any resistance level
            for resistance in sr_data.resistance_levels:
                if current_price > resistance:
                    return True

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
