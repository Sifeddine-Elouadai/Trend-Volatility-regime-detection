import yfinance as yf
import pandas as pd


def load_prices(ticker: str = "SPY", start: str = "2000-01-01") -> pd.Series:
    """
    Download adjusted closing prices for a given ticker.

    Parameters
    ----------
    ticker : str
        Yahoo Finance ticker symbol (default: 'SPY').
    start : str
        Start date in 'YYYY-MM-DD' format (default: '2000-01-01').

    Returns
    -------
    pd.Series
        Daily closing prices named after the ticker.
    """
    data = yf.download(ticker, start=start, progress=False, auto_adjust=False)

    if data.empty:
        raise RuntimeError(f"Failed to download data for {ticker}")

    close = data["Close"]

    # Force Series (handles multi-ticker DataFrames)
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    close = close.dropna()
    close.name = "price"

    if len(close) < 2000:
        raise RuntimeError(
            f"Insufficient history for {ticker}: only {len(close)} trading days available. "
            "At least 2000 days required for reliable calibration."
        )

    return close
