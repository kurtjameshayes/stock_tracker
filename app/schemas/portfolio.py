"""
Portfolio-related Pydantic schemas.

Schemas for portfolio and transaction management.
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field
from decimal import Decimal
from app.models.enums import TransactionType


class PortfolioBase(BaseModel):
    """Base portfolio schema."""
    name: str = Field(..., min_length=1, max_length=100)
    currency: str = "USD"


class PortfolioCreate(PortfolioBase):
    """Schema for creating a new portfolio."""
    pass


class PortfolioUpdate(BaseModel):
    """Schema for updating portfolio."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    currency: Optional[str] = None


class PortfolioResponse(PortfolioBase):
    """Schema for portfolio response."""
    id: str = Field(..., alias="_id")
    user_id: str
    created_at: datetime

    class Config:
        populate_by_name = True


class PositionBase(BaseModel):
    """Base schema for portfolio position."""
    stock_id: str
    quantity: Decimal = Field(..., gt=0)
    average_cost: Decimal = Field(..., gt=0)


class PositionResponse(PositionBase):
    """Schema for position response with calculated fields."""
    id: str = Field(..., alias="_id")
    portfolio_id: str
    first_purchase_date: date
    last_update_date: datetime
    current_value: Optional[Decimal] = None
    total_gain_loss: Optional[Decimal] = None
    percent_gain_loss: Optional[Decimal] = None

    class Config:
        populate_by_name = True


class TransactionBase(BaseModel):
    """Base schema for transaction."""
    stock_id: str
    type: TransactionType
    quantity: Decimal = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)
    fees: Decimal = Field(default=Decimal("0"), ge=0)
    notes: Optional[str] = None


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction."""
    timestamp: Optional[datetime] = None  # Defaults to now if not provided


class TransactionResponse(TransactionBase):
    """Schema for transaction response."""
    id: str = Field(..., alias="_id")
    portfolio_id: str
    timestamp: datetime

    class Config:
        populate_by_name = True


class PortfolioPerformance(BaseModel):
    """Schema for portfolio performance metrics."""
    portfolio_id: str
    total_value: Decimal
    total_cost: Decimal
    total_gain_loss: Decimal
    percent_gain_loss: Decimal
    cash_balance: Decimal
    positions_count: int
    day_change: Decimal
    day_percent_change: Decimal


class PortfolioAnalytics(BaseModel):
    """Schema for portfolio analytics and risk metrics."""
    portfolio_id: str
    diversification_score: Decimal  # 0-100
    sector_allocation: dict  # Sector -> percentage
    risk_score: Decimal  # 0-100
    sharpe_ratio: Optional[Decimal] = None
    beta: Optional[Decimal] = None
    volatility: Optional[Decimal] = None  # Standard deviation
    max_drawdown: Optional[Decimal] = None
    total_dividends: Decimal
