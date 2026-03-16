import pandas as pd
from src.data_loader import load_stock_data
from src.returns_calculator import calculate_returns
from src.correlation import plot_correlation
from src.volatility import rolling_volatility
from src.var_model import calculate_var
from src.monte_carlo import monte_carlo_simulation

# Load data
stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
data = load_stock_data(stocks)
print("Data loaded:")
print(data.head())

# Calculate returns
returns = calculate_returns(data)
print("\nReturns calculated:")
print(returns.head())

# Plot correlation
plot_correlation(returns)
print("\nCorrelation heatmap saved to images/correlation_heatmap.png")

# Calculate volatility
vol = rolling_volatility(returns)
print("\nRolling volatility calculated:")
print(vol.tail())

# Calculate VaR
var = calculate_var(returns)
print(f"\nVaR at 95% confidence: {var}")

# Monte Carlo simulation
simulations = monte_carlo_simulation(returns, simulations=1000, days=252)
print(f"\nMonte Carlo simulation completed with {len(simulations)} simulations")
print(f"Sample result: Return {simulations[0][0]:.4f}, Volatility {simulations[0][1]:.4f}")

print("\nAll computations completed!")