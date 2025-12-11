"""
Unit tests for Portfolio Service.

Tests portfolio creation, transaction management, and position tracking.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from app.services.portfolio_service import PortfolioService
from app.repositories.portfolio_repository import (
    PortfolioRepository, PositionRepository, TransactionRepository
)
from app.schemas.portfolio import PortfolioCreate, TransactionCreate
from app.models.enums import TransactionType
from fastapi import HTTPException


@pytest.fixture
def mock_portfolio_repo():
    """Create mock portfolio repository."""
    return AsyncMock(spec=PortfolioRepository)


@pytest.fixture
def mock_position_repo():
    """Create mock position repository."""
    return AsyncMock(spec=PositionRepository)


@pytest.fixture
def mock_transaction_repo():
    """Create mock transaction repository."""
    return AsyncMock(spec=TransactionRepository)


@pytest.fixture
def portfolio_service(mock_portfolio_repo, mock_position_repo, mock_transaction_repo):
    """Create portfolio service with mocked dependencies."""
    return PortfolioService(mock_portfolio_repo, mock_position_repo, mock_transaction_repo)


@pytest.fixture
def sample_portfolio_data():
    """Provide sample portfolio data for testing."""
    return {
        "name": "My Portfolio",
        "description": "Test portfolio",
        "currency": "USD"
    }


@pytest.fixture
def sample_portfolio_doc():
    """Provide sample portfolio document as returned from DB."""
    return {
        "_id": "portfolio123",
        "user_id": "user123",
        "name": "My Portfolio",
        "description": "Test portfolio",
        "currency": "USD",
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def sample_position_doc():
    """Provide sample position document."""
    return {
        "_id": "position123",
        "portfolio_id": "portfolio123",
        "stock_id": "stock123",
        "quantity": 100.0,
        "average_cost": 150.0,
        "first_purchase_date": datetime.utcnow().date(),
        "last_update_date": datetime.utcnow()
    }


@pytest.fixture
def sample_transaction_doc():
    """Provide sample transaction document."""
    return {
        "_id": "transaction123",
        "portfolio_id": "portfolio123",
        "stock_id": "stock123",
        "type": "buy",
        "quantity": 100.0,
        "price": 150.0,
        "fees": 10.0,
        "timestamp": datetime.utcnow()
    }


class TestCreatePortfolio:
    """Tests for portfolio creation."""

    @pytest.mark.asyncio
    async def test_create_portfolio_success(self, portfolio_service, mock_portfolio_repo, sample_portfolio_data):
        """Test successful portfolio creation."""
        mock_portfolio_repo.create.return_value = "portfolio123"
        mock_portfolio_repo.get_by_id.return_value = {
            "_id": "portfolio123",
            "user_id": "user123",
            **sample_portfolio_data
        }

        portfolio_create = MagicMock()
        portfolio_create.model_dump.return_value = sample_portfolio_data

        result = await portfolio_service.create_portfolio("user123", portfolio_create)

        assert result is not None
        assert result["_id"] == "portfolio123"
        assert result["user_id"] == "user123"
        assert result["name"] == sample_portfolio_data["name"]
        mock_portfolio_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_portfolio_sets_user_id(self, portfolio_service, mock_portfolio_repo, sample_portfolio_data):
        """Test that user_id is properly set on portfolio creation."""
        mock_portfolio_repo.create.return_value = "portfolio123"
        mock_portfolio_repo.get_by_id.return_value = {
            "_id": "portfolio123",
            "user_id": "user456",
            **sample_portfolio_data
        }

        portfolio_create = MagicMock()
        portfolio_create.model_dump.return_value = sample_portfolio_data.copy()

        await portfolio_service.create_portfolio("user456", portfolio_create)

        call_args = mock_portfolio_repo.create.call_args[0][0]
        assert call_args["user_id"] == "user456"


class TestGetPortfolios:
    """Tests for retrieving portfolios."""

    @pytest.mark.asyncio
    async def test_get_user_portfolios(self, portfolio_service, mock_portfolio_repo, sample_portfolio_doc):
        """Test getting all portfolios for a user."""
        mock_portfolio_repo.get_user_portfolios.return_value = [sample_portfolio_doc]

        result = await portfolio_service.get_user_portfolios("user123")

        assert len(result) == 1
        assert result[0]["_id"] == "portfolio123"
        mock_portfolio_repo.get_user_portfolios.assert_called_once_with("user123")

    @pytest.mark.asyncio
    async def test_get_portfolio_success(self, portfolio_service, mock_portfolio_repo, sample_portfolio_doc):
        """Test getting a single portfolio by ID."""
        mock_portfolio_repo.get_by_id.return_value = sample_portfolio_doc

        result = await portfolio_service.get_portfolio("portfolio123", "user123")

        assert result["_id"] == "portfolio123"
        mock_portfolio_repo.get_by_id.assert_called_once_with("portfolio123")

    @pytest.mark.asyncio
    async def test_get_portfolio_not_found(self, portfolio_service, mock_portfolio_repo):
        """Test getting a non-existent portfolio raises 404."""
        mock_portfolio_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await portfolio_service.get_portfolio("nonexistent", "user123")

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_get_portfolio_unauthorized(self, portfolio_service, mock_portfolio_repo, sample_portfolio_doc):
        """Test getting a portfolio belonging to another user raises 403."""
        mock_portfolio_repo.get_by_id.return_value = sample_portfolio_doc

        with pytest.raises(HTTPException) as exc_info:
            await portfolio_service.get_portfolio("portfolio123", "different_user")

        assert exc_info.value.status_code == 403
        assert "not authorized" in str(exc_info.value.detail).lower()


class TestAddTransaction:
    """Tests for adding transactions."""

    @pytest.mark.asyncio
    async def test_add_buy_transaction_creates_position(
        self, portfolio_service, mock_portfolio_repo, mock_position_repo,
        mock_transaction_repo, sample_portfolio_doc
    ):
        """Test that a BUY transaction creates a new position."""
        mock_portfolio_repo.get_by_id.return_value = sample_portfolio_doc
        mock_position_repo.get_position.return_value = None  # No existing position
        mock_transaction_repo.create_transaction.return_value = "transaction123"
        mock_transaction_repo.get_by_id.return_value = {
            "_id": "transaction123",
            "portfolio_id": "portfolio123",
            "stock_id": "stock123",
            "type": "buy",
            "quantity": 100.0,
            "price": 150.0,
            "fees": 10.0
        }
        mock_position_repo.create.return_value = "position123"

        transaction_create = MagicMock()
        transaction_create.model_dump.return_value = {
            "stock_id": "stock123",
            "type": "buy",
            "quantity": Decimal("100"),
            "price": Decimal("150"),
            "fees": Decimal("10"),
            "timestamp": datetime.utcnow()
        }

        result = await portfolio_service.add_transaction(
            "portfolio123", "user123", transaction_create
        )

        assert result is not None
        mock_position_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_buy_transaction_updates_existing_position(
        self, portfolio_service, mock_portfolio_repo, mock_position_repo,
        mock_transaction_repo, sample_portfolio_doc, sample_position_doc
    ):
        """Test that a BUY transaction updates existing position with averaged cost."""
        mock_portfolio_repo.get_by_id.return_value = sample_portfolio_doc
        mock_position_repo.get_position.return_value = sample_position_doc  # Existing position
        mock_transaction_repo.create_transaction.return_value = "transaction123"
        mock_transaction_repo.get_by_id.return_value = {
            "_id": "transaction123",
            "portfolio_id": "portfolio123",
            "stock_id": "stock123",
            "type": "buy",
            "quantity": 50.0,
            "price": 160.0
        }
        mock_position_repo.update.return_value = True

        transaction_create = MagicMock()
        transaction_create.model_dump.return_value = {
            "stock_id": "stock123",
            "type": "buy",
            "quantity": Decimal("50"),
            "price": Decimal("160"),
            "fees": None,
            "timestamp": datetime.utcnow()
        }

        await portfolio_service.add_transaction(
            "portfolio123", "user123", transaction_create
        )

        # Should update existing position
        mock_position_repo.update.assert_called_once()
        update_call = mock_position_repo.update.call_args
        update_data = update_call[0][1]

        # New qty should be 100 + 50 = 150
        assert update_data["quantity"] == 150.0
        # New avg should be ((100 * 150) + (50 * 160)) / 150 = 153.33...
        expected_avg = ((100 * 150) + (50 * 160)) / 150
        assert abs(update_data["average_cost"] - expected_avg) < 0.01

    @pytest.mark.asyncio
    async def test_add_sell_transaction_reduces_position(
        self, portfolio_service, mock_portfolio_repo, mock_position_repo,
        mock_transaction_repo, sample_portfolio_doc, sample_position_doc
    ):
        """Test that a SELL transaction reduces position quantity."""
        mock_portfolio_repo.get_by_id.return_value = sample_portfolio_doc
        mock_position_repo.get_position.return_value = sample_position_doc  # 100 shares
        mock_transaction_repo.create_transaction.return_value = "transaction123"
        mock_transaction_repo.get_by_id.return_value = {
            "_id": "transaction123",
            "portfolio_id": "portfolio123",
            "stock_id": "stock123",
            "type": "sell",
            "quantity": 30.0,
            "price": 160.0
        }
        mock_position_repo.update.return_value = True

        transaction_create = MagicMock()
        transaction_create.model_dump.return_value = {
            "stock_id": "stock123",
            "type": "sell",
            "quantity": Decimal("30"),
            "price": Decimal("160"),
            "fees": None,
            "timestamp": datetime.utcnow()
        }

        await portfolio_service.add_transaction(
            "portfolio123", "user123", transaction_create
        )

        mock_position_repo.update.assert_called_once()
        update_call = mock_position_repo.update.call_args
        update_data = update_call[0][1]

        # New qty should be 100 - 30 = 70
        assert update_data["quantity"] == 70.0

    @pytest.mark.asyncio
    async def test_add_sell_transaction_closes_position(
        self, portfolio_service, mock_portfolio_repo, mock_position_repo,
        mock_transaction_repo, sample_portfolio_doc, sample_position_doc
    ):
        """Test that selling all shares closes the position."""
        mock_portfolio_repo.get_by_id.return_value = sample_portfolio_doc
        mock_position_repo.get_position.return_value = sample_position_doc  # 100 shares
        mock_transaction_repo.create_transaction.return_value = "transaction123"
        mock_transaction_repo.get_by_id.return_value = {
            "_id": "transaction123",
            "portfolio_id": "portfolio123",
            "stock_id": "stock123",
            "type": "sell",
            "quantity": 100.0,
            "price": 160.0
        }
        mock_position_repo.delete.return_value = True

        transaction_create = MagicMock()
        transaction_create.model_dump.return_value = {
            "stock_id": "stock123",
            "type": "sell",
            "quantity": Decimal("100"),
            "price": Decimal("160"),
            "fees": None,
            "timestamp": datetime.utcnow()
        }

        await portfolio_service.add_transaction(
            "portfolio123", "user123", transaction_create
        )

        # Should delete position when qty becomes 0
        mock_position_repo.delete.assert_called_once_with("position123")

    @pytest.mark.asyncio
    async def test_add_transaction_unauthorized(
        self, portfolio_service, mock_portfolio_repo, sample_portfolio_doc
    ):
        """Test adding transaction to another user's portfolio raises 403."""
        mock_portfolio_repo.get_by_id.return_value = sample_portfolio_doc

        transaction_create = MagicMock()
        transaction_create.model_dump.return_value = {
            "stock_id": "stock123",
            "type": "buy",
            "quantity": Decimal("100"),
            "price": Decimal("150")
        }

        with pytest.raises(HTTPException) as exc_info:
            await portfolio_service.add_transaction(
                "portfolio123", "different_user", transaction_create
            )

        assert exc_info.value.status_code == 403


