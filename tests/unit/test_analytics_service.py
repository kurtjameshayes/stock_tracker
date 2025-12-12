"""
Unit tests for Analytics Service.

Tests technical indicator calculations and trading signal generation.
"""

import pytest
import pandas as pd
import numpy as np
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from app.services.analytics_service import AnalyticsService
from app.repositories.stock_repository import StockPriceRepository


@pytest.fixture
def mock_price_repo():
    """Create mock price repository."""
    return AsyncMock(spec=StockPriceRepository)


@pytest.fixture
def analytics_service(mock_price_repo):
    """Create analytics service with mocked dependencies."""
    return AnalyticsService(mock_price_repo)


@pytest.fixture
def sample_price_df():
    """Generate sample price DataFrame for testing."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    np.random.seed(42)

    # Generate realistic price data
    base_price = 100
    returns = np.random.randn(100) * 0.02  # 2% daily volatility
    prices = base_price * np.exp(np.cumsum(returns))

    df = pd.DataFrame({
        'open': prices * (1 - np.random.rand(100) * 0.01),
        'high': prices * (1 + np.random.rand(100) * 0.02),
        'low': prices * (1 - np.random.rand(100) * 0.02),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)

    return df


@pytest.fixture
def sample_price_list():
    """Generate sample price list as returned from repository."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    np.random.seed(42)

    base_price = 100
    returns = np.random.randn(100) * 0.02
    prices = base_price * np.exp(np.cumsum(returns))

    price_list = []
    for i, date in enumerate(dates):
        price_list.append({
            'timestamp': date.to_pydatetime(),
            'open': float(prices[i] * (1 - np.random.rand() * 0.01)),
            'high': float(prices[i] * (1 + np.random.rand() * 0.02)),
            'low': float(prices[i] * (1 - np.random.rand() * 0.02)),
            'close': float(prices[i]),
            'volume': int(np.random.randint(1000000, 10000000))
        })

    return price_list


class TestPricesToDataframe:
    """Tests for price list to DataFrame conversion."""

    def test_empty_prices_returns_empty_df(self, analytics_service):
        """Test that empty price list returns empty DataFrame."""
        df = analytics_service._prices_to_dataframe([])

        assert df.empty

    def test_prices_converted_to_dataframe(self, analytics_service, sample_price_list):
        """Test that price list is properly converted to DataFrame."""
        df = analytics_service._prices_to_dataframe(sample_price_list)

        assert not df.empty
        assert len(df) == 100
        assert 'close' in df.columns
        assert 'volume' in df.columns

    def test_dataframe_sorted_by_timestamp(self, analytics_service):
        """Test that DataFrame is sorted by timestamp."""
        unsorted_prices = [
            {'timestamp': datetime(2024, 1, 3), 'open': 102, 'high': 103, 'low': 101, 'close': 102, 'volume': 1000},
            {'timestamp': datetime(2024, 1, 1), 'open': 100, 'high': 101, 'low': 99, 'close': 100, 'volume': 1000},
            {'timestamp': datetime(2024, 1, 2), 'open': 101, 'high': 102, 'low': 100, 'close': 101, 'volume': 1000},
        ]

        df = analytics_service._prices_to_dataframe(unsorted_prices)

        assert df.index[0].day == 1
        assert df.index[1].day == 2
        assert df.index[2].day == 3


class TestSimpleMovingAverage:
    """Tests for SMA calculation."""

    def test_sma_calculation(self, analytics_service, sample_price_df):
        """Test SMA is calculated correctly."""
        sma = analytics_service.calculate_sma(sample_price_df, period=20)

        assert len(sma) == len(sample_price_df)
        # First 19 values should be NaN
        assert pd.isna(sma.iloc[18])
        # Value at index 19 should be calculated
        assert pd.notna(sma.iloc[19])

    def test_sma_value_correctness(self, analytics_service):
        """Test SMA value is correct for known data."""
        df = pd.DataFrame({
            'close': [10, 20, 30, 40, 50]
        })

        sma = analytics_service.calculate_sma(df, period=3)

        # SMA at index 2 should be (10+20+30)/3 = 20
        assert sma.iloc[2] == 20.0
        # SMA at index 4 should be (30+40+50)/3 = 40
        assert sma.iloc[4] == 40.0


