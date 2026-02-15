"""Main CLI entry point for halal-invest."""

import typer

from halal_invest.commands.screen import app as screen_app
from halal_invest.commands.research import app as research_app
from halal_invest.commands.portfolio import app as portfolio_app
from halal_invest.commands.watchlist import app as watchlist_app
from halal_invest.commands.signals import app as signals_app
from halal_invest.commands.filter import app as filter_app

app = typer.Typer(
    name="halal-invest",
    help="Halal Stock & ETF Investment Tool — screen, research, track, and analyze Sharia-compliant investments.",
    no_args_is_help=True,
)

app.add_typer(screen_app, name="screen", help="Screen stocks/ETFs for halal compliance")
app.add_typer(research_app, name="research", help="Research dashboard with fundamentals & halal status")
app.add_typer(portfolio_app, name="portfolio", help="Track your portfolio, P&L, and purification")
app.add_typer(watchlist_app, name="watchlist", help="Manage your stock watchlist and price alerts")
app.add_typer(signals_app, name="signals", help="Technical buy/sell signals")
app.add_typer(filter_app, name="filter", help="Filter SPUS stocks by valuation, signal, CAGR, and growth")


if __name__ == "__main__":
    app()
