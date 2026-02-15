"""Research dashboard with fundamentals and halal status."""

import typer
from typing import Optional

from halal_invest.core.fundamentals import get_fundamentals
from halal_invest.core.screener import screen_stock
from halal_invest.display.tables import (
    console, display_fundamentals, display_single_screen,
    format_halal_status, format_currency, format_percentage, format_ratio,
)

from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import box

app = typer.Typer(invoke_without_command=True)


@app.callback(invoke_without_command=True)
def research(
    ticker: str = typer.Argument(..., help="Stock ticker to research"),
    compare: Optional[str] = typer.Option(None, "--compare", "-c", help="Compare with another ticker"),
):
    """Full research dashboard with fundamentals and halal compliance status."""
    ticker = ticker.upper()
    console.print(f"\n[bold]Research Dashboard: {ticker}[/bold]\n")

    # Halal screening
    screen_result = screen_stock(ticker)
    display_single_screen(screen_result)

    # Fundamentals
    fundamentals = get_fundamentals(ticker)
    if fundamentals:
        display_fundamentals(fundamentals)
    else:
        console.print("[red]Could not fetch fundamental data.[/red]")

    # Comparison mode
    if compare:
        compare = compare.upper()
        console.print(f"\n[bold]Comparison: {ticker} vs {compare}[/bold]\n")

        compare_screen = screen_stock(compare)
        compare_fundamentals = get_fundamentals(compare)

        if not compare_fundamentals:
            console.print(f"[red]Could not fetch data for {compare}.[/red]")
            return

        _display_comparison(ticker, fundamentals, screen_result, compare, compare_fundamentals, compare_screen)


def _display_comparison(
    ticker1: str, fund1: dict, screen1: dict,
    ticker2: str, fund2: dict, screen2: dict,
):
    """Display side-by-side comparison of two stocks."""
    table = Table(
        title=f"{ticker1} vs {ticker2}",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Metric", style="bold")
    table.add_column(ticker1, justify="right")
    table.add_column(ticker2, justify="right")

    # Halal status
    table.add_row(
        "Halal Status",
        format_halal_status(screen1.get("halal_status", "N/A")),
        format_halal_status(screen2.get("halal_status", "N/A")),
    )
    table.add_row("", "", "", style="dim")

    # Valuation
    table.add_row("[bold]Valuation[/bold]", "", "", style="dim")
    _add_comparison_row(table, "P/E Ratio", fund1, fund2, "pe_ratio", "ratio")
    _add_comparison_row(table, "Forward P/E", fund1, fund2, "forward_pe", "ratio")
    _add_comparison_row(table, "P/B Ratio", fund1, fund2, "pb_ratio", "ratio")
    _add_comparison_row(table, "PEG Ratio", fund1, fund2, "peg_ratio", "ratio")
    _add_comparison_row(table, "Market Cap", fund1, fund2, "market_cap", "currency")
    table.add_row("", "", "", style="dim")

    # Profitability
    table.add_row("[bold]Profitability[/bold]", "", "", style="dim")
    _add_comparison_row(table, "Gross Margin", fund1, fund2, "gross_margin", "pct")
    _add_comparison_row(table, "Operating Margin", fund1, fund2, "operating_margin", "pct")
    _add_comparison_row(table, "Net Margin", fund1, fund2, "net_margin", "pct")
    _add_comparison_row(table, "ROE", fund1, fund2, "roe", "pct")
    _add_comparison_row(table, "ROA", fund1, fund2, "roa", "pct")
    table.add_row("", "", "", style="dim")

    # Growth
    table.add_row("[bold]Growth[/bold]", "", "", style="dim")
    _add_comparison_row(table, "Revenue Growth", fund1, fund2, "revenue_growth", "pct")
    _add_comparison_row(table, "Earnings Growth", fund1, fund2, "earnings_growth", "pct")
    table.add_row("", "", "", style="dim")

    # Financial Health
    table.add_row("[bold]Financial Health[/bold]", "", "", style="dim")
    _add_comparison_row(table, "Debt/Equity", fund1, fund2, "debt_to_equity", "ratio")
    _add_comparison_row(table, "Current Ratio", fund1, fund2, "current_ratio", "ratio")
    _add_comparison_row(table, "Free Cash Flow", fund1, fund2, "free_cash_flow", "currency")
    table.add_row("", "", "", style="dim")

    # Dividends
    table.add_row("[bold]Dividends[/bold]", "", "", style="dim")
    _add_comparison_row(table, "Dividend Yield", fund1, fund2, "dividend_yield", "pct")
    _add_comparison_row(table, "Payout Ratio", fund1, fund2, "payout_ratio", "pct")

    console.print(table)


def _add_comparison_row(table: Table, label: str, fund1: dict, fund2: dict, key: str, fmt: str):
    """Add a comparison row with formatted values."""
    v1 = fund1.get(key)
    v2 = fund2.get(key)

    if fmt == "pct":
        s1 = format_percentage(v1)
        s2 = format_percentage(v2)
    elif fmt == "currency":
        s1 = format_currency(v1)
        s2 = format_currency(v2)
    elif fmt == "ratio":
        s1 = format_ratio(v1)
        s2 = format_ratio(v2)
    else:
        s1 = str(v1) if v1 is not None else "N/A"
        s2 = str(v2) if v2 is not None else "N/A"

    table.add_row(f"  {label}", s1, s2)
