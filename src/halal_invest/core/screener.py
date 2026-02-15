"""Halal screening engine based on AAOIFI standards."""

from halal_invest.core.data import get_stock_info, get_financial_data

# ---------------------------------------------------------------------------
# Non-compliant sector and industry lists
# ---------------------------------------------------------------------------

HARAM_SECTORS: set[str] = {"Financial Services", "Financials"}

HARAM_INDUSTRIES: set[str] = {
    "Alcoholic Beverages",
    "Tobacco",
    "Gambling",
    "Casinos & Gaming",
    "Brewers",
    "Distillers & Vintners",
    "Adult Entertainment",
    "Cannabis",
    "Aerospace & Defense",
}

# ---------------------------------------------------------------------------
# Individual screening functions
# ---------------------------------------------------------------------------


def screen_business_activity(info: dict) -> dict:
    """Check whether the company's sector/industry is Sharia-compliant.

    Args:
        info: Stock info dictionary from yfinance.

    Returns:
        dict with keys ``pass``, ``detail``, and ``reason``.
    """
    sector = info.get("sector", "")
    industry = info.get("industry", "")

    if sector in HARAM_SECTORS:
        return {
            "pass": False,
            "detail": f"Sector '{sector}' is non-compliant",
            "reason": f"Sector '{sector}' falls under prohibited financial services",
        }

    if industry in HARAM_INDUSTRIES:
        return {
            "pass": False,
            "detail": f"Industry '{industry}' is non-compliant",
            "reason": f"Industry '{industry}' involves prohibited activities",
        }

    return {
        "pass": True,
        "detail": f"Sector '{sector}', Industry '{industry}' are compliant",
        "reason": "Business activity is permissible",
    }


def screen_debt_ratio(info: dict) -> dict:
    """Check total-debt-to-market-cap ratio (must be < 33%).

    Args:
        info: Stock info dictionary from yfinance.

    Returns:
        dict with keys ``pass``, ``value``, ``threshold``, and ``reason``.
    """
    total_debt = info.get("totalDebt")
    market_cap = info.get("marketCap")

    if total_debt is None or market_cap is None or market_cap == 0:
        return {
            "pass": True,
            "value": None,
            "threshold": 0.33,
            "reason": "Data unavailable - assumed compliant",
        }

    ratio = total_debt / market_cap

    return {
        "pass": ratio < 0.33,
        "value": ratio,
        "threshold": 0.33,
        "reason": (
            f"Debt ratio {ratio:.2%} is {'below' if ratio < 0.33 else 'above or equal to'} "
            f"the 33% threshold"
        ),
    }


def screen_liquid_assets_ratio(info: dict) -> dict:
    """Check liquid-assets-to-market-cap ratio (must be < 33%).

    Liquid assets = totalCash + shortTermInvestments.

    Args:
        info: Stock info dictionary from yfinance.

    Returns:
        dict with keys ``pass``, ``value``, ``threshold``, and ``reason``.
    """
    total_cash = info.get("totalCash", 0) or 0
    short_term_investments = info.get("shortTermInvestments", 0) or 0
    market_cap = info.get("marketCap")

    if market_cap is None or market_cap == 0:
        return {
            "pass": True,
            "value": None,
            "threshold": 0.33,
            "reason": "Data unavailable - assumed compliant",
        }

    ratio = (total_cash + short_term_investments) / market_cap

    return {
        "pass": ratio < 0.33,
        "value": ratio,
        "threshold": 0.33,
        "reason": (
            f"Liquid assets ratio {ratio:.2%} is "
            f"{'below' if ratio < 0.33 else 'above or equal to'} the 33% threshold"
        ),
    }


def screen_impure_income(info: dict) -> dict:
    """Check impure (interest) income as a percentage of revenue (must be < 5%).

    Uses the greater of ``interestExpense`` (absolute value) and
    ``interestIncome`` to capture interest-related revenue more accurately.

    Args:
        info: Stock info dictionary from yfinance.

    Returns:
        dict with keys ``pass``, ``value``, ``threshold``, and ``reason``.
    """
    interest_expense = abs(info.get("interestExpense", 0) or 0)
    interest_income = abs(info.get("interestIncome", 0) or 0)
    impure_amount = max(interest_expense, interest_income)
    total_revenue = info.get("totalRevenue")

    if total_revenue is None or total_revenue == 0:
        return {
            "pass": True,
            "value": None,
            "threshold": 0.05,
            "reason": "Data unavailable - assumed compliant",
        }

    ratio = impure_amount / total_revenue

    return {
        "pass": ratio < 0.05,
        "value": ratio,
        "threshold": 0.05,
        "reason": (
            f"Impure income ratio {ratio:.2%} is "
            f"{'below' if ratio < 0.05 else 'above or equal to'} the 5% threshold"
        ),
    }


