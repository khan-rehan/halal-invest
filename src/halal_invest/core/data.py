"""
yfinance wrapper module for fetching stock market data.

Provides functions to retrieve stock info, financial statements,
price history, and current prices via the yfinance library.
"""

import pandas as pd
import yfinance as yf


def get_stock_info(ticker: str) -> dict:
    """Fetch stock info for the given ticker.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").

    Returns:
        Dictionary of stock information from yfinance, or an empty dict
        if the request fails.
    """
    try:
        stock = yf.Ticker(ticker)
        return stock.info
    except Exception as e:
        print(f"Error fetching stock info for {ticker}: {e}")
        return {}


def get_financial_data(ticker: str) -> dict:
    """Fetch financial statements for the given ticker.

    Retrieves the balance sheet, income statement, and cash flow statement.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").

    Returns:
        Dictionary with keys "balance_sheet", "income_statement", and
        "cash_flow", each containing a pandas DataFrame. Returns empty
        DataFrames on failure.
    """
    try:
        stock = yf.Ticker(ticker)
        return {
            "balance_sheet": stock.balance_sheet,
            "income_statement": stock.income_stmt,
            "cash_flow": stock.cashflow,
        }
    except Exception as e:
        print(f"Error fetching financial data for {ticker}: {e}")
        return {
            "balance_sheet": pd.DataFrame(),
            "income_statement": pd.DataFrame(),
            "cash_flow": pd.DataFrame(),
        }


def get_price_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Fetch historical OHLCV price data for the given ticker.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").
        period: Time period to retrieve (e.g. "1d", "5d", "1mo", "3mo",
                "6mo", "1y", "2y", "5y", "10y", "ytd", "max").
                Defaults to "1y".

    Returns:
        DataFrame with Open, High, Low, Close, Volume columns, or an
        empty DataFrame on failure.
    """
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period=period)
        return history
    except Exception as e:
        print(f"Error fetching price history for {ticker}: {e}")
        return pd.DataFrame()


def get_current_price(ticker: str) -> float | None:
    """Fetch the current (or last closing) price for the given ticker.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").

    Returns:
        The current price as a float, or None if unavailable.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        # Try currentPrice first, fall back to regularMarketPreviousClose
        price = info.get("currentPrice") or info.get("regularMarketPreviousClose")
        return float(price) if price is not None else None
    except Exception as e:
        print(f"Error fetching current price for {ticker}: {e}")
        return None
