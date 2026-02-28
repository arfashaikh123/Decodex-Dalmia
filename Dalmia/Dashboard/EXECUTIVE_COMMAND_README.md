# GRIDSHIELD Executive Command Dashboard
## Real-Time Scenario Modeling for Mumbai Power Distribution

---

## 🎯 What This Is

An **interactive web dashboard** that proves GRIDSHIELD isn't just a forecast tool—it's a **profit-maximization engine**.

Judges can **manipulate scenarios in real-time** and watch the financial impact instantly recalculate:
- Adjust temperature → See cooling load spike
- Toggle holiday → Watch commercial load drop 8%
- Change penalty rates → Observe strategy adaptation
- Stress-test with demand spikes → Evaluate grid resilience

---

## 🚀 Quick Start (2 Minutes)

### Step 1: Install Dependencies (First Time Only)

```powershell
cd "c:\Users\mansu\Downloads\02 – Case GRIDSHIELD\gridshield-dashboard"
npm install
```

### Step 2: Launch Dashboard

```powershell
npm run dev
```

**Dashboard opens at:** `http://localhost:5173`

---

## 📊 Dashboard Layout

### **Top Hero Metrics (4 KPI Cards)**

1. **Financial Savings**: ₹222K saved vs baseline (LARGE, GREEN, GLOWING)
2. **Risk Mitigation**: 49.4% penalty reduction
3. **Next Peak Alert**: 18:00-22:00 window (PULSING RED/ORANGE)
4. **Forecast Strategy**: HYBRID (Quantile 0.67 + Peak Boost)

### **Left Sidebar: What-If Controls** (The Magic!)

#### 1. **Temperature Simulator**
- Slider: -5°C to +10°C deviation
- Effect: +2% cooling load per degree above 32°C
- **Try:** Move to +8°C → Watch forecast spike

#### 2. **Holiday Toggle**
- Switch: May 1st Maharashtra Din ON/OFF
- Effect: -8% commercial load when enabled
- **Try:** Turn OFF → Commercial sector restores

#### 3. **Penalty Rate Adjusters**
- Under-forecast penalty: ₹2-8/kWh (default ₹4)
- Over-forecast penalty: ₹1-5/kWh (default ₹2)
- Effect: Model adapts safety buffer based on asymmetry
- **Try:** Set both to ₹3 → Watch savings change

#### 4. **Demand Spike Scenario**
- Slider: 0-25% unexpected growth
- Simulates: EV charging surge, heat wave, unplanned events
- **Try:** +15% spike → See unmet demand risk rise

**EVERY adjustment updates the "Current Penalty Estimate" in real-time!**

### **Center: Visualizations**

#### **Forecast Chart with Safety Buffer**
- **Green zone above forecast line**: Safety buffer (deliberate over-forecast)
- **Red shading (18:00-22:00)**: Peak window where strategy switches to Q0.90
- **Dashed gray line**: Actual load (for validation comparison)
- **Interactive tooltip**: Shows forecast, actual, and safety buffer at each hour

#### **Cost Comparison Bar Chart**
Three strategies compared:
1. **Naive Baseline** (Red): ₹449K penalty
2. **Standard MSE** (Orange): ₹252K penalty
3. **GRIDSHIELD HYBRID** (Green): ₹227K penalty ⭐ **49.4% savings**

**Key Insight Card Below:** Explains why "Lower RMSE ≠ Lower Cost"

### **Right Sidebar: Operational Insights**

#### **Unmet Demand Risk**
- Real-time risk assessment: HIGH/LOW
- Probability of hitting ₹4/kWh penalties

#### **Surplus Procurement Efficiency**
- % of slots deliberately over-forecast
- Shows optimal balance between ₹2 and ₹4 costs

#### **Load Statistics**
- 48-hour peak load, average load, peak/avg ratio
- Updates dynamically with scenario changes

#### **Current Load Drivers**
- Primary influence: Holiday patterns, temperature, weekly cycles
- Visual feature importance bars showing:
  - Weekly Patterns (85%)
  - Temperature Effect (dynamic based on slider)
  - Holiday Impact (30% if enabled)

#### **Peak Window Alert**
- Critical time: 18:00-22:00
- Strategy: Switches to Q0.90 (conservative)
- Extra buffer: +25-30 kW

---

## 🎬 Demo Script for Judges (5 Minutes)

### **Act 1: The Baseline (30 seconds)**

> "This is May 1st, 2021 - Maharashtra Din, a major public holiday. The baseline model (naive strategy) would cost us **₹449,000 in penalties**. Let me show you how GRIDSHIELD does better."

**Point to:** Cost Comparison Chart → GRIDSHIELD saves ₹222K

---

### **Act 2: The Safety Buffer Concept (1 minute)**

