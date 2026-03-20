"""
var_model.py - AlphaPulse Investment Risk Monitor
Calculates Value at Risk (VaR) and Conditional VaR (CVaR / Expected Shortfall)
using three industry-standard methods:
  1. Historical Simulation  — non-parametric, uses actual return distribution
  2. Parametric (Variance-Covariance) — assumes normality, fast
  3. Monte Carlo VaR        — derived from simulation results

Exports a Tableau-ready CSV with per-asset and portfolio-level risk metrics.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

CONFIDENCE_LEVELS = [0.90, 0.95, 0.99]
PORTFOLIO_VALUE   = 100_000.0
EXPORT_PATH       = "data/var_risk_metrics.csv"


def calculate_var(
    returns: pd.DataFrame,
    portfolio_value: float = PORTFOLIO_VALUE,
    confidence_levels: list = CONFIDENCE_LEVELS,
    method: str = "historical",
    export_csv: bool = True,
    export_path: str = EXPORT_PATH,
    plot: bool = True,
) -> dict:
    """
    Calculate Value at Risk (VaR) and CVaR for the portfolio.

    Args:
        returns           : DataFrame of daily returns (dates × tickers).
        portfolio_value   : Portfolio size in dollars (default $100,000).
        confidence_levels : List of confidence levels, e.g. [0.95, 0.99].
        method            : 'historical', 'parametric', or 'both'.
        export_csv        : Save Tableau-ready results to CSV.
        export_path       : Output path for the CSV.
        plot              : Save a VaR visualisation.

    Returns:
        Dictionary with VaR and CVaR values keyed by method and confidence level.
    """
    print(f"[AlphaPulse] Calculating VaR | Method: {method} | Portfolio: ${portfolio_value:,.0f}")

    # Equal-weight portfolio returns
    weights          = np.ones(len(returns.columns)) / len(returns.columns)
    portfolio_returns = returns.dot(weights)

    results = {}

    # ── Method 1: Historical Simulation ──────────────────────────────────
    if method in ("historical", "both"):
        hist = _historical_var(portfolio_returns, portfolio_value, confidence_levels)
        results["historical"] = hist
        _print_var_table("Historical Simulation", hist, portfolio_value, confidence_levels)

    # ── Method 2: Parametric (Variance-Covariance) ────────────────────────
    if method in ("parametric", "both"):
        para = _parametric_var(portfolio_returns, portfolio_value, confidence_levels)
        results["parametric"] = para
        _print_var_table("Parametric (Normal)", para, portfolio_value, confidence_levels)

    # ── Per-asset VaR (Historical, 95%) ───────────────────────────────────
    per_asset = _per_asset_var(returns, portfolio_value, cl=0.95)
    results["per_asset_var_95"] = per_asset

    # ── Additional risk metrics ────────────────────────────────────────────
    risk_metrics = _compute_risk_metrics(portfolio_returns, portfolio_value)
    results["risk_metrics"] = risk_metrics

    # ── Export CSV for Tableau ─────────────────────────────────────────────
    if export_csv:
        _export_for_tableau(results, returns, portfolio_value, confidence_levels, export_path)

    # ── Plot ───────────────────────────────────────────────────────────────
    if plot:
        _plot_var(portfolio_returns, portfolio_value, results, confidence_levels)

    return results


# ── VaR Method Implementations ─────────────────────────────────────────────

def _historical_var(
    portfolio_returns: pd.Series,
    portfolio_value: float,
    confidence_levels: list,
) -> dict:
    """Non-parametric VaR: sort actual returns and read off the tail."""
    output = {}
    sorted_returns = np.sort(portfolio_returns.dropna().values)

    for cl in confidence_levels:
        idx      = int(np.floor((1 - cl) * len(sorted_returns)))
        var_ret  = sorted_returns[idx]
        var_usd  = var_ret * portfolio_value          # negative = loss
        # CVaR = mean of all returns worse than VaR threshold
        cvar_ret = sorted_returns[:idx + 1].mean()
        cvar_usd = cvar_ret * portfolio_value

        output[cl] = {
            "var_return"  : float(var_ret),
            "var_usd"     : float(var_usd),
            "cvar_return" : float(cvar_ret),
            "cvar_usd"    : float(cvar_usd),
        }
    return output


def _parametric_var(
    portfolio_returns: pd.Series,
    portfolio_value: float,
    confidence_levels: list,
) -> dict:
    """
    Parametric (Variance-Covariance) VaR.
    Assumes returns are normally distributed.
    """
    from scipy.stats import norm  # optional import — only needed here

    mu    = portfolio_returns.mean()
    sigma = portfolio_returns.std()
    output = {}

    for cl in confidence_levels:
        z_score  = norm.ppf(1 - cl)
        var_ret  = mu + z_score * sigma
        var_usd  = var_ret * portfolio_value

        # CVaR for normal distribution: mu - sigma * phi(z) / (1 - cl)
        cvar_ret = mu - sigma * norm.pdf(z_score) / (1 - cl)
        cvar_usd = cvar_ret * portfolio_value

        output[cl] = {
            "var_return"  : float(var_ret),
            "var_usd"     : float(var_usd),
            "cvar_return" : float(cvar_ret),
            "cvar_usd"    : float(cvar_usd),
            "z_score"     : float(z_score),
            "mu"          : float(mu),
            "sigma"       : float(sigma),
        }
    return output


def _per_asset_var(
    returns: pd.DataFrame,
    portfolio_value: float,
    cl: float = 0.95,
) -> pd.DataFrame:
    """Calculate individual VaR for each stock in the portfolio."""
    per_asset_value = portfolio_value / len(returns.columns)
    rows = []

    for ticker in returns.columns:
        r           = returns[ticker].dropna()
        sorted_r    = np.sort(r.values)
        idx         = int(np.floor((1 - cl) * len(sorted_r)))
        var_ret     = sorted_r[idx]
        var_usd     = var_ret * per_asset_value
        cvar_ret    = sorted_r[:idx + 1].mean()
        cvar_usd    = cvar_ret * per_asset_value
        ann_vol     = r.std() * np.sqrt(252)
        ann_return  = r.mean() * 252

        rows.append({
            "ticker"           : ticker,
            "allocated_value"  : per_asset_value,
            "var_return_95"    : round(var_ret, 6),
            "var_usd_95"       : round(var_usd, 2),
            "cvar_return_95"   : round(cvar_ret, 6),
            "cvar_usd_95"      : round(cvar_usd, 2),
            "annualised_vol"   : round(ann_vol, 6),
            "annualised_return": round(ann_return, 6),
            "sharpe_ratio"     : round(ann_return / ann_vol if ann_vol != 0 else 0, 4),
        })

    return pd.DataFrame(rows)


def _compute_risk_metrics(
    portfolio_returns: pd.Series,
    portfolio_value: float,
) -> dict:
    """Compute supplementary risk metrics for the Executive Summary tab."""
    cumulative   = (1 + portfolio_returns).cumprod()
    rolling_max  = cumulative.cummax()
    drawdown     = (cumulative - rolling_max) / rolling_max
    max_drawdown = float(drawdown.min())

    ann_return   = portfolio_returns.mean() * 252
    ann_vol      = portfolio_returns.std() * np.sqrt(252)
    sharpe       = ann_return / ann_vol if ann_vol != 0 else 0

    # Sortino ratio (downside deviation only)
    downside = portfolio_returns[portfolio_returns < 0]
    downside_dev = downside.std() * np.sqrt(252)
    sortino  = ann_return / downside_dev if downside_dev != 0 else 0

    return {
        "annualised_return"   : round(ann_return, 6),
        "annualised_volatility": round(ann_vol, 6),
        "sharpe_ratio"        : round(sharpe, 4),
        "sortino_ratio"       : round(sortino, 4),
        "max_drawdown"        : round(max_drawdown, 6),
        "max_drawdown_usd"    : round(max_drawdown * portfolio_value, 2),
        "best_day_return"     : round(float(portfolio_returns.max()), 6),
        "worst_day_return"    : round(float(portfolio_returns.min()), 6),
        "positive_days_pct"   : round(float((portfolio_returns > 0).mean() * 100), 2),
    }


# ── Tableau Export ─────────────────────────────────────────────────────────

def _export_for_tableau(
    results: dict,
    returns: pd.DataFrame,
    portfolio_value: float,
    confidence_levels: list,
    export_path: str,
) -> None:
    """
    Build three Tableau-ready CSVs:
      1. var_risk_metrics.csv          — Portfolio VaR summary (all methods & CL)
      2. var_per_asset_metrics.csv     — Individual stock risk breakdown
      3. var_executive_summary.csv     — KPIs for the Executive Summary tab
    """
    os.makedirs("data", exist_ok=True)

    # ── 1. Portfolio VaR summary ──────────────────────────────────────────
    rows = []
    for method_key in ("historical", "parametric"):
        if method_key not in results:
            continue
        method_data = results[method_key]
        for cl in confidence_levels:
            if cl not in method_data:
                continue
            d = method_data[cl]
            rows.append({
                "method"            : method_key.capitalize(),
                "confidence_level"  : f"{int(cl * 100)}%",
                "var_return"        : d["var_return"],
                "var_usd"           : d["var_usd"],
                "cvar_return"       : d["cvar_return"],
                "cvar_usd"          : d["cvar_usd"],
                "portfolio_value"   : portfolio_value,
            })

    summary_df = pd.DataFrame(rows)
    summary_df.to_csv(export_path, index=False)
    print(f"[AlphaPulse] Portfolio VaR metrics saved → {export_path}")

    # ── 2. Per-asset breakdown ────────────────────────────────────────────
    if "per_asset_var_95" in results and isinstance(results["per_asset_var_95"], pd.DataFrame):
        asset_path = export_path.replace(".csv", "_per_asset.csv")
        results["per_asset_var_95"].to_csv(asset_path, index=False)
        print(f"[AlphaPulse] Per-asset VaR saved → {asset_path}")

    # ── 3. Executive Summary KPIs ─────────────────────────────────────────
    if "risk_metrics" in results and "historical" in results:
        hist_95 = results["historical"].get(0.95, {})
        exec_data = {
            **results["risk_metrics"],
            "current_var_95_usd"  : hist_95.get("var_usd", "N/A"),
            "current_cvar_95_usd" : hist_95.get("cvar_usd", "N/A"),
            "portfolio_value"     : portfolio_value,
        }
        exec_df   = pd.DataFrame([exec_data])
        exec_path = export_path.replace(".csv", "_executive_summary.csv")
        exec_df.to_csv(exec_path, index=False)
        print(f"[AlphaPulse] Executive Summary KPIs saved → {exec_path}")


# ── Visualisation ──────────────────────────────────────────────────────────

def _plot_var(
    portfolio_returns: pd.Series,
    portfolio_value: float,
    results: dict,
    confidence_levels: list,
) -> None:
    """Plot return distribution with VaR/CVaR lines."""
    os.makedirs("images", exist_ok=True)

    dollar_returns = portfolio_returns * portfolio_value
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.hist(dollar_returns, bins=80, color="#4A90D9", edgecolor="white", alpha=0.8, label="Daily P&L")

    colors = ["#E74C3C", "#E67E22", "#9B59B6"]
    if "historical" in results:
        for (cl, data), color in zip(results["historical"].items(), colors):
            ax.axvline(data["var_usd"], color=color, linestyle="--", linewidth=2,
                       label=f"VaR {int(cl*100)}% (Hist): ${data['var_usd']:,.0f}")
            ax.axvline(data["cvar_usd"], color=color, linestyle=":", linewidth=1.5,
                       label=f"CVaR {int(cl*100)}%: ${data['cvar_usd']:,.0f}")

    ax.axvline(0, color="white", linewidth=1, alpha=0.5)
    ax.set_title("Daily Portfolio P&L Distribution with VaR / CVaR", fontsize=14, pad=15)
    ax.set_xlabel("Daily Profit / Loss ($)", fontsize=11)
    ax.set_ylabel("Frequency", fontsize=11)
    ax.legend(fontsize=9, loc="upper left")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    plt.tight_layout()

    path = "images/var_distribution.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[AlphaPulse] VaR distribution plot saved → {path}")


def _print_var_table(
    method_name: str,
    data: dict,
    portfolio_value: float,
    confidence_levels: list,
) -> None:
    print(f"\n  ── {method_name} ──")
    print(f"  {'CL':>5} | {'VaR Return':>12} | {'VaR ($)':>12} | {'CVaR ($)':>12}")
    print(f"  {'-'*5}-+-{'-'*12}-+-{'-'*12}-+-{'-'*12}")
    for cl in confidence_levels:
        if cl in data:
            d = data[cl]
            print(f"  {int(cl*100):>4}% | {d['var_return']:>12.4%} | ${d['var_usd']:>11,.2f} | ${d['cvar_usd']:>11,.2f}")


if __name__ == "__main__":
    # Quick self-test with synthetic data
    np.random.seed(42)
    n_assets = 10
    fake_returns = pd.DataFrame(
        np.random.normal(0.0003, 0.015, (500, n_assets)),
        columns=[f"ASSET_{i}" for i in range(n_assets)],
    )
    results = calculate_var(fake_returns, method="both")
    print("\nDone. Check data/ and images/ folders.")
