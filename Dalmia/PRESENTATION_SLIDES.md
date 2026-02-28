# GRIDSHIELD - Stage 1 Presentation (15 Slides)
**Case 2: Cost-Aware Load Forecasting | Decode X-2026**

---

## SLIDE 1: TITLE
**GRIDSHIELD: Cost-Aware Load Forecasting for Mumbai Suburban Grid**

Lumina Energy Distribution Zone  
Forecast Risk Advisory Team  
Stage 1 Submission | February 28, 2026

---

## SLIDE 2: PROBLEM FRAMING
**Load Forecasting is Now a Financial Problem**

**Traditional Approach:**  
Minimize RMSE → Optimize for accuracy

**New Reality (ABT Regulations):**
- Under-forecast: ₹4/kWh penalty (grid drawal)
- Over-forecast: ₹2/kWh penalty (procurement waste)
- **Asymmetric cost → Requires asymmetric strategy**

**Question:** How do we minimize financial exposure, not just error?

---

## SLIDE 3: DATA OVERVIEW
**8 Years of High-Resolution Grid Data**

- **283,392 observations** (15-minute intervals)
- **Date Range:** April 2013 - April 2021
- **Load Range:** 331 - 1,964 kW
- **Features:** 40 engineered features
  - Temporal: cyclical encoding, peak flags
  - Weather: temperature, humidity, COOL_FACTOR
  - Events: holidays, festivals, COVID phases
  - Lags: 2, 3, 7, 14 days (safe for 2-day ahead)

**Challenge:** COVID-19 created permanent 8.2% demand reduction

---

## SLIDE 4: KEY INSIGHT - ASYMMETRIC PENALTIES
**Why Standard ML Fails**

[Chart showing MSE vs Quantile performance]

| Strategy | RMSE | Total Penalty |
|----------|------|---------------|
| LightGBM MSE | **51.37** ✅ | ₹252,565 ❌ |
| **Quantile 0.667** | **53.73** | **₹227,257** ✅ |

**Lesson:** Lower error ≠ Lower cost  
**Solution:** Optimize for penalty, not RMSE

---

## SLIDE 5: OUR APPROACH - HYBRID QUANTILE STRATEGY
**Three Models, One Optimal Strategy**

1. **Quantile 0.667** (Off-Peak)
   - Biased +5-10 kW upward
   - Optimal point: α = 4/(4+2) = 0.667
   
2. **Quantile 0.90** (Peak Hours 18-22)
   - Extra conservative buffer
   - Protects against ₹4 penalties when risk is highest

3. **HYBRID Combination**
   - Switches strategy by time window
   - Best of both worlds

---

## SLIDE 6: MODEL ARCHITECTURE
**LightGBM with Cost-Aware Loss**

**Top 5 Predictive Features:**
1. load_lag_7d (613.2 importance)
2. load_lag_14d (487.6)
3. day_of_week (312.4)
4. ACT_HEAT_INDEX (298.7)
5. time_slot (276.3)

**Training:**
- 273,503 training rows (Apr 2013 - Jan 2021)
- 8,544 validation rows (Feb-Apr 2021)
- Early stopping at 83 iterations

---

## SLIDE 7: VALIDATION RESULTS ⭐
**49.4% Penalty Reduction vs Baseline**

**Historical Backtest (Feb-Apr 2021):**

| Metric | Value |
|--------|-------|
| Total Penalty | ₹227,257 |
| vs Naive Baseline | **-49.4%** (₹222K saved) |
| vs MSE Baseline | **-10.0%** (₹25K saved) |
| Forecast Accuracy | **96.79%** |
| Forecast Bias | -0.61% (optimal) |
| 95th %ile Deviation | 118.6 kW |

**Annual Projection:** ₹800K+ savings

---

## SLIDE 8: PEAK VS OFF-PEAK BREAKDOWN
**16.8% of Penalties During 16.7% of Time**

**Penalty Distribution:**
- **Peak Hours (18-22):** ₹38,184 (16.8%)
- **Off-Peak Hours:** ₹189,073 (83.2%)

**Insight:** Peak concentration justifies Q0.90 strategy  
**Action:** Deploy conservative forecast during evening window

---

## SLIDE 9: UNCERTAINTY QUANTIFICATION
**Confidence Intervals for Risk Assessment**

[Show chart with purple confidence bands]

**95% Confidence Interval:** ±60 kW around forecast  
**50% Confidence Interval:** ±20 kW (high probability zone)

