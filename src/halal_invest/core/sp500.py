"""
S&P 500 company list retrieval module.

Scrapes the current S&P 500 constituents from Wikipedia and returns
a cleaned list of ticker symbols compatible with yfinance.
"""

from io import StringIO
from urllib.request import Request, urlopen

import pandas as pd


SP500_WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; HalalInvestBot/1.0; "
        "+https://github.com/khan-rehan/halal-invest)"
    ),
    "Accept": "text/html",
}


def get_sp500_tickers() -> list[str]:
    """Fetch the current list of S&P 500 ticker symbols.

    Scrapes the S&P 500 company list from Wikipedia and cleans the
    ticker symbols for yfinance compatibility (e.g. BRK.B -> BRK-B).

    Returns:
        Sorted list of ticker symbol strings. Returns an empty list
        if the Wikipedia scrape fails.
    """
    try:
        req = Request(SP500_WIKI_URL, headers=_HEADERS)
        with urlopen(req) as resp:
            html = resp.read().decode("utf-8")
        tables = pd.read_html(StringIO(html))
        # The first table on the page contains the current constituents
        df = tables[0]
        tickers = df["Symbol"].tolist()
        # Clean tickers: replace "." with "-" for yfinance compatibility
        tickers = [ticker.replace(".", "-") for ticker in tickers]
        return sorted(tickers)
    except Exception as e:
        print(f"Warning: Failed to fetch S&P 500 tickers from Wikipedia: {e}")
        return []
