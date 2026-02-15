"""Rich terminal display formatters."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def format_halal_status(status: str) -> str:
    """Return a Rich-markup coloured string for the given halal status.

    Args:
        status: One of ``"PASS"``, ``"FAIL"``, ``"DOUBTFUL"``, or ``"ERROR"``.

    Returns:
        Rich-markup string with appropriate colour.
    """
    mapping = {
        "PASS": "[bold green]HALAL[/bold green]",
        "FAIL": "[bold red]NOT HALAL[/bold red]",
        "DOUBTFUL": "[bold yellow]DOUBTFUL[/bold yellow]",
        "ERROR": "[bold red]ERROR[/bold red]",
    }
    return mapping.get(status, status)


def format_pass_fail(passed: bool) -> str:
    """Return a Rich-markup coloured PASS or FAIL string.

    Args:
        passed: ``True`` for PASS, ``False`` for FAIL.

    Returns:
        Rich-markup string.
    """
    return "[green]PASS[/green]" if passed else "[red]FAIL[/red]"


def format_percentage(value: float | None) -> str:
    """Format a float as a percentage string.

    Args:
        value: Ratio value (e.g. ``0.1234``), or ``None``.

    Returns:
        Formatted string like ``"12.34%"`` or ``"N/A"``.
    """
    if value is None:
        return "N/A"
    return f"{value * 100:.2f}%"


def format_currency(value: float | None) -> str:
    """Format a numeric value as a human-readable USD string.

    Uses B (billions), M (millions), K (thousands) suffixes.

    Args:
        value: Dollar amount, or ``None``.

    Returns:
        Formatted string like ``"$1.23B"`` or ``"N/A"``.
    """
    if value is None:
        return "N/A"

    abs_value = abs(value)
    sign = "-" if value < 0 else ""

    if abs_value >= 1_000_000_000:
        return f"{sign}${abs_value / 1_000_000_000:.2f}B"
    elif abs_value >= 1_000_000:
        return f"{sign}${abs_value / 1_000_000:.2f}M"
    elif abs_value >= 1_000:
        return f"{sign}${abs_value / 1_000:.2f}K"
    else:
        return f"{sign}${abs_value:.2f}"


def format_ratio(value: float | None) -> str:
    """Format a ratio value to two decimal places.

    Args:
        value: Ratio value, or ``None``.

    Returns:
        Formatted string like ``"0.23"`` or ``"N/A"``.
    """
    if value is None:
        return "N/A"
    return f"{value:.2f}"


# ---------------------------------------------------------------------------
# Display functions
# ---------------------------------------------------------------------------


def display_screening_results(results: list[dict]) -> None:
    """Display a summary table of screening results for multiple stocks.

    Args:
        results: List of screening result dicts as returned by
            :func:`~halal_invest.core.screener.screen_stock`.
    """
    table = Table(
        title="Halal Screening Results",
        box=box.ROUNDED,
        show_lines=True,
    )

    table.add_column("Ticker", style="bold cyan", no_wrap=True)
    table.add_column("Company", style="white")
    table.add_column("Sector", style="dim")
    table.add_column("Status", justify="center")
    table.add_column("Debt Ratio", justify="right")
    table.add_column("Liquid Assets", justify="right")
    table.add_column("Impure Income", justify="right")

    for result in results:
        screens = result.get("screens", {})

        debt_value = screens.get("debt_ratio", {}).get("value")
        liquid_value = screens.get("liquid_assets_ratio", {}).get("value")
        impure_value = screens.get("impure_income", {}).get("value")

        table.add_row(
            result.get("ticker", ""),
            result.get("company", ""),
            result.get("sector", "N/A"),
            format_halal_status(result.get("halal_status", "ERROR")),
            format_ratio(debt_value),
            format_ratio(liquid_value),
            format_percentage(impure_value),
        )

    console.print()
    console.print(table)
    console.print()


def display_single_screen(result: dict) -> None:
    """Display a detailed screening breakdown for a single stock.

    Shows each screening criterion with its PASS/FAIL status, computed
    value, threshold, and explanatory reason inside a rich Panel.

    Args:
        result: Screening result dict as returned by
            :func:`~halal_invest.core.screener.screen_stock`.
    """
    ticker = result.get("ticker", "???")
    company = result.get("company", ticker)
    status = result.get("halal_status", "ERROR")
    sector = result.get("sector", "N/A")
    industry = result.get("industry", "N/A")
    screens = result.get("screens", {})

    # Header
    header = Text()
    header.append(f"{company} ", style="bold white")
    header.append(f"({ticker})", style="dim")

    # Build detail table
    detail_table = Table(box=box.SIMPLE, show_header=True, expand=True)
    detail_table.add_column("Criterion", style="bold", ratio=2)
    detail_table.add_column("Result", justify="center", ratio=1)
    detail_table.add_column("Value", justify="right", ratio=1)
    detail_table.add_column("Threshold", justify="right", ratio=1)
    detail_table.add_column("Reason", ratio=3)

    # Business activity screen
    ba = screens.get("business_activity", {})
    if ba:
        detail_table.add_row(
            "Business Activity",
            format_pass_fail(ba.get("pass", False)),
            "—",
            "—",
            ba.get("reason", ""),
        )

    # Financial screens
    financial_screens = [
        ("Debt Ratio", "debt_ratio"),
        ("Liquid Assets Ratio", "liquid_assets_ratio"),
        ("Impure Income", "impure_income"),
    ]

    for label, key in financial_screens:
        screen = screens.get(key, {})
        if screen:
            value = screen.get("value")
            threshold = screen.get("threshold")
            detail_table.add_row(
                label,
                format_pass_fail(screen.get("pass", False)),
                format_ratio(value),
                format_ratio(threshold),
                screen.get("reason", ""),
            )

    # Info line
    info_line = Text()
    info_line.append("Sector: ", style="bold")
    info_line.append(f"{sector}  ", style="white")
    info_line.append("Industry: ", style="bold")
    info_line.append(industry, style="white")

    # Compose the panel content
    content = Text()
    content.append("")

    panel = Panel(
        renderable=detail_table,
        title=f"{company} ({ticker})",
        subtitle=f"Status: {format_halal_status(status)}",
        border_style="green" if status == "PASS" else "red" if status == "FAIL" else "yellow",
        box=box.ROUNDED,
        padding=(1, 2),
    )

    console.print()
    console.print(info_line, justify="center")
    console.print(panel)
    console.print()


def display_fundamentals(data: dict) -> None:
    """Display fundamental analysis metrics in categorised rich panels.

    Groups metrics into Valuation, Profitability, Growth, Financial Health,
    and Dividends categories, each rendered as a sub-table inside a Panel.

    Args:
        data: Fundamentals dictionary as returned by
            :func:`~halal_invest.core.fundamentals.get_fundamentals`.
    """
    name = data.get("name", "Unknown")
    sector = data.get("sector", "N/A")
    industry = data.get("industry", "N/A")

    # Header
    console.print()
    console.print(
        f"[bold]{name}[/bold]  |  Sector: {sector}  |  Industry: {industry}",
        justify="center",
    )

    if data.get("description"):
        console.print(
            Panel(data["description"], title="About", box=box.SIMPLE, padding=(0, 2)),
        )

    # Category definitions: (display_label, key, formatter)
    categories = {
        "Valuation": [
            ("P/E Ratio", "pe_ratio", format_ratio),
            ("Forward P/E", "forward_pe", format_ratio),
            ("P/B Ratio", "pb_ratio", format_ratio),
            ("PEG Ratio", "peg_ratio", format_ratio),
            ("EV/EBITDA", "ev_ebitda", format_ratio),
            ("Market Cap", "market_cap", format_currency),
        ],
        "Profitability": [
            ("Gross Margin", "gross_margin", format_percentage),
            ("Operating Margin", "operating_margin", format_percentage),
            ("Net Margin", "net_margin", format_percentage),
            ("ROE", "roe", format_percentage),
            ("ROA", "roa", format_percentage),
        ],
        "Growth": [
            ("Revenue Growth", "revenue_growth", format_percentage),
            ("Earnings Growth", "earnings_growth", format_percentage),
        ],
        "Financial Health": [
            ("Debt/Equity", "debt_to_equity", format_ratio),
            ("Current Ratio", "current_ratio", format_ratio),
            ("Free Cash Flow", "free_cash_flow", format_currency),
            ("Total Debt", "total_debt", format_currency),
            ("Total Cash", "total_cash", format_currency),
        ],
        "Dividends": [
            ("Dividend Yield", "dividend_yield", format_percentage),
            ("Payout Ratio", "payout_ratio", format_percentage),
        ],
    }

    for category_name, metrics in categories.items():
        table = Table(box=box.SIMPLE, show_header=False, expand=True, padding=(0, 2))
        table.add_column("Metric", style="bold", ratio=1)
        table.add_column("Value", justify="right", ratio=1)

        for label, key, formatter in metrics:
            value = data.get(key)
            table.add_row(label, formatter(value))

        panel = Panel(
            table,
            title=f"[bold]{category_name}[/bold]",
            box=box.ROUNDED,
            padding=(0, 1),
        )
        console.print(panel)

    console.print()


def display_signals(ticker: str, signals: dict) -> None:
    """Display technical analysis signals in a rich table.

    Args:
        ticker: Stock ticker symbol.
        signals: Dictionary of signal results. Each key (e.g. ``"rsi"``,
            ``"macd"``, ``"sma_crossover"``, ``"bollinger"``, ``"volume"``,
            ``"overall"``) maps to a dict with ``"signal"`` (BUY/SELL/HOLD)
            and ``"detail"`` keys.
    """

    def _colour_signal(signal: str) -> str:
        """Return Rich-markup coloured signal string."""
        signal_upper = signal.upper()
        if signal_upper == "BUY":
            return "[bold green]BUY[/bold green]"
        elif signal_upper == "SELL":
            return "[bold red]SELL[/bold red]"
        else:
            return "[bold yellow]HOLD[/bold yellow]"

    table = Table(
        title=f"Technical Signals - {ticker}",
        box=box.ROUNDED,
        show_lines=True,
    )

    table.add_column("Indicator", style="bold cyan", ratio=1)
    table.add_column("Signal", justify="center", ratio=1)
    table.add_column("Detail", ratio=3)

    # Preserve a logical display order
    indicator_order = ["rsi", "macd", "sma_crossover", "bollinger", "volume", "overall"]

    # Show ordered indicators first, then any extras
    displayed = set()
    for key in indicator_order:
        if key in signals:
            entry = signals[key]
            signal_str = entry.get("signal", "HOLD")
            detail_str = entry.get("detail", "")
            label = key.replace("_", " ").title()

            if key == "overall":
                label = "[bold]Overall[/bold]"

            table.add_row(label, _colour_signal(signal_str), detail_str)
            displayed.add(key)

    # Any remaining signals not in the predefined order
    for key, entry in signals.items():
        if key not in displayed and isinstance(entry, dict):
            signal_str = entry.get("signal", "HOLD")
            detail_str = entry.get("detail", "")
            label = key.replace("_", " ").title()
            table.add_row(label, _colour_signal(signal_str), detail_str)

    console.print()
    console.print(table)
    console.print()
