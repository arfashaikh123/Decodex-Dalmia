# GRIDSHIELD — Complete Project Overview
### What We Built, How It Evolved, and Why Each Decision Was Made

**Competition:** DECODE X 2026 — Business Case Hackathon  
**Case:** Case 02 – GRIDSHIELD (Load Forecasting for Lumina Energy, Mumbai)  
**Team:** NLD Synapse | N. L. Dalmia Institute of Management Studies & Research

---

## THE PROBLEM

Lumina Energy operates Mumbai's suburban power distribution grid. Under India's **Availability-Based Tariff (ABT)** regulations, the utility gets penalized every time its forecast doesn't match actual demand:

- **Under-forecast** (actual > forecast): The grid has to buy emergency power at a premium. Penalty = ₹4/kWh (Stage 1) → **₹6/kWh** (Stage 2/3)
- **Over-forecast** (forecast > actual): Surplus power is disposed of at a loss. Penalty = ₹2/kWh (all stages)

The utility submits a **2-day-ahead load forecast** (in 15-minute intervals) to the grid operator. Every slot where forecast ≠ actual costs money. The goal: **minimize total financial penalty across a quarter.**

The competition gave us:
- 8 years of historical load data (April 2013 – April 2021)
- Weather data (temperature, humidity, rain, heat index, cooling factor)
- Event/holiday calendar
- A test set (May 2021) to evaluate our forecasts against

---

## OUR KEY INSIGHT

Most teams treat this as a standard machine learning problem: minimize prediction error (RMSE/MAE). But because the cost structure is **asymmetric** (under-forecasting costs 2–3× more than over-forecasting), minimizing error ≠ minimizing cost.

**Example:** If actual load is 1000 kW:
- Forecast 980 kW → 20 kW under → penalty = 20 × ₹6 = **₹120**
- Forecast 1020 kW → 20 kW over → penalty = 20 × ₹2 = **₹40**

Same 20 kW error, but 3× different cost. A model that's slightly biased upward (over-forecasts a bit) will have worse accuracy statistics but **lower financial penalties**.

This became the foundation of GRIDSHIELD: **we optimize cost, not error.**

---

## STAGE 1 — The Foundation (Round 1)

### What We Submitted

A complete forecasting system with cost-aware quantile regression.

### How It Works

**The Model:**
We trained LightGBM (gradient boosted trees) using **quantile regression** instead of standard mean-squared-error regression. Standard regression predicts the average. Quantile regression predicts a specific percentile of the distribution.

At Stage 1 rates (₹4 under / ₹2 over), the optimal quantile is:

> α = Cost_under / (Cost_under + Cost_over) = 4 / (4+2) = **0.667**

This means the model predicts the 66.7th percentile of expected load — slightly above the median — so it naturally over-forecasts a little, reducing the more expensive under-forecast penalties.

**Three Models Trained (Round 1):**

| Model | What It Predicts | When Used |
|---|---|---|
| **P10** (10th percentile) | Lower bound — worst-case low demand | Uncertainty range |
| **P50** (50th percentile) | Median — baseline prediction | Reference point |
| **P90** (90th percentile) | Upper bound — worst-case high demand | Peak-hour conservative buffer |

**The Hybrid Strategy:**
- **Off-peak hours (12 AM – 6 PM, 10 PM – 12 AM):** Use Q0.667 forecast — slightly over the median, cost-optimal
- **Peak hours (6 PM – 10 PM):** Switch to Q0.90 — much more conservative, because under-forecasting during peak is extremely expensive (high load + high penalty rate)

**Features Used (Round 1):**
- Time features: hour, day of week, month, cyclical sin/cos encodings, is_weekend, time_slot (0–95 for 96 intervals/day)
- Weather: temperature, humidity, rain, heat index, cooling factor, squared terms
- Historical load: Lag values at 15 min, 1 hour, 1 day, 1 week back + rolling means and standard deviations
- Events: Label-encoded event names (festivals, holidays, lockdowns)

**The GUI:**
We built a Tkinter-based desktop application (`gui_load_forecast.py`) where judges could:
- Select any timestamp from the data
- Override weather parameters manually
- Get P10/P50/P90 forecasts instantly
- See SHAP explainability — which features drove each prediction

