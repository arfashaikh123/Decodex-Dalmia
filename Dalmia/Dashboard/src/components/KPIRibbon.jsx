import React from 'react';
import { 
  AlertCircle, 
  TrendingUp, 
  Zap, 
  ThermometerSun,
  Clock,
  CheckCircle2
} from 'lucide-react';
import KPICard from './KPICard';
import { keyMetrics, liveMetrics, formatNumber, formatCurrency } from '../data/sampleData';

const KPIRibbon = () => {
  const { hours, minutes, isPeakNow } = liveMetrics.timeToNextPeak;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* Primary KPI: Penalty Reduction */}
      <KPICard
        title="Penalty Risk Reduction"
        value={`${keyMetrics.penaltyReduction}%`}
        valueClassName="text-success-green-400 animate-pulse-slow"
        subtitle={`Saved ${formatCurrency(keyMetrics.totalSavings)} vs Naive`}
        trend="up"
        trendValue="vs Baseline"
        className="border-l-4 border-success-green-500 shadow-glow-blue"
      />

      {/* Peak Window Status */}
      <div className="card-grid-dark border-l-4 border-safety-orange-500">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="metric-label">Peak Window Status</p>
            <Clock className="w-4 h-4 text-safety-orange-400" />
          </div>
          {isPeakNow ? (
            <>
              <div className="flex items-center gap-2">
                <AlertCircle className="w-6 h-6 text-peak-red-400 animate-pulse" />
                <span className="text-2xl font-bold text-peak-red-400">ACTIVE</span>
              </div>
              <p className="text-sm text-gray-400">18:00 - 22:00 IST</p>
              <span className="badge-peak">High Risk Period</span>
            </>
          ) : (
            <>
              <div className="metric-value text-electric-blue-400">
                {hours}h {minutes}m
              </div>
              <p className="text-sm text-gray-400">Until next peak window</p>
              <span className="badge-success">
                <CheckCircle2 className="w-3 h-3 mr-1" />
                Monitoring
              </span>
            </>
          )}
        </div>
      </div>

      {/* Current Load vs Forecast */}
      <div className="card-grid-dark">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="metric-label">Current Load vs Forecast</p>
            <Zap className="w-4 h-4 text-electric-blue-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-electric-blue-400">
              {formatNumber(liveMetrics.currentLoad, 1)}
            </span>
            <span className="text-lg text-gray-400">kW</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">Forecast:</span>
            <span className="font-mono text-gray-200">
              {formatNumber(liveMetrics.currentForecast, 1)} kW
            </span>
          </div>
          <div className={`flex items-center gap-1 ${liveMetrics.delta > 0 ? 'text-peak-red-400' : 'text-success-green-400'}`}>
            <TrendingUp className="w-4 h-4" />
            <span className="text-sm font-semibold">
              Δ {formatNumber(Math.abs(liveMetrics.delta), 1)} kW ({liveMetrics.deltaPercent}%)
            </span>
          </div>
        </div>
      </div>

      {/* Weather Impact */}
      <div className="card-grid-dark">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="metric-label">Weather Impact</p>
            <ThermometerSun className="w-4 h-4 text-safety-orange-400" />
          </div>
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">Heat Index</span>
              <span className="text-xl font-bold font-mono text-safety-orange-400">
                {formatNumber(liveMetrics.heatIndex, 1)}°C
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">Temperature</span>
              <span className="font-mono text-gray-200">{formatNumber(liveMetrics.weatherTemp, 1)}°C</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">Humidity</span>
              <span className="font-mono text-gray-200">{liveMetrics.weatherHumidity}%</span>
            </div>
          </div>
          <div className="mt-2">
            {liveMetrics.coolFactor > 0 ? (
              <span className="badge-peak">AC Load Active</span>
            ) : (
              <span className="badge-success">Normal Demand</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default KPIRibbon;
