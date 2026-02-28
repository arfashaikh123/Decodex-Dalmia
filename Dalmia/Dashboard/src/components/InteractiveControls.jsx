import React, { useState } from 'react';
import { Sliders, Play, Download, Info, AlertCircle } from 'lucide-react';
import { keyMetrics, covidImpact, formatNumber } from '../data/sampleData';

const InteractiveControls = ({ onStrategyChange, onHolidayToggle }) => {
  const [selectedStrategy, setSelectedStrategy] = useState('hybrid');
  const [day1Holiday, setDay1Holiday] = useState(true);
  const [day2Holiday, setDay2Holiday] = useState(false);
  const [quantileValue, setQuantileValue] = useState(67);
  const [showCovidInfo, setShowCovidInfo] = useState(false);

  const handleStrategyChange = (strategy) => {
    setSelectedStrategy(strategy);
    onStrategyChange?.(strategy);
  };

  const handleHolidayChange = (day, value) => {
    if (day === 1) {
      setDay1Holiday(value);
    } else {
      setDay2Holiday(value);
    }
    onHolidayToggle?.(day, value);
  };

  const handleExport = () => {
    alert('Generating SLDC Submission File...\n\nFile format: CSV with 192 time slots\nIncludes: HYBRID strategy forecast (Q67 + Q90 peak)\nReady for submission to Mumbai SLDC');
  };

  return (
    <div className="space-y-6">
      {/* Strategy Selection */}
      <div className="card-grid-dark">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-100">Forecast Strategy</h3>
          <Sliders className="w-5 h-5 text-electric-blue-400" />
        </div>

        <div className="space-y-2">
          {[
            { id: 'mse', label: 'Standard MSE', desc: 'Minimizes RMSE (naive)' },
            { id: 'q67', label: 'Quantile 0.67', desc: 'Cost-aware (optimal)' },
            { id: 'q90', label: 'Quantile 0.90', desc: 'Conservative (peak-safe)' },
            { id: 'hybrid', label: 'HYBRID (Recommended)', desc: 'Q67 + Q90 for peaks' },
          ].map((strategy) => (
            <button
              key={strategy.id}
              onClick={() => handleStrategyChange(strategy.id)}
              className={`w-full text-left p-3 rounded-lg border transition-all ${
                selectedStrategy === strategy.id
                  ? 'bg-electric-blue-500/20 border-electric-blue-500 shadow-glow-blue'
                  : 'bg-grid-dark-700 border-grid-dark-600 hover:border-electric-blue-500/50'
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-gray-100">{strategy.label}</p>
                  <p className="text-xs text-gray-400">{strategy.desc}</p>
                </div>
                {strategy.id === 'hybrid' && (
                  <span className="badge-success text-xs">Best</span>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Holiday Toggle */}
      <div className="card-grid-dark">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-100">Holiday Effect</h3>
          <Info className="w-5 h-5 text-safety-orange-400" />
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-grid-dark-700 rounded-lg">
            <div>
              <p className="text-sm font-medium text-gray-100">Day 1 (May 1)</p>
              <p className="text-xs text-gray-400">Maharashtra Din</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={day1Holiday}
                onChange={(e) => handleHolidayChange(1, e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-grid-dark-600 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-electric-blue-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-electric-blue-500"></div>
            </label>
          </div>

          <div className="flex items-center justify-between p-3 bg-grid-dark-700 rounded-lg">
            <div>
              <p className="text-sm font-medium text-gray-100">Day 2 (May 2)</p>
              <p className="text-xs text-gray-400">Saturday</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={day2Holiday}
                onChange={(e) => handleHolidayChange(2, e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-grid-dark-600 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-electric-blue-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-electric-blue-500"></div>
            </label>
          </div>
        </div>

        <div className="mt-3 p-3 bg-safety-orange-500/10 border border-safety-orange-500/30 rounded-lg">
          <p className="text-xs text-gray-300">
            <strong>Effect:</strong> Reduces commercial load by ~8-12% due to office closures
          </p>
        </div>
      </div>

      {/* Quantile Slider */}
      <div className="card-grid-dark">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-100">Quantile Explorer</h3>
          <Sliders className="w-5 h-5 text-electric-blue-400" />
        </div>

        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">Alpha (α)</span>
              <span className="text-xl font-bold font-mono text-electric-blue-400">
                {(quantileValue / 100).toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min="50"
              max="95"
              step="1"
              value={quantileValue}
              onChange={(e) => setQuantileValue(parseInt(e.target.value))}
              className="w-full h-2 bg-grid-dark-700 rounded-lg appearance-none cursor-pointer accent-electric-blue-500"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>0.50 (Median)</span>
              <span>0.67 (Optimal)</span>
              <span>0.95 (Max)</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2 bg-peak-red-500/10 border border-peak-red-500/30 rounded">
              <p className="text-gray-400 mb-1">Under-forecast Risk</p>
              <p className="font-mono text-peak-red-400">
                {formatNumber((100 - quantileValue), 0)}%
              </p>
            </div>
            <div className="p-2 bg-success-green-500/10 border border-success-green-500/30 rounded">
              <p className="text-gray-400 mb-1">Over-forecast Rate</p>
              <p className="font-mono text-success-green-400">
                {formatNumber(quantileValue, 0)}%
              </p>
            </div>
          </div>

          <div className="p-3 bg-electric-blue-500/10 border border-electric-blue-500/30 rounded-lg">
            <p className="text-xs text-gray-300">
              {quantileValue === 67 ? (
                <span className="text-success-green-400">✓ Optimal for ₹4:₹2 penalty ratio</span>
              ) : quantileValue < 67 ? (
                <span className="text-peak-red-400">⚠ High under-forecast risk</span>
              ) : (
                <span className="text-safety-orange-400">⚠ Excessive over-forecast cost</span>
              )}
            </p>
          </div>
        </div>
      </div>

      {/* COVID Regime Indicator */}
      <div className="card-grid-dark border-l-4 border-peak-red-500">
        <button
          onClick={() => setShowCovidInfo(!showCovidInfo)}
          className="w-full flex items-center justify-between mb-3"
        >
          <h3 className="text-lg font-semibold text-gray-100">Structural Shock</h3>
          <AlertCircle className="w-5 h-5 text-peak-red-400" />
        </button>

        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Pre-COVID Avg Load</span>
            <span className="font-mono text-gray-100">{covidImpact.preCovid.avgDailyLoad} kW</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Post-COVID Avg Load</span>
            <span className="font-mono text-gray-100">{covidImpact.postCovid.avgDailyLoad} kW</span>
          </div>
          <div className="flex justify-between pt-2 border-t border-grid-dark-600">
            <span className="text-gray-400">Permanent Shift</span>
            <span className="font-mono text-peak-red-400">{covidImpact.postCovid.changePercent}%</span>
          </div>
        </div>

        {showCovidInfo && (
          <div className="mt-3 p-3 bg-grid-dark-900/50 rounded-lg text-xs text-gray-300">
            <p className="mb-2">
              <strong>March 2020:</strong> Lockdown induced structural change in load pattern.
            </p>
            <p>
              Model includes <code className="px-1 py-0.5 bg-grid-dark-800 rounded text-electric-blue-400">covid_regime</code> feature
              to capture permanent behavioral shift (WFH, reduced commercial activity).
            </p>
          </div>
        )}
      </div>

      {/* Export Action */}
      <button
        onClick={handleExport}
        className="btn-primary w-full flex items-center justify-center gap-2"
      >
        <Download className="w-5 h-5" />
        Generate SLDC Submission File
      </button>
    </div>
  );
};

export default InteractiveControls;
