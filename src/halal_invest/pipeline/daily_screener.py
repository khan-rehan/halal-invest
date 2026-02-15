"""Daily S&P 500 halal screening pipeline.

Orchestrates: Fetch S&P 500 → Screen all → Compute research data → Generate PDF → Email report.

Usage:
    python -m halal_invest.pipeline.daily_screener
"""

import sys
import time
from datetime import datetime

from halal_invest.core.sp500 import get_sp500_tickers
from halal_invest.core.screener import screen_stock
from halal_invest.core.fundamentals import get_fundamentals
from halal_invest.core.technicals import get_signals
from halal_invest.report.pdf_generator import generate_report
from halal_invest.report.emailer import send_report_email


def run_pipeline():
    """Run the full daily screening pipeline."""
    start_time = time.time()
    print(f"=== Halal S&P 500 Daily Screener ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Step 1: Get S&P 500 tickers
    print("[1/5] Fetching S&P 500 ticker list...")
    tickers = get_sp500_tickers()
    if not tickers:
        print("ERROR: Could not fetch S&P 500 tickers. Aborting.")
        sys.exit(1)
    print(f"  Found {len(tickers)} tickers")

    # Step 2: Screen all tickers
    print(f"\n[2/5] Screening {len(tickers)} stocks for halal compliance...")
    all_results = []
    passed_results = []

    for i, ticker in enumerate(tickers, 1):
        if i % 50 == 0 or i == len(tickers):
            print(f"  Progress: {i}/{len(tickers)}")

        try:
            screen_result = screen_stock(ticker)
            all_results.append(screen_result)

            if screen_result.get("halal_status") in ("PASS", "DOUBTFUL"):
                passed_results.append(screen_result)
        except Exception as e:
            print(f"  Warning: Error screening {ticker}: {e}")

        # Small delay to avoid rate limiting
        if i % 10 == 0:
            time.sleep(0.5)

    total_screened = len(all_results)
    total_passed = len(passed_results)
    total_failed = total_screened - total_passed

    print(f"\n  Results: {total_passed} PASSED, {total_failed} FAILED out of {total_screened}")

    # Step 3: Get full research data for passing stocks
    print(f"\n[3/5] Fetching research data for {total_passed} passing stocks...")
    full_results = []

    for i, screen_result in enumerate(passed_results, 1):
        ticker = screen_result["ticker"]
        if i % 20 == 0 or i == len(passed_results):
            print(f"  Progress: {i}/{len(passed_results)}")

        try:
            fundamentals = get_fundamentals(ticker)
            signals = get_signals(ticker, period="6mo")

            full_results.append({
                "screening": screen_result,
                "fundamentals": fundamentals or {},
                "signals": signals or {},
            })
        except Exception as e:
            print(f"  Warning: Error getting data for {ticker}: {e}")
            full_results.append({
                "screening": screen_result,
                "fundamentals": {},
                "signals": {},
            })

        if i % 10 == 0:
            time.sleep(0.5)

    # Step 4: Generate PDF
    print(f"\n[4/5] Generating PDF report...")
    try:
        pdf_path = generate_report(full_results)
        print(f"  PDF saved to: {pdf_path}")
    except Exception as e:
        print(f"ERROR: Failed to generate PDF: {e}")
        sys.exit(1)

    # Step 5: Send email
    print(f"\n[5/5] Sending email report...")
    success = send_report_email(
        pdf_path=pdf_path,
        total_screened=total_screened,
        total_passed=total_passed,
    )

    elapsed = time.time() - start_time
    print(f"\n=== Pipeline Complete ===")
    print(f"Duration: {elapsed:.0f} seconds")
    print(f"Stocks screened: {total_screened}")
    print(f"Halal compliant: {total_passed}")
    print(f"PDF: {pdf_path}")
    print(f"Email: {'Sent' if success else 'FAILED'}")

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    run_pipeline()
