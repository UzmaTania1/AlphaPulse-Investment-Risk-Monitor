# 📈 AlphaPulse — Investment Risk & Volatility Monitor

> **Zaalima Development | Data Analytics Division — Project 2: Financial Analytics**
> Product Brand Name: **AlphaPulse** | Sprint: Q4 2025

AlphaPulse is an end-to-end financial analytics pipeline that monitors stock market behaviour, quantifies portfolio risk exposure, and delivers executive-grade insights through an interactive Tableau dashboard.

The system ingests live market data via `yfinance`, computes industry-standard risk metrics using NumPy, and presents results through a dynamic Tableau dashboard with What-If scenario analysis — enabling portfolio managers to make data-driven investment decisions.

---

## 🚀 Project Overview

Financial markets are highly volatile, and investment firms must constantly monitor portfolio performance and risk exposure. AlphaPulse delivers a structured analytics pipeline that:

- Fetches historical data for **10 stocks across diverse sectors + S&P 500 benchmark** via `yfinance`
- Calculates daily log returns, rolling volatility, and cross-asset correlations
- Runs a **10,000-path Monte Carlo simulation** to forecast 1-year portfolio performance
- Computes **Value at Risk (VaR) and CVaR** using both Historical and Parametric methods
- Exports Tableau-ready CSVs and publishes an interactive executive dashboard

---

## 🧠 Key Analytics Features

### 📊 Stock Price Trend Analysis
Visualises how stock prices evolve over time for all 11 assets (10 stocks + S&P 500 index). Helps identify long-term performance trends and sector rotation patterns.

### 📉 Daily Log Returns
Calculates percentage change in price day-over-day for each asset. Forms the foundation for all downstream volatility and risk calculations.

### 📊 Rolling Volatility (30-Day)
Computes the 30-day moving standard deviation of daily returns — a key indicator of market uncertainty. Periods of elevated rolling volatility signal increased portfolio risk.

### 🔥 Correlation Heatmap
Dynamic matrix showing how all 11 assets move relative to one another. Positive correlation = assets move together. Negative = opposite directions. Used to assess diversification quality.

### 🎲 Monte Carlo Simulation (10,000 Runs)
Runs **10,000 stochastic simulations** using a multivariate normal distribution fitted to historical return statistics. Preserves cross-asset correlations via Cholesky decomposition. Forecasts portfolio value 1 year (252 trading days) into the future, producing a probability-based risk profile including best/worst/median outcomes.

### ⚠️ Value at Risk (VaR) & CVaR
Calculates VaR at 90%, 95%, and 99% confidence levels using both:
- **Historical Simulation** — non-parametric, uses actual return distribution
- **Parametric (Variance-Covariance)** — assumes normality, fast to compute

Also calculates **Conditional VaR (CVaR / Expected Shortfall)** — the average loss beyond the VaR threshold — which is a more conservative and complete risk measure.

---

## 🏗️ System Architecture (ETL Pipeline)

```
yfinance API
     │
     ▼
[Extract] data_loader.py
  • 10 diverse stocks + ^GSPC (S&P 500)
  • Auto-adjust for stock splits & dividends
  • Resilient retry logic for API rate limits
  • Saves → data/raw_market_data.csv
     │
     ▼
[Transform] src/ modules
  ├── returns_calculator.py  → Daily log returns
  ├── volatility.py          → 30-day rolling std dev
  ├── correlation.py         → Correlation matrix & heatmap
  ├── monte_carlo.py         → 10,000-path simulation
  └── var_model.py           → VaR, CVaR, risk metrics
  • Saves → data/processed_market_data.csv
            data/monte_carlo_results.csv
            data/var_risk_metrics.csv
            data/var_risk_metrics_per_asset.csv
            data/var_risk_metrics_executive_summary.csv
     │
     ▼
[Load] Tableau Dashboard
  • Connected to processed CSV outputs
  • Interactive What-If parameters
  • Executive Summary tab (VaR + Max Drawdown)
  • Published → Tableau Public
```

---

## 🛠️ Technology Stack

| Layer | Tool | Purpose |
|---|---|---|
| Data Source | `yfinance` | Live market data via API |
| Processing | `Python 3.10+` | Pipeline orchestration |
| Computation | `NumPy` | Matrix ops, simulation, VaR math |
| Manipulation | `Pandas` | DataFrames, cleaning, export |
| Visualisation (dev) | `Matplotlib / Seaborn` | Exploratory plots |
| Visualisation (prod) | **Tableau** | Executive dashboard |
| Version Control | `GitHub` | Code & documentation |

---

## 📂 Project Structure

