import numpy as np
import pandas as pd


# ----------------------------
# Valid regime set
# ----------------------------

VALID_REGIMES = {
    "RISK_ON",
    "RISK_ON_FRAGILE",
    "BULL_EXPANSION",
    "NEUTRAL",
    "RISK_OFF_TRANSITION",
    "RISK_OFF",
}


# ----------------------------
# Helpers
# ----------------------------


def smooth_state(series: pd.Series, window: int = 5) -> pd.Series:
    """
    Smooth a categorical volatility state using rolling majority vote.

    Converts the categorical series to integer codes, applies a rolling
    mode, then maps back to labels.  This avoids pandas SettingWithCopy
    warnings and is safe across pandas versions.

    Parameters
    ----------
    series : pd.Series
        Categorical series with values in {'LOW', 'MEDIUM', 'HIGH'}.
    window : int
        Rolling window length for the majority vote (default: 5).

    Returns
    -------
    pd.Series
        Smoothed categorical series with the same index.
    """
    mapping = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    inverse_mapping = {v: k for k, v in mapping.items()}

    numeric = series.map(mapping)
    smoothed_numeric = numeric.rolling(window, min_periods=1).apply(
        lambda x: pd.Series(x).value_counts().idxmax(), raw=False
    )
    return smoothed_numeric.map(inverse_mapping)


def confirm_regime(series: pd.Series, min_days: int = 3) -> pd.Series:
    """
    Enforce regime persistence: a new regime must hold for at least
    ``min_days`` consecutive days before it is accepted.  Until then,
    the previous confirmed regime is carried forward.

    Implemented via a NumPy loop on the underlying array to avoid
    repeated ``iloc`` writes, which are slow and trigger
    SettingWithCopyWarning in recent pandas versions.

    Parameters
    ----------
    series : pd.Series
        Raw regime labels.
    min_days : int
        Minimum consecutive days required to confirm a regime change
        (default: 3).

    Returns
    -------
    pd.Series
        Confirmed regime labels with the same index as ``series``.
    """
    values = series.to_numpy(dtype=object)
    confirmed = values.copy()
    count = 1

    for i in range(1, len(values)):
        if values[i] == values[i - 1]:
            count += 1
        else:
            count = 1

        if count < min_days:
            confirmed[i] = confirmed[i - 1]

    return pd.Series(confirmed, index=series.index, name=series.name)


# ----------------------------
# Regime classifier
# ----------------------------


def _classify_row(trend: str, vol: str) -> str:
    """Map a (trend_state, vol_state) pair to a regime label."""
    if trend == "UP" and vol == "LOW":
        return "RISK_ON"
    if trend == "UP" and vol == "MEDIUM":
        return "RISK_ON_FRAGILE"
    if trend == "UP" and vol == "HIGH":
        return "BULL_EXPANSION"
    if trend == "DOWN" and vol == "HIGH":
        return "RISK_OFF"
    if trend == "DOWN":           # LOW or MEDIUM vol in a downtrend
        return "RISK_OFF_TRANSITION"
    # trend == "NEUTRAL" (any vol)
    return "NEUTRAL"


# ----------------------------
# Method 1 — main entry point
# ----------------------------


def apply_method_1(
    df: pd.DataFrame,
    calibration_start: str = "2000",
    calibration_end: str = "2020",
) -> pd.DataFrame:
    """
    Apply the Trend × Volatility market regime detection framework.

    Regime labels
    -------------
    RISK_ON              : Uptrend + low volatility
    RISK_ON_FRAGILE      : Uptrend + medium volatility
    BULL_EXPANSION       : Uptrend + high volatility  (late-cycle expansion)
    RISK_OFF_TRANSITION  : Downtrend + low/medium volatility
    RISK_OFF             : Downtrend + high volatility
    NEUTRAL              : Price near 200-day MA (no dominant trend)

    Confidence score
    ----------------
    A composite [0, 1] signal measuring the internal stability and
    conviction of the detected regime.  It combines:
      - Trend strength   (40 %): normalised distance from 200-day MA
      - Volatility score (30 %): proximity to a vol-state boundary
      - Duration score   (30 %): how long the current regime has persisted

    All thresholds (vol quantiles) are estimated exclusively on the
    calibration window to avoid look-ahead bias.  The confidence
    formula uses only those calibration-period constants and does NOT
    re-examine out-of-sample data.

    Parameters
    ----------
    df : pd.DataFrame
        Feature DataFrame produced by ``compute_features``.
        Must contain columns: price, vol_20d, ma_200, trend_dist.
    calibration_start : str
        Start of the calibration (in-sample) window (default: '2000').
    calibration_end : str
        End of the calibration window (default: '2020').

    Returns
    -------
    pd.DataFrame
        Input DataFrame augmented with columns:
        trend_state, vol_state_raw, vol_state, regime_raw, regime, confidence.
    """
    df = df.copy()

    # ------------------------------------------------------------------
    # 1. Calibrate volatility thresholds on in-sample window only
    # ------------------------------------------------------------------
    calib = df.loc[calibration_start:calibration_end]

    low_vol  = calib["vol_20d"].quantile(0.33)
    high_vol = calib["vol_20d"].quantile(0.66)
    mid_vol  = (low_vol + high_vol) / 2.0       # stored as constant; not re-estimated

    # ------------------------------------------------------------------
    # 2. Trend state
    # ------------------------------------------------------------------
    df["trend_state"] = np.where(
        df["price"] > df["ma_200"],
        "UP",
        np.where(df["price"] < df["ma_200"], "DOWN", "NEUTRAL"),
    )

    # ------------------------------------------------------------------
    # 3. Volatility state (raw then smoothed)
    # ------------------------------------------------------------------
    df["vol_state_raw"] = pd.cut(
        df["vol_20d"],
        bins=[-np.inf, low_vol, high_vol, np.inf],
        labels=["LOW", "MEDIUM", "HIGH"],
    ).astype(str)

    df["vol_state"] = smooth_state(df["vol_state_raw"], window=5)

    # ------------------------------------------------------------------
    # 4. Regime classification + persistence filter
    # ------------------------------------------------------------------
    df["regime_raw"] = df.apply(
        lambda row: _classify_row(row["trend_state"], row["vol_state"]), axis=1
    )
    df["regime"] = confirm_regime(df["regime_raw"], min_days=3)

    # Sanity check — no unexpected labels should ever appear
    unexpected = set(df["regime"].unique()) - VALID_REGIMES
    assert not unexpected, f"Unexpected regime labels detected: {unexpected}"

    # ------------------------------------------------------------------
    # 5. Confidence score (uses only calibration-period constants)
    # ------------------------------------------------------------------

    # Trend strength: ±5 % from MA is treated as "strong" conviction
    trend_score = np.clip(np.abs(df["trend_dist"]) / 0.05, 0, 1)

    # Volatility score: how far is current vol from the mid-point boundary?
    # Computed using calibration constants (low_vol, high_vol, mid_vol)
    # — no look-ahead involved.
    vol_range   = high_vol - low_vol          # scalar from calibration window
    vol_dist    = np.abs(df["vol_20d"] - mid_vol) / vol_range
    vol_score   = np.clip(1.0 - vol_dist, 0, 1)

    # Duration score: regimes that have persisted ≥ 20 days score 1.0
    blocks         = (df["regime"] != df["regime"].shift()).cumsum()
    duration       = df.groupby(blocks).cumcount() + 1
    duration_score = np.clip(duration / 20, 0, 1)

    df["confidence"] = (
        0.4 * trend_score
        + 0.3 * vol_score
        + 0.3 * duration_score
    )

    return df
