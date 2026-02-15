"""Filter SPUS ETF holdings by valuation, signal, CAGR, and growth criteria."""

import time

import typer
from rich.table import Table
from rich import box

from halal_invest.core.spus import get_spus_tickers
from halal_invest.core.fundamentals import get_fundamentals, get_historical_growth
from halal_invest.core.technicals import get_signals
from halal_invest.core.scoring import score_stock, get_valuation_tag
from halal_invest.display.tables import console

app = typer.Typer(invoke_without_command=True)


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}%"


def _colour_signal(signal: str) -> str:
    s = signal.upper()
    if s == "BUY":
        return "[bold green]BUY[/bold green]"
    if s == "SELL":
        return "[bold red]SELL[/bold red]"
    return "[yellow]HOLD[/yellow]"


def _colour_valuation(tag: str) -> str:
    if tag == "UNDERPRICED":
        return "[bold green]UNDERPRICED[/bold green]"
    if tag == "OVERPRICED":
        return "[bold red]OVERPRICED[/bold red]"
    return "[yellow]FAIR VALUE[/yellow]"


@app.callback(invoke_without_command=True)
def filter_stocks(
    valuation: str = typer.Option(
        "FAIR VALUE", "--valuation", "-v",
        help="Valuation tag filter: 'FAIR VALUE', 'UNDERPRICED', or 'ALL'",
    ),
    signal: str = typer.Option(
        "BUY", "--signal", "-s",
        help="Technical signal filter: 'BUY', 'HOLD', 'SELL', or 'ALL'",
    ),
    cagr_5y: float = typer.Option(
        10.0, "--cagr-5y",
        help="Minimum 5-year CAGR percentage (e.g. 10 for 10%)",
    ),
    cagr_10y: float = typer.Option(
        15.0, "--cagr-10y",
        help="Minimum 10-year CAGR percentage (e.g. 15 for 15%)",
    ),
    rev_growth: float = typer.Option(
        5.0, "--rev-growth", "-r",
        help="Minimum revenue growth percentage (e.g. 5 for 5%)",
    ),
):
    """Filter SPUS ETF holdings by valuation, signal, CAGR, and revenue growth."""
    console.print("\n[bold]SPUS Stock Filter[/bold]\n")

    # Normalize inputs
    valuation_upper = valuation.upper().strip()
    signal_upper = signal.upper().strip()

    allowed_valuations = None  # None means all
    if valuation_upper != "ALL":
        allowed_valuations = [valuation_upper]

    allowed_signal = None
    if signal_upper != "ALL":
        allowed_signal = signal_upper

    cagr_5y_min = cagr_5y / 100
    cagr_10y_min = cagr_10y / 100
    rev_growth_min = rev_growth / 100

    # Show active filters
    console.print(f"  Valuation: [cyan]{valuation_upper}[/cyan]")
    console.print(f"  Signal:    [cyan]{signal_upper}[/cyan]")
    console.print(f"  5Y CAGR:   [cyan]>{cagr_5y:.0f}%[/cyan]")
    console.print(f"  10Y CAGR:  [cyan]>{cagr_10y:.0f}%[/cyan]")
    console.print(f"  Rev Growth:[cyan] >{rev_growth:.0f}%[/cyan]")
    console.print()

    # Fetch tickers
    tickers = get_spus_tickers()
    if not tickers:
        console.print("[red]ERROR: Could not fetch SPUS tickers.[/red]")
        raise typer.Exit(1)

    console.print(f"Fetching data for [bold]{len(tickers)}[/bold] SPUS stocks...\n")

    # Gather data
    results = []
    with console.status("[bold green]Analyzing stocks...") as status:
        for i, ticker in enumerate(tickers, 1):
            status.update(f"[bold green]Analyzing {ticker} ({i}/{len(tickers)})...")
            try:
                fund = get_fundamentals(ticker)
                sigs = get_signals(ticker, period="6mo")
                hist = get_historical_growth(ticker)
                score = score_stock(fund, sigs, hist)
                tag = get_valuation_tag(fund)
                sig = sigs.get("overall", {}).get("signal", "N/A")

                results.append({
                    "ticker": ticker,
                    "company": fund.get("name") or "N/A",
                    "sector": fund.get("sector") or "N/A",
                    "score": score,
                    "valuation": tag,
                    "signal": sig,
                    "price": fund.get("current_price"),
                    "pe_ratio": fund.get("pe_ratio"),
                    "revenue_growth": fund.get("revenue_growth"),
                    "cagr_5y": hist.get("cagr_5y"),
                    "cagr_10y": hist.get("cagr_10y"),
                })
            except Exception as e:
                console.print(f"  [dim]Warning: {ticker} failed: {e}[/dim]")

            if i % 10 == 0:
                time.sleep(0.3)

    # Apply filters
    def passes(r):
        if allowed_valuations and r["valuation"] not in allowed_valuations:
            return False
        if allowed_signal and (r["signal"] or "").upper() != allowed_signal:
            return False
        c5 = r["cagr_5y"]
        if c5 is None or c5 <= cagr_5y_min:
            return False
        c10 = r["cagr_10y"]
        if c10 is None or c10 <= cagr_10y_min:
            return False
        rg = r["revenue_growth"]
        if rg is None or rg <= rev_growth_min:
            return False
        return True

    matched = [r for r in results if passes(r)]
    matched.sort(key=lambda r: r["score"], reverse=True)

    # Display results
    if not matched:
        console.print("[yellow]No stocks match the given criteria.[/yellow]\n")
        console.print(f"[dim]Total analyzed: {len(results)}[/dim]")
        raise typer.Exit(0)

    table = Table(
        title=f"Filtered SPUS Stocks ({len(matched)} matches)",
        box=box.ROUNDED,
        show_lines=True,
    )

    table.add_column("#", style="dim", justify="right", width=3)
    table.add_column("Ticker", style="bold cyan", no_wrap=True)
    table.add_column("Company", style="white")
    table.add_column("Score", justify="center")
    table.add_column("Price", justify="right")
    table.add_column("Valuation", justify="center")
    table.add_column("Signal", justify="center")
    table.add_column("P/E", justify="right")
    table.add_column("5Y CAGR", justify="right")
    table.add_column("10Y CAGR", justify="right")
    table.add_column("Rev Growth", justify="right")
    table.add_column("Sector", style="dim")

    for i, r in enumerate(matched, 1):
        score = r["score"]
        if score >= 70:
            score_str = f"[bold green]{score:.1f}[/bold green]"
        elif score >= 50:
            score_str = f"[yellow]{score:.1f}[/yellow]"
        else:
            score_str = f"[red]{score:.1f}[/red]"

        price = f"${r['price']:.2f}" if r["price"] else "N/A"
        pe = f"{r['pe_ratio']:.1f}" if r["pe_ratio"] else "N/A"

        table.add_row(
            str(i),
            r["ticker"],
            r["company"][:28],
            score_str,
            price,
            _colour_valuation(r["valuation"]),
            _colour_signal(r["signal"]),
            pe,
            _fmt_pct(r["cagr_5y"]),
            _fmt_pct(r["cagr_10y"]),
            _fmt_pct(r["revenue_growth"]),
            r["sector"][:20],
        )

    console.print()
    console.print(table)
    console.print(f"\n[dim]Total SPUS stocks analyzed: {len(results)}[/dim]\n")
