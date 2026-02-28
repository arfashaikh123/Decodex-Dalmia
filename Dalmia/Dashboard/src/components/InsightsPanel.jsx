import React from 'react';
import {
  TrendingUp, TrendingDown, AlertCircle, DollarSign,
  BarChart2, Zap, Shield, Target, CheckCircle, XCircle,
} from 'lucide-react';

const fmt = (v) => v != null ? `₹${Math.round(v).toLocaleString('en-IN')}` : '—';
const fmtN = (v, dec = 1) => v != null ? v.toFixed(dec) : '—';

// Mini metric row
function MetricRow({ label, value, sub, color = 'text-gray-100', border }) {
  return (
    <div className={`flex items-center justify-between py-2 ${border ? 'border-t border-grid-dark-600' : ''}`}>
      <span className="text-xs text-gray-400">{label}</span>
      <div className="text-right">
        <span className={`text-sm font-bold font-mono ${color}`}>{value}</span>
        {sub && <p className="text-[10px] text-gray-500 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

// Score badge
function ScoreBadge({ score, max = 100 }) {
  const pct = Math.round((score / max) * 100);
  const color = pct >= 70 ? 'text-success-green-400' : pct >= 40 ? 'text-safety-orange-400' : 'text-peak-red-400';
  const bg = pct >= 70 ? 'bg-success-green-500/20 border-success-green-500/40' : pct >= 40 ? 'bg-safety-orange-500/20 border-safety-orange-500/40' : 'bg-peak-red-500/20 border-peak-red-500/40';
  return (
    <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-bold ${bg} ${color}`}>
      {pct >= 70 ? <CheckCircle className="w-3 h-3" /> : pct >= 40 ? <AlertCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
      {pct}% Efficiency
    </div>
  );
}

function InsightsPanel({
  data, penalties, startDate, endDate,
  hasApiData, underPenalty = 4, overPenalty = 2,
  explainData, weatherSummary, autoBest,
}) {
  const validData = data.filter(d => d.forecastHybrid != null);
  const pointsWithActual = validData.filter(d => d.actual != null);

  // ── Financial Metrics ─────────────────────────────────────────────────────
  const savings = (penalties.baseline || 0) - (penalties.gridshield || 0);
  const savingsPct = penalties.baseline > 0
    ? ((savings / penalties.baseline) * 100).toFixed(1) : '—';
  const penaltyPerSlot = pointsWithActual.length > 0 && penalties.gridshield > 0
    ? (penalties.gridshield / pointsWithActual.length).toFixed(1) : '—';
  const baselinePerSlot = pointsWithActual.length > 0 && penalties.baseline > 0
    ? (penalties.baseline / pointsWithActual.length).toFixed(1) : '—';

  // ── Demand Coverage ───────────────────────────────────────────────────────
  // Coverage = slots where forecast ≥ actual (supply was procured)
  const coveredSlots = pointsWithActual.filter(d => d.forecastHybrid >= d.actual).length;
  const uncoveredSlots = pointsWithActual.length - coveredSlots;
  const coveragePct = pointsWithActual.length > 0
    ? ((coveredSlots / pointsWithActual.length) * 100).toFixed(1) : null;

  // Optimal α = underPenalty / (underPenalty + overPenalty)
  const optimalAlpha = underPenalty / (underPenalty + overPenalty);
  const optimalCoverage = (optimalAlpha * 100).toFixed(0);

  // ── Business Efficiency Score (0–100) ─────────────────────────────────────
  // = how much cost we avoided relative to naive, normalised to 0-100
  const efficiencyScore = penalties.baseline > 0
    ? Math.min(100, Math.max(0, (savings / penalties.baseline) * 100)) : 0;

  // ── Strategy Comparison Table ─────────────────────────────────────────────
  const strategies = penalties.strategies || {};
  // Auto-selected winner key from API (fallback to 'hybrid')
  const winnerKey = autoBest?.strategy || 'hybrid';
  const stratOrders = [
    { key: 'naive', label: 'Naïve (Mean)', alpha: '—' },
    { key: 'mse', label: 'MSE Regression', alpha: '0.50' },
    { key: 'q67', label: 'Quantile Q0.67', alpha: '0.67' },
    { key: 'q75', label: 'Quantile Q0.75', alpha: '0.75' },
    { key: 'q90', label: 'Quantile Q0.90', alpha: '0.90' },
    { key: 'q95', label: 'Quantile Q0.95', alpha: '0.95' },
    { key: 'hybrid', label: 'HYBRID (auto-best)', alpha: `${optimalAlpha.toFixed(2)}` },
  ];

  const dataStats = explainData?.data_statistics || {};
  const naiveTotal = strategies.naive?.total || penalties.baseline || 1;

  return (
    <div className="space-y-4">

      {/* ── Header ── */}
      <div className="card-grid-dark">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <BarChart2 className="w-5 h-5 text-electric-blue-400" />
            <h2 className="text-base font-bold text-gray-100">Business Analytics</h2>
          </div>
          {hasApiData && <ScoreBadge score={efficiencyScore} />}
        </div>
        <p className="text-xs text-gray-400">Executive KPIs · Penalty cost analysis</p>
      </div>

      {/* ── Financial Savings ── */}
      <div className="card-grid-dark bg-gradient-to-br from-success-green-500/10 to-grid-dark-800 border border-success-green-500/30">
        <div className="flex items-center gap-2 mb-3">
          <DollarSign className="w-4 h-4 text-success-green-400" />
          <span className="text-xs font-bold text-success-green-400 uppercase tracking-wider">Penalty Savings vs Naive</span>
        </div>
        <p className="text-4xl font-bold text-success-green-400 mb-1">
          {hasApiData ? fmt(savings) : '—'}
        </p>
        <p className="text-xs text-gray-400 mb-3">
          {hasApiData
            ? `${savingsPct}% reduction · HYBRID vs Naïve baseline`
            : 'Run prediction to see savings'}
        </p>
        {hasApiData && (
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-grid-dark-700 rounded-lg p-2">
              <p className="text-gray-500 mb-0.5">Naïve Penalty</p>
              <p className="text-peak-red-400 font-bold font-mono">{fmt(penalties.baseline)}</p>
              <p className="text-gray-600 text-[10px]">{baselinePerSlot} ₹/slot</p>
            </div>
            <div className="bg-grid-dark-700 rounded-lg p-2">
              <p className="text-gray-500 mb-0.5">HYBRID Penalty</p>
              <p className="text-success-green-400 font-bold font-mono">{fmt(penalties.gridshield)}</p>
              <p className="text-gray-600 text-[10px]">{penaltyPerSlot} ₹/slot</p>
            </div>
          </div>
        )}
      </div>

      {/* ── Demand Coverage ── */}
      <div className={`card-grid-dark border-l-4 ${coveragePct !== null && parseFloat(coveragePct) >= parseFloat(optimalCoverage) - 5
        ? 'border-success-green-500 bg-success-green-500/5'
        : 'border-safety-orange-500 bg-safety-orange-500/5'
        }`}>
        <div className="flex items-start gap-3">
          <Target className="w-5 h-5 flex-shrink-0 mt-0.5 text-electric-blue-400" />
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-sm font-semibold text-gray-100">Demand Coverage Rate</h3>
              {coveragePct !== null && (
                <span className={`text-xl font-bold font-mono ${parseFloat(coveragePct) >= parseFloat(optimalCoverage) - 5
                  ? 'text-success-green-400' : 'text-safety-orange-400'
                  }`}>{coveragePct}%</span>
              )}
            </div>
            {/* Coverage bar */}
            {coveragePct !== null && (
              <div className="mb-2">
                <div className="w-full h-3 bg-grid-dark-700 rounded-full overflow-hidden relative">
                  <div
                    className="h-full bg-electric-blue-500 rounded-full transition-all"
                    style={{ width: `${coveragePct}%` }}
                  />
                  {/* Target line */}
                  <div
                    className="absolute top-0 bottom-0 w-0.5 bg-success-green-400"
                    style={{ left: `${optimalCoverage}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-gray-500 mt-1">
                  <span>0%</span>
                  <span className="text-success-green-400">Target {optimalCoverage}% (optimal α)</span>
                  <span>100%</span>
                </div>
              </div>
            )}
            <p className="text-xs text-gray-400 leading-relaxed">
              {coveragePct !== null
                ? `${coveredSlots} of ${pointsWithActual.length} intervals covered (forecast ≥ actual). ${uncoveredSlots} under-supply slots expose ₹${underPenalty}/kW penalty.`
                : `Optimal coverage target: ${optimalCoverage}% (α = ${optimalAlpha.toFixed(3)}). Run prediction to evaluate.`
              }
            </p>
          </div>
        </div>
      </div>

      {/* ── Strategy Performance Comparison ── */}
      {hasApiData && Object.keys(strategies).length > 0 && (
        <div className="card-grid-dark">
          <div className="flex items-center gap-2 mb-2">
            <BarChart2 className="w-4 h-4 text-electric-blue-400" />
            <h3 className="text-sm font-semibold text-gray-100">Strategy Comparison</h3>
          </div>

          {/* Auto-best banner */}
          {autoBest && (
            <div className="mb-3 px-3 py-2 rounded-lg bg-success-green-500/15 border border-success-green-500/40 text-xs text-gray-300 leading-relaxed">
              <span className="text-success-green-400 font-bold">✓ Auto-selected: </span>
              {autoBest.description}
            </div>
          )}

          <div className="space-y-1.5">
            {stratOrders.map(({ key, label }) => {
              const s = strategies[key];
              if (!s) return null;
              const isWinner = key === winnerKey;
              const isNaive = key === 'naive';
              const isHybrid = key === 'hybrid';
              const pctVsNaive = ((1 - s.total / naiveTotal) * 100).toFixed(1);
              const barWidth = Math.max(3, Math.round((s.total / naiveTotal) * 100));
              const barColor = isWinner ? 'bg-success-green-500'
                : isNaive ? 'bg-peak-red-500'
                  : isHybrid ? 'bg-electric-blue-500'
                    : 'bg-electric-blue-500/40';
              const rowBg = isWinner
                ? 'bg-success-green-500/10 border border-success-green-500/40'
                : isNaive ? 'bg-peak-red-500/5 border border-peak-red-500/20'
                  : 'bg-grid-dark-700/50';
              return (
                <div key={key} className={`rounded-lg px-3 py-2 ${rowBg}`}>
                  <div className="flex items-center justify-between mb-1">
                    <span className={`text-xs font-semibold flex items-center gap-1 ${isWinner ? 'text-success-green-400' : isNaive ? 'text-peak-red-400' : 'text-gray-300'
                      }`}>
                      {isWinner && <span>✓</span>}
                      {label}
                      {isWinner && !isHybrid && (
                        <span className="ml-1 text-[10px] font-bold bg-success-green-500/30 px-1.5 py-0.5 rounded-full">BEST</span>
                      )}
                    </span>
                    <div className="text-right">
                      <span className={`text-xs font-bold font-mono ${isWinner ? 'text-success-green-400' : isNaive ? 'text-peak-red-400' : 'text-gray-200'
                        }`}>
                        {fmt(s.total)}
                      </span>
                      {!isNaive && (
                        <span className={`ml-1.5 text-[10px] font-semibold ${parseFloat(pctVsNaive) > 0 ? 'text-success-green-400' : 'text-peak-red-400'}`}>
                          -{pctVsNaive}%
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="w-full h-1.5 bg-grid-dark-600 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${barColor}`} style={{ width: `${barWidth}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}


      {/* ── Peak vs Off-Peak Cost Split ── */}
      {hasApiData && penalties.peakPenalty != null && (
        <div className="card-grid-dark">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="w-4 h-4 text-safety-orange-400" />
            <h3 className="text-sm font-semibold text-gray-100">Cost Exposure by Window</h3>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-peak-red-500/10 border border-peak-red-500/30 rounded-lg p-3">
              <p className="text-xs text-gray-400 mb-1">Peak (18–22h)</p>
              <p className="text-xl font-bold font-mono text-peak-red-400">{fmt(penalties.peakPenalty)}</p>
              <p className="text-[10px] text-gray-500 mt-1">
                {penalties.gridshield > 0 ? ((penalties.peakPenalty / penalties.gridshield) * 100).toFixed(0) : '—'}% of total
              </p>
            </div>
            <div className="bg-electric-blue-500/10 border border-electric-blue-500/30 rounded-lg p-3">
              <p className="text-xs text-gray-400 mb-1">Off-Peak</p>
              <p className="text-xl font-bold font-mono text-electric-blue-400">{fmt(penalties.offPeakPenalty)}</p>
              <p className="text-[10px] text-gray-500 mt-1">
                {penalties.gridshield > 0 ? ((penalties.offPeakPenalty / penalties.gridshield) * 100).toFixed(0) : '—'}% of total
              </p>
            </div>
          </div>
          <div className="mt-3 bg-grid-dark-700/50 rounded-lg p-2.5 text-xs text-gray-400">
            <span className="font-semibold text-gray-300">Penalty Asymmetry: </span>
            ₹{underPenalty}/kW under-supply vs ₹{overPenalty}/kW over-supply → optimal α = {optimalAlpha.toFixed(3)}
          </div>
        </div>
      )}

      {/* ── Model Health ── */}
      {hasApiData && (
        <div className="card-grid-dark">
          <div className="flex items-center gap-2 mb-3">
            <Shield className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-semibold text-gray-100">Model Health</h3>
          </div>
          <div className="space-y-0">
            <MetricRow
              label="Forecast Bias (mean actual − forecast)"
              value={penalties.bias !== 'N/A' ? `${parseFloat(penalties.bias) > 0 ? '+' : ''}${penalties.bias} kW` : '—'}
              color={
                penalties.bias === 'N/A' ? 'text-gray-500'
                  : parseFloat(penalties.bias) < 0 ? 'text-success-green-400'
                    : parseFloat(penalties.bias) > 30 ? 'text-peak-red-400'
                      : 'text-electric-blue-400'
              }
              sub={
                penalties.bias !== 'N/A'
                  ? parseFloat(penalties.bias) < 0
                    ? 'Over-forecasting ✓ (protects vs under-supply)'
                    : parseFloat(penalties.bias) > 30
                      ? 'Under-forecasting — high exposure'
                      : 'Near-neutral'
                  : undefined
              }
            />
            <MetricRow
              label="MAE"
              value={penalties.mae !== 'N/A' ? `${penalties.mae} kW` : '—'}
              color="text-gray-200"
              border
            />
            <MetricRow
              label="95th Pct Error"
              value={penalties.p95Error !== 'N/A' ? `${penalties.p95Error} kW` : '—'}
              color="text-safety-orange-400"
              sub="Worst-case exposure per slot"
              border
            />
            <MetricRow
              label="Accuracy (1 − MAPE)"
              value={penalties.accuracy !== 'N/A' ? `${penalties.accuracy}%` : '—'}
              color={parseFloat(penalties.accuracy) >= 90 ? 'text-success-green-400' : 'text-safety-orange-400'}
              border
            />
          </div>
        </div>
      )}

      {/* ── Market Context ── */}
      {dataStats.avg_load != null && (
        <div className="card-grid-dark">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-electric-blue-400" />
            <h3 className="text-sm font-semibold text-gray-100">Market Context</h3>
          </div>
          <div className="space-y-0">
            <MetricRow
              label="Avg load (training baseline)"
              value={`${dataStats.avg_load?.toFixed(0)} kW`}
              color="text-gray-300"
            />
            <MetricRow
              label="Peak uplift (18–22h, historical)"
              value={`+${dataStats.peak_uplift_pct}%`}
              color="text-safety-orange-400"
              border
            />
            <MetricRow
              label="Holiday load impact"
              value={`${dataStats.holiday_impact_pct > 0 ? '+' : ''}${dataStats.holiday_impact_pct}%`}
              color="text-success-green-400"
              border
            />
            <MetricRow
              label="Weekend load impact"
              value={`${dataStats.weekend_impact_pct > 0 ? '+' : ''}${dataStats.weekend_impact_pct}%`}
              color="text-electric-blue-400"
              border
            />
            {weatherSummary?.temperature && (
              <MetricRow
                label="Period avg temperature"
                value={`${weatherSummary.temperature.mean}°C`}
                color="text-safety-orange-400"
                sub={`Temp→Load corr: ${dataStats.correlation_temp || '—'}`}
                border
              />
            )}
          </div>
        </div>
      )}

      {/* ── Bottom line ── */}
      {hasApiData && (
        <div className="rounded-xl bg-gradient-to-br from-electric-blue-500/15 to-grid-dark-800 border border-electric-blue-500/30 p-4">
          <div className="flex items-center gap-2 mb-2">
            {savings > 0
              ? <TrendingDown className="w-4 h-4 text-success-green-400" />
              : <TrendingUp className="w-4 h-4 text-peak-red-400" />
            }
            <span className="text-xs font-bold text-electric-blue-400 uppercase tracking-wider">Bottom Line</span>
          </div>
          <p className="text-xs text-gray-300 leading-relaxed">
            HYBRID strategy delivered{' '}
            <span className="text-success-green-400 font-bold">{fmt(savings)}</span> in penalty savings
            ({savingsPct}% vs naïve) over {startDate} – {endDate}.{' '}
            {parseFloat(coveragePct) >= parseFloat(optimalCoverage) - 5
              ? `Demand coverage ${coveragePct}% is within target range (${optimalCoverage}%).`
              : `Demand coverage ${coveragePct}% is below optimal ${optimalCoverage}% — consider increasing quantile or bias correction.`
            }
          </p>
        </div>
      )}
    </div>
  );
}

export default InsightsPanel;
