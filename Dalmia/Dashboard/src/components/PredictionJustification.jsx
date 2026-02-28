import React, { useState } from 'react';
import { Brain, ChevronDown, ChevronUp, TrendingUp, TrendingDown, Minus } from 'lucide-react';

function PredictionJustification({ justification, startDate, endDate }) {
  const [expanded, setExpanded] = useState(true);

  if (!justification) return null;

  const { summary, reasons, top_drivers, period_stats } = justification;

  const impactColor = (val) => {
    if (val > 2) return 'text-safety-orange-400';
    if (val < -2) return 'text-electric-blue-400';
    return 'text-gray-400';
  };

  const impactBg = (val) => {
    if (val > 2) return 'bg-safety-orange-500/10 border-safety-orange-500/30';
    if (val < -2) return 'bg-electric-blue-500/10 border-electric-blue-500/30';
    return 'bg-grid-dark-700/50 border-grid-dark-600';
  };

  const TrendIcon = ({ val }) => {
    if (val > 2) return <TrendingUp className="w-4 h-4 text-safety-orange-400" />;
    if (val < -2) return <TrendingDown className="w-4 h-4 text-electric-blue-400" />;
    return <Minus className="w-4 h-4 text-gray-500" />;
  };

  // Category for driver features
  const driverCategory = (feat) => {
    if (feat.includes('lag') || feat.includes('rolling') || feat.includes('daily'))
      return { label: 'Historical', color: 'bg-purple-500' };
    if (['ACT_TEMP','ACT_HUMIDITY','ACT_RAIN','ACT_HEAT_INDEX','COOL_FACTOR',
         'temp_humidity','heat_rain','temp_sq','cool_sq','is_hot'].includes(feat))
      return { label: 'Weather', color: 'bg-safety-orange-500' };
    if (['hour','minute','sin_hour','cos_hour','dayofweek','sin_dow','cos_dow',
         'month','sin_month','cos_month','time_of_day','dayofyear','weekofyear',
         'year','day','quarter','is_weekend'].includes(feat))
      return { label: 'Temporal', color: 'bg-electric-blue-500' };
    return { label: 'Other', color: 'bg-gray-500' };
  };

  return (
    <div className="card-grid-dark border-l-4 border-purple-500 bg-purple-500/5">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between mb-2"
      >
        <div className="flex items-center gap-3">
          <Brain className="w-5 h-5 text-purple-400" />
          <h2 className="text-lg font-bold text-gray-100">
            Why This Prediction?
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">{startDate} – {endDate}</span>
          {expanded
            ? <ChevronUp className="w-4 h-4 text-gray-400" />
            : <ChevronDown className="w-4 h-4 text-gray-400" />}
        </div>
      </button>

      {/* Summary */}
      <p className="text-xs text-gray-400 leading-relaxed mb-4">{summary}</p>

      {expanded && (
        <div className="space-y-4">
          {/* Period overview */}
          {period_stats && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-grid-dark-700/50 rounded-lg p-3 text-center">
                <p className="text-[10px] text-gray-500 uppercase mb-1">Predicted Avg</p>
                <p className="text-lg font-mono font-bold text-electric-blue-400">
                  {period_stats.predicted_avg} kW
                </p>
              </div>
              <div className="bg-grid-dark-700/50 rounded-lg p-3 text-center">
                <p className="text-[10px] text-gray-500 uppercase mb-1">vs Training Mean</p>
                <p className={`text-lg font-mono font-bold ${impactColor(period_stats.deviation_pct)}`}>
                  {period_stats.deviation_pct > 0 ? '+' : ''}{period_stats.deviation_pct}%
                </p>
              </div>
              <div className="bg-grid-dark-700/50 rounded-lg p-3 text-center">
                <p className="text-[10px] text-gray-500 uppercase mb-1">Peak Intervals</p>
                <p className="text-lg font-mono font-bold text-peak-red-400">
                  {period_stats.n_peak_intervals}
                </p>
              </div>
              <div className="bg-grid-dark-700/50 rounded-lg p-3 text-center">
                <p className="text-[10px] text-gray-500 uppercase mb-1">Temp Δ</p>
                <p className={`text-lg font-mono font-bold ${impactColor(period_stats.temp_delta)}`}>
                  {period_stats.temp_delta > 0 ? '+' : ''}{period_stats.temp_delta}°C
                </p>
              </div>
            </div>
          )}

          {/* Factor-by-factor reasons */}
          {reasons && reasons.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs text-gray-500 uppercase tracking-wide font-semibold">
                Key Factors Driving This Forecast
              </p>
              {reasons.map((r, i) => (
                <div
                  key={i}
                  className={`border rounded-lg p-3 ${impactBg(r.impact)}`}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-lg flex-shrink-0 mt-0.5">{r.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <p className="text-sm font-semibold text-gray-200">{r.factor}</p>
                        <div className="flex items-center gap-1">
                          <TrendIcon val={r.impact} />
                          <span className={`text-xs font-mono font-bold ${impactColor(r.impact)}`}>
                            {r.impact > 0 ? '+' : ''}{r.impact.toFixed(1)}%
                          </span>
                        </div>
                      </div>
                      <p className="text-xs text-gray-400 leading-relaxed">{r.detail}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Top feature drivers */}
          {top_drivers && top_drivers.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide font-semibold mb-2">
                Top Model Features for This Period
              </p>
              <div className="space-y-1.5">
                {top_drivers.map((d, i) => {
                  const cat = driverCategory(d.feature);
                  const maxScore = top_drivers[0].importance_rank_score || 1;
                  const barWidth = Math.min(100, (d.importance_rank_score / maxScore) * 100);
                  return (
                    <div key={i} className="flex items-center gap-2 text-xs">
                      <span className={`w-2 h-2 rounded-full flex-shrink-0 ${cat.color}`}></span>
                      <span className="text-gray-400 truncate w-32" title={d.feature}>
                        {d.feature}
                      </span>
                      <div className="flex-1 h-2 bg-grid-dark-700 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${cat.color} rounded-full`}
                          style={{ width: `${barWidth}%` }}
                        ></div>
                      </div>
                      <span className={`w-16 text-right font-mono ${
                        d.direction === 'higher' ? 'text-safety-orange-400' :
                        d.direction === 'lower' ? 'text-electric-blue-400' :
                        'text-gray-500'
                      }`}>
                        {d.period_value}
                      </span>
                      <span className="text-gray-600 w-4 text-center">
                        {d.direction === 'higher' ? '↑' : d.direction === 'lower' ? '↓' : '–'}
                      </span>
                    </div>
                  );
                })}
              </div>
              <p className="text-[10px] text-gray-600 mt-2">
                Bars show feature importance × deviation from training average. Values show this period's average.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default PredictionJustification;
