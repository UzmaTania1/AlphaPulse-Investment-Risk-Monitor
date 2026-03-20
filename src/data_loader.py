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

# ── Diverse 10-stock portfolio spanning multiple sectors + S&P 500 index ──
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

    Args:
        tickers      : List of ticker symbols (default: project portfolio).
        period       : Data period string accepted by yfinance (e.g. '5y', '2y').
        max_retries  : Number of retry attempts on API failure / rate-limit.
        retry_delay  : Seconds to wait between retries.

    Returns:
        DataFrame with dates as index and tickers as columns (Adj Close prices).
    """
    print(f"[AlphaPulse] Fetching data for {len(tickers)} tickers: {tickers}")

    all_data = {}

    for ticker in tickers:
        attempt = 0
        success = False

        while attempt < max_retries and not success:
            try:
                print(f"  → Downloading {ticker} (attempt {attempt + 1}/{max_retries})...")
                raw = yf.download(
                    ticker,
                    period=period,
                    auto_adjust=True,   # handles splits & dividends automatically
                    progress=False,
                )

                if raw.empty:
                    print(f"  ⚠  No data returned for {ticker}. Skipping.")
                    break

                # Use 'Close' column (auto_adjust=True renames Adj Close → Close)
                all_data[ticker] = raw["Close"]
                success = True
                print(f"  ✓  {ticker}: {len(raw)} rows fetched.")

            except Exception as e:
                attempt += 1
                if "rate" in str(e).lower() or "429" in str(e):
                    print(f"  ⚠  Rate limit hit for {ticker}. Waiting {retry_delay}s before retry...")
                else:
                    print(f"  ✗  Error fetching {ticker}: {e}")

                if attempt < max_retries:
                    time.sleep(retry_delay)
                else:
                    print(f"  ✗  Max retries reached for {ticker}. Skipping.")

        # Small polite delay between tickers to avoid hammering the API
        time.sleep(0.5)

    if not all_data:
        raise ValueError("[AlphaPulse] No data was fetched. Check your internet connection or ticker symbols.")

    prices = pd.DataFrame(all_data)
    prices.index.name = "Date"

    # ── Drop rows where ALL tickers are NaN (e.g. weekends/holidays) ──
    prices.dropna(how="all", inplace=True)

    # ── Forward-fill then back-fill to handle occasional missing closes ──
    prices.ffill(inplace=True)
    prices.bfill(inplace=True)

    # ── Persist raw data ──
    os.makedirs("data", exist_ok=True)
    prices.to_csv(RAW_DATA_PATH)
    print(f"\n[AlphaPulse] Raw data saved → {RAW_DATA_PATH}")
    print(f"[AlphaPulse] Shape: {prices.shape}  |  Date range: {prices.index[0].date()} → {prices.index[-1].date()}")

    return prices


def load_from_csv(path: str = RAW_DATA_PATH) -> pd.DataFrame:
    """
    Load previously saved price data from CSV (offline / fast reload).

    Args:
        path : Path to the CSV file.

    Returns:
        DataFrame of prices with a DatetimeIndex.
    """
    print(f"[AlphaPulse] Loading data from {path} ...")
    df = pd.read_csv(path, index_col="Date", parse_dates=True)
    print(f"[AlphaPulse] Loaded {df.shape[0]} rows × {df.shape[1]} tickers.")
    return df


if __name__ == "__main__":
    prices = load_stock_data()
    print(prices.tail())
