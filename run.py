from data import load_spy
from features import compute_features
from method1 import apply_method_1
from plotting import plot_method_1


def main():
    prices = load_spy()
    features = compute_features(prices)
    result = apply_method_1(features)

    print(result[["regime", "trend_state", "vol_state", "confidence"]].tail())

    plot_method_1(result)


if __name__ == "__main__":
    main()
