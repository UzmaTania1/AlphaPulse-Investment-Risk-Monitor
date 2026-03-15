import pandas as pd
from src.data_loader import load_stock_data
from src.returns_calculator import calculate_returns
from src.volatility import rolling_volatility
from src.correlation import plot_correlation
from src.var_model import calculate_var

stocks = ["AAPL","MSFT","GOOGL","AMZN","TSLA"]

prices = load_stock_data(stocks)

returns = calculate_returns(prices)

volatility = rolling_volatility(returns)

var = calculate_var(returns)

plot_correlation(returns)

print("Portfolio VaR:", var)