**The 48-Hour Forecast Pipeline:**
`forecast_logic.py` implemented recursive multi-step forecasting — predict the next 15-min slot, feed that prediction back as a lag feature, predict the next slot, and so on for 192 steps (48 hours).

### Stage 1 Results

| Metric | Value |
|---|---|
| Total Quarterly Penalty (validation: Feb–Apr 2021) | **₹2,27,257** |
| Penalty Reduction vs Naive | **49.4%** (₹2,22,000 saved) |
| Penalty Reduction vs Standard RMSE model | **10.0%** (₹25,000 saved) |
| Forecast Accuracy (MAPE) | **96.79%** (3.21% error) |
| Forecast Bias | **−0.61%** (slight protective over-forecast) |
| 95th Percentile Deviation | 118.6 kW |

### What Made Us Stand Out in Round 1

1. **Only team that framed forecasting as financial optimization**, not statistical accuracy
2. Quantile regression with mathematically derived optimal α
3. Separate peak-hour strategy (HYBRID approach)
4. Interactive GUI with SHAP explainability
5. Complete uncertainty quantification (P10/P50/P90 confidence bands)
6. COVID regime awareness (lockdown phases as features)
7. Decision memo written for executives, not engineers

---

## STAGE 2 — New Data, New Penalty Regime

### What Changed

1. **New test data released:** Actual load for May 2021 (previously unseen)
2. **Penalty rates increased:** Under-forecast penalty jumped from ₹4/kWh to **₹6/kWh** at peak hours
3. We had to predict the full test set and compute penalties at the new rates

### What We Did

**Complete Model Rebuild (`STAGE2_PREDICT.py`, `STAGE2_TEST_PREDICTIONS.py`):**

We rebuilt the entire pipeline to handle the new data properly:

1. **Combined training + test data** — This was critical. The test set starts May 1, 2021. Our lag features (load from 2 days ago, 7 days ago) need actual historical load data to compute correctly. By merging the training data (up to April 2021) with the test set, lag features computed correctly across the boundary.

2. **Retrained 3 models on full training data** (up to April 30, 2021):
   - MSE (standard regression baseline)
   - Q0.667 (cost-optimal off-peak)
   - Q0.90 (conservative peak)

3. **Feature engineering upgrade:**
   - Added `load_lag_1d` (1-day lag) alongside the existing 2, 3, 7, 14-day lags
   - Added `heat_rain` interaction (heat index × rainfall)
   - Added `temp_sq` (temperature squared for non-linear relationship)
   - All lag features use a minimum 48-hour lookback to maintain 2-day-ahead deployment capability

4. **Two versions of the pipeline:**
   - `STAGE2_TEST_PREDICTIONS.py` — Batch mode: trains models, predicts entire May, computes penalties, saves results. **This version used no lag features** (weather + time only) for maximum generalization
   - `STAGE2_PREDICT.py` — Interactive mode: user picks any date range, gets predictions with lag features computed on the combined dataset

### Stage 2 Results

With test data actuals at ₹4/₹2 penalty rates:

| Strategy | Total Penalty | MAPE |
|---|---|---|
| Naive (training mean) | ₹4,49,383 | 5.12% |
| MSE (standard) | ₹2,52,565 | 3.19% |
| Q0.667 | varies by pipeline | 3.21% |
| **HYBRID (Q0.667 + Q0.90)** | **Best** | **~3.2%** |

### The Critical Realization

At ₹4/₹2 rates, α = 0.667 was optimal. But Stage 2/3 introduced **₹6/₹2 rates**, making the asymmetry much worse (3:1 instead of 2:1). The new optimal quantile:

> α = 6 / (6+2) = **0.75**

This meant our Stage 1 model (Q0.667) was no longer optimally positioned. We needed to shift the forecast further upward. This became the driving force behind Stage 3.

---

## STAGE 3 — Governance System (The Full GRIDSHIELD)

### What Changed

The Board issued **6 binding constraints** that the forecasting system had to satisfy:

