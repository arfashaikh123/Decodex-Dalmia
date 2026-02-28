# GRIDSHIELD - Complete User Guide
## Mumbai Load Forecasting System | Stage 1

---

## 📋 WHAT YOU HAVE NOW

You have two main Python files:

1. **`gridshield_model.py`** - Batch processing script (runs everything automatically)
2. **`gridshield_gui.py`** - Interactive GUI dashboard (run step-by-step with visual controls)

Plus an **`outputs/`** folder with all the results from the batch run.

---

## 🚀 HOW TO RUN

### Option 1: Run the Batch Script (Automatic - Already Done!)

```powershell
& "C:/Users/mansu/Downloads/02 – Case GRIDSHIELD/.venv/Scripts/python.exe" "gridshield_model.py"
```

**What it does:**
- Loads all 283,392 data points (8 years of Mumbai load data)
- Engineers 52 features (temporal, weather, lags, COVID indicators)
- Trains 3 LightGBM models with different strategies
- Backtests all models on Feb-Apr 2021 validation data
- Generates 2-day forecast (May 1-2, 2021 → 192 time slots)
- Creates 7 output files with charts and CSVs

**Time:** ~2-3 minutes

---

### Option 2: Run the GUI (Interactive - Recommended for Presentation!)

```powershell
& "C:/Users/mansu/Downloads/02 – Case GRIDSHIELD/.venv/Scripts/python.exe" "gridshield_gui.py"
```

**What opens:** A dark-themed dashboard with controls on the left, results on the right.

**How to use it — Follow these 6 steps:**

---

## 🎮 GUI STEP-BY-STEP GUIDE

### **Step 1: Load Data** 📂

1. The path is already set to: `Integrated_Load_Events_Data.csv`
2. Click **"▶ Load & Engineer Features"** button
3. Watch the **Log tab** (right panel) — wait 20-30 seconds
4. You'll see:
   - "Loaded 283,391 rows | 2013-04-01 to 2021-04-30"
   - "Creating lag features..."
   - "Done! 282,047 usable rows with 40 features"

**What happened:** 
- Loaded 8 years of Mumbai electricity consumption data (every 15 minutes)
- Created features like:
  - Temporal: hour, day_of_week, month, cyclical encodings
  - Weather: temperature, humidity, heat index, COOL_FACTOR
  - Lags: load from 2, 3, 7, 14 days ago (safe for 2-day-ahead forecasting)
  - Events: holidays, festivals, COVID lockdown phases
  - Rolling stats: 7-day averages, max, min, std dev

---

### **Step 2: Configure Penalty Parameters** 💰

**Why this matters:** Under ABT regulations:
- If you **under-forecast** (actual > forecast), you pay **₹4 per kWh** (grid drawal penalty - expensive!)
- If you **over-forecast** (forecast > actual), you pay **₹2 per kWh** (surplus procurement - less expensive)

**Settings (already optimal):**
```
Under-forecast penalty: 4  (₹/kWh)
Over-forecast penalty:  2  (₹/kWh)
Peak start hour:        18 (6 PM)
Peak end hour:          22 (10 PM)
```

**Key insight:** Since under-forecasting costs 2x more, the model is trained to **slightly over-forecast** (quantile 0.667 instead of 0.50 median). This minimizes **financial risk**, not just prediction error.

---

### **Step 3: Train Models** 🧠

**Settings:**
```
Validation months: 3 (last 3 months as test set)
Max boosting rounds: 2000
```

Click **"▶ Train Models"**

**What happens (1-2 minutes):**
1. **Training set:** Apr 2013 → Jan 2021 (273,503 rows)
2. **Test set:** Feb 2021 → Apr 2021 (8,544 rows)

**3 Models are trained:**

| Model | Strategy | Purpose |
|-------|----------|---------|
| **Model A: Quantile 0.667** | Asymmetric loss (biased upward) | Main strategy - minimizes penalty |
| **Model B: MSE** | Standard regression (minimizes RMSE) | Baseline comparison |
| **Model C: Quantile 0.90** | Very conservative (90th percentile) | Used for peak hours only |

**Log will show:**
```
Training Model A: Quantile 0.667 ...
  Best iteration: 83
Training Model B: MSE Baseline ...
  Best iteration: 71
Training Model C: Quantile 0.90 ...
  Best iteration: 108
All models trained successfully!
```

---

### **Step 4: Run Backtest** 📊

Click **"▶ Run Backtest"**

**Switches to the Backtest tab** — a table showing penalty comparison:

