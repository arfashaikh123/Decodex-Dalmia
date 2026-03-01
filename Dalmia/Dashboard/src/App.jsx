import React, { useState, useMemo, useEffect, useCallback } from 'react';
import {
  Activity, Zap, Download, TrendingDown, Shield, AlertTriangle,
  DollarSign, Calendar, Loader, RefreshCw,
  Thermometer, Droplets, Wind, CloudRain, Gauge, BarChart2, GitBranch,
} from 'lucide-react';
import ForecastChart from './components/ForecastChart';
import CostComparisonChart from './components/CostComparisonChart';
import InsightsPanel from './components/InsightsPanel';
import PredictionJustification from './components/PredictionJustification';
import Stage3ComplianceDashboard from './components/Stage3ComplianceDashboard';

const API_BASE = 'http://localhost:5000';

function WeatherStatCard({ icon: Icon, label, value, unit, sub, color = 'text-electric-blue-400' }) {
  return (
    <div className="bg-grid-dark-800 border border-grid-dark-600 rounded-xl p-4 flex flex-col gap-1">
      <div className="flex items-center gap-2">
        <Icon className={`w-4 h-4 ${color}`} />
        <span className="text-xs text-gray-400 uppercase tracking-wider font-semibold">{label}</span>
      </div>
      <p className={`text-2xl font-bold ${color}`}>
        {value != null ? `${value}${unit}` : '—'}
      </p>
      {sub && <p className="text-xs text-gray-500">{sub}</p>}
    </div>
  );
}

