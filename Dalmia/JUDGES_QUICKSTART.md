# GRIDSHIELD - Quick Start for Judges
**Case 2: Cost-Aware Load Forecasting | Stage 1 Submission**

---

## 🎯 **TL;DR - Key Results**

- **49.4% penalty reduction** vs naive baseline (₹449K → ₹227K)
- **96.79% forecast accuracy** (MAPE: 3.21%)
- **2-day ahead** forecast (192 time slots, 15-min resolution)
- **Cost-aware strategy:** Quantile 0.667 optimization (not RMSE)

---

## 🚀 **Quick Demo (3 minutes)**

### **Option 1: Web Dashboard (Recommended)**
```powershell
cd "gridshield-dashboard"
npm run dev
```
Open: http://localhost:3001

**Try this:**
1. Move "Temperature" slider to +5°C → Watch load jump +25%
2. Toggle "Holiday Mode" → See -15% commercial reduction
3. Add "Demand Spike" +20% → Peak amplification visible
4. Click "Export CSV" → Download SLDC schedule

---

### **Option 2: Python Model (Technical)**
```powershell
jupyter notebook train.ipynb
```
Run all cells (2-3 minutes) → See:
- 6 EDA plots showing COVID impact
- 3 model comparisons (Naive, MSE, Quantile)
- Penalty calculations: ₹227K (best) vs ₹449K (naive)
- 2-day forecast visualization

---

## 📂 **What's Included**

### **Mandatory Deliverables:**
- ✅ **DECISION_MEMO.md** - One-page executive summary (required)
- ✅ **train.ipynb** - Technical appendix (716 lines, fully reproducible)
- ✅ **outputs/2day_ahead_forecast.csv** - 192-slot SLDC schedule
- ✅ **gridshield-dashboard/** - Interactive Executive Command Center

### **Supporting Materials:**
- ✅ **PRESENTATION_SLIDES.md** - 15-slide deck with talking points
- ✅ **outputs/backtest_results.csv** - All strategy comparisons
- ✅ **outputs/*.png** - 7 validation charts (EDA, feature importance, forecasts)
- ✅ **USER_GUIDE.md** - Complete documentation (435 lines)

---

## 🎓 **Key Insights to Highlight**

### **1. Problem Reframing**
Traditional ML optimizes RMSE. We optimize **financial penalty** under ABT regulations.

**Result:** Our model has slightly higher RMSE but **10% lower penalties** than MSE baseline.

---

### **2. Asymmetric Strategy**
- Under-forecast penalty: ₹4/kWh (expensive!)
- Over-forecast penalty: ₹2/kWh (cheaper)
- **Optimal quantile:** α = 4/(4+2) = 0.667 (deliberately biased)

**Evidence:** -0.61% forecast bias = optimal positioning

---

### **3. Peak Risk Management**
- **Peak hours (18-22):** Only 16.7% of time, but 16.8% of penalties
- **Strategy:** Switch to Quantile 0.90 (conservative) during peak
- **Hybrid approach:** Best of both worlds (₹227K total penalty)

---

### **4. Uncertainty Quantification**
We provide **50%, 90%, 95% confidence intervals** (purple bands in dashboard).

**Use case:** SLDC operators can see worst-case scenarios and maintain adequate reserves.

---

### **5. COVID Structural Break**
Post-March 2020: Permanent 8.2% load reduction.

**Feature:** `lockdown_phase` (0-4) captures regime shifts  
**Readiness:** Model prepared for Stage 2 structural shocks

---

## 📊 **Validation Metrics (Feb-Apr 2021)**

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Total Penalty** | ₹227,257 | 49.4% better than naive |
| **Peak Penalty** | ₹38,184 | 16.8% of total (managed) |
| **Off-Peak Penalty** | ₹189,073 | 83.2% of total |
| **Forecast Bias** | -0.61% | Optimal (slight over-forecast) |
| **95th %ile Deviation** | 118.6 kW | Tail risk quantified |
| **MAE** | 37.90 kW | Avg error on 1,450 kW load = 2.6% |
| **MAPE** | 3.21% | Accuracy = 96.79% ✅ |

---

## 🏆 **Why This Wins**

### **Evaluation Criteria Alignment:**

1. **Analytical Depth (25%):** ✅
   - Quantile regression theory
   - Confidence intervals
   - 40 engineered features

2. **Re-Optimization Under Shock (20%):** ✅
   - COVID regime features
   - Dashboard scenario modeling
   - Retrain-ready architecture

3. **Decision Logic & Trade-Off Clarity (25%):** ✅
   - Decision memo explicitly states trade-offs
   - RMSE vs penalty comparison
   - Peak/off-peak strategy explained

4. **Systems Thinking (15%):** ✅
   - Understands ABT regulations
   - Peak risk concentration analysis
   - Grid stability implications

5. **Business Communication (15%):** ✅
   - Executive dashboard (non-technical)
   - One-page memo (board-ready)
   - ₹800K annual savings quantified

---

## 🔧 **If Something Breaks**

### Web Dashboard Not Loading?
```powershell
cd gridshield-dashboard
npm install
npm run dev
```

### Python Notebook Has Errors?
```powershell
# Unlock model files
Remove-Item outputs/model_*.txt -ErrorAction SilentlyContinue

# Restart kernel and run all cells
```

### Need to Regenerate Outputs?
```powershell
& .venv/Scripts/python.exe train.ipynb
```
All 7 output files will be recreated in `outputs/` folder.

---

## 📞 **Questions Judges Might Ask**

**Q: Why not just use RMSE?**  
A: RMSE minimizes error, but we need to minimize cost. Our model has 2 kW higher RMSE but saves ₹25K vs MSE baseline.

**Q: How do you handle COVID structural break?**  
A: We engineered `lockdown_phase` features (0-4) and `is_post_covid` flag. Model learns different patterns for each regime.

**Q: What if penalty rates change?**  
A: Dashboard has penalty rate sliders—adjust them and see instant recalculation. If ₹4→₹6, optimal quantile shifts to 0.75.

**Q: Can this adapt to Stage 2 data?**  
A: Yes! Architecture is modular. New data → Retrain → Update dashboard (5 minutes).

**Q: Why Quantile 0.667 specifically?**  
A: Mathematical optimum: α = C_under / (C_under + C_over) = 4/(4+2) = 0.667. This is **proven optimal** for asymmetric loss.

---

## 🎬 **3-Minute Demo Script**

**[Open Dashboard]**

"This is GRIDSHIELD Executive Command Center. See the baseline forecast—1,400 kW average, peaking at 1,750 kW during evening."

**[Move temp slider to +5°C]**

"If temperature rises 5°C tomorrow, watch this: load jumps +25%. The purple banner shows 'LOAD INCREASED' with exact impact. This is real-time scenario modeling."

**[Toggle holiday OFF]**

"Now I disable the holiday flag—see commercial load surge +15%. This lets operators test assumptions instantly."

**[Scroll to Insights Panel]**

"Here are the mandatory Stage 1 metrics:
- Peak vs off-peak penalty breakdown
- Forecast bias: -0.61% (optimal)
- 95th percentile deviation: 118.6 kW
- All confidence intervals visualized"

**[Click Export]**

"One click exports the 192-slot SLDC schedule. This is what we actually submit to the grid operator."

**[End]**

"49% penalty reduction, 97% accuracy, fully dynamic. Ready for Stage 2."

---

**Built for Decode X-2026 | Lumina Energy | Stage 1 Submission**
