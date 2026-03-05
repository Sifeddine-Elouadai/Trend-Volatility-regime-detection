# run.py
from data import load_prices
from features import compute_features
from method1 import apply_method_1
from plotting import (
    plot_current_regime_card,
    plot_method_1,
    plot_regime_heatmap,
    plot_regime_performance_dashboard,
    plot_regime_transition_matrix,
    plot_regime_confidence_overlay,
)
from analytics import (
    compute_regime_statistics,
    export_statistics_csv,
    plot_regime_bars,
    export_full_regime_history,
)
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


def main(ticker: str = "SPY"):
    print("\n" + "=" * 60)
    print("MARKET REGIME DETECTION — TREND × VOLATILITY")
    print("=" * 60 + "\n")

    # Step 1: Load data
    print(f"📥 Loading {ticker} data...")
    prices = load_prices(ticker)
    print(
        f"   ✓ Loaded {len(prices)} days from "
        f"{prices.index[0].date()} to {prices.index[-1].date()}"
    )

    # Step 2: Compute features
    print("\n🔧 Computing features...")
    features = compute_features(prices)
    print("   ✓ Features computed: returns, 20d volatility, 200d MA, trend distance")

    # Step 3: Apply regime detection
    print("\n🎯 Applying regime detection (calibration: 2000–2020)...")
    result = apply_method_1(features)

    unique_regimes = result["regime"].unique()
    print(f"   ✓ Detected regimes: {', '.join(sorted(unique_regimes))}")

    # Step 4: Latest signals
    print("\n" + "=" * 60)
    print("📊 LATEST REGIME SIGNAL")
    print("=" * 60)

    for idx, row in result.tail(5).iterrows():
        bar = "█" * int(row["confidence"] * 20) + "░" * (20 - int(row["confidence"] * 20))
        print(
            f"{idx.date()} | {row['regime']:<20} | "
            f"Trend: {row['trend_state']:<7} | Vol: {row['vol_state']:<6} | "
            f"Conf: [{bar}] {row['confidence']:.1%}"
        )

    print("=" * 60 + "\n")

    # Step 5: Visualisations
    print("🎨 Generating visualisations...")

    for label, fn, args in [
        ("main regime chart",          plot_method_1,                    (result,)),
        ("regime heatmap",             plot_regime_heatmap,              (result,)),
        ("confidence overlay",         plot_regime_confidence_overlay,   (result,)),
    ]:
        print(f"   - {label}...")
        fn(*args)
        plt.show(block=False)
        plt.pause(0.5)

    # Step 6: Statistics
    print("\n📈 Computing regime statistics...")
    stats = compute_regime_statistics(result)

    print("\n" + "=" * 60)
    print("📊 REGIME PERFORMANCE STATISTICS")
    print("=" * 60)

    display = stats.copy()
    display["Annualized Return"]    = display["Annualized Return"].map("{:.2%}".format)
    display["Annualized Volatility"]= display["Annualized Volatility"].map("{:.2%}".format)
    display["Sharpe Ratio"]         = display["Sharpe Ratio"].map("{:.2f}".format)
    display["Max Drawdown"]         = display["Max Drawdown"].map("{:.2%}".format)
    display["Average Daily Return"] = display["Average Daily Return"].map("{:.4%}".format)

    print(display.to_string(index=False))
    print("=" * 60 + "\n")

    # Step 7: Performance visualisations
    print("🎨 Generating performance visualisations...")

    for label, fn, args in [
        ("performance dashboard",      plot_regime_performance_dashboard, (stats,)),
        ("current regime card",        plot_current_regime_card,          (result,)),
        ("transition matrix",          plot_regime_transition_matrix,     (result,)),
        ("regime bars",                plot_regime_bars,                  (stats,)),
    ]:
        print(f"   - {label}...")
        fn(*args)
        plt.show(block=False)
        plt.pause(0.5)

    # Step 8: Export
    print("\n💾 Exporting data...")
    export_full_regime_history(result)
    export_statistics_csv(stats)

    # Step 9: Summary
    print("\n" + "=" * 60)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"📅 Date range  : {result.index[0].date()} → {result.index[-1].date()}")
    print(f"📊 Days analysed: {len(result)}")
    print(f"🎯 Current regime: {result['regime'].iloc[-1]}")
    print(f"📈 Confidence  : {result['confidence'].iloc[-1]:.1%}")
    print(f"📉 Trend: {result['trend_state'].iloc[-1]}  |  Vol: {result['vol_state'].iloc[-1]}")
    print("\n🪟 Plot windows open — close them to exit.")
    print("=" * 60)

    plt.show()


if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "SPY"
    try:
        main(ticker)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted.")
    except Exception as e:
        import traceback
        print(f"\n❌ Error: {e}")
        traceback.print_exc()
    finally:
        print("\n👋 Goodbye!")
