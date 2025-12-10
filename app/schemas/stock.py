"""
Stock-related Pydantic schemas.

Schemas for stocks, prices, and market data.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from decimal import Decimal
from app.models.enums import Exchange, DataSource, TimeInterval


class StockBase(BaseModel):
    """Base stock schema."""
    symbol: str = Field(..., min_length=1, max_length=10)
    name: str = Field(..., min_length=1, max_length=200)
    exchange: Exchange
    sector: Optional[str] = None
    industry: Optional[str] = None
    currency: str = "USD"
    metadata: Dict[str, Any] = {}


class StockCreate(StockBase):
    """Schema for creating a new stock."""
    pass


class StockUpdate(BaseModel):
    """Schema for updating stock information."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    sector: Optional[str] = None
    industry: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class StockResponse(StockBase):
    """Schema for stock response."""
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class StockPriceBase(BaseModel):
    """Base schema for stock price data."""
    open: Decimal = Field(..., gt=0)
    high: Decimal = Field(..., gt=0)
    low: Decimal = Field(..., gt=0)
    close: Decimal = Field(..., gt=0)
    volume: int = Field(..., ge=0)
    adjusted_close: Optional[Decimal] = None


class StockPriceCreate(StockPriceBase):
    """Schema for creating stock price entry."""
    stock_id: str
    timestamp: datetime
    source: DataSource = DataSource.MANUAL


class StockPriceResponse(StockPriceBase):
    """Schema for stock price response."""
    id: str = Field(..., alias="_id")
    stock_id: str
    timestamp: datetime
    source: DataSource

    class Config:
        populate_by_name = True


class StockQuote(BaseModel):
    """Schema for real-time stock quote."""
    symbol: str
    current_price: Decimal
    change: Decimal
    percent_change: Decimal
    volume: int
    open: Decimal
    high: Decimal
    low: Decimal
    previous_close: Decimal
    timestamp: datetime


class StockSearch(BaseModel):
    """Schema for stock search results."""
    symbol: str
    name: str
    exchange: Exchange
    currency: str


class HistoricalDataRequest(BaseModel):
    """Schema for requesting historical data."""
    symbol: str
    start_date: datetime
    end_date: datetime
    interval: TimeInterval = TimeInterval.ONE_DAY


class PriceHistory(BaseModel):
    """Schema for historical price data response."""
    symbol: str
    interval: TimeInterval
    data: list[StockPriceResponse]
