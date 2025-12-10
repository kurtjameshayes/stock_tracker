"""
Unit tests for Stock Service.

Tests stock data management and price operations.
"""

import pytest
from app.services.stock_service import StockService
from app.repositories.stock_repository import StockRepository, StockPriceRepository
from app.schemas.stock import StockCreate, StockPriceCreate
from app.models.enums import DataSource
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_create_stock(test_db, sample_stock_data):
    """Test creating a new stock."""
    stock_repo = StockRepository(test_db)
    price_repo = StockPriceRepository(test_db)

    # Mock Redis client
    redis_mock = AsyncMock()

    stock_service = StockService(stock_repo, price_repo, redis_mock)

    stock_create = StockCreate(**sample_stock_data)
    stock = await stock_service.create_stock(stock_create)

    assert stock is not None
    assert stock["symbol"] == sample_stock_data["symbol"]
    assert stock["name"] == sample_stock_data["name"]
    assert stock["exchange"] == sample_stock_data["exchange"]


@pytest.mark.asyncio
async def test_get_stock_by_symbol(test_db, sample_stock_data):
    """Test retrieving stock by symbol."""
    stock_repo = StockRepository(test_db)
    price_repo = StockPriceRepository(test_db)

    # Mock Redis client
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.setex = AsyncMock()

    stock_service = StockService(stock_repo, price_repo, redis_mock)

    # Create stock first
    stock_create = StockCreate(**sample_stock_data)
    created_stock = await stock_service.create_stock(stock_create)

    # Get by symbol
    stock = await stock_service.get_stock_by_symbol(sample_stock_data["symbol"])

    assert stock is not None
    assert stock["_id"] == created_stock["_id"]
    assert stock["symbol"] == sample_stock_data["symbol"]


@pytest.mark.asyncio
async def test_search_stocks(test_db, sample_stock_data):
    """Test searching stocks."""
    stock_repo = StockRepository(test_db)
    price_repo = StockPriceRepository(test_db)
    redis_mock = AsyncMock()

    stock_service = StockService(stock_repo, price_repo, redis_mock)

    # Create stock
    stock_create = StockCreate(**sample_stock_data)
    await stock_service.create_stock(stock_create)

    # Search
    results = await stock_service.search_stocks("AAP")

    assert len(results) > 0
    assert any(s["symbol"] == "AAPL" for s in results)


@pytest.mark.asyncio
async def test_add_price_data(test_db, sample_stock_data, sample_price_data):
    """Test adding price data for a stock."""
    stock_repo = StockRepository(test_db)
    price_repo = StockPriceRepository(test_db)
    redis_mock = AsyncMock()

    stock_service = StockService(stock_repo, price_repo, redis_mock)

    # Create stock
    stock_create = StockCreate(**sample_stock_data)
    stock = await stock_service.create_stock(stock_create)

    # Add price data
    price_create = StockPriceCreate(
        stock_id=stock["_id"],
        **sample_price_data,
        source=DataSource.MANUAL
    )

    price_id = await stock_service.add_price_data(price_create)

    assert price_id is not None

    # Verify price was added
    latest_price = await price_repo.get_latest_price(stock["_id"])
    assert latest_price is not None
    assert float(latest_price["close"]) == float(sample_price_data["close"])
