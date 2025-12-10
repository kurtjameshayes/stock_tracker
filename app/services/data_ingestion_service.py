"""
Data ingestion service for fetching stock data from external APIs.

Handles integration with multiple data providers and manages rate limiting.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import yfinance as yf
from decimal import Decimal
from app.repositories.stock_repository import StockRepository, StockPriceRepository
from app.models.enums import DataSource
from config.settings import settings
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class DataIngestionService:
    """Service for ingesting stock data from external APIs."""

    def __init__(
        self,
        stock_repository: StockRepository,
        price_repository: StockPriceRepository
    ):
        """
        Initialize data ingestion service.

        Args:
            stock_repository: Stock repository instance
            price_repository: Stock price repository instance
        """
        self.stock_repo = stock_repository
        self.price_repo = price_repository
        self.executor = ThreadPoolExecutor(max_workers=5)

    async def fetch_stock_data_yahoo(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch stock data from Yahoo Finance.

        Args:
            symbol: Stock symbol

        Returns:
            Stock data dict or None if not found
        """
        try:
            # Run in thread pool since yfinance is synchronous
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(self.executor, yf.Ticker, symbol)
            info = await loop.run_in_executor(self.executor, lambda: ticker.info)

            stock_data = {
                "symbol": symbol.upper(),
                "name": info.get("longName", symbol),
                "exchange": info.get("exchange", "UNKNOWN"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "currency": info.get("currency", "USD"),
                "metadata": {
                    "market_cap": info.get("marketCap"),
                    "employees": info.get("fullTimeEmployees"),
                    "website": info.get("website"),
                    "description": info.get("longBusinessSummary"),
                }
            }

            logger.info(f"Fetched stock data for {symbol} from Yahoo Finance")
            return stock_data

        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol} from Yahoo: {e}")
            return None

    async def fetch_historical_prices_yahoo(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d"
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical price data from Yahoo Finance.

        Args:
            symbol: Stock symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            List of price data dicts
        """
        try:
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(self.executor, yf.Ticker, symbol)
            hist = await loop.run_in_executor(
                self.executor,
                lambda: ticker.history(period=period, interval=interval)
            )

            prices = []
            for timestamp, row in hist.iterrows():
                price_data = {
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                    "adjusted_close": float(row.get("Close", row["Close"])),
                    "timestamp": timestamp.to_pydatetime(),
                    "source": DataSource.YAHOO_FINANCE
                }
                prices.append(price_data)

            logger.info(f"Fetched {len(prices)} historical prices for {symbol}")
            return prices

        except Exception as e:
            logger.error(f"Error fetching historical prices for {symbol}: {e}")
            return []

    async def fetch_realtime_quote_yahoo(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch real-time quote from Yahoo Finance.

        Args:
            symbol: Stock symbol

        Returns:
            Quote data or None
        """
        try:
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(self.executor, yf.Ticker, symbol)
            info = await loop.run_in_executor(self.executor, lambda: ticker.info)

            quote = {
                "symbol": symbol,
                "current_price": float(info.get("currentPrice", 0) or info.get("regularMarketPrice", 0)),
                "open": float(info.get("open", 0) or info.get("regularMarketOpen", 0)),
                "high": float(info.get("dayHigh", 0) or info.get("regularMarketDayHigh", 0)),
                "low": float(info.get("dayLow", 0) or info.get("regularMarketDayLow", 0)),
                "volume": int(info.get("volume", 0) or info.get("regularMarketVolume", 0)),
                "previous_close": float(info.get("previousClose", 0) or info.get("regularMarketPreviousClose", 0)),
            }

            return quote

        except Exception as e:
            logger.error(f"Error fetching real-time quote for {symbol}: {e}")
            return None

    async def ingest_stock(self, symbol: str) -> Optional[str]:
        """
        Ingest stock data and store in database.

        Args:
            symbol: Stock symbol

        Returns:
            Stock ID if successful, None otherwise
        """
        # Check if stock already exists
        existing = await self.stock_repo.get_by_symbol(symbol)
        if existing:
            logger.info(f"Stock {symbol} already exists")
            return existing["_id"]

        # Fetch stock data
        stock_data = await self.fetch_stock_data_yahoo(symbol)
        if not stock_data:
            return None

        # Create stock entry
        stock_id = await self.stock_repo.create(stock_data)
        logger.info(f"Ingested stock {symbol} with ID {stock_id}")

        return stock_id

    async def ingest_historical_prices(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d"
    ) -> int:
        """
        Ingest historical prices for a stock.

        Args:
            symbol: Stock symbol
            period: Time period
            interval: Data interval

        Returns:
            Number of price entries created
        """
        # Ensure stock exists
        stock = await self.stock_repo.get_by_symbol(symbol)
        if not stock:
            stock_id = await self.ingest_stock(symbol)
            if not stock_id:
                logger.error(f"Failed to ingest stock {symbol}")
                return 0
            stock = await self.stock_repo.get_by_id(stock_id)

        # Fetch prices
        prices = await self.fetch_historical_prices_yahoo(symbol, period, interval)

        if not prices:
            return 0

        # Add stock_id to each price
        for price in prices:
            price["stock_id"] = stock["_id"]

        # Bulk insert
        count = await self.price_repo.bulk_insert_prices(prices)
        logger.info(f"Ingested {count} historical prices for {symbol}")

        return count

    async def update_current_price(self, symbol: str) -> Optional[str]:
        """
        Update current price for a stock.

        Args:
            symbol: Stock symbol

        Returns:
            Price entry ID if successful
        """
        stock = await self.stock_repo.get_by_symbol(symbol)
        if not stock:
            logger.warning(f"Stock {symbol} not found for price update")
            return None

        quote = await self.fetch_realtime_quote_yahoo(symbol)
        if not quote:
            return None

        price_data = {
            "stock_id": stock["_id"],
            "open": quote["open"],
            "high": quote["high"],
            "low": quote["low"],
            "close": quote["current_price"],
            "volume": quote["volume"],
            "adjusted_close": quote["current_price"],
            "timestamp": datetime.utcnow(),
            "source": DataSource.YAHOO_FINANCE
        }

        price_id = await self.price_repo.create_price(price_data)
        logger.info(f"Updated current price for {symbol}")

        return price_id

    async def bulk_update_prices(self, symbols: List[str]) -> Dict[str, int]:
        """
        Update prices for multiple stocks.

        Args:
            symbols: List of stock symbols

        Returns:
            Dict with success and failure counts
        """
        results = {"success": 0, "failed": 0}

        for symbol in symbols:
            try:
                price_id = await self.update_current_price(symbol)
                if price_id:
                    results["success"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.error(f"Error updating price for {symbol}: {e}")
                results["failed"] += 1

            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)

        logger.info(f"Bulk price update: {results['success']} success, {results['failed']} failed")
        return results
