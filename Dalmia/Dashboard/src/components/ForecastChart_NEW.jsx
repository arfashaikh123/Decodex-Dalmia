import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, ReferenceArea } from 'recharts';
import { formatTime } from '../data/sampleData';

function ForecastChart({ data }) {
  // Format data for chart (every 4th point/hourly for cleaner display)
  const chartData = data.filter((_, idx) => idx % 4 === 0).map(point => ({
    time: formatTime(point.datetime),
    actual: point.actual,
    forecast: point.forecastHybrid,
    upperBuffer: point.forecastHybrid + 30, // Safety buffer visualization
    lowerBound: point.forecastHybrid - 20,
    hour: point.hour,
    isPeak: point.isPeak,
  }));

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const safetyBuffer = data.forecast - data.actual;
      
      return (
        <div className="bg-grid-dark-800 border border-electric-blue-500/30 rounded-lg p-4 shadow-xl">
          <p className="text-xs text-gray-400 mb-2">{data.time} IST</p>
          <div className="space-y-1">
            <div className="flex items-center justify-between gap-4">
              <span className="text-xs text-gray-400">Forecast:</span>
              <span className="text-sm font-mono font-bold text-electric-blue-400">
                {data.forecast.toFixed(1)} kW
              </span>
            </div>
            <div className="flex items-center justify-between gap-4">
              <span className="text-xs text-gray-400">Actual:</span>
              <span className="text-sm font-mono font-bold text-gray-200">
                {data.actual.toFixed(1)} kW
              </span>
            </div>
            <div className="flex items-center justify-between gap-4">
              <span className="text-xs text-gray-400">Safety Buffer:</span>
              <span className={`text-sm font-mono font-bold ${
                safetyBuffer > 0 ? 'text-success-green-400' : 'text-peak-red-400'
              }`}>
                {safetyBuffer > 0 ? '+' : ''}{safetyBuffer.toFixed(1)} kW
              </span>
            </div>
          </div>
          {data.isPeak && (
            <div className="mt-2 pt-2 border-t border-grid-dark-600">
              <span className="text-xs text-safety-orange-400 font-semibold">🔴 PEAK HOUR</span>
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
            48-Hour Load Forecast with Safety Buffer
          </h2>
          <p className="text-xs text-gray-400">
            May 1-2, 2021 • 15-minute resolution • HYBRID strategy (Q0.67 + Peak Boost)
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-electric-blue-500 rounded"></div>
            <span className="text-gray-400">Forecast</span>
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
                  strokeOpacity={0.3}stroke="#ff3366"
                />
              );
            }
            return null;
          })}
          
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

      {/* Chart Legend & Info */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-grid-dark-700/50 rounded-lg">
        <div>
          <p className="text-xs text-gray-400 mb-1">Peak Window Strategy</p>
          <p className="text-sm font-semibold text-gray-200">
            Conservative Q0.90 forecast during 18:00-22:00
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-400 mb-1">Safety Buffer</p>
          <p className="text-sm font-semibold text-gray-200">
            Green zone: Over-forecast protection (₹2/kWh cost)
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-400 mb-1">Risk Management</p>
          <p className="text-sm font-semibold text-gray-200">
            Minimizes ₹4/kWh under-forecast penalties
          </p>
        </div>
      </div>
    </div>
  );
}

export default ForecastChart;
