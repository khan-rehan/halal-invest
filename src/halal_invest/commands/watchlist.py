"""Watchlist management commands."""

import typer
from typing import Optional

from halal_invest.db.watchlist import (
    add_to_watchlist,
    remove_from_watchlist,
    get_watchlist,
    set_target_prices,
    get_alerts,
)
from halal_invest.core.data import get_current_price
from halal_invest.core.screener import screen_stock
from halal_invest.display.tables import console, format_halal_status, format_currency

from rich.table import Table
from rich import box

app = typer.Typer()


@app.command("add")
def add(
    tickers: list[str] = typer.Argument(..., help="One or more ticker symbols to add"),
) -> None:
    """Add tickers to the watchlist."""
    for ticker in tickers:
        ticker_upper = ticker.upper()
        add_to_watchlist(ticker_upper)
        console.print(f"[green]Added[/green] [bold]{ticker_upper}[/bold] to watchlist.")
    console.print()


@app.command("remove")
def remove(
    ticker: str = typer.Argument(..., help="Ticker symbol to remove"),
) -> None:
    """Remove a ticker from the watchlist."""
    ticker_upper = ticker.upper()
    remove_from_watchlist(ticker_upper)
    console.print(
        f"\n[green]Removed[/green] [bold]{ticker_upper}[/bold] from watchlist.\n"
    )


@app.command("show")
def show() -> None:
    """Display the watchlist with current prices and halal status."""
    watchlist = get_watchlist()
    if not watchlist:
        console.print(
            "\n[yellow]Watchlist is empty.[/yellow] Use 'watchlist add' to add tickers.\n"
        )
        return

    table = Table(title="Watchlist", box=box.ROUNDED)
    table.add_column("Ticker", style="bold cyan")
    table.add_column("Current Price", justify="right")
    table.add_column("Halal Status", justify="center")
    table.add_column("Target Buy", justify="right")
    table.add_column("Target Sell", justify="right")
    table.add_column("Notes")

    for item in watchlist:
        ticker = item["ticker"]

        # Fetch current price
        price = get_current_price(ticker)
        price_str = format_currency(price) if price is not None else "[dim]N/A[/dim]"

        # Fetch halal status
        try:
            result = screen_stock(ticker)
            status = result.get("status", "UNKNOWN")
            status_str = format_halal_status(status)
        except Exception:
            status_str = "[dim]N/A[/dim]"

        # Target prices
        buy_target = (
            format_currency(item["target_buy_price"])
            if item["target_buy_price"] is not None
            else "[dim]--[/dim]"
        )
        sell_target = (
            format_currency(item["target_sell_price"])
            if item["target_sell_price"] is not None
            else "[dim]--[/dim]"
        )

        notes = item["notes"] or ""

        table.add_row(ticker, price_str, status_str, buy_target, sell_target, notes)

    console.print()
    console.print(table)
    console.print()


@app.command("set-target")
def set_target(
    ticker: str = typer.Argument(..., help="Ticker symbol"),
    buy: Optional[float] = typer.Option(
        None, "--buy", "-b", help="Target buy price"
    ),
    sell: Optional[float] = typer.Option(
        None, "--sell", "-s", help="Target sell price"
    ),
) -> None:
    """Set target buy/sell prices for a watchlist ticker."""
    ticker_upper = ticker.upper()
    if buy is None and sell is None:
        console.print(
            "\n[red]Error:[/red] Provide at least one of --buy or --sell.\n"
        )
        raise typer.Exit(code=1)

    set_target_prices(ticker_upper, buy_price=buy, sell_price=sell)

    parts = []
    if buy is not None:
        parts.append(f"buy={format_currency(buy)}")
    if sell is not None:
        parts.append(f"sell={format_currency(sell)}")

    console.print(
        f"\n[green]Updated[/green] targets for [bold]{ticker_upper}[/bold]: "
        f"{', '.join(parts)}\n"
    )


@app.command("alerts")
def alerts() -> None:
    """Check for triggered price alerts on watchlist items."""
    watchlist = get_watchlist()
    if not watchlist:
        console.print("\n[yellow]Watchlist is empty.[/yellow]\n")
        return

    # Fetch current prices for all watchlist tickers
    current_prices: dict[str, float] = {}
    for item in watchlist:
        ticker = item["ticker"]
        price = get_current_price(ticker)
        if price is not None:
            current_prices[ticker] = price

    triggered = get_alerts(current_prices)

    if not triggered:
        console.print("\n[green]No price alerts triggered.[/green]\n")
        return

    table = Table(title="Triggered Alerts", box=box.HEAVY_EDGE, border_style="yellow")
    table.add_column("Ticker", style="bold cyan")
    table.add_column("Alert", justify="center")
    table.add_column("Target Price", justify="right")
    table.add_column("Current Price", justify="right")

    for alert in triggered:
        alert_style = "green bold" if alert["alert_type"] == "BUY" else "red bold"
        alert_str = f"[{alert_style}]{alert['alert_type']}[/{alert_style}]"

        table.add_row(
            alert["ticker"],
            alert_str,
            format_currency(alert["target"]),
            format_currency(alert["current"]),
        )

    console.print()
    console.print(table)
    console.print()