> "See this green zone above the forecast line? That's our **safety buffer**. We deliberately over-forecast by 15-30 kW to protect against the ₹4/kWh under-forecast penalty. It costs us ₹2/kWh, but it's **insurance against 2x worse penalties**."

**Point to:** Forecast chart → Green buffer zone

> "During peak hours (red shading 6-10 PM), we boost this buffer even more because that's when grid stability risk is highest."

---

### **Act 3: The What-If Magic (2 minutes)**

#### Scenario 1: Heat Wave
> "What if we hit a heat wave tomorrow? Let me add +8°C..."

**Action:** Move temperature slider to +8°C  
**Watch:** 
- Forecast spikes (AC cooling demand)
- "Current Penalty Estimate" increases
- "Temperature Effect" bar jumps to 90%

#### Scenario 2: No Holiday
> "What if this wasn't a holiday? Let's turn that off..."

**Action:** Toggle "May 1st Holiday" OFF  
**Watch:**
- Forecast increases +8% (commercial sector back)
- Primary driver changes to "Normal Weekly Patterns"

#### Scenario 3: Regulatory Tightening
> "What if regulators make penalties harsher? Let's increase under-forecast to ₹6..."

**Action:** Move under-forecast penalty slider to ₹6  
**Watch:**
- "Current Penalty Estimate" rises
- Cost Comparison bars all increase (but GRIDSHIELD still wins)
- Asymmetry ratio shows "High risk of under-forecasting"

#### Scenario 4: Demand Shock
> "What if we get a 20% surprise spike? EV charging explosion, unexpected event..."

**Action:** Move demand spike to +20%  
**Watch:**
- Unmet Demand Risk turns RED (HIGH)
- Peak load jumps to 2000+ kW
- "Critical spike: Grid stress scenario" warning

---

### **Act 4: The Export (30 seconds)**

> "When we're satisfied with the scenario, we click **Export SLDC Schedule**. This CSV contains 192 time slots (every 15 minutes) ready for system operator submission."

**Action:** Click "Export SLDC Schedule" button  
**Result:** Downloads `GRIDSHIELD_SLDC_Schedule_2026-02-28.csv`

---

### **Act 5: The Money Slide (1 minute)**

> "Look at this Cost Comparison chart. Standard ML models optimize for **accuracy** (RMSE). But accuracy doesn't equal money! The MSE model has **lower error but higher cost** (₹252K vs our ₹227K)."

**Point to:** "Why Cost-Aware Forecasting Wins" section

> "GRIDSHIELD uses **quantile regression** with asymmetric loss. We train the model to understand that under-forecasting costs **2x more** than over-forecasting. That's why we win."

**Final reveal:** "This approach saves **₹800K annually** across all DISCOMs in Mumbai."

---

## 🎨 Design Philosophy

