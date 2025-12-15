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

    def calculate_stochastic(
        self,
        df: pd.DataFrame,
        k_period: int = 14,
        d_period: int = 3
    ) -> Dict[str, pd.Series]:
        """
        Calculate Stochastic Oscillator.

        Args:
            df: Price DataFrame
            k_period: %K period (default 14)
            d_period: %D smoothing period (default 3)

        Returns:
            Dict with %K and %D lines
        """
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()

        stoch_k = 100 * (df['close'] - low_min) / (high_max - low_min)
        stoch_d = stoch_k.rolling(window=d_period).mean()

        return {
            "k": stoch_k,
            "d": stoch_d
        }

    def calculate_cci(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        Calculate Commodity Channel Index.

        Args:
            df: Price DataFrame
            period: CCI period (default 20)

        Returns:
            CCI series
        """
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mean_deviation = typical_price.rolling(window=period).apply(
            lambda x: np.abs(x - x.mean()).mean()
        )

        cci = (typical_price - sma_tp) / (0.015 * mean_deviation)
        return cci

    def calculate_roc(self, df: pd.DataFrame, period: int = 12) -> pd.Series:
        """
        Calculate Rate of Change.

        Args:
            df: Price DataFrame
            period: ROC period (default 12)

        Returns:
            ROC series (percentage)
        """
        roc = ((df['close'] - df['close'].shift(period)) / df['close'].shift(period)) * 100
        return roc

    def calculate_williams_r(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Williams %R.

        Args:
            df: Price DataFrame
            period: Lookback period (default 14)

        Returns:
            Williams %R series
        """
        high_max = df['high'].rolling(window=period).max()
        low_min = df['low'].rolling(window=period).min()

        williams_r = -100 * (high_max - df['close']) / (high_max - low_min)
        return williams_r

    def calculate_adx(self, df: pd.DataFrame, period: int = 14) -> Dict[str, pd.Series]:
        """
        Calculate Average Directional Index.

        Args:
            df: Price DataFrame
            period: ADX period (default 14)

        Returns:
            Dict with ADX, +DI, and -DI
        """
        high = df['high']
        low = df['low']
        close = df['close']

        # Calculate True Range
        tr1 = high - low
        tr2 = np.abs(high - close.shift())
        tr3 = np.abs(low - close.shift())
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Calculate directional movement
        plus_dm = high.diff()
        minus_dm = -low.diff()

        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        # When both are positive, keep only the larger one
        plus_dm[(plus_dm > 0) & (minus_dm > 0) & (plus_dm <= minus_dm)] = 0
        minus_dm[(plus_dm > 0) & (minus_dm > 0) & (minus_dm < plus_dm)] = 0

        # Smooth with EMA
        atr = true_range.ewm(span=period, adjust=False).mean()
        plus_di = 100 * (plus_dm.ewm(span=period, adjust=False).mean() / atr)
        minus_di = 100 * (minus_dm.ewm(span=period, adjust=False).mean() / atr)

        # Calculate DX and ADX
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.ewm(span=period, adjust=False).mean()

        return {
            "adx": adx,
            "plus_di": plus_di,
            "minus_di": minus_di
        }

    def calculate_standard_deviation(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        Calculate rolling standard deviation of closing prices.

        Args:
            df: Price DataFrame
            period: Rolling period (default 20)

        Returns:
            Standard deviation series
        """
        return df['close'].rolling(window=period).std()

    def calculate_volume_sma(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        Calculate Volume Simple Moving Average.

        Args:
            df: Price DataFrame
            period: Period length (default 20)

        Returns:
            Volume SMA series
        """
        return df['volume'].rolling(window=period).mean()

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

        # RSI
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

        # Stochastic
        stoch = self.calculate_stochastic(df)
        stoch_k = stoch["k"].loc[latest_idx] if not stoch["k"].empty else None
        stoch_d = stoch["d"].loc[latest_idx] if not stoch["d"].empty else None

        # CCI
        cci = self.calculate_cci(df)
        cci_value = cci.loc[latest_idx] if not cci.empty else None

        # ROC
        roc = self.calculate_roc(df)
        roc_value = roc.loc[latest_idx] if not roc.empty else None

        return MomentumIndicators(
            rsi=Decimal(str(rsi_value)) if rsi_value and not np.isnan(rsi_value) else None,
            rsi_signal=rsi_signal,
            stochastic_k=Decimal(str(stoch_k)) if stoch_k and not np.isnan(stoch_k) else None,
            stochastic_d=Decimal(str(stoch_d)) if stoch_d and not np.isnan(stoch_d) else None,
            cci=Decimal(str(cci_value)) if cci_value and not np.isnan(cci_value) else None,
            roc=Decimal(str(roc_value)) if roc_value and not np.isnan(roc_value) else None,
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

        # MACD
        macd_data = self.calculate_macd(df)
        macd_value = macd_data["macd"].loc[latest_idx] if not macd_data["macd"].empty else None
        macd_signal_value = macd_data["signal"].loc[latest_idx] if not macd_data["signal"].empty else None
        macd_hist = macd_data["histogram"].loc[latest_idx] if not macd_data["histogram"].empty else None

        # ADX
        adx_data = self.calculate_adx(df)
        adx_value = adx_data["adx"].loc[latest_idx] if not adx_data["adx"].empty else None

        # Determine ADX signal based on strength
        adx_signal = None
        if adx_value and not np.isnan(adx_value):
            plus_di = adx_data["plus_di"].loc[latest_idx]
            minus_di = adx_data["minus_di"].loc[latest_idx]
            if adx_value > 25:
                if plus_di > minus_di:
                    adx_signal = "strong_uptrend"
                else:
                    adx_signal = "strong_downtrend"
            else:
                adx_signal = "weak"

        return TrendIndicators(
            macd=Decimal(str(macd_value)) if macd_value and not np.isnan(macd_value) else None,
            macd_signal=Decimal(str(macd_signal_value)) if macd_signal_value and not np.isnan(macd_signal_value) else None,
            macd_histogram=Decimal(str(macd_hist)) if macd_hist and not np.isnan(macd_hist) else None,
            adx=Decimal(str(adx_value)) if adx_value and not np.isnan(adx_value) else None,
            adx_signal=adx_signal,
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
        std_dev = self.calculate_standard_deviation(df)

        bb_upper = bb["upper"].loc[latest_idx] if not bb["upper"].empty else None
        bb_middle = bb["middle"].loc[latest_idx] if not bb["middle"].empty else None
        bb_lower = bb["lower"].loc[latest_idx] if not bb["lower"].empty else None
        atr_value = atr.loc[latest_idx] if not atr.empty else None
        std_value = std_dev.loc[latest_idx] if not std_dev.empty else None

        return VolatilityIndicators(
            bollinger_upper=Decimal(str(bb_upper)) if bb_upper and not np.isnan(bb_upper) else None,
            bollinger_middle=Decimal(str(bb_middle)) if bb_middle and not np.isnan(bb_middle) else None,
            bollinger_lower=Decimal(str(bb_lower)) if bb_lower and not np.isnan(bb_lower) else None,
            atr=Decimal(str(atr_value)) if atr_value and not np.isnan(atr_value) else None,
            standard_deviation=Decimal(str(std_value)) if std_value and not np.isnan(std_value) else None,
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
        vol_sma = self.calculate_volume_sma(df)

        obv_value = obv.loc[latest_idx] if not obv.empty else None
        vwap_value = vwap.loc[latest_idx] if not vwap.empty else None
        vol_sma_value = vol_sma.loc[latest_idx] if not vol_sma.empty else None

        return VolumeIndicators(
            obv=Decimal(str(obv_value)) if obv_value and not np.isnan(obv_value) else None,
            vwap=Decimal(str(vwap_value)) if vwap_value and not np.isnan(vwap_value) else None,
            volume_sma=Decimal(str(vol_sma_value)) if vol_sma_value and not np.isnan(vol_sma_value) else None,
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

    async def get_trading_signals(self, stock_id: str) -> List[TradingSignal]:
        """
        Get trading signals for a stock.

        Args:
            stock_id: Stock ID

        Returns:
            List of trading signals
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=100)

        prices = await self.price_repo.get_price_history(stock_id, start_date, end_date)
        df = self._prices_to_dataframe(prices)

        if df.empty:
            return []

        # Get latest price
        current_price = float(df['close'].iloc[-1])

        return self.generate_trading_signals(df, current_price)

    def calculate_support_resistance(
        self,
        df: pd.DataFrame,
        lookback: int = 20
    ) -> Dict[str, Any]:
        """
        Calculate support and resistance levels using pivot points and local extrema.

        Args:
            df: Price DataFrame
            lookback: Lookback period for finding levels

        Returns:
            Dict with support levels, resistance levels, pivot point, and fibonacci levels
        """
        if df.empty or len(df) < lookback:
            return {
                "support_levels": [],
                "resistance_levels": [],
                "pivot_point": None,
                "fibonacci_levels": {}
            }

        # Use recent data for pivot calculation
        recent_df = df.tail(lookback)

        high = recent_df['high'].max()
        low = recent_df['low'].min()
        close = df['close'].iloc[-1]

        # Calculate pivot point
        pivot = (high + low + close) / 3

        # Calculate support and resistance from pivot
        r1 = (2 * pivot) - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)

        s1 = (2 * pivot) - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)

        # Find local maxima and minima for additional support/resistance
        support_levels = [s1, s2, s3]
        resistance_levels = [r1, r2, r3]

        # Calculate Fibonacci retracement levels
        price_range = high - low
        fib_levels = {
            "0.0": high,
            "0.236": high - (price_range * 0.236),
            "0.382": high - (price_range * 0.382),
            "0.5": high - (price_range * 0.5),
            "0.618": high - (price_range * 0.618),
            "0.786": high - (price_range * 0.786),
            "1.0": low
        }

        return {
            "support_levels": sorted([s for s in support_levels if not np.isnan(s)], reverse=True),
            "resistance_levels": sorted([r for r in resistance_levels if not np.isnan(r)]),
            "pivot_point": pivot,
            "fibonacci_levels": fib_levels
        }

    async def get_support_resistance(self, stock_id: str) -> SupportResistance:
        """
        Get support and resistance levels for a stock.

        Args:
            stock_id: Stock ID

        Returns:
            Support and resistance data
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=100)

        prices = await self.price_repo.get_price_history(stock_id, start_date, end_date)
        df = self._prices_to_dataframe(prices)

        if df.empty:
            return SupportResistance()

        sr_data = self.calculate_support_resistance(df)

        return SupportResistance(
            support_levels=[Decimal(str(s)) for s in sr_data["support_levels"]],
            resistance_levels=[Decimal(str(r)) for r in sr_data["resistance_levels"]],
            pivot_point=Decimal(str(sr_data["pivot_point"])) if sr_data["pivot_point"] else None,
            fibonacci_levels={k: Decimal(str(v)) for k, v in sr_data["fibonacci_levels"].items()}
        )

    async def get_comprehensive_analysis(
        self,
        stock_id: str,
        symbol: str
    ) -> ComprehensiveAnalysis:
        """
        Get comprehensive technical analysis for a stock.

        Args:
            stock_id: Stock ID
            symbol: Stock symbol

        Returns:
            Comprehensive analysis data
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=250)

        prices = await self.price_repo.get_price_history(stock_id, start_date, end_date)
        df = self._prices_to_dataframe(prices)

        if df.empty:
            return ComprehensiveAnalysis(
                symbol=symbol,
                current_price=Decimal("0"),
                timestamp=datetime.utcnow(),
                moving_averages=MovingAverageData(),
                momentum=MomentumIndicators(),
                trend=TrendIndicators(),
                volatility=VolatilityIndicators(),
                volume=VolumeIndicators(),
                support_resistance=SupportResistance(),
                signals=[],
                patterns=[],
                technical_rating="neutral",
                risk_level="medium",
                summary="Insufficient data for analysis"
            )

        current_price = Decimal(str(df['close'].iloc[-1]))

        # Get all indicators
        moving_averages = await self.get_moving_averages(stock_id)
        momentum = await self.get_momentum_indicators(stock_id)
        trend = await self.get_trend_indicators(stock_id)
        volatility = await self.get_volatility_indicators(stock_id)
        volume = await self.get_volume_indicators(stock_id)
        support_resistance = await self.get_support_resistance(stock_id)
        signals = self.generate_trading_signals(df, float(current_price))

        # Calculate technical rating based on indicators
        buy_signals = 0
        sell_signals = 0
        total_signals = 0

        # RSI signal
        if momentum.rsi:
            total_signals += 1
            if float(momentum.rsi) < 30:
                buy_signals += 1
            elif float(momentum.rsi) > 70:
                sell_signals += 1

        # MACD signal
        if trend.macd and trend.macd_signal:
            total_signals += 1
            if float(trend.macd) > float(trend.macd_signal):
                buy_signals += 1
            else:
                sell_signals += 1

        # Moving average signals
        if moving_averages.sma_50 and moving_averages.sma_200:
            total_signals += 1
            if float(moving_averages.sma_50) > float(moving_averages.sma_200):
                buy_signals += 1
            else:
                sell_signals += 1

        # ADX trend strength
        if trend.adx:
            total_signals += 1
            if trend.adx_signal == "strong_uptrend":
                buy_signals += 1
            elif trend.adx_signal == "strong_downtrend":
                sell_signals += 1

        # Stochastic signal
        if momentum.stochastic_k:
            total_signals += 1
            if float(momentum.stochastic_k) < 20:
                buy_signals += 1
            elif float(momentum.stochastic_k) > 80:
                sell_signals += 1

        # Determine rating
        if total_signals > 0:
            buy_ratio = buy_signals / total_signals
            sell_ratio = sell_signals / total_signals

            if buy_ratio >= 0.7:
                technical_rating = "strong_buy"
            elif buy_ratio >= 0.5:
                technical_rating = "buy"
            elif sell_ratio >= 0.7:
                technical_rating = "strong_sell"
            elif sell_ratio >= 0.5:
                technical_rating = "sell"
            else:
                technical_rating = "neutral"
        else:
            technical_rating = "neutral"

        # Determine risk level based on volatility
        risk_level = "medium"
        if volatility.atr and volatility.bollinger_middle:
            atr_percent = (float(volatility.atr) / float(volatility.bollinger_middle)) * 100
            if atr_percent > 5:
                risk_level = "high"
            elif atr_percent < 2:
                risk_level = "low"

        # Generate summary
        summary_parts = []

        if technical_rating in ["strong_buy", "buy"]:
            summary_parts.append(f"Technical indicators suggest bullish sentiment for {symbol}.")
        elif technical_rating in ["strong_sell", "sell"]:
            summary_parts.append(f"Technical indicators suggest bearish sentiment for {symbol}.")
        else:
            summary_parts.append(f"Technical indicators are mixed for {symbol}.")

        if momentum.rsi_signal:
            summary_parts.append(f"RSI indicates {momentum.rsi_signal} conditions.")

        if trend.adx_signal:
            if trend.adx_signal == "strong_uptrend":
                summary_parts.append("Strong upward trend detected.")
            elif trend.adx_signal == "strong_downtrend":
                summary_parts.append("Strong downward trend detected.")
            else:
                summary_parts.append("Trend strength is weak.")

        summary = " ".join(summary_parts)

        return ComprehensiveAnalysis(
            symbol=symbol,
            current_price=current_price,
            timestamp=datetime.utcnow(),
            moving_averages=moving_averages,
            momentum=momentum,
            trend=trend,
            volatility=volatility,
            volume=volume,
            support_resistance=support_resistance,
            signals=signals,
            patterns=[],  # Chart pattern detection not yet implemented
            technical_rating=technical_rating,
            risk_level=risk_level,
            summary=summary
        )
