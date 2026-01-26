import matplotlib.pyplot as plt


def plot_method_1(df):
    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(df.index, df["price"], color="black", lw=1, label="Price")
    ax.plot(df.index, df["ma_200"], color="blue", lw=1, ls="--", label="MA 200")

    colors = {
        "RISK_ON": "green",
        "RISK_ON_FRAGILE": "yellow",
        "RISK_OFF": "red",
        "RISK_OFF_TRANSITION": "orange",
        "TRANSITION": "gray",
    }

    ymin, ymax = df["price"].min(), df["price"].max()

    for regime, color in colors.items():
        mask = df["regime"] == regime
        if mask.any():
            ax.fill_between(
                df.index, ymin, ymax, where=mask, color=color, alpha=0.08, label=regime
            )

    ax.set_title("Method 1 — Trend × Volatility Regimes")
    ax.legend(ncol=3)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.show()
