import numpy as np
import pandas as pd


def compute_features(prices: pd.Series) -> pd.DataFrame:
    df = pd.DataFrame(index=prices.index)
    df["price"] = prices

    df["ret"] = np.log(df["price"] / df["price"].shift(1))
    df["vol_20d"] = df["ret"].rolling(20).std() * np.sqrt(252)
    df["ma_200"] = df["price"].rolling(200).mean()
    df["trend_dist"] = (df["price"] - df["ma_200"]) / df["ma_200"]

    return df.dropna()
