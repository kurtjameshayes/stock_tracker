#!/usr/bin/env python3
"""
Example script to fetch stock data by ticker symbol using yfinance.

This script demonstrates how to use the yfinance API to retrieve
stock information and return it as JSON.

Usage:
    python fetch_stock_by_ticker.py AAPL
    python fetch_stock_by_ticker.py MSFT GOOGL TSLA
"""

import json
import sys
from typing import Any

import yfinance as yf


def fetch_stock_info(symbol: str) -> dict[str, Any]:
    """
    Fetch stock information for a given ticker symbol.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')

    Returns:
        Dictionary containing stock information from yfinance
    """
    ticker = yf.Ticker(symbol)
    info = ticker.info
    return info


def fetch_stock_history(symbol: str, period: str = "1mo", interval: str = "1d") -> list[dict[str, Any]]:
    """
    Fetch historical price data for a given ticker symbol.

    Args:
        symbol: Stock ticker symbol
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

    Returns:
        List of dictionaries containing historical price data
    """
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period, interval=interval)

    prices = []
    for timestamp, row in hist.iterrows():
        price_data = {
            "timestamp": timestamp.isoformat(),
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": int(row["Volume"]),
        }
        prices.append(price_data)

    return prices


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python fetch_stock_by_ticker.py <TICKER> [TICKER2] [TICKER3] ...")
        print("Example: python fetch_stock_by_ticker.py AAPL")
        sys.exit(1)

    symbols = sys.argv[1:]

    for symbol in symbols:
        symbol = symbol.upper()
        print(f"\n{'='*60}")
        print(f"Fetching data for: {symbol}")
        print("=" * 60)

        # Fetch stock info
        print("\n--- Stock Info ---")
        info = fetch_stock_info(symbol)
        print(json.dumps(info, indent=2, default=str))

        # Fetch historical prices (last month, daily)
        print("\n--- Historical Prices (1 month, daily) ---")
        history = fetch_stock_history(symbol, period="1mo", interval="1d")
        print(json.dumps(history, indent=2))


if __name__ == "__main__":
    main()
