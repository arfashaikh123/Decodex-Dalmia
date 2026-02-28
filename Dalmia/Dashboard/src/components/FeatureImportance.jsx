import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { TrendingUp } from 'lucide-react';
import { featureImportance, formatNumber } from '../data/sampleData';

const FeatureImportance = ({ topN = 10 }) => {
  // Get top N features
  const topFeatures = featureImportance.slice(0, topN);

  // Category colors
  const categoryColors = {
    'Lag Features': '#00d4ff',
    'Temporal': '#ff8555',
    'Weather': '#ffcc00',
    'Cyclical': '#ff3366',
    'Event': '#00ff88',
    'Rolling Stats': '#9966ff',
    'Engineered': '#ff66cc',
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-grid-dark-800 border border-grid-dark-600 p-3 rounded-lg shadow-xl">
          <p className="text-sm font-semibold text-gray-100 mb-1">{data.feature}</p>
          <p className="text-xs text-gray-400 mb-2">{data.category}</p>
          <p className="text-lg font-mono font-bold text-electric-blue-400">
            {formatNumber(data.importance, 1)}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="card-grid-dark">
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-100">
            Feature Influence Heatmap
          </h3>
          <TrendingUp className="w-5 h-5 text-electric-blue-400" />
        </div>
        <p className="text-sm text-gray-400">
          Top {topN} drivers from LightGBM model
        </p>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={topFeatures}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 120, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#2d2d3d" />
          <XAxis
            type="number"
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
          />
          <YAxis
            type="category"
            dataKey="feature"
            stroke="#6b7280"
            style={{ fontSize: '11px' }}
            width={110}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="importance" radius={[0, 8, 8, 0]}>
            {topFeatures.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={categoryColors[entry.category] || '#6b7280'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Category Legend */}
      <div className="mt-4 grid grid-cols-2 gap-2 border-t border-grid-dark-600 pt-3">
        {Object.entries(categoryColors).map(([category, color]) => (
          <div key={category} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded"
              style={{ backgroundColor: color }}
            ></div>
            <span className="text-xs text-gray-400">{category}</span>
          </div>
        ))}
      </div>

      {/* Key Insights */}
      <div className="mt-4 bg-electric-blue-500/10 border border-electric-blue-500/30 rounded-lg p-3">
        <p className="text-xs font-semibold text-electric-blue-400 mb-2">Key Insights</p>
        <ul className="text-xs text-gray-300 space-y-1">
          <li>• <strong>Weekly patterns</strong> (load_lag_7d) most influential</li>
          <li>• <strong>Heat Index</strong> drives cooling demand (AC load)</li>
          <li>• <strong>COVID regime</strong> captures structural shift</li>
        </ul>
      </div>
    </div>
  );
};

export default FeatureImportance;
