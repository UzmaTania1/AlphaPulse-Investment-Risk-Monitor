import pandas as pd

def calculate_returns(price_data):

    returns = price_data.pct_change()

    return returns.dropna()
