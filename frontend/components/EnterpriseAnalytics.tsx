'use client';

import { useState, useEffect } from 'react';
import { 
  Brain, TrendingUp, Users, Target, BarChart3, DollarSign, ShoppingCart, Star,
  PieChart, Activity, Globe, Zap, AlertTriangle, CheckCircle, ArrowUpRight,
  ArrowDownRight, Calendar, Filter, Download, RefreshCw
} from 'lucide-react';

interface AnalyticsData {
  revenue_analytics: {
    total_revenue: number;
    trend_data: Array<{date: string; value: number}>;
    growth_rate: number;
    forecast: {
      next_month: number;
      confidence: number;
    };
  };
  customer_analytics: {
    satisfaction_score: number;
    total_customers: number;
    geographic_distribution: Record<string, number>;
  };
  product_analytics: {
    top_categories: Array<{name: string; revenue: number; rank: number}>;
    category_performance: Record<string, number>;
  };
  operational_analytics: {
    delivery_performance: {
      on_time_delivery_rate: number;
      avg_delivery_days: number;
    };
    payment_methods: Record<string, number>;
  };
  business_insights: string[];
  recommendations: string[];
}

export default function EnterpriseAnalytics() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTimeRange, setSelectedTimeRange] = useState('30d');
  const [selectedMetric, setSelectedMetric] = useState('revenue');
  const [lastUpdate, setLastUpdate] = useState<string>('');

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/v1/analytics/real-time');
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
        setLastUpdate(new Date().toLocaleTimeString());
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
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

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-gray-200 rounded w-1/3"></div>
            <div className="grid grid-cols-4 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-32 bg-gray-200 rounded"></div>
              ))}
            </div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <BarChart3 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Analytics Unavailable</h3>
        <p className="text-gray-500 mb-4">Unable to load analytics data. Please check your connection.</p>
        <button 
          onClick={fetchAnalytics}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Advanced Analytics</h1>
            <p className="text-blue-100 text-lg">
              AI-powered insights from {formatNumber(analytics.customer_analytics.total_customers)} customers
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <p className="text-sm text-blue-100">Last Updated</p>
              <p className="font-semibold">{lastUpdate}</p>
            </div>
            <button 
              onClick={fetchAnalytics}
              className="p-2 bg-white/20 rounded-lg hover:bg-white/30 transition-colors"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Control Panel */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Calendar className="w-4 h-4 text-gray-500" />
              <select 
                value={selectedTimeRange}
                onChange={(e) => setSelectedTimeRange(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
              >
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
                <option value="90d">Last 90 days</option>
                <option value="1y">Last year</option>
              </select>
            </div>
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <select 
                value={selectedMetric}
                onChange={(e) => setSelectedMetric(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
              >
                <option value="revenue">Revenue</option>
                <option value="orders">Orders</option>
                <option value="customers">Customers</option>
                <option value="satisfaction">Satisfaction</option>
              </select>
            </div>
          </div>
          <button className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            <Download className="w-4 h-4" />
            <span>Export Report</span>
          </button>
        </div>
      </div>

      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-green-100 rounded-xl">
              <DollarSign className="w-6 h-6 text-green-600" />
            </div>
            <div className="flex items-center space-x-1 text-green-600">
              <ArrowUpRight className="w-4 h-4" />
              <span className="text-sm font-medium">+{analytics.revenue_analytics.growth_rate.toFixed(1)}%</span>
            </div>
          </div>
          <h3 className="text-sm font-medium text-gray-600 mb-1">Total Revenue</h3>
          <p className="text-2xl font-bold text-gray-900 mb-2">
            {formatCurrency(analytics.revenue_analytics.total_revenue)}
          </p>
          <p className="text-xs text-gray-500">
            Forecast: {formatCurrency(analytics.revenue_analytics.forecast.next_month)}
          <