# Trend-Volatility-regime-detection
A framework for detecting market regimes by combining trend direction and volatility levels. This implementation classifies financial markets into five economically interpretable regimes.

# Method 1: Market Regime Detection Framework

A structural framework for classifying market environments based on trend and volatility dynamics.

## Overview

Financial markets do not operate in a single continuous state. Instead, they evolve through regimes characterized by different combinations of direction, stress, and investor behavior. Method 1 is a structural market regime detection framework designed to classify the prevailing risk environment rather than predict returns.

### Core Objective

> To determine whether the current market environment structurally rewards risk-taking, punishes it, or is transitioning between the two.

This method deliberately avoids short-term forecasting, machine learning, or performance optimization. Its role is to provide context, which serves as the foundation for higher-level models and decision-making processes.

## Why Trend and Volatility?

Market behavior can be decomposed into two orthogonal dimensions:

| Dimension | Question Answered |
|-----------|-------------------|
| **Trend** | Is capital structurally moving into or out of risky assets? |
| **Volatility** | How violently and disorderly is this movement occurring? |

Neither variable alone is sufficient. An uptrend can coexist with rising fragility, and a downtrend can unfold quietly before panic emerges. The interaction between trend and volatility defines the true market regime.

## Feature Construction

Method 1 relies on four core features derived directly from market prices.

### 1. Price
The price series represents the final aggregation of all available market information. All other features are transformations of price.

### 2. Log Returns
Daily log returns are computed as:
r_t = log(P_t / P_{t-1})


Log returns are additive over time, scale-invariant, and standard in financial modeling. Returns are used as inputs for risk measurement, not as predictive signals.

### 3. Realized Volatility (20-Day)
Realized volatility is estimated as:
σ_20(t) = √252 * std(r_{t-19:t})


Volatility captures market stress, uncertainty, leverage effects, and information shocks. It is treated as a regime variable, not a directional signal.

### 4. 200-Day Moving Average
The 200-day moving average is defined as:
MA_200(t) = (1/200) * Σ(P_{t-i}) for i = 0 to 199


This indicator approximates the market's long-term equilibrium and reflects the horizon at which large institutional capital reallocates.

### 5. Trend Distance
Trend strength is measured by the normalized distance between price and its long-term equilibrium:
TrendDist_t = (P_t - MA_200(t)) / MA_200(t)


This quantity captures the conviction and maturity of the prevailing trend.

## State Variables

From the continuous features, two discrete state variables are derived.

### Trend State
| State | Description |
|-------|-------------|
| **UP** | Price is above the 200-day moving average |
| **DOWN** | Price is below the 200-day moving average |
| **NEUTRAL** | Price fluctuates near the moving average |

### Volatility State
Volatility is discretized into three levels using historical calibration:

| State | Description |
|-------|-------------|
| **LOW** | Calm, orderly markets |
| **MEDIUM** | Rising stress and uncertainty |
| **HIGH** | Disorderly markets and systemic pressure |

*Note: The volatility state is smoothed using rolling majority voting to avoid noise-induced regime switching.*

## Regime Definitions

The combination of trend and volatility states yields five economically interpretable regimes.

### RISKON
- **Definition:** Uptrend with low volatility
- **Characteristics:**
  - Capital flows favor risk assets
  - Drawdowns are shallow and short-lived
  - Risk premia compress
- **Interpretation:** Risk-taking is structurally rewarded

### RISKON FRAGILE
- **Definition:** Uptrend with medium volatility
- **Characteristics:**
  - Trend remains positive
  - Stress is increasing
  - Downside risks become asymmetric
- **Interpretation:** Risk-taking remains valid but requires caution

### TRANSITION
- **Definition:** No dominant trend-volatility alignment
- **Characteristics:**
  - Choppy price action
  - Conflicting signals
  - High probability of false breakouts
- **Interpretation:** The market is reassessing its structure

### RISKOFF TRANSITION
- **Definition:** Downtrend without extreme volatility
- **Characteristics:**
  - Capital quietly de-risks
  - Volatility has not yet spiked
  - Often underestimated by investors
- **Interpretation:** Risk appetite is deteriorating beneath the surface

### RISKOFF
- **Definition:** Downtrend with high volatility
- **Characteristics:**
  - Forced selling and deleveraging
  - Correlations rise sharply
  - Liquidity conditions worsen
- **Interpretation:** Capital preservation dominates investment decisions

## Regime Confidence

Regime confidence measures the internal consistency and stability of the detected state. It is **not** a probability of correctness but an assessment of regime strength based on:

- Trend strength (distance from equilibrium)
- Volatility positioning relative to historical norms
- Persistence of the regime over time

Higher confidence indicates a stable and well-established regime, while lower confidence signals fragility or transition.

## Interpretation and Usage

Method 1 should be interpreted as a situational awareness tool. It provides context rather than forecasts.

### Example Interpretations

| Regime | Confidence | Action Implication |
|--------|------------|-------------------|
| RISKON | High | Favor risk exposure |
| RISKON FRAGILE | Moderate | Maintain exposure with tighter risk control |
| RISKOFF TRANSITION | Any | Begin defensive positioning early |
| RISKOFF | High | Prioritize capital preservation |

## Conclusion

Method 1 establishes a disciplined and economically grounded approach to market regime classification. By separating direction from stress and embedding persistence and confidence, it provides a reliable structural view of the market environment. This makes it suitable as a standalone analytical tool and as the base layer for more sophisticated models.

---

**Note:** This framework is intentionally simple, interpretable, and extensible, forming a robust foundation for more advanced regime models.
