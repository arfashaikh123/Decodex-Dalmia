import React from 'react';
import { Thermometer, Calendar, DollarSign, TrendingUp, Sliders } from 'lucide-react';

function ScenarioControls({
  tempDeviation,
  setTempDeviation,
  isHoliday,
  setIsHoliday,
  underPenalty,
  setUnderPenalty,
  overPenalty,
  setOverPenalty,
  demandSpike,
  setDemandSpike,
  penalties,
  explainData,
}) {
  // Use real data-driven stats from /api/explain when available
  const dataStats = explainData?.data_statistics || {};
  
  // Temperature sensitivity from real data: kW per °C → approximate % impact
  const tempSensPerC = dataStats.temp_sensitivity_peak_kW_per_C || 0;
  const avgLoad = dataStats.avg_load || 1;
  const tempPctPerC = avgLoad > 0 ? Math.abs(tempSensPerC / avgLoad * 100) : 5;
  
  // Holiday impact from real data
  const holidayPct = dataStats.holiday_impact_pct || -12;
  
  // Calculate combined impact using data-driven rates
  const tempImpact = tempDeviation * tempPctPerC;
  const holidayImpact = isHoliday ? holidayPct : 0;
  const spikeImpact = demandSpike; // Direct percentage
  const totalImpact = tempImpact + holidayImpact + spikeImpact;
  const isModified = Math.abs(totalImpact) > 1;
  
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="card-grid-dark">
        <div className="flex items-center gap-3 mb-2">
          <Sliders className="w-5 h-5 text-electric-blue-400" />
          <h2 className="text-lg font-bold text-gray-100">What-If Scenarios</h2>
        </div>
        <p className="text-xs text-gray-400">
          Adjust parameters to stress-test grid resilience
        </p>
      </div>

      {/* Total Impact Indicator */}
      {isModified && (
        <div className={`border-2 rounded-xl p-5 ${
          totalImpact > 0 
            ? 'bg-gradient-to-br from-safety-orange-500/20 to-safety-orange-500/5 border-safety-orange-500/40 animate-pulse' 
            : 'bg-gradient-to-br from-electric-blue-500/20 to-electric-blue-500/5 border-electric-blue-500/40 animate-pulse'
        }`}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="text-2xl">⚡</span>
              <span className="text-xs text-gray-400 uppercase tracking-wider font-semibold">
                Combined Scenario Impact
              </span>
            </div>
            <div className={`text-3xl font-bold font-mono ${
              totalImpact > 0 ? 'text-safety-orange-400' : 'text-electric-blue-400'
            }`}>
              {totalImpact > 0 ? '+' : ''}{totalImpact.toFixed(1)}%
            </div>
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            {Math.abs(tempImpact) > 0 && (
              <div className="text-center">
                <p className="text-gray-500">Temp</p>
                <p className={`font-bold ${tempImpact > 0 ? 'text-safety-orange-400' : 'text-electric-blue-400'}`}>
                  {tempImpact > 0 ? '+' : ''}{tempImpact.toFixed(1)}%
                </p>
              </div>
            )}
            {holidayImpact !== 0 && (
              <div className="text-center">
                <p className="text-gray-500">Holiday</p>
                <p className="font-bold text-success-green-400">{holidayImpact.toFixed(0)}%</p>
              </div>
            )}
            {spikeImpact > 0 && (
              <div className="text-center">
                <p className="text-gray-500">Spike</p>
                <p className="font-bold text-safety-orange-400">+{spikeImpact.toFixed(0)}%</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Total Financial Impact */}
      <div className="bg-gradient-to-br from-success-green-500/20 to-success-green-500/5 border-2 border-success-green-500/40 rounded-xl p-6">
        <p className="text-xs text-gray-400 uppercase tracking-wider font-semibold mb-2">
          Current Penalty Estimate
        </p>
        <p className="text-4xl font-bold text-success-green-400 mb-1">
          ₹{penalties.gridshield.toLocaleString('en-IN')}
        </p>
        <p className="text-xs text-gray-400 mt-2">
          Based on current scenario parameters
        </p>
      </div>

      {/* Control 1: Weather Simulator */}
      <div className="card-grid-dark">
        <div className="flex items-center gap-2 mb-4">
          <Thermometer className="w-4 h-4 text-safety-orange-400" />
          <h3 className="text-sm font-semibold text-gray-100">Temperature Deviation</h3>
        </div>
        
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400">Deviation from period baseline</span>
            <span className={`text-sm font-bold ${
              tempDeviation > 0 ? 'text-safety-orange-400' : 
              tempDeviation < 0 ? 'text-electric-blue-400' : 
              'text-gray-300'
            }`}>
              {tempDeviation > 0 ? '+' : ''}{tempDeviation}°C
            </span>
          </div>
          
          <input
            type="range"
            min="-5"
            max="10"
            step="0.5"
            value={tempDeviation}
            onChange={(e) => setTempDeviation(parseFloat(e.target.value))}
            className="w-full h-2 bg-grid-dark-700 rounded-lg appearance-none cursor-pointer accent-safety-orange-500"
          />
          
          <div className="flex justify-between text-xs text-gray-500">
            <span>-5°C</span>
            <span>0</span>
            <span>+10°C</span>
          </div>
          
          <div className="bg-grid-dark-700 rounded-lg p-3 text-xs text-gray-400">
            <p className="leading-relaxed">
              {tempDeviation > 3 ? `🔥 Heat wave: ~${tempPctPerC.toFixed(1)}% cooling load per °C (sensitivity: ${tempSensPerC} kW/°C from training data)` :
               tempDeviation > 0 ? `⚠️ Warmer: +${(tempDeviation * tempPctPerC).toFixed(1)}% estimated load increase` :
               tempDeviation < -2 ? '❄️ Cool weather: Reduced AC demand significantly' :
               tempDeviation < 0 ? `❄️ Cooler: ~${(tempDeviation * tempPctPerC).toFixed(1)}% load reduction` :
               '☀️ Normal conditions (baseline)'}
            </p>
            {Math.abs(tempDeviation) > 0 && (
              <p className="mt-2 font-semibold text-electric-blue-400">
                → Forecast shifted by ~{Math.abs(tempDeviation * tempPctPerC).toFixed(1)}% ({tempSensPerC ? `${(tempDeviation * tempSensPerC).toFixed(0)} kW` : 'estimated'})
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Control 2: Holiday Toggle */}
      <div className="card-grid-dark">
        <div className="flex items-center gap-2 mb-4">
          <Calendar className="w-4 h-4 text-success-green-400" />
          <h3 className="text-sm font-semibold text-gray-100">Holiday Override</h3>
        </div>
        
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400">Public holiday / restricted day</span>
            <button
              onClick={() => setIsHoliday(!isHoliday)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                isHoliday ? 'bg-success-green-500' : 'bg-grid-dark-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  isHoliday ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
          
          <div className="bg-grid-dark-700 rounded-lg p-3 text-xs text-gray-400">
            <p className="leading-relaxed">
              {isHoliday
                ? `📅 Holiday mode: Historical data shows ${holidayPct > 0 ? '+' : ''}${holidayPct.toFixed(1)}% load change on holidays vs normal days`
                : '⚠️ Normal workday: Full commercial/industrial consumption active'}
            </p>
            {isHoliday && (
              <p className="mt-2 font-semibold text-success-green-400">
                → Total load ~{Math.abs(holidayPct).toFixed(0)}% {holidayPct < 0 ? 'lower' : 'higher'} than normal weekday
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Control 3: Penalty Rates */}
      <div className="card-grid-dark">
        <div className="flex items-center gap-2 mb-4">
          <DollarSign className="w-4 h-4 text-electric-blue-400" />
          <h3 className="text-sm font-semibold text-gray-100">Penalty Rates</h3>
        </div>
        
        <div className="space-y-4">
          {/* Under-forecast penalty */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-gray-400">Under-forecast (Actual &gt; Forecast)</span>
              <span className="text-sm font-bold text-peak-red-400">
                ₹{underPenalty}/kW
              </span>
            </div>
            <input
              type="range"
              min="2"
              max="8"
              step="0.5"
              value={underPenalty}
              onChange={(e) => setUnderPenalty(parseFloat(e.target.value))}
              className="w-full h-2 bg-grid-dark-700 rounded-lg appearance-none cursor-pointer accent-peak-red-500"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>₹2</span>
              <span>₹8</span>
            </div>
          </div>
          
          {/* Over-forecast penalty */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-gray-400">Over-forecast (Forecast &gt; Actual)</span>
              <span className="text-sm font-bold text-success-green-400">
                ₹{overPenalty}/kW
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="5"
              step="0.5"
              value={overPenalty}
              onChange={(e) => setOverPenalty(parseFloat(e.target.value))}
              className="w-full h-2 bg-grid-dark-700 rounded-lg appearance-none cursor-pointer accent-success-green-500"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>₹1</span>
              <span>₹5</span>
            </div>
          </div>
          
          <div className="bg-grid-dark-700 rounded-lg p-3 text-xs text-gray-400">
            <p className="leading-relaxed">
              Asymmetry ratio: {(underPenalty / overPenalty).toFixed(2)}x — optimal quantile α = {(underPenalty / (underPenalty + overPenalty)).toFixed(3)}
              {underPenalty / overPenalty >= 2 ? ' (Bias-high: over-forecast preferred)' : ' (Near-symmetric penalty structure)'}
            </p>
          </div>
        </div>
      </div>

      {/* Control 4: Demand Spike */}
      <div className="card-grid-dark">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-4 h-4 text-safety-orange-400" />
          <h3 className="text-sm font-semibold text-gray-100">Unexpected Demand Spike</h3>
        </div>
        
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400">Growth %</span>
            <span className={`text-sm font-bold ${
              demandSpike > 0 ? 'text-safety-orange-400' : 'text-gray-300'
            }`}>
              +{demandSpike}%
            </span>
          </div>
          
          <input
            type="range"
            min="0"
            max="25"
            step="1"
            value={demandSpike}
            onChange={(e) => setDemandSpike(parseFloat(e.target.value))}
            className="w-full h-2 bg-grid-dark-700 rounded-lg appearance-none cursor-pointer accent-safety-orange-500"
          />
          
          <div className="flex justify-between text-xs text-gray-500">
            <span>0%</span>
            <span>+25%</span>
          </div>
          
          <div className="bg-grid-dark-700 rounded-lg p-3 text-xs text-gray-400">
            <p className="leading-relaxed">
              {demandSpike === 0 ? '✅ Normal demand pattern' :
               demandSpike <= 10 ? `⚠️ Moderate spike: +${demandSpike}% base load. Peak hours (18-22) have ${(dataStats.peak_uplift_pct || 0).toFixed(0)}% historical uplift.` :
               demandSpike <= 20 ? `🔥 Major spike: +${demandSpike}% load. Peak-hour demand will be amplified further.` :
               `🚨 CRITICAL SPIKE: +${demandSpike}% base demand. Grid under severe stress.`}
            </p>
            {demandSpike > 0 && (
              <p className="mt-2 font-semibold text-safety-orange-400">
                → Evening peak (18-22) especially vulnerable with {(dataStats.peak_uplift_pct || 0).toFixed(0)}% baseline uplift
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Reset Button */}
      <button
        onClick={() => {
          setTempDeviation(0);
          setIsHoliday(false);
          setUnderPenalty(4);
          setOverPenalty(2);
          setDemandSpike(0);
        }}
        className="w-full bg-grid-dark-700 hover:bg-grid-dark-600 border border-grid-dark-600 hover:border-electric-blue-500/50 text-gray-300 py-3 rounded-lg font-medium text-sm transition-all"
      >
        Reset to Baseline
      </button>
    </div>
  );
}

export default ScenarioControls;
