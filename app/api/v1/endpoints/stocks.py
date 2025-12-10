"""
Stock API endpoints.

Handles stock data, price quotes, and historical data.
"""

from fastapi import APIRouter, Depends, Query
from typing import List
from datetime import datetime
from app.schemas.stock import (
    StockCreate, StockResponse, StockQuote, StockSearch
)
from app.services.stock_service import StockService
from app.services.data_ingestion_service import DataIngestionService
from app.api.dependencies import get_stock_service, get_data_ingestion_service
from app.core.security import get_current_user_id

router = APIRouter()


@router.get("/search", response_model=List[StockSearch])
async def search_stocks(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    stock_service: StockService = Depends(get_stock_service)
):
    """
    Search stocks by symbol or name.

    Returns matching stocks based on the search query.
    """
    stocks = await stock_service.search_stocks(q, limit)
    return stocks


@router.get("/{symbol}", response_model=StockResponse)
async def get_stock(
    symbol: str,
    stock_service: StockService = Depends(get_stock_service)
):
    """
    Get stock details by symbol.

    Returns detailed information about a specific stock.
    """
    stock = await stock_service.get_stock_by_symbol(symbol)
    return stock


@router.get("/{symbol}/quote", response_model=StockQuote)
async def get_quote(
    symbol: str,
    stock_service: StockService = Depends(get_stock_service)
):
    """
    Get current quote for a stock.

    Returns real-time price information for the specified stock.
    """
    quote = await stock_service.get_current_quote(symbol)
    return quote


@router.get("/{symbol}/history")
async def get_price_history(
    symbol: str,
    start_date: datetime = Query(..., description="Start date"),
    end_date: datetime = Query(..., description="End date"),
    stock_service: StockService = Depends(get_stock_service)
):
    """
    Get historical price data.

    Returns historical OHLCV data for the specified date range.
    """
    history = await stock_service.get_price_history(symbol, start_date, end_date)
    return {"symbol": symbol, "data": history}


@router.post("/{symbol}/ingest")
async def ingest_stock_data(
    symbol: str,
    period: str = Query("1mo", description="Period (1d, 5d, 1mo, 3mo, 6mo, 1y, etc.)"),
    current_user_id: str = Depends(get_current_user_id),
    ingestion_service: DataIngestionService = Depends(get_data_ingestion_service)
):
    """
    Ingest stock data from external APIs.

    Fetches and stores stock information and historical prices.
    Requires authentication.
    """
    stock_id = await ingestion_service.ingest_stock(symbol)
    if not stock_id:
        return {"message": "Failed to ingest stock data"}

    count = await ingestion_service.ingest_historical_prices(symbol, period)

    return {
        "message": "Stock data ingested successfully",
        "stock_id": stock_id,
        "prices_ingested": count
    }
