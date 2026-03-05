import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ----------------------------
# Performance Statistics
# ----------------------------


def compute_regime_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute annualised performance statistics for each regime.

    Metrics returned
    ----------------
    Average Daily Return   : Mean log return per trading day
    Annualized Return      : Average daily return × 252
    Annualized Volatility  : Daily return std × sqrt(252)
    Sharpe Ratio           : Annualised return / annualised volatility
                             (no risk-free rate adjustment)
    Max Drawdown           : Maximum peak-to-trough drawdown within the regime
    Observations           : Number of trading days spent in the regime

    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns 'price' and 'regime'.

    Returns
    -------
    pd.DataFrame
        One row per regime, sorted alphabetically by regime name.
    """
    df = df.copy()

    df["daily_ret"] = np.log(df["price"] / df["price"].shift(1))
    df = df.dropna(subset=["daily_ret"])

    regime_stats = []

    for regime, group in df.groupby("regime"):
        avg_daily = group["daily_ret"].mean()
        ann_return = avg_daily * 252
        ann_vol = group["daily_ret"].std() * np.sqrt(252)
        sharpe = ann_return / ann_vol if ann_vol != 0 else np.nan

        cumulative = (1 + group["daily_ret"]).cumprod()
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak
        max_dd = drawdown.min()

        regime_stats.append(
            {
                "Regime": regime,
                "Average Daily Return": avg_daily,
                "Annualized Return": ann_return,
                "Annualized Volatility": ann_vol,
                "Sharpe Ratio": sharpe,
                "Max Drawdown": max_dd,
                "Observations": len(group),
            }
        )

    stats_df = pd.DataFrame(regime_stats).sort_values("Regime")
    stats_df.reset_index(drop=True, inplace=True)

    return stats_df


# ----------------------------
# CSV Export
# ----------------------------


def export_statistics_csv(
    stats_df: pd.DataFrame, path: str = "regime_statistics.csv"
) -> None:
    """Save regime statistics to a CSV file."""
    stats_df.to_csv(path, index=False)
    print(f"   ✓ Saved: {path}")


def export_full_regime_history(
    df: pd.DataFrame, path: str = "regime_history.csv"
) -> None:
    """Export the full day-by-day regime history to a CSV file."""
    export_cols = ["price", "trend_state", "vol_state", "regime", "confidence"]
    df[export_cols].to_csv(path)
    print(f"   ✓ Saved: {path}")


# ----------------------------
# Bar Charts
# ----------------------------


def plot_regime_bars(stats_df: pd.DataFrame) -> None:
    """
    Plot a simple bar chart for each key performance metric by regime.

    Parameters
    ----------
    stats_df : pd.DataFrame
        Output of ``compute_regime_statistics``.
    """
    metrics = [
        "Annualized Return",
        "Annualized Volatility",
        "Sharpe Ratio",
        "Max Drawdown",
    ]

    for metric in metrics:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(range(len(stats_df)), stats_df[metric])
        ax.set_title(f"{metric} by Regime")
        ax.set_xticks(range(len(stats_df)))
        ax.set_xticklabels(stats_df["Regime"], rotation=45, ha="right")
        ax.grid(alpha=0.3)
        fig.tight_layout()
        plt.show()
