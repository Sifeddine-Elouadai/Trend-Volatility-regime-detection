# Trend × Volatility Market Regime Detection

> A framework that classifies every trading day into one of six
> structurally distinct market regimes using price trend and realised volatility.
> Built on 26 years of S&P 500 data (2000–2026).
> a confidence score, and a complete visualisation suite.

---

## The Core Idea

Most quantitative models try to predict **where** the market will go. This framework answers
a different and more tractable question:

**What kind of environment is the market operating in right now?**

Markets cycle through structurally different states. A calm uptrend, a fragile rally, a quiet
deterioration before a crash, and outright panic are not just different in degree, they are
different in kind. Risk premia, drawdown profiles, correlation structures, and the right
portfolio behaviour all change depending on which state you are in.

This framework detects those states in real time from price data alone.

---

## Live Signal — As of 2026-03-05

```
Regime    : RISK_ON_FRAGILE
Trend     : UP      │  Price is above the 200-day moving average
Volatility: MEDIUM  │  Realised volatility in the middle tercile
Confidence: 88.8%   │  Signal well-established; not a borderline call
```

*Interpretation: The uptrend is intact but stress is building. Maintain risk exposure
with tighter controls. Do not add to positions until volatility resolves lower.*

---

## The Six Regimes

| Regime | Trend | Volatility | Character | Days* | Ann. Return | Sharpe |
|---|---|---|---|---|---|---|
| 🟢 **RISK\_ON** | UP | LOW | Calm uptrend; shallow drawdowns; risk-taking structurally rewarded | 1,962 (30.7%) | +3.9% | 0.35 |
| 🟡 **RISK\_ON\_FRAGILE** | UP | MEDIUM | Trend intact; stress rising; asymmetric downside risk | 1,989 (31.2%) | +11.7% | 0.88 |
| 🟣 **BULL\_EXPANSION** | UP | HIGH | High-vol rally; late-cycle or post-crisis recovery | 598 (9.4%) | +24.1% | 1.46 |
| ⚫ **NEUTRAL** | FLAT | ANY | Price near MA; no dominant signal; reduce exposure | — | — | — |
| 🟠 **RISK\_OFF\_TRANSITION** | DOWN | LOW/MED | Quiet de-risking; the regime investors underestimate most | 340 (5.3%) | −10.2% | −0.52 |
| 🔴 **RISK\_OFF** | DOWN | HIGH | Forced selling; deleveraging; capital preservation only | 1,494 (23.4%) | −1.1% | −0.04 |

*\*Days and statistics: SPY, Oct 2000 – Mar 2026 (6,383 trading days).*

> **On the RISK\_ON return:** The 3.9% aggregate figure is a known statistical artefact of
> computing returns over 1,962 non-consecutive fragmented days spanning 26 years. When broken
> into coherent calendar sub-periods, RISK\_ON produces Sharpe ratios of 0.64–2.18 among
> the best risk-adjusted performance of any regime. The correct metrics here are
> **Sharpe ratio** and **max drawdown (−22.3%)**, not raw return.
> Full explanation in the [model manual](Model_Manual.pdf).

---

## Validation Against Known Market Events

The most important test for any regime model is whether it correctly classifies periods
history has already judged. No parameters were tuned to these outcomes.

| Year | Event | Model Output | Verdict |
|---|---|---|---|
| 2008 | Global Financial Crisis | 217d RISK\_OFF, 36d RISK\_OFF\_TRANSITION | Nearly the entire year correctly risk-off |
| 2017 | Quietest bull market in SPY history | 251d RISK\_ON — the full year, uninterrupted | 100% RISK\_ON, zero noise |
| 2020 | COVID crash + violent recovery | 57d RISK\_OFF → BULL\_EXPANSION → RISK\_ON\_FRAGILE | Captures both crash and recovery |
| 2022 | Fed rate-hike bear market | 199d RISK\_OFF, 29d BULL\_EXPANSION (bounces) | Predominantly risk-off through the drawdown |

---

## How It Works

### Step 1 — Features (`features.py`)

All inputs are derived from daily closing prices. No external data, no analyst estimates.

| Feature | Formula | Role |
|---|---|---|
| Log return | `r_t = log(P_t / P_{t-1})` | Input for volatility computation |
| Realised vol (20d) | `σ = sqrt(252) × std(r_{t-19:t})` | Volatility state variable |
| 200-day MA | `MA = mean(P_{t-199:t})` | Long-term trend proxy (~1 business year) |
| Trend distance | `(P_t − MA) / MA` | Trend conviction; feeds confidence score |

### Step 2 — State Variables (`method1.py`)

**Trend state** — price position relative to the 200-day MA:

- `UP` if price > MA · `DOWN` if price < MA · `NEUTRAL` if price ≈ MA

**Volatility state** — realised vol discretised using quantile thresholds estimated
**exclusively on the 2000–2020 calibration window** and applied as fixed constants to all
data, including the out-of-sample period. Zero look-ahead.

- `LOW` (≤ 33rd pct) · `MEDIUM` (33rd–66th pct) · `HIGH` (> 66th pct)
- Smoothed with a **5-day rolling majority vote** to suppress threshold-boundary flicker

### Step 3 — Regime Classification

A 3×2 grid maps every (trend state, vol state) pair to a named regime:

```
               VOL: LOW           VOL: MEDIUM        VOL: HIGH
Trend: UP    → RISK_ON            RISK_ON_FRAGILE    BULL_EXPANSION
Trend: DOWN  → RISK_OFF_TRANS.    RISK_OFF_TRANS.    RISK_OFF
Trend: FLAT  → NEUTRAL            NEUTRAL            NEUTRAL
```

