# Data loading module
import yfinance as yf
import pandas as pd

def load_stock_data(tickers, start="2020-01-01", end="2025-01-01"):
    
    data = yf.download(tickers, start=start, end=end)["Close"]
    
    data.to_csv("../data/raw_market_data.csv")
    
    return data


if __name__ == "__main__":
    
    stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    
    df = load_stock_data(stocks)
    
    print(df.head())
