import React, { useState, useMemo } from 'react';
import { Activity, Zap, Download, TrendingDown, Shield, AlertTriangle, DollarSign } from 'lucide-react';
import { getBaselineData, applyScenarioModifiers, calculatePenalties } from './data/sampleData';
import ForecastChart from './components/ForecastChart';
import ScenarioControls from './components/ScenarioControls';
import CostComparisonChart from './components/CostComparisonChart';
import InsightsPanel from './components/InsightsPanel';

function App() {
  // Scenario state
  const [tempDeviation, setTempDeviation] = useState(0); // °C deviation
  const [isHoliday, setIsHoliday] = useState(true); // May 1st Maharashtra Din
  const [underPenalty, setUnderPenalty] = useState(4); // ₹/kWh
  const [overPenalty, setOverPenalty] = useState(2); // ₹/kWh
  const [demandSpike, setDemandSpike] = useState(0); // % increase

  // Apply scenario modifications to forecast data
  const modifiedData = useMemo(() => {
    const baseData = getBaselineData();
    return applyScenarioModifiers(baseData, {
      tempDeviation,
      isHoliday,
      demandSpike,
    });
  }, [tempDeviation, isHoliday, demandSpike]);

  // Calculate penalties with current penalty rates
  const penalties = useMemo(() => {
    return calculatePenalties(modifiedData, underPenalty, overPenalty);
  }, [modifiedData, underPenalty, overPenalty]);

  // Export forecast to CSV
  const handleExport = () => {
    const csv = [
      ['DateTime', 'TimeSlot', 'Forecast_kW', 'Peak_Window', 'Holiday'],
      ...modifiedData.map(d => [
        d.datetime,
        d.timeSlot,
        d.forecastHybrid.toFixed(2),
        d.isPeak ? 'Yes' : 'No',
        d.isHoliday ? 'Yes' : 'No'
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `GRIDSHIELD_SLDC_Schedule_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

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
                  <h1 className="text-3xl font-bold text-gray-100 tracking-tight">
                    GRIDSHIELD
                  </h1>
                  <p className="text-xs text-gray-400 font-medium uppercase tracking-wider">
                    Executive Command • Mumbai DISCOM
                  </p>
                </div>
              </div>
              <div className="hidden lg:flex items-center gap-2 ml-8 px-3 py-1 bg-success-green-500/10 border border-success-green-500/30 rounded-full">
                <Activity className="w-3 h-3 text-success-green-400 animate-pulse" />
                <span className="text-xs text-success-green-400 font-semibold">OPERATIONAL</span>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="hidden md:block text-right mr-4">
                <p className="text-xs text-gray-400">Forecast Window</p>
                <p className="text-sm font-bold text-electric-blue-400">
                  May 1-2, 2021 • 48 Hours
                </p>
              </div>
              <button
                onClick={handleExport}
                className="bg-gradient-to-r from-electric-blue-500 to-electric-blue-600 hover:from-electric-blue-600 hover:to-electric-blue-700 text-white px-6 py-2.5 rounded-lg font-semibold text-sm flex items-center gap-2 shadow-lg shadow-electric-blue-500/30 transition-all"
              >
                <Download className="w-4 h-4" />
                <span>Export SLDC Schedule</span>
              </button>
            </div>
          </div>
        </div>
      </header>

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
                ₹{(penalties.baseline - penalties.gridshield).toLocaleString('en-IN')}
              </p>
              <p className="text-xs text-gray-400">vs Baseline Model (3-month validation)</p>
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
                {((1 - penalties.gridshield / penalties.baseline) * 100).toFixed(1)}%
              </p>
              <p className="text-xs text-gray-400">Penalty Exposure Reduced</p>
            </div>
          </div>

          {/* KPI 3: Critical Window Alert */}
          <div className="relative bg-gradient-to-br from-safety-orange-500/20 to-safety-orange-500/5 border-2 border-safety-orange-500/40 rounded-xl p-6 overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-safety-orange-500/10 rounded-full blur-3xl animate-pulse"></div>
            <div className="relative">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs text-gray-400 uppercase tracking-wider font-semibold">Next Peak Alert</p>
                <AlertTriangle className="w-5 h-5 text-safety-orange-400" />
              </div>
              <p className="text-4xl font-bold text-safety-orange-400 mb-1">
                18:00 - 22:00
              </p>
              <p className="text-xs text-gray-400">High Penalty Risk Window (Today)</p>
            </div>
          </div>

          {/* KPI 4: Forecast Confidence */}
          <div className="relative bg-gradient-to-br from-grid-dark-700 to-grid-dark-800 border-2 border-grid-dark-600 rounded-xl p-6 overflow-hidden">
            <div className="relative">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs text-gray-400 uppercase tracking-wider font-semibold">Forecast Strategy</p>
                <TrendingDown className="w-5 h-5 text-electric-blue-400" />
              </div>
              <p className="text-4xl font-bold text-gray-100 mb-1">
                HYBRID
              </p>
              <p className="text-xs text-gray-400">Quantile 0.67 + Peak Boost</p>
            </div>
          </div>
        </div>

        {/* Main Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left: Scenario Controls */}
          <div className="lg:col-span-1">
            <ScenarioControls
              tempDeviation={tempDeviation}
              setTempDeviation={setTempDeviation}
              isHoliday={isHoliday}
              setIsHoliday={setIsHoliday}
              underPenalty={underPenalty}
              setUnderPenalty={setUnderPenalty}
              overPenalty={overPenalty}
              setOverPenalty={setOverPenalty}
              demandSpike={demandSpike}
              setDemandSpike={setDemandSpike}
              penalties={penalties}
            />
          </div>

          {/* Center: Forecast Chart + Cost Comparison */}
          <div className="lg:col-span-2 space-y-6">
            <ForecastChart data={modifiedData} />
            <CostComparisonChart penalties={penalties} />
          </div>

          {/* Right: Insights */}
          <div className="lg:col-span-1">
            <InsightsPanel
              data={modifiedData}
              penalties={penalties}
              tempDeviation={tempDeviation}
              isHoliday={isHoliday}
            />
          </div>
        </div>

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
                GRIDSHIELD Stage 1: Profit-Maximization Through Cost-Aware Forecasting
              </h3>
              <p className="text-sm text-gray-400 leading-relaxed mb-3">
                This dashboard demonstrates a <span className="text-electric-blue-400 font-semibold">49.4% penalty reduction</span> vs naive baseline 
                using asymmetric quantile regression optimized for Mumbai ABT penalty structure (₹4 under-forecast, ₹2 over-forecast).
              </p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                <div>
                  <p className="text-gray-500 mb-1">Training Period</p>
                  <p className="text-gray-300 font-semibold">Apr 2013 - Jan 2021</p>
                </div>
                <div>
                  <p className="text-gray-500 mb-1">Validation</p>
                  <p className="text-gray-300 font-semibold">Feb - Apr 2021</p>
                </div>
                <div>
                  <p className="text-gray-500 mb-1">Resolution</p>
                  <p className="text-gray-300 font-semibold">15-minute intervals</p>
                </div>
                <div>
                  <p className="text-gray-500 mb-1">Observations</p>
                  <p className="text-gray-300 font-semibold">283,391 data points</p>
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
            </p>
            <div className="flex items-center gap-6 text-xs text-gray-400">
              <span>Powered by LightGBM</span>
              <span>•</span>
              <span>Real-time Scenario Modeling</span>
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
