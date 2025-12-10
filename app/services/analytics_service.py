"""
Analytics service for technical analysis and indicators.

Provides comprehensive stock analysis including technical indicators,
chart patterns, and trading signals.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
import numpy as np
from app.repositories.stock_repository import StockPriceRepository
from app.schemas.analytics import (
    TechnicalIndicatorRequest, MovingAverageData,
    MomentumIndicators, TrendIndicators, VolatilityIndicators,
    VolumeIndicators, SupportResistance, ComprehensiveAnalysis,
    TradingSignal, ChartPattern
)
from app.models.enums import TechnicalIndicator
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for stock analytics and technical analysis."""

    def __init__(self, price_repository: StockPriceRepository):
        """
        Initialize analytics service.

        Args:
            price_repository: Stock price repository instance
        """
        self.price_repo = price_repository

    def _prices_to_dataframe(self, prices: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert price list to pandas DataFrame.

        Args:
            prices: List of price documents

        Returns:
            DataFrame with OHLCV data
        """
        if not prices:
            return pd.DataFrame()

        df = pd.DataFrame(prices)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)

        # Convert to float
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = df[col].astype(float)

        return df

    def calculate_sma(self, df: pd.DataFrame, period: int) -> pd.Series:
        """
        Calculate Simple Moving Average.

        Args:
            df: Price DataFrame
            period: Period length

        Returns:
            SMA series
        """
        return df['close'].rolling(window=period).mean()

    def calculate_ema(self, df: pd.DataFrame, period: int) -> pd.Series:
        """
        Calculate Exponential Moving Average.

        Args:
            df: Price DataFrame
            period: Period length

        Returns:
            EMA series
        """
        return df['close'].ewm(span=period, adjust=False).mean()

    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index.

        Args:
            df: Price DataFrame
            period: RSI period (default 14)

        Returns:
            RSI series
        """
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def calculate_macd(
        self,
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Dict[str, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            df: Price DataFrame
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period

        Returns:
            Dict with MACD, signal, and histogram
        """
        ema_fast = self.calculate_ema(df, fast)
        ema_slow = self.calculate_ema(df, slow)

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram
        }

    def calculate_bollinger_bands(
        self,
        df: pd.DataFrame,
        period: int = 20,
        std_dev: int = 2
    ) -> Dict[str, pd.Series]:
        """
        Calculate Bollinger Bands.

        Args:
            df: Price DataFrame
            period: Moving average period
            std_dev: Number of standard deviations

        Returns:
            Dict with upper, middle, and lower bands
        """
        middle = self.calculate_sma(df, period)
        std = df['close'].rolling(window=period).std()

        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        return {
            "upper": upper,
            "middle": middle,
            "lower": lower
        }

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range.

        Args:
            df: Price DataFrame
            period: ATR period

        Returns:
            ATR series
        """
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

        return atr

    def calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate On-Balance Volume.

        Args:
            df: Price DataFrame

        Returns:
            OBV series
        """
        obv = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
        return obv

    def calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate Volume Weighted Average Price.

        Args:
            df: Price DataFrame

        Returns:
            VWAP series
        """
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        return vwap

    async def get_moving_averages(self, stock_id: str) -> MovingAverageData:
        """
        Calculate moving averages for a stock.

        Args:
            stock_id: Stock ID

        Returns:
            Moving average data
        """
        # Get 200 days of price data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=250)

        prices = await self.price_repo.get_price_history(stock_id, start_date, end_date)
        df = self._prices_to_dataframe(prices)

        if df.empty:
            return MovingAverageData()

        latest_idx = df.index[-1]

        ma_data = MovingAverageData(
            sma_20=Decimal(str(self.calculate_sma(df, 20).loc[latest_idx])) if len(df) >= 20 else None,
            sma_50=Decimal(str(self.calculate_sma(df, 50).loc[latest_idx])) if len(df) >= 50 else None,
            sma_200=Decimal(str(self.calculate_sma(df, 200).loc[latest_idx])) if len(df) >= 200 else None,
            ema_12=Decimal(str(self.calculate_ema(df, 12).loc[latest_idx])) if len(df) >= 12 else None,
            ema_26=Decimal(str(self.calculate_ema(df, 26).loc[latest_idx])) if len(df) >= 26 else None,
        )

        return ma_data

    async def get_momentum_indicators(self, stock_id: str) -> MomentumIndicators:
        """
        Calculate momentum indicators for a stock.

        Args:
            stock_id: Stock ID

        Returns:
            Momentum indicators
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=100)

        prices = await self.price_repo.get_price_history(stock_id, start_date, end_date)
        df = self._prices_to_dataframe(prices)

        if df.empty:
            return MomentumIndicators()

        latest_idx = df.index[-1]

        rsi = self.calculate_rsi(df)
        rsi_value = rsi.loc[latest_idx] if not rsi.empty else None

        rsi_signal = None
        if rsi_value:
            if rsi_value > 70:
                rsi_signal = "overbought"
            elif rsi_value < 30:
                rsi_signal = "oversold"
            else:
                rsi_signal = "neutral"

        return MomentumIndicators(
            rsi=Decimal(str(rsi_value)) if rsi_value else None,
            rsi_signal=rsi_signal
        )

    async def get_trend_indicators(self, stock_id: str) -> TrendIndicators:
        """
        Calculate trend indicators for a stock.

        Args:
            stock_id: Stock ID

        Returns:
            Trend indicators
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=100)

        prices = await self.price_repo.get_price_history(stock_id, start_date, end_date)
        df = self._prices_to_dataframe(prices)

        if df.empty:
            return TrendIndicators()

        latest_idx = df.index[-1]

        macd_data = self.calculate_macd(df)

        return TrendIndicators(
            macd=Decimal(str(macd_data["macd"].loc[latest_idx])) if not macd_data["macd"].empty else None,
            macd_signal=Decimal(str(macd_data["signal"].loc[latest_idx])) if not macd_data["signal"].empty else None,
            macd_histogram=Decimal(str(macd_data["histogram"].loc[latest_idx])) if not macd_data["histogram"].empty else None,
        )

    async def get_volatility_indicators(self, stock_id: str) -> VolatilityIndicators:
        """
        Calculate volatility indicators for a stock.

        Args:
            stock_id: Stock ID

        Returns:
            Volatility indicators
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=100)

        prices = await self.price_repo.get_price_history(stock_id, start_date, end_date)
        df = self._prices_to_dataframe(prices)

        if df.empty:
            return VolatilityIndicators()

        latest_idx = df.index[-1]

        bb = self.calculate_bollinger_bands(df)
        atr = self.calculate_atr(df)

        return VolatilityIndicators(
            bollinger_upper=Decimal(str(bb["upper"].loc[latest_idx])) if not bb["upper"].empty else None,
            bollinger_middle=Decimal(str(bb["middle"].loc[latest_idx])) if not bb["middle"].empty else None,
            bollinger_lower=Decimal(str(bb["lower"].loc[latest_idx])) if not bb["lower"].empty else None,
            atr=Decimal(str(atr.loc[latest_idx])) if not atr.empty else None,
        )

    async def get_volume_indicators(self, stock_id: str) -> VolumeIndicators:
        """
        Calculate volume indicators for a stock.

        Args:
            stock_id: Stock ID

        Returns:
            Volume indicators
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=100)

        prices = await self.price_repo.get_price_history(stock_id, start_date, end_date)
        df = self._prices_to_dataframe(prices)

        if df.empty:
            return VolumeIndicators()

        latest_idx = df.index[-1]

        obv = self.calculate_obv(df)
        vwap = self.calculate_vwap(df)

        return VolumeIndicators(
            obv=Decimal(str(obv.loc[latest_idx])) if not obv.empty else None,
            vwap=Decimal(str(vwap.loc[latest_idx])) if not vwap.empty else None,
        )

    def generate_trading_signals(
        self,
        df: pd.DataFrame,
        current_price: float
    ) -> List[TradingSignal]:
        """
        Generate trading signals based on technical indicators.

        Args:
            df: Price DataFrame
            current_price: Current stock price

        Returns:
            List of trading signals
        """
        signals = []

        if df.empty or len(df) < 50:
            return signals

        latest_idx = df.index[-1]

        # RSI signal
        rsi = self.calculate_rsi(df)
        if not rsi.empty:
            rsi_value = rsi.loc[latest_idx]
            if rsi_value < 30:
                signals.append(TradingSignal(
                    signal_type="buy",
                    strength=8,
                    indicators=["RSI"],
                    price=Decimal(str(current_price)),
                    timestamp=datetime.utcnow(),
                    reasoning="RSI indicates oversold condition (below 30)"
                ))
            elif rsi_value > 70:
                signals.append(TradingSignal(
                    signal_type="sell",
                    strength=8,
                    indicators=["RSI"],
                    price=Decimal(str(current_price)),
                    timestamp=datetime.utcnow(),
                    reasoning="RSI indicates overbought condition (above 70)"
                ))

        # MACD signal
        macd_data = self.calculate_macd(df)
        if not macd_data["macd"].empty and not macd_data["signal"].empty:
            macd_current = macd_data["macd"].loc[latest_idx]
            signal_current = macd_data["signal"].loc[latest_idx]

            if len(df) > 1:
                prev_idx = df.index[-2]
                macd_prev = macd_data["macd"].loc[prev_idx]
                signal_prev = macd_data["signal"].loc[prev_idx]

                # Bullish crossover
                if macd_prev < signal_prev and macd_current > signal_current:
                    signals.append(TradingSignal(
                        signal_type="buy",
                        strength=7,
                        indicators=["MACD"],
                        price=Decimal(str(current_price)),
                        timestamp=datetime.utcnow(),
                        reasoning="MACD bullish crossover detected"
                    ))

                # Bearish crossover
                if macd_prev > signal_prev and macd_current < signal_current:
                    signals.append(TradingSignal(
                        signal_type="sell",
                        strength=7,
                        indicators=["MACD"],
                        price=Decimal(str(current_price)),
                        timestamp=datetime.utcnow(),
                        reasoning="MACD bearish crossover detected"
                    ))

        return signals
