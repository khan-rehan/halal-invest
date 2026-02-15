"""Portfolio database operations."""

import sqlite3
from datetime import date

from halal_invest.db.database import get_connection


def add_transaction(
    ticker: str,
    action: str,
    shares: float,
    price: float,
    txn_date: str | None = None,
) -> None:
    """Insert a buy or sell transaction.

    Args:
        ticker: Stock ticker symbol.
        action: Either 'buy' or 'sell'.
        shares: Number of shares.
        price: Price per share.
        txn_date: Transaction date as YYYY-MM-DD string. Defaults to today.

    Raises:
        ValueError: If selling more shares than currently held.
    """
    ticker = ticker.upper()
    txn_date = txn_date or date.today().isoformat()

    if action == "sell":
        holdings = get_holdings()
        held = 0.0
        for h in holdings:
            if h["ticker"] == ticker:
                held = h["shares"]
                break
        if shares > held:
            raise ValueError(
                f"Cannot sell {shares} shares of {ticker}. "
                f"Only {held} shares held."
            )

    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO transactions (ticker, action, shares, price, date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ticker, action, shares, price, txn_date),
        )
        conn.commit()
    finally:
        conn.close()


def get_holdings() -> list[dict]:
    """Calculate current holdings from transactions.

    Returns:
        List of dicts with keys: ticker, shares, avg_cost, total_invested.
        Only tickers with remaining shares > 0 are included.
        avg_cost is the weighted average cost of all buy transactions.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT ticker, action, shares, price FROM transactions ORDER BY date"
        ).fetchall()
    finally:
        conn.close()

    # Accumulate per-ticker data
    tickers: dict[str, dict] = {}
    for row in rows:
        ticker = row["ticker"]
        if ticker not in tickers:
            tickers[ticker] = {
                "bought_shares": 0.0,
                "bought_cost": 0.0,
                "sold_shares": 0.0,
            }
        if row["action"] == "buy":
            tickers[ticker]["bought_shares"] += row["shares"]
            tickers[ticker]["bought_cost"] += row["shares"] * row["price"]
        elif row["action"] == "sell":
            tickers[ticker]["sold_shares"] += row["shares"]

    holdings = []
    for ticker, data in tickers.items():
        remaining = data["bought_shares"] - data["sold_shares"]
        if remaining > 0:
            avg_cost = (
                data["bought_cost"] / data["bought_shares"]
                if data["bought_shares"] > 0
                else 0.0
            )
            holdings.append(
                {
                    "ticker": ticker,
                    "shares": remaining,
                    "avg_cost": avg_cost,
                    "total_invested": remaining * avg_cost,
                }
            )
    return holdings


def get_transactions(ticker: str | None = None) -> list[dict]:
    """Fetch all transactions, optionally filtered by ticker.

    Args:
        ticker: If provided, only return transactions for this ticker.

    Returns:
        List of transaction dicts ordered by date descending.
    """
    conn = get_connection()
    try:
        if ticker:
            rows = conn.execute(
                "SELECT * FROM transactions WHERE ticker = ? ORDER BY date DESC",
                (ticker.upper(),),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM transactions ORDER BY date DESC"
            ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_portfolio_summary() -> dict:
    """Get a summary of the portfolio.

    Returns:
        Dict with keys: holdings, total_invested, total_holdings.
    """
    holdings = get_holdings()
    total_invested = sum(h["total_invested"] for h in holdings)
    return {
        "holdings": holdings,
        "total_invested": total_invested,
        "total_holdings": len(holdings),
    }


def log_purification(
    ticker: str, impure_pct: float, dividend_amount: float
) -> float:
    """Log a purification calculation.

    Args:
        ticker: Stock ticker symbol.
        impure_pct: Percentage of impure income (0-100).
        dividend_amount: Total dividend amount received.

    Returns:
        The calculated purification amount.
    """
    ticker = ticker.upper()
    purification_amount = dividend_amount * (impure_pct / 100)
    txn_date = date.today().isoformat()

    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO purification_log
                (ticker, impure_percentage, dividend_amount, purification_amount, date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ticker, impure_pct, dividend_amount, purification_amount, txn_date),
        )
        conn.commit()
    finally:
        conn.close()

    return purification_amount


def get_purification_log() -> list[dict]:
    """Fetch all purification records.

    Returns:
        List of purification record dicts ordered by date descending.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM purification_log ORDER BY date DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
