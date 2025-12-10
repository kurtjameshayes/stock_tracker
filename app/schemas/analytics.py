"""
Analytics-related Pydantic schemas.

Schemas for technical analysis, indicators, and trading signals.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from decimal import Decimal
from app.models.enums import TechnicalIndicator, TimeInterval


class TechnicalIndicatorRequest(BaseModel):
    """Schema for requesting technical indicator calculation."""
    symbol: str
    indicator: TechnicalIndicator
    period: TimeInterval = TimeInterval.ONE_DAY
    length: Optional[int] = None  # Period length (e.g., 14 for RSI-14)
    params: Dict[str, Any] = {}  # Additional indicator-specific parameters


class TechnicalIndicatorValue(BaseModel):
    """Schema for technical indicator value."""
    indicator: TechnicalIndicator
    value: Dict[str, Any]  # Can contain single value or multiple (e.g., MACD has signal, histogram)
    period: str
    timestamp: datetime


class TechnicalIndicatorResponse(BaseModel):
    """Schema for technical indicator response."""
    id: str = Field(..., alias="_id")
    stock_id: str
    indicator: TechnicalIndicator
    period: str
    value: Dict[str, Any]
    timestamp: datetime

    class Config:
        populate_by_name = True


class MovingAverageData(BaseModel):
    """Schema for moving average data."""
    sma_20: Optional[Decimal] = None
    sma_50: Optional[Decimal] = None
    sma_200: Optional[Decimal] = None
    ema_12: Optional[Decimal] = None
    ema_26: Optional[Decimal] = None


class MomentumIndicators(BaseModel):
    """Schema for momentum indicators."""
    rsi: Optional[Decimal] = None
    rsi_signal: Optional[str] = None  # "overbought", "oversold", "neutral"
    stochastic_k: Optional[Decimal] = None
    stochastic_d: Optional[Decimal] = None
    cci: Optional[Decimal] = None
    roc: Optional[Decimal] = None


class TrendIndicators(BaseModel):
    """Schema for trend indicators."""
    macd: Optional[Decimal] = None
    macd_signal: Optional[Decimal] = None
    macd_histogram: Optional[Decimal] = None
    adx: Optional[Decimal] = None
    adx_signal: Optional[str] = None  # "strong_uptrend", "strong_downtrend", "weak"


class VolatilityIndicators(BaseModel):
    """Schema for volatility indicators."""
    bollinger_upper: Optional[Decimal] = None
    bollinger_middle: Optional[Decimal] = None
    bollinger_lower: Optional[Decimal] = None
    atr: Optional[Decimal] = None
    standard_deviation: Optional[Decimal] = None


class VolumeIndicators(BaseModel):
    """Schema for volume indicators."""
    obv: Optional[Decimal] = None
    vwap: Optional[Decimal] = None
    volume_sma: Optional[Decimal] = None


class SupportResistance(BaseModel):
    """Schema for support and resistance levels."""
    support_levels: List[Decimal] = []
    resistance_levels: List[Decimal] = []
    pivot_point: Optional[Decimal] = None
    fibonacci_levels: Dict[str, Decimal] = {}


class TradingSignal(BaseModel):
    """Schema for trading signal."""
    signal_type: str  # "buy", "sell", "hold"
    strength: int = Field(..., ge=1, le=10)  # 1-10
    indicators: List[str]  # Which indicators generated the signal
    price: Decimal
    timestamp: datetime
    reasoning: str


class ChartPattern(BaseModel):
    """Schema for detected chart pattern."""
    pattern_type: str  # "head_shoulders", "double_top", "triangle", etc.
    confidence: Decimal = Field(..., ge=0, le=1)  # 0-1
    detected_at: datetime
    price_target: Optional[Decimal] = None
    description: str


class ComprehensiveAnalysis(BaseModel):
    """Schema for comprehensive stock analysis."""
    symbol: str
    current_price: Decimal
    timestamp: datetime

    # Technical indicators
    moving_averages: MovingAverageData
    momentum: MomentumIndicators
    trend: TrendIndicators
    volatility: VolatilityIndicators
    volume: VolumeIndicators
    support_resistance: SupportResistance

    # Signals and patterns
    signals: List[TradingSignal] = []
    patterns: List[ChartPattern] = []

    # Overall assessment
    technical_rating: str  # "strong_buy", "buy", "neutral", "sell", "strong_sell"
    risk_level: str  # "low", "medium", "high"
    summary: str


class SectorPerformance(BaseModel):
    """Schema for sector performance data."""
    sector: str
    percent_change_1d: Decimal
    percent_change_1w: Decimal
    percent_change_1m: Decimal
    top_gainers: List[str] = []  # Stock symbols
    top_losers: List[str] = []


class MarketMover(BaseModel):
    """Schema for market movers (gainers/losers)."""
    symbol: str
    name: str
    price: Decimal
    change: Decimal
    percent_change: Decimal
    volume: int


class MarketMovers(BaseModel):
    """Schema for market movers response."""
    top_gainers: List[MarketMover]
    top_losers: List[MarketMover]
    most_active: List[MarketMover]
    timestamp: datetime


class BacktestRequest(BaseModel):
    """Schema for backtesting request."""
    symbol: str
    strategy: str  # Strategy name or definition
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal = Field(default=Decimal("10000"))
    params: Dict[str, Any] = {}


class BacktestResult(BaseModel):
    """Schema for backtest results."""
    symbol: str
    strategy: str
    period: str
    total_return: Decimal
    sharpe_ratio: Decimal
    max_drawdown: Decimal
    win_rate: Decimal
    total_trades: int
    profitable_trades: int
    losing_trades: int
    average_win: Decimal
    average_loss: Decimal
    profit_factor: Decimal
    final_value: Decimal
