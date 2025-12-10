"""
Enumeration types used across the application.

Defines all enum types for consistent type checking and validation.
"""

from enum import Enum


class UserTier(str, Enum):
    """User subscription tiers."""
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class AlertType(str, Enum):
    """Types of price alerts."""
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PERCENT_CHANGE_UP = "percent_change_up"
    PERCENT_CHANGE_DOWN = "percent_change_down"
    VOLUME_ABOVE = "volume_above"
    VOLUME_BELOW = "volume_below"
    RSI_ABOVE = "rsi_above"
    RSI_BELOW = "rsi_below"
    MACD_CROSS_UP = "macd_cross_up"
    MACD_CROSS_DOWN = "macd_cross_down"
    MOVING_AVERAGE_CROSS_UP = "moving_average_cross_up"
    MOVING_AVERAGE_CROSS_DOWN = "moving_average_cross_down"
    SUPPORT_BREAK = "support_break"
    RESISTANCE_BREAK = "resistance_break"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class TransactionType(str, Enum):
    """Portfolio transaction types."""
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    SPLIT = "split"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"


class TechnicalIndicator(str, Enum):
    """Technical indicator types."""
    # Trend indicators
    SMA = "sma"  # Simple Moving Average
    EMA = "ema"  # Exponential Moving Average
    WMA = "wma"  # Weighted Moving Average
    MACD = "macd"  # Moving Average Convergence Divergence
    ADX = "adx"  # Average Directional Index

    # Momentum indicators
    RSI = "rsi"  # Relative Strength Index
    STOCH = "stoch"  # Stochastic Oscillator
    CCI = "cci"  # Commodity Channel Index
    ROC = "roc"  # Rate of Change
    WILLIAMS_R = "williams_r"  # Williams %R

    # Volatility indicators
    BOLLINGER_BANDS = "bollinger_bands"
    ATR = "atr"  # Average True Range
    STANDARD_DEVIATION = "standard_deviation"

    # Volume indicators
    OBV = "obv"  # On-Balance Volume
    VWAP = "vwap"  # Volume Weighted Average Price
    VOLUME_PROFILE = "volume_profile"

    # Support/Resistance
    FIBONACCI = "fibonacci"
    PIVOT_POINTS = "pivot_points"


class TimeInterval(str, Enum):
    """Time intervals for price data."""
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"
    FOUR_HOURS = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1M"


class Exchange(str, Enum):
    """Stock exchanges."""
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    AMEX = "AMEX"
    LSE = "LSE"  # London Stock Exchange
    TSE = "TSE"  # Tokyo Stock Exchange
    HKEX = "HKEX"  # Hong Kong Exchange
    SSE = "SSE"  # Shanghai Stock Exchange
    OTHER = "OTHER"


class DataSource(str, Enum):
    """External data source providers."""
    ALPHA_VANTAGE = "alpha_vantage"
    YAHOO_FINANCE = "yahoo_finance"
    IEX_CLOUD = "iex_cloud"
    FINNHUB = "finnhub"
    POLYGON = "polygon"
    MANUAL = "manual"
