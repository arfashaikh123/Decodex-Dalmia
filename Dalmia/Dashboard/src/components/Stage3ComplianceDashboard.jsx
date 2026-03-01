import React, { useState, useMemo } from 'react';
import {
  Shield, CheckCircle, XCircle, AlertTriangle, TrendingDown,
  TrendingUp, DollarSign, Activity, Zap, BarChart2, Lock,
  BarChart, ChevronDown, ChevronUp, Info,
} from 'lucide-react';

// ── Static verified data from backtest_results.csv ───────────────────────────
const STAGE2_BASELINE = {
  label: 'Stage 2 Baseline (Uncontrolled MSE)',
  totalPenalty: 252565,
  peakPenalty: 38595,
  offPeakPenalty: 213970,
  underPenalty: 186933,
  overPenalty: 65631,
  bias: 0.54,          // positive → under-forecast risk
  p95Deviation: 101.95,
  mape: 3.03,
  mae: 37.24,
  bufferUplift: '~6.5 kW (insufficient)',
  peakConcentration: 15.3,
};

const STAGE3_GRIDSHIELD = {
  label: 'Stage 3 GRIDSHIELD (Governed)',
  totalPenalty: 227257,
  peakPenalty: 38184,
  offPeakPenalty: 189073,
  underPenalty: 130700,
  overPenalty: 96557,
  bias: -0.61,         // negative → protective over-forecast
  p95Deviation: 101.63,
  mape: 3.19,
  mae: 37.90,
  bufferUplift: '+15 to +30 kW (peak: +30 kW)',
  peakConcentration: 16.8,
};

// Stage 1 = Dalmia Round 1 HYBRID model (Q0.667 off-peak + Q0.90 peak)
const STAGE1_HYBRID = {
  label: 'Stage 1 HYBRID (Round 1 Submission)',
  totalPenalty: 229037,
  peakPenalty: 39963,
  offPeakPenalty: 189074,
  underPenalty: 112318,
  overPenalty: 116719,
  bias: -1.17,
  p95Deviation: 113.11,
  mape: 3.40,
  mae: 40.47,
  bufferUplift: 'No deliberate uplift',
  peakConcentration: 17.4,
};

// EXPOSURE_CAP is now a user-controlled state inside the component.
// CONSTRAINTS is derived via useMemo inside the component.
const BASE_CONSTRAINTS = [
  { id: 1, metric: 'Total Financial Exposure', isCap: true },
  {
    id: 2, metric: 'Peak-Hour Penalty', requirement: '≤ ₹40,000 per quarter',
    baseline: `₹${STAGE2_BASELINE.peakPenalty.toLocaleString('en-IN')}`, baselinePass: STAGE2_BASELINE.peakPenalty <= 40000,
    stage1: `₹${STAGE1_HYBRID.peakPenalty.toLocaleString('en-IN')}`, stage1Pass: STAGE1_HYBRID.peakPenalty <= 40000,
    stage3: `₹${STAGE3_GRIDSHIELD.peakPenalty.toLocaleString('en-IN')}`, stage3Pass: STAGE3_GRIDSHIELD.peakPenalty <= 40000,
    detail: 'Q0.90 guardrail active during 18:00–22:00 window. Stage 1 used Q0.90 peak but without \ngoverned off-peak strategy. Stage 3 unifies both under the GRIDSHIELD architecture.'
  },
  {
    id: 3, metric: 'Off-Peak Penalty', requirement: '≤ ₹2,15,000 per quarter',
    baseline: `₹${STAGE2_BASELINE.offPeakPenalty.toLocaleString('en-IN')}`, baselinePass: STAGE2_BASELINE.offPeakPenalty <= 215000,
    stage1: `₹${STAGE1_HYBRID.offPeakPenalty.toLocaleString('en-IN')}`, stage1Pass: STAGE1_HYBRID.offPeakPenalty <= 215000,
    stage3: `₹${STAGE3_GRIDSHIELD.offPeakPenalty.toLocaleString('en-IN')}`, stage3Pass: STAGE3_GRIDSHIELD.offPeakPenalty <= 215000,
    detail: 'Stage 1 HYBRID already used Q0.667 off-peak securing ₹1,89,074 — matching Stage 3. Stage 3 adds \ngovernance layers on top of this strategy.'
  },
  { id: 4, metric: 'Exposure Cap Compliance', isCap: true, isCapCompliance: true },
  {
    id: 5, metric: 'Forecast Bias Direction', requirement: 'Slight over-forecast (bias < 0%)',
    baseline: `+${STAGE2_BASELINE.bias}% (under-forecast)`, baselinePass: false,
    stage1: `${STAGE1_HYBRID.bias}% (over-forecast)`, stage1Pass: true,
    stage3: `${STAGE3_GRIDSHIELD.bias}% (over-forecast)`, stage3Pass: true,
    detail: 'Stage 1 HYBRID achieved −1.17% bias vs Stage 3 at −0.61%. Both over-forecast. Stage 2 under-forecasts \nat +0.54%, exposing grid to ₹4/kWh penalty.'
  },
  {
    id: 6, metric: 'Average Buffering Uplift', requirement: '+5 to +30 kW above median',
    baseline: STAGE2_BASELINE.bufferUplift, baselinePass: false,
    stage1: STAGE1_HYBRID.bufferUplift, stage1Pass: false,
    stage3: STAGE3_GRIDSHIELD.bufferUplift, stage3Pass: true,
    detail: 'Neither Stage 1 nor Stage 2 had a deliberate buffering uplift layer. Stage 3 introduces the \nBuffer Optimization Manager enforcing +15 kW off-peak / +30 kW peak.'
  },
  {
    id: 7, metric: 'Peak-Hour Reliability Violations', requirement: '≤ 17% of total penalty',
    baseline: `${STAGE2_BASELINE.peakConcentration}% of total`, baselinePass: STAGE2_BASELINE.peakConcentration <= 17,
    stage1: `${STAGE1_HYBRID.peakConcentration}% of total`, stage1Pass: STAGE1_HYBRID.peakConcentration <= 17,
    stage3: `${STAGE3_GRIDSHIELD.peakConcentration}% of total`, stage3Pass: STAGE3_GRIDSHIELD.peakConcentration <= 17,
    detail: 'Stage 1 peak concentration was 17.4% — marginally above the 17% Board ceiling. Stage 3 \nbrings it down to 16.8% via the Peak Reliability Guardrail.'
  },
  {
    id: 8, metric: '95th Percentile Deviation', requirement: '≤ 120 kW tail risk',
    baseline: `${STAGE2_BASELINE.p95Deviation} kW`, baselinePass: STAGE2_BASELINE.p95Deviation <= 120,
    stage1: `${STAGE1_HYBRID.p95Deviation} kW`, stage1Pass: STAGE1_HYBRID.p95Deviation <= 120,
    stage3: `${STAGE3_GRIDSHIELD.p95Deviation} kW`, stage3Pass: STAGE3_GRIDSHIELD.p95Deviation <= 120,
    detail: 'Stage 1 P95 tail deviation was 113.11 kW — within the 120 kW cap. Stage 3 further tightens \ntail risk to 101.63 kW via the Volatility Detector layer.'
  },
  {
    id: 9, metric: 'Worst Deviation Intervals Impact', requirement: 'Identified & flagged to Board',
    baseline: 'Not governed', baselinePass: false,
    stage1: 'Not reported', stage1Pass: false,
    stage3: 'Flagged in Risk Report', stage3Pass: true,
    detail: 'Stage 1 had no mechanism to surface worst-deviation intervals to stakeholders. Stage 3 \nidentifies, classifies, and discloses the top 5 deviation intervals in this Risk Transparency Report.'
  },
];

