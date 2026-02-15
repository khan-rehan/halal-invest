"""Composite scoring and valuation tagging for halal-compliant stocks."""

import math


# ---------------------------------------------------------------------------
# Sub-metric scoring helpers (each returns 0-10)
# ---------------------------------------------------------------------------

def _score_pe(value):
    """Score P/E ratio: lower is better (cheaper stock)."""
    if value is None or value <= 0:
        return 5  # neutral if unavailable or negative earnings
    if value < 15:
        return 10
    if value < 25:
        return 7
    if value < 35:
        return 4
    return 1


def _score_pb(value):
    """Score P/B ratio: lower is better."""
    if value is None or value <= 0:
        return 5
    if value < 1.5:
        return 10
    if value < 3:
        return 7
    if value < 5:
        return 4
    return 1


def _score_peg(value):
    """Score PEG ratio: lower means growth exceeds price."""
    if value is None or value <= 0:
        return 5
    if value < 1:
        return 10
    if value < 2:
        return 7
    if value < 3:
        return 4
    return 1


def _score_net_margin(value):
    """Score net margin: higher is better."""
    if value is None:
        return 5
    pct = value * 100 if abs(value) < 1 else value
    if pct > 20:
        return 10
    if pct > 10:
        return 7
    if pct > 5:
        return 5
    if pct > 0:
        return 3
    return 1


def _score_roe(value):
    """Score ROE: higher is better."""
    if value is None:
        return 5
    pct = value * 100 if abs(value) < 1 else value
    if pct > 25:
        return 10
    if pct > 15:
        return 7
    if pct > 10:
        return 5
    if pct > 0:
        return 3
    return 1


def _score_roa(value):
    """Score ROA: higher is better."""
    if value is None:
        return 5
    pct = value * 100 if abs(value) < 1 else value
    if pct > 15:
        return 10
    if pct > 10:
        return 7
    if pct > 5:
        return 5
    if pct > 0:
        return 3
    return 1


def _score_revenue_growth(value):
    """Score revenue growth: higher is better."""
    if value is None:
        return 5
    pct = value * 100 if abs(value) < 1 else value
    if pct > 25:
        return 10
    if pct > 15:
        return 8
    if pct > 5:
        return 6
    if pct > 0:
        return 4
    return 2


def _score_earnings_growth(value):
    """Score earnings growth: higher is better."""
    if value is None:
        return 5
    pct = value * 100 if abs(value) < 1 else value
    if pct > 30:
        return 10
    if pct > 15:
        return 8
    if pct > 5:
        return 6
    if pct > 0:
        return 4
    return 2


def _score_debt_to_equity(value):
    """Score debt/equity: lower is better."""
    if value is None:
        return 5
    if value < 30:
        return 10
    if value < 60:
        return 7
    if value < 100:
        return 5
    if value < 150:
        return 3
    return 1


def _score_current_ratio(value):
    """Score current ratio: higher is better (but extremely high is wasteful)."""
    if value is None:
        return 5
    if value > 3:
        return 8
    if value > 2:
        return 10
    if value > 1.5:
        return 7
    if value > 1:
        return 5
    return 2


def _score_fcf(value):
    """Score free cash flow: positive and high is better."""
    if value is None:
        return 5
    if value > 10_000_000_000:
        return 10
    if value > 1_000_000_000:
        return 8
    if value > 100_000_000:
        return 6
    if value > 0:
        return 4
    return 1


def _score_technical_signal(signal_str):
    """Score overall technical signal: BUY > HOLD > SELL."""
    signal = (signal_str or "").upper()
    if signal == "BUY":
        return 10
    if signal == "HOLD":
        return 5
    if signal == "SELL":
        return 1
    return 5  # N/A


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------

def score_stock(fundamentals: dict, signals: dict) -> float:
    """Compute a 0-100 composite score for a stock.

    Categories and weights:
        Valuation (30%):  P/E, P/B, PEG
        Profitability (25%): Net margin, ROE, ROA
        Growth (20%): Revenue growth, earnings growth
        Financial Health (15%): Debt/equity, current ratio, FCF
        Technical (10%): Overall signal

    Args:
        fundamentals: Output from ``get_fundamentals()``.
        signals: Output from ``get_signals()``.

    Returns:
        Composite score from 0 to 100 (rounded to 1 decimal).
    """
    # Valuation (average of 3 sub-metrics, weight 30%)
    val_scores = [
        _score_pe(fundamentals.get("pe_ratio")),
        _score_pb(fundamentals.get("pb_ratio")),
        _score_peg(fundamentals.get("peg_ratio")),
    ]
    valuation_avg = sum(val_scores) / len(val_scores)

    # Profitability (average of 3 sub-metrics, weight 25%)
    prof_scores = [
        _score_net_margin(fundamentals.get("net_margin")),
        _score_roe(fundamentals.get("roe")),
        _score_roa(fundamentals.get("roa")),
    ]
    profitability_avg = sum(prof_scores) / len(prof_scores)

    # Growth (average of 2 sub-metrics, weight 20%)
    growth_scores = [
        _score_revenue_growth(fundamentals.get("revenue_growth")),
        _score_earnings_growth(fundamentals.get("earnings_growth")),
    ]
    growth_avg = sum(growth_scores) / len(growth_scores)

    # Financial Health (average of 3 sub-metrics, weight 15%)
    health_scores = [
        _score_debt_to_equity(fundamentals.get("debt_to_equity")),
        _score_current_ratio(fundamentals.get("current_ratio")),
        _score_fcf(fundamentals.get("free_cash_flow")),
    ]
    health_avg = sum(health_scores) / len(health_scores)

    # Technical (single metric, weight 10%)
    overall_signal = signals.get("overall", {}).get("signal", "N/A")
    technical_score = _score_technical_signal(overall_signal)

    # Weighted composite (each avg is 0-10, scale to 0-100)
    composite = (
        valuation_avg * 0.30
        + profitability_avg * 0.25
        + growth_avg * 0.20
        + health_avg * 0.15
        + technical_score * 0.10
    ) * 10

    return round(composite, 1)


