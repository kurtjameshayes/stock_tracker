"""
Analytics API endpoints.

Handles technical analysis, indicators, and trading signals.
"""

from fastapi import APIRouter, Depends, Path, HTTPException, status
from app.schemas.analytics import (
    MovingAverageData, MomentumIndicators, TrendIndicators,
    VolatilityIndicators, VolumeIndicators
)
from app.services.analytics_service import AnalyticsService
from app.services.stock_service import StockService
from app.api.dependencies import get_analytics_service, get_stock_service
from app.core.security import get_current_user_id

router = APIRouter()


@router.get("/{symbol}/moving-averages", response_model=MovingAverageData)
async def get_moving_averages(
    symbol: str = Path(...),
    current_user_id: str = Depends(get_current_user_id),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    stock_service: StockService = Depends(get_stock_service)
):
    """
    Get moving averages for a stock.

    Returns SMA and EMA values for various periods.
    """
    stock = await stock_service.get_stock_by_symbol(symbol)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock {symbol} not found"
        )

    ma_data = await analytics_service.get_moving_averages(stock["_id"])
    return ma_data


@router.get("/{symbol}/momentum", response_model=MomentumIndicators)
async def get_momentum_indicators(
    symbol: str,
    current_user_id: str = Depends(get_current_user_id),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    stock_service: StockService = Depends(get_stock_service)
):
    """
    Get momentum indicators for a stock.

    Returns RSI and other momentum indicators.
    """
    stock = await stock_service.get_stock_by_symbol(symbol)
    momentum = await analytics_service.get_momentum_indicators(stock["_id"])
    return momentum


@router.get("/{symbol}/trend", response_model=TrendIndicators)
async def get_trend_indicators(
    symbol: str,
    current_user_id: str = Depends(get_current_user_id),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    stock_service: StockService = Depends(get_stock_service)
):
    """
    Get trend indicators for a stock.

    Returns MACD and other trend indicators.
    """
    stock = await stock_service.get_stock_by_symbol(symbol)
    trend = await analytics_service.get_trend_indicators(stock["_id"])
    return trend


@router.get("/{symbol}/volatility", response_model=VolatilityIndicators)
async def get_volatility_indicators(
    symbol: str,
    current_user_id: str = Depends(get_current_user_id),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    stock_service: StockService = Depends(get_stock_service)
):
    """
    Get volatility indicators for a stock.

    Returns Bollinger Bands, ATR, and other volatility indicators.
    """
    stock = await stock_service.get_stock_by_symbol(symbol)
    volatility = await analytics_service.get_volatility_indicators(stock["_id"])
    return volatility


@router.get("/{symbol}/volume", response_model=VolumeIndicators)
async def get_volume_indicators(
    symbol: str,
    current_user_id: str = Depends(get_current_user_id),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    stock_service: StockService = Depends(get_stock_service)
):
    """
    Get volume indicators for a stock.

    Returns OBV, VWAP, and other volume indicators.
    """
    stock = await stock_service.get_stock_by_symbol(symbol)
    volume = await analytics_service.get_volume_indicators(stock["_id"])
    return volume
