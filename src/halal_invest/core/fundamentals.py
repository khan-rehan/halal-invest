"""
Fundamental analysis metrics module.

Computes and organizes fundamental financial metrics from yfinance
stock data, covering valuation, profitability, growth, financial
health, dividends, and general company information.
"""

from halal_invest.core.data import get_stock_info, get_price_history


def get_fundamentals(ticker: str) -> dict:
    """Fetch and organize fundamental metrics for the given ticker.

    Retrieves stock info via yfinance and extracts key fundamental
    metrics across multiple categories.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").

    Returns:
        Dictionary containing fundamental metrics with the following keys:

        Price: current_price, fifty_two_week_high, fifty_two_week_low
        Valuation: pe_ratio, forward_pe, pb_ratio, peg_ratio, ev_ebitda,
                   market_cap
        Profitability: gross_margin, operating_margin, net_margin, roe, roa
        Growth: revenue_growth, earnings_growth
        Financial Health: debt_to_equity, current_ratio, free_cash_flow,
                          total_debt, total_cash
        Dividends: dividend_yield, payout_ratio
        General: name, sector, industry, description

        Missing data points are set to None.
    """
    info = get_stock_info(ticker)

    # Determine company name: prefer shortName, fall back to longName
    name = info.get("shortName") or info.get("longName")

    # Truncate description to 200 characters
    description = info.get("longBusinessSummary")
    if description and len(description) > 200:
        description = description[:200]

    # Price data
    current_price = info.get("currentPrice") or info.get("regularMarketPreviousClose")

    return {
        # Price
        "current_price": current_price,
        "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
        "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
        # Valuation
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "pb_ratio": info.get("priceToBook"),
        "peg_ratio": info.get("pegRatio"),
        "ev_ebitda": info.get("enterpriseToEbitda"),
        "market_cap": info.get("marketCap"),
        # Profitability
        "gross_margin": info.get("grossMargins"),
        "operating_margin": info.get("operatingMargins"),
        "net_margin": info.get("profitMargins"),
        "roe": info.get("returnOnEquity"),
        "roa": info.get("returnOnAssets"),
        # Growth
        "revenue_growth": info.get("revenueGrowth"),
        "earnings_growth": info.get("earningsGrowth"),
        # Financial Health
        "debt_to_equity": info.get("debtToEquity"),
        "current_ratio": info.get("currentRatio"),
        "free_cash_flow": info.get("freeCashflow"),
        "total_debt": info.get("totalDebt"),
        "total_cash": info.get("totalCash"),
        # Dividends
        "dividend_yield": info.get("dividendYield"),
        "payout_ratio": info.get("payoutRatio"),
        # General
        "name": name,
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "description": description,
    }


# ---------------------------------------------------------------------------
# Historical Growth (CAGR)
# ---------------------------------------------------------------------------


def _compute_cagr(start_price: float, end_price: float, years: float) -> float | None:
    """Compute Compound Annual Growth Rate.

    Args:
        start_price: Price at the beginning of the period.
        end_price: Price at the end of the period.
        years: Number of years in the period.

    Returns:
        CAGR as a decimal (e.g. 0.12 for 12%), or None if inputs are invalid.
    """
    if start_price is None or end_price is None or years <= 0:
        return None
    if start_price <= 0:
        return None
    try:
        return (end_price / start_price) ** (1 / years) - 1
    except (ZeroDivisionError, ValueError, OverflowError):
        return None


def get_historical_growth(ticker: str) -> dict:
    """Fetch historical price growth (CAGR) for multiple time periods.

    Computes the Compound Annual Growth Rate for 1-year, 3-year, 5-year,
    and 10-year periods. Each period is fetched independently so stocks
    with shorter histories still return partial data.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").

    Returns:
        Dictionary with keys: cagr_1y, cagr_3y, cagr_5y, cagr_10y.
        Each value is a float (decimal) or None if unavailable.
    """
    periods = [
        ("cagr_1y", "1y", 1),
        ("cagr_3y", "3y", 3),
        ("cagr_5y", "5y", 5),
        ("cagr_10y", "10y", 10),
    ]

    result = {}
    for key, period, years in periods:
        try:
            history = get_price_history(ticker, period=period)
            if history.empty or len(history) < 2:
                result[key] = None
                continue
            start_price = float(history["Close"].iloc[0])
            end_price = float(history["Close"].iloc[-1])
            result[key] = _compute_cagr(start_price, end_price, years)
        except Exception:
            result[key] = None

    return result