# ---------------------------------------------------------------------------
# Valuation tag
# ---------------------------------------------------------------------------

def get_valuation_tag(fundamentals: dict) -> str:
    """Classify a stock as UNDERPRICED, FAIR VALUE, or OVERPRICED.

    Uses majority vote across four signals:
        1. P/E ratio: < 15 cheap, 15-25 fair, > 25 expensive
        2. P/B ratio: < 1.5 cheap, 1.5-3 fair, > 3 expensive
        3. PEG ratio: < 1 cheap, 1-2 fair, > 2 expensive
        4. 52-week position: near low = cheap, near high = expensive

    Args:
        fundamentals: Output from ``get_fundamentals()``.

    Returns:
        One of ``"UNDERPRICED"``, ``"FAIR VALUE"``, or ``"OVERPRICED"``.
    """
    votes = {"cheap": 0, "fair": 0, "expensive": 0}

    # P/E
    pe = fundamentals.get("pe_ratio")
    if pe is not None and pe > 0:
        if pe < 15:
            votes["cheap"] += 1
        elif pe <= 25:
            votes["fair"] += 1
        else:
            votes["expensive"] += 1
    else:
        votes["fair"] += 1

    # P/B
    pb = fundamentals.get("pb_ratio")
    if pb is not None and pb > 0:
        if pb < 1.5:
            votes["cheap"] += 1
        elif pb <= 3:
            votes["fair"] += 1
        else:
            votes["expensive"] += 1
    else:
        votes["fair"] += 1

    # PEG
    peg = fundamentals.get("peg_ratio")
    if peg is not None and peg > 0:
        if peg < 1:
            votes["cheap"] += 1
        elif peg <= 2:
            votes["fair"] += 1
        else:
            votes["expensive"] += 1
    else:
        votes["fair"] += 1

    # 52-week position
    price = fundamentals.get("current_price")
    high = fundamentals.get("fifty_two_week_high")
    low = fundamentals.get("fifty_two_week_low")
    if price is not None and high is not None and low is not None and high > low:
        position = (price - low) / (high - low)
        if position < 0.33:
            votes["cheap"] += 1
        elif position <= 0.66:
            votes["fair"] += 1
        else:
            votes["expensive"] += 1
    else:
        votes["fair"] += 1

    # Majority vote
    if votes["cheap"] >= votes["fair"] and votes["cheap"] >= votes["expensive"]:
        return "UNDERPRICED"
    if votes["expensive"] >= votes["fair"] and votes["expensive"] > votes["cheap"]:
        return "OVERPRICED"
    return "FAIR VALUE"


# ---------------------------------------------------------------------------
# Investment allocation
# ---------------------------------------------------------------------------

def allocate_investment(top_stocks: list[dict], amount: float = 1000) -> list[dict]:
    """Suggest dollar allocation across top stocks.

    Weights by composite score, only allocates to stocks tagged
    UNDERPRICED or FAIR VALUE (skips OVERPRICED).

    Args:
        top_stocks: List of dicts with keys ``ticker``, ``company``,
            ``price``, ``score``, ``valuation_tag``.
        amount: Total dollars to invest (default $1,000).

    Returns:
        List of dicts with ``ticker``, ``company``, ``price``,
        ``allocation_dollars``, ``approx_shares``.
    """
    eligible = [
        s for s in top_stocks
        if s.get("valuation_tag") in ("UNDERPRICED", "FAIR VALUE")
        and s.get("price") and s["price"] > 0
    ]

    if not eligible:
        return []

    total_score = sum(s.get("score", 0) for s in eligible)
    if total_score == 0:
        total_score = len(eligible)  # equal weight fallback

    allocations = []
    allocated = 0

    for s in eligible:
        weight = s.get("score", 0) / total_score if total_score else 1 / len(eligible)
        raw_dollars = amount * weight
        rounded = round(raw_dollars / 10) * 10  # round to nearest $10
        rounded = max(rounded, 10)  # minimum $10 per stock

        price = s["price"]
        approx_shares = math.floor(rounded / price * 100) / 100  # 2 decimal places

        allocations.append({
            "ticker": s["ticker"],
            "company": s["company"],
            "price": price,
            "allocation_dollars": rounded,
            "approx_shares": approx_shares,
        })
        allocated += rounded

    # Adjust if we've over/under-allocated due to rounding
    if allocations:
        diff = amount - allocated
        # Apply the difference to the highest-scored stock
        allocations[0]["allocation_dollars"] += diff
        price = allocations[0]["price"]
        allocations[0]["approx_shares"] = (
            math.floor(allocations[0]["allocation_dollars"] / price * 100) / 100
        )

    return allocations