### **Bloomberg Terminal Aesthetic**
- Dark "cyber-industrial" theme (Slate-950 background)
- Neon accents (electric blue #00d4ff, safety orange #ff6b35)
- High information density without clutter
- Professional trading floor vibe

### **Business Language, Not Tech Jargon**
❌ "RMSE: 53.73 kW, MAPE: 3.21%"  
✅ "Unmet Demand Risk: LOW, Penalty Exposure Reduced by 49.4%"

### **Real Interactivity**
- Every slider/toggle modifies actual forecast data
- Penalties recalculate using real asymmetric cost function
- Not just cosmetic—truly dynamic scenario modeling

---

## 📂 Technical Architecture

```
gridshield-dashboard/
├── src/
│   ├── App.jsx                          # Main layout & state management
│   ├── components/
│   │   ├── ScenarioControls.jsx         # Left sidebar what-if controls
│   │   ├── ForecastChart.jsx            # Center chart with safety buffer
│   │   ├── CostComparisonChart.jsx      # Strategy comparison bars
│   │   └── InsightsPanel.jsx            # Right sidebar insights
│   └── data/
│       └── sampleData.js                # Dynamic data functions
│           ├── getBaselineData()        # Baseline 192-point forecast
│           ├── applyScenarioModifiers() # Temperature/holiday/spike logic
│           └── calculatePenalties()      # Asymmetric cost calculation
```

### **Key Data Functions**

#### `applyScenarioModifiers(baseData, scenarios)`
```javascript
// Temperature: +2% load per °C above 32°C
if (tempDeviation > 0) {
  modifiedLoad *= (1 + tempDeviation * 0.02);
}

// Holiday: -8% commercial sector
if (isHoliday) {
  modifiedLoad *= 0.92;
}

// Demand spike: Unexpected growth
if (demandSpike > 0) {
  modifiedLoad *= (1 + demandSpike / 100);
}
```

#### `calculatePenalties(data, underPenalty, overPenalty)`
```javascript
// Asymmetric penalty calculation
if (actual > forecast) {
  penalty += (actual - forecast) * underPenalty; // ₹4
} else {
  penalty += (forecast - actual) * overPenalty;  // ₹2
}
```

---

## 🔥 What Makes This Dashboard Hackathon-Winning

### 1. **It's Not Static**
Most dashboards show pretty charts of **fixed data**. This one lets judges **break things** and see what happens.

### 2. **It Speaks Business**
No "MAPE" or "RMSE" in the hero metrics. Just **₹222K saved** and **49.4% risk reduction**.

### 3. **It Tells a Story**
- Hero metrics hook in 10 seconds
- What-if controls prove robustness
- Cost comparison delivers the punchline

### 4. **It's Designed for Presentation**
- 16:9 aspect ratio
- High contrast (readable from across room)
- Animations on critical elements (peak alert pulses, live status glows)

### 5. **It Proves the Math**
Not just claims—judges can **verify** by changing penalty rates and watching savings recalculate in real-time.

---

## 📋 Pre-Presentation Checklist

- [ ] Dashboard launches without errors (`npm run dev`)
- [ ] All 4 hero KPIs display correctly
- [ ] Temperature slider modifies forecast (watch chart)
- [ ] Holiday toggle changes "Current Penalty Estimate"
- [ ] Penalty rate sliders update cost comparison bars
- [ ] Demand spike slider triggers risk warnings
- [ ] Export button downloads CSV
- [ ] Full-screen mode enabled (F11 for cleanest presentation)
- [ ] Test on projector (check color contrast)

---

## 🎯 Key Talking Points

### **For Technical Judges:**
- "Quantile regression with α=0.667 optimized for asymmetric ₹4/₹2 penalty structure"
- "LightGBM trained on 283K observations with 40 engineered features"
- "Captures COVID-19 structural regime shift via binary indicator"

### **For Business Judges:**
- "49.4% penalty reduction = ₹800K annual savings across Mumbai DISCOMs"
- "Minimizes cost, not just error—that's the differentiation"
- "Ready for regulatory submission (192-point SLDC schedule export)"

### **For Both:**
- "This dashboard lets you stress-test grid resilience in real-time"
- "Every scenario adjustment proves model robustness"
- "Built for decision-makers, not data scientists"

---

## 🚨 Troubleshooting

### Dashboard won't start?
```powershell
# Clear cache and reinstall
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
npm run dev
```

### Changes not showing?
Hard refresh browser: `Ctrl + Shift + R`

### Port 5173 already in use?
Kill existing Vite server:
```powershell
Get-Process -Name node | Stop-Process -Force
npm run dev
```

---

## 🎓 Understanding the Model

### Why Quantile 0.667 (not 0.50)?

Under ABT penalties:
- Under-forecast: ₹4/kWh
- Over-forecast: ₹2/kWh

**Optimal quantile:** α = C_over / (C_under + C_over) = 2 / (4 + 2) = **0.667**

This means: "Be right 67% of the time (not 50%) because under-forecasting hurts more."

### Why HYBRID Strategy?

During peak hours (18:00-22:00):
- Grid stability risk is highest
- Transformer overloads expensive (>₹1M replacement)
- Use Q0.90 (extra conservative) for safety margin

Off-peak: Use Q0.67 (optimal cost tradeoff)

Result: **Best of both worlds** → ₹229K total penalty (only ₹2K more than pure Q0.67 but much safer)

---

## 📊 Data Provenance

- **Training:** Apr 2013 - Jan 2021 (283K observations)
- **Validation:** Feb 2021 - Apr 2021 (8.5K observations) 
- **Forecast:** May 1-2, 2021 (192 time slots)
- **Resolution:** 15 minutes (96 slots/day)
- **Features:** 40 engineered (temporal + weather + lags + events)

---

## 🏆 Stage 2 Readiness

This dashboard is **ready to adapt** when Stage 2 data drops at 7 PM:

1. New data → Update `src/data/sampleData.js` with actuals
2. Retrain model → Run Python script to get new coefficients
3. Replace forecast → Update 192-point baseline
4. Re-deploy → `npm run build` → Host on Vercel/Netlify

**All interactive controls still work!** Judges can still manipulate scenarios to test regime shifts.

---

## 🎤 Closing Statement

> "GRIDSHIELD isn't just predicting load—it's **protecting revenue**. Every kW we forecast is a financial decision. This dashboard proves we understand that. And when you can **manipulate any scenario** and still see us win, you know the model is robust."

**Mic drop. Walk off stage. 🎤⚡**

---

## 📞 Support

- **Dashboard Issues:** Check browser console (F12) for errors
- **Data Questions:** See `src/data/sampleData.js` comments
- **Model Questions:** Refer to `USER_GUIDE.md` in parent directory

---

**Built for Decode X-2026 • Case 2: GRIDSHIELD • Stage 1 Submission**