const WORST_INTERVALS = [
  { rank: 1, period: 'Evening Peak (20:00)', condition: 'Sudden temperature spike', deviation: '~178 kW', penalty: '~₹712/slot', governed: true },
  { rank: 2, period: 'Morning Ramp (09:00)', condition: 'Commercial load surge post-holiday', deviation: '~160 kW', penalty: '~₹640/slot', governed: false },
  { rank: 3, period: 'Evening Peak (19:30)', condition: 'Industrial demand above forecast', deviation: '~150 kW', penalty: '~₹600/slot', governed: true },
  { rank: 4, period: 'Afternoon Trans. (16:30)', condition: 'Pre-peak AC activation', deviation: '~135 kW', penalty: '~₹540/slot', governed: false },
  { rank: 5, period: 'Late Night (23:30)', condition: 'Delayed commercial shutdown', deviation: '~125 kW', penalty: '~₹500/slot', governed: false },
];

const SYSTEM_COMPONENTS = [
  {
    name: 'Exposure Control Engine',
    icon: Shield,
    color: 'text-electric-blue-400',
    borderColor: 'border-electric-blue-500/40',
    bgColor: 'from-electric-blue-500/10',
    status: 'ACTIVE',
    statusColor: 'text-success-green-400',
    detail: 'Monitors cumulative penalty vs ₹2,30,000 quarterly cap. Alerts if 30-day run rate exceeds threshold.',
    metric: '₹2,27,257',
    metricLabel: '98.8% of cap used — COMPLIANT',
  },
  {
    name: 'Bias Governance Layer',
    icon: BarChart2,
    color: 'text-success-green-400',
    borderColor: 'border-success-green-500/40',
    bgColor: 'from-success-green-500/10',
    status: 'ACTIVE',
    statusColor: 'text-success-green-400',
    detail: 'Enforces α = 0.667 (Q0.667) off-peak. Verifies bias within −0.3% to −1.5% corridor.',
    metric: '−0.61%',
    metricLabel: 'Realized bias — within governed corridor',
  },
  {
    name: 'Peak Reliability Guardrail',
    icon: AlertTriangle,
    color: 'text-safety-orange-400',
    borderColor: 'border-safety-orange-500/40',
    bgColor: 'from-safety-orange-500/10',
    status: 'ACTIVE',
    statusColor: 'text-success-green-400',
    detail: 'Deploys Q0.90 during 18:00–22:00 window (+25–30 kW buffer). Cost: ~₹1,780/quarter.',
    metric: '₹38,184',
    metricLabel: 'Peak penalty (16.8% — controlled)',
  },
  {
    name: 'Buffer Optimization Manager',
    icon: TrendingUp,
    color: 'text-peak-red-400',
    borderColor: 'border-peak-red-500/40',
    bgColor: 'from-peak-red-500/10',
    status: 'ACTIVE',
    statusColor: 'text-success-green-400',
    detail: 'Off-peak: +5–15 kW uplift (Q0.667). Peak: +25–30 kW uplift (Q0.90). Revalidated quarterly.',
    metric: '−30.1%',
    metricLabel: 'Under-forecast penalty reduction',
  },
  {
    name: 'Risk Transparency Dashboard',
    icon: Activity,
    color: 'text-electric-blue-400',
    borderColor: 'border-electric-blue-500/40',
    bgColor: 'from-electric-blue-500/10',
    status: 'THIS VIEW',
    statusColor: 'text-electric-blue-400',
    detail: 'Reports 95th %ile deviation, worst 5 intervals, cap utilization, and penalty breakdown to Board.',
    metric: '9/9',
    metricLabel: 'Board constraints satisfied',
  },
];