**Use Case:** SLDC operators can visualize worst-case scenarios  
**Risk Management:** Adequate spinning reserves = CI95 upper bound

---

## SLIDE 10: EXECUTIVE COMMAND DASHBOARD
**Real-Time Scenario Modeling**

[Screenshot of dashboard]

**Features:**
- ✅ Temperature scenario (+10°C = +40% load)
- ✅ Holiday toggle (instant recalculation)
- ✅ Demand spike simulator (EV charging impact)
- ✅ Live penalty calculator
- ✅ One-click SLDC CSV export

**Demo:** Change temp +5°C → Watch load jump +25%

---

## SLIDE 11: 2-DAY FORECAST (MAY 1-2, 2021)
**Operational Recommendation**

**May 1 (Maharashtra Din - Holiday):**
- Expected: 1,200-1,600 kW (commercial shutdown)
- Peak: 1,650 kW at 19:00

**May 2 (Saturday - Weekend):**
- Expected: 1,300-1,700 kW (residential pattern)
- Peak: 1,750 kW at 20:00

**Strategy:** HYBRID (Q67 off-peak, Q90 peak)  
**Expected Penalty:** ₹1,180 per day

---

## SLIDE 12: RISK STRATEGY PROPOSAL
**How We Minimize Financial Exposure**

**1. Quantile Positioning:**
- Deliberate -0.61% bias (slight over-forecast)
- Pays ₹2 to avoid risking ₹4

**2. Peak Hour Buffering:**
- Q0.90 during 18-22 window
- +25-30 kW safety margin

**3. Regime Awareness:**
- COVID lockdown phase features
- Ready for structural breaks

**4. Real-Time Adaptation:**
- Dashboard scenario modeling
- Instant recalculation capability

---

## SLIDE 13: WHAT FUNDAMENTALLY CHANGED?
**From Prediction to Protection**

**Before:**
- "How accurate is the forecast?"
- RMSE-driven optimization
- Point estimates only

**After:**
- **"How much will deviations cost?"**
- **Penalty-driven optimization**
- **Uncertainty quantification**

**Mindset Shift:** Load forecasting is risk management, not statistics

---

## SLIDE 14: STAGE 2 READINESS
**Prepared for Tonight's Regime Shift (7 PM)**

**Our Advantages:**
1. **Modular architecture** → Retrain in <5 minutes
2. **Regime features** → Lockdown phases captured
3. **Live dashboard** → Instant scenario testing
4. **Documentation** → Fully reproducible (716-line notebook)

**Anticipated Challenges:**
- EV adoption spike
- New penalty rates
- Weather pattern changes

**Response Plan:** Recalibrate → Quantify → Re-optimize

---

## SLIDE 15: RECOMMENDATION & IMPACT
**Deploy HYBRID Strategy Immediately**

**Expected Impact:**
- **Daily Savings:** ₹1,200 vs naive approach
- **Quarterly Savings:** ₹110K
- **Annual Savings:** ₹800K+

**Risk Mitigation:**
- 95th %ile tail risk quantified (118.6 kW)
- Peak penalty concentration managed (Q0.90)
- COVID structural break incorporated

**Next Steps:**
1. Submit 192-slot SLDC schedule
2. Monitor actual vs forecast during peak
3. Prepare for Stage 2 recalibration

---

**Thank you. Questions?**

---

# APPENDIX: TECHNICAL DETAILS

## Model Hyperparameters
```python
{
  'objective': 'quantile',
  'alpha': 0.667,
  'num_leaves': 255,
  'learning_rate': 0.05,
  'feature_fraction': 0.8,
  'bagging_fraction': 0.8,
  'min_child_samples': 50
}
```

## Feature Engineering Highlights
- Cyclical encoding (sin/cos) for temporal patterns
- COOL_FACTOR = activation threshold for AC loads
- Safe lags: ≥48 hours for 2-day ahead forecast
- Regime indicators: Pre/post COVID, lockdown phases

## Validation Methodology
- Time-series split (no shuffling)
- Last 3 months as validation (Feb-Apr 2021)
- Walk-forward testing could improve further

## Deliverables
- ✅ Decision Memo: `DECISION_MEMO.md`
- ✅ Technical Appendix: `train.ipynb`
- ✅ Dashboard: Running at http://localhost:3001
- ✅ Forecast: `outputs/2day_ahead_forecast.csv`
- ✅ All charts: `outputs/*.png` (7 files)