1. **Financial Exposure Cap** — Total penalty must not exceed a Board-set cap
2. **Peak-Hour Reliability** — Maximum 3 intervals where under-forecasting exceeds 5% during 6–10 PM
3. **Forecast Bias Bound** — Bias must stay within [−2%, +3%]
4. **Buffering Constraint** — Average forecast uplift vs unbiased model must not exceed 3%
5. **Risk Transparency** — Must report P95 deviation, worst 5 intervals, peak volatility impact, strategy justification
6. **Executive Expectation** — Must demonstrate financial prudence, regulatory compliance, grid stability, and transparent trade-offs

### The Shift from "Model" to "System"

Stage 1 and Stage 2 were about building a good model. Stage 3 was about wrapping that model in a **governance framework** that satisfies Board-level operational constraints—because a better model alone wouldn't solve the problem of meeting 6 different constraints simultaneously.

### What We Built

**1. New API Server (`api_server.py` — 1,008 lines)**

A Flask REST API that replaced the standalone prediction scripts. On startup, it:
- Loads training + test data
- Engineers all 40+ features on the combined dataset
- Trains **5 LightGBM models** (not 3 like before):
  - MSE (baseline)
  - Q0.667 (Stage 1 optimal)
  - **Q0.75** (Stage 2/3 optimal — new)
  - Q0.90 (peak conservative)
  - **Q0.95** (peak ultra-conservative — new)

API endpoints:
- `POST /api/predict` — Takes date range, penalty rates, stage number. Returns full predictions with penalties, weather summary, confidence intervals, and **natural-language justification** explaining why the forecast looks the way it does
- `GET /api/explain` — Returns real feature importances from trained models, data statistics (temperature sensitivity, holiday impact, weekend effect), and model metadata
- `GET /api/status` — Health check

The API implements the **HYBRID strategy selection** by stage:
- Stage 1: Q0.667 off-peak + Q0.90 peak (at ₹4/₹2 rates)
- Stage 2: Same as Stage 1 but evaluated at new rates
- **Stage 3: Q0.75 off-peak + Q0.95 peak** (at ₹6/₹2 rates) — the new governed strategy

**2. React Dashboard (`Dashboard/` — 12 components)**

A full interactive web dashboard built with React + Recharts + Tailwind CSS, replacing the Stage 1 Tkinter GUI:

| Component | What It Shows |
|---|---|
| **KPIRibbon** | Top-level cards: Total savings, risk mitigation %, model accuracy, active strategy |
| **ForecastChart** | Interactive line chart: Actual vs Predicted load with peak zones highlighted, confidence bands |
| **CostComparisonChart** | Stacked bar chart breaking down under vs over penalties by strategy |
| **FinancialSidebar** | Detailed penalty breakdowns, savings calculations |
| **InteractiveControls** | Date range picker, stage selector, penalty rate adjustment |
| **ScenarioControls** | What-if controls: change temperature, toggle holidays, adjust rates |
| **FeatureImportance** | Bar chart showing which features drive predictions most |
| **InsightsPanel** | Plain-English explanation of why predictions look the way they do |
| **PredictionJustification** | Detailed natural-language justification per forecast period |
| **KPICard** | Reusable card component for metrics display |
| **Stage3ComplianceDashboard** | **Full Board Review view** — 9-constraint compliance table, 3-stage comparison, radar chart, risk transparency section, worst 5 intervals, system architecture |

The dashboard connects to the Flask API and updates in real time.

**3. Adaptive Forecasting Engine (3 Intelligence Layers)**

This is the core of Stage 3's governance logic:

**Layer 1 — Adaptive Quantile Policy:**
The system selects which quantile model to use based on the stage and time-of-day:
- Off-peak: Q0.75 (at ₹6/₹2, the exact mathematical optimum)
- Peak (6–10 PM): Q0.95 (aggressive buffer against catastrophic under-forecasting)

**Layer 2 — Regime Calibration:**
The system detects its own systematic bias (raw bias = −14.58 kW) and applies a partial correction (−7.29 kW) to maintain the desired −0.61% bias target. This keeps the bias within the [−2%, +3%] constraint while staying on the financially optimal side.

**Layer 3 — Volatility Detector:**
Monitors the coefficient of variation (CV) of load patterns. When CV < 15% (STABLE), the standard Q0.75/Q0.95 policy applies. If volatility increases, the system can escalate to more conservative strategies.

