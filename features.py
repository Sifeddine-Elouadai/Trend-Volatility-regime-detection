import numpy as np
import pandas as pd


def compute_features(prices: pd.Series) -> pd.DataFrame:
    """
    Compute all features required for regime detection from a price series.

    Features computed
    -----------------
    ret        : Daily log return
    vol_20d    : 20-day realized volatility, annualised (sqrt-252 scaled)
    ma_200     : 200-day simple moving average
    trend_dist : Normalised distance of price from 200-day MA

    Parameters
    ----------
    prices : pd.Series
        Daily closing prices with a DatetimeIndex.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns [price, ret, vol_20d, ma_200, trend_dist].
        Leading NaN rows (burn-in period) are dropped.
    """
    df = pd.DataFrame(index=prices.index)
    df["price"] = prices

    df["ret"] = np.log(df["price"] / df["price"].shift(1))
    df["vol_20d"] = df["ret"].rolling(20).std() * np.sqrt(252)
    df["ma_200"] = df["price"].rolling(200).mean()
    df["trend_dist"] = (df["price"] - df["ma_200"]) / df["ma_200"]

    return df.dropna()
