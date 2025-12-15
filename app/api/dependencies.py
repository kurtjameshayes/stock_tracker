"""
API dependencies for dependency injection.

Provides dependency functions for repositories and services
used across API endpoints.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
import redis.asyncio as aioredis
from app.core.database import get_database, get_redis

# Repositories
from app.repositories.user_repository import UserRepository
from app.repositories.stock_repository import StockRepository, StockPriceRepository
from app.repositories.alert_repository import AlertRepository, AlertHistoryRepository
from app.repositories.watchlist_repository import WatchlistRepository, WatchlistItemRepository
from app.repositories.portfolio_repository import (
    PortfolioRepository, PositionRepository, TransactionRepository
)

# Services
from app.services.user_service import UserService
from app.services.stock_service import StockService
from app.services.data_ingestion_service import DataIngestionService
from app.services.analytics_service import AnalyticsService
from app.services.alert_service import AlertService
from app.services.watchlist_service import WatchlistService
from app.services.portfolio_service import PortfolioService


async def get_user_service(
    db: AsyncIOMotorDatabase = None
) -> UserService:
    """
    Get user service instance.

    Returns:
        UserService instance
    """
    if db is None:
        db = await get_database()

    user_repo = UserRepository(db)
    return UserService(user_repo)


async def get_stock_service(
    db: AsyncIOMotorDatabase = None,
    redis: aioredis.Redis = None
) -> StockService:
    """
    Get stock service instance.

    Returns:
        StockService instance
    """
    if db is None:
        db = await get_database()
    if redis is None:
        redis = await get_redis()

    stock_repo = StockRepository(db)
    price_repo = StockPriceRepository(db)

    return StockService(stock_repo, price_repo, redis)


async def get_data_ingestion_service(
    db: AsyncIOMotorDatabase = None
) -> DataIngestionService:
    """
    Get data ingestion service instance.

    Returns:
        DataIngestionService instance
    """
    if db is None:
        db = await get_database()

    stock_repo = StockRepository(db)
    price_repo = StockPriceRepository(db)

    return DataIngestionService(stock_repo, price_repo)


async def get_analytics_service(
    db: AsyncIOMotorDatabase = None
) -> AnalyticsService:
    """
    Get analytics service instance.

    Returns:
        AnalyticsService instance
    """
    if db is None:
        db = await get_database()

    price_repo = StockPriceRepository(db)

    return AnalyticsService(price_repo)


async def get_alert_service(
    db: AsyncIOMotorDatabase = None
) -> AlertService:
    """
    Get alert service instance.

    Returns:
        AlertService instance
    """
    if db is None:
        db = await get_database()

    alert_repo = AlertRepository(db)
    history_repo = AlertHistoryRepository(db)
    price_repo = StockPriceRepository(db)

    # Create analytics service for technical indicator alerts
    analytics_service = AnalyticsService(price_repo)

    return AlertService(alert_repo, history_repo, price_repo, analytics_service)


async def get_watchlist_service(
    db: AsyncIOMotorDatabase = None
) -> WatchlistService:
    """
    Get watchlist service instance.

    Returns:
        WatchlistService instance
    """
    if db is None:
        db = await get_database()

    watchlist_repo = WatchlistRepository(db)
    item_repo = WatchlistItemRepository(db)

    return WatchlistService(watchlist_repo, item_repo)


async def get_portfolio_service(
    db: AsyncIOMotorDatabase = None
) -> PortfolioService:
    """
    Get portfolio service instance.

    Returns:
        PortfolioService instance
    """
    if db is None:
        db = await get_database()

    portfolio_repo = PortfolioRepository(db)
    position_repo = PositionRepository(db)
    transaction_repo = TransactionRepository(db)

    return PortfolioService(portfolio_repo, position_repo, transaction_repo)
