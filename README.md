# Halal Invest

Automated halal investment analysis tool using the **SPUS ETF** (SP Funds S&P 500 Sharia Industry Exclusions ETF). Fetches ~211 pre-screened Sharia-compliant stocks daily, scores them with a composite ranking system including historical growth analysis, and delivers a PDF report via email.

## What It Does

1. **SPUS ETF Holdings** - Fetches the current holdings of the SPUS ETF, which contains S&P 500 stocks pre-screened for Sharia compliance by professional analysts. No custom screening needed.

2. **Fundamental Analysis** - Fetches valuation (P/E, P/B, PEG), profitability (margins, ROE, ROA), growth, and financial health metrics

3. **Historical Growth** - Computes Compound Annual Growth Rate (CAGR) over 1-year, 3-year, 5-year, and 10-year periods to evaluate long-term performance

4. **Technical Analysis** - Computes RSI, MACD, SMA crossover, and Bollinger Band signals with an overall BUY/HOLD/SELL vote

5. **Composite Scoring** - Ranks every stock 0-100 based on:
   - Valuation (25%) | Profitability (20%) | Short-term Growth (15%) | Historical Growth (15%) | Financial Health (15%) | Technical (10%)

6. **PDF Report** - Generates a multi-page report with:
   - Summary dashboard with stock count, average score, and average 5Y CAGR
   - Glossary explaining every metric in plain English
   - Top 10 best stocks with a $1,000 investment allocation plan
   - All stocks in compact tables grouped by sector with 5Y and 10Y CAGR columns
   - Color-coded valuation tags (UNDERPRICED / FAIR VALUE / OVERPRICED)

7. **Email Delivery** - Sends the PDF via Resend API

## Setup

**Requirements:** Python 3.11+

```bash
# Clone and install
git clone https://github.com/khan-rehan/halal-invest.git
cd halal-invest
python -m venv .venv
source .venv/bin/activate
pip install .
```

## Usage

### CLI Commands

```bash
# Screen individual stocks (uses built-in halal screener)
halal-invest screen AAPL MSFT GOOGL

# Detailed screening breakdown
halal-invest screen AAPL --detailed

# Technical signals
halal-invest signals AAPL
halal-invest signals AAPL --period 6mo

# Portfolio management
halal-invest portfolio buy AAPL 10 150.00
halal-invest portfolio sell AAPL 5 175.00
halal-invest portfolio summary

# Watchlist
halal-invest watchlist add AAPL
halal-invest watchlist list
```

### Run Full Pipeline Locally

```bash
# Analyzes all SPUS holdings, generates PDF to ~/halal-invest-reports/
python -m halal_invest.pipeline.daily_screener
```

For email delivery, set these environment variables:
```bash
export RESEND_API_KEY="re_..."
export SENDER_EMAIL="reports@yourdomain.com"
export RECIPIENT_EMAIL="you@email.com"
```

## Automated Daily Reports

A GitHub Actions workflow runs every weekday at 9:00 AM EST:

1. Fetches current SPUS ETF holdings (~211 stocks)
2. Gathers fundamentals, technical signals, and historical growth for each stock
3. Generates and emails the PDF report
4. Uploads the PDF as a workflow artifact (retained 30 days)

To trigger manually: **Actions** > **Daily SPUS Halal Investment Report** > **Run workflow**

### Required GitHub Secrets

| Secret | Description |
|---|---|
| `RESEND_API_KEY` | API key from [resend.com](https://resend.com) |
| `SENDER_EMAIL` | Verified sender email address |
| `RECIPIENT_EMAIL` | Where to deliver the daily report |

## Project Structure

```
src/halal_invest/
  core/
    spus.py           # SPUS ETF holdings from SP Funds CSV
    scoring.py        # Composite 0-100 scoring, valuation tags, investment allocation
    fundamentals.py   # Valuation, profitability, growth, health metrics + CAGR
    technicals.py     # RSI, MACD, SMA crossover, Bollinger signals
    data.py           # yfinance data fetching wrapper
    sp500.py          # S&P 500 ticker list from Wikipedia
    screener.py       # Halal compliance screens (used by CLI commands)
  report/
    pdf_generator.py  # Multi-page PDF with tables, glossary, Top 10
    emailer.py        # Resend API email delivery
  pipeline/
    daily_screener.py # Orchestrates the full daily SPUS analysis
  commands/           # CLI command handlers
  db/                 # SQLite portfolio and watchlist tracking
tests/
  test_screener.py    # Halal screening tests (24 tests)
  test_fundamentals.py
  test_portfolio.py
```

## Tests

```bash
# Run all tests
python -m pytest tests/ -v
```

## Tech Stack

- **Data**: yfinance, pandas
- **Technical Analysis**: ta (Technical Analysis library)
- **PDF**: fpdf2
- **CLI**: typer + rich
- **Email**: Resend API
- **CI/CD**: GitHub Actions
- **Database**: SQLite (portfolio/watchlist)
