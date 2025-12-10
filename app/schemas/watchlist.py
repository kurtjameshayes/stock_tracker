"""
Watchlist-related Pydantic schemas.

Schemas for managing stock watchlists.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class WatchlistBase(BaseModel):
    """Base watchlist schema."""
    name: str = Field(..., min_length=1, max_length=100)
    is_default: bool = False


class WatchlistCreate(WatchlistBase):
    """Schema for creating a new watchlist."""
    pass


class WatchlistUpdate(BaseModel):
    """Schema for updating watchlist."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_default: Optional[bool] = None


class WatchlistItemBase(BaseModel):
    """Base schema for watchlist item."""
    stock_id: str
    notes: Optional[str] = None


class WatchlistItemCreate(WatchlistItemBase):
    """Schema for adding stock to watchlist."""
    position: Optional[int] = None


class WatchlistItemUpdate(BaseModel):
    """Schema for updating watchlist item."""
    position: Optional[int] = None
    notes: Optional[str] = None


class WatchlistItemResponse(WatchlistItemBase):
    """Schema for watchlist item response."""
    id: str = Field(..., alias="_id")
    watchlist_id: str
    position: int
    added_at: datetime

    class Config:
        populate_by_name = True


class WatchlistResponse(WatchlistBase):
    """Schema for watchlist response."""
    id: str = Field(..., alias="_id")
    user_id: str
    created_at: datetime
    items: List[WatchlistItemResponse] = []

    class Config:
        populate_by_name = True
