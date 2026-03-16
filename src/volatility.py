import pandas as pd

def rolling_volatility(returns, window=30):
    volatility = returns.rolling(window).std()
    return volatility