```
AlphaPulse-Investment-Risk-Monitor/
│
├── data/
│   ├── raw_market_data.csv                        ← Fetched from yfinance
│   ├── processed_market_data.csv                  ← Cleaned returns
│   ├── monte_carlo_results.csv                    ← 10,000 final values
│   ├── monte_carlo_results_daily_percentiles.csv  ← Daily fan chart data
│   ├── var_risk_metrics.csv                       ← Portfolio VaR summary
│   ├── var_risk_metrics_per_asset.csv             ← Per-stock risk breakdown
│   └── var_risk_metrics_executive_summary.csv     ← KPIs for exec tab
│
├── src/
│   ├── data_loader.py         ← yfinance fetch + error handling
│   ├── returns_calculator.py  ← Daily log return computation
│   ├── volatility.py          ← Rolling 30-day volatility
│   ├── correlation.py         ← Correlation matrix + heatmap export
│   ├── monte_carlo.py         ← 10,000-run stochastic simulation
│   └── var_model.py           ← VaR, CVaR, Sharpe, Max Drawdown
│
├── notebooks/
│   └── AlphaPulse_Analysis.ipynb   ← Full exploratory walkthrough
│
├── dashboard/
│   └── AlphaPulse_Dashboard.twbx   ← Tableau packaged workbook
│
├── images/
│   ├── dashboard_preview.png
│   ├── monte_carlo_distribution.png
│   ├── var_distribution.png
│   └── correlation_heatmap.png
│
├── main.py              ← Full pipeline runner (all modules)
├── run_pipeline.py      ← Simplified single-command runner
├── requirements.txt
└── README.md
```

---

## 📦 Portfolio Composition

| # | Ticker | Company | Sector |
|---|--------|---------|--------|
| 1 | AAPL | Apple Inc. | Technology |
| 2 | MSFT | Microsoft Corp. | Technology |
| 3 | JPM | JPMorgan Chase | Financials |
| 4 | JNJ | Johnson & Johnson | Healthcare |
| 5 | XOM | ExxonMobil | Energy |
| 6 | AMZN | Amazon.com | Consumer Discretionary |
| 7 | PG | Procter & Gamble | Consumer Staples |
| 8 | CAT | Caterpillar Inc. | Industrials |
| 9 | NEE | NextEra Energy | Utilities |
| 10 | BHP | BHP Group | Materials |
| + | ^GSPC | S&P 500 Index | Benchmark |

---

## ⚙️ Installation & Setup

**1. Clone the repository**
```bash
git clone https://github.com/UzmaTania1/AlphaPulse-Investment-Risk-Monitor.git
cd AlphaPulse-Investment-Risk-Monitor
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Run the full pipeline**
```bash
python run_pipeline.py
```

This will fetch data, compute all metrics, export CSVs to `data/`, and save plots to `images/`.

**4. Automate (optional — scheduled refresh)**

On Linux/macOS, add to crontab to run every Sunday night at 11 PM:
```bash
crontab -e
# Add this line:
0 23 * * 0 /usr/bin/python3 /path/to/AlphaPulse/run_pipeline.py >> /path/to/pipeline.log 2>&1
```

On Windows, use Task Scheduler to run `run_pipeline.py` on a weekly trigger.

---

## 📊 Tableau Dashboard

### Connecting Tableau to the Data
1. Open Tableau Desktop
2. Connect to `data/var_risk_metrics.csv` (and other processed CSVs)
3. Use **Data → Refresh** to update after running the pipeline

### Dashboard Sheets

| Sheet | Data Source | Description |
|---|---|---|
| Stock Price Trends | processed_market_data.csv | Price line chart, all 11 assets |
| Daily Returns | processed_market_data.csv | Return distribution per ticker |
| Rolling Volatility | processed_market_data.csv | 30-day std dev over time |
| Correlation Heatmap | processed_market_data.csv | Cross-asset correlation matrix |
| Monte Carlo Fan Chart | monte_carlo_results_daily_percentiles.csv | P5/P25/P50/P75/P95 bands |
| Monte Carlo Distribution | monte_carlo_results.csv | Histogram of final portfolio values |
| VaR Summary | var_risk_metrics.csv | VaR & CVaR by method and confidence level |
| Per-Asset Risk | var_risk_metrics_per_asset.csv | Individual stock VaR breakdown |
| **Executive Summary** | var_risk_metrics_executive_summary.csv | **Current VaR, Max Drawdown, Sharpe, Sortino** |

### What-If Parameters (Week 3 Requirement)
In Tableau, create a **Parameter** named `Sector Shock (%)` (range: -50% to +50%).
Use a calculated field to adjust returns for the relevant sector tickers and watch VaR and the Monte Carlo chart update dynamically.

---

## 🌐 Live Dashboard

View the interactive Tableau dashboard here:
[https://public.tableau.com/app/profile/shaik.uzmatania4925/viz/AlphaPulse-investment-Risk-Monitor1/AlphaPulseInvestmentRiskVolatilityMonitor](https://public.tableau.com/app/profile/shaik.uzmatania4925/viz/AlphaPulse-investment-Risk-Monitor1/AlphaPulseInvestmentRiskVolatilityMonitor)

---

## 📈 Project Outcomes

This project demonstrates practical, production-grade skills in:
- Live financial data ingestion with API resilience
- Quantitative risk modelling (VaR, CVaR, Monte Carlo, Sharpe, Sortino, Max Drawdown)
- End-to-end Python data pipelines with automated scheduling
- Executive-grade Tableau dashboard design with What-If interactivity
- Clean, modular code with professional GitHub documentation

---

## 🔮 Future Improvements

- Real-time streaming data via WebSocket or Kafka
- Portfolio optimisation (Efficient Frontier / Markowitz)
- GARCH model for volatility forecasting
- Stress testing against historical crisis scenarios (2008, COVID-19)
- Automated email alert when VaR breaches a set threshold
