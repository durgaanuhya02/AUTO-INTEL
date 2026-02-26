'use client';

import { useState, useEffect } from 'react';
import { 
  TrendingUp, TrendingDown, DollarSign, ShoppingCart, Users, Star,
  Activity, Zap, Target, BarChart3, PieChart, Globe
} from 'lucide-react';

interface MetricData {
  current_metrics: {
    revenue: number;
    orders: number;
    avg_order_value: number;
    customer_satisfaction: number;
    monthly_growth: number;
  };
  trends: {
    revenue: number[];
    orders: number[];
    customer_satisfaction: number[];
    growth_rate: number[];
  };
  data_freshness: {
    last_update: string;
    source: string;
    records_processed: number;
    data_quality: string;
  };
}

export default function RealTimeMetrics() {
  const [metrics, setMetrics] = useState<MetricData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/v1/dashboard');
      if (response.ok) {
        const data = await response.json();
        setMetrics(data);
        setLastUpdate(new Date().toLocaleTimeString());
      }
    } catch (error) {
      console.error('Error fetching metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('en-US').format(value);
  };

  const getTrendDirection = (trend: number[]) => {
    if (trend.length < 2) return 'neutral';
    const recent = trend.slice(-3);
    const avg = recent.reduce((a, b) => a + b, 0) / recent.length;
    const previous = trend.slice(-6, -3);
    const prevAvg = previous.reduce((a, b) => a + b, 0) / previous.length;
    
    if (avg > prevAvg * 1.02) return 'up';
    if (avg < prevAvg * 0.98) return 'down';
    return 'neutral';
  };

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'up': return <TrendingUp className="w-4 h-4 text-green-600" />;
      case 'down': return <TrendingDown className="w-4 h-4 text-red-600" />;
      default: return <Activity className="w-4 h-4 text-gray-400" />;
    }
  };

  const getTrendColor = (direction: string) => {
    switch (direction) {
      case 'up': return 'text-green-600';
      case 'down': return 'text-red-600';
      default: return 'text-gray-500';
    }
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="animate-pulse">
              <div className="flex items-center justify-between mb-4">
                <div className="h-4 bg-gray-200 rounded w-24"></div>
                <div className="h-6 w-6 bg-gray-200 rounded"></div>
              </div>
              <div className="h-8 bg-gray-200 rounded w-32 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-20"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <h3 className="text-lg font-medium text-gray-900 mb-1">No Data Available</h3>
        <p className="text-gray-500">Please ensure the production server is running</p>
      </div>
    );
  }

  const revenueTrend = getTrendDirection(metrics.trends.revenue);
  const ordersTrend = getTrendDirection(metrics.trends.orders);
  const satisfactionTrend = getTrendDirection(metrics.trends.customer_satisfaction);

  return (
    <div className="space-y-6">
      {/* Data Freshness Indicator */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <div>
              <p className="text-sm font-medium text-blue-900">
                Live Data from {metrics.data_freshness?.source || 'Brazilian E-commerce Dataset'}
              </p>
              <p className="text-xs text-blue-700">
                {formatNumber(metrics.data_freshness?.records_processed || 0)} records processed • 
                Last update: {lastUpdate} • 
                Quality: {metrics.data_freshness?.data_quality || 'High'}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Zap className="w-4 h-4 text-yellow-500" />
            <span className="text-xs font-medium text-blue-900">Real-time</span>
          </div>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Revenue */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-all duration-200">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-green-100 rounded-lg">
              <DollarSign className="w-6 h-6 text-green-600" />
            </div>
            <div className="flex items-center space-x-1">
              {getTrendIcon(revenueTrend)}
              <span className={`text-xs font-medium ${getTrendColor(revenueTrend)}`}>
                {metrics.current_metrics.monthly_growth > 0 ? '+' : ''}{metrics.current_metrics.monthly_growth.toFixed(1)}%
              </span>
            </div>
          </div>
          <h3 className="text-sm font-medium text-gray-600 mb-1">Total Revenue</h3>
          <p className="text-3xl font-bold text-gray-900 mb-2">
            {formatCurrency(metrics.current_metrics.revenue)}
          </p>
          <div className="flex items-center space-x-2">
            <div className="w-full bg-gray-200 rounded-full h-1.5">
              <div 
                className="bg-green-500 h-1.5 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, (metrics.current_metrics.revenue / 2000000) * 100)}%` }}
              />
            </div>
            <span className="text-xs text-gray-500">Target</span>
          </div>
        </div>

        {/* Total Orders */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-all duration-200">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-blue-100 rounded-lg">
              <ShoppingCart className="w-6 h-6 text-blue-600" />
            </div>
            {getTrendIcon(ordersTrend)}
          </div>
          <h3 className="text-sm font-medium text-gray-600 mb-1">Total Orders</h3>
          <p className="text-3xl font-bold text-gray-900 mb-2">
            {formatNumber(metrics.current_metrics.orders)}
          </p>
          <p className={`text-sm ${getTrendColor(ordersTrend)}`}>
            {ordersTrend === 'up' ? 'Increasing' : ordersTrend === 'down' ? 'Decreasing' : 'Stable'} order volume
          </p>
        </div>

        {/* Average Order Value */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-all duration-200">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Target className="w-6 h-6 text-purple-600" />
            </div>
            <div className="text-purple-600">
              <BarChart3 className="w-4 h-4" />
            </div>
          </div>
          <h3 className="text-sm font-medium text-gray-600 mb-1">Avg Order Value</h3>
          <p className="text-3xl font-bold text-gray-900 mb-2">
            {formatCurrency(metrics.current_metrics.avg_order_value)}
          </p>
          <p className="text-sm text-purple-600">
            {((metrics.current_metrics.avg_order_value / 100) * 100).toFixed(0)}% of target AOV
          </p>
        </div>

        {/* Customer Satisfaction */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-all duration-200">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <Star className="w-6 h-6 text-yellow-600" />
            </div>
            {getTrendIcon(satisfactionTrend)}
          </div>
          <h3 className="text-sm font-medium text-gray-600 mb-1">Customer Satisfaction</h3>
          <p className="text-3xl font-bold text-gray-900 mb-2">
            {metrics.current_metrics.customer_satisfaction.toFixed(1)}/5.0
          </p>
          <div className="flex items-center space-x-1">
            {[1, 2, 3, 4, 5].map((star) => (
              <Star
                key={star}
                className={`w-4 h-4 ${
                  star <= Math.round(metrics.current_metrics.customer_satisfaction)
                    ? 'text-yellow-400 fill-current'
                    : 'text-gray-300'
                }`}
              />
            ))}
            <span className="text-sm text-gray-500 ml-2">
              {satisfactionTrend === 'up' ? 'Improving' : satisfactionTrend === 'down' ? 'Declining' : 'Stable'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
    