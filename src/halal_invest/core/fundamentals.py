"""
Fundamental analysis metrics module.

Computes and organizes fundamental financial metrics from yfinance
stock data, covering valuation, profitability, growth, financial
health, dividends, and general company information.
"""

from halal_invest.core.data import get_stock_info


def get_fundamentals(ticker: str) -> dict:
    """Fetch and organize fundamental metrics for the given ticker.

    Retrieves stock info via yfinance and extracts key fundamental
    metrics across multiple categories.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").

    Returns:
        Dictionary containing fundamental metrics with the following keys:

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

    return {
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