class TestExponentialMovingAverage:
    """Tests for EMA calculation."""

    def test_ema_calculation(self, analytics_service, sample_price_df):
        """Test EMA is calculated correctly."""
        ema = analytics_service.calculate_ema(sample_price_df, period=12)

        assert len(ema) == len(sample_price_df)
        # EMA should have values from the start (unlike SMA)
        assert pd.notna(ema.iloc[11])

    def test_ema_more_weight_to_recent(self, analytics_service):
        """Test that EMA gives more weight to recent prices."""
        df = pd.DataFrame({
            'close': [100, 100, 100, 100, 200]  # Sudden jump
        })

        ema = analytics_service.calculate_ema(df, period=3)
        sma = analytics_service.calculate_sma(df, period=3)

        # EMA should react faster to the jump than SMA
        assert ema.iloc[4] > sma.iloc[4]


class TestRSI:
    """Tests for RSI calculation."""

    def test_rsi_calculation(self, analytics_service, sample_price_df):
        """Test RSI is calculated correctly."""
        rsi = analytics_service.calculate_rsi(sample_price_df, period=14)

        assert len(rsi) == len(sample_price_df)
        # RSI should be between 0 and 100 (where not NaN)
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()

    def test_rsi_overbought_oversold(self, analytics_service):
        """Test RSI identifies overbought/oversold conditions."""
        # Create consistently rising prices
        df_up = pd.DataFrame({
            'close': [100 + i * 5 for i in range(20)]
        })

        rsi_up = analytics_service.calculate_rsi(df_up, period=14)
        # RSI should be high (overbought territory) for consistently rising prices
        assert rsi_up.iloc[-1] > 70

        # Create consistently falling prices
        df_down = pd.DataFrame({
            'close': [200 - i * 5 for i in range(20)]
        })

        rsi_down = analytics_service.calculate_rsi(df_down, period=14)
        # RSI should be low (oversold territory) for consistently falling prices
        assert rsi_down.iloc[-1] < 30


class TestMACD:
    """Tests for MACD calculation."""

    def test_macd_calculation(self, analytics_service, sample_price_df):
        """Test MACD components are calculated correctly."""
        macd_data = analytics_service.calculate_macd(sample_price_df)

        assert "macd" in macd_data
        assert "signal" in macd_data
        assert "histogram" in macd_data
        assert len(macd_data["macd"]) == len(sample_price_df)

    def test_macd_histogram_is_difference(self, analytics_service, sample_price_df):
        """Test that MACD histogram is the difference between MACD and signal."""
        macd_data = analytics_service.calculate_macd(sample_price_df)

        calculated_histogram = macd_data["macd"] - macd_data["signal"]

        # Allow small floating point differences
        diff = (calculated_histogram - macd_data["histogram"]).abs()
        assert (diff < 0.0001).all()


class TestBollingerBands:
    """Tests for Bollinger Bands calculation."""

    def test_bollinger_bands_calculation(self, analytics_service, sample_price_df):
        """Test Bollinger Bands are calculated correctly."""
        bb = analytics_service.calculate_bollinger_bands(sample_price_df, period=20, std_dev=2)

        assert "upper" in bb
        assert "middle" in bb
        assert "lower" in bb
        assert len(bb["upper"]) == len(sample_price_df)

    def test_bollinger_bands_relationships(self, analytics_service, sample_price_df):
        """Test that upper > middle > lower."""
        bb = analytics_service.calculate_bollinger_bands(sample_price_df, period=20, std_dev=2)

        # Get non-NaN values
        valid_idx = ~bb["middle"].isna()

        assert (bb["upper"][valid_idx] > bb["middle"][valid_idx]).all()
        assert (bb["middle"][valid_idx] > bb["lower"][valid_idx]).all()

    def test_bollinger_bands_middle_is_sma(self, analytics_service, sample_price_df):
        """Test that middle band equals SMA."""
        bb = analytics_service.calculate_bollinger_bands(sample_price_df, period=20)
        sma = analytics_service.calculate_sma(sample_price_df, period=20)

        diff = (bb["middle"] - sma).abs()
        assert (diff < 0.0001).all() or diff.isna().all()


