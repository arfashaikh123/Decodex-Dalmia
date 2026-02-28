import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { formatNumber, formatCurrency } from '../data/sampleData';

const KPICard = ({ title, value, unit, subtitle, trend, trendValue, className = "", valueClassName = "" }) => {
  const getTrendIcon = () => {
    if (!trend) return null;
    if (trend === 'up') return <TrendingUp className="w-4 h-4 text-success-green-400" />;
    if (trend === 'down') return <TrendingDown className="w-4 h-4 text-peak-red-400" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  const getTrendColor = () => {
    if (trend === 'up') return 'text-success-green-400';
    if (trend === 'down') return 'text-peak-red-400';
    return 'text-gray-400';
  };

  return (
    <div className={`card-grid-dark ${className}`}>
      <div className="space-y-2">
        <p className="metric-label">{title}</p>
        <div className="flex items-baseline gap-2">
          <span className={`metric-value ${valueClassName}`}>{value}</span>
          {unit && <span className="text-lg text-gray-400 font-medium">{unit}</span>}
        </div>
        {subtitle && (
          <p className="text-sm text-gray-400">{subtitle}</p>
        )}
        {trend && (
          <div className={`flex items-center gap-1 ${getTrendColor()}`}>
            {getTrendIcon()}
            <span className="text-sm font-semibold">{trendValue}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default KPICard;