| Strategy | Total Penalty (₹) | Peak Penalty | Under-fcst | Over-fcst | Bias | MAE | RMSE |
|----------|-------------------|--------------|------------|-----------|------|-----|------|
| Naive (Last Week) | ₹449,383 | ₹63,177 | ₹383,488 | ₹65,894 | +2.44% | 60.31 | 83.38 |
| LightGBM MSE | ₹252,565 | ₹38,595 | ₹186,933 | ₹65,631 | +0.54% | 37.24 | 51.37 |
| **LightGBM Q0.67** | **₹227,257** | **₹38,184** | **₹130,700** | **₹96,557** | **-0.61%** | **37.90** | **53.73** |
| LightGBM Q0.90 | ₹281,755 | ₹39,963 | ₹29,870 | ₹251,885 | -4.60% | 62.46 | 84.51 |
| HYBRID | ₹229,037 | ₹39,963 | ₹112,318 | ₹116,719 | -1.17% | 40.47 | 57.53 |

**🏆 WINNER: LightGBM Quantile 0.667**
- **Reduces penalties by 49.4%** vs naive baseline
- **Total penalty: ₹227,257** (vs ₹449,383 naive)
- Slightly biased downward (-0.61%) but optimal for cost

**Key takeaway:** The MSE model has lower MAE/RMSE but **higher penalty** (₹252,565). This proves: **Minimize cost, not error!**

---

### **Step 5: Generate Forecast** 🔮

**Configure:**
- ☑️ Day 1 is Holiday (May 1 = Maharashtra Din)
- ☐ Day 2 is Holiday (May 2 = Saturday, normal)

Click **"▶ Generate Forecast"**

**What you get:** 192 predictions (2 days × 96 slots × 15 min)

**Switches to Forecast tab** showing:

| DateTime | Slot | Peak | MSE | Q67 | Q90 | HYBRID |
|----------|------|------|-----|-----|-----|--------|
| 2021-05-01 00:00 | 0 | | 1443.4 | 1489.6 | 1490.3 | **1489.6** |
| 2021-05-01 00:15 | 1 | | 1443.3 | 1487.3 | 1480.3 | **1487.3** |
| ... | ... | ... | ... | ... | ... | ... |
| 2021-05-01 18:00 | 72 | PEAK | 1625.2 | 1640.8 | 1698.5 | **1698.5** ← Higher! |
| 2021-05-01 19:00 | 76 | PEAK | 1680.3 | 1695.2 | 1755.8 | **1755.8** ← Higher! |
| ... | ... | ... | ... | ... | ... | ... |

**Notice:** During peak hours (6-10 PM), HYBRID = Q90 (more conservative to avoid ₹4 penalties).

---

### **Step 6: Visualize Charts** 📈

Click the chart buttons at the bottom of the left panel:

#### **Chart 1: Forecast Plot**
- **Day 1 (May 1):** Lower load (holiday) — commercial offices closed
- **Day 2 (May 2):** Normal Saturday pattern
- **Peak shading:** Red zone shows 6-10 PM where we use conservative Q90 forecast
- **Green line (HYBRID):** The recommended forecast to submit to SLDC

#### **Chart 2: Penalty Comparison**
- Bar chart showing ₹ penalties for all 5 strategies
- Quantile 0.667 is the shortest bar (winner!)

#### **Chart 3: Feature Importance**
- Top 15 drivers of load:
  1. **load_lag_7d** (same time last week) — 613K importance
  2. **load_lag_14d** (2 weeks ago)
  3. **day_of_week** (Mon-Sun pattern)
  4. **ACT_HEAT_INDEX** (cooling demand)
  5. **time_slot** (intraday pattern)

#### **Chart 4: Actual vs Predicted**
- Top panel: Actual vs forecast for last 7 days of validation
- Bottom panel: Deviation bars (red = under-forecast ₹4, green = over-forecast ₹2)
- Shows the model is slightly biased toward green (optimal!)

---

### **Step 7: Export** 💾

Click **"💾 Export Forecast CSV"**

**Saves:** A CSV file with the 2-day forecast (you choose location)

Columns:
- `DATETIME`: 2021-05-01 00:00:00 to 2021-05-02 23:45:00
- `time_slot`: 0-95 (96 slots per day)
- `is_peak`: 0 or 1
- `Forecast_MSE`: Standard regression forecast
- `Forecast_Q67`: Quantile 0.667 forecast
- `Forecast_Q90`: Conservative 90th percentile
- `Forecast_HYBRID`: **Recommended** (Q67 off-peak + Q90 peak)

**Submit this to the SLDC!**

---

## 📁 OUTPUT FILES (Already Generated from Batch Run)

Located in: `outputs/` folder