class TestATR:
    """Tests for ATR calculation."""

    def test_atr_calculation(self, analytics_service, sample_price_df):
        """Test ATR is calculated correctly."""
        atr = analytics_service.calculate_atr(sample_price_df, period=14)

        assert len(atr) == len(sample_price_df)
        # ATR should be positive
        valid_atr = atr.dropna()
        assert (valid_atr >= 0).all()

    def test_atr_reflects_volatility(self, analytics_service):
        """Test that ATR reflects volatility levels."""
        # Low volatility data
        low_vol = pd.DataFrame({
            'open': [100] * 20,
            'high': [101] * 20,
            'low': [99] * 20,
            'close': [100] * 20
        })

        # High volatility data
        high_vol = pd.DataFrame({
            'open': [100] * 20,
            'high': [110] * 20,
            'low': [90] * 20,
            'close': [100] * 20
        })

        atr_low = analytics_service.calculate_atr(low_vol, period=14)
        atr_high = analytics_service.calculate_atr(high_vol, period=14)

        assert atr_high.iloc[-1] > atr_low.iloc[-1]


class TestOBV:
    """Tests for OBV calculation."""

    def test_obv_calculation(self, analytics_service, sample_price_df):
        """Test OBV is calculated correctly."""
        obv = analytics_service.calculate_obv(sample_price_df)

        assert len(obv) == len(sample_price_df)

    def test_obv_direction(self, analytics_service):
        """Test OBV direction based on price movement."""
        df = pd.DataFrame({
            'close': [100, 110, 120, 130, 140],  # Rising prices
            'volume': [1000, 1000, 1000, 1000, 1000]
        })

        obv = analytics_service.calculate_obv(df)

        # OBV should be increasing with rising prices
        assert obv.iloc[-1] > obv.iloc[0]


class TestVWAP:
    """Tests for VWAP calculation."""

    def test_vwap_calculation(self, analytics_service, sample_price_df):
        """Test VWAP is calculated correctly."""
        vwap = analytics_service.calculate_vwap(sample_price_df)

        assert len(vwap) == len(sample_price_df)
        assert pd.notna(vwap.iloc[-1])


class TestGetMovingAverages:
    """Tests for async moving average retrieval."""

    @pytest.mark.asyncio
    async def test_get_moving_averages_success(self, analytics_service, mock_price_repo, sample_price_list):
        """Test getting moving averages for a stock."""
        mock_price_repo.get_price_history.return_value = sample_price_list

        result = await analytics_service.get_moving_averages("stock123")

        assert result is not None
        mock_price_repo.get_price_history.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_moving_averages_empty_data(self, analytics_service, mock_price_repo):
        """Test moving averages with no price data returns empty result."""
        mock_price_repo.get_price_history.return_value = []

        result = await analytics_service.get_moving_averages("stock123")

        # Should return empty MovingAverageData
        assert result.sma_20 is None


class TestGetMomentumIndicators:
    """Tests for momentum indicators retrieval."""

    @pytest.mark.asyncio
    async def test_get_momentum_indicators_success(self, analytics_service, mock_price_repo, sample_price_list):
        """Test getting momentum indicators for a stock."""
        mock_price_repo.get_price_history.return_value = sample_price_list

        result = await analytics_service.get_momentum_indicators("stock123")

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_momentum_indicators_empty_data(self, analytics_service, mock_price_repo):
        """Test momentum indicators with no price data returns empty result."""
        mock_price_repo.get_price_history.return_value = []

        result = await analytics_service.get_momentum_indicators("stock123")

        assert result.rsi is None


