"""Technical buy/sell signal analysis."""

import typer

from halal_invest.core.technicals import get_signals
from halal_invest.display.tables import display_signals, console

app = typer.Typer(invoke_without_command=True)


@app.callback(invoke_without_command=True)
def signals(
    ticker: str = typer.Argument(..., help="Stock ticker to analyze"),
    period: str = typer.Option(
        "1y", "--period", "-p", help="Historical period (1mo, 3mo, 6mo, 1y, 2y)"
    ),
):
    """Show technical buy/sell signals for a stock."""
    console.print(f"\n[bold]Technical Signals for {ticker.upper()}[/bold]\n")
    result = get_signals(ticker.upper(), period)
    display_signals(ticker.upper(), result)
