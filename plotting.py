# plotting.py
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates

plt.style.use("seaborn-v0_8-darkgrid")

COLORS = {
    "RISK_ON": "#2ecc71",  # Emerald green
    "RISK_ON_FRAGILE": "#f1c40f",  # Sunflower yellow
    "BULL_EXPANSION": "#9b59b6",  # Amethyst purple
    "RISK_OFF": "#e74c3c",  # Alizarin red
    "RISK_OFF_TRANSITION": "#e67e22",  # Carrot orange
    "NEUTRAL": "#95a5a6",  # Concrete gray
    "TRANSITION": "#95a5a6",  # Fallback (should never appear)
    "PRICE": "#2c3e50",  # Dark blue
    "MA200": "#3498db",  # Peter river blue
}

# Canonical ordering used across all plots
REGIME_ORDER = [
    "RISK_ON",
    "RISK_ON_FRAGILE",
    "BULL_EXPANSION",
    "NEUTRAL",
    "RISK_OFF_TRANSITION",
    "RISK_OFF",
]


def _regime_blocks(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of df with a 'regime_block' column for groupby iteration."""
    out = df.copy()
    out["regime_block"] = (out["regime"] != out["regime"].shift()).cumsum()
    return out


def plot_method_1(
    df: pd.DataFrame,
    start_date: str | None = None,
    end_date: str | None = None,
    figsize: tuple[int, int] = (16, 8),
):
    """
    Main regime chart: price, 200-day MA, and colour-coded regime backgrounds.

    Parameters
    ----------
    df : pd.DataFrame
        Output of ``apply_method_1``.
    start_date, end_date : str, optional
        ISO date strings to slice the plot window.
    figsize : tuple
        Matplotlib figure size.

    Returns
    -------
    (fig, ax)
    """
    plot_df = df.copy()
    if start_date:
        plot_df = plot_df[plot_df.index >= start_date]
    if end_date:
        plot_df = plot_df[plot_df.index <= end_date]

    plot_df = _regime_blocks(plot_df)

    fig, ax = plt.subplots(figsize=figsize, facecolor="white")

    # --- Price and MA200
    ax.plot(
        plot_df.index,
        plot_df["price"],
        color=COLORS["PRICE"],
        lw=2,
        label="SPY",
        zorder=5,
    )
    ax.plot(
        plot_df.index,
        plot_df["ma_200"],
        color=COLORS["MA200"],
        lw=1.5,
        ls="--",
        alpha=0.8,
        label="200-day MA",
        zorder=4,
    )

    # --- Fill between price and MA200
    ax.fill_between(
        plot_df.index,
        plot_df["price"],
        plot_df["ma_200"],
        where=(plot_df["price"] >= plot_df["ma_200"]),
        color=COLORS["RISK_ON"],
        alpha=0.1,
        label="Above MA (Uptrend)",
        zorder=1,
    )
    ax.fill_between(
        plot_df.index,
        plot_df["price"],
        plot_df["ma_200"],
        where=(plot_df["price"] < plot_df["ma_200"]),
        color=COLORS["RISK_OFF"],
        alpha=0.1,
        label="Below MA (Downtrend)",
        zorder=1,
    )

    # --- Regime background blocks
    ymax = plot_df["price"].max() * 1.05

    for _, group in plot_df.groupby("regime_block"):
        regime = group["regime"].iloc[0]
        color = COLORS.get(regime, "#95a5a6")
        ax.axvspan(group.index[0], group.index[-1], alpha=0.15, color=color, zorder=0)

        if len(group) > 10:
            mid_point = group.index[len(group) // 2]
            ax.text(
                mid_point,
                ymax * 0.98,
                regime.replace("_", " "),
                fontsize=9,
                fontweight="bold",
                color=color,
                ha="center",
                va="top",
                bbox=dict(
                    boxstyle="round,pad=0.3",
                    facecolor="white",
                    alpha=0.8,
                    edgecolor=color,
                ),
            )

    # --- Formatting
    ax.set_title(
        "Market Regimes: Trend × Volatility Analysis",
        fontsize=18,
        fontweight="bold",
        pad=20,
    )
    ax.set_ylabel("Price ($)", fontsize=12, fontweight="semibold")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

    ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)

    legend_elements = [
        mpatches.Patch(color=COLORS[r], alpha=0.5, label=r.replace("_", " "))
        for r in REGIME_ORDER
    ]
    ax.legend(
        handles=legend_elements, loc="upper left", ncol=3, fontsize=10, framealpha=0.95
    )

    plt.tight_layout()
    return fig, ax


def plot_regime_heatmap(df: pd.DataFrame, figsize: tuple[int, int] = (16, 6)):
    """
    Timeline heatmap showing regime duration and transitions at weekly resolution.

    Uses pcolormesh with a DatetimeIndex so the x-axis displays real calendar
    years instead of raw matplotlib ordinal integers.

    Returns
    -------
    (fig, ax)
    """
    plot_df = df.copy()  # avoid mutating caller's DataFrame

    existing_regimes = [r for r in REGIME_ORDER if r in plot_df["regime"].unique()]
    regime_to_num = {r: i for i, r in enumerate(existing_regimes)}
    n_regimes = len(existing_regimes)

    plot_df["regime_num"] = plot_df["regime"].map(regime_to_num)

    colors = [COLORS[r] for r in existing_regimes]
    cmap = LinearSegmentedColormap.from_list("regime_cmap", colors, N=n_regimes)

    # Resample to weekly — preserves a true DatetimeIndex
    weekly_regime = plot_df["regime_num"].resample("W").last().dropna()

    # pcolormesh needs cell-edge coordinates (one more point than data columns).
    # Convert dates to matplotlib float numbers so we can compute midpoints/offsets.
    x_vals = mdates.date2num(weekly_regime.index.to_pydatetime())
    half = 3.5  # half a week in matplotlib date units (days)
    x_edges = np.concatenate(
        [
            [x_vals[0] - half],
            (x_vals[:-1] + x_vals[1:]) / 2,
            [x_vals[-1] + half],
        ]
    )
    y_edges = np.array([0.0, 1.0])
    data = weekly_regime.values.reshape(1, -1).astype(float)

    fig, ax = plt.subplots(figsize=figsize, facecolor="white")

    mesh = ax.pcolormesh(
        x_edges,
        y_edges,
        data,
        cmap=cmap,
        vmin=-0.5,
        vmax=n_regimes - 0.5,
        shading="flat",
    )

    # Register the x-axis as a date axis so formatters work correctly
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

    ax.set_xlim(x_edges[0], x_edges[-1])
    ax.set_yticks([])
    ax.set_title("Regime Timeline Heatmap", fontsize=16, fontweight="bold", pad=20)

    # Colourbar: one centred tick per regime
    cbar = plt.colorbar(mesh, ax=ax, orientation="vertical", pad=0.02)
    cbar.set_ticks(np.arange(n_regimes))
    cbar.set_ticklabels(existing_regimes)
    cbar.ax.tick_params(labelsize=10)

    plt.tight_layout()
    return fig, ax


def plot_regime_performance_dashboard(
    stats_df: pd.DataFrame,
    figsize: tuple[int, int] = (16, 10),
):
    """
    2 × 2 dashboard: annualised return, Sharpe ratio, max drawdown, time allocation.

    Returns
    -------
    (fig, axes)
    """
    stats_df = stats_df.copy()
    stats_df = stats_df[stats_df["Observations"] > 0].reset_index(drop=True)
    stats_df = (
        stats_df.set_index("Regime")
        .reindex(REGIME_ORDER)
        .reset_index()
        .dropna(subset=["Observations"])
    )

    bar_colors = [COLORS.get(r, "#95a5a6") for r in stats_df["Regime"]]

    fig, axes = plt.subplots(2, 2, figsize=figsize, facecolor="white")
    fig.suptitle("Regime Performance Analytics", fontsize=18, fontweight="bold", y=0.98)

    def _bar(ax, y, title, ylabel, fmt="{:.1%}"):
        x = range(len(stats_df))
        bars = ax.bar(x, y, color=bar_colors, alpha=0.8)
        ax.axhline(y=0, color="black", linewidth=0.5)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_ylabel(ylabel)
        ax.set_xticks(range(len(stats_df)))
        ax.set_xticklabels(stats_df["Regime"], rotation=45, ha="right")
        ax.grid(alpha=0.3)
        for bar in bars:
            h = bar.get_height()
            if np.isfinite(h):
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    h,
                    fmt.format(h),
                    ha="center",
                    va="bottom" if h >= 0 else "top",
                    fontsize=9,
                    fontweight="bold",
                )
        return bars

    # 1. Annualised Return
    _bar(axes[0, 0], stats_df["Annualized Return"], "Annualized Return", "Return")

    # 2. Sharpe Ratio
    _bar(axes[0, 1], stats_df["Sharpe Ratio"], "Sharpe Ratio", "Sharpe", fmt="{:.2f}")

    # 3. Max Drawdown
    _bar(axes[1, 0], stats_df["Max Drawdown"], "Maximum Drawdown", "Drawdown")

    # 4. Time allocation (pie)
    ax4 = axes[1, 1]
    pie_data = stats_df[stats_df["Observations"] > 0]
    if not pie_data.empty and np.all(np.isfinite(pie_data["Observations"].values)):
        wedges, texts, autotexts = ax4.pie(
            pie_data["Observations"].values,
            labels=pie_data["Regime"].values,
            colors=[COLORS.get(r, "#95a5a6") for r in pie_data["Regime"]],
            autopct=lambda pct: f"{pct:.1f}%" if pct > 0 else "",
            startangle=90,
            textprops={"fontsize": 9},
            pctdistance=0.85,
        )
        for at in autotexts:
            at.set_color("white")
            at.set_fontweight("bold")
    else:
        ax4.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax4.transAxes)
    ax4.set_title("Time Spent in Each Regime", fontsize=12, fontweight="bold")

    plt.tight_layout()
    return fig, axes


def plot_current_regime_card(df: pd.DataFrame, figsize: tuple[int, int] = (8, 4)):
    """
    'Weather card' showing the most recent regime and key metrics.

    Returns
    -------
    (fig, ax)
    """
    latest = df.iloc[-1]
    regime = latest["regime"]
    color = COLORS.get(regime, "#95a5a6")

    fig, ax = plt.subplots(figsize=figsize, facecolor="white")

    ax.add_patch(
        Rectangle(
            (0, 0), 1, 1, transform=ax.transAxes, color=color, alpha=0.2, zorder=0
        )
    )

    ax.text(
        0.5,
        0.75,
        regime.replace("_", " "),
        fontsize=28,
        fontweight="bold",
        ha="center",
        color=color,
        transform=ax.transAxes,
    )

    metrics_text = (
        f"Trend: {latest['trend_state']}  |  "
        f"Volatility: {latest['vol_state']}  |  "
        f"Confidence: {latest['confidence']:.1%}"
    )
    ax.text(
        0.5,
        0.45,
        metrics_text,
        fontsize=14,
        ha="center",
        transform=ax.transAxes,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.8),
    )

    ax.text(
        0.5,
        0.15,
        f"As of {latest.name.strftime('%Y-%m-%d')}",
        fontsize=12,
        ha="center",
        transform=ax.transAxes,
        style="italic",
        color="gray",
    )

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    plt.tight_layout()
    return fig, ax


def plot_regime_transition_matrix(df: pd.DataFrame, figsize: tuple[int, int] = (10, 8)):
    """
    Empirical transition probability matrix between regimes.

    Rows = current regime (today), columns = next regime (tomorrow).

    Returns
    -------
    (fig, ax)
    """
    from collections import Counter

    regimes = df["regime"].dropna()
    transitions = list(zip(regimes[:-1], regimes[1:]))
    trans_counts = Counter(transitions)

    unique_regimes = [r for r in REGIME_ORDER if r in df["regime"].unique()]
    n = len(unique_regimes)
    regime_to_idx = {r: i for i, r in enumerate(unique_regimes)}

    trans_matrix = np.zeros((n, n))
    for (from_r, to_r), count in trans_counts.items():
        if from_r in regime_to_idx and to_r in regime_to_idx:
            trans_matrix[regime_to_idx[from_r], regime_to_idx[to_r]] = count

    row_sums = trans_matrix.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    trans_matrix = trans_matrix / row_sums

    fig, ax = plt.subplots(figsize=figsize, facecolor="white")
    im = ax.imshow(trans_matrix, cmap="YlOrRd", vmin=0, vmax=1)

    for i in range(n):
        for j in range(n):
            if trans_matrix[i, j] > 0:
                text_color = "white" if trans_matrix[i, j] > 0.5 else "black"
                ax.text(
                    j,
                    i,
                    f"{trans_matrix[i, j]:.0%}",
                    ha="center",
                    va="center",
                    color=text_color,
                    fontweight="bold",
                )

    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels(unique_regimes, rotation=45, ha="right")
    ax.set_yticklabels(unique_regimes)
    ax.set_xlabel("To Regime (Tomorrow)", fontsize=12, fontweight="bold")
    ax.set_ylabel("From Regime (Today)", fontsize=12, fontweight="bold")
    ax.set_title("Regime Transition Probabilities", fontsize=16, fontweight="bold")

    plt.colorbar(im, ax=ax, label="Transition Probability")
    plt.tight_layout()
    return fig, ax


def plot_regime_confidence_overlay(
    df: pd.DataFrame, figsize: tuple[int, int] = (16, 6)
):
    """
    Price chart with the confidence score as a secondary-axis area fill.

    Regime background shading is applied by block (not by individual day)
    to avoid O(n) ``axvspan`` calls.

    Returns
    -------
    (fig, (ax1, ax2))
    """
    plot_df = _regime_blocks(df.copy())

    fig, ax1 = plt.subplots(figsize=figsize, facecolor="white")

    # Price
    ax1.plot(plot_df.index, plot_df["price"], color=COLORS["PRICE"], lw=2, label="SPY")
    ax1.set_ylabel("Price ($)", fontsize=12, fontweight="semibold")

    # Confidence
    ax2 = ax1.twinx()
    ax2.fill_between(
        plot_df.index,
        0,
        plot_df["confidence"],
        color=COLORS["RISK_ON_FRAGILE"],
        alpha=0.3,
        label="Confidence",
    )
    ax2.set_ylabel("Confidence Score", fontsize=12, fontweight="semibold")
    ax2.set_ylim(0, 1)

    # Regime background — one axvspan per block (not per day)
    for _, group in plot_df.groupby("regime_block"):
        regime = group["regime"].iloc[0]
        color = COLORS.get(regime, "#95a5a6")
        ax2.axvspan(group.index[0], group.index[-1], alpha=0.05, color=color)

    ax1.set_title(
        "Price with Regime Confidence Overlay", fontsize=16, fontweight="bold", pad=20
    )
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha="right")
    ax1.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    plt.tight_layout()
    return fig, (ax1, ax2)
