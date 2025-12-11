"""
Unit tests for Alert Service.

Tests alert creation, evaluation, triggering, and management.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.alert_service import AlertService
from app.repositories.alert_repository import AlertRepository, AlertHistoryRepository
from app.repositories.stock_repository import StockPriceRepository
from app.schemas.alert import AlertCreate, AlertUpdate
from app.models.enums import AlertType, NotificationChannel
from fastapi import HTTPException


@pytest.fixture
def mock_alert_repo():
    """Create mock alert repository."""
    return AsyncMock(spec=AlertRepository)


@pytest.fixture
def mock_history_repo():
    """Create mock alert history repository."""
    return AsyncMock(spec=AlertHistoryRepository)


@pytest.fixture
def mock_price_repo():
    """Create mock price repository."""
    return AsyncMock(spec=StockPriceRepository)


@pytest.fixture
def alert_service(mock_alert_repo, mock_history_repo, mock_price_repo):
    """Create alert service with mocked dependencies."""
    return AlertService(mock_alert_repo, mock_history_repo, mock_price_repo)


@pytest.fixture
def sample_alert_data():
    """Provide sample alert data for testing."""
    return {
        "stock_id": "stock123",
        "type": AlertType.PRICE_ABOVE,
        "condition": {"threshold": 150.00},
        "notification_channels": [NotificationChannel.EMAIL],
        "is_active": True
    }


@pytest.fixture
def sample_alert_doc():
    """Provide sample alert document as returned from DB."""
    return {
        "_id": "alert123",
        "user_id": "user123",
        "stock_id": "stock123",
        "type": "price_above",
        "condition": {"threshold": 150.00},
        "notification_channels": ["email"],
        "is_active": True,
        "triggered_at": None,
        "created_at": datetime.utcnow()
    }


class TestCreateAlert:
    """Tests for alert creation."""

    @pytest.mark.asyncio
    async def test_create_alert_success(self, alert_service, mock_alert_repo, sample_alert_data):
        """Test successful alert creation."""
        mock_alert_repo.create.return_value = "alert123"
        mock_alert_repo.get_by_id.return_value = {
            "_id": "alert123",
            "user_id": "user123",
            **sample_alert_data
        }

        alert_create = MagicMock()
        alert_create.model_dump.return_value = sample_alert_data

        result = await alert_service.create_alert("user123", alert_create)

        assert result is not None
        assert result["_id"] == "alert123"
        assert result["user_id"] == "user123"
        mock_alert_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_alert_sets_user_id(self, alert_service, mock_alert_repo, sample_alert_data):
        """Test that user_id is properly set on alert creation."""
        mock_alert_repo.create.return_value = "alert123"
        mock_alert_repo.get_by_id.return_value = {
            "_id": "alert123",
            "user_id": "user456",
            **sample_alert_data
        }

        alert_create = MagicMock()
        alert_create.model_dump.return_value = sample_alert_data.copy()

        await alert_service.create_alert("user456", alert_create)

        # Verify the user_id was added to the document
        call_args = mock_alert_repo.create.call_args[0][0]
        assert call_args["user_id"] == "user456"


class TestGetAlerts:
    """Tests for retrieving alerts."""

    @pytest.mark.asyncio
    async def test_get_user_alerts(self, alert_service, mock_alert_repo, sample_alert_doc):
        """Test getting all alerts for a user."""
        mock_alert_repo.get_user_alerts.return_value = [sample_alert_doc]

        result = await alert_service.get_user_alerts("user123")

        assert len(result) == 1
        assert result[0]["_id"] == "alert123"
        mock_alert_repo.get_user_alerts.assert_called_once_with("user123", False)

    @pytest.mark.asyncio
    async def test_get_user_alerts_active_only(self, alert_service, mock_alert_repo, sample_alert_doc):
        """Test getting only active alerts for a user."""
        mock_alert_repo.get_user_alerts.return_value = [sample_alert_doc]

        await alert_service.get_user_alerts("user123", active_only=True)

        mock_alert_repo.get_user_alerts.assert_called_once_with("user123", True)

    @pytest.mark.asyncio
    async def test_get_alert_success(self, alert_service, mock_alert_repo, sample_alert_doc):
        """Test getting a single alert by ID."""
        mock_alert_repo.get_by_id.return_value = sample_alert_doc

        result = await alert_service.get_alert("alert123", "user123")

        assert result["_id"] == "alert123"
        mock_alert_repo.get_by_id.assert_called_once_with("alert123")

    @pytest.mark.asyncio
    async def test_get_alert_not_found(self, alert_service, mock_alert_repo):
        """Test getting a non-existent alert raises 404."""
        mock_alert_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await alert_service.get_alert("nonexistent", "user123")

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_get_alert_unauthorized(self, alert_service, mock_alert_repo, sample_alert_doc):
        """Test getting an alert belonging to another user raises 403."""
        mock_alert_repo.get_by_id.return_value = sample_alert_doc

        with pytest.raises(HTTPException) as exc_info:
            await alert_service.get_alert("alert123", "different_user")

        assert exc_info.value.status_code == 403
        assert "not authorized" in str(exc_info.value.detail).lower()


class TestUpdateAlert:
    """Tests for updating alerts."""

    @pytest.mark.asyncio
    async def test_update_alert_success(self, alert_service, mock_alert_repo, sample_alert_doc):
        """Test successful alert update."""
        mock_alert_repo.get_by_id.return_value = sample_alert_doc
        mock_alert_repo.update.return_value = True

        updated_doc = sample_alert_doc.copy()
        updated_doc["is_active"] = False
        mock_alert_repo.get_by_id.side_effect = [sample_alert_doc, updated_doc]

        update_data = MagicMock()
        update_data.model_dump.return_value = {"is_active": False}

        result = await alert_service.update_alert("alert123", "user123", update_data)

        assert result["is_active"] == False
        mock_alert_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_alert_unauthorized(self, alert_service, mock_alert_repo, sample_alert_doc):
        """Test updating an alert belonging to another user raises 403."""
        mock_alert_repo.get_by_id.return_value = sample_alert_doc

        update_data = MagicMock()
        update_data.model_dump.return_value = {"is_active": False}

        with pytest.raises(HTTPException) as exc_info:
            await alert_service.update_alert("alert123", "different_user", update_data)

        assert exc_info.value.status_code == 403


class TestDeleteAlert:
    """Tests for deleting alerts."""

    @pytest.mark.asyncio
    async def test_delete_alert_success(self, alert_service, mock_alert_repo, sample_alert_doc):
        """Test successful alert deletion."""
        mock_alert_repo.get_by_id.return_value = sample_alert_doc
        mock_alert_repo.delete.return_value = True

        result = await alert_service.delete_alert("alert123", "user123")

        assert result == True
        mock_alert_repo.delete.assert_called_once_with("alert123")

    @pytest.mark.asyncio
    async def test_delete_alert_unauthorized(self, alert_service, mock_alert_repo, sample_alert_doc):
        """Test deleting an alert belonging to another user raises 403."""
        mock_alert_repo.get_by_id.return_value = sample_alert_doc

        with pytest.raises(HTTPException) as exc_info:
            await alert_service.delete_alert("alert123", "different_user")

        assert exc_info.value.status_code == 403


class TestEvaluateAlert:
    """Tests for alert evaluation logic."""

    @pytest.mark.asyncio
    async def test_evaluate_price_above_triggered(self, alert_service):
        """Test PRICE_ABOVE alert triggers when price exceeds threshold."""
        alert = {
            "_id": "alert123",
            "type": "price_above",
            "condition": {"threshold": 100.00}
        }

        result = await alert_service.evaluate_alert(alert, Decimal("105.00"))

        assert result == True

    @pytest.mark.asyncio
    async def test_evaluate_price_above_not_triggered(self, alert_service):
        """Test PRICE_ABOVE alert doesn't trigger when price is below threshold."""
        alert = {
            "_id": "alert123",
            "type": "price_above",
            "condition": {"threshold": 100.00}
        }

        result = await alert_service.evaluate_alert(alert, Decimal("95.00"))

        assert result == False

    @pytest.mark.asyncio
    async def test_evaluate_price_below_triggered(self, alert_service):
        """Test PRICE_BELOW alert triggers when price is below threshold."""
        alert = {
            "_id": "alert123",
            "type": "price_below",
            "condition": {"threshold": 100.00}
        }

        result = await alert_service.evaluate_alert(alert, Decimal("95.00"))

        assert result == True

    @pytest.mark.asyncio
    async def test_evaluate_price_below_not_triggered(self, alert_service):
        """Test PRICE_BELOW alert doesn't trigger when price exceeds threshold."""
        alert = {
            "_id": "alert123",
            "type": "price_below",
            "condition": {"threshold": 100.00}
        }

        result = await alert_service.evaluate_alert(alert, Decimal("105.00"))

        assert result == False

    @pytest.mark.asyncio
    async def test_evaluate_unimplemented_alert_type(self, alert_service):
        """Test that unimplemented alert types return False."""
        alert = {
            "_id": "alert123",
            "type": "volume_above",
            "condition": {"threshold": 1000000}
        }

        result = await alert_service.evaluate_alert(alert, Decimal("100.00"))

        assert result == False

    @pytest.mark.asyncio
    async def test_evaluate_alert_with_invalid_condition(self, alert_service):
        """Test that invalid conditions don't cause crashes."""
        alert = {
            "_id": "alert123",
            "type": "price_above",
            "condition": {}  # Missing threshold
        }

        # Should return False, not raise exception
        result = await alert_service.evaluate_alert(alert, Decimal("100.00"))

        assert result == False


