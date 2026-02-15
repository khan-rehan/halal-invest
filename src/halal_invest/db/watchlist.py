"""Watchlist database operations."""

from halal_invest.db.database import get_connection


def add_to_watchlist(ticker: str, notes: str | None = None) -> None:
    """Add a ticker to the watchlist.

    Uses INSERT OR IGNORE to handle duplicate tickers gracefully.

    Args:
        ticker: Stock ticker symbol.
        notes: Optional notes about the ticker.
    """
    ticker = ticker.upper()
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO watchlist (ticker, notes) VALUES (?, ?)",
            (ticker, notes),
        )
        conn.commit()
    finally:
        conn.close()


def remove_from_watchlist(ticker: str) -> None:
    """Remove a ticker from the watchlist.

    Args:
        ticker: Stock ticker symbol.
    """
    ticker = ticker.upper()
    conn = get_connection()
    try:
        conn.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker,))
        conn.commit()
    finally:
        conn.close()


def get_watchlist() -> list[dict]:
    """Fetch all watchlist entries.

    Returns:
        List of dicts with all watchlist columns.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM watchlist ORDER BY added_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def set_target_prices(
    ticker: str,
    buy_price: float | None = None,
    sell_price: float | None = None,
) -> None:
    """Update target buy/sell prices for a ticker in the watchlist.

    Only updates non-None values. If the ticker is not already in the
    watchlist, it is added first.

    Args:
        ticker: Stock ticker symbol.
        buy_price: Target price at which to buy (optional).
        sell_price: Target price at which to sell (optional).
    """
    ticker = ticker.upper()

    # Ensure the ticker is in the watchlist
    add_to_watchlist(ticker)

    conn = get_connection()
    try:
        if buy_price is not None:
            conn.execute(
                "UPDATE watchlist SET target_buy_price = ? WHERE ticker = ?",
                (buy_price, ticker),
            )
        if sell_price is not None:
            conn.execute(
                "UPDATE watchlist SET target_sell_price = ? WHERE ticker = ?",
                (sell_price, ticker),
            )
        conn.commit()
    finally:
        conn.close()


def get_alerts(current_prices: dict[str, float]) -> list[dict]:
    """Check watchlist items against current prices for triggered alerts.

    Args:
        current_prices: Mapping of ticker symbol to current price.

    Returns:
        List of alert dicts with keys: ticker, alert_type, target, current.
        alert_type is 'BUY' when current price <= target_buy_price,
        or 'SELL' when current price >= target_sell_price.
    """
    watchlist = get_watchlist()
    alerts = []

    for item in watchlist:
        ticker = item["ticker"]
        current = current_prices.get(ticker)
        if current is None:
            continue

        if (
            item["target_buy_price"] is not None
            and current <= item["target_buy_price"]
        ):
            alerts.append(
                {
                    "ticker": ticker,
                    "alert_type": "BUY",
                    "target": item["target_buy_price"],
                    "current": current,
                }
            )

        if (
            item["target_sell_price"] is not None
            and current >= item["target_sell_price"]
        ):
            alerts.append(
                {
                    "ticker": ticker,
                    "alert_type": "SELL",
                    "target": item["target_sell_price"],
                    "current": current,
                }
            )

    return alerts
