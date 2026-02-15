"""Technical indicator calculations for buy/sell signals."""

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from ta.volatility import BollingerBands

from halal_invest.core.data import get_price_history


def calculate_rsi(df: pd.DataFrame, window: int = 14) -> dict:
    """Calculate RSI and return signal dict."""
    rsi_indicator = RSIIndicator(close=df["Close"], window=window)
    rsi_values = rsi_indicator.rsi()
    latest_rsi = round(rsi_values.iloc[-1], 2)

    if latest_rsi < 30:
        signal = "BUY"
        detail = f"RSI at {latest_rsi} — Oversold (below 30)"
    elif latest_rsi > 70:
        signal = "SELL"
        detail = f"RSI at {latest_rsi} — Overbought (above 70)"
    else:
        signal = "HOLD"
        detail = f"RSI at {latest_rsi} — Neutral range (30-70)"

    return {"value": latest_rsi, "signal": signal, "detail": detail}


def calculate_macd(df: pd.DataFrame) -> dict:
    """Calculate MACD and return signal dict."""
    macd_indicator = MACD(close=df["Close"])
    macd_line = macd_indicator.macd()
    signal_line = macd_indicator.macd_signal()

    latest_macd = round(macd_line.iloc[-1], 4)
    latest_signal = round(signal_line.iloc[-1], 4)

    # Check for crossover by comparing last 2 values
    prev_macd = macd_line.iloc[-2]
    prev_signal = signal_line.iloc[-2]

    if latest_macd > latest_signal:
        signal = "BUY"
        if prev_macd <= prev_signal:
            detail = f"MACD ({latest_macd}) crossed above signal ({latest_signal}) — Bullish crossover"
        else:
            detail = f"MACD ({latest_macd}) above signal ({latest_signal}) — Bullish"
    elif latest_macd < latest_signal:
        signal = "SELL"
        if prev_macd >= prev_signal:
            detail = f"MACD ({latest_macd}) crossed below signal ({latest_signal}) — Bearish crossover"
        else:
            detail = f"MACD ({latest_macd}) below signal ({latest_signal}) — Bearish"
    else:
        signal = "HOLD"
        detail = f"MACD ({latest_macd}) equal to signal ({latest_signal}) — Neutral"

    return {
        "macd": latest_macd,
        "signal_line": latest_signal,
        "signal": signal,
        "detail": detail,
    }


def calculate_sma_crossover(df: pd.DataFrame) -> dict:
    """Calculate SMA 50/200 crossover and return signal dict."""
    sma_50_indicator = SMAIndicator(close=df["Close"], window=50)
    sma_50_values = sma_50_indicator.sma_indicator()
    latest_sma_50 = sma_50_values.iloc[-1]

    # Check if we have enough data for SMA 200
    if len(df) < 200:
        return {
            "sma_50": round(latest_sma_50, 2) if pd.notna(latest_sma_50) else None,
            "sma_200": None,
            "signal": "HOLD",
            "detail": "Insufficient data for SMA 200",
        }

    sma_200_indicator = SMAIndicator(close=df["Close"], window=200)
    sma_200_values = sma_200_indicator.sma_indicator()
    latest_sma_200 = sma_200_values.iloc[-1]

    if pd.isna(latest_sma_50) or pd.isna(latest_sma_200):
        return {
            "sma_50": None,
            "sma_200": None,
            "signal": "HOLD",
            "detail": "Insufficient data for SMA 200",
        }

    latest_sma_50 = round(latest_sma_50, 2)
    latest_sma_200 = round(latest_sma_200, 2)

    if latest_sma_50 > latest_sma_200:
        signal = "BUY"
        detail = f"SMA 50 ({latest_sma_50}) above SMA 200 ({latest_sma_200}) — Golden Cross territory"
    elif latest_sma_50 < latest_sma_200:
        signal = "SELL"
        detail = f"SMA 50 ({latest_sma_50}) below SMA 200 ({latest_sma_200}) — Death Cross territory"
    else:
        signal = "HOLD"
        detail = f"SMA 50 ({latest_sma_50}) equal to SMA 200 ({latest_sma_200}) — Neutral"

    return {
        "sma_50": latest_sma_50,
        "sma_200": latest_sma_200,
        "signal": signal,
        "detail": detail,
    }


