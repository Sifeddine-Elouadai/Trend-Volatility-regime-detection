import yfinance as yf
import pandas as pd


def load_spy(start="2000-01-01") -> pd.Series:
    data = yf.download("SPY", start=start, progress=False, auto_adjust=False)

    if data.empty:
        raise RuntimeError("Failed to download SPY data")

    close = data["Close"]

    # Force Series (critical)
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    close = close.dropna()
    close.name = "price"

    if len(close) < 2000:
        raise RuntimeError("Not enough history")

    return close
