'use client';

import { useState } from 'react';
import { BarChart, Bar, LineChart, Line, AreaChart, Area, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';
import { BarChart3, LineChart as LineChartIcon, PieChart as PieChartIcon, TrendingUp, Download } from 'lucide-react';

interface DataVisualizationProps {
  data: any[];
  title: string;
  type?: 'bar' | 'line' | 'area' | 'pie' | 'scatter';
  xKey: string;
  yKey: string;
  colorKey?: string;
  height?: number;
  className?: string;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#84cc16', '#f97316'];

export default function DataVisualization({
  data,
  title,
  type = 'line',
  xKey,
  yKey,
  colorKey,
  height = 300,
  className = ''
}: DataVisualizationProps) {
  const [chartType, setChartType] = useState(type);

  const formatValue = (value: any) => {
    if (typeof value === 'number') {
      if (value > 1000000) {
        return `${(value / 1000000).toFixed(1)}M`;
      } else if (value > 1000) {
        return `${(value / 1000).toFixed(1)}K`;
      }
      return value.toLocaleString();
    }
    return value;
  };

  const exportData = () => {
    const csvContent = [
      Object.keys(data[0]).join(','),
      ...data.map(row => Object.values(row).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.replace(/\s+/g, '_')}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const renderChart = () => {
    const commonProps = {
      data,
      margin: { top: 5, right: 30, left: 20, bottom: 5 }
    };

    switch (chartType) {
      case 'bar':
        return (
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey} />
            <YAxis tickFormatter={formatValue} />
            <Tooltip formatter={(value) => [formatValue(value), yKey]} />
            <Legend />
            <Bar dataKey={yKey} fill={COLORS[0]} />
          </BarChart>
        );

      case 'area':
        return (
          <AreaChart {...commonProps}>
            <defs>
              <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={COLORS[0]} stopOpacity={0.8} />
                <stop offset="95%" stopColor={COLORS[0]} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey} />
            <YAxis tickFormatter={formatValue} />
            <Tooltip formatter={(value) => [formatValue(value), yKey]} />
            <Area
              type="monotone"
              dataKey={yKey}
              stroke={COLORS[0]}
              fillOpacity={1}
              fill="url(#colorGradient)"
            />
          </AreaChart>
        );

      case 'pie':
        const pieData = data.map((item, index) => ({
          ...item,
          fill: COLORS[index % COLORS.length]
        }));
        
        return (
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey={yKey}
            >
              {pieData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value) => [formatValue(value), yKey]} />
          </PieChart>
        );

      case 'scatter':
        return (
          <ScatterChart {...commonProps}>
            <CartesianGrid />
            <XAxis dataKey={xKey} />
            <YAxis dataKey={yKey} tickFormatter={formatValue} />
            <Tooltip formatter={(value) => [formatValue(value), yKey]} />
            <Scatter dataKey={yKey} fill={COLORS[0]} />
          </ScatterChart>
        );

      default: // line
        return (
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey} />
            <YAxis tickFormatter={formatValue} />
            <Tooltip formatter={(value) => [formatValue(value), yKey]} />
            <Legend />
            <Line
              type="monotone"
              dataKey={yKey}
              stroke={COLORS[0]}
              strokeWidth={2}
              dot={{ fill: COLORS[0] }}
            />
          </LineChart>
        );
    }
  };

  if (!data || data.length === 0) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-500">No data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        
        <div className="flex items-center space-x-2">
          {/* Chart Type Selector */}
          <div className="flex items-center space-x-1 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setChartType('line')}
              className={`p-2 rounded ${chartType === 'line' ? 'bg-white shadow-sm' : 'hover:bg-gray-200'}`}
              title="Line Chart"
            >
              <LineChartIcon className="w-4 h-4" />
            </button>
            <button
              onClick={() => setChartType('bar')}
              className={`p-2 rounded ${chartType === 'bar' ? 'bg-white shadow-sm' : 'hover:bg-gray-200'}`}
              title="Bar Chart"
            >
              <BarChart3 className="w-4 h-4" />
            </button>
            <button
              onClick={() => setChartType('area')}
              className={`p-2 rounded ${chartType === 'area' ? 'bg-white shadow-sm' : 'hover:bg-gray-200'}`}
              title="Area Chart"
            >
              <TrendingUp className="w-4 h-4" />
            </button>
            <button
              onClick={() => setChartType('pie')}
              className={`p-2 rounded ${chartType === 'pie' ? 'bg-white shadow-sm' : 'hover:bg-gray-200'}`}
              title="Pie Chart"
            >
              <PieChartIcon className="w-4 h-4" />
            </button>
          </div>

          {/* Export Button */}
          <button
            onClick={exportData}
            className="flex items-center space-x-1 px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Download className="w-4 h-4" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Chart */}
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>

      {/* Summary Stats */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="text-center">
            <p className="text-gray-500">Total Points</p>
            <p className="font-semibold text-gray-900">{data.length}</p>
          </div>
          <div className="text-center">
            <p className="text-gray-500">Average</p>
            <p className="font-semibold text-gray-900">
              {formatValue(data.reduce((sum, item) => sum + (item[yKey] || 0), 0) / data.length)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-gray-500">Maximum</p>
            <p className="font-semibold text-gray-900">
              {formatValue(Math.max(...data.map(item => item[yKey] || 0)))}
            </p>
          </div>
          <div className="text-center">
            <p className="text-gray-500">Minimum</p>
            <p className="font-semibold text-gray-900">
              {formatValue(Math.min(...data.map(item => item[yKey] || 0)))}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}