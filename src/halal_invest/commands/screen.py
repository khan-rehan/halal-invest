"""Screen stocks and ETFs for halal compliance."""

import typer
from typing import Optional

from halal_invest.core.screener import screen_stock, screen_multiple
from halal_invest.display.tables import display_screening_results, display_single_screen, console

app = typer.Typer(invoke_without_command=True)


@app.callback(invoke_without_command=True)
def screen(
    tickers: list[str] = typer.Argument(..., help="One or more stock/ETF tickers to screen"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed screening breakdown"),
):
    """Screen stocks/ETFs for Sharia (halal) compliance using AAOIFI standards."""
    if len(tickers) == 1 or detailed:
        for ticker in tickers:
            result = screen_stock(ticker.upper())
            display_single_screen(result)
    else:
        results = screen_multiple([t.upper() for t in tickers])
        display_screening_results(results)