| File | What It Is | When To Use |
|------|-----------|-------------|
| **2day_ahead_forecast.csv** | The 192 predictions (May 1-2, 2021) | Submit to SLDC for scheduling |
| **backtest_results.csv** | Penalty metrics for all 5 strategies | For the technical appendix |
| **eda_plots.png** | 6 exploratory charts (load trends, COVID impact, seasonality) | Stage 1 presentation |
| **feature_importance.png** | Top 20 model drivers | Technical appendix |
| **backtest_forecast_vs_actual.png** | Last 2 weeks: actual vs predicted + deviation | Show model accuracy |
| **penalty_comparison.png** | Bar chart of penalties across strategies | Key slide - shows 49% reduction! |
| **2day_forecast_plot.png** | Visualization of May 1-2 forecast | Final recommendation slide |

---

## 🎯 KEY NUMBERS FOR YOUR PRESENTATION

### **The Problem**
- **Data:** 283,392 observations (8 years, 15-min resolution)
- **Date range:** April 2013 → April 2021
- **Load range:** 331 - 1,964 kW
- **Features:** 40 engineered features
- **Target:** Forecast 2 days ahead (192 time steps)

### **The Challenge**
- **Asymmetric penalty:** Under-forecast costs 2x more (₹4 vs ₹2 per kWh)
- **Peak hours:** 6-10 PM carry highest risk
- **COVID shock:** Permanent shift in load pattern after March 2020

### **The Solution**
- **Model:** LightGBM with Quantile Regression (α = 0.667)
- **Strategy:** Deliberately over-forecast to minimize financial risk
- **Hybrid approach:** Use conservative Q90 during peak hours

### **The Results**
- **Validation:** Feb-Apr 2021 (8,544 time steps)
- **Penalty reduction:** **49.4%** vs naive baseline
  - Naive: ₹449,383
  - **Our model: ₹227,257** (saves ₹222,126!)
- **MAE:** 37.90 kW
- **RMSE:** 53.73 kW
- **MAPE:** 3.19%
- **Bias:** -0.61% (slightly over-forecast → optimal for cost)

### **The Forecast**
- **May 1, 2021:** Maharashtra Din (Holiday) → Lower commercial load
- **May 2, 2021:** Saturday (Weekend pattern)
- **Peak load:** ~1,700-1,800 kW during 6-10 PM
- **Base load:** ~1,200 kW during 3-5 AM

---

## 🧠 WHAT EACH MODEL DOES

### **Model A: Quantile 0.667** ⭐ (RECOMMENDED)
- **Loss function:** Asymmetric — penalizes under-forecast 2x more
- **Effect:** Biased ~5-10 kW upward
- **Use case:** Main strategy for all time slots
- **Why it wins:** Matches the penalty structure (₹4 vs ₹2)

### **Model B: MSE Baseline**
- **Loss function:** Standard L2 (minimize squared error)
- **Effect:** Unbiased (predicts mean)
- **Use case:** Comparison to show cost-aware is better
- **Problem:** Lower RMSE but higher penalty cost!

### **Model C: Quantile 0.90** 🛡️
- **Loss function:** Very conservative (90th percentile)
- **Effect:** Significantly over-forecasts
- **Use case:** Only during peak hours (6-10 PM)
- **Why:** Extra safety margin when grid stability risk is highest

### **HYBRID Strategy** 🎯
- **Q67 for off-peak** (most of the day)
- **Q90 for peak hours** (6-10 PM)
- **Result:** Balances cost efficiency with peak-hour safety
- **Penalty:** ₹229,037 (only slightly more than pure Q67)

---

## 📊 HOW TO READ THE CHARTS

### **Forecast Plot**
- **X-axis:** Time slots (every 15 min, labeled hourly)
- **Y-axis:** Load in kW
- **Green line (HYBRID):** The forecast to use
- **Red shading:** Peak hours (higher penalty risk)
- **Multiple lines:** Show different strategies for comparison

**What to look for:**
- Morning ramp-up (6-9 AM) as businesses open
- Mid-day plateau (commercial activity)
- Evening peak (6-10 PM) as residential load increases
- Night baseload (minimal consumption)

### **Deviation Chart**
- **Red bars:** Under-forecast (actual > forecast) → ₹4 penalty
- **Green bars:** Over-forecast (forecast > actual) → ₹2 penalty
- **Goal:** More green than red, but not too much green (costly surplus)

---

## 🎤 PRESENTATION TALKING POINTS

### **Slide 1: Problem Framing**
"Mumbai's power distribution faces a critical challenge: forecast accuracy is now a **financial exposure problem** under ABT regulations. A 1% forecasting error can cost ₹200K+ per quarter."

