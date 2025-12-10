"""
Stock repository for database operations.

Handles all database operations related to stocks and prices.
"""

from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base import BaseRepository
from datetime import datetime
from bson import ObjectId


class StockRepository(BaseRepository):
    """Repository for stock data operations."""

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize stock repository.

        Args:
            database: MongoDB database instance
        """
        super().__init__(database, "stocks")

    async def get_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get stock by symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL")

        Returns:
            Stock document or None
        """
        return await self.get_by_field("symbol", symbol.upper())

    async def search_stocks(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search stocks by symbol or name.

        Args:
            query: Search query
            limit: Maximum results to return

        Returns:
            List of matching stocks
        """
        # Text search on symbol and name
        filter_dict = {
            "$or": [
                {"symbol": {"$regex": query.upper(), "$options": "i"}},
                {"name": {"$regex": query, "$options": "i"}}
            ]
        }

        return await self.find_many(filter_dict, limit=limit)

    async def get_by_exchange(self, exchange: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get stocks by exchange.

        Args:
            exchange: Exchange name (e.g., "NYSE", "NASDAQ")
            skip: Number of records to skip
            limit: Maximum results to return

        Returns:
            List of stocks on the exchange
        """
        return await self.find_many({"exchange": exchange}, skip=skip, limit=limit)

    async def get_by_sector(self, sector: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get stocks by sector.

        Args:
            sector: Sector name
            skip: Number of records to skip
            limit: Maximum results to return

        Returns:
            List of stocks in the sector
        """
        return await self.find_many({"sector": sector}, skip=skip, limit=limit)


class StockPriceRepository(BaseRepository):
    """Repository for stock price data operations."""

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize stock price repository.

        Args:
            database: MongoDB database instance
        """
        super().__init__(database, "stock_prices")

    async def create_price(self, price_data: Dict[str, Any]) -> str:
        """
        Create a new price entry.

        Args:
            price_data: Price data including stock_id, prices, timestamp, etc.

        Returns:
            Created price entry ID
        """
        # Convert stock_id string to ObjectId if needed
        if isinstance(price_data.get("stock_id"), str):
            try:
                price_data["stock_id"] = ObjectId(price_data["stock_id"])
            except Exception:
                pass

        return await self.create(price_data)

    async def get_latest_price(self, stock_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent price for a stock.

        Args:
            stock_id: Stock ID

        Returns:
            Latest price document or None
        """
        try:
            prices = await self.find_many(
                {"stock_id": ObjectId(stock_id)},
                limit=1,
                sort=[("timestamp", -1)]
            )
            return prices[0] if prices else None
        except Exception:
            return None

    async def get_price_history(
        self,
        stock_id: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get price history for a stock within date range.

        Args:
            stock_id: Stock ID
            start_date: Start date
            end_date: End date
            limit: Maximum results to return

        Returns:
            List of price documents
        """
        try:
            filter_dict = {
                "stock_id": ObjectId(stock_id),
                "timestamp": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }

            return await self.find_many(
                filter_dict,
                limit=limit,
                sort=[("timestamp", 1)]
            )
        except Exception:
            return []

    async def bulk_insert_prices(self, prices: List[Dict[str, Any]]) -> int:
        """
        Bulk insert price data.

        Args:
            prices: List of price documents

        Returns:
            Number of inserted documents
        """
        if not prices:
            return 0

        # Add timestamps
        now = datetime.utcnow()
        for price in prices:
            price["created_at"] = now
            price["updated_at"] = now

        result = await self.collection.insert_many(prices)
        return len(result.inserted_ids)
