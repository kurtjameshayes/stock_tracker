"""
Pytest configuration and fixtures.

Provides common fixtures for testing.
"""

import pytest
import asyncio
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db():
    """
    Provide test database connection.

    Creates a test database and cleans up after tests.
    """
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client["stock_tracker_test"]

    yield db

    # Cleanup: Drop test database
    await client.drop_database("stock_tracker_test")
    client.close()


@pytest.fixture
def mock_redis():
    """Provide mock Redis client for testing."""
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.setex = AsyncMock()
    redis_mock.incr = AsyncMock()
    return redis_mock


@pytest.fixture
def sample_user_data():
    """Provide sample user data for testing."""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "password": "TestPass123",
        "tier": "free",
        "preferences": {}
    }


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


@pytest.fixture
def sample_alert_data():
    """Provide sample alert data for testing."""
    return {
        "stock_id": "stock123",
        "type": "price_above",
        "condition": {"threshold": 150.00},
        "notification_channels": ["email"],
        "is_active": True
    }


@pytest.fixture
def sample_portfolio_data():
    """Provide sample portfolio data for testing."""
    return {
        "name": "My Portfolio",
        "description": "Test portfolio",
        "currency": "USD"
    }


@pytest.fixture
def sample_watchlist_data():
    """Provide sample watchlist data for testing."""
    return {
        "name": "Tech Stocks",
        "description": "My technology watchlist",
        "is_default": False
    }


@pytest.fixture
def sample_transaction_data():
    """Provide sample transaction data for testing."""
    return {
        "stock_id": "stock123",
        "type": "buy",
        "quantity": Decimal("100"),
        "price": Decimal("150.00"),
        "fees": Decimal("10.00"),
        "timestamp": datetime.utcnow()
    }
