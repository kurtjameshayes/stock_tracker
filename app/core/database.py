"""
Database connection and initialization.

Handles MongoDB and Redis connections with connection pooling
and health checks.
"""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import redis.asyncio as aioredis
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    """
    Database connection manager.

    Handles MongoDB and Redis connections with proper initialization
    and cleanup.
    """

    def __init__(self):
        """Initialize database connection attributes."""
        self.mongodb_client: Optional[AsyncIOMotorClient] = None
        self.mongodb: Optional[AsyncIOMotorDatabase] = None
        self.redis_client: Optional[aioredis.Redis] = None

    async def connect_mongodb(self) -> None:
        """
        Connect to MongoDB.

        Establishes connection with configured pool size and
        validates connection with a ping.
        """
        try:
            self.mongodb_client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
                maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
            )
            self.mongodb = self.mongodb_client[settings.MONGODB_DB_NAME]

            # Test connection
            await self.mongodb_client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")

            # Create indexes
            await self._create_indexes()

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def connect_redis(self) -> None:
        """
        Connect to Redis.

        Establishes connection and validates with a ping.
        """
        try:
            self.redis_client = await aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )

            # Test connection
            await self.redis_client.ping()
            logger.info("Connected to Redis")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def close_mongodb(self) -> None:
        """Close MongoDB connection."""
        if self.mongodb_client:
            self.mongodb_client.close()
            logger.info("Closed MongoDB connection")

    async def close_redis(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Closed Redis connection")

    async def _create_indexes(self) -> None:
        """
        Create database indexes for optimal query performance.

        Creates indexes on frequently queried fields and ensures
        unique constraints where needed.
        """
        try:
            # Users collection indexes
            await self.mongodb.users.create_index("email", unique=True)
            await self.mongodb.users.create_index("created_at")

            # Stocks collection indexes
            await self.mongodb.stocks.create_index("symbol", unique=True)
            await self.mongodb.stocks.create_index("exchange")
            await self.mongodb.stocks.create_index([("name", "text"), ("symbol", "text")])

            # Stock prices collection indexes (time-series optimized)
            await self.mongodb.stock_prices.create_index([("stock_id", 1), ("timestamp", -1)])
            await self.mongodb.stock_prices.create_index("timestamp")
            await self.mongodb.stock_prices.create_index("stock_id")

            # Alerts collection indexes
            await self.mongodb.alerts.create_index([("user_id", 1), ("is_active", 1)])
            await self.mongodb.alerts.create_index([("stock_id", 1), ("is_active", 1)])
            await self.mongodb.alerts.create_index("created_at")

            # Watchlists collection indexes
            await self.mongodb.watchlists.create_index([("user_id", 1), ("is_default", 1)])

            # Portfolios collection indexes
            await self.mongodb.portfolios.create_index("user_id")

            # Transactions collection indexes
            await self.mongodb.transactions.create_index([("portfolio_id", 1), ("timestamp", -1)])
            await self.mongodb.transactions.create_index("stock_id")

            # Technical indicators collection indexes
            await self.mongodb.technical_indicators.create_index([("stock_id", 1), ("indicator", 1), ("timestamp", -1)])

            # Alert history collection indexes
            await self.mongodb.alert_history.create_index([("alert_id", 1), ("timestamp", -1)])
            await self.mongodb.alert_history.create_index("timestamp")

            logger.info("Database indexes created successfully")

        except Exception as e:
            logger.error(f"Error creating indexes: {e}")


# Global database instance
db = Database()


async def get_database() -> AsyncIOMotorDatabase:
    """
    Dependency for getting database instance.

    Returns:
        AsyncIOMotorDatabase: MongoDB database instance

    Yields:
        Database instance for dependency injection
    """
    return db.mongodb


async def get_redis() -> aioredis.Redis:
    """
    Dependency for getting Redis client.

    Returns:
        aioredis.Redis: Redis client instance

    Yields:
        Redis client for dependency injection
    """
    return db.redis_client
