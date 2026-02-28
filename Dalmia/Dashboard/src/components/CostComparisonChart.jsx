import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

function CostComparisonChart({ penalties, startDate, endDate, underPenalty = 4, overPenalty = 2, explainData }) {
  const optimalAlpha = (underPenalty / (underPenalty + overPenalty)).toFixed(3);
  const asymmetryRatio = (underPenalty / overPenalty).toFixed(1);

  const chartData = [
    {
      strategy: 'Naive\nBaseline',
      penalty: penalties.baseline,
      color: '#ff3366',
      label: 'Strategy A',
    },
    {
      strategy: 'Standard\nMSE',
      penalty: penalties.mse,
      color: '#ff6b35',
      label: 'Strategy B',
    },
  ];

  // Include Q67 and Q90 if available from API
  if (penalties.q67 != null) {
    chartData.push({
      strategy: `Quantile\nQ${optimalAlpha}`,
      penalty: penalties.q67,
      color: '#a855f7',
      label: 'Strategy C',
    });
  }
  if (penalties.q90 != null) {
    chartData.push({
      strategy: 'Quantile\nQ0.90',
      penalty: penalties.q90,
      color: '#f59e0b',
      label: 'Strategy D',
    });
  }

  chartData.push({
    strategy: 'GRIDSHIELD\nHYBRID',
    penalty: penalties.gridshield,
    color: '#00ff88',
    label: 'Strategy E',
  });

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const savingsVsNaive = penalties.baseline - data.penalty;
      const reduction = penalties.baseline > 0 ? ((savingsVsNaive / penalties.baseline) * 100).toFixed(1) : '0';
      
      return (
        <div className="bg-grid-dark-800 border border-electric-blue-500/30 rounded-lg p-4 shadow-xl">
          <p className="text-sm font-semibold text-gray-100 mb-3">{data.strategy.replace('\n', ' ')}</p>
          <div className="space-y-2">
            <div className="flex items-center justify-between gap-6">
              <span className="text-xs text-gray-400">Total Penalty:</span>
              <span className="text-base font-mono font-bold text-gray-200">
                ₹{data.penalty.toLocaleString('en-IN')}
              </span>
            </div>
            {savingsVsNaive !== 0 && (
              <>
                <div className="flex items-center justify-between gap-6">
                  <span className="text-xs text-gray-400">Savings vs Naive:</span>
                  <span className={`text-base font-mono font-bold ${
                    savingsVsNaive > 0 ? 'text-success-green-400' : 'text-peak-red-400'
                  }`}>
                    ₹{Math.abs(savingsVsNaive).toLocaleString('en-IN')}
                  </span>
                </div>
                <div className="flex items-center justify-between gap-6">
                  <span className="text-xs text-gray-400">Reduction:</span>
                  <span className={`text-base font-mono font-bold ${
                    savingsVsNaive > 0 ? 'text-success-green-400' : 'text-peak-red-400'
                  }`}>
                    {reduction}%
                  </span>
                </div>
              </>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="card-grid-dark">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-100 mb-1">
          Cost of Being Wrong: Strategy Comparison
        </h2>
        <p className="text-xs text-gray-400">
          {startDate && endDate
            ? `Total penalty cost: ${startDate} – ${endDate} (₹${underPenalty}/kW under, ₹${overPenalty}/kW over)`
            : 'Total penalty cost across validation period'}
        </p>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2d2d3d" opacity={0.3} />
          
          <XAxis
            dataKey="strategy"
            stroke="#6b7280"
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            tickLine={{ stroke: '#3d3d4d' }}
            angle={0}
            textAnchor="middle"
          />
          
          <YAxis
            stroke="#6b7280"
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            tickLine={{ stroke: '#3d3d4d' }}
            label={{
              value: 'Total Penalty (₹)',
              angle: -90,
              position: 'insideLeft',
              fill: '#9ca3af',
              fontSize: 12,
            }}
            tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}K`}
          />
          
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }} />
          
          <Bar dataKey="penalty" radius={[8, 8, 0, 0]} barSize={60}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.color}
                opacity={entry.strategy.includes('GRIDSHIELD') ? 1 : 0.7}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Key Insight Cards */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-peak-red-500/10 border border-peak-red-500/30 rounded-lg p-4">
          <p className="text-xs text-gray-400 mb-1">Naive Baseline</p>
          <p className="text-2xl font-bold text-peak-red-400 mb-1">
            ₹{penalties.baseline.toLocaleString('en-IN')}
          </p>
          <p className="text-xs text-gray-400">Mean-load copy strategy</p>
        </div>

        <div className="bg-safety-orange-500/10 border border-safety-orange-500/30 rounded-lg p-4">
          <p className="text-xs text-gray-400 mb-1">Standard MSE</p>
          <p className="text-2xl font-bold text-safety-orange-400 mb-1">
            ₹{penalties.mse.toLocaleString('en-IN')}
          </p>
          <p className="text-xs text-gray-400">Minimizes RMSE, not cost</p>
        </div>

        <div className="bg-success-green-500/10 border border-success-green-500/30 rounded-lg p-4">
          <p className="text-xs text-gray-400 mb-1">GRIDSHIELD HYBRID</p>
          <p className="text-2xl font-bold text-success-green-400 mb-1">
            ₹{penalties.gridshield.toLocaleString('en-IN')}
          </p>
          <p className="text-xs text-gray-400">
            Saves ₹{penalties.savingsVsBaseline.toLocaleString('en-IN')} ({penalties.reductionPercent}% less)
          </p>
        </div>
      </div>


    </div>
  );
}

export default CostComparisonChart;
