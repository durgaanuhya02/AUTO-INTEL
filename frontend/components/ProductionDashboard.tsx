'use client';

import { useState, useEffect } from 'react';
import { 
  TrendingUp, TrendingDown, DollarSign, ShoppingCart, Users, Star, 
  MapPin, CreditCard, Truck, AlertTriangle, CheckCircle, BarChart3,
  PieChart, Activity, Globe, Target, Zap, Brain, Database
} from 'lucide-react';

interface ProductionMetrics {
  revenue: number;
  orders: number;
  avg_order_value: number;
  customer_satisfaction: number;
  monthly_growth: number;
}

interface TrendData {
  revenue: number[];
  orders: number[];
  customer_satisfaction: number[];
  growth_rate: number[];
}

interface BusinessInsight {
  executive_summary: {
    total_revenue: string;
    total_orders: string;
    growth_rate: string;
    satisfaction: string;
  };
  key_findings: string[];
  strategic_recommendations: string[];
  market_opportunities: string[];
}

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
}

export default function ProductionDashboard() {
  const [metrics, setMetrics] = useState<ProductionMetrics | null>(null);
  const [trends, setTrends] = useState<TrendData | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [insights, setInsights] = useState<BusinessInsight | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchDashboardData();
    fetchAnalytics();
    fetchInsights();
    
    // Update every 30 seconds
    const interval = setInterval(() => {
      fetchDashboardData();
      fetchAnalytics();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/v1/dashboard');
      if (response.ok) {
        const data = await response.json();
        setMetrics(data.current_metrics);
        setTrends(data.trends);
        setLastUpdate(new Date().toLocaleTimeString());
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/v1/analytics/real-time');
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  const fetchInsights = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/v1/insights/business');
      if (response.ok) {
        const data = await response.json();
        setInsights(data);
      }
    } catch (error) {
      console.error('Error fetching insights:', error);
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

  const getTrendIcon = (current: number, previous: number) => {
    if (current > previous) return <TrendingUp className="w-4 h-4 text-green-600" />;
    if (current < previous) return <TrendingDown className="w-4 h-4 text-red-600" />;
    return <Activity className="w-4 h-4 text-gray-400" />;
  };

  const getTrendColor = (current: number, previous: number) => {
    if (current > previous) return 'text-green-600';
    if (current < previous) return 'text-red-600';
    return 'text-gray-500';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-6"></div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Loading Production Analytics</h2>
          <p className="text-gray-600">Processing Brazilian E-commerce Dataset...</p>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', name: 'Executive Overview', icon: BarChart3 },
    { id: 'analytics', name: 'Advanced Analytics', icon: Brain },
    { id: 'insights', name: 'Business Insights', icon: Target },
    { id: 'operations', name: 'Operations', icon: Truck }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-lg border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
                <Database className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Production E-commerce Analytics
                </h1>
                <p className="text-sm text-gray-600">
                  Brazilian E-commerce Dataset • Real-time Insights • {formatNumber(metrics?.orders || 0)} Orders Processed
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium text-gray-700">Live Data</span>
              </div>
              
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">Last Update</p>
                <p className="text-xs text-gray-500">{lastUpdate}</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.name}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* Executive KPIs */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <DollarSign className="w-6 h-6 text-green-600" />
                  </div>
                  {trends && trends.revenue.length >= 2 && getTrendIcon(trends.revenue[trends.revenue.length - 1], trends.revenue[trends.revenue.length - 2])}
                </div>
                <h3 className="text-sm font-medium text-gray-600 mb-1">Total Revenue</h3>
                <p className="text-3xl font-bold text-gray-900">{formatCurrency(metrics?.revenue || 0)}</p>
                <p className={`text-sm mt-2 ${getTrendColor(trends?.reve