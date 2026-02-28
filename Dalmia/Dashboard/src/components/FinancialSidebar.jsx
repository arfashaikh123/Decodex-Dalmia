import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { DollarSign, TrendingDown, AlertTriangle, CheckCircle } from 'lucide-react';
import { backtestMetrics, keyMetrics, formatCurrency, formatNumber } from '../data/sampleData';

const FinancialSidebar = () => {
  // Prepare penalty comparison data
  const penaltyData = [
    { name: 'Naive', value: backtestMetrics.naive.totalPenalty, color: '#6b7280' },
    { name: 'MSE', value: backtestMetrics.mse.totalPenalty, color: '#00d4ff' },
    { name: 'Q0.67', value: backtestMetrics.q67.totalPenalty, color: '#00ff88' },
    { name: 'Q0.90', value: backtestMetrics.q90.totalPenalty, color: '#ff8555' },
    { name: 'HYBRID', value: backtestMetrics.hybrid.totalPenalty, color: '#ffcc00' },
  ];

  // Custom tooltip for penalty chart
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <div className="bg-grid-dark-800 border border-grid-dark-600 p-3 rounded-lg shadow-xl">
          <p className="text-sm font-semibold text-gray-100 mb-1">{data.payload.name}</p>
          <p className="text-lg font-mono font-bold text-electric-blue-400">
            {formatCurrency(data.value)}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Financial Asymmetry Explanation */}
      <div className="card-grid-dark border-l-4 border-safety-orange-500">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-100">Financial Asymmetry</h3>
            <AlertTriangle className="w-5 h-5 text-safety-orange-400" />
          </div>
          
          <div className="space-y-2">
            <div className="bg-peak-red-500/10 border border-peak-red-500/30 rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-gray-400">Under-forecast Penalty</span>
                <AlertTriangle className="w-4 h-4 text-peak-red-400" />
              </div>
              <div className="text-2xl font-bold font-mono text-peak-red-400">
                ₹4 <span className="text-sm text-gray-400">/ kWh</span>
              </div>
              <p className="text-xs text-gray-400 mt-1">When Actual &gt; Forecast</p>
            </div>

            <div className="bg-success-green-500/10 border border-success-green-500/30 rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-gray-400">Over-forecast Penalty</span>
                <CheckCircle className="w-4 h-4 text-success-green-400" />
              </div>
              <div className="text-2xl font-bold font-mono text-success-green-400">
                ₹2 <span className="text-sm text-gray-400">/ kWh</span>
              </div>
              <p className="text-xs text-gray-400 mt-1">When Forecast &gt; Actual</p>
            </div>
          </div>

          <div className="bg-electric-blue-500/10 border border-electric-blue-500/30 rounded-lg p-3 mt-3">
            <p className="text-xs text-gray-400 mb-1">Optimal Quantile</p>
            <div className="text-xl font-bold font-mono text-electric-blue-400">
              α = {keyMetrics.optimalQuantile}
            </div>
            <p className="text-xs text-gray-400 mt-1">
              Calculated as 4/(4+2) = 0.667
            </p>
          </div>
        </div>
      </div>

      {/* Penalty Comparison Chart */}
      <div className="card-grid-dark">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-100 mb-1">
            Penalty Comparison
          </h3>
          <p className="text-sm text-gray-400">
            Validation Period: {keyMetrics.validationPeriod}
          </p>
        </div>

        <ResponsiveContainer width="100%" height={300}>
          <BarChart
            data={penaltyData}
            margin={{ top: 10, right: 10, left: 10, bottom: 60 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#2d2d3d" />
            <XAxis
              dataKey="name"
              stroke="#6b7280"
              angle={-45}
              textAnchor="end"
              height={60}
              style={{ fontSize: '12px' }}
            />
            <YAxis
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
              tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}K`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="value" radius={[8, 8, 0, 0]}>
              {penaltyData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Money Saved Counter */}
      <div className="card-grid-dark bg-gradient-to-br from-success-green-500/10 to-transparent border-l-4 border-success-green-500">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-gray-300">Total Savings</h3>
            <DollarSign className="w-5 h-5 text-success-green-400" />
          </div>
          
          <div className="space-y-2">
            <div className="text-3xl font-bold font-mono text-success-green-400">
              {formatCurrency(keyMetrics.totalSavings)}
            </div>
            <p className="text-sm text-gray-400">
              vs Naive Baseline (3 months)
            </p>
          </div>

          <div className="flex items-center gap-2 pt-3 border-t border-grid-dark-600">
            <TrendingDown className="w-4 h-4 text-success-green-400" />
            <span className="text-xl font-bold text-success-green-400">
              {keyMetrics.penaltyReduction}%
            </span>
            <span className="text-sm text-gray-400">penalty reduction</span>
          </div>

          <div className="bg-grid-dark-900/50 rounded p-3 mt-3">
            <p className="text-xs text-gray-400 mb-2">Annual Projection</p>
            <div className="text-2xl font-bold font-mono text-electric-blue-400">
              {formatCurrency(keyMetrics.totalSavings * 4)}
            </div>
          </div>
        </div>
      </div>

      {/* Strategy Breakdown */}
      <div className="card-grid-dark">
        <h3 className="text-sm font-semibold text-gray-100 mb-3">
          Best Strategy: LightGBM Q0.67
        </h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Total Penalty</span>
            <span className="font-mono text-gray-100">
              {formatCurrency(backtestMetrics.q67.totalPenalty)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Under-forecast</span>
            <span className="font-mono text-peak-red-400">
              {formatCurrency(backtestMetrics.q67.underForecastPenalty)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Over-forecast</span>
            <span className="font-mono text-success-green-400">
              {formatCurrency(backtestMetrics.q67.overForecastPenalty)}
            </span>
          </div>
          <div className="flex justify-between pt-2 border-t border-grid-dark-600">
            <span className="text-gray-400">MAE</span>
            <span className="font-mono text-gray-100">{backtestMetrics.q67.mae} kW</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">RMSE</span>
            <span className="font-mono text-gray-100">{backtestMetrics.q67.rmse} kW</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">MAPE</span>
            <span className="font-mono text-gray-100">{backtestMetrics.q67.mape}%</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FinancialSidebar;