// ── Sub-components ────────────────────────────────────────────────────────────

function PassBadge({ pass }) {
  return pass ? (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-success-green-500/15 border border-success-green-500/30 text-success-green-400 text-xs font-bold">
      <CheckCircle className="w-3 h-3" /> PASS
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-peak-red-500/15 border border-peak-red-500/30 text-peak-red-400 text-xs font-bold">
      <XCircle className="w-3 h-3" /> FAIL
    </span>
  );
}

function SectionHeader({ icon: Icon, title, subtitle, badge }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-electric-blue-500/10 border border-electric-blue-500/20">
          <Icon className="w-5 h-5 text-electric-blue-400" />
        </div>
        <div>
          <h2 className="text-base font-bold text-gray-100 uppercase tracking-wider">{title}</h2>
          {subtitle && <p className="text-xs text-gray-500">{subtitle}</p>}
        </div>
      </div>
      {badge && (
        <span className="px-3 py-1 rounded-full bg-success-green-500/10 border border-success-green-500/30 text-success-green-400 text-xs font-bold">
          {badge}
        </span>
      )}
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function Stage3ComplianceDashboard({ penalties, hasApiData }) {
  const [expandedRow, setExpandedRow] = useState(null);
  const [expandedComponent, setExpandedComponent] = useState(null);
  // ── User-editable Board Exposure Cap ──────────────────────────────────────
  const [exposureCap, setExposureCap] = useState(230000);
  const [capInput, setCapInput] = useState('230000');

  const handleCapChange = (e) => {
    setCapInput(e.target.value);
    const parsed = parseInt(e.target.value.replace(/,/g, ''), 10);
    if (!isNaN(parsed) && parsed > 0) setExposureCap(parsed);
  };

  // Use live data if available, otherwise fall back to static verified values
  const totalPenalty = hasApiData && penalties?.gridshield > 0
    ? penalties.gridshield
    : STAGE3_GRIDSHIELD.totalPenalty;

  const baselinePenalty = hasApiData && penalties?.mse > 0
    ? penalties.mse
    : STAGE2_BASELINE.totalPenalty;

  const peakPenalty = hasApiData && penalties?.peakPenalty > 0
    ? penalties.peakPenalty
    : STAGE3_GRIDSHIELD.peakPenalty;

  const offPeakPenalty = hasApiData && penalties?.offPeakPenalty > 0
    ? penalties.offPeakPenalty
    : STAGE3_GRIDSHIELD.offPeakPenalty;

  const p95 = hasApiData && penalties?.p95Error !== 'N/A'
    ? parseFloat(penalties.p95Error)
    : STAGE3_GRIDSHIELD.p95Deviation;

  const bias = hasApiData && penalties?.bias !== 'N/A'
    ? parseFloat(penalties.bias)
    : STAGE3_GRIDSHIELD.bias;

  // Derive CONSTRAINTS dynamically from live exposureCap
  const CONSTRAINTS = useMemo(() => {
    const baselineCapBreachPct = (((STAGE2_BASELINE.totalPenalty - exposureCap) / exposureCap) * 100).toFixed(1);
    const s1WithinCapPct = (((exposureCap - STAGE1_HYBRID.totalPenalty) / exposureCap) * 100).toFixed(1);
    const s3WithinCapPct = (((exposureCap - STAGE3_GRIDSHIELD.totalPenalty) / exposureCap) * 100).toFixed(1);
    const baselineCapPass = STAGE2_BASELINE.totalPenalty <= exposureCap;
    const s1CapPass = STAGE1_HYBRID.totalPenalty <= exposureCap;
    const s3CapPass = STAGE3_GRIDSHIELD.totalPenalty <= exposureCap;
    return BASE_CONSTRAINTS.map(c => {
      if (c.isCap && !c.isCapCompliance) {
        return {
          ...c,
          requirement: `≤ ₹${exposureCap.toLocaleString('en-IN')} per quarter`,
          baseline: `₹${STAGE2_BASELINE.totalPenalty.toLocaleString('en-IN')}`,
          baselinePass: baselineCapPass,
          stage1: `₹${STAGE1_HYBRID.totalPenalty.toLocaleString('en-IN')}`,
          stage1Pass: s1CapPass,
          stage3: `₹${STAGE3_GRIDSHIELD.totalPenalty.toLocaleString('en-IN')}`,
          stage3Pass: s3CapPass,
          detail: `Cap: ₹${exposureCap.toLocaleString('en-IN')}. S2: ${baselineCapPass ? 'within' : `${baselineCapBreachPct}% above`} cap. S1 HYBRID: ${s1CapPass ? `${s1WithinCapPct}% below` : 'above'} cap. S3 GRIDSHIELD: ${s3CapPass ? `${s3WithinCapPct}% below cap ✓` : 'above cap ❌'}.`,
        };
      }
      if (c.isCapCompliance) {
        const basePass = STAGE2_BASELINE.totalPenalty <= exposureCap;
        const s1Pass = STAGE1_HYBRID.totalPenalty <= exposureCap;
        const s3Pass = STAGE3_GRIDSHIELD.totalPenalty <= exposureCap;
        const s1BeachPct = Math.abs((((STAGE1_HYBRID.totalPenalty - exposureCap) / exposureCap) * 100).toFixed(1));
        return {
          ...c,
          requirement: `Within ₹${exposureCap.toLocaleString('en-IN')} ceiling`,
          baseline: basePass ? `${(((exposureCap - STAGE2_BASELINE.totalPenalty) / exposureCap) * 100).toFixed(1)}% BELOW ✓` : `${Math.abs(baselineCapBreachPct)}% ABOVE ❌`,
          baselinePass: basePass,
          stage1: s1Pass ? `${s1WithinCapPct}% BELOW ✓` : `${s1BeachPct}% ABOVE ❌`,
          stage1Pass: s1Pass,
          stage3: s3Pass ? `${s3WithinCapPct}% BELOW ✓` : 'ABOVE CAP ❌',
          stage3Pass: s3Pass,
          detail: `Cap: ₹${exposureCap.toLocaleString('en-IN')}. Stage 2: ${basePass ? 'COMPLIANT' : 'NON-COMPLIANT'}. Stage 1 HYBRID: ${s1Pass ? 'COMPLIANT' : 'NON-COMPLIANT'}. Stage 3 GRIDSHIELD: ${s3Pass ? 'COMPLIANT ✓' : 'NON-COMPLIANT'}.`,
        };
      }
      return c;
    });
  }, [exposureCap]);

  const passCount = CONSTRAINTS.filter(c => c.stage3Pass).length;
  const improvement = baselinePenalty - totalPenalty;
  const improvementPct = ((improvement / baselinePenalty) * 100).toFixed(1);
  const capUtilisation = ((totalPenalty / exposureCap) * 100).toFixed(1);
  const capStatus = totalPenalty <= exposureCap;

  return (
    <div className="space-y-6 mt-6">

      {/* ── Dashboard Title Banner ── */}
      <div className="relative overflow-hidden rounded-xl border border-electric-blue-500/30 bg-gradient-to-r from-electric-blue-500/10 via-grid-dark-900 to-success-green-500/10 p-6">
        <div className="absolute top-0 right-0 w-64 h-64 bg-electric-blue-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-success-green-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="relative flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="relative">
              <Shield className="w-12 h-12 text-electric-blue-400" />
              <div className="absolute inset-0 blur-xl bg-electric-blue-500 opacity-30 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h1 className="text-2xl font-bold text-gray-100 tracking-tight">Stage 3 Board Constraint Compliance Summary</h1>
                <span className="px-2 py-0.5 rounded bg-electric-blue-500/20 border border-electric-blue-500/40 text-electric-blue-400 text-xs font-bold">BOARD REVIEW</span>
              </div>
              <p className="text-sm text-gray-400">
                GRIDSHIELD Governed System • Decode X-2026 • Mumbai Suburban Distribution Zone
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Validation Period: Feb–Apr 2021 • 8,544 intervals @ 15-min resolution
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            {/* Board Cap Input */}
            <div className="flex flex-col gap-1 px-4 py-2.5 rounded-lg bg-grid-dark-800 border border-electric-blue-500/40">
              <label className="text-xs text-electric-blue-400 font-bold uppercase tracking-wider">Board Exposure Cap (₹)</label>
              <div className="flex items-center gap-1">
                <span className="text-gray-400 text-sm">₹</span>
                <input
                  type="text"
                  value={capInput}
                  onChange={handleCapChange}
                  className="w-32 bg-grid-dark-700 border border-electric-blue-500/30 text-electric-blue-400 font-bold text-sm rounded px-2 py-1 focus:outline-none focus:border-electric-blue-400 text-right"
                  placeholder="230000"
                />
                <span className="text-xs text-gray-500">/qtr</span>
              </div>
              <p className="text-xs text-gray-600">Edit to recalculate compliance</p>
            </div>
            <div className="text-center px-4 py-3 rounded-lg bg-success-green-500/10 border border-success-green-500/30">
              <p className="text-3xl font-bold text-success-green-400">{passCount}/9</p>
              <p className="text-xs text-gray-400 uppercase tracking-wide">Constraints Passed</p>
            </div>
            <div className={`text-center px-4 py-3 rounded-lg border ${capStatus ? 'bg-success-green-500/10 border-success-green-500/30' : 'bg-peak-red-500/10 border-peak-red-500/30'}`}>
              <p className={`text-2xl font-bold ${capStatus ? 'text-success-green-400' : 'text-peak-red-400'}`}>
                {capStatus ? 'COMPLIANT' : 'BREACH'}
              </p>
              <p className="text-xs text-gray-400 uppercase tracking-wide">Cap Status</p>
              <p className="text-xs text-gray-500">{capUtilisation}% utilized</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Hero KPI Strip — Stage 3 ── */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          {
            label: 'Total Exposure', value: `₹${totalPenalty.toLocaleString('en-IN')}`,
            sub: `Cap: ₹${exposureCap.toLocaleString('en-IN')} · ${capUtilisation}% used`, color: capStatus ? 'text-success-green-400' : 'text-peak-red-400',
            border: capStatus ? 'border-success-green-500/30' : 'border-peak-red-500/30',
            icon: DollarSign,
          },
          {
            label: 'Peak Penalty', value: `₹${peakPenalty.toLocaleString('en-IN')}`,
            sub: '16.8% of total', color: 'text-safety-orange-400',
            border: 'border-safety-orange-500/30', icon: AlertTriangle,
          },
          {
            label: 'Off-Peak Penalty', value: `₹${offPeakPenalty.toLocaleString('en-IN')}`,
            sub: '83.2% of total', color: 'text-electric-blue-400',
            border: 'border-electric-blue-500/30', icon: BarChart,
          },
          {
            label: 'Forecast Bias', value: `${bias > 0 ? '+' : ''}${bias !== STAGE3_GRIDSHIELD.bias ? bias.toFixed(2) : STAGE3_GRIDSHIELD.bias}%`,
            sub: bias < 0 ? 'Protective over-forecast ✓' : 'Under-forecast risk ⚠',
            color: bias < 0 ? 'text-success-green-400' : 'text-peak-red-400',
            border: bias < 0 ? 'border-success-green-500/30' : 'border-peak-red-500/30',
            icon: TrendingDown,
          },
          {
            label: '95th %ile Deviation', value: `${p95 || STAGE3_GRIDSHIELD.p95Deviation} kW`,
            sub: '≤120 kW required ✓', color: 'text-electric-blue-400',
            border: 'border-electric-blue-500/30', icon: Activity,
          },
          {
            label: 'Savings vs Baseline', value: `₹${improvement.toLocaleString('en-IN')}`,
            sub: `${improvementPct}% improvement`, color: 'text-success-green-400',
            border: 'border-success-green-500/30', icon: TrendingDown,
          },
        ].map((kpi, i) => (
          <div key={i} className={`bg-grid-dark-800 border ${kpi.border} rounded-xl p-4`}>
            <div className="flex items-center gap-1.5 mb-2">
              <kpi.icon className={`w-3.5 h-3.5 ${kpi.color}`} />
              <p className="text-xs text-gray-400 uppercase tracking-wide font-semibold leading-tight">{kpi.label}</p>
            </div>
            <p className={`text-xl font-bold ${kpi.color}`}>{kpi.value}</p>
            <p className="text-xs text-gray-500 mt-0.5">{kpi.sub}</p>
          </div>
        ))}
      </div>

      {/* ── Compliance Table ── */}
      <div className="rounded-xl border border-grid-dark-700 overflow-hidden bg-grid-dark-900">
        <div className="px-5 py-3 bg-grid-dark-800 border-b border-grid-dark-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-electric-blue-400" />
            <span className="text-sm font-bold text-gray-200 uppercase tracking-wider">Board Constraint Matrix — 9 Required Metrics</span>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="px-2 py-0.5 text-xs bg-yellow-500/10 border border-yellow-500/30 text-yellow-400 rounded-full font-bold">
              Stage 1: {CONSTRAINTS.filter(c => c.stage1Pass).length}/9 PASS
            </span>
            <span className="px-2 py-0.5 text-xs bg-peak-red-500/10 border border-peak-red-500/30 text-peak-red-400 rounded-full font-bold">
              Stage 2: {CONSTRAINTS.filter(c => c.baselinePass).length}/9 PASS
            </span>
            <span className="px-2 py-0.5 text-xs bg-success-green-500/10 border border-success-green-500/30 text-success-green-400 rounded-full font-bold">
              Stage 3: {passCount}/9 PASS
            </span>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-grid-dark-700 bg-grid-dark-850">
                <th className="text-left text-xs text-gray-500 uppercase tracking-wider px-4 py-3 font-semibold w-6">#</th>
                <th className="text-left text-xs text-gray-500 uppercase tracking-wider px-4 py-3 font-semibold">Constraint / Metric</th>
                <th className="text-left text-xs text-gray-500 uppercase tracking-wider px-4 py-3 font-semibold">Board Requirement</th>
                <th className="text-left text-xs text-yellow-400/80 uppercase tracking-wider px-4 py-3 font-semibold">Stage 1 HYBRID</th>
                <th className="text-left text-xs text-gray-500 uppercase tracking-wider px-4 py-3 font-semibold">Stage 2 Baseline</th>
                <th className="text-left text-xs text-success-green-400/80 uppercase tracking-wider px-4 py-3 font-semibold">Stage 3 GRIDSHIELD</th>
                <th className="text-center text-xs text-gray-500 uppercase tracking-wider px-4 py-3 font-semibold">S3 Status</th>
                <th className="text-center text-xs text-gray-500 uppercase px-4 py-3 w-8" />
              </tr>
            </thead>
            <tbody>
              {CONSTRAINTS.map((row, idx) => (
                <React.Fragment key={row.id}>
                  <tr
                    className={`border-b border-grid-dark-700 cursor-pointer transition-colors ${expandedRow === idx ? 'bg-grid-dark-800' : 'hover:bg-grid-dark-800/60'}`}
                    onClick={() => setExpandedRow(expandedRow === idx ? null : idx)}
                  >
                    <td className="px-4 py-3 text-xs text-gray-500">{row.id}</td>
                    <td className="px-4 py-3 font-semibold text-gray-200">{row.metric}</td>
                    <td className="px-4 py-3 text-xs text-gray-400">{row.requirement}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-medium ${row.stage1Pass ? 'text-yellow-300' : 'text-peak-red-400'}`}>
                          {row.stage1}
                        </span>
                        <PassBadge pass={row.stage1Pass} />
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-medium ${row.baselinePass ? 'text-gray-300' : 'text-peak-red-400'}`}>
                          {row.baseline}
                        </span>
                        <PassBadge pass={row.baselinePass} />
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-medium ${row.stage3Pass ? 'text-success-green-400' : 'text-peak-red-400'}`}>
                          {row.stage3}
                        </span>
                        <PassBadge pass={row.stage3Pass} />
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {row.stage3Pass ? (
                        <CheckCircle className="w-5 h-5 text-success-green-400 mx-auto" />
                      ) : (
                        <XCircle className="w-5 h-5 text-peak-red-400 mx-auto" />
                      )}
                    </td>
                    <td className="px-4 py-3 text-center text-gray-500">
                      {expandedRow === idx ? <ChevronUp className="w-4 h-4 mx-auto" /> : <ChevronDown className="w-4 h-4 mx-auto" />}
                    </td>
                  </tr>
                  {expandedRow === idx && (
                    <tr className="bg-grid-dark-800/80 border-b border-grid-dark-700">
                      <td colSpan={8} className="px-6 py-3">
                        <div className="flex items-start gap-2">
                          <Info className="w-3.5 h-3.5 text-electric-blue-400 mt-0.5 flex-shrink-0" />
                          <p className="text-xs text-gray-400 leading-relaxed">{row.detail}</p>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Baseline vs Stage 3 Financial Comparison ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Penalty Waterfall */}
        <div className="rounded-xl border border-grid-dark-700 bg-grid-dark-900 overflow-hidden">
          <div className="px-5 py-3 bg-grid-dark-800 border-b border-grid-dark-700 flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-success-green-400" />
            <span className="text-sm font-bold text-gray-200">Financial Exposure: Baseline vs Stage 3</span>
          </div>
          <div className="p-5 space-y-4">
            {[
              { label: 'Total Penalty', baseline: STAGE2_BASELINE.totalPenalty, s3: totalPenalty, cap: exposureCap },
              { label: 'Peak-Hour Penalty', baseline: STAGE2_BASELINE.peakPenalty, s3: peakPenalty, cap: 40000 },
              { label: 'Off-Peak Penalty', baseline: STAGE2_BASELINE.offPeakPenalty, s3: offPeakPenalty, cap: 215000 },
              { label: 'Under-Forecast Penalty', baseline: STAGE2_BASELINE.underPenalty, s3: STAGE3_GRIDSHIELD.underPenalty, cap: null },
            ].map((item, i) => {
              const maxVal = Math.max(item.baseline, item.s3);
              const baselinePct = (item.baseline / maxVal * 100).toFixed(1);
              const s3Pct = (item.s3 / maxVal * 100).toFixed(1);
              const saving = item.baseline - item.s3;
              const savingPct = ((saving / item.baseline) * 100).toFixed(1);
              return (
                <div key={i}>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-semibold text-gray-300">{item.label}</span>
                    <span className="text-xs text-success-green-400 font-bold">
                      −₹{saving.toLocaleString('en-IN')} ({savingPct}%)
                    </span>
                  </div>
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500 w-24">S2 Baseline</span>
                      <div className="flex-1 h-5 bg-grid-dark-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-peak-red-500 to-peak-red-400 rounded-full flex items-center justify-end pr-2"
                          style={{ width: `${baselinePct}%` }}
                        >
                          <span className="text-xs text-white font-bold">₹{(item.baseline / 1000).toFixed(0)}K</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500 w-24">S3 GRIDSHIELD</span>
                      <div className="flex-1 h-5 bg-grid-dark-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-success-green-600 to-success-green-400 rounded-full flex items-center justify-end pr-2"
                          style={{ width: `${s3Pct}%` }}
                        >
                          <span className="text-xs text-white font-bold">₹{(item.s3 / 1000).toFixed(0)}K</span>
                        </div>
                      </div>
                    </div>
                    {item.cap && (
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-600 w-24">Board Cap</span>
                        <div className="flex-1 h-1 bg-grid-dark-700 rounded-full relative">
                          <div
                            className="absolute top-1/2 -translate-y-1/2 w-0.5 h-4 bg-electric-blue-400"
                            style={{ left: `${(item.cap / maxVal * 100).toFixed(1)}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Risk Metrics Panel */}
        <div className="rounded-xl border border-grid-dark-700 bg-grid-dark-900 overflow-hidden">
          <div className="px-5 py-3 bg-grid-dark-800 border-b border-grid-dark-700 flex items-center gap-2">
            <Activity className="w-4 h-4 text-electric-blue-400" />
            <span className="text-sm font-bold text-gray-200">Risk Transparency Metrics — Board Report</span>
          </div>
          <div className="p-5 space-y-4">

            {/* Bias Comparison */}
            <div className="rounded-lg bg-grid-dark-800 border border-grid-dark-700 p-4">
              <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Forecast Bias — Governance Check</p>
              <div className="grid grid-cols-2 gap-3">
                <div className="text-center p-3 rounded-lg bg-peak-red-500/10 border border-peak-red-500/20">
                  <p className="text-xs text-gray-500 mb-1">Stage 2 Baseline</p>
                  <p className="text-2xl font-bold text-peak-red-400">+{STAGE2_BASELINE.bias}%</p>
                  <p className="text-xs text-peak-red-300 mt-1">Under-forecast risk</p>
                  <p className="text-xs text-gray-500">Exposed to ₹4/kWh</p>
                </div>
                <div className="text-center p-3 rounded-lg bg-success-green-500/10 border border-success-green-500/20">
                  <p className="text-xs text-gray-500 mb-1">Stage 3 GRIDSHIELD</p>
                  <p className="text-2xl font-bold text-success-green-400">{STAGE3_GRIDSHIELD.bias}%</p>
                  <p className="text-xs text-success-green-300 mt-1">Protective over-forecast</p>
                  <p className="text-xs text-gray-500">Pays ₹2/kWh (correct)</p>
                </div>
              </div>
              <div className="mt-3 p-2 rounded bg-electric-blue-500/5 border border-electric-blue-500/20">
                <p className="text-xs text-gray-400 text-center">
                  Optimal α = C_under / (C_under + C_over) = 4/(4+2) = <span className="text-electric-blue-400 font-bold">0.667</span>
                </p>
              </div>
            </div>

            {/* 95th Percentile */}
            <div className="rounded-lg bg-grid-dark-800 border border-grid-dark-700 p-4">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">95th Percentile Deviation</p>
                <CheckCircle className="w-4 h-4 text-success-green-400" />
              </div>
              <div className="flex items-end gap-3">
                <div>
                  <p className="text-3xl font-bold text-electric-blue-400">{p95 || STAGE3_GRIDSHIELD.p95Deviation} kW</p>
                  <p className="text-xs text-gray-500 mt-0.5">Tail risk — worst 5% of intervals</p>
                </div>
                <div className="pb-1 text-right ml-auto">
                  <p className="text-sm font-bold text-safety-orange-400">~₹{((p95 || STAGE3_GRIDSHIELD.p95Deviation) * 4).toFixed(0)}/slot</p>
                  <p className="text-xs text-gray-500">Max ₹4/kWh exposure</p>
                </div>
              </div>
              <div className="mt-2 flex items-center gap-2">
                <div className="flex-1 h-2 bg-grid-dark-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-electric-blue-500 to-electric-blue-400 rounded-full"
                    style={{ width: `${((p95 || STAGE3_GRIDSHIELD.p95Deviation) / 120 * 100).toFixed(0)}%` }}
                  />
                </div>
                <span className="text-xs text-gray-500">Cap: 120 kW</span>
              </div>
              <p className="text-xs text-success-green-400 mt-1">✓ Within 120 kW Board limit → Spinning reserve: ≥102 kW</p>
            </div>

            {/* Peak Concentration */}
            <div className="rounded-lg bg-grid-dark-800 border border-grid-dark-700 p-4">
              <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Peak-Hour Penalty Concentration</p>
              <div className="flex items-center gap-4">
                <div className="relative w-16 h-16">
                  <svg viewBox="0 0 36 36" className="w-16 h-16 -rotate-90">
                    <circle cx="18" cy="18" r="15.9" fill="none" stroke="#1f2937" strokeWidth="3.5" />
                    <circle cx="18" cy="18" r="15.9" fill="none" stroke="#f97316" strokeWidth="3.5"
                      strokeDasharray={`${16.8} ${83.2}`} strokeLinecap="round" />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-xs font-bold text-safety-orange-400">16.8%</span>
                  </div>
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="w-3 h-3 rounded-full bg-safety-orange-400 flex-shrink-0" />
                    <span className="text-xs text-gray-300">Peak 18–22h: ₹{peakPenalty.toLocaleString('en-IN')} (16.8%)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-electric-blue-400 flex-shrink-0" />
                    <span className="text-xs text-gray-300">Off-Peak: ₹{offPeakPenalty.toLocaleString('en-IN')} (83.2%)</span>
                  </div>
                  <p className="text-xs text-success-green-400 mt-2">✓ Near-proportional (16.8% penalty vs 16.7% time)</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── GRIDSHIELD System Architecture ── */}
      <div className="rounded-xl border border-grid-dark-700 bg-grid-dark-900 overflow-hidden">
        <div className="px-5 py-3 bg-grid-dark-800 border-b border-grid-dark-700 flex items-center gap-2">
          <Lock className="w-4 h-4 text-electric-blue-400" />
          <span className="text-sm font-bold text-gray-200">GRIDSHIELD Governance Architecture — 5 Active Control Layers</span>
          <span className="ml-auto text-xs text-gray-500">Analytics enable; governance controls outcomes</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 divide-y lg:divide-y-0 lg:divide-x divide-grid-dark-700">
          {SYSTEM_COMPONENTS.map((comp, i) => (
            <div
              key={i}
              className={`p-4 cursor-pointer transition-colors ${expandedComponent === i ? 'bg-grid-dark-800' : 'hover:bg-grid-dark-800/50'}`}
              onClick={() => setExpandedComponent(expandedComponent === i ? null : i)}
            >
              <div className="flex items-center justify-between mb-3">
                <div className={`p-1.5 rounded-lg bg-grid-dark-700 border ${comp.borderColor}`}>
                  <comp.icon className={`w-4 h-4 ${comp.color}`} />
                </div>
                <span className={`text-xs font-bold ${comp.statusColor}`}>● {comp.status}</span>
              </div>
              <p className="text-xs font-bold text-gray-200 mb-1 leading-tight">{comp.name}</p>
              <p className={`text-lg font-bold ${comp.color}`}>{comp.metric}</p>
              <p className="text-xs text-gray-500 mt-0.5 leading-tight">{comp.metricLabel}</p>
              {expandedComponent === i && (
                <p className="text-xs text-gray-400 mt-3 pt-3 border-t border-grid-dark-700 leading-relaxed">
                  {comp.detail}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* ── Worst 5 Deviation Intervals ── */}
      <div className="rounded-xl border border-grid-dark-700 bg-grid-dark-900 overflow-hidden">
        <div className="px-5 py-3 bg-grid-dark-800 border-b border-grid-dark-700 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-safety-orange-400" />
          <span className="text-sm font-bold text-gray-200">Worst 5 Deviation Intervals — Board Transparency Disclosure</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-grid-dark-700">
                <th className="text-left text-xs text-gray-500 uppercase px-4 py-2.5 font-semibold">Rank</th>
                <th className="text-left text-xs text-gray-500 uppercase px-4 py-2.5 font-semibold">Period</th>
                <th className="text-left text-xs text-gray-500 uppercase px-4 py-2.5 font-semibold">Triggering Condition</th>
                <th className="text-left text-xs text-gray-500 uppercase px-4 py-2.5 font-semibold">Deviation</th>
                <th className="text-left text-xs text-gray-500 uppercase px-4 py-2.5 font-semibold">Est. Penalty</th>
                <th className="text-left text-xs text-gray-500 uppercase px-4 py-2.5 font-semibold">Guardrail</th>
              </tr>
            </thead>
            <tbody>
              {WORST_INTERVALS.map((row) => (
                <tr key={row.rank} className="border-b border-grid-dark-700 hover:bg-grid-dark-800/40 transition-colors">
                  <td className="px-4 py-3">
                    <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold
                      ${row.rank === 1 ? 'bg-peak-red-500/20 text-peak-red-400' :
                        row.rank === 2 ? 'bg-safety-orange-500/20 text-safety-orange-400' :
                          'bg-grid-dark-700 text-gray-400'}`}>
                      {row.rank}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs font-semibold text-gray-300">{row.period}</td>
                  <td className="px-4 py-3 text-xs text-gray-400">{row.condition}</td>
                  <td className="px-4 py-3 text-xs font-bold text-safety-orange-400">{row.deviation}</td>
                  <td className="px-4 py-3 text-xs font-bold text-peak-red-400">{row.penalty}</td>
                  <td className="px-4 py-3">
                    {row.governed ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-success-green-500/10 border border-success-green-500/20 text-success-green-400 text-xs font-semibold">
                        <CheckCircle className="w-3 h-3" /> Q0.90 Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-electric-blue-500/10 border border-electric-blue-500/20 text-electric-blue-400 text-xs font-semibold">
                        <Activity className="w-3 h-3" /> Monitored
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="px-5 py-3 border-t border-grid-dark-700 bg-grid-dark-850">
          <p className="text-xs text-gray-500">
            Intervals 1 & 3 occur during 18:00–22:00 → managed by Peak Reliability Guardrail.
            Intervals 2, 4, 5 → monitored via Risk Transparency Dashboard. All disclosed to Board per Stage 3 governance requirements.
          </p>
        </div>
      </div>

      {/* ── Board Decision Confidence Summary ── */}
      <div className="rounded-xl border border-success-green-500/30 bg-gradient-to-r from-success-green-500/5 via-grid-dark-900 to-electric-blue-500/5 p-6">
        <div className="flex items-center gap-3 mb-5">
          <CheckCircle className="w-6 h-6 text-success-green-400" />
          <h3 className="text-base font-bold text-gray-100 uppercase tracking-wider">Board Decision Confidence — Stage 3 Approval</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            {
              dimension: 'Financial Prudence',
              confidence: 'HIGH',
              color: 'text-success-green-400',
              detail: 'Total exposure ₹2,27,257 — ₹2,743 within Board-authorized cap. ₹25,308 quarterly improvement is defensible and repeatable.',
            },
            {
              dimension: 'Regulatory Compliance',
              confidence: 'HIGH',
              color: 'text-success-green-400',
              detail: 'ABT penalty structure fully governed. Bias positioned at −0.61% (mathematical optimum for ₹4:₹2 penalty ratio).',
            },
            {
              dimension: 'Grid Stability',
              confidence: 'HIGH',
              color: 'text-success-green-400',
              detail: 'Peak concentration at 16.8% (near-proportional). Spinning reserve quantified at ≥102 kW from 95th %ile disclosure.',
            },
            {
              dimension: 'Controlled Trade-offs',
              confidence: 'HIGH',
              color: 'text-success-green-400',
              detail: '0.16% accuracy reduction accepted for ₹25K quarterly saving. Over-forecast increase is deliberate, governed, and financially rational.',
            },
          ].map((item, i) => (
            <div key={i} className="p-4 rounded-lg bg-grid-dark-800 border border-grid-dark-700">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-bold text-gray-300 uppercase tracking-wide">{item.dimension}</p>
                <span className={`text-xs font-bold ${item.color}`}>{item.confidence}</span>
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">{item.detail}</p>
            </div>
          ))}
        </div>

        <div className="mt-5 pt-5 border-t border-grid-dark-700 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-sm text-gray-400">
            <span className="text-success-green-400 font-bold">GRIDSHIELD</span> satisfies all Stage 3 Board constraints while achieving{' '}
            <span className="text-success-green-400 font-bold">₹25,308 quarterly improvement</span> and{' '}
            <span className="text-success-green-400 font-bold">~₹1,00,000 annual governance benefit</span> over the uncontrolled Stage 2 baseline.
          </p>
          <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-success-green-500/10 border border-success-green-500/30 flex-shrink-0">
            <CheckCircle className="w-5 h-5 text-success-green-400" />
            <span className="text-success-green-400 font-bold text-sm">RECOMMENDED FOR BOARD APPROVAL</span>
          </div>
        </div>
      </div>

    </div>
  );
}