def calculate_bollinger(df: pd.DataFrame) -> dict:
    """Calculate Bollinger Bands and return signal dict."""
    bb_indicator = BollingerBands(close=df["Close"], window=20, window_dev=2)

    upper_band = round(bb_indicator.bollinger_hband().iloc[-1], 2)
    lower_band = round(bb_indicator.bollinger_lband().iloc[-1], 2)
    middle_band = round(bb_indicator.bollinger_mavg().iloc[-1], 2)
    latest_price = round(df["Close"].iloc[-1], 2)

    if latest_price < lower_band:
        signal = "BUY"
        detail = f"Price ({latest_price}) below lower band ({lower_band}) — Potentially oversold"
    elif latest_price > upper_band:
        signal = "SELL"
        detail = f"Price ({latest_price}) above upper band ({upper_band}) — Potentially overbought"
    else:
        signal = "HOLD"
        detail = f"Price ({latest_price}) within bands ({lower_band} - {upper_band}) — Neutral"

    return {
        "upper": upper_band,
        "lower": lower_band,
        "middle": middle_band,
        "price": latest_price,
        "signal": signal,
        "detail": detail,
    }


def calculate_volume_signal(df: pd.DataFrame) -> dict:
    """Calculate volume signal relative to 20-day average."""
    avg_volume = df["Volume"].tail(20).mean()
    current_volume = int(df["Volume"].iloc[-1])
    ratio = round(current_volume / avg_volume, 2) if avg_volume > 0 else 0.0

    if ratio > 1.5:
        signal = "HIGH VOLUME"
        detail = f"Volume ({current_volume:,}) is {ratio}x the 20-day average ({int(avg_volume):,}) — Unusual activity"
    else:
        signal = "NORMAL"
        detail = f"Volume ({current_volume:,}) is {ratio}x the 20-day average ({int(avg_volume):,}) — Normal activity"

    return {
        "current_volume": current_volume,
        "avg_volume": round(avg_volume, 2),
        "ratio": ratio,
        "signal": signal,
        "detail": detail,
    }


def get_signals(ticker: str, period: str = "1y") -> dict:
    """Fetch price history and compute all technical signals for a ticker."""
    df = get_price_history(ticker, period)

    na_result = {"signal": "N/A", "detail": "No data available"}

    if df is None or df.empty:
        return {
            "ticker": ticker,
            "rsi": na_result,
            "macd": na_result,
            "sma_crossover": na_result,
            "bollinger": na_result,
            "volume": na_result,
            "overall": {"signal": "N/A", "detail": "No price data available"},
        }

    # Calculate each indicator, catching errors individually
    try:
        rsi_result = calculate_rsi(df)
    except Exception:
        rsi_result = {"signal": "N/A", "detail": "Error calculating RSI"}

    try:
        macd_result = calculate_macd(df)
    except Exception:
        macd_result = {"signal": "N/A", "detail": "Error calculating MACD"}

    try:
        sma_result = calculate_sma_crossover(df)
    except Exception:
        sma_result = {"signal": "N/A", "detail": "Error calculating SMA crossover"}

    try:
        bollinger_result = calculate_bollinger(df)
    except Exception:
        bollinger_result = {"signal": "N/A", "detail": "Error calculating Bollinger Bands"}

    try:
        volume_result = calculate_volume_signal(df)
    except Exception:
        volume_result = {"signal": "N/A", "detail": "Error calculating volume signal"}

    # Determine overall signal from the 4 directional indicators (volume excluded)
    indicator_signals = [
        rsi_result.get("signal"),
        macd_result.get("signal"),
        sma_result.get("signal"),
        bollinger_result.get("signal"),
    ]

    buy_count = sum(1 for s in indicator_signals if s == "BUY")
    sell_count = sum(1 for s in indicator_signals if s == "SELL")

    if buy_count > sell_count:
        overall_signal = "BUY"
    elif sell_count > buy_count:
        overall_signal = "SELL"
    else:
        overall_signal = "HOLD"

    overall_detail = f"{buy_count} of 4 indicators suggest BUY"

    return {
        "ticker": ticker,
        "rsi": rsi_result,
        "macd": macd_result,
        "sma_crossover": sma_result,
        "bollinger": bollinger_result,
        "volume": volume_result,
        "overall": {"signal": overall_signal, "detail": overall_detail},
    }
