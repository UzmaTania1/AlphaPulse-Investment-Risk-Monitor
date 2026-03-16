import numpy as np
import pandas as pd

# number of simulations
num_simulations = 500

returns = np.random.normal(0.12, 0.05, num_simulations)
volatility = np.random.normal(0.20, 0.04, num_simulations)

simulations = np.arange(1, num_simulations+1)

df = pd.DataFrame({
    "Simulation": simulations,
    "Return": returns,
    "Volatility": volatility
})

df.to_csv("data/monte_carlo_results.csv", index=False)

print(df.head())

