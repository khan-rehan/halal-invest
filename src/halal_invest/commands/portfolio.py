"""Portfolio tracking commands."""

import typer
from typing import Optional
from datetime import date

from halal_invest.db.portfolio import (
    add_transaction,
    get_holdings,
    get_transactions,
    get_portfolio_summary,
    log_purification,
    get_purification_log,
)
from halal_invest.core.data import get_current_price
from halal_invest.core.screener import screen_stock
from halal_invest.display.tables import console, format_currency, format_percentage

from rich.table import Table
from rich.panel import Panel
from rich import box

app = typer.Typer()


@app.command("add")
def add(
    ticker: str = typer.Argument(..., help="Stock ticker symbol"),
    shares: float = typer.Argument(..., help="Number of shares"),
    price: float = typer.Argument(..., help="Price per share"),
    txn_date: Optional[str] = typer.Option(
        None, "--date", "-d", help="Transaction date (YYYY-MM-DD). Defaults to today."
    ),
) -> None:
    """Record a stock purchase."""
    ticker = ticker.upper()
    add_transaction(ticker, action="buy", shares=shares, price=price, txn_date=txn_date)
    console.print(
        f"\n[green]Added:[/green] Bought {shares} shares of "
        f"[bold]{ticker}[/bold] at {format_currency(price)}\n"
    )


@app.command("sell")
def sell(
    ticker: str = typer.Argument(..., help="Stock ticker symbol"),
    shares: float = typer.Argument(..., help="Number of shares to sell"),
    price: float = typer.Argument(..., help="Price per share"),
    txn_date: Optional[str] = typer.Option(
        None, "--date", "-d", help="Transaction date (YYYY-MM-DD). Defaults to today."
    ),
) -> None:
    """Record a stock sale."""
    ticker = ticker.upper()
    try:
        add_transaction(
            ticker, action="sell", shares=shares, price=price, txn_date=txn_date
        )
        console.print(
            f"\n[green]Recorded:[/green] Sold {shares} shares of "
            f"[bold]{ticker}[/bold] at {format_currency(price)}\n"
        )
    except ValueError as e:
        console.print(f"\n[red]Error:[/red] {e}\n")


@app.command("show")
def show() -> None:
    """Show current portfolio holdings with live prices and P&L."""
    holdings = get_holdings()
    if not holdings:
        console.print("\n[yellow]No holdings found.[/yellow] Use 'portfolio add' to record a purchase.\n")
        return

    table = Table(
        title="Portfolio Holdings",
        box=box.ROUNDED,
        show_footer=True,
        footer_style="bold",
    )
    table.add_column("Ticker", style="bold cyan")
    table.add_column("Shares", justify="right")
    table.add_column("Avg Cost", justify="right")
    table.add_column("Current Price", justify="right")
    table.add_column("Market Value", justify="right")
    table.add_column("P&L", justify="right")
    table.add_column("P&L %", justify="right")

    total_invested = 0.0
    total_market_value = 0.0
    total_pnl = 0.0

    for h in holdings:
        current_price = get_current_price(h["ticker"])
        if current_price is None:
            current_price_str = "[dim]N/A[/dim]"
            market_value = 0.0
            pnl = 0.0
            pnl_pct = 0.0
        else:
            current_price_str = format_currency(current_price)
            market_value = h["shares"] * current_price
            cost_basis = h["shares"] * h["avg_cost"]
            pnl = market_value - cost_basis
            pnl_pct = (pnl / cost_basis) if cost_basis != 0 else 0.0

        total_invested += h["total_invested"]
        total_market_value += market_value
        total_pnl += pnl

        pnl_color = "green" if pnl >= 0 else "red"
        pnl_str = f"[{pnl_color}]{format_currency(pnl)}[/{pnl_color}]"
        pnl_pct_str = f"[{pnl_color}]{format_percentage(pnl_pct)}[/{pnl_color}]"

        table.add_row(
            h["ticker"],
            f"{h['shares']:.2f}",
            format_currency(h["avg_cost"]),
            current_price_str,
            format_currency(market_value),
            pnl_str,
            pnl_pct_str,
        )

    # Totals footer
    total_pnl_color = "green" if total_pnl >= 0 else "red"
    total_pnl_pct = (
        (total_pnl / total_invested) if total_invested != 0 else 0.0
    )
    table.columns[0].footer = "TOTAL"
    table.columns[4].footer = format_currency(total_market_value)
    table.columns[5].footer = f"[{total_pnl_color}]{format_currency(total_pnl)}[/{total_pnl_color}]"
    table.columns[6].footer = f"[{total_pnl_color}]{format_percentage(total_pnl_pct)}[/{total_pnl_color}]"

    console.print()
    console.print(table)
    console.print()


