# GRIDSHIELD — Stage 3 Board Directive Compliance Report

**Case 02 – GRIDSHIELD | DECODE X 2026 | NLD Synapse**  
**To:** Board of Directors, Lumina Energy  
**From:** GRIDSHIELD Advisory Team  
**Date:** 01 March 2026  
**Subject:** Board Constraint Verification & Risk Disclosure

---

> This report confirms that the GRIDSHIELD Forecasting System meets **all six binding constraints** issued by the Board. Each constraint is verified with evidence, strategic rationale, and dashboard proof.

---

## TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Constraint 1 — Financial Exposure Cap](#2-constraint-1--financial-exposure-cap)
3. [Constraint 2 — Peak-Hour Reliability](#3-constraint-2--peak-hour-reliability)
4. [Constraint 3 — Forecast Bias Bound](#4-constraint-3--forecast-bias-bound)
5. [Constraint 4 — Buffering Constraint](#5-constraint-4--buffering-constraint)
6. [Constraint 5 — Risk Transparency](#6-constraint-5--risk-transparency)
7. [Constraint 6 — Executive Expectation](#7-constraint-6--executive-expectation)
8. [Our Approach — How GRIDSHIELD Works](#8-our-approach--how-gridshield-works)
9. [Why This Strategy — Regime Justification](#9-why-this-strategy--regime-justification)
10. [Stage 2 vs Stage 3 — Head-to-Head](#10-stage-2-vs-stage-3--head-to-head)
11. [Board Resolution & Deployment](#11-board-resolution--deployment)
12. [Appendix — Dashboard Screenshot Guide](#12-appendix--dashboard-screenshot-guide)

---

## 1. EXECUTIVE SUMMARY

### The Challenge

Lumina Energy's distribution grid operates under **Availability-Based Tariff (ABT)** regulations with a fundamentally asymmetric cost structure:

| | Under-Forecasting | Over-Forecasting |
|---|---|---|
| **What happens** | Grid draws emergency power | Surplus is disposed |
| **Penalty rate** | **₹6/kWh** (3× more expensive) | ₹2/kWh |
| **Business impact** | Regulatory risk + high cost | Low-cost, manageable |

**The core insight:** Traditional forecasting models treat over- and under-errors equally. In an ABT regime, this is expensive. GRIDSHIELD treats forecasting as a **financial risk problem**, not a statistical accuracy problem.

### What GRIDSHIELD Delivers

GRIDSHIELD is a **governed forecasting system** with five layers of control:

| Layer | What It Does |
|---|---|
| **Exposure Control** | Tracks total penalty against Board-approved cap in real-time |
| **Bias Governance** | Positions forecasts on the financially optimal side (slight over-forecast) |
| **Peak Reliability Guardrail** | Activates conservative forecasting during peak hours (6–10 PM) |
| **Buffer Optimization** | Ensures deliberate safety margins stay within Board limits |
| **Risk Transparency Dashboard** | Live Board-level reporting with full disclosure |

### Results at a Glance

| | Stage 2 (Before GRIDSHIELD) | Stage 3 (With GRIDSHIELD) |
|---|---|---|
| **Quarterly Penalty** | ₹3,46,031 | **₹2,92,607** (−15.4%) |
| **Savings vs Naive Forecast** | — | **₹4,48,844** (88.2% risk mitigation) |
| **Forecast Accuracy** | 96.97% | **96.9%** |
| **Bias Direction** | +0.54% (risky under-forecast) | **−0.61%** (protective over-forecast) |
| **Board Constraints Met** | 4 of 9 | **9 of 9** |

> **The trade-off:** We accepted a 0.07% accuracy reduction to unlock ₹53,424/quarter in penalty savings and move from 4/9 to 9/9 constraint compliance. We optimize for cost, not just error.

---

📸 **[SCREENSHOT 1 — INSERT HERE]**  
**What:** Dashboard landing page — KPI ribbon + Adaptive Forecasting Engine  
**Capture:** Top section showing KPI cards (₹4,48,844 savings, 88.2% risk mitigation, 96.9% accuracy, HYBRID strategy), Adaptive Forecasting Engine panel (Q0.75/Q0.95 policy, Regime Calibration, Volatility Detector), and Test Dataset Context

---

## 2. CONSTRAINT 1 — Financial Exposure Cap

> **Board Directive:** Total penalty must not exceed the exposure cap set relative to Stage 2 performance.

### How We Met This

| | Stage 2 Baseline | Stage 3 GRIDSHIELD | Change |
|---|---|---|---|
| **Total Penalty** | ₹3,46,031 | **₹2,92,607** | **−₹53,424** |
| Peak-Hour Penalty | ₹52,943 | ₹49,158 | −7.1% |
| Off-Peak Penalty | ₹2,93,088 | ₹2,43,449 | −16.9% |
| Under-Forecast Cost | ₹2,80,400 | **₹1,96,050** | **−30.1%** |
| Over-Forecast Cost | ₹65,631 | ₹96,557 | +47% (deliberate) |

**Why the over-forecast increase is intentional:** Under-forecasting costs ₹6/kWh. Over-forecasting costs ₹2/kWh. By shifting forecast bias slightly upward, we reduced the expensive penalty by ₹84,350 while adding only ₹30,926 in the cheaper category — a **net gain of ₹53,424/quarter** (~₹2.1 lakh annualized).

**Status: ✅ WITHIN CAP**

---

📸 **[SCREENSHOT 2 — INSERT HERE]**  
**What:** Penalty comparison bar chart (Stage 1 / Stage 2 / Stage 3)  
**Capture:** Dashboard → "Stage 3 Board Review" tab → Bar chart at top

📸 **[SCREENSHOT 3 — INSERT HERE]**  
**What:** Under vs Over penalty breakdown chart  
**Capture:** Dashboard → Main view → "Cost Comparison" stacked bar chart

---

## 3. CONSTRAINT 2 — Peak-Hour Reliability

> **Board Directive:** During peak hours (6–10 PM), underestimation exceeding 5% of actual load is permitted for a maximum of **3 intervals**.

### How We Met This

During peak hours, GRIDSHIELD switches from its standard forecast to the more conservative **Q0.95 forecast**, adding a +25–30 kW safety buffer. This means the system forecasts above the 95th percentile of expected load — virtually eliminating large under-predictions during the highest-risk window.

| | Stage 2 | Stage 3 GRIDSHIELD |
|---|---|---|
| Peak intervals tested | 496 | 496 |
| Intervals exceeding 5% underestimation | **119** ❌ | **0** ✅ |
| Board limit | 3 | 3 |

**Why this matters:** Peak hours carry the highest grid stress and ₹6/kWh penalty exposure. The Q0.95 guardrail acts as an insurance policy — the cost is modest, but the protection against catastrophic under-forecasting is significant.

Peak penalty share (16.8%) is nearly proportional to peak time share (16.7%), confirming **no concentration risk**.

**Status: ✅ ZERO VIOLATIONS (limit was 3)**

---

📸 **[SCREENSHOT 4 — INSERT HERE]**  
**What:** Forecast chart with actual vs predicted during peak hours — peak zones highlighted  
**Capture:** Dashboard → Main Forecast → 7-day view (e.g., May 1–7) showing actual (blue) vs HYBRID forecast (green) with red peak zones

---

## 4. CONSTRAINT 3 — Forecast Bias Bound

> **Board Directive:** Forecast bias must remain within **[−2%, +3%]**.

### How We Met This

| | Bias | Direction | Within Bounds? |
|---|---|---|---|
| **Stage 2 Baseline** | +0.54% | Under-forecast (risky) | In range, but wrong direction |
| **Stage 3 GRIDSHIELD** | **−0.61%** | Over-forecast (protective) | ✅ **PASS** |

**Why −0.61% is the right number:** Under the ₹6/₹2 penalty structure, the financially optimal position is to forecast slightly above actual. A −0.61% bias means the system consistently over-predicts by a small margin — paying ₹2/kWh for the overshoot instead of ₹6/kWh for missing low. This bias is:

- Well within the [−2%, +3%] corridor
- On the financially optimal side
- Actively governed by the Regime Calibration layer (not accidental)

**Status: ✅ PASS — bias is governed and optimally positioned**

---

📸 **[SCREENSHOT 5 — INSERT HERE]**  
**What:** Constraint compliance rows for Bias and Buffering  
**Capture:** Dashboard → "Stage 3 Board Review" tab → Constraint table rows showing bias and buffer metrics with PASS indicators

---

## 5. CONSTRAINT 4 — Buffering Constraint

> **Board Directive:** Average forecast uplift vs. the unbiased model must not exceed **3%**.

### How We Met This

| Metric | Value | Limit | Status |
|---|---|---|---|
| Average forecast uplift | **+2.95%** | ≤ 3% | ✅ **PASS** |

This constraint ensures GRIDSHIELD isn't gaming the penalty system through excessive over-forecasting. Our 2.95% uplift confirms the savings come from **smart positioning, not brute-force buffering**:

- **Off-peak hours:** Moderate uplift of +5–15 kW
- **Peak hours:** Higher uplift of +25–30 kW (only 4 hours/day)
- **Blended result:** 2.95% — disciplined and within Board tolerance

**Status: ✅ PASS**

---

## 6. CONSTRAINT 5 — Risk Transparency

> **Board Directive:** Report the 95th percentile deviation, worst 5 intervals, peak-hour volatility impact, and regime strategy justification.

### 6.1 — Tail Risk: 95th Percentile Deviation

| | Stage 2 Baseline | Stage 3 GRIDSHIELD |
|---|---|---|
| **P95 Deviation** | 101.95 kW | **101.63 kW** |
| Max penalty per interval | ~₹612 | ~₹610 |
| Recommended spinning reserve | ≥ 102 kW | ≥ 102 kW |

In the worst 5% of intervals, forecast error is bounded at ~102 kW. This tail risk is **known, bounded, and disclosed** — not hidden.

---

### 6.2 — Worst 5 Deviation Intervals

| Rank | When | Root Cause | Impact | Governed? |
|---|---|---|---|---|
| **1** | Evening Peak (20:00) | Temperature spike → AC surge | ~₹712 | ✅ Peak Guardrail active |
| **2** | Morning Ramp (09:00) | Post-holiday commercial surge | ~₹640 | 🔍 Monitored via Dashboard |
| **3** | Evening Peak (19:30) | Industrial demand above forecast | ~₹600 | ✅ Peak Guardrail active |
| **4** | Afternoon (16:30) | Pre-peak AC activation wave | ~₹540 | 🔍 Monitored via Dashboard |
| **5** | Late Night (23:30) | Delayed commercial shutdown | ~₹500 | 🔍 Monitored via Dashboard |

Peak-hour deviations (Ranks 1 & 3) are actively managed by the Q0.95 guardrail. Off-peak deviations are flagged on the dashboard for operator intervention. The dashboard also allows operators to **simulate these scenarios in advance** via temperature and holiday controls.

---

📸 **[SCREENSHOT 6 — INSERT HERE]**  
**What:** Worst 5 Deviation Intervals table with governance indicators  
**Capture:** Dashboard → "Stage 3 Board Review" tab → Risk Transparency section

---

### 6.3 — Peak-Hour Volatility

| Metric | Finding |
|---|---|
| Peak time share | 16.7% of the day |
| Peak penalty share | **16.8%** of total penalty |
| Interpretation | **Proportional** — no concentration risk |

Without GRIDSHIELD, peak hours would generate disproportionate penalties. With the guardrail, penalty share matches time share — confirming the system works as designed.

---

📸 **[SCREENSHOT 7 — INSERT HERE]**  
**What:** System architecture (5-component governance view)  
**Capture:** Dashboard → "Stage 3 Board Review" tab → System components section

---

### 6.4 — Regime Strategy Justification

*Detailed in Section 9 below.*

**Status: ✅ ALL FOUR SUB-ITEMS DISCLOSED**

---

## 7. CONSTRAINT 6 — Executive Expectation

> **Board Directive:** Demonstrate financial prudence, regulatory compliance, grid stability, and transparent trade-off articulation.

### Financial Prudence

- Total penalty within cap: ₹2,92,607 ✅
- Under-forecast penalty reduced 30.1% vs Stage 2 ✅
- Net savings: ₹53,424/quarter (~₹2.1 lakh/year) ✅
- Savings vs naive: ~₹8.8 lakh/year ✅
- **No additional capital investment** — savings come from strategy alone ✅

### Regulatory Compliance

- Bias: −0.61%, within [−2%, +3%] corridor ✅
- Peak violations: 0 of 496 (limit was 3) ✅
- Exposure cap met ✅
- Buffering: 2.95%, within 3% limit ✅
- Volatility: CV = 10.1% (STABLE regime) ✅

### Grid Stability

- Peak concentration proportional (16.8% vs 16.7%) ✅
- Tail risk bounded at 102 kW → spinning reserve sized accordingly ✅
- Conservative Q0.95 guardrail active during 6–10 PM ✅
- All 5 worst intervals identified and governance-assigned ✅

### Trade-Off Transparency

| What We Accepted | What We Avoided | Why |
|---|---|---|
| 0.07% lower accuracy | ₹53,424 quarterly penalty | Financial prudence > statistical precision |
| +₹31K over-forecast cost | ₹84K under-forecast exposure | ₹2/kWh beats ₹6/kWh |
| −0.61% bias | Positive bias (regulatory risk) | Optimal positioning under ABT |
| Peak buffer cost | Disproportionate peak escalation | Insurance against highest-cost window |

Every trade-off is quantified, justified, and reversible if market conditions change.

**Status: ✅ ALL FOUR EXPECTATIONS MET**

---

📸 **[SCREENSHOT 8 — INSERT HERE]**  
**What:** Prediction justification panel ("Why These Predictions?")  
**Capture:** Dashboard → Main view → After running prediction → Natural-language explanation panel showing temperature impact, lag patterns, and peak-hour strategy reasoning

---

## 8. OUR APPROACH — How GRIDSHIELD Works

### The Core Idea

Most forecasting systems output a single number. GRIDSHIELD outputs a **governed forecast** — one that has been checked against financial constraints, operational guardrails, and Board directives before it reaches the grid operator.

The system operates in three intelligence layers:

**Layer 1 — Adaptive Quantile Policy**  
Instead of predicting the average load, GRIDSHIELD predicts the 75th percentile (off-peak) and 95th percentile (peak hours). This intentionally biases the forecast slightly upward — paying the cheaper ₹2/kWh over-forecast penalty instead of the ₹6/kWh under-forecast penalty.

**Layer 2 — Regime Calibration**  
The system detects systematic bias in its own predictions and applies a calibrated correction, maintaining the desired −0.61% bias target.

**Layer 3 — Volatility Detection**  
GRIDSHIELD monitors load pattern stability. When conditions are stable, the standard policy applies. If volatility spikes, the system can escalate to more conservative strategies.

### What Powers It

| Component | Role |
|---|---|
| **ML Engine** | Gradient-boosted tree models trained on 8 years of load data |
| **API Server** | Serves real-time predictions with penalty calculations and plain-English justifications |
| **Live Dashboard** | Interactive Board-ready dashboard with compliance view, scenario controls, and export |

The engine uses 40 features spanning time patterns, weather conditions, historical load, and events — all using a minimum 48-hour lookback to support **2-day-ahead forecasting**.

---

📸 **[SCREENSHOT 9 — INSERT HERE]**  
**What:** Feature importance chart  
**Capture:** Dashboard → Main view → "Feature Importance" bar chart showing top drivers of predictions

---

## 9. WHY THIS STRATEGY — Regime Justification

### What Changed Between Stages

| | Stage 1 | Stage 2 / Stage 3 |
|---|---|---|
| Under-forecast penalty | ₹4/kWh | **₹6/kWh** (+50%) |
| Over-forecast penalty | ₹2/kWh | ₹2/kWh (same) |
| Cost asymmetry | 2:1 | **3:1** (much more punitive) |
| Optimal forecast position | Slightly above median | **Meaningfully above median** |

When the penalty for under-forecasting jumps 50%, the rational response is to shift the forecast upward. This is exactly what GRIDSHIELD does — not arbitrarily, but to the **financially optimal position** for the ₹6/₹2 cost structure.

### Why Governance — Not Retraining

The underlying models are already well-calibrated on 8 years of data. The problem in Stage 2 wasn't model quality — it was the absence of **operational controls** to manage cost asymmetry. Retraining might marginally improve accuracy, but it cannot:

- Position bias in the financially optimal direction
- Enforce peak-hour guardrails
- Monitor exposure caps in real-time
- Provide Board-level transparency

**The ₹53,424 quarterly saving comes from strategy, not statistics.** GRIDSHIELD wraps a governance layer around solid models — delivering financial discipline without sacrificing forecast quality.

### The GRIDSHIELD Response to Each Stage 2 Gap

| Stage 2 Gap | Stage 3 Fix |
|---|---|
| Under-forecast bias (+0.54%) | Bias Governance → corrected to −0.61% |
| No peak protection | Q0.95 guardrail → 0 violations |
| No exposure monitoring | Live cap tracking in dashboard |
| No tail risk reporting | P95, worst 5, peak volatility — all disclosed |
| No Board compliance view | Full 9-metric compliance dashboard deployed |

---

## 10. STAGE 2 vs STAGE 3 — Head-to-Head

### Financial Performance

| Metric | Stage 2 (Before) | Stage 3 (After) | Change |
|---|---|---|---|
| **Total Penalty** | ₹3,46,031 | **₹2,92,607** | **−₹53,424 (−15.4%)** |
| Peak Penalty | ₹52,943 | ₹49,158 | −7.1% |
| Off-Peak Penalty | ₹2,93,088 | ₹2,43,449 | −16.9% |
| Under-Forecast Cost | ₹2,80,400 | **₹1,96,050** | **−30.1%** |
| Over-Forecast Cost | ₹65,631 | ₹96,557 | +47% (deliberate) |

### Risk & Quality

| Metric | Stage 2 | Stage 3 | Verdict |
|---|---|---|---|
| Bias | +0.54% (risky) | **−0.61% (protective)** | ✅ Corrected |
| P95 Deviation | 101.95 kW | 101.63 kW | ✅ Improved |
| Accuracy (MAPE) | 96.97% | 96.9% | Controlled trade-off |
| Peak Violations (>5%) | 119 | **0** | ✅ Eliminated |

### Governance Maturity

| Dimension | Stage 2 | Stage 3 |
|---|---|---|
| Governance model | None — raw model output | Active 5-component system |
| Bias control | Incidental | Deliberate & governed |
| Peak protection | None | Q0.95 guardrail |
| Exposure monitoring | None | Live cap tracking |
| Board readiness | Not ready | Full transparency & compliance |

---

📸 **[SCREENSHOT 10 — INSERT HERE]**  
**What:** Full constraint compliance table (9 rows, Stage 1 / Stage 2 / Stage 3 with PASS/FAIL)  
**Capture:** Dashboard → "Stage 3 Board Review" tab → Constraint table at top — **this is the most important visual in the report**

📸 **[SCREENSHOT 11 — INSERT HERE]**  
**What:** Radar chart comparing Stage 1 / Stage 2 / Stage 3 across dimensions  
**Capture:** Dashboard → "Stage 3 Board Review" tab → Radar/spider chart

---

## 11. BOARD RESOLUTION & DEPLOYMENT

### Resolution

**RESOLVED:** The Board of Directors of Lumina Energy confirms:

1. GRIDSHIELD satisfies **all six binding constraints**.
2. Total exposure (₹2,92,607) is within the Board-approved cap.
3. Peak-hour reliability: **zero violations** (limit was 3).
4. Forecast bias (−0.61%) is within the [−2%, +3%] corridor and governed by Regime Calibration.
5. Buffering uplift (2.95%) is within the 3% limit.
6. Risk transparency: P95, worst 5, peak volatility, and regime justification all disclosed.
7. Financial prudence, regulatory compliance, grid stability, and trade-off transparency all demonstrated.

### Deployment Status

| Component | Status |
|---|---|
| API Server | ✅ Operational — models trained, predictions live |
| Dashboard | ✅ Operational — 12 interactive views deployed |
| Stage 3 Compliance View | ✅ Live — constraint table, radar chart, risk transparency |
| Explainability Engine | ✅ Active — plain-English justifications per forecast |
| Scenario Controls | ✅ Active — temperature, holiday, penalty rate adjustments |

### Ongoing Monitoring

| What We Monitor | How Often | Escalation Trigger |
|---|---|---|
| Cumulative exposure vs cap | Weekly | >80% cap usage at mid-quarter |
| Forecast bias | Daily | Bias drifts above +0.3% |
| Peak penalty concentration | Weekly | Peak share > 20% of total |
| P95 tail deviation | Monthly | Deviation > 130 kW |
| Model calibration | Monthly | MAPE > 5% on rolling 30 days |

---

## 12. APPENDIX — Dashboard Screenshot Guide

### Screenshot Checklist

| # | What to Capture | Where in Dashboard | Goes in Section |
|---|---|---|---|
| **1** | KPI Ribbon + Adaptive Engine | Main view → Top | Section 1 |
| **2** | Penalty Comparison Bar Chart | Board Review tab → Bar chart | Section 2 |
| **3** | Under vs Over Penalty Breakdown | Main view → Cost Comparison | Section 2 |
| **4** | Forecast Chart with Peak Zones | Main view → 7-day forecast | Section 3 |
| **5** | Bias & Buffering Compliance | Board Review tab → Constraints | Sections 4 & 5 |
| **6** | Worst 5 Intervals Table | Board Review → Risk Transparency | Section 6 |
| **7** | System Architecture Boxes | Board Review → Components | Section 8 |
| **8** | Prediction Justification Panel | Main view → "Why" panel | Section 7 |
| **9** | Feature Importance Chart | Main view → Explainability | Section 8 |
| **10** | Full Constraint Table (9 rows) | Board Review → Top | Section 10 |
| **11** | Radar Chart (S1/S2/S3) | Board Review → Radar | Section 10 |

### Steps to Capture

1. Start API: `python api_server.py`
2. Start Dashboard: `cd Dashboard && npm run dev`
3. Set Stage to 3, run prediction for May 1–31
4. Use Win+Shift+S to capture each screenshot
5. For Board Review tab: click the Shield icon

### Suggested Page Layout

```
Page 1:  Title + Table of Contents
Page 2:  Executive Summary + [Screenshot 1]
Page 3:  Constraint 1 (Exposure Cap) + [Screenshot 2] + [Screenshot 3]
Page 4:  Constraint 2 (Peak Reliability) + [Screenshot 4]
Page 5:  Constraints 3 & 4 (Bias + Buffering) + [Screenshot 5]
Page 6:  Constraint 5 (Risk Transparency) + [Screenshot 6] + [Screenshot 7]
Page 7:  Constraint 6 (Executive Expectation) + [Screenshot 8]
Page 8:  Our Approach + [Screenshot 9]
Page 9:  Regime Justification
Page 10: Stage 2 vs 3 Comparison + [Screenshot 10] + [Screenshot 11]
Page 11: Board Resolution & Deployment
```

---

## CONCLUSION

| Constraint | Requirement | Result | Status |
|---|---|---|---|
| **1. Financial Exposure** | ≤ Cap | ₹2,92,607 | ✅ **PASS** |
| **2. Peak Reliability** | ≤ 3 violations | **0 violations** | ✅ **PASS** |
| **3. Forecast Bias** | [−2%, +3%] | **−0.61%** | ✅ **PASS** |
| **4. Buffering** | ≤ 3% | **2.95%** | ✅ **PASS** |
| **5. Risk Transparency** | All 4 items disclosed | **All disclosed** | ✅ **PASS** |
| **6. Executive Expectation** | Prudence, Compliance, Stability, Transparency | **All met** | ✅ **PASS** |

> **GRIDSHIELD doesn't just forecast load — it governs financial exposure, enforces operational discipline, and gives the Board the transparency needed to run a regulated utility with confidence.**

---

**Prepared by:** GRIDSHIELD Advisory Team | NLD Synapse  
**Submission:** Stage 3 — Decode X 2026 | Case 02: GRIDSHIELD  
**Organization:** N. L. Dalmia Institute of Management Studies & Research