class TestGetPortfolioPositions:
    """Tests for getting portfolio positions."""

    @pytest.mark.asyncio
    async def test_get_portfolio_positions_success(
        self, portfolio_service, mock_portfolio_repo, mock_position_repo,
        sample_portfolio_doc, sample_position_doc
    ):
        """Test getting all positions in a portfolio."""
        mock_portfolio_repo.get_by_id.return_value = sample_portfolio_doc
        mock_position_repo.get_portfolio_positions.return_value = [sample_position_doc]

        result = await portfolio_service.get_portfolio_positions("portfolio123", "user123")

        assert len(result) == 1
        assert result[0]["stock_id"] == "stock123"
        mock_position_repo.get_portfolio_positions.assert_called_once_with("portfolio123")

    @pytest.mark.asyncio
    async def test_get_portfolio_positions_unauthorized(
        self, portfolio_service, mock_portfolio_repo, sample_portfolio_doc
    ):
        """Test getting positions from another user's portfolio raises 403."""
        mock_portfolio_repo.get_by_id.return_value = sample_portfolio_doc

        with pytest.raises(HTTPException) as exc_info:
            await portfolio_service.get_portfolio_positions("portfolio123", "different_user")

        assert exc_info.value.status_code == 403


class TestGetPortfolioTransactions:
    """Tests for getting portfolio transactions."""

    @pytest.mark.asyncio
    async def test_get_portfolio_transactions_success(
        self, portfolio_service, mock_portfolio_repo, mock_transaction_repo,
        sample_portfolio_doc, sample_transaction_doc
    ):
        """Test getting all transactions in a portfolio."""
        mock_portfolio_repo.get_by_id.return_value = sample_portfolio_doc
        mock_transaction_repo.get_portfolio_transactions.return_value = [sample_transaction_doc]

        result = await portfolio_service.get_portfolio_transactions(
            "portfolio123", "user123", skip=0, limit=100
        )

        assert len(result) == 1
        assert result[0]["_id"] == "transaction123"
        mock_transaction_repo.get_portfolio_transactions.assert_called_once_with(
            "portfolio123", 0, 100
        )

    @pytest.mark.asyncio
    async def test_get_portfolio_transactions_with_pagination(
        self, portfolio_service, mock_portfolio_repo, mock_transaction_repo,
        sample_portfolio_doc
    ):
        """Test getting transactions with pagination."""
        mock_portfolio_repo.get_by_id.return_value = sample_portfolio_doc
        mock_transaction_repo.get_portfolio_transactions.return_value = []

        await portfolio_service.get_portfolio_transactions(
            "portfolio123", "user123", skip=10, limit=20
        )

        mock_transaction_repo.get_portfolio_transactions.assert_called_once_with(
            "portfolio123", 10, 20
        )

    @pytest.mark.asyncio
    async def test_get_portfolio_transactions_unauthorized(
        self, portfolio_service, mock_portfolio_repo, sample_portfolio_doc
    ):
        """Test getting transactions from another user's portfolio raises 403."""
        mock_portfolio_repo.get_by_id.return_value = sample_portfolio_doc

        with pytest.raises(HTTPException) as exc_info:
            await portfolio_service.get_portfolio_transactions(
                "portfolio123", "different_user"
            )

        assert exc_info.value.status_code == 403
