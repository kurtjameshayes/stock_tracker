"""
Unit tests for Watchlist Service.

Tests watchlist creation, stock management, and access control.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from app.services.watchlist_service import WatchlistService
from app.repositories.watchlist_repository import WatchlistRepository, WatchlistItemRepository
from app.schemas.watchlist import WatchlistCreate, WatchlistUpdate, WatchlistItemCreate
from fastapi import HTTPException


@pytest.fixture
def mock_watchlist_repo():
    """Create mock watchlist repository."""
    return AsyncMock(spec=WatchlistRepository)


@pytest.fixture
def mock_item_repo():
    """Create mock watchlist item repository."""
    return AsyncMock(spec=WatchlistItemRepository)


@pytest.fixture
def watchlist_service(mock_watchlist_repo, mock_item_repo):
    """Create watchlist service with mocked dependencies."""
    return WatchlistService(mock_watchlist_repo, mock_item_repo)


@pytest.fixture
def sample_watchlist_data():
    """Provide sample watchlist data for testing."""
    return {
        "name": "Tech Stocks",
        "description": "My technology watchlist",
        "is_default": False
    }


@pytest.fixture
def sample_watchlist_doc():
    """Provide sample watchlist document as returned from DB."""
    return {
        "_id": "watchlist123",
        "user_id": "user123",
        "name": "Tech Stocks",
        "description": "My technology watchlist",
        "is_default": False,
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def sample_watchlist_item_doc():
    """Provide sample watchlist item document."""
    return {
        "_id": "item123",
        "watchlist_id": "watchlist123",
        "stock_id": "stock123",
        "notes": "Watching for breakout",
        "added_at": datetime.utcnow()
    }


class TestCreateWatchlist:
    """Tests for watchlist creation."""

    @pytest.mark.asyncio
    async def test_create_watchlist_success(self, watchlist_service, mock_watchlist_repo, sample_watchlist_data):
        """Test successful watchlist creation."""
        mock_watchlist_repo.get_user_watchlists.return_value = [{"_id": "existing"}]  # Not first
        mock_watchlist_repo.create.return_value = "watchlist123"
        mock_watchlist_repo.get_by_id.return_value = {
            "_id": "watchlist123",
            "user_id": "user123",
            **sample_watchlist_data
        }

        watchlist_create = MagicMock()
        watchlist_create.model_dump.return_value = sample_watchlist_data

        result = await watchlist_service.create_watchlist("user123", watchlist_create)

        assert result is not None
        assert result["_id"] == "watchlist123"
        assert result["name"] == sample_watchlist_data["name"]
        mock_watchlist_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_first_watchlist_is_default(self, watchlist_service, mock_watchlist_repo, sample_watchlist_data):
        """Test that first watchlist is automatically set as default."""
        mock_watchlist_repo.get_user_watchlists.return_value = []  # No existing watchlists
        mock_watchlist_repo.create.return_value = "watchlist123"
        mock_watchlist_repo.get_by_id.return_value = {
            "_id": "watchlist123",
            "user_id": "user123",
            "is_default": True,
            **sample_watchlist_data
        }

        watchlist_create = MagicMock()
        watchlist_create.model_dump.return_value = sample_watchlist_data.copy()

        await watchlist_service.create_watchlist("user123", watchlist_create)

        call_args = mock_watchlist_repo.create.call_args[0][0]
        assert call_args["is_default"] == True

    @pytest.mark.asyncio
    async def test_create_watchlist_sets_user_id(self, watchlist_service, mock_watchlist_repo, sample_watchlist_data):
        """Test that user_id is properly set on watchlist creation."""
        mock_watchlist_repo.get_user_watchlists.return_value = []
        mock_watchlist_repo.create.return_value = "watchlist123"
        mock_watchlist_repo.get_by_id.return_value = {
            "_id": "watchlist123",
            "user_id": "user456",
            **sample_watchlist_data
        }

        watchlist_create = MagicMock()
        watchlist_create.model_dump.return_value = sample_watchlist_data.copy()

        await watchlist_service.create_watchlist("user456", watchlist_create)

        call_args = mock_watchlist_repo.create.call_args[0][0]
        assert call_args["user_id"] == "user456"


class TestGetWatchlists:
    """Tests for retrieving watchlists."""

    @pytest.mark.asyncio
    async def test_get_user_watchlists(self, watchlist_service, mock_watchlist_repo, sample_watchlist_doc):
        """Test getting all watchlists for a user."""
        mock_watchlist_repo.get_user_watchlists.return_value = [sample_watchlist_doc]

        result = await watchlist_service.get_user_watchlists("user123")

        assert len(result) == 1
        assert result[0]["_id"] == "watchlist123"
        mock_watchlist_repo.get_user_watchlists.assert_called_once_with("user123")

    @pytest.mark.asyncio
    async def test_get_watchlist_success(self, watchlist_service, mock_watchlist_repo, mock_item_repo, sample_watchlist_doc, sample_watchlist_item_doc):
        """Test getting a single watchlist by ID with items."""
        mock_watchlist_repo.get_by_id.return_value = sample_watchlist_doc
        mock_item_repo.get_watchlist_items.return_value = [sample_watchlist_item_doc]

        result = await watchlist_service.get_watchlist("watchlist123", "user123")

        assert result["_id"] == "watchlist123"
        assert "items" in result
        assert len(result["items"]) == 1
        mock_watchlist_repo.get_by_id.assert_called_once_with("watchlist123")

    @pytest.mark.asyncio
    async def test_get_watchlist_without_items(self, watchlist_service, mock_watchlist_repo, mock_item_repo, sample_watchlist_doc):
        """Test getting a watchlist without items."""
        mock_watchlist_repo.get_by_id.return_value = sample_watchlist_doc

        result = await watchlist_service.get_watchlist(
            "watchlist123", "user123", include_items=False
        )

        assert result["_id"] == "watchlist123"
        assert "items" not in result
        mock_item_repo.get_watchlist_items.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_watchlist_not_found(self, watchlist_service, mock_watchlist_repo):
        """Test getting a non-existent watchlist raises 404."""
        mock_watchlist_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await watchlist_service.get_watchlist("nonexistent", "user123")

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_get_watchlist_unauthorized(self, watchlist_service, mock_watchlist_repo, sample_watchlist_doc):
        """Test getting a watchlist belonging to another user raises 403."""
        mock_watchlist_repo.get_by_id.return_value = sample_watchlist_doc

        with pytest.raises(HTTPException) as exc_info:
            await watchlist_service.get_watchlist("watchlist123", "different_user")

        assert exc_info.value.status_code == 403
        assert "not authorized" in str(exc_info.value.detail).lower()


class TestUpdateWatchlist:
    """Tests for updating watchlists."""

    @pytest.mark.asyncio
    async def test_update_watchlist_success(self, watchlist_service, mock_watchlist_repo, sample_watchlist_doc):
        """Test successful watchlist update."""
        mock_watchlist_repo.get_by_id.return_value = sample_watchlist_doc
        mock_watchlist_repo.update.return_value = True

        updated_doc = sample_watchlist_doc.copy()
        updated_doc["name"] = "Updated Name"
        mock_watchlist_repo.get_by_id.side_effect = [sample_watchlist_doc, updated_doc]

        update_data = MagicMock()
        update_data.model_dump.return_value = {"name": "Updated Name"}

        result = await watchlist_service.update_watchlist("watchlist123", "user123", update_data)

        assert result["name"] == "Updated Name"
        mock_watchlist_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_watchlist_set_default(self, watchlist_service, mock_watchlist_repo, sample_watchlist_doc):
        """Test setting a watchlist as default."""
        mock_watchlist_repo.get_by_id.return_value = sample_watchlist_doc
        mock_watchlist_repo.set_default.return_value = True

        updated_doc = sample_watchlist_doc.copy()
        updated_doc["is_default"] = True
        mock_watchlist_repo.get_by_id.side_effect = [sample_watchlist_doc, updated_doc]

        update_data = MagicMock()
        update_data.model_dump.return_value = {"is_default": True}

        result = await watchlist_service.update_watchlist("watchlist123", "user123", update_data)

        mock_watchlist_repo.set_default.assert_called_once_with("watchlist123", "user123")

    @pytest.mark.asyncio
    async def test_update_watchlist_unauthorized(self, watchlist_service, mock_watchlist_repo, sample_watchlist_doc):
        """Test updating a watchlist belonging to another user raises 403."""
        mock_watchlist_repo.get_by_id.return_value = sample_watchlist_doc

        update_data = MagicMock()
        update_data.model_dump.return_value = {"name": "New Name"}

        with pytest.raises(HTTPException) as exc_info:
            await watchlist_service.update_watchlist("watchlist123", "different_user", update_data)

        assert exc_info.value.status_code == 403


class TestDeleteWatchlist:
    """Tests for deleting watchlists."""

    @pytest.mark.asyncio
    async def test_delete_watchlist_success(self, watchlist_service, mock_watchlist_repo, mock_item_repo, sample_watchlist_doc, sample_watchlist_item_doc):
        """Test successful watchlist deletion."""
        mock_watchlist_repo.get_by_id.return_value = sample_watchlist_doc
        mock_item_repo.get_watchlist_items.return_value = [sample_watchlist_item_doc]
        mock_item_repo.delete.return_value = True
        mock_watchlist_repo.delete.return_value = True

        result = await watchlist_service.delete_watchlist("watchlist123", "user123")

        assert result == True
        mock_item_repo.delete.assert_called_once_with("item123")
        mock_watchlist_repo.delete.assert_called_once_with("watchlist123")

    @pytest.mark.asyncio
    async def test_delete_watchlist_removes_all_items(self, watchlist_service, mock_watchlist_repo, mock_item_repo, sample_watchlist_doc):
        """Test that deleting watchlist removes all items first."""
        mock_watchlist_repo.get_by_id.return_value = sample_watchlist_doc
        items = [
            {"_id": "item1"},
            {"_id": "item2"},
            {"_id": "item3"}
        ]
        mock_item_repo.get_watchlist_items.return_value = items
        mock_item_repo.delete.return_value = True
        mock_watchlist_repo.delete.return_value = True

        await watchlist_service.delete_watchlist("watchlist123", "user123")

        assert mock_item_repo.delete.call_count == 3

    @pytest.mark.asyncio
    async def test_delete_watchlist_unauthorized(self, watchlist_service, mock_watchlist_repo, sample_watchlist_doc):
        """Test deleting a watchlist belonging to another user raises 403."""
        mock_watchlist_repo.get_by_id.return_value = sample_watchlist_doc

        with pytest.raises(HTTPException) as exc_info:
            await watchlist_service.delete_watchlist("watchlist123", "different_user")

        assert exc_info.value.status_code == 403


class TestAddStockToWatchlist:
    """Tests for adding stocks to watchlists."""

    @pytest.mark.asyncio
    async def test_add_stock_success(self, watchlist_service, mock_watchlist_repo, mock_item_repo, sample_watchlist_doc, sample_watchlist_item_doc):
        """Test successfully adding a stock to watchlist."""
        mock_watchlist_repo.get_by_id.return_value = sample_watchlist_doc
        mock_item_repo.add_stock.return_value = "item123"
        mock_item_repo.get_by_id.return_value = sample_watchlist_item_doc

        item_data = MagicMock()
        item_data.stock_id = "stock123"
        item_data.notes = "Watching for breakout"

        result = await watchlist_service.add_stock_to_watchlist(
            "watchlist123", "user123", item_data
        )

        assert result is not None
        assert result["_id"] == "item123"
        mock_item_repo.add_stock.assert_called_once_with(
            "watchlist123", "stock123", "Watching for breakout"
        )

    @pytest.mark.asyncio
    async def test_add_stock_unauthorized(self, watchlist_service, mock_watchlist_repo, sample_watchlist_doc):
        """Test adding stock to another user's watchlist raises 403."""
        mock_watchlist_repo.get_by_id.return_value = sample_watchlist_doc

        item_data = MagicMock()
        item_data.stock_id = "stock123"
        item_data.notes = None

        with pytest.raises(HTTPException) as exc_info:
            await watchlist_service.add_stock_to_watchlist(
                "watchlist123", "different_user", item_data
            )

        assert exc_info.value.status_code == 403


