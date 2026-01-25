'use client';

import { useState, useEffect } from 'react';
import { 
  Brain, TrendingUp, Users, Target, BarChart3, DollarSign, ShoppingCart, Star,
  PieChart, Activity, Globe, Zap, AlertTriangle, CheckCircle, ArrowUpRight,
  ArrowDownRight, Calendar, Filter, Download, RefreshCw, TrendingDown
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

export default function ProductionAnalytics() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [advancedAnalytics, setAdvancedAnalytics] = useState<any>(null);
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
      // Fetch real-time analytics
      const response = await fetch('http://localhost:8001/api/v1/analytics/real-time');
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
        setLastUpdate(new Date().toLocaleTimeString());
      }
      
      // Fetch advanced analytics
      const advancedResponse = await fetch('http://localhost:8001/api/v1/analytics/advanced');
      if (advancedResponse.ok) {
        const advancedData = await advancedResponse.json();
        setAdvancedAnalytics(advancedData.advanced_analytics);
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

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-6 rounded-lg border border-blue-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-blue-900">Total Revenue</h3>
            <DollarSign className="w-6 h-6 text-blue-600" />
          </div>
          <p className="text-2xl font-bold text-blue-900 mb-2">
            {formatCurrency(analytics.revenue_analytics.total_revenue)}
          </p>
          <p className="text-sm text-blue-700">
            Growth: {analytics.revenue_analytics.growth_rate > 0 ? '+' : ''}{analytics.revenue_analytics.growth_rate.toFixed(1)}%
          </p>
        </div>

        <div className="bg-gradient-to-r from-green-50 to-green-100 p-6 rounded-lg border border-green-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-green-900">Customers</h3>
            <Users className="w-6 h-6 text-green-600" />
          </div>
          <p className="text-2xl font-bold text-green-900 mb-2">
            {formatNumber(analytics.customer_analytics.total_customers)}
          </p>
          <p className="text-sm text-green-700">Active customers</p>
        </div>

        <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-6 rounded-lg border border-purple-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-purple-900">Satisfaction</h3>
            <Star className="w-6 h-6 text-purple-600" />
          </div>
          <p className="text-2xl font-bold text-purple-900 mb-2">
            {analytics.customer_analytics.satisfaction_score.toFixed(1)}/5.0
          </p>
          <p className="text-sm text-purple-700">Average rating</p>
        </div>

        <div className="bg-gradient-to-r from-orange-50 to-orange-100 p-6 rounded-lg border border-orange-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-orange-900">Forecast</h3>
            <Target className="w-6 h-6 text-orange-600" />
          </div>
          <p className="text-2xl font-bold text-orange-900 mb-2">
            {formatCurrency(analytics.revenue_analytics.forecast.next_month)}
          </p>
          <p className="text-sm text-orange-700">
            {(analytics.revenue_analytics.forecast.confidence * 100).toFixed(0)}% confidence
          </p>
        </div>
      </div>

      {/* AI Insights */}
      <div className="bg-gradient-to-r from-indigo-50 to-blue-50 rounded-lg p-6 border border-indigo-200">
        <h4 className="font-semibold text-indigo-900 mb-4 flex items-center">
          <Brain className="w-5 h-5 mr-2" />
          AI-Generated Business Insights
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <h5 className="font-medium text-indigo-800">Key Insights:</h5>
            <ul className="text-sm text-indigo-700 space-y-1">
              {analytics.business_insights.slice(0, 4).map((insight, index) => (
                <li key={index}>• {insight}</li>
              ))}
            </ul>
          </div>
          <div className="space-y-2">
            <h5 className="font-medium text-indigo-800">Recommendations:</h5>
            <ul className="text-sm text-indigo-700 space-y-1">
              {analytics.recommendations.slice(0, 4).map((recommendation, index) => (
                <li key={index}>• {recommendation}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Advanced Analytics Section */}
      {advancedAnalytics && (
        <div className="space-y-6">
          {/* Forecasting */}
          {advancedAnalytics.forecasts && advancedAnalytics.forecasts.length > 0 && (
            <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-6 border border-purple-200">
              <h4 className="font-semibold text-purple-900 mb-4 flex items-center">
                <Target className="w-5 h-5 mr-2" />
                AI Forecasting & Predictions
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {advancedAnalytics.forecasts.map((forecast: any, index: number) => (
                  <div key={index} className="bg-white rounded-lg p-4 border border-purple-100">
                    <h5 className="font-medium text-purple-900 capitalize mb-2">{forecast.metric}</h5>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-purple-700">Current:</span>
                        <span className="font-medium">
                          {forecast.metric === 'revenue' ? formatCurrency(forecast.current_value) : 
                           forecast.metric === 'satisfaction' ? forecast.current_value.toFixed(1) :
                           formatNumber(Math.round(forecast.current_value))}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-purple-700">Predicted:</span>
                        <span className="font-medium">
                          {forecast.metric === 'revenue' ? formatCurrency(forecast.predicted_value) : 
                           forecast.metric === 'satisfaction' ? forecast.predicted_value.toFixed(1) :
                           formatNumber(Math.round(forecast.predicted_value))}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-purple-700">Trend:</span>
                        <span className={`font-medium flex items-center ${
                          forecast.trend_direction === 'up' ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {forecast.trend_direction === 'up' ? (
                            <ArrowUpRight className="w-3 h-3 mr-1" />
                          ) : (
                            <ArrowDownRight className="w-3 h-3 mr-1" />
                          )}
                          {forecast.trend_direction}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-purple-700">Confidence:</span>
                        <span className="font-medium">{(forecast.confidence_score * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Advanced Recommendations */}
          {advancedAnalytics.recommendations && advancedAnalytics.recommendations.length > 0 && (
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-6 border border-green-200">
              <h4 className="font-semibold text-green-900 mb-4 flex items-center">
                <CheckCircle className="w-5 h-5 mr-2" />
                AI-Powered Recommendations
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {advancedAnalytics.recommendations.map((recommendation: string, index: number) => (
                  <div key={index} className="bg-white rounded-lg p-4 border border-green-100">
                    <p className="text-sm text-green-800">{recommendation}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}