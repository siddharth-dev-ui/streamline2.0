"""Technical indicator calculations and explanations."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

INDICATOR_EXPLANATIONS = {
    "RSI": (
        "**RSI (Relative Strength Index)** measures how quickly price has been rising or falling "
        "on a 0–100 scale. Readings above 70 often mean strong recent buying; below 30 often mean "
        "strong recent selling. It describes momentum, not whether a stock is a good investment."
    ),
    "MACD": (
        "**MACD** compares two moving averages of price to show momentum shifts. When the MACD line "
        "crosses above the signal line, upward momentum may be building; a cross below may mean "
        "momentum is fading. The histogram shows the gap between the two lines."
    ),
    "SMA": (
        "**SMA (Simple Moving Average)** is the average closing price over a set number of days. "
        "The 50-day SMA reflects the medium-term trend; the 200-day SMA reflects the long-term trend. "
        "Price above these lines often means the trend is up over that time frame."
    ),
    "EMA": (
        "**EMA (Exponential Moving Average)** is like an SMA but gives more weight to recent prices. "
        "It reacts faster to new price moves and is often used to track the current trend."
    ),
    "Bollinger Bands": (
        "**Bollinger Bands** place a moving average in the middle with upper and lower bands based on "
        "recent volatility. When bands widen, volatility is high; when they narrow, volatility is low. "
        "Price near the upper band can mean strong recent gains; near the lower band can mean recent weakness."
    ),
    "ATR": (
        "**ATR (Average True Range)** measures how much a stock typically moves per day. A higher ATR "
        "means larger daily swings; a lower ATR means calmer trading. It describes volatility, not direction."
    ),
    "Volume trend": (
        "**Volume trend** compares recent trading volume to a longer average. Rising volume during a "
        "price move can mean more participants are involved. Falling volume can mean interest is fading. "
        "Volume alone does not predict future price."
    ),
}


@dataclass
class TechnicalSnapshot:
    """Latest values for key technical indicators."""

    rsi: float | None
    macd: float | None
    macd_signal: float | None
    sma_50: float | None
    sma_200: float | None
    ema_20: float | None
    bb_upper: float | None
    bb_lower: float | None
    atr: float | None
    volume_trend: float | None


def _find_row(df: pd.DataFrame, labels: list[str]) -> pd.Series | None:
    for label in labels:
        if label in df.index:
            return df.loc[label]
    return None


def compute_indicators(history: pd.DataFrame) -> pd.DataFrame:
    """Add technical indicator columns to OHLCV history."""
    data = history.copy()
    close = data["Close"]
    high = data["High"]
    low = data["Low"]
    volume = data["Volume"]

    data["SMA_50"] = close.rolling(50).mean()
    data["SMA_200"] = close.rolling(200).mean()
    data["EMA_20"] = close.ewm(span=20, adjust=False).mean()

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    data["RSI"] = 100 - (100 / (1 + rs))

    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    data["MACD"] = ema_12 - ema_26
    data["MACD_Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()
    data["MACD_Hist"] = data["MACD"] - data["MACD_Signal"]

    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    data["BB_Mid"] = bb_mid
    data["BB_Upper"] = bb_mid + 2 * bb_std
    data["BB_Lower"] = bb_mid - 2 * bb_std

    true_range = pd.concat(
        [
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs(),
        ],
        axis=1,
    ).max(axis=1)
    data["ATR"] = true_range.rolling(14).mean()

    vol_20 = volume.rolling(20).mean()
    vol_50 = volume.rolling(50).mean()
    data["Volume_SMA_20"] = vol_20
    data["Volume_SMA_50"] = vol_50
    data["Volume_Trend"] = vol_20 / vol_50.replace(0, pd.NA)

    return data


def latest_snapshot(data: pd.DataFrame) -> TechnicalSnapshot:
    """Return the most recent indicator values."""
    row = data.iloc[-1]
    return TechnicalSnapshot(
        rsi=_safe(row.get("RSI")),
        macd=_safe(row.get("MACD")),
        macd_signal=_safe(row.get("MACD_Signal")),
        sma_50=_safe(row.get("SMA_50")),
        sma_200=_safe(row.get("SMA_200")),
        ema_20=_safe(row.get("EMA_20")),
        bb_upper=_safe(row.get("BB_Upper")),
        bb_lower=_safe(row.get("BB_Lower")),
        atr=_safe(row.get("ATR")),
        volume_trend=_safe(row.get("Volume_Trend")),
    )


def _safe(value) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)
