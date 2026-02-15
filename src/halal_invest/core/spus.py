"""
SPUS ETF holdings retrieval module.

Downloads the current holdings of the SP Funds S&P 500 Sharia Industry
Exclusions ETF (SPUS) from the provider's daily CSV file. These stocks
are pre-screened for Sharia compliance by professional analysts.
"""

import csv
import io
from urllib.request import Request, urlopen


SPUS_CSV_URL = (
    "https://www.sp-funds.com/wp-content/uploads/data/TidalFG_Holdings_SPUS.csv"
)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; HalalInvestBot/1.0; "
        "+https://github.com/khan-rehan/halal-invest)"
    ),
    "Accept": "text/csv",
}


def get_spus_tickers() -> list[str]:
    """Fetch the current list of SPUS ETF ticker symbols.

    Downloads the daily holdings CSV from SP Funds and extracts clean
    ticker symbols, filtering out cash positions and non-stock entries.

    Returns:
        Sorted list of ticker symbol strings. Returns an empty list
        if the download fails.
    """
    holdings = get_spus_holdings()
    return sorted(h["ticker"] for h in holdings)


def get_spus_holdings() -> list[dict]:
    """Fetch full SPUS ETF holdings data.

    Downloads the daily holdings CSV from SP Funds and returns parsed
    holding records with ticker, name, weight, shares, price, and
    market value.

    Returns:
        List of dicts with keys: ticker, name, weight, shares, price,
        market_value. Returns an empty list if the download fails.
    """
    try:
        req = Request(SPUS_CSV_URL, headers=_HEADERS)
        with urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
    except Exception as e:
        print(f"Warning: Failed to fetch SPUS holdings CSV: {e}")
        return []

    reader = csv.DictReader(io.StringIO(raw))
    holdings = []

    for row in reader:
        ticker = (row.get("StockTicker") or "").strip()

        # Skip empty tickers, cash positions, and non-alphabetic entries
        if not ticker or not ticker.isalpha():
            continue
        if ticker.upper() in ("CASH", "CASHANDOTHER", "CASH&OTHER"):
            continue

        name = (row.get("SecurityName") or "").strip()
        if "cash" in name.lower() and "other" in name.lower():
            continue

        def _parse_float(val):
            try:
                return float(val)
            except (TypeError, ValueError):
                return None

        holdings.append({
            "ticker": ticker,
            "name": name,
            "weight": _parse_float(row.get("Weightings")),
            "shares": _parse_float(row.get("Shares")),
            "price": _parse_float(row.get("Price")),
            "market_value": _parse_float(row.get("MarketValue")),
        })

    return holdings