def screen_receivables_ratio(info: dict) -> dict:
    """Check accounts receivable to market cap ratio (must be < 33%).

    AAOIFI standard: net receivables / market cap should be below 33%.

    Args:
        info: Stock info dictionary from yfinance.

    Returns:
        dict with keys ``pass``, ``value``, ``threshold``, and ``reason``.
    """
    net_receivables = info.get("netReceivables")
    market_cap = info.get("marketCap")

    if net_receivables is None or market_cap is None or market_cap == 0:
        return {
            "pass": True,
            "value": None,
            "threshold": 0.33,
            "reason": "Data unavailable - marked doubtful",
        }

    ratio = net_receivables / market_cap

    return {
        "pass": ratio < 0.33,
        "value": ratio,
        "threshold": 0.33,
        "reason": (
            f"Receivables ratio {ratio:.2%} is "
            f"{'below' if ratio < 0.33 else 'above or equal to'} the 33% threshold"
        ),
    }


# ---------------------------------------------------------------------------
# Main screening functions
# ---------------------------------------------------------------------------


def screen_stock(ticker: str) -> dict:
    """Run the full halal compliance screen for a single stock.

    Fetches stock info via :func:`get_stock_info` and runs all five screening
    criteria (business activity, debt ratio, liquid assets ratio, impure
    income, receivables ratio).

    Args:
        ticker: Stock ticker symbol (e.g. ``"AAPL"``).

    Returns:
        Dictionary containing ``ticker``, ``company``, ``sector``,
        ``industry``, ``halal_status``, and a ``screens`` sub-dict with the
        result of each individual screen.
    """
    try:
        info = get_stock_info(ticker)
        if not info:
            raise ValueError(f"No data returned for {ticker}")
    except Exception:
        return {
            "ticker": ticker,
            "company": ticker,
            "sector": "N/A",
            "industry": "N/A",
            "halal_status": "ERROR",
            "screens": {},
        }

    business_activity = screen_business_activity(info)
    debt_ratio = screen_debt_ratio(info)
    liquid_assets_ratio = screen_liquid_assets_ratio(info)
    impure_income = screen_impure_income(info)
    receivables_ratio = screen_receivables_ratio(info)

    screens = {
        "business_activity": business_activity,
        "debt_ratio": debt_ratio,
        "liquid_assets_ratio": liquid_assets_ratio,
        "impure_income": impure_income,
        "receivables_ratio": receivables_ratio,
    }

    all_results = [
        business_activity, debt_ratio, liquid_assets_ratio,
        impure_income, receivables_ratio,
    ]

    # Determine overall status
    if any(not r["pass"] for r in all_results):
        halal_status = "FAIL"
    elif any(
        r.get("value") is None
        for r in [debt_ratio, liquid_assets_ratio, impure_income, receivables_ratio]
    ):
        halal_status = "DOUBTFUL"
    else:
        halal_status = "PASS"

    return {
        "ticker": ticker,
        "company": info.get("shortName", ticker),
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "halal_status": halal_status,
        "screens": screens,
    }


def screen_multiple(tickers: list[str], show_progress: bool = True) -> list[dict]:
    """Screen multiple tickers for halal compliance.

    Args:
        tickers: List of stock ticker symbols.
        show_progress: If ``True``, display a rich progress bar in the
            terminal while screening.

    Returns:
        List of screening result dictionaries (one per ticker).
    """
    results: list[dict] = []

    if show_progress:
        from rich.progress import Progress

        with Progress() as progress:
            task = progress.add_task("Screening stocks...", total=len(tickers))
            for ticker in tickers:
                results.append(screen_stock(ticker))
                progress.advance(task)
    else:
        for ticker in tickers:
            results.append(screen_stock(ticker))

    return results