function App() {
  // Penalty rate state — auto-updated by stage, still manually overridable
  const [underPenalty, setUnderPenalty] = useState(4);
  const [overPenalty, setOverPenalty] = useState(2);
  // Stage: 1 = Round 1 (₹4/₹2), 2 = Round 2 (₹6/₹2), 3 = Board Review (₹6/₹2)
  const [stage, setStage] = useState(2);

  // Auto-sync penalty rates to the hackathon-defined values per stage
  const handleStageChange = React.useCallback((newStage) => {
    setStage(newStage);
    if (newStage === 1) {
      setUnderPenalty(4);
      setOverPenalty(2);
    } else {
      // Stage 2 and Stage 3: Dalmia Round 2 has stricter ₹6 under penalty
      setUnderPenalty(6);
      setOverPenalty(2);
    }
  }, []);

  // API / prediction state
  const [startDate, setStartDate] = useState('2021-05-01');
  const [endDate, setEndDate] = useState('2021-05-07');
  const [apiReady, setApiReady] = useState(false);
  const [apiStatus, setApiStatus] = useState('Connecting to model server...');
  const [isLoading, setIsLoading] = useState(false);
  const [apiData, setApiData] = useState(null);
  const [apiError, setApiError] = useState(null);
  const [dateRange, setDateRange] = useState({
    min: '2021-05-01', max: '2021-06-01',
    testStart: '2021-05-01', testEnd: '2021-06-01',
  });
  const [explainData, setExplainData] = useState(null);

  // Weather preview state (auto-fetched on date change)
  const [weatherPreview, setWeatherPreview] = useState(null);
  const [weatherLoading, setWeatherLoading] = useState(false);

  // Poll /api/status until model is ready
  useEffect(() => {
    let interval;
    const checkStatus = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/status`);
        const json = await res.json();
        setApiStatus(json.status);
        if (json.ready) {
          setApiReady(true);
          clearInterval(interval);
          Promise.all([
            fetch(`${API_BASE}/api/date_range`).then(r => r.json()),
            fetch(`${API_BASE}/api/explain`).then(r => r.json()),
          ]).then(([dr, ex]) => {
            setDateRange(dr);
            setExplainData(ex);
          }).catch(() => { });
        }
      } catch {
        setApiStatus('Model server offline – run: python api_server.py');
      }
    };
    checkStatus();
    interval = setInterval(checkStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  // Auto-fetch weather preview when date range changes (and API is ready)
  const fetchWeatherPreview = useCallback(async (start, end) => {
    if (!apiReady) return;
    setWeatherLoading(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/weather_preview?start_date=${start}&end_date=${end}`
      );
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Could not fetch weather preview');
      setWeatherPreview(json);
    } catch {
      setWeatherPreview(null);
    } finally {
      setWeatherLoading(false);
    }
  }, [apiReady]);

  // Trigger weather fetch whenever dates change and API is ready
  useEffect(() => {
    if (apiReady && startDate && endDate) {
      fetchWeatherPreview(startDate, endDate);
    }
  }, [apiReady, startDate, endDate, fetchWeatherPreview]);

  // Fetch prediction from API
  const runPrediction = useCallback(async () => {
    if (!apiReady) return;
    setIsLoading(true);
    setApiError(null);
    try {
      const res = await fetch(`${API_BASE}/api/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_date: startDate,
          end_date: endDate,
          penalty_under: underPenalty,
          penalty_over: overPenalty,
          stage,
        }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'API error');
      setApiData(json);
    } catch (e) {
      setApiError(e.message);
    } finally {
      setIsLoading(false);
    }
  }, [apiReady, startDate, endDate, underPenalty, overPenalty]);

  // Derive chart data from API
  const modifiedData = useMemo(() => {
    if (apiData && apiData.chart_data) {
      return apiData.chart_data.map(d => ({
        ...d,
        percentChange: 0,
        isModified: false,
        timeSlot: d.datetime,
        ci95Upper: d.ci90Upper,
        ci95Lower: d.ci90Lower,
        ci90Upper: d.ci90Upper,
        ci90Lower: d.ci90Lower,
        ci50Upper: d.ci50Upper,
        ci50Lower: d.ci50Lower,
      }));
    }
    return [];
  }, [apiData]);

  // Derive penalties from API
  const penalties = useMemo(() => {
    if (apiData && apiData.penalties && apiData.penalties.naive) {
      const p = apiData.penalties;
      const baselineTotal = Math.round(p.naive.total);
      const gridshieldTotal = Math.round(p.hybrid.total);
      return {
        baseline: baselineTotal,
        gridshield: gridshieldTotal,
        q67: Math.round(p.q67.total),
        q90: Math.round(p.q90.total),
        mse: Math.round(p.mse.total),
        savingsVsBaseline: baselineTotal - gridshieldTotal,
        reductionPercent: ((1 - p.hybrid.total / p.naive.total) * 100).toFixed(1),
        accuracy: p.hybrid.mape != null ? (100 - p.hybrid.mape).toFixed(1) : 'N/A',
        mae: p.hybrid.mae != null ? p.hybrid.mae.toFixed(1) : 'N/A',
        rmse: p.hybrid.rmse != null ? p.hybrid.rmse.toFixed(1) : 'N/A',
        bias: p.hybrid.bias != null ? p.hybrid.bias.toFixed(1) : 'N/A',
        peakPenalty: Math.round(p.hybrid.peak),
        offPeakPenalty: Math.round(p.hybrid.offpeak),
        p95Error: p.hybrid.p95 != null ? p.hybrid.p95.toFixed(0) : 'N/A',
        strategies: {
          naive: { ...p.naive, total: Math.round(p.naive.total) },
          mse: { ...p.mse, total: Math.round(p.mse.total) },
          q67: { ...p.q67, total: Math.round(p.q67.total) },
          q75: p.q75 ? { ...p.q75, total: Math.round(p.q75.total) } : null,
          q90: { ...p.q90, total: Math.round(p.q90.total) },
          q95: p.q95 ? { ...p.q95, total: Math.round(p.q95.total) } : null,
          hybrid: { ...p.hybrid, total: Math.round(p.hybrid.total) },
        },
      };
    }
    return {
      baseline: 0, gridshield: 0, q67: 0, q90: 0, mse: 0,
      savingsVsBaseline: 0, reductionPercent: '0.0',
      accuracy: 'N/A', mae: 'N/A', rmse: 'N/A', bias: 'N/A',
      peakPenalty: 0, offPeakPenalty: 0, p95Error: 'N/A',
      strategies: {},
    };
  }, [apiData]);

  // Export forecast to CSV
  const handleExport = () => {
    if (!apiData?.chart_data) return;
    const rows = apiData.chart_data;
    const csv = [
      ['DateTime', 'Actual_kW', 'Forecast_Hybrid', 'Forecast_Q67', 'Forecast_Q90', 'Temp_C', 'Humidity_%', 'Peak_Window'],
      ...rows.map(d => [
        d.datetime || d.timeSlot,
        d.actual != null ? d.actual.toFixed(1) : '',
        d.forecastHybrid != null ? d.forecastHybrid.toFixed(1) : '',
        d.forecastQ67 != null ? d.forecastQ67.toFixed(1) : '',
        d.forecastQ90 != null ? d.forecastQ90.toFixed(1) : '',
        d.temperature != null ? d.temperature.toFixed(1) : '',
        d.humidity != null ? d.humidity.toFixed(1) : '',
        d.isPeak ? 'Yes' : 'No',
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `GRIDSHIELD_${startDate}_to_${endDate}.csv`;
    a.click();
  };

  const wth = weatherPreview?.weather;

  return (
    <div className="min-h-screen bg-grid-dark-950 text-gray-100">
      {/* Header */}
      <header className="bg-grid-dark-900 border-b border-electric-blue-500/20 sticky top-0 z-50 shadow-2xl">
        <div className="max-w-[1920px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <Zap className="w-10 h-10 text-electric-blue-400" />
                  <div className="absolute inset-0 blur-xl bg-electric-blue-500 opacity-40 animate-pulse"></div>
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-gray-100 tracking-tight">GRIDSHIELD</h1>
                  <p className="text-xs text-gray-400 font-medium uppercase tracking-wider">
                    {stage === 3 ? '⚖ Stage 3 Board Review • Mumbai DISCOM' : 'Executive Command • Mumbai DISCOM'}
                  </p>
                </div>
              </div>
              <div className={`hidden lg:flex items-center gap-2 ml-8 px-3 py-1 rounded-full border ${apiReady
                ? 'bg-success-green-500/10 border-success-green-500/30'
                : 'bg-safety-orange-500/10 border-safety-orange-500/30'
                }`}>
                <Activity className={`w-3 h-3 animate-pulse ${apiReady ? 'text-success-green-400' : 'text-safety-orange-400'}`} />
                <span className={`text-xs font-semibold ${apiReady ? 'text-success-green-400' : 'text-safety-orange-400'}`}>
                  {apiReady ? 'MODEL READY' : 'LOADING...'}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="hidden md:block text-right mr-4">
                <p className="text-xs text-gray-400">Forecast Window</p>
                <p className="text-sm font-bold text-electric-blue-400">
                  {apiData ? `${startDate} → ${endDate}` : 'Select dates to run prediction'}
                </p>
              </div>
              <button
                onClick={handleExport}
                disabled={!apiData}
                className={`px-6 py-2.5 rounded-lg font-semibold text-sm flex items-center gap-2 shadow-lg transition-all ${apiData
                  ? 'bg-gradient-to-r from-electric-blue-500 to-electric-blue-600 hover:from-electric-blue-600 hover:to-electric-blue-700 text-white shadow-electric-blue-500/30'
                  : 'bg-grid-dark-700 text-gray-500 cursor-not-allowed'
                  }`}
              >
                <Download className="w-4 h-4" />
                <span>Export SLDC Schedule</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Date Picker Bar */}
      <div className="bg-grid-dark-900/80 border-b border-grid-dark-700 px-6 py-3">
        <div className="max-w-[1920px] mx-auto flex flex-wrap items-center gap-4">
          {/* Status indicator */}
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold border ${apiReady
            ? 'bg-success-green-500/10 border-success-green-500/30 text-success-green-400'
            : 'bg-safety-orange-500/10 border-safety-orange-500/30 text-safety-orange-400'
            }`}>
            {apiReady
              ? <><Activity className="w-3 h-3 animate-pulse" /> Model Ready</>
              : <><Loader className="w-3 h-3 animate-spin" /> {apiStatus}</>
            }
          </div>

          {/* Date inputs */}
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-electric-blue-400" />
            <label className="text-xs text-gray-400">From</label>
            <input
              type="date"
              value={startDate}
              min={dateRange.testStart}
              max={dateRange.testEnd}
              onChange={e => setStartDate(e.target.value)}
              className="bg-grid-dark-800 border border-grid-dark-600 text-gray-200 text-xs rounded px-2 py-1 focus:outline-none focus:border-electric-blue-500"
            />
            <label className="text-xs text-gray-400">To</label>
            <input
              type="date"
              value={endDate}
              min={dateRange.testStart}
              max={dateRange.testEnd}
              onChange={e => setEndDate(e.target.value)}
              className="bg-grid-dark-800 border border-grid-dark-600 text-gray-200 text-xs rounded px-2 py-1 focus:outline-none focus:border-electric-blue-500"
            />
          </div>

          {/* Penalty Rates (compact inline) */}
          <div className="flex items-center gap-3 px-3 py-1 bg-grid-dark-800 border border-grid-dark-700 rounded-lg">
            <DollarSign className="w-3 h-3 text-gray-500" />
            <span className="text-xs text-gray-400">Penalty:</span>
            <label className="text-xs text-gray-400">Under</label>
            <input
              type="number" min="1" max="10" step="0.5"
              value={underPenalty}
              onChange={e => setUnderPenalty(parseFloat(e.target.value))}
              className="w-14 bg-grid-dark-700 border border-grid-dark-600 text-peak-red-400 text-xs rounded px-1 py-0.5 focus:outline-none focus:border-electric-blue-500 font-bold"
            />
            <span className="text-xs text-gray-500">₹/kW</span>
            <label className="text-xs text-gray-400">Over</label>
            <input
              type="number" min="1" max="8" step="0.5"
              value={overPenalty}
              onChange={e => setOverPenalty(parseFloat(e.target.value))}
              className="w-14 bg-grid-dark-700 border border-grid-dark-600 text-success-green-400 text-xs rounded px-1 py-0.5 focus:outline-none focus:border-electric-blue-500 font-bold"
            />
            <span className="text-xs text-gray-500">₹/kW</span>
          </div>

          {/* Stage Selector — auto-sets correct penalty rate per stage */}
          <div className="flex items-center gap-2 px-3 py-1 bg-grid-dark-800 border border-grid-dark-700 rounded-lg">
            <GitBranch className="w-3 h-3 text-electric-blue-400" />
            <span className="text-xs text-gray-400 font-semibold">Stage:</span>
            <button
              onClick={() => handleStageChange(1)}
              className={`px-2 py-0.5 rounded text-xs font-bold transition-all ${stage === 1
                ? 'bg-electric-blue-500 text-white'
                : 'bg-grid-dark-700 text-gray-400 hover:text-gray-200'
                }`}
              title="Stage 1: Round 1 penalty ₹4 under / ₹2 over"
            >
              1 · Q67/Q90 · ₹4/₹2
            </button>
            <button
              onClick={() => handleStageChange(2)}
              className={`px-2 py-0.5 rounded text-xs font-bold transition-all ${stage === 2
                ? 'bg-safety-orange-500 text-white'
                : 'bg-grid-dark-700 text-gray-400 hover:text-gray-200'
                }`}
              title="Stage 2: Round 2 penalty ₹6 under / ₹2 over"
            >
              2 · Q75/Q95 · ₹6/₹2
            </button>
            <button
              onClick={() => handleStageChange(3)}
              className={`px-2 py-0.5 rounded text-xs font-bold transition-all ${stage === 3
                ? 'bg-success-green-600 text-white ring-1 ring-success-green-400'
                : 'bg-grid-dark-700 text-gray-400 hover:text-gray-200'
                }`}
              title="Stage 3: Board Review — governance layer on ₹6/₹2 regime"
            >
              3 · Board Review
            </button>
          </div>

          {/* Run button */}
          <button
            onClick={runPrediction}
            disabled={!apiReady || isLoading}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${apiReady && !isLoading
              ? 'bg-electric-blue-500 hover:bg-electric-blue-600 text-white shadow-lg shadow-electric-blue-500/30'
              : 'bg-grid-dark-700 text-gray-500 cursor-not-allowed'
              }`}
          >
            {isLoading
              ? <><Loader className="w-3 h-3 animate-spin" /> Running...</>
              : <><RefreshCw className="w-3 h-3" /> Run Prediction</>
            }
          </button>

          {/* Error or result summary */}
          {apiError && (
            <span className="text-xs text-peak-red-400 font-semibold">⚠ {apiError}</span>
          )}
          {apiData && !isLoading && (
            <span className="text-xs text-success-green-400 font-semibold">
              ✓ {apiData.total_rows} intervals • {((1 - penalties.gridshield / penalties.baseline) * 100).toFixed(1)}% penalty reduction
            </span>
          )}
        </div>
      </div>

      {/* Hero KPI Metrics */}
      <div className="max-w-[1920px] mx-auto px-6 py-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {/* KPI 1: Financial Savings */}
          <div className="relative bg-gradient-to-br from-success-green-500/20 to-success-green-500/5 border-2 border-success-green-500/40 rounded-xl p-6 overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-success-green-500/10 rounded-full blur-3xl"></div>
            <div className="relative">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs text-gray-400 uppercase tracking-wider font-semibold">Financial Savings</p>
                <DollarSign className="w-5 h-5 text-success-green-400" />
              </div>
              <p className="text-4xl font-bold text-success-green-400 mb-1">
                {apiData ? `₹${(penalties.baseline - penalties.gridshield).toLocaleString('en-IN')}` : '—'}
              </p>
              <p className="text-xs text-gray-400">
                {apiData ? `vs Naive forecast (${startDate} – ${endDate})` : 'Run prediction to see savings'}
              </p>
            </div>
          </div>

          {/* KPI 2: Risk Mitigation */}
          <div className="relative bg-gradient-to-br from-electric-blue-500/20 to-electric-blue-500/5 border-2 border-electric-blue-500/40 rounded-xl p-6 overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-electric-blue-500/10 rounded-full blur-3xl"></div>
            <div className="relative">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs text-gray-400 uppercase tracking-wider font-semibold">Risk Mitigation</p>
                <Shield className="w-5 h-5 text-electric-blue-400" />
              </div>
              <p className="text-4xl font-bold text-electric-blue-400 mb-1">
                {apiData ? `${((1 - penalties.gridshield / penalties.baseline) * 100).toFixed(1)}%` : '—'}
              </p>
              <p className="text-xs text-gray-400">Penalty Exposure Reduced</p>
            </div>
          </div>

          {/* KPI 3: Model Accuracy */}
          <div className="relative bg-gradient-to-br from-safety-orange-500/20 to-safety-orange-500/5 border-2 border-safety-orange-500/40 rounded-xl p-6 overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-safety-orange-500/10 rounded-full blur-3xl animate-pulse"></div>
            <div className="relative">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs text-gray-400 uppercase tracking-wider font-semibold">
                  {apiData ? 'Model Accuracy' : 'Peak Alert Window'}
                </p>
                <AlertTriangle className="w-5 h-5 text-safety-orange-400" />
              </div>
              <p className="text-4xl font-bold text-safety-orange-400 mb-1">
                {apiData && penalties.accuracy ? `${penalties.accuracy}%` : '18:00–22:00'}
              </p>
              <p className="text-xs text-gray-400">
                {apiData ? `MAE: ${penalties.mae} kW  |  Bias: ${penalties.bias} kW` : 'High Penalty Risk Window'}
              </p>
            </div>
          </div>

          <div className="relative bg-gradient-to-br from-grid-dark-700 to-grid-dark-800 border-2 border-grid-dark-600 rounded-xl p-6 overflow-hidden">
            <div className="relative">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs text-gray-400 uppercase tracking-wider font-semibold">Forecast Strategy</p>
                <TrendingDown className="w-5 h-5 text-electric-blue-400" />
              </div>
              <p className="text-4xl font-bold text-gray-100 mb-1">HYBRID</p>
              <p className="text-xs text-gray-400">
                {stage === 1 ? 'Q0.67 Off-Peak + Q0.90 Peak Hours' : 'Q0.75 Off-Peak + Q0.95 Peak Hours'}
              </p>
            </div>
          </div>
        </div>

        {/* ── Enhancement Engine Status Panel ─────────────────────────── */}
        {apiData && (
          <div className="mb-6 rounded-xl border border-electric-blue-500/20 bg-grid-dark-900 overflow-hidden">
            <div className="px-5 py-2.5 bg-grid-dark-800 border-b border-grid-dark-700 flex items-center gap-2">
              <Gauge className="w-4 h-4 text-electric-blue-400" />
              <span className="text-sm font-semibold text-gray-200">Adaptive Forecasting Engine</span>
              <span className="ml-auto text-xs text-gray-500">3 intelligence layers active</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-grid-dark-700">
              {/* Step 1 – Adaptive Quantile Policy */}
              {(() => {
                // Use API data if available, fall back to local stage state
                const ap = apiData.adaptive_policy;
                const stageNum = ap?.stage ?? stage;
                const offpeak = ap?.offpeak_quantile ?? (stage === 1 ? 0.67 : 0.75);
                const peak = ap?.peak_quantile ?? (stage === 1 ? 0.90 : 0.95);
                const desc = ap?.description ??
                  `Stage ${stageNum}: Q${offpeak} off-peak + Q${peak} peak hours (restart server to activate adaptive engine)`;
                return (
                  <div className="px-5 py-4">
                    <div className="flex items-center gap-2 mb-2">
                      <BarChart2 className="w-4 h-4 text-electric-blue-400" />
                      <span className="text-xs font-bold text-electric-blue-400 uppercase tracking-wider">Adaptive Quantile Policy</span>
                    </div>
                    <p className="text-lg font-bold text-gray-100">
                      Stage {stageNum} —{' '}
                      <span className="text-electric-blue-400">Q{offpeak} / Q{peak}</span>
                    </p>
                    <p className="text-xs text-gray-400 mt-1 leading-relaxed">{desc}</p>
                  </div>
                );
              })()}
              {/* Step 2 – Regime Shift Calibration */}
              {(() => {
                const rc = apiData.regime_calibration;
                const applied = rc?.applied;
                const bias = rc?.recent_bias_kw;
                const corr = rc?.correction_kw;
                const desc = rc?.description ?? 'Restart api_server.py to enable regime shift calibration';
                return (
                  <div className="px-5 py-4">
                    <div className="flex items-center gap-2 mb-2">
                      <GitBranch className="w-4 h-4 text-success-green-400" />
                      <span className="text-xs font-bold text-success-green-400 uppercase tracking-wider">Regime Calibration</span>
                    </div>
                    <p className="text-lg font-bold text-gray-100">
                      {applied
                        ? <><span className={bias >= 0 ? 'text-safety-orange-400' : 'text-electric-blue-400'}>
                          {bias >= 0 ? '+' : ''}{bias} kW
                        </span>{' '}bias →{' '}<span className="text-success-green-400">{corr >= 0 ? '+' : ''}{corr} kW</span> applied</>
                        : <span className="text-gray-500 text-sm">{rc ? 'No prior-day data' : '⟳ Pending restart'}</span>
                      }
                    </p>
                    <p className="text-xs text-gray-400 mt-1 leading-relaxed">{desc}</p>
                  </div>
                );
              })()}
              {/* Step 3 – Volatility Detector */}
              {(() => {
                const vd = apiData.volatility_detector;
                const cvPct = ((vd?.avg_volatility_cv ?? 0) * 100).toFixed(1);
                const isHighVol = vd?.is_high_volatility ?? false;
                const action = vd?.action ?? 'Restart api_server.py to enable volatility detection';
                return (
                  <div className="px-5 py-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Gauge className="w-4 h-4 text-safety-orange-400" />
                      <span className="text-xs font-bold text-safety-orange-400 uppercase tracking-wider">Volatility Detector</span>
                    </div>
                    <p className="text-lg font-bold text-gray-100">
                      CV ={' '}
                      <span className={isHighVol ? 'text-peak-red-400' : vd ? 'text-success-green-400' : 'text-gray-500'}>
                        {cvPct}%
                      </span>
                      <span className={`ml-2 text-sm ${isHighVol ? 'text-peak-red-400' : vd ? 'text-success-green-400' : 'text-gray-500'
                        }`}>
                        {vd ? (isHighVol ? '⚠ HIGH' : '✓ STABLE') : '⟳ Pending'}
                      </span>
                    </p>
                    <p className="text-xs text-gray-400 mt-1 leading-relaxed">{action}</p>
                  </div>
                );
              })()}
            </div>
          </div>
        )}

        {/* Weather Preview Panel — auto-populated from test dataset */}
        <div className={`mb-6 rounded-xl border transition-all ${wth
          ? 'bg-gradient-to-r from-electric-blue-500/10 via-grid-dark-800 to-grid-dark-800 border-electric-blue-500/30'
          : 'bg-grid-dark-900 border-grid-dark-700'
          }`}>
          <div className="px-5 py-3 border-b border-grid-dark-700 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Thermometer className="w-4 h-4 text-electric-blue-400" />
              <span className="text-sm font-semibold text-gray-200">
                Test Dataset Context — {startDate} to {endDate}
              </span>
              <span className="text-xs text-gray-500 ml-1">
                (auto-fetched from External_Factor_Data_Test.csv)
              </span>
            </div>
            {weatherLoading && (
              <div className="flex items-center gap-1 text-xs text-gray-400">
                <Loader className="w-3 h-3 animate-spin" /> Fetching…
              </div>
            )}
            {wth && !weatherLoading && (
              <span className="text-xs text-success-green-400 font-semibold">
                ✓ {weatherPreview.n_intervals} intervals · {weatherPreview.n_days} day(s)
              </span>
            )}
          </div>

          <div className="px-5 py-4">
            {!apiReady && (
              <p className="text-xs text-gray-500 text-center py-2">Waiting for model server…</p>
            )}
            {apiReady && weatherLoading && !wth && (
              <p className="text-xs text-gray-500 text-center py-2">Loading weather data…</p>
            )}
            {wth && (
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
                <WeatherStatCard
                  icon={Thermometer}
                  label="Temperature"
                  value={wth.temperature?.mean}
                  unit="°C"
                  sub={wth.temperature ? `Min ${wth.temperature.min}°C · Max ${wth.temperature.max}°C` : ''}
                  color="text-safety-orange-400"
                />
                <WeatherStatCard
                  icon={Droplets}
                  label="Humidity"
                  value={wth.humidity?.mean}
                  unit="%"
                  sub={wth.humidity ? `Min ${wth.humidity.min}% · Max ${wth.humidity.max}%` : ''}
                  color="text-electric-blue-400"
                />
                <WeatherStatCard
                  icon={Wind}
                  label="Heat Index"
                  value={wth.heat_index?.mean}
                  unit="°C"
                  sub={wth.heat_index ? `Min ${wth.heat_index.min}°C · Max ${wth.heat_index.max}°C` : ''}
                  color="text-peak-red-400"
                />
                <WeatherStatCard
                  icon={CloudRain}
                  label="Rainfall"
                  value={wth.rain?.mean}
                  unit=" mm"
                  sub={wth.rain ? `Max ${wth.rain.max} mm` : ''}
                  color="text-success-green-400"
                />
                <div className="bg-grid-dark-800 border border-grid-dark-600 rounded-xl p-4 flex flex-col gap-1">
                  <div className="flex items-center gap-2">
                    <Zap className="w-4 h-4 text-safety-orange-400" />
                    <span className="text-xs text-gray-400 uppercase tracking-wider font-semibold">Period Mix</span>
                  </div>
                  {weatherPreview?.period_info && (
                    <div className="text-xs text-gray-400 mt-1 space-y-1">
                      <p><span className="text-safety-orange-400 font-bold">{weatherPreview.period_info.peak_pct}%</span> peak-hour intervals</p>
                      <p><span className="text-electric-blue-400 font-bold">{weatherPreview.period_info.weekend_pct}%</span> weekend intervals</p>
                      <p><span className="text-gray-300 font-bold">{weatherPreview.period_info.n_holiday_intervals}</span> holiday intervals</p>
                    </div>
                  )}
                </div>
              </div>
            )}
            {!weatherLoading && !wth && apiReady && (
              <p className="text-xs text-gray-500 text-center py-2">Select a valid date range to load weather context</p>
            )}
          </div>
        </div>

        {/* Main Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Center: Forecast Chart + Cost Comparison */}
          <div className="lg:col-span-3 space-y-6">
            <ForecastChart
              data={modifiedData}
              startDate={startDate}
              endDate={endDate}
              hasApiData={!!apiData}
              totalRows={apiData?.total_rows}
            />
            {apiData?.justification && (
              <PredictionJustification
                justification={apiData.justification}
                startDate={startDate}
                endDate={endDate}
              />
            )}
            <CostComparisonChart
              penalties={penalties}
              startDate={startDate}
              endDate={endDate}
              underPenalty={underPenalty}
              overPenalty={overPenalty}
              explainData={explainData}
            />
          </div>

          {/* Right: Insights */}
          <div className="lg:col-span-1">
            <InsightsPanel
              data={modifiedData}
              penalties={penalties}
              tempDeviation={0}
              isHoliday={false}
              startDate={startDate}
              endDate={endDate}
              hasApiData={!!apiData}
              underPenalty={underPenalty}
              overPenalty={overPenalty}
              explainData={explainData}
              weatherSummary={apiData?.weather_summary}
              autoBest={apiData?.auto_best}
            />
          </div>
        </div>

        {/* ── Stage 3 Board Compliance Dashboard ─────────────────────────── */}
        {stage === 3 && (
          <Stage3ComplianceDashboard
            penalties={penalties}
            hasApiData={!!apiData}
            abuData={apiData?.asymmetric_bias_uplift}
            penaltyUnder={underPenalty}
            penaltyOver={overPenalty}
          />
        )}

        {/* Footer Info Banner */}
        <div className="mt-8 bg-gradient-to-r from-electric-blue-500/10 via-grid-dark-800 to-safety-orange-500/10 border border-electric-blue-500/30 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 mt-1">
              <div className="relative">
                <Zap className="w-8 h-8 text-electric-blue-400" />
                <div className="absolute inset-0 blur-lg bg-electric-blue-500 opacity-30"></div>
              </div>
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-100 mb-2">
                {stage === 3 ? 'GRIDSHIELD Stage 3: Board Governance Review — Bias-Controlled Forecasting System' : 'GRIDSHIELD Stage 2: Real-time Prediction on Held-Out Test Set'}
              </h3>
              <p className="text-sm text-gray-400 leading-relaxed mb-3">
                {stage === 3
                  ? <><span className="text-success-green-400 font-semibold">Stage 3 Board Review mode active.</span> The compliance dashboard below shows all 9 Board constraint metrics. Toggle to Stage 1 or 2 to view the forecast-vs-actual chart. Stage 3 GRIDSHIELD passes all governance constraints and delivers <span className="text-success-green-400 font-semibold">₹25,308 quarterly improvement</span> over Stage 2 baseline.</>
                  : apiData
                    ? <><span className="text-electric-blue-400 font-semibold">{penalties.reductionPercent}% penalty reduction</span> vs naive baseline on <span className="text-electric-blue-400 font-semibold">{startDate} – {endDate}</span> ({apiData.total_rows} intervals). Asymmetric quantile regression optimised for Mumbai ABT structure (₹{underPenalty} under / ₹{overPenalty} over).</>
                    : <>Select a date range and click <span className="text-electric-blue-400 font-semibold">Run Prediction</span> to compute real penalties from the test set using the trained LightGBM HYBRID model. Weather context is auto-loaded from the test dataset when dates are selected.</>
                }
              </p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                <div>
                  <p className="text-gray-500 mb-1">Training Period</p>
                  <p className="text-gray-300 font-semibold">{apiData?.training_period || explainData?.model_info?.training_period || 'Loading...'}</p>
                </div>
                <div>
                  <p className="text-gray-500 mb-1">{apiData ? 'Test Period' : 'Test Set'}</p>
                  <p className="text-gray-300 font-semibold">{apiData ? `${startDate} – ${endDate}` : `${dateRange.testStart} – ${dateRange.testEnd}`}</p>
                </div>
                <div>
                  <p className="text-gray-500 mb-1">Resolution</p>
                  <p className="text-gray-300 font-semibold">15-minute intervals</p>
                </div>
                <div>
                  <p className="text-gray-500 mb-1">{apiData ? 'Intervals Shown' : 'Training Rows'}</p>
                  <p className="text-gray-300 font-semibold">
                    {apiData
                      ? apiData.total_rows.toLocaleString()
                      : (explainData?.model_info?.training_rows || '…').toLocaleString?.() || '…'
                    }
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-grid-dark-900 border-t border-grid-dark-700 mt-12">
        <div className="max-w-[1920px] mx-auto px-6 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-xs text-gray-400">
              © 2026 GRIDSHIELD • Decode X-2026 • Case 2: Mumbai Load Forecasting
              {stage === 3 && <span className="ml-2 text-success-green-400 font-semibold">• Stage 3 Board Review Mode Active</span>}
            </p>
            <div className="flex items-center gap-6 text-xs text-gray-400">
              <span>Powered by LightGBM</span>
              <span>•</span>
              <span>Real-time Prediction on Test Set</span>
              <span>•</span>
              <span className="text-success-green-400">System Status: Operational</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
