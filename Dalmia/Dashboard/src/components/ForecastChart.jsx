import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, ReferenceArea } from 'recharts';

const formatChartTime = (isoString) => {
  const date = new Date(isoString);
  return date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false });
};

function ForecastChart({ data, startDate, endDate, hasApiData, totalRows }) {
  // Calculate overall change metrics
  const totalChange = data.reduce((sum, d) => sum + (d.percentChange || 0), 0) / data.length;
  const maxChange = Math.max(...data.map(d => Math.abs(d.percentChange || 0)));
  const isSignificantlyModified = Math.abs(totalChange) > 1;
  
  // Format data for chart (every 4th point/hourly for cleaner display)
  const chartData = data.filter((_, idx) => idx % 4 === 0).map(point => ({
    time: formatChartTime(point.datetime),
    actual: point.actual,
    forecast: point.forecastHybrid,
    upperBuffer: point.forecastQ90 || point.forecastHybrid, // Q0.90 as safety buffer
    lowerBound: point.forecastQ67 || point.forecastHybrid,
    // Confidence intervals from quantile model spread
    ci95Upper: point.ci95Upper,
    ci95Lower: point.ci95Lower,
    ci90Upper: point.ci90Upper,
    ci90Lower: point.ci90Lower,
    ci50Upper: point.ci50Upper,
    ci50Lower: point.ci50Lower,
    hour: point.hour,
    isPeak: point.isPeak,
    percentChange: point.percentChange || 0,
    isModified: point.isModified,
    // Weather info for tooltip
    temperature: point.temperature,
    humidity: point.humidity,
    heatIndex: point.heatIndex,
    lag7d: point.lag7d,
    isHoliday: point.isHoliday,
  }));

  // Custom tooltip with weather and factor context
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const safetyBuffer = data.forecast && data.actual ? data.forecast - data.actual : null;
      const percentChange = data.percentChange || 0;
      
      return (
        <div className="bg-grid-dark-800 border border-electric-blue-500/30 rounded-lg p-4 shadow-xl max-w-xs">
          <p className="text-xs text-gray-400 mb-2">{data.time} IST</p>
          
          {/* Show modification banner if changed */}
          {Math.abs(percentChange) > 0.5 && (
            <div className={`mb-3 px-2 py-1 rounded text-xs font-bold ${
              percentChange > 0 
                ? 'bg-safety-orange-500/20 text-safety-orange-400' 
                : 'bg-electric-blue-500/20 text-electric-blue-400'
            }`}>
              Modified: {percentChange > 0 ? '+' : ''}{percentChange.toFixed(1)}% from baseline
            </div>
          )}
          
          <div className="space-y-1">
            <div className="flex items-center justify-between gap-4">
              <span className="text-xs text-gray-400">Forecast:</span>
              <span className="text-sm font-mono font-bold text-electric-blue-400">
                {data.forecast?.toFixed(1)} kW
              </span>
            </div>
            {data.actual != null && (
              <div className="flex items-center justify-between gap-4">
                <span className="text-xs text-gray-400">Actual:</span>
                <span className="text-sm font-mono font-bold text-gray-200">
                  {data.actual.toFixed(1)} kW
                </span>
              </div>
            )}
            {safetyBuffer != null && (
              <div className="flex items-center justify-between gap-4">
                <span className="text-xs text-gray-400">Buffer:</span>
                <span className={`text-sm font-mono font-bold ${
                  safetyBuffer > 0 ? 'text-success-green-400' : 'text-peak-red-400'
                }`}>
                  {safetyBuffer > 0 ? '+' : ''}{safetyBuffer.toFixed(1)} kW
                </span>
              </div>
            )}
          </div>
          
          {/* Weather & factor context */}
          {(data.temperature != null || data.lag7d != null) && (
            <div className="mt-2 pt-2 border-t border-grid-dark-600 space-y-1">
              <p className="text-[10px] text-gray-500 uppercase tracking-wide mb-1">Factors at this point</p>
              {data.temperature != null && (
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500">Temp:</span>
                  <span className="text-gray-300 font-mono">{data.temperature}°C</span>
                </div>
              )}
              {data.humidity != null && (
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500">Humidity:</span>
                  <span className="text-gray-300 font-mono">{data.humidity}%</span>
                </div>
              )}
              {data.lag7d != null && (
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500">7d Lag Load:</span>
                  <span className="text-gray-300 font-mono">{data.lag7d} kW</span>
                </div>
              )}
              {data.isHoliday && (
                <span className="text-xs text-success-green-400 font-semibold">📅 Holiday</span>
              )}
            </div>
          )}
          
          {data.isPeak && (
            <div className="mt-2 pt-2 border-t border-grid-dark-600">
              <span className="text-xs text-safety-orange-400 font-semibold">PEAK HOUR (Q0.90 strategy)</span>
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="card-grid-dark">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-100 mb-1">
            {hasApiData && startDate
              ? `Load Forecast: ${startDate} – ${endDate}`
              : 'Load Forecast — Sample Preview'}
          </h2>
          <p className="text-xs text-gray-400">
            {hasApiData
              ? `${totalRows?.toLocaleString() ?? '–'} intervals • 15-min resolution • HYBRID strategy (Q0.67 off-peak + Q0.90 peak)`
              : '15-minute resolution • HYBRID strategy (Q0.67 + Q0.90 peak) • Run prediction to load real data'}
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-electric-blue-500 rounded"></div>
            <span className="text-gray-400">Forecast</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-purple-500/30 rounded"></div>
            <span className="text-gray-400">95% CI</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-success-green-500/40 rounded"></div>
            <span className="text-gray-400">Safety Buffer</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-peak-red-500/20 rounded"></div>
            <span className="text-gray-400">Peak Window</span>
          </div>
        </div>
      </div>

      {/* Modification Indicator Banner */}
      {isSignificantlyModified && (
        <div className={`mb-4 p-4 rounded-lg border-2 ${
          totalChange > 0 
            ? 'bg-safety-orange-500/10 border-safety-orange-500/40' 
            : 'bg-electric-blue-500/10 border-electric-blue-500/40'
        } animate-pulse`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl">⚡</span>
              <div>
                <p className="text-sm font-bold text-gray-100">
                  Scenario Modified: {totalChange > 0 ? 'LOAD INCREASED' : 'LOAD DECREASED'}
                </p>
                <p className="text-xs text-gray-400">
                  Average change: {totalChange > 0 ? '+' : ''}{totalChange.toFixed(1)}%
                  {maxChange > 5 && ` | Peak impact: ${maxChange.toFixed(1)}%`}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className={`text-3xl font-bold font-mono ${
                totalChange > 0 ? 'text-safety-orange-400' : 'text-electric-blue-400'
              }`}>
                {totalChange > 0 ? '+' : ''}{totalChange.toFixed(1)}%
              </p>
              <p className="text-xs text-gray-400">vs baseline</p>
            </div>
          </div>
        </div>
      )}

      <ResponsiveContainer width="100%" height={400}>
        <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            {/* Safety Buffer gradient (green) */}
            <linearGradient id="safetyBuffer" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00ff88" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#00ff88" stopOpacity={0.05} />
            </linearGradient>
            
            {/* Forecast gradient (blue) */}
            <linearGradient id="forecastGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#00d4ff" stopOpacity={0.1} />
            </linearGradient>
            
            {/* Confidence interval gradients */}
            <linearGradient id="ci95Gradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#9333ea" stopOpacity={0.08} />
              <stop offset="95%" stopColor="#9333ea" stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="ci90Gradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#a855f7" stopOpacity={0.12} />
              <stop offset="95%" stopColor="#a855f7" stopOpacity={0.03} />
            </linearGradient>
            <linearGradient id="ci50Gradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#c084fc" stopOpacity={0.18} />
              <stop offset="95%" stopColor="#c084fc" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          
          <CartesianGrid strokeDasharray="3 3" stroke="#2d2d3d" opacity={0.3} />
          
          <XAxis
            dataKey="time"
            stroke="#6b7280"
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            tickLine={{ stroke: '#3d3d4d' }}
          />
          
          <YAxis
            stroke="#6b7280"
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            tickLine={{ stroke: '#3d3d4d' }}
            label={{ value: 'Load (kW)', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
          />
          
          <Tooltip content={<CustomTooltip />} />
          
          {/* Peak Hour Shading (18:00 - 22:00) */}
          {chartData.map((point, idx) => {
            if (point.isPeak && chartData[idx + 1] && !chartData[idx + 1].isPeak) {
              return (
                <ReferenceArea
                  key={`peak-${idx}`}
                  x1={point.time}
                  x2={chartData[idx + 3]?.time || point.time}
                  fill="#ff3366"
                  fillOpacity={0.1}
                  strokeOpacity={0.3}
                  stroke="#ff3366"
                />
              );
            }
            return null;
          })}
          
          {/* 95% Confidence Interval (widest, lightest) */}
          <Area
            type="monotone"
            dataKey="ci95Upper"
            stroke="none"
            fill="url(#ci95Gradient)"
            fillOpacity={0.6}
          />
          <Area
            type="monotone"
            dataKey="ci95Lower"
            stroke="none"
            fill="url(#ci95Gradient)"
            fillOpacity={0.6}
          />
          
          {/* 90% Confidence Interval */}
          <Area
            type="monotone"
            dataKey="ci90Upper"
            stroke="none"
            fill="url(#ci90Gradient)"
            fillOpacity={0.7}
          />
          <Area
            type="monotone"
            dataKey="ci90Lower"
            stroke="none"
            fill="url(#ci90Gradient)"
            fillOpacity={0.7}
          />
          
          {/* 50% Confidence Interval (darkest, highest probability) */}
          <Area
            type="monotone"
            dataKey="ci50Upper"
            stroke="none"
            fill="url(#ci50Gradient)"
            fillOpacity={0.8}
          />
          <Area
            type="monotone"
            dataKey="ci50Lower"
            stroke="none"
            fill="url(#ci50Gradient)"
            fillOpacity={0.8}
          />
          
          {/* Safety Buffer Area (green zone above forecast) */}
          <Area
            type="monotone"
            dataKey="upperBuffer"
            stroke="none"
            fill="url(#safetyBuffer)"
            fillOpacity={1}
          />
          
          {/* Forecast Line */}
          <Area
            type="monotone"
            dataKey="forecast"
            stroke="#00d4ff"
            strokeWidth={3}
            fill="url(#forecastGradient)"
            fillOpacity={1}
          />
          
          {/* Actual Load (dashed line for reference) */}
          <Area
            type="monotone"
            dataKey="actual"
            stroke="#9ca3af"
            strokeWidth={2}
            strokeDasharray="5 5"
            fill="none"
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>


    </div>
  );
}

export default ForecastChart;
