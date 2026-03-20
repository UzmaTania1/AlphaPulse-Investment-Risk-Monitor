"""
monte_carlo.py - AlphaPulse Investment Risk Monitor
Monte Carlo simulation: minimum 10,000 runs as per project specification.
Forecasts portfolio value distribution 1 year into the future.
Exports simulation results to CSV for Tableau visualisation.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

SIMULATIONS = 10_000   # ← Project spec: minimum 10,000 runs
FORECAST_DAYS = 252    # ← 1 trading year ahead


def monte_carlo_simulation(
    returns: pd.DataFrame,
    simulations: int = SIMULATIONS,
    days: int = FORECAST_DAYS,
    initial_portfolio_value: float = 100_000.0,
    confidence_levels: list = [0.95, 0.99],
    export_csv: bool = True,
    export_path: str = "data/monte_carlo_results.csv",
    plot: bool = True,
) -> dict:
    """
    Run a Monte Carlo simulation on a portfolio of stocks.

    The simulation draws daily returns from a multivariate normal distribution
    fitted to the historical log-return mean vector and covariance matrix.
    This preserves cross-asset correlations in every simulated path.

    Args:
        returns          : DataFrame of daily log returns (dates × tickers).
        simulations      : Number of Monte Carlo paths (default 10,000).
        days             : Number of trading days to simulate (default 252 = 1 year).
        initial_portfolio_value : Starting portfolio value in dollars.
        confidence_levels: List of confidence levels for VaR/CVaR reporting.
        export_csv       : Whether to save summary results to CSV.
        export_path      : Output CSV file path.
        plot             : Whether to save a distribution plot.

    Returns:
        Dictionary containing:
            - 'final_values'     : np.array of shape (simulations,) — final portfolio values
            - 'all_paths'        : np.array of shape (simulations, days) — full price paths
            - 'summary_stats'    : dict of key statistics
            - 'var'              : dict of VaR at each confidence level
            - 'cvar'             : dict of CVaR (Expected Shortfall) at each confidence level
    """
    print(f"[AlphaPulse] Running Monte Carlo Simulation")
    print(f"  Simulations : {simulations:,}")
    print(f"  Forecast    : {days} trading days (≈ 1 year)")
    print(f"  Portfolio   : ${initial_portfolio_value:,.0f}")
    print(f"  Assets      : {list(returns.columns)}\n")

    # ── Step 1: Compute mean return vector and covariance matrix ──────────
    mean_returns = returns.mean().values           # shape: (n_assets,)
    cov_matrix   = returns.cov().values            # shape: (n_assets, n_assets)
    n_assets     = len(mean_returns)

    # Equal-weight portfolio weights
    weights = np.ones(n_assets) / n_assets

    # ── Step 2: Cholesky decomposition (preserves correlation structure) ──
    try:
        L = np.linalg.cholesky(cov_matrix)
    except np.linalg.LinAlgError:
        # Fallback: add small jitter to ensure positive-definiteness
        cov_matrix += np.eye(n_assets) * 1e-8
        L = np.linalg.cholesky(cov_matrix)

    # ── Step 3: Simulate paths ─────────────────────────────────────────────
    all_paths    = np.zeros((simulations, days))
    final_values = np.zeros(simulations)

    for i in range(simulations):
        # Draw correlated random returns for all assets over all days
        random_z         = np.random.standard_normal((n_assets, days))   # (n_assets, days)
        correlated_z     = L @ random_z                                   # (n_assets, days)
        daily_returns_sim = mean_returns[:, None] + correlated_z          # (n_assets, days)

        # Portfolio daily return = weighted sum of asset returns
        portfolio_daily  = weights @ daily_returns_sim                    # (days,)

        # Cumulative portfolio value path
        cumulative_path  = initial_portfolio_value * np.exp(np.cumsum(portfolio_daily))
        all_paths[i]     = cumulative_path
        final_values[i]  = cumulative_path[-1]

        if (i + 1) % 2000 == 0:
            print(f"  ... {i + 1:,} / {simulations:,} simulations complete")

    print(f"\n[AlphaPulse] Simulation complete. Computing statistics...")

    # ── Step 4: Summary statistics ────────────────────────────────────────
    summary_stats = {
        "initial_value"        : initial_portfolio_value,
        "mean_final_value"     : float(np.mean(final_values)),
        "median_final_value"   : float(np.median(final_values)),
        "std_final_value"      : float(np.std(final_values)),
        "min_final_value"      : float(np.min(final_values)),
        "max_final_value"      : float(np.max(final_values)),
        "mean_return_pct"      : float((np.mean(final_values) / initial_portfolio_value - 1) * 100),
        "skewness"             : float(_skewness(final_values)),
        "kurtosis"             : float(_kurtosis(final_values)),
        "simulations"          : simulations,
        "forecast_days"        : days,
    }

    # ── Step 5: VaR & CVaR (Expected Shortfall) ───────────────────────────
    profit_loss = final_values - initial_portfolio_value
    var_dict    = {}
    cvar_dict   = {}

    for cl in confidence_levels:
        var_value  = float(np.percentile(profit_loss, (1 - cl) * 100))
        cvar_value = float(profit_loss[profit_loss <= var_value].mean())
        var_dict[f"VaR_{int(cl*100)}"]  = var_value
        cvar_dict[f"CVaR_{int(cl*100)}"] = cvar_value

    # ── Step 6: Export CSV for Tableau ────────────────────────────────────
    if export_csv:
        os.makedirs("data", exist_ok=True)

        # Export final values distribution
        results_df = pd.DataFrame({
            "simulation_id"   : np.arange(1, simulations + 1),
            "final_value"     : final_values,
            "profit_loss"     : profit_loss,
            "return_pct"      : (final_values / initial_portfolio_value - 1) * 100,
        })
        results_df.to_csv(export_path, index=False)
        print(f"[AlphaPulse] Monte Carlo results saved → {export_path}")

        # Export daily paths summary (percentiles) for Tableau line chart
        percentiles_df = _summarise_paths(all_paths, initial_portfolio_value, days)
        pct_path = export_path.replace(".csv", "_daily_percentiles.csv")
        percentiles_df.to_csv(pct_path, index=False)
        print(f"[AlphaPulse] Daily percentile paths saved → {pct_path}")

    # ── Step 7: Plot distribution ─────────────────────────────────────────
    if plot:
        _plot_distribution(final_values, initial_portfolio_value, var_dict, simulations)

    # ── Print results summary ─────────────────────────────────────────────
    print("\n" + "=" * 55)
    print("  MONTE CARLO SIMULATION RESULTS")
    print("=" * 55)
    print(f"  Initial Portfolio Value : ${initial_portfolio_value:>12,.2f}")
    print(f"  Mean Final Value        : ${summary_stats['mean_final_value']:>12,.2f}")
    print(f"  Median Final Value      : ${summary_stats['median_final_value']:>12,.2f}")
    print(f"  Std Deviation           : ${summary_stats['std_final_value']:>12,.2f}")
    print(f"  Best Case               : ${summary_stats['max_final_value']:>12,.2f}")
    print(f"  Worst Case              : ${summary_stats['min_final_value']:>12,.2f}")
    print(f"  Mean Return             : {summary_stats['mean_return_pct']:>11.2f}%")
    print(f"  Distribution Skewness   : {summary_stats['skewness']:>12.4f}")
    print(f"  Distribution Kurtosis   : {summary_stats['kurtosis']:>12.4f}")
    print("-" * 55)
    for key, val in var_dict.items():
        cl = key.split("_")[1]
        print(f"  VaR  @ {cl}% Confidence : ${val:>12,.2f}")
        print(f"  CVaR @ {cl}% Confidence : ${cvar_dict['CVaR_' + cl]:>12,.2f}")
    print("=" * 55)

    return {
        "final_values"  : final_values,
        "all_paths"     : all_paths,
        "summary_stats" : summary_stats,
        "var"           : var_dict,
        "cvar"          : cvar_dict,
    }


# ── Helper functions ───────────────────────────────────────────────────────

def _skewness(arr: np.ndarray) -> float:
    """Calculate skewness manually (avoids scipy dependency)."""
    n   = len(arr)
    mu  = np.mean(arr)
    std = np.std(arr)
    return (np.sum((arr - mu) ** 3) / n) / (std ** 3)


def _kurtosis(arr: np.ndarray) -> float:
    """Calculate excess kurtosis manually (avoids scipy dependency)."""
    n   = len(arr)
    mu  = np.mean(arr)
    std = np.std(arr)
    return (np.sum((arr - mu) ** 4) / n) / (std ** 4) - 3


def _summarise_paths(
    all_paths: np.ndarray,
    initial_value: float,
    days: int,
) -> pd.DataFrame:
    """
    Summarise all simulation paths into daily percentile bands.
    This is the data format Tableau needs to draw the fan chart.
    """
    rows = []
    for day in range(days):
        daily_vals = all_paths[:, day]
        rows.append({
            "day"        : day + 1,
            "p5"         : float(np.percentile(daily_vals, 5)),
            "p25"        : float(np.percentile(daily_vals, 25)),
            "p50_median" : float(np.percentile(daily_vals, 50)),
            "p75"        : float(np.percentile(daily_vals, 75)),
            "p95"        : float(np.percentile(daily_vals, 95)),
            "mean"       : float(np.mean(daily_vals)),
            "initial_value" : initial_value,
        })
    return pd.DataFrame(rows)


def _plot_distribution(
    final_values: np.ndarray,
    initial_value: float,
    var_dict: dict,
    simulations: int,
) -> None:
    """Save a histogram of final portfolio value distribution."""
    os.makedirs("images", exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.hist(final_values, bins=100, color="#4A90D9", edgecolor="white", alpha=0.85)

    # Mark VaR lines
    colors = ["#E74C3C", "#E67E22"]
    for (key, val), color in zip(var_dict.items(), colors):
        cl = key.split("_")[1]
        ax.axvline(
            x=initial_value + val,
            color=color, linestyle="--", linewidth=1.8,
            label=f"VaR {cl}%: ${val:,.0f}",
        )

    ax.axvline(x=initial_value, color="#2ECC71", linestyle="-", linewidth=1.8, label="Initial Value")
    ax.axvline(x=np.mean(final_values), color="white", linestyle=":", linewidth=1.5, label=f"Mean: ${np.mean(final_values):,.0f}")

    ax.set_title(f"Monte Carlo Simulation — Final Portfolio Value Distribution\n({simulations:,} simulations | 1-Year Forecast)", fontsize=14, pad=15)
    ax.set_xlabel("Portfolio Value ($)", fontsize=11)
    ax.set_ylabel("Frequency", fontsize=11)
    ax.legend(fontsize=10)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x/1000:.0f}K"))

    plt.tight_layout()
    path = "images/monte_carlo_distribution.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[AlphaPulse] Distribution plot saved → {path}")


if __name__ == "__main__":
    # Quick self-test with synthetic data
    np.random.seed(42)
    n_assets = 10
    fake_returns = pd.DataFrame(
        np.random.normal(0.0003, 0.015, (500, n_assets)),
        columns=[f"ASSET_{i}" for i in range(n_assets)],
    )
    results = monte_carlo_simulation(fake_returns, simulations=10_000, days=252)