### Step 4 — Persistence Filter

A candidate regime must appear on **3 consecutive days** before it is accepted.
Until confirmed, the previous regime is carried forward.

Result: **zero regime blocks shorter than 3 days** across 281 total blocks and 6,383 trading
days. The filter is strictly backward-looking — no look-ahead.

### Step 5 — Confidence Score

A composite `[0, 1]` score measuring how clearly the market is expressing the current regime:

```
Confidence = 0.4 × TrendScore + 0.3 × VolScore + 0.3 × DurationScore
```

| Component | Weight | What it measures |
|---|---|---|
| TrendScore | 40% | Distance of price from MA, normalised at 5% threshold |
| VolScore | 30% | How far vol sits from the nearest classification boundary |
| DurationScore | 30% | Regime persistence — saturates at 20 consecutive days |

All thresholds are calibration-period constants. Out-of-sample data never re-enters the formula.

---

## Regime Transition Probabilities

On any given day, the empirical probability of staying in or leaving the current regime
(computed from 6,383 days of data):

| From \ To | RISK\_ON | RISK\_ON\_FRAG | BULL\_EXP | RISK\_OFF\_TRANS | RISK\_OFF |
|---|---|---|---|---|---|
| **RISK\_ON** | **96%** | 3% | 0% | 0% | 0% |
| **RISK\_ON\_FRAGILE** | 4% | **95%** | 1% | 1% | 0% |
| **BULL\_EXPANSION** | 0% | 5% | **93%** | 0% | 2% |
| **RISK\_OFF\_TRANSITION** | 0% | 3% | 1% | **91%** | 5% |
| **RISK\_OFF** | 0% | 0% | 1% | 1% | **98%** |

Two things stand out. First, **RISK\_ON never transitions directly to RISK\_OFF (0%)** the
market always deteriorates through intermediate regimes first, giving time to act.
Second, RISK\_OFF\_TRANSITION → RISK\_OFF runs at 5% per day, quiet and underestimated,
but compounding quickly over a two-to-three week horizon.

---

## Outputs

**Terminal — live signal, last 5 trading days**
```
2026-03-05 | RISK_ON_FRAGILE      | Trend: UP      | Vol: MEDIUM | Conf: [█████████████████░░░] 88.8%
```

**Charts — 6 visualisations generated on every run**

| Chart | What it shows |
|---|---|
| Main regime chart | 26-year price history with colour-coded regime backgrounds and 200-day MA |
| Regime timeline heatmap | Single-band regime sequence from 2000 to present with correct year labels |
| Confidence overlay | Price with confidence score on secondary axis; drops sharply at every transition |
| Performance dashboard | 2×2 grid: annualised return, Sharpe ratio, max drawdown, time allocation |
| Current regime card | Today's regime, trend, vol state, and confidence at a glance |
| Transition matrix | Empirical heatmap of regime-to-regime daily transition probabilities |

**CSV exports — written on every run**

| File | Contents |
|---|---|
| `regime_history.csv` | Day-by-day: price, trend state, vol state, regime, confidence |
| `regime_statistics.csv` | Per-regime: annualised return, volatility, Sharpe ratio, max drawdown, observations |

---

## Project Structure

```
regime-detection/
├── data.py                   # Downloads and validates price data via yfinance
├── features.py               # Log returns, 20d realised vol, 200d MA, trend distance
├── method1.py                # Core engine: discretisation, classification, persistence, confidence
├── analytics.py              # Per-regime performance statistics and bar charts
├── plotting.py               # All six visualisation types
├── run.py                    # End-to-end pipeline; accepts ticker as CLI argument
├── requirements.txt
├── README.md
└── Method1_Model_Manual.pdf  # Model documentation
```

---

## Design Principles

**No look-ahead bias.** Volatility thresholds are estimated on 2000–2020 in-sample data only
and stored as fixed constants. The out-of-sample period never influences any parameter.

**No machine learning.** Classification is fully deterministic and inspectable. Every regime
assignment on every day traces directly to the underlying price and volatility values.

**No external data.** The only input is a daily closing price series.

**Extensible by design.** The regime label and confidence score are clean scalar outputs
on every trading day — direct inputs for portfolio overlays, position sizing rules,
or higher-level quantitative models.

---

## Limitations

**Lagging by construction.** The 200-day MA and 20-day vol window are backward-looking.
The 3-day persistence filter adds a further minimum 2-day delay. Regime changes are confirmed
after the fact, not predicted in advance.

**Fixed calibration window.** Thresholds reflect SPY's volatility distribution from 2000–2020.
If the structural volatility of the market shifts materially, periodic recalibration is advisable.

**Single-asset calibration.** Designed for a broad equity index ETF. Applying to individual
stocks, fixed income, or commodities requires recalibrating the volatility thresholds.

**Gross Sharpe ratios.** No risk-free rate is deducted. Subtract the prevailing short rate
to compute excess-return Sharpe ratios (reduces all figures by roughly 0.2–0.5, depending
on the interest rate environment).

**No transaction costs.** Backtest statistics assume frictionless execution.

---

## Documentation

[`Method1_Model_Manual.pdf`](Method1_Model_Manual.pdf) is a complete technical reference
covering every design decision from first principles: the mathematics of each feature,
the economic rationale for every parameter choice, the look-ahead bias problem and how it
is avoided, the RISK\_ON return paradox with full sub-period analysis, crisis-year validation,
transition matrix interpretation, and an honest accounting of all limitations.
Written to be defensible as a standalone document.
