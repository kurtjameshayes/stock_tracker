"""
Watchlist API endpoints.

Handles watchlist and item management.
"""

from fastapi import APIRouter, Depends, Path
from typing import List
from app.schemas.watchlist import (
    WatchlistCreate, WatchlistResponse, WatchlistUpdate,
    WatchlistItemCreate, WatchlistItemResponse
)
from app.services.watchlist_service import WatchlistService
from app.api.dependencies import get_watchlist_service
from app.core.security import get_current_user_id

router = APIRouter()


@router.get("", response_model=List[WatchlistResponse])
async def get_watchlists(
    current_user_id: str = Depends(get_current_user_id),
    watchlist_service: WatchlistService = Depends(get_watchlist_service)
):
    """
    Get all watchlists for the current user.

    Returns all watchlists owned by the authenticated user.
    """
    watchlists = await watchlist_service.get_user_watchlists(current_user_id)
    return watchlists


@router.post("", response_model=WatchlistResponse)
async def create_watchlist(
    watchlist_data: WatchlistCreate,
    current_user_id: str = Depends(get_current_user_id),
    watchlist_service: WatchlistService = Depends(get_watchlist_service)
):
    """
    Create a new watchlist.

    Creates a new watchlist for organizing stocks.
    """
    watchlist = await watchlist_service.create_watchlist(current_user_id, watchlist_data)
    return watchlist


@router.get("/{watchlist_id}", response_model=WatchlistResponse)
async def get_watchlist(
    watchlist_id: str = Path(...),
    current_user_id: str = Depends(get_current_user_id),
    watchlist_service: WatchlistService = Depends(get_watchlist_service)
):
    """
    Get watchlist by ID with items.

    Returns watchlist details including all stocks in the list.
    """
    watchlist = await watchlist_service.get_watchlist(watchlist_id, current_user_id)
    return watchlist


@router.put("/{watchlist_id}", response_model=WatchlistResponse)
async def update_watchlist(
    watchlist_id: str,
    update_data: WatchlistUpdate,
    current_user_id: str = Depends(get_current_user_id),
    watchlist_service: WatchlistService = Depends(get_watchlist_service)
):
    """
    Update watchlist.

    Updates watchlist name or default status.
    """
    watchlist = await watchlist_service.update_watchlist(
        watchlist_id, current_user_id, update_data
    )
    return watchlist


@router.delete("/{watchlist_id}")
async def delete_watchlist(
    watchlist_id: str,
    current_user_id: str = Depends(get_current_user_id),
    watchlist_service: WatchlistService = Depends(get_watchlist_service)
):
    """
    Delete watchlist.

    Permanently removes the watchlist and all its items.
    """
    success = await watchlist_service.delete_watchlist(watchlist_id, current_user_id)
    return {"message": "Watchlist deleted successfully" if success else "Failed to delete watchlist"}


@router.post("/{watchlist_id}/stocks", response_model=WatchlistItemResponse)
async def add_stock_to_watchlist(
    watchlist_id: str,
    item_data: WatchlistItemCreate,
    current_user_id: str = Depends(get_current_user_id),
    watchlist_service: WatchlistService = Depends(get_watchlist_service)
):
    """
    Add stock to watchlist.

    Adds a stock to the specified watchlist.
    """
    item = await watchlist_service.add_stock_to_watchlist(
        watchlist_id, current_user_id, item_data
    )
    return item


@router.delete("/{watchlist_id}/stocks/{stock_id}")
async def remove_stock_from_watchlist(
    watchlist_id: str,
    stock_id: str,
    current_user_id: str = Depends(get_current_user_id),
    watchlist_service: WatchlistService = Depends(get_watchlist_service)
):
    """
    Remove stock from watchlist.

    Removes a stock from the specified watchlist.
    """
    success = await watchlist_service.remove_stock_from_watchlist(
        watchlist_id, stock_id, current_user_id
    )
    return {"message": "Stock removed successfully" if success else "Failed to remove stock"}