class TestTriggerAlert:
    """Tests for alert triggering."""

    @pytest.mark.asyncio
    async def test_trigger_alert_success(self, alert_service, mock_alert_repo, mock_history_repo, sample_alert_doc):
        """Test successful alert triggering."""
        mock_alert_repo.mark_triggered.return_value = True
        mock_history_repo.log_trigger.return_value = "history123"

        await alert_service.trigger_alert(sample_alert_doc, Decimal("155.00"))

        mock_alert_repo.mark_triggered.assert_called_once_with("alert123")
        mock_history_repo.log_trigger.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_alert_logs_correct_data(self, alert_service, mock_alert_repo, mock_history_repo, sample_alert_doc):
        """Test that alert triggering logs correct history data."""
        mock_alert_repo.mark_triggered.return_value = True
        mock_history_repo.log_trigger.return_value = "history123"

        await alert_service.trigger_alert(sample_alert_doc, Decimal("155.00"))

        call_args = mock_history_repo.log_trigger.call_args[0][0]
        assert call_args["alert_id"] == "alert123"
        assert call_args["stock_id"] == "stock123"
        assert call_args["triggered_value"] == 155.00


class TestCheckAlertsForStock:
    """Tests for bulk alert checking."""

    @pytest.mark.asyncio
    async def test_check_alerts_for_stock_triggers_matching(self, alert_service, mock_alert_repo, mock_history_repo):
        """Test that matching alerts are triggered."""
        active_alerts = [
            {
                "_id": "alert1",
                "type": "price_above",
                "condition": {"threshold": 100.00},
                "stock_id": "stock123",
                "notification_channels": ["email"]
            },
            {
                "_id": "alert2",
                "type": "price_below",
                "condition": {"threshold": 90.00},
                "stock_id": "stock123",
                "notification_channels": ["email"]
            }
        ]
        mock_alert_repo.get_active_alerts_for_stock.return_value = active_alerts
        mock_alert_repo.mark_triggered.return_value = True
        mock_history_repo.log_trigger.return_value = "history123"

        # Price is 105, so only price_above alert should trigger
        triggered_count = await alert_service.check_alerts_for_stock("stock123", Decimal("105.00"))

        assert triggered_count == 1

    @pytest.mark.asyncio
    async def test_check_alerts_for_stock_no_matches(self, alert_service, mock_alert_repo):
        """Test when no alerts match the current price."""
        active_alerts = [
            {
                "_id": "alert1",
                "type": "price_above",
                "condition": {"threshold": 200.00},
                "stock_id": "stock123",
                "notification_channels": ["email"]
            }
        ]
        mock_alert_repo.get_active_alerts_for_stock.return_value = active_alerts

        # Price is 105, threshold is 200, so no trigger
        triggered_count = await alert_service.check_alerts_for_stock("stock123", Decimal("105.00"))

        assert triggered_count == 0


class TestGetAlertHistory:
    """Tests for alert history retrieval."""

    @pytest.mark.asyncio
    async def test_get_alert_history_success(self, alert_service, mock_alert_repo, mock_history_repo, sample_alert_doc):
        """Test getting alert history."""
        mock_alert_repo.get_by_id.return_value = sample_alert_doc
        mock_history_repo.get_alert_history.return_value = [
            {"alert_id": "alert123", "triggered_value": 155.00}
        ]

        result = await alert_service.get_alert_history("alert123", "user123")

        assert len(result) == 1
        mock_history_repo.get_alert_history.assert_called_once_with("alert123")

    @pytest.mark.asyncio
    async def test_get_alert_history_unauthorized(self, alert_service, mock_alert_repo, sample_alert_doc):
        """Test getting alert history for another user's alert raises 403."""
        mock_alert_repo.get_by_id.return_value = sample_alert_doc

        with pytest.raises(HTTPException) as exc_info:
            await alert_service.get_alert_history("alert123", "different_user")

        assert exc_info.value.status_code == 403
