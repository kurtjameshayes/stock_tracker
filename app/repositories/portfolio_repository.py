"""
Portfolio repository for database operations.

Handles all database operations related to portfolios, positions, and transactions.
"""

from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base import BaseRepository
from bson import ObjectId
from datetime import datetime
from decimal import Decimal


class PortfolioRepository(BaseRepository):
    """Repository for portfolio data operations."""

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize portfolio repository.

        Args:
            database: MongoDB database instance
        """
        super().__init__(database, "portfolios")

    async def get_user_portfolios(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all portfolios for a user.

        Args:
            user_id: User ID

        Returns:
            List of portfolio documents
        """
        return await self.find_many(
            {"user_id": user_id},
            sort=[("created_at", -1)]
        )


class PositionRepository(BaseRepository):
    """Repository for portfolio position operations."""

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize position repository.

        Args:
            database: MongoDB database instance
        """
        super().__init__(database, "positions")

    async def get_portfolio_positions(self, portfolio_id: str) -> List[Dict[str, Any]]:
        """
        Get all positions in a portfolio.

        Args:
            portfolio_id: Portfolio ID

        Returns:
            List of position documents
        """
        return await self.find_many({"portfolio_id": portfolio_id})

    async def get_position(self, portfolio_id: str, stock_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific position.

        Args:
            portfolio_id: Portfolio ID
            stock_id: Stock ID

        Returns:
            Position document or None
        """
        position = await self.collection.find_one({
            "portfolio_id": portfolio_id,
            "stock_id": stock_id
        })

        if position:
            position["_id"] = str(position["_id"])

        return position

    async def upsert_position(self, position_data: Dict[str, Any]) -> str:
        """
        Create or update a position.

        Args:
            position_data: Position data

        Returns:
            Position ID
        """
        existing = await self.get_position(
            position_data["portfolio_id"],
            position_data["stock_id"]
        )

        if existing:
            await self.update(existing["_id"], position_data)
            return existing["_id"]
        else:
            return await self.create(position_data)


class TransactionRepository(BaseRepository):
    """Repository for transaction operations."""

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize transaction repository.

        Args:
            database: MongoDB database instance
        """
        super().__init__(database, "transactions")

    async def create_transaction(self, transaction_data: Dict[str, Any]) -> str:
        """
        Create a new transaction.

        Args:
            transaction_data: Transaction data

        Returns:
            Created transaction ID
        """
        if "timestamp" not in transaction_data:
            transaction_data["timestamp"] = datetime.utcnow()

        return await self.create(transaction_data)

    async def get_portfolio_transactions(
        self,
        portfolio_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get transactions for a portfolio.

        Args:
            portfolio_id: Portfolio ID
            skip: Number to skip
            limit: Maximum to return

        Returns:
            List of transaction documents
        """
        return await self.find_many(
            {"portfolio_id": portfolio_id},
            skip=skip,
            limit=limit,
            sort=[("timestamp", -1)]
        )

    async def get_stock_transactions(
        self,
        portfolio_id: str,
        stock_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all transactions for a specific stock in a portfolio.

        Args:
            portfolio_id: Portfolio ID
            stock_id: Stock ID

        Returns:
            List of transaction documents
        """
        return await self.find_many(
            {"portfolio_id": portfolio_id, "stock_id": stock_id},
            sort=[("timestamp", 1)]
        )
