# Halal Invest

Automated halal stock screening tool for the S&P 500. Screens all ~500 stocks daily against AAOIFI Sharia compliance standards, scores them with a composite ranking system, and delivers a PDF report via email.

## What It Does

1. **Halal Screening** - Filters stocks through 5 compliance checks:
   - Business activity (excludes alcohol, tobacco, gambling, weapons, cannabis, financial services)
   - Debt ratio < 33% of market cap
   - Liquid assets ratio < 33% of market cap
   - Receivables ratio < 33% of market cap
   - Impure (interest) income < 5% of revenue

2. **Fundamental Analysis** - Fetches valuation (P/E, P/B, PEG), profitability (margins, ROE, ROA), growth, and financial health metrics

3. **Technical Analysis** - Computes RSI, MACD, SMA crossover, and Bollinger Band signals with an overall BUY/HOLD/SELL vote

4. **Composite Scoring** - Ranks every passing stock 0-100 based on:
   - Valuation (30%) | Profitability (25%) | Growth (20%) | Financial Health (15%) | Technical (10%)

5. **PDF Report** - Generates a multi-page report with:
   - Summary dashboard with pass/fail stats and sector breakdown
   - Glossary explaining every metric in plain English
   - Top 10 best stocks with a $1,000 investment allocation plan
   - All passing stocks in compact tables grouped by sector
   - Color-coded valuation tags (UNDERPRICED / FAIR VALUE / OVERPRICED)

6. **Email Delivery** - Sends the PDF via Resend API

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
# Screen individual stocks
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
# Runs all 500 stocks, generates PDF to ~/halal-invest-reports/
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

- Screens all S&P 500 stocks
- Generates the PDF report
- Emails it to the configured recipient
- Uploads the PDF as a workflow artifact (retained 30 days)

To trigger manually: **Actions** > **Daily Halal S&P 500 Screener** > **Run workflow**

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
    screener.py       # 5 halal compliance screens
    scoring.py        # Composite 0-100 scoring, valuation tags, investment allocation
    fundamentals.py   # Valuation, profitability, growth, health metrics
    technicals.py     # RSI, MACD, SMA crossover, Bollinger signals
    data.py           # yfinance data fetching wrapper
    sp500.py          # S&P 500 ticker list from Wikipedia
  report/
    pdf_generator.py  # Multi-page PDF with tables, glossary, Top 10
    emailer.py        # Resend API email delivery
  pipeline/
    daily_screener.py # Orchestrates the full daily run
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