@app.command("summary")
def summary() -> None:
    """Show a high-level portfolio summary."""
    data = get_portfolio_summary()
    holdings = data["holdings"]

    if not holdings:
        console.print("\n[yellow]No holdings found.[/yellow]\n")
        return

    total_invested = data["total_invested"]
    total_market_value = 0.0

    for h in holdings:
        current_price = get_current_price(h["ticker"])
        if current_price is not None:
            total_market_value += h["shares"] * current_price

    total_pnl = total_market_value - total_invested
    pnl_pct = (total_pnl / total_invested) if total_invested != 0 else 0.0
    pnl_color = "green" if total_pnl >= 0 else "red"

    summary_text = (
        f"[bold]Total Invested:[/bold]   {format_currency(total_invested)}\n"
        f"[bold]Current Value:[/bold]    {format_currency(total_market_value)}\n"
        f"[bold]Total P&L:[/bold]        [{pnl_color}]{format_currency(total_pnl)} "
        f"({format_percentage(pnl_pct)})[/{pnl_color}]\n"
        f"[bold]Holdings:[/bold]          {data['total_holdings']} stocks"
    )

    console.print()
    console.print(Panel(summary_text, title="Portfolio Summary", border_style="blue"))
    console.print()


@app.command("purify")
def purify() -> None:
    """Show purification requirements for portfolio holdings."""
    holdings = get_holdings()
    if not holdings:
        console.print("\n[yellow]No holdings found.[/yellow]\n")
        return

    table = Table(
        title="Purification Report",
        box=box.ROUNDED,
    )
    table.add_column("Ticker", style="bold cyan")
    table.add_column("Shares", justify="right")
    table.add_column("Impure Income %", justify="right")
    table.add_column("Action Required", style="yellow")

    for h in holdings:
        try:
            result = screen_stock(h["ticker"])
            impure_pct = result.get("impure_income_ratio", 0.0)
            if impure_pct is None:
                impure_pct = 0.0
            # Convert from decimal to percentage if needed
            if impure_pct < 1:
                impure_pct_display = impure_pct * 100
            else:
                impure_pct_display = impure_pct

            if impure_pct_display > 0:
                action = f"Purify {impure_pct_display:.2f}% of any dividends received"
            else:
                action = "[green]No purification needed[/green]"
        except Exception:
            impure_pct_display = 0.0
            action = "[dim]Unable to determine[/dim]"

        table.add_row(
            h["ticker"],
            f"{h['shares']:.2f}",
            format_percentage(impure_pct_display),
            action,
        )

    console.print()
    console.print(table)
    console.print(
        "\n[bold yellow]Note:[/bold yellow] Donate the purification amount to charity.\n"
    )


@app.command("history")
def history(
    ticker: Optional[str] = typer.Argument(
        None, help="Filter by ticker symbol (optional)"
    ),
) -> None:
    """Display transaction history."""
    transactions = get_transactions(ticker)
    if not transactions:
        msg = f"No transactions found for {ticker.upper()}." if ticker else "No transactions found."
        console.print(f"\n[yellow]{msg}[/yellow]\n")
        return

    title = f"Transaction History — {ticker.upper()}" if ticker else "Transaction History"
    table = Table(title=title, box=box.ROUNDED)
    table.add_column("Date", style="dim")
    table.add_column("Ticker", style="bold cyan")
    table.add_column("Action", justify="center")
    table.add_column("Shares", justify="right")
    table.add_column("Price", justify="right")
    table.add_column("Total", justify="right")

    for txn in transactions:
        action_style = "green" if txn["action"] == "buy" else "red"
        action_str = f"[{action_style}]{txn['action'].upper()}[/{action_style}]"
        total = txn["shares"] * txn["price"]

        table.add_row(
            txn["date"],
            txn["ticker"],
            action_str,
            f"{txn['shares']:.2f}",
            format_currency(txn["price"]),
            format_currency(total),
        )

    console.print()
    console.print(table)
    console.print()
