"""
Unit tests for Stock Service.

Tests stock data management and price operations.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from app.services.stock_service import StockService
from app.repositories.stock_repository import StockRepository, StockPriceRepository
from app.schemas.stock import StockCreate, StockPriceCreate
from app.models.enums import DataSource


@pytest.fixture
def mock_stock_repo():
    """Create mock stock repository."""
    return AsyncMock(spec=StockRepository)


@pytest.fixture
def mock_price_repo():
    """Create mock price repository."""
    return AsyncMock(spec=StockPriceRepository)


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.setex = AsyncMock()
    return redis_mock


@pytest.fixture
def stock_service(mock_stock_repo, mock_price_repo, mock_redis):
    """Create stock service with mocked dependencies."""
    return StockService(mock_stock_repo, mock_price_repo, mock_redis)


@pytest.fixture
def sample_stock_data():
    """Provide sample stock data for testing."""
    return {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "exchange": "NASDAQ",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "currency": "USD",
        "metadata": {}
    }


@pytest.fixture
def sample_stock_doc():
    """Provide sample stock document as returned from DB."""
    return {
        "_id": "stock123",
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "exchange": "NASDAQ",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "currency": "USD",
        "metadata": {},
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def sample_price_data():
    """Provide sample price data for testing."""
    return {
        "open": Decimal("150.00"),
        "high": Decimal("152.50"),
        "low": Decimal("149.00"),
        "close": Decimal("151.25"),
        "volume": 100000000,
        "adjusted_close": Decimal("151.25"),
        "timestamp": datetime.utcnow(),
        "source": "manual"
    }


class TestCreateStock:
    """Tests for stock creation."""

    @pytest.mark.asyncio
    async def test_create_stock_success(self, stock_service, mock_stock_repo, sample_stock_data, sample_stock_doc):
        """Test creating a new stock."""
        mock_stock_repo.create.return_value = "stock123"
        mock_stock_repo.get_by_id.return_value = sample_stock_doc

        stock_create = MagicMock()
        stock_create.model_dump.return_value = sample_stock_data

        stock = await stock_service.create_stock(stock_create)

        assert stock is not None
        assert stock["symbol"] == sample_stock_data["symbol"]
        assert stock["name"] == sample_stock_data["name"]
        assert stock["exchange"] == sample_stock_data["exchange"]
        mock_stock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_stock_returns_created_doc(self, stock_service, mock_stock_repo, sample_stock_data, sample_stock_doc):
        """Test that create_stock returns the full document."""
        mock_stock_repo.create.return_value = "stock123"
        mock_stock_repo.get_by_id.return_value = sample_stock_doc

        stock_create = MagicMock()
        stock_create.model_dump.return_value = sample_stock_data

        stock = await stock_service.create_stock(stock_create)

        assert stock["_id"] == "stock123"
        mock_stock_repo.get_by_id.assert_called_once_with("stock123")


class TestGetStockBySymbol:
    """Tests for retrieving stocks by symbol."""

    @pytest.mark.asyncio
    async def test_get_stock_by_symbol_cache_miss(self, stock_service, mock_stock_repo, mock_redis, sample_stock_doc):
        """Test retrieving stock by symbol with cache miss."""
        mock_redis.get.return_value = None
        mock_stock_repo.get_by_symbol.return_value = sample_stock_doc

        stock = await stock_service.get_stock_by_symbol("AAPL")

        assert stock is not None
        assert stock["symbol"] == "AAPL"
        mock_stock_repo.get_by_symbol.assert_called_once_with("AAPL")

    @pytest.mark.asyncio
    async def test_get_stock_by_symbol_cache_hit(self, stock_service, mock_stock_repo, mock_redis, sample_stock_doc):
        """Test retrieving stock by symbol with cache hit."""
        import json
        mock_redis.get.return_value = json.dumps(sample_stock_doc, default=str)

        stock = await stock_service.get_stock_by_symbol("AAPL")

        assert stock is not None
        # Repository should not be called if cache hit
        mock_stock_repo.get_by_symbol.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_stock_by_symbol_not_found(self, stock_service, mock_stock_repo, mock_redis):
        """Test retrieving non-existent stock raises 404."""
        from fastapi import HTTPException
        mock_redis.get.return_value = None
        mock_stock_repo.get_by_symbol.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await stock_service.get_stock_by_symbol("INVALID")

        assert exc_info.value.status_code == 404


class TestSearchStocks:
    """Tests for searching stocks."""

    @pytest.mark.asyncio
    async def test_search_stocks_success(self, stock_service, mock_stock_repo, sample_stock_doc):
        """Test searching stocks returns results."""
        mock_stock_repo.search_stocks.return_value = [sample_stock_doc]

        results = await stock_service.search_stocks("AAP")

        assert len(results) == 1
        assert results[0]["symbol"] == "AAPL"
        mock_stock_repo.search_stocks.assert_called_once_with("AAP", 20)

    @pytest.mark.asyncio
    async def test_search_stocks_with_limit(self, stock_service, mock_stock_repo):
        """Test searching stocks with custom limit."""
        mock_stock_repo.search_stocks.return_value = []

        await stock_service.search_stocks("AAP", limit=10)

        mock_stock_repo.search_stocks.assert_called_once_with("AAP", 10)

    @pytest.mark.asyncio
    async def test_search_stocks_no_results(self, stock_service, mock_stock_repo):
        """Test searching stocks with no matches returns empty list."""
        mock_stock_repo.search_stocks.return_value = []

        results = await stock_service.search_stocks("XXXXXX")

        assert results == []


class TestAddPriceData:
    """Tests for adding price data."""

    @pytest.mark.asyncio
    async def test_add_price_data_success(self, stock_service, mock_price_repo, sample_price_data):
        """Test adding price data for a stock."""
        mock_price_repo.create_price.return_value = "price123"

        price_create = MagicMock()
        price_create.model_dump.return_value = {
            "stock_id": "stock123",
            **sample_price_data
        }

        price_id = await stock_service.add_price_data(price_create)

        assert price_id == "price123"
        mock_price_repo.create_price.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_price_data_converts_decimals(self, stock_service, mock_price_repo, sample_price_data):
        """Test that price data decimals are properly handled."""
        mock_price_repo.create_price.return_value = "price123"

        price_create = MagicMock()
        price_create.model_dump.return_value = {
            "stock_id": "stock123",
            **sample_price_data
        }

        await stock_service.add_price_data(price_create)

        call_args = mock_price_repo.create_price.call_args[0][0]
        assert "stock_id" in call_args


class TestGetPriceHistory:
    """Tests for retrieving price history."""

    @pytest.mark.asyncio
    async def test_get_price_history_success(self, stock_service, mock_stock_repo, mock_price_repo, sample_stock_doc):
        """Test getting price history for a stock."""
        mock_stock_repo.get_by_symbol.return_value = sample_stock_doc
        mock_price_repo.get_price_history.return_value = [
            {"close": 150.0, "timestamp": datetime.utcnow()},
            {"close": 151.0, "timestamp": datetime.utcnow()}
        ]

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        history = await stock_service.get_price_history("AAPL", start_date, end_date)

        assert len(history) == 2
        mock_price_repo.get_price_history.assert_called_once()
