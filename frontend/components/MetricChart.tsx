'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { motion } from 'framer-motion';

interface MetricChartProps {
  title: string;
  data: number[];
  color?: string;
  type?: 'line' | 'area';
  format?: 'number' | 'currency' | 'percentage';
  height?: number;
}

export default function MetricChart({
  title,
  data,
  color = '#3b82f6',
  type = 'line',
  format = 'number',
  height = 200
}: MetricChartProps) {
  // Transform data for recharts
  const chartData = data.map((value, index) => ({
    index,
    value,
    time: `${index * 30}m ago` // Assuming 30-minute intervals
  }));

  const formatValue = (value: number) => {
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(value);
      case 'percentage':
        return `${(value * 100).toFixed(1)}%`;
      default:
        return new Intl.NumberFormat('en-US').format(value);
    }
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="text-sm text-gray-600">{`${data.length - label - 1} periods ago`}</p>
          <p className="text-sm font-medium text-gray-900">
            {formatValue(payload[0].value)}
          </p>
        </div>
      );
    }
    return null;
  };

  if (data.length === 0) {
    return (
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
        <div className="flex items-center justify-center h-48">
          <p className="text-gray-500">No data available</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      className="card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <div className="text-right">
          <p className="text-2xl font-bold text-gray-900">
            {formatValue(data[data.length - 1])}
          </p>
          <p className="text-sm text-gray-500">Current</p>
        </div>
      </div>

      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          {type === 'area' ? (
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id={`gradient-${title}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="index" 
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 12, fill: '#6b7280' }}
                tickFormatter={(value) => `${data.length - value - 1}p`}
              />
              <YAxis 
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 12, fill: '#6b7280' }}
                tickFormatter={formatValue}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="value"
                stroke={color}
                strokeWidth={2}
                fill={`url(#gradient-${title})`}
                dot={false}
                activeDot={{ r: 4, fill: color }}
              />
            </AreaChart>
          ) : (
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="index" 
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 12, fill: '#6b7280' }}
                tickFormatter={(value) => `${data.length - value - 1}p`}
              />
              <YAxis 
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 12, fill: '#6b7280' }}
                tickFormatter={formatValue}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="value"
                stroke={color}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: color }}
              />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Trend indicator */}
      <div className="mt-3 pt-3 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500">Trend</span>
          {data.length >= 2 && (
            <span className={`font-medium ${
              data[data.length - 1] > data[data.length - 2] 
                ? 'text-success-600' 
                : data[data.length - 1] < data[data.length - 2]
                ? 'text-danger-600'
                : 'text-gray-600'
            }`}>
              {data[data.length - 1] > data[data.length - 2] 
                ? '↗ Increasing' 
                : data[data.length - 1] < data[data.length - 2]
                ? '↘ Decreasing'
                : '→ Stable'
              }
            </span>
          )}
        </div>
      </div>
    </motion.div>
  );
}