class TestRemoveStockFromWatchlist:
    """Tests for removing stocks from watchlists."""

    @pytest.mark.asyncio
    async def test_remove_stock_success(self, watchlist_service, mock_watchlist_repo, mock_item_repo, sample_watchlist_doc):
        """Test successfully removing a stock from watchlist."""
        mock_watchlist_repo.get_by_id.return_value = sample_watchlist_doc
        mock_item_repo.remove_stock.return_value = True

        result = await watchlist_service.remove_stock_from_watchlist(
            "watchlist123", "stock123", "user123"
        )

        assert result == True
        mock_item_repo.remove_stock.assert_called_once_with("watchlist123", "stock123")

    @pytest.mark.asyncio
    async def test_remove_stock_not_found(self, watchlist_service, mock_watchlist_repo, mock_item_repo, sample_watchlist_doc):
        """Test removing a stock that's not in the watchlist."""
        mock_watchlist_repo.get_by_id.return_value = sample_watchlist_doc
        mock_item_repo.remove_stock.return_value = False

        result = await watchlist_service.remove_stock_from_watchlist(
            "watchlist123", "nonexistent_stock", "user123"
        )

        assert result == False

    @pytest.mark.asyncio
    async def test_remove_stock_unauthorized(self, watchlist_service, mock_watchlist_repo, sample_watchlist_doc):
        """Test removing stock from another user's watchlist raises 403."""
        mock_watchlist_repo.get_by_id.return_value = sample_watchlist_doc

        with pytest.raises(HTTPException) as exc_info:
            await watchlist_service.remove_stock_from_watchlist(
                "watchlist123", "stock123", "different_user"
            )

        assert exc_info.value.status_code == 403
