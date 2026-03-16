import numpy as np

def calculate_var(returns, confidence_level=0.95):
    portfolio_returns = returns.mean(axis=1)
    var = np.percentile(portfolio_returns, (1-confidence_level)*100)
    return var