class TestGetTrendIndicators:
    """Tests for trend indicators retrieval."""

    @pytest.mark.asyncio
    async def test_get_trend_indicators_success(self, analytics_service, mock_price_repo, sample_price_list):
        """Test getting trend indicators for a stock."""
        mock_price_repo.get_price_history.return_value = sample_price_list

        result = await analytics_service.get_trend_indicators("stock123")

        assert result is not None


class TestGetVolatilityIndicators:
    """Tests for volatility indicators retrieval."""

    @pytest.mark.asyncio
    async def test_get_volatility_indicators_success(self, analytics_service, mock_price_repo, sample_price_list):
        """Test getting volatility indicators for a stock."""
        mock_price_repo.get_price_history.return_value = sample_price_list

        result = await analytics_service.get_volatility_indicators("stock123")

        assert result is not None


class TestGetVolumeIndicators:
    """Tests for volume indicators retrieval."""

    @pytest.mark.asyncio
    async def test_get_volume_indicators_success(self, analytics_service, mock_price_repo, sample_price_list):
        """Test getting volume indicators for a stock."""
        mock_price_repo.get_price_history.return_value = sample_price_list

        result = await analytics_service.get_volume_indicators("stock123")

        assert result is not None


class TestGenerateTradingSignals:
    """Tests for trading signal generation."""

    def test_generate_signals_empty_df(self, analytics_service):
        """Test signal generation with empty DataFrame returns empty list."""
        df = pd.DataFrame()

        signals = analytics_service.generate_trading_signals(df, 100.0)

        assert signals == []

    def test_generate_signals_insufficient_data(self, analytics_service):
        """Test signal generation with insufficient data returns empty list."""
        df = pd.DataFrame({
            'close': [100] * 10
        })

        signals = analytics_service.generate_trading_signals(df, 100.0)

        assert signals == []

    def test_generate_rsi_oversold_signal(self, analytics_service):
        """Test that RSI oversold condition generates buy signal."""
        # Create consistently falling prices to trigger RSI oversold
        df = pd.DataFrame({
            'close': [200 - i * 3 for i in range(60)]
        }, index=pd.date_range(start='2024-01-01', periods=60, freq='D'))

        signals = analytics_service.generate_trading_signals(df, 80.0)

        rsi_signals = [s for s in signals if "RSI" in s.indicators]
        # Should have a buy signal from RSI oversold
        buy_signals = [s for s in rsi_signals if s.signal_type == "buy"]
        assert len(buy_signals) > 0

    def test_generate_rsi_overbought_signal(self, analytics_service):
        """Test that RSI overbought condition generates sell signal."""
        # Create consistently rising prices to trigger RSI overbought
        df = pd.DataFrame({
            'close': [100 + i * 3 for i in range(60)]
        }, index=pd.date_range(start='2024-01-01', periods=60, freq='D'))

        signals = analytics_service.generate_trading_signals(df, 280.0)

        rsi_signals = [s for s in signals if "RSI" in s.indicators]
        # Should have a sell signal from RSI overbought
        sell_signals = [s for s in rsi_signals if s.signal_type == "sell"]
        assert len(sell_signals) > 0

    def test_signal_contains_required_fields(self, analytics_service):
        """Test that generated signals contain all required fields."""
        df = pd.DataFrame({
            'close': [200 - i * 3 for i in range(60)]
        }, index=pd.date_range(start='2024-01-01', periods=60, freq='D'))

        signals = analytics_service.generate_trading_signals(df, 80.0)

        if signals:  # If any signals generated
            signal = signals[0]
            assert hasattr(signal, 'signal_type')
            assert hasattr(signal, 'strength')
            assert hasattr(signal, 'indicators')
            assert hasattr(signal, 'price')
            assert hasattr(signal, 'timestamp')
            assert hasattr(signal, 'reasoning')
