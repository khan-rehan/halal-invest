"""Daily SPUS halal investment analysis pipeline.

Orchestrates: Fetch SPUS tickers -> Fetch research data -> Generate PDF -> Email report.

Usage:
    python -m halal_invest.pipeline.daily_screener
"""

import sys
import time
from datetime import datetime

from halal_invest.core.spus import get_spus_tickers
from halal_invest.core.fundamentals import get_fundamentals, get_historical_growth
from halal_invest.core.technicals import get_signals
from halal_invest.report.pdf_generator import generate_report
from halal_invest.report.emailer import send_report_email


def run_pipeline():
    """Run the full daily SPUS analysis pipeline."""
    start_time = time.time()
    print(f"=== SPUS Halal Investment Report ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Step 1: Get SPUS tickers
    print("[1/4] Fetching SPUS ETF holdings...")
    tickers = get_spus_tickers()
    if not tickers:
        print("ERROR: Could not fetch SPUS tickers. Aborting.")
        sys.exit(1)
    print(f"  Found {len(tickers)} stocks")

    # Step 2: Fetch research data for all stocks
    print(f"\n[2/4] Fetching research data for {len(tickers)} stocks...")
    full_results = []

    for i, ticker in enumerate(tickers, 1):
        if i % 20 == 0 or i == len(tickers):
            print(f"  Progress: {i}/{len(tickers)}")

        try:
            fundamentals = get_fundamentals(ticker)
            signals = get_signals(ticker, period="6mo")
            historical_growth = get_historical_growth(ticker)

            full_results.append({
                "ticker": ticker,
                "fundamentals": fundamentals or {},
                "signals": signals or {},
                "historical_growth": historical_growth or {},
            })
        except Exception as e:
            print(f"  Warning: Error getting data for {ticker}: {e}")
            full_results.append({
                "ticker": ticker,
                "fundamentals": {},
                "signals": {},
                "historical_growth": {},
            })

        if i % 10 == 0:
            time.sleep(0.5)

    # Step 3: Generate PDF
    print(f"\n[3/4] Generating PDF report...")
    try:
        pdf_path = generate_report(full_results)
        print(f"  PDF saved to: {pdf_path}")
    except Exception as e:
        print(f"ERROR: Failed to generate PDF: {e}")
        sys.exit(1)

    # Step 4: Send email
    print(f"\n[4/4] Sending email report...")
    success = send_report_email(
        pdf_path=pdf_path,
        total_stocks=len(tickers),
    )

    elapsed = time.time() - start_time
    print(f"\n=== Pipeline Complete ===")
    print(f"Duration: {elapsed:.0f} seconds")
    print(f"Stocks analyzed: {len(tickers)}")
    print(f"PDF: {pdf_path}")
    print(f"Email: {'Sent' if success else 'FAILED'}")

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    run_pipeline()