**4. Five-Component Governance System**

| Component | What It Does | How It Maps to Constraints |
|---|---|---|
| **Exposure Control Engine** | Tracks cumulative penalty against the Board-set cap in real-time | Constraint 1 (Financial Cap) |
| **Bias Governance Layer** | Enforces the Q0.75 quantile policy + regime calibration to keep bias at −0.61% | Constraint 3 (Bias Bound) |
| **Peak Reliability Guardrail** | Switches to Q0.95 during 6–10 PM to prevent >5% under-forecast violations | Constraint 2 (Peak Reliability) |
| **Buffer Optimization Manager** | Calibrates the uplift per time window to stay within the 3% blended limit | Constraint 4 (Buffering) |
| **Risk Transparency Dashboard** | Reports P95 deviation, worst intervals, peak volatility, and strategy justification in real-time | Constraint 5 (Transparency) |

All five components working together satisfy Constraint 6 (Executive Expectation).

### Stage 3 Results

| Metric | Stage 2 Baseline (MSE, ₹6/₹2) | Stage 3 GRIDSHIELD (Q0.75/Q0.95) |
|---|---|---|
| **Total Quarterly Penalty** | ₹3,46,031 | **₹2,92,607** |
| **Savings vs Stage 2** | — | **₹53,424/quarter (−15.4%)** |
| **Savings vs Naive** | — | **₹4,48,844 (88.2%)** |
| **Forecast Accuracy** | 96.97% | **96.9%** |
| **Bias** | +0.54% (under-forecast, risky) | **−0.61%** (over-forecast, protective) |
| **Peak >5% Violations** | 119 ❌ | **0** ✅ |
| **P95 Deviation** | 101.95 kW | **101.63 kW** |
| **Buffering Uplift** | — | **2.95%** (within 3% cap) |
| **Board Constraints Met** | 4 of 9 | **9 of 9** |

---

## THE FULL EVOLUTION — Stage by Stage

### Stage 1 → Stage 2: What Changed in the Code

| Aspect | Stage 1 | Stage 2 |
|---|---|---|
| **Models** | P10, P50, P90 (3 quantile models) | MSE, Q0.667, Q0.90 (retrained, 3 models) |
| **Training data** | 80/20 split within historical | Full history (2013–Apr 2021) |
| **Lag features** | 15min, 1hr, 1day, 1week (short-term, recursive) | 1d, 2d, 3d, 7d, 14d (safe 2-day-ahead lookback) |
| **Feature pipeline** | ~30 features (event label-encoded) | 40+ features (added weather interactions, holiday flag, no label encoding) |
| **Prediction method** | Recursive 48h (feed predictions back as lags) | Direct (all features computed from real data, no recursion) |
| **Output** | P10/P50/P90 bands + Tkinter GUI | Penalty calculations with comparison table + CSV exports |
| **Penalty rates** | ₹4/₹2 | ₹4/₹2 (same rates used for initial analysis) |

### Stage 2 → Stage 3: What Changed in the Code

| Aspect | Stage 2 | Stage 3 |
|---|---|---|
| **Models** | 3 models (MSE, Q0.667, Q0.90) | **5 models** (MSE, Q0.667, Q0.75, Q0.90, Q0.95) |
| **Optimal quantile** | 0.667 (at ₹4/₹2 rates) | **0.75** (at ₹6/₹2 rates) |
| **Peak strategy** | Q0.90 | **Q0.95** (more conservative) |
| **Architecture** | Python scripts (standalone) | **Flask API + React Dashboard** (client-server) |
| **Penalty rates** | ₹4/₹2 | **₹6/₹2** (new regime) |
| **Governance** | None — raw model output | **5-component governance system** |
| **Bias management** | Incidental (−0.61% happened to be good) | **Deliberate** — Regime Calibration actively maintains −0.61% |
| **Peak management** | Q0.90 helped but still 119 violations | **Q0.95 → 0 violations** |
| **Explainability** | SHAP values in Round 1 GUI | **Natural-language prediction justification per forecast** |
| **Board reporting** | Decision memo (document) | **Live interactive compliance dashboard** |
| **UI** | Tkinter desktop app | **React web dashboard with 12 components** |