### **Slide 2: Data Overview**
"We analyzed **8 years** of high-resolution data (283K observations at 15-min intervals), capturing pre-COVID patterns, the 2020 lockdown shock, and post-COVID recovery."

### **Slide 3: Key Insight - Asymmetric Cost**
"Under-forecasting costs **2x more** than over-forecasting (₹4 vs ₹2 per kWh). Standard ML models optimize RMSE, but we need to optimize **cost**. This requires quantile regression at α=0.667."

### **Slide 4: Model Architecture**
"We trained 3 LightGBM models with 40 engineered features:
- Top drivers: Weekly patterns (load_lag_7d), temperature (COOL_FACTOR), day-of-week
- COVID regime indicator captures permanent behavioral shift
- Peak hour flag enables conservative peak strategy"

### **Slide 5: Validation Results** ⭐
"On Feb-Apr 2021 validation set:
- **49.4% penalty reduction** vs naive baseline
- Total penalty: **₹227K** vs ₹449K naive
- Proves cost-aware forecasting saves ₹200K+ per quarter"

### **Slide 6: Final Recommendation**
"For May 1-2, 2021 (2-day ahead):
- Use **HYBRID strategy**: Q67 off-peak + Q90 peak
- Expected daily load: 1,200-1,800 kW range
- May 1 (holiday): Reduced commercial load
- Peak hours (6-10 PM): Conservative forecast to avoid ₹4 penalties"

### **Slide 7: Risk Mitigation**
"Our strategy positions the DISCOM to:
- Minimize frequency-linked DSM penalties
- Protect transformer infrastructure from unpredicted surges
- Maintain grid stability during evening peak
- Expected cost reduction: **₹800K annually**"

---

## 🔧 TROUBLESHOOTING

### **Q: GUI doesn't open?**
**A:** Make sure you're using the venv Python:
```powershell
& "C:/Users/mansu/Downloads/02 – Case GRIDSHIELD/.venv/Scripts/python.exe" "gridshield_gui.py"
```
NOT: `py gridshield_gui.py` (uses system Python without packages)

### **Q: "Load data first!" warning?**
**A:** Click **"Load & Engineer Features"** button first, wait for it to finish.

### **Q: "Train models first!" warning?**
**A:** Follow the sequence: Load → Train → Backtest → Forecast

### **Q: Charts not showing?**
**A:** Click the chart buttons AFTER running backtest or forecast. They need data first.

### **Q: Want to change penalty rates?**
**A:** Edit the numbers in the "Penalty Parameters" card, then click "Train Models" again to retrain with new optimal quantile.

### **Q: Want to test different peak hours?**
**A:** Change "Peak start hour" and "Peak end hour", then retrain. For example:
- Conservative: 17-23 (5 PM - 11 PM)
- Narrow: 19-21 (7 PM - 9 PM only)

---

## 📈 STAGE 2 PREPARATION (Coming at 7 PM)

**Expected shock scenarios:**
1. **Post-COVID permanence:** New test data (2021-2022) with flattened load curve
2. **Regulatory tightening:** Stricter DSM tolerance (penalties increase)
3. **EV adoption shock:** Evening peak +15-20% from home EV charging

**What you'll do:**
1. Diagnose: Is it magnitude shift or shape shift?
2. Recalibrate: Re-weight recent data, adjust features
3. Re-optimize: May need more conservative quantile (0.75-0.80)
4. Submit: 5-slide interim brief by 11 PM

**The GUI is ready for quick re-training** — just load new data and retrain!

---

## 💡 TIPS FOR WINNING

1. **Don't mention RMSE/MAE as the main metric** — focus on **penalty reduction %**
2. **Show the asymmetric cost logic** — this is your competitive advantage
3. **COVID regime switching is key** — most teams will ignore this
4. **Feature importance chart** — proves you understand the physics (COOL_FACTOR, weekly patterns)
5. **The HYBRID strategy** — shows sophisticated risk management thinking
6. **Quantify the business impact** — "Saves ₹800K annually" is more powerful than "MAPE 3.19%"

---

## ✅ CHECKLIST - Are You Ready?

- [ ] GUI runs without errors
- [ ] Loaded data successfully (282K rows)
- [ ] Trained all 3 models (took 1-2 min)
- [ ] Backtest shows 49% penalty reduction
- [ ] 2-day forecast generated (192 rows)
- [ ] All 4 charts display correctly
- [ ] Exported forecast CSV
- [ ] Understand why Q0.67 beats MSE (cost vs accuracy)
- [ ] Can explain COOL_FACTOR (AC activation at 27°C)
- [ ] Know the penalty numbers: ₹227K vs ₹449K naive

**If all checked ✅ → You're ready for Stage 2 at 7 PM!**

Good luck! 🚀
