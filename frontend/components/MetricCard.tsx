'use client';

import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: number | string;
  change?: number;
  changeType?: 'increase' | 'decrease' | 'neutral';
  format?: 'number' | 'currency' | 'percentage';
  icon?: React.ReactNode;
  loading?: boolean;
  trend?: number[]; // Historical data for trend calculation
}

export default function MetricCard({
  title,
  value,
  change,
  changeType = 'neutral',
  format = 'number',
  icon,
  loading = false,
  trend = []
}: MetricCardProps) {
  // Calculate trend if not provided
  const calculatedChange = change ?? (trend.length >= 2 ? 
    ((trend[trend.length - 1] - trend[trend.length - 2]) / trend[trend.length - 2]) * 100 : 0
  );
  
  const calculatedChangeType = changeType === 'neutral' && calculatedChange !== 0 ? 
    (calculatedChange > 0 ? 'increase' : 'decrease') : changeType;
  const formatValue = (val: number | string) => {
    if (typeof val === 'string') return val;
    
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(val);
      case 'percentage':
        return `${(val * 100).toFixed(1)}%`;
      default:
        return new Intl.NumberFormat('en-US').format(val);
    }
  };

  const getTrendIcon = () => {
    switch (calculatedChangeType) {
      case 'increase':
        return <TrendingUp className="w-4 h-4 text-green-600" />;
      case 'decrease':
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      default:
        return <Minus className="w-4 h-4 text-gray-400" />;
    }
  };

  const getTrendColor = () => {
    switch (calculatedChangeType) {
      case 'increase':
        return 'text-green-600';
      case 'decrease':
        return 'text-red-600';
      default:
        return 'text-gray-500';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="flex items-center justify-between mb-2">
            <div className="h-4 bg-gray-200 rounded w-24"></div>
            <div className="h-6 w-6 bg-gray-200 rounded"></div>
          </div>
          <div className="h-8 bg-gray-200 rounded w-32 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-20"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-all duration-200 cursor-pointer">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        {icon && <div className="text-gray-400">{icon}</div>}
      </div>
      
      <div className="flex items-baseline justify-between">
        <p className="text-2xl font-bold text-gray-900">
          {formatValue(value)}
        </p>
        
        {(calculatedChange !== undefined && calculatedChange !== 0) && (
          <div className={`flex items-center space-x-1 ${getTrendColor()}`}>
            {getTrendIcon()}
            <span className="text-sm font-medium">
              {Math.abs(calculatedChange).toFixed(1)}%
            </span>
          </div>
        )}
      </div>
    </div>
  );
}