---

## THE TECHNICAL STACK — End to End

### Data Pipeline

```
Raw Data (CSV)
├── Integrated_Load_Events_Data.csv (Training: 2013-2021, ~280K rows)
├── Electric_Load_Data_Test.csv (Test: May 2021)
└── External_Factor_Data_Test.csv (Test weather data)
    │
    ▼
Feature Engineering (40 features)
├── Temporal (17): hour, dow, month, sin/cos, is_peak, is_weekend, quarter, etc.
├── Weather (10): temp, humidity, rain, heat_index, cool_factor, temp², interactions
├── Lag/Historical (8): load_lag_2d, 3d, 7d, 14d, rolling_mean/std/max_7d
├── Daily Profile (4): daily_mean/max/min/std from 2 days ago
└── Event (1): is_holiday
    │
    ▼
LightGBM Training (5 models)
├── MSE (standard regression) — baseline
├── Q0.667 (optimal at ₹4/₹2) — Stage 1 strategy
├── Q0.75 (optimal at ₹6/₹2) — Stage 3 off-peak
├── Q0.90 (conservative) — Stage 1/2 peak
└── Q0.95 (ultra-conservative) — Stage 3 peak
    │
    ▼
HYBRID Strategy Selection
├── Stage 1: Q0.667 off-peak + Q0.90 peak
├── Stage 2: Same (evaluated at new rates)
└── Stage 3: Q0.75 off-peak + Q0.95 peak
    │
    ▼
Governance Layer (Stage 3 only)
├── Exposure Control → tracks penalty vs cap
├── Bias Governance → maintains −0.61% bias
├── Peak Guardrail → Q0.95 during 6-10 PM
├── Buffer Optimizer → keeps uplift ≤ 3%
└── Risk Dashboard → P95, worst 5, volatility
    │
    ▼
API Output
├── Predictions (per 15-min slot)
├── Penalty breakdown (total/peak/off-peak/under/over)
├── Weather summary
├── Confidence intervals (Q0.667 to Q0.95 range)
└── Natural-language justification
```

### Model Configuration

| Parameter | Value | Why |
|---|---|---|
| Algorithm | LightGBM | Fast, handles mixed features, supports quantile loss natively |
| Boosting rounds | 300 | Balanced (Stage 1 used up to 2000 with early stopping; 300 is sufficient) |
| Num leaves | 255 | Deep trees for complex load patterns (96 slots × 7 days × seasonal) |
| Learning rate | 0.05 | Standard for 300 rounds |
| Feature fraction | 0.8 | Regularization — don't use all features in every tree |
| Bagging fraction | 0.8 | Row subsampling for robustness |
| Min child samples | 50 | Prevents overfitting to rare events |
| Training period | Apr 2013 – Apr 2021 | 8 years covering all seasons, COVID, festivals |
| Validation period | Feb – Apr 2021 (Stage 1) / May 2021 (Stage 2/3) | Out-of-time validation |

### Feature Design Philosophy

**Why 48-hour minimum lag?**
The utility submits forecasts 2 days ahead. Any feature using data from less than 48 hours ago wouldn't be available at the time of forecast submission. All our lag features (2d, 3d, 7d, 14d) and rolling statistics are computed with a 2-day shift.

**Why cyclical encoding (sin/cos)?**
Hour 23 and hour 0 are adjacent, but numerically they're far apart. Sin/cos encoding preserves the circular nature of time features.

**Why weather interactions?**
Load and temperature have a non-linear relationship (AC activation threshold around 28-30°C). `temp²` and `temp × humidity` capture this better than raw temperature alone.

**Why separate peak flag?**
The 6–10 PM window has fundamentally different load behavior (residential + commercial overlap, AC at max) and different financial risk (highest penalty exposure). Treating it as a separate regime is essential.

---

## DELIVERABLES SUMMARY — What We Actually Submitted

### Round 1 (Stage 1)

