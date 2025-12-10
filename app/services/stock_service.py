"""
Stock service for business logic.

Handles stock data operations, price tracking, and market data.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
from app.repositories.stock_repository import StockRepository, StockPriceRepository
from app.schemas.stock import (
    StockCreate, StockUpdate, StockResponse,
    StockPriceCreate, StockQuote, HistoricalDataRequest
)
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class StockService:
    """Service for stock-related business logic."""

    def __init__(
        self,
        stock_repository: StockRepository,
        price_repository: StockPriceRepository,
        redis_client
    ):
        """
        Initialize stock service.

        Args:
            stock_repository: Stock repository instance
            price_repository: Stock price repository instance
            redis_client: Redis client for caching
        """
        self.stock_repo = stock_repository
        self.price_repo = price_repository
        self.redis = redis_client

    async def create_stock(self, stock_data: StockCreate) -> Dict[str, Any]:
        """
        Create a new stock entry.

        Args:
            stock_data: Stock creation data

        Returns:
            Created stock document

        Raises:
            HTTPException: If stock symbol already exists
        """
        # Check if symbol already exists
        existing = await self.stock_repo.get_by_symbol(stock_data.symbol)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock with symbol {stock_data.symbol} already exists"
            )

        stock_doc = stock_data.model_dump()
        stock_doc["symbol"] = stock_doc["symbol"].upper()

        stock_id = await self.stock_repo.create(stock_doc)
        stock = await self.stock_repo.get_by_id(stock_id)

        logger.info(f"Created stock: {stock_data.symbol}")

        return stock

    async def get_stock_by_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        Get stock by symbol with caching.

        Args:
            symbol: Stock symbol

        Returns:
            Stock document

        Raises:
            HTTPException: If stock not found
        """
        # Try cache first
        cache_key = f"stock:{symbol.upper()}"
        cached = await self.redis.get(cache_key)

        if cached:
            import json
            return json.loads(cached)

        stock = await self.stock_repo.get_by_symbol(symbol)

        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock {symbol} not found"
            )

        # Cache for 1 hour
        import json
        await self.redis.setex(cache_key, 3600, json.dumps(stock, default=str))

        return stock

    async def search_stocks(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search stocks by symbol or name.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching stocks
        """
        if not query or len(query) < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query must be at least 1 character"
            )

        return await self.stock_repo.search_stocks(query, limit)

    async def get_current_quote(self, symbol: str) -> StockQuote:
        """
        Get current quote for a stock.

        Args:
            symbol: Stock symbol

        Returns:
            Current stock quote

        Raises:
            HTTPException: If stock or price data not found
        """
        stock = await self.get_stock_by_symbol(symbol)

        # Get latest price
        latest_price = await self.price_repo.get_latest_price(stock["_id"])

        if not latest_price:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No price data available for {symbol}"
            )

        # Get previous day's close for change calculation
        # For simplicity, using the same latest price (should fetch previous day in production)
        previous_close = latest_price.get("close", latest_price["close"])
        current_price = latest_price["close"]

        change = current_price - previous_close
        percent_change = (change / previous_close * 100) if previous_close != 0 else Decimal("0")

        quote = StockQuote(
            symbol=stock["symbol"],
            current_price=current_price,
            change=change,
            percent_change=percent_change,
            volume=latest_price["volume"],
            open=latest_price["open"],
            high=latest_price["high"],
            low=latest_price["low"],
            previous_close=previous_close,
            timestamp=latest_price["timestamp"]
        )

        return quote

    async def get_price_history(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get historical price data.

        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date

        Returns:
            List of price documents
        """
        stock = await self.get_stock_by_symbol(symbol)
        return await self.price_repo.get_price_history(
            stock["_id"],
            start_date,
            end_date
        )

    async def add_price_data(self, price_data: StockPriceCreate) -> str:
        """
        Add price data for a stock.

        Args:
            price_data: Price data

        Returns:
            Created price entry ID
        """
        price_doc = price_data.model_dump()

        # Convert Decimal to float for MongoDB
        for key in ["open", "high", "low", "close", "adjusted_close"]:
            if key in price_doc and price_doc[key] is not None:
                price_doc[key] = float(price_doc[key])

        price_id = await self.price_repo.create_price(price_doc)

        logger.info(f"Added price data for stock_id: {price_data.stock_id}")

        return price_id
