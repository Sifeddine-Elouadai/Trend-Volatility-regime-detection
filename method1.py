import numpy as np
import pandas as pd


# ----------------------------
# Helpers
# ----------------------------


def smooth_state(series: pd.Series, window=5) -> pd.Series:
    """
    Smooth categorical states using rolling majority vote
    via numeric encoding (pandas-safe).
    """
    mapping = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    inverse_mapping = {v: k for k, v in mapping.items()}

    numeric = series.map(mapping)

    smoothed_numeric = numeric.rolling(window, min_periods=1).apply(
        lambda x: x.value_counts().idxmax(), raw=False
    )

    return smoothed_numeric.map(inverse_mapping)


def confirm_regime(series: pd.Series, min_days=3) -> pd.Series:
    confirmed = series.copy()
    count = 1

    for i in range(1, len(series)):
        if series.iloc[i] == series.iloc[i - 1]:
            count += 1
        else:
            count = 1

        if count < min_days:
            confirmed.iloc[i] = confirmed.iloc[i - 1]

    return confirmed


# ----------------------------
# Method 1
# ----------------------------


def apply_method_1(
    df: pd.DataFrame, calibration_start="2000", calibration_end="2020"
) -> pd.DataFrame:

    calib = df.loc[calibration_start:calibration_end]

    # --- Volatility thresholds
    low_vol = calib["vol_20d"].quantile(0.33)
    high_vol = calib["vol_20d"].quantile(0.66)
    mid_vol = (low_vol + high_vol) / 2

    # --- Trend state
    df["trend_state"] = np.where(
        df["price"] > df["ma_200"],
        "UP",
        np.where(df["price"] < df["ma_200"], "DOWN", "NEUTRAL"),
    )

    # --- Raw volatility state
    df["vol_state_raw"] = pd.cut(
        df["vol_20d"],
        bins=[-np.inf, low_vol, high_vol, np.inf],
        labels=["LOW", "MEDIUM", "HIGH"],
    ).astype(str)

    # --- Smoothed volatility state
    df["vol_state"] = smooth_state(df["vol_state_raw"], window=5)

    # --- Regime logic
    def classify(row):
        if row["trend_state"] == "UP" and row["vol_state"] == "LOW":
            return "RISK_ON"
        if row["trend_state"] == "UP" and row["vol_state"] == "MEDIUM":
            return "RISK_ON_FRAGILE"
        if row["trend_state"] == "DOWN" and row["vol_state"] == "HIGH":
            return "RISK_OFF"
        if row["trend_state"] == "DOWN":
            return "RISK_OFF_TRANSITION"
        return "TRANSITION"

    df["regime_raw"] = df.apply(classify, axis=1)

    # --- Confirm regime persistence
    df["regime"] = confirm_regime(df["regime_raw"], min_days=3)

    # ----------------------------
    # Confidence score
    # ----------------------------

    # Trend strength (5% = strong)
    trend_score = np.clip(np.abs(df["trend_dist"]) / 0.05, 0, 1)

    # Volatility distance from mid
    vol_dist = np.abs(df["vol_20d"] - mid_vol) / (high_vol - low_vol)
    vol_score = np.clip(1 - vol_dist, 0, 1)

    # Regime duration
    blocks = (df["regime"] != df["regime"].shift()).cumsum()
    duration = df.groupby(blocks).cumcount() + 1
    duration_score = np.clip(duration / 20, 0, 1)

    df["confidence"] = 0.4 * trend_score + 0.3 * vol_score + 0.3 * duration_score

    return df
