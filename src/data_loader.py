"""
data_loader.py - AlphaPulse Investment Risk Monitor
Fetches historical stock data using yfinance API.
Portfolio: 10 stocks across diverse sectors + S&P 500 index.
Includes resilient error handling for API rate limits.
"""

import yfinance as yf
import pandas as pd
import time
import os

STOCKS = [
    "AAPL",   # Technology
    "MSFT",   # Technology
    "JPM",    # Financials
    "JNJ",    # Healthcare
    "XOM",    # Energy
    "AMZN",   # Consumer Discretionary
    "PG",     # Consumer Staples
    "CAT",    # Industrials
    "NEE",    # Utilities
    "BHP",    # Materials
    "^GSPC",  # S&P 500 Index (benchmark)
]

RAW_DATA_PATH = "data/raw_market_data.csv"
PROCESSED_DATA_PATH = "data/processed_market_data.csv"


def load_stock_data(
    tickers: list = STOCKS,
    period: str = "5y",
    max_retries: int = 3,
    retry_delay: int = 5,
) -> pd.DataFrame:
    """
    Download adjusted closing prices for the given tickers using yfinance.
    Returns DataFrame with dates as index and tickers as columns.
    """
    print(f"[AlphaPulse] Fetching data for {len(tickers)} tickers: {tickers}")

    all_data = {}

    for ticker in tickers:
        attempt = 0
        success = False

        while attempt < max_retries and not success:
            try:
                print(f"  -> Downloading {ticker} (attempt {attempt + 1}/{max_retries})...")

                raw = yf.download(
                    ticker,
                    period=period,
                    auto_adjust=True,
                    progress=False,
                    multi_level_index=False,
                )

                if raw is None or raw.empty:
                    print(f"  WARNING: No data returned for {ticker}. Skipping.")
                    break

                # Handle both DataFrame and Series returns from yfinance
                if isinstance(raw, pd.DataFrame):
                    if "Close" in raw.columns:
                        series = raw["Close"].copy()
                    elif "Adj Close" in raw.columns:
                        series = raw["Adj Close"].copy()
                    else:
                        series = raw.iloc[:, 0].copy()
                elif isinstance(raw, pd.Series):
                    series = raw.copy()
                else:
                    print(f"  WARNING: Unexpected type for {ticker}: {type(raw)}. Skipping.")
                    break

                series.index = pd.to_datetime(series.index)
                series.name = ticker

                all_data[ticker] = series
                success = True
                print(f"  OK  {ticker}: {len(series)} rows fetched.")

            except Exception as e:
                attempt += 1
                if "rate" in str(e).lower() or "429" in str(e):
                    print(f"  WARNING: Rate limit for {ticker}. Waiting {retry_delay}s...")
                else:
                    print(f"  ERROR fetching {ticker}: {e}")

                if attempt < max_retries:
                    time.sleep(retry_delay)
                else:
                    print(f"  ERROR: Max retries reached for {ticker}. Skipping.")

        time.sleep(0.5)

    if not all_data:
        raise ValueError("[AlphaPulse] No data fetched. Check internet connection or tickers.")

    # Build DataFrame using pd.concat (handles Series with DatetimeIndex correctly)
    prices = pd.concat(all_data, axis=1)
    prices.index = pd.to_datetime(prices.index)
    prices.index.name = "Date"

    prices.dropna(how="all", inplace=True)
    prices.ffill(inplace=True)
    prices.bfill(inplace=True)

    os.makedirs("data", exist_ok=True)
    prices.to_csv(RAW_DATA_PATH)
    print(f"\n[AlphaPulse] Raw data saved -> {RAW_DATA_PATH}")
    print(f"[AlphaPulse] Shape: {prices.shape}  |  Date range: {prices.index[0].date()} -> {prices.index[-1].date()}")

    return prices


def load_from_csv(path: str = RAW_DATA_PATH) -> pd.DataFrame:
    """Load previously saved price data from CSV."""
    print(f"[AlphaPulse] Loading data from {path} ...")
    df = pd.read_csv(path, index_col="Date", parse_dates=True)
    print(f"[AlphaPulse] Loaded {df.shape[0]} rows x {df.shape[1]} tickers.")
    return df


if __name__ == "__main__":
    prices = load_stock_data()
    print(prices.tail())