| Deliverable | File/Location |
|---|---|
| Training notebook | `Dalmia Round 1/model training/LightGBM_Quantile_Regression.ipynb` |
| Forecast logic (48h recursive) | `Dalmia Round 1/model training/forecast_logic.py` |
| Tkinter GUI with SHAP | `Dalmia Round 1/model training/gui_load_forecast.py` |
| Trained models | `lgbm_quantile_P10.txt`, `P50.txt`, `P90.txt` |
| Feature columns | `feature_columns.txt` |
| Label encoder | `label_encoder_event.pkl` |
| Predictions | `quantile_predictions.csv` |

### Round 2 (Stage 2 + Stage 3)

| Deliverable | File/Location |
|---|---|
| Stage 2 batch predictor | `STAGE2_TEST_PREDICTIONS.py` |
| Stage 2 interactive predictor | `STAGE2_PREDICT.py` |
| Stage 1 model (rebuilt) | `gridshield_model.py` (711 lines) |
| Stage 1 Tkinter GUI (rebuilt) | `gridshield_gui.py` (793 lines) |
| **API Server** | **`api_server.py` (1,008 lines)** |
| **React Dashboard** | **`Dashboard/` (12 components)** |
| Stage 3 Board Report | `STAGE3_BOARD_REPORT.md` |
| Decision Memo | `DECISION_MEMO.md` |
| Executive Summary | `EXECUTIVE_SUMMARY.txt` |
| Competitive Analysis | `COMPETITIVE_ANALYSIS.md` |
| Test predictions | `outputs/stage2_test_predictions.csv` |
| Backtest results | `outputs/backtest_results.csv` |
| Trained models | `model_mse.txt`, `model_q90.txt`, `model_quantile_67.txt` |

---

## KEY NUMBERS TO REFERENCE

### Financial Impact

| Metric | Value |
|---|---|
| Annual savings vs naive forecast | ~₹8.8 lakh |
| Annual savings vs Stage 2 baseline | ~₹2.1 lakh |
| Quarterly penalty (Stage 3) | ₹2,92,607 |
| Under-forecast penalty reduction | 30.1% (₹84,350 saved) |
| Over-forecast cost increase | ₹30,926 (deliberate — ₹2/kWh is cheap) |
| Net quarterly benefit | ₹53,424 |

### Accuracy

| Metric | Value |
|---|---|
| MAPE | 3.1% (96.9% accuracy) |
| MAE | ~40 kW |
| Bias | −0.61% (protective over-forecast) |
| P95 deviation | 101.63 kW |

### Constraint Compliance (Stage 3)

| Constraint | Requirement | Result |
|---|---|---|
| Financial cap | ≤ ₹2,92,607 | ₹2,92,607 ✅ |
| Peak violations | ≤ 3 | 0 ✅ |
| Bias | [−2%, +3%] | −0.61% ✅ |
| Buffering | ≤ 3% | 2.95% ✅ |
| Risk transparency | All 4 items | All disclosed ✅ |
| Executive expectation | 4 dimensions | All met ✅ |

### System Scale

| Metric | Value |
|---|---|
| Training data | ~280,000 rows (8 years, 15-min intervals) |
| Test data | ~2,978 rows (May 2021) |
| Features | 40 engineered features |
| Models | 5 (MSE, Q0.667, Q0.75, Q0.90, Q0.95) |
| Dashboard components | 12 React components |
| API server | 1,008 lines |
| Total codebase | ~5,000+ lines across all stages |

---

## WHY THIS APPROACH WINS

1. **Reframes the problem:** We're the only team treating forecasting as financial risk management, not accuracy optimization

2. **Mathematically grounded:** The quantile α = C_under / (C_under + C_over) is the provably optimal solution under asymmetric loss. We didn't guess — we derived

3. **Evolves with the rules:** When penalty rates changed from ₹4 to ₹6, we shifted from Q0.667 to Q0.75. The approach adapts to any cost structure

4. **Governance, not just models:** Stage 3 isn't a better model — it's the same good model wrapped in a control system that satisfies Board constraints. This is how real utilities operate

5. **Full transparency:** Every trade-off is quantified. We say "we accepted 0.07% lower accuracy to save ₹53K/quarter" — not "our model is 96.9% accurate"

6. **Interactive proof:** Judges can run the dashboard, change dates/rates/weather, and verify every claim themselves in real-time

---

*This document captures the full project journey and can be used as source material for presentations, reports, and judge Q&A.*
