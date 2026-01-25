'use client';

import { useState, useEffect } from 'react';
import { 
  TrendingUp, TrendingDown, DollarSign, ShoppingCart, Users, Star,
  Activity, BarChart3, Database, Brain, Shield, Target, AlertTriangle,
  CheckCircle, Clock, Zap, Eye, Globe, Cpu, PieChart, LineChart,
  ArrowUpRight, ArrowDownRight, Minus, RefreshCw
} from 'lucide-react';

interface DashboardData {
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
  alerts: Array<{
    id: number;
    title: string;
    message: string;
    severity: string;
    timestamp: string;
    action_required: boolean;
  }>;
  recent_decisions: Array<{
    id: number;
    title: string;
    description: string;
    status: string;
    confidence_score: number;
    financial_impact: number;
  }>;
  agent_statuses: Array<{
    agent_type: string;
    status: string;
    current_task: string;
    metrics: { processed_count: number };
  }>;
  ml_insights?: {
    ml_models?: any;
    real_time_predictions?: any;
    csv_data_insights?: any;
    business_intelligence?: any;
    recommendations?: string[];
  };
  ml_performance?: {
    models_active: number;
    accuracy: number;
    processing_time_ms: number;
    data_points_processed: number;
    anomalies_detected: number;
  };
  data_freshness: {
    last_update: string;
    source: string;
    records_processed: number;
    data_quality: string;
  };
}

interface DataSource {
  name: string;
  status: 'healthy' | 'warning' | 'error';
  records: number;
  lastSync: string;
  quality: number;
}

export default function EnterpriseDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [activeTab, setActiveTab] = useState('overview');
  const [isLive, setIsLive] = useState(true);

  // Mock data sources from CSV files
  const [dataSources] = useState<DataSource[]>([
    { name: 'Orders Dataset', status: 'healthy', records: 99441, lastSync: 'Live', quality: 98.5 },
    { name: 'Customers Dataset', status: 'healthy', records: 99441, lastSync: 'Live', quality: 97.2 },
    { name: 'Products Dataset', status: 'healthy', records: 32951, lastSync: 'Live', quality: 99.1 },
    { name: 'Payments Dataset', status: 'warning', records: 103886, lastSync: 'Live', quality: 95.8 },
    { name: 'Reviews Dataset', status: 'healthy', records: 99224, lastSync: 'Live', quality: 96.7 },
    { name: 'Geolocation Dataset', status: 'healthy', records: 1000163, lastSync: 'Live', quality: 94.3 },
    { name: 'ML Models', status: 'healthy', records: 4, lastSync: 'Active', quality: 99.9 }
  ]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/v1/dashboard');
      if (response.ok) {
        const dashboardData = await response.json();
        setData(dashboardData);
        setLastUpdate(new Date().toLocaleTimeString());
        setIsLive(true);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      setIsLive(false);
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

  const getTrendIcon = (current: number, previous: number) => {
    if (current > previous * 1.02) return <ArrowUpRight className="w-4 h-4 text-green-500" />;
    if (current < previous * 0.98) return <ArrowDownRight className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'error': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-500 border-t-transparent mx-auto mb-4"></div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Loading Enterprise Analytics</h2>
          <p className="text-gray-600">Initializing ML-powered real-time dashboard...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Connection Error</h2>
          <p className="text-gray-600">Unable to connect to analytics backend</p>
          <button 
            onClick={fetchData}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', name: 'Executive Overview', icon: BarChart3 },
    { id: 'analytics', name: 'ML Analytics', icon: Brain },
    { id: 'data', name: 'Data Sources', icon: Database },
    { id: 'agents', name: 'AI Agents', icon: Cpu }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Enterprise AI Analytics Platform
                </h1>
                <p className="text-sm text-gray-600">
                  Real-time ML Intelligence • {formatNumber(data.current_metrics.orders)} Orders • Brazilian E-commerce Dataset
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-6">
              <div className={`flex items-center space-x-2 px-3 py-2 rounded-lg ${
                isLive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
                <span className="text-sm font-medium">{isLive ? 'Live' : 'Offline'}</span>
              </div>
              
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">Last Update</p>
                <p className="text-xs text-gray-500">{lastUpdate}</p>
              </div>
              
              <button 
                onClick={fetchData}
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                title="Refresh Data"
              >
                <RefreshCw className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-6">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
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
            {/* Live Data Indicator */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                  <div>
                    <p className="text-sm font-medium text-blue-900">
                      Live ML-Powered Analytics from {data.data_freshness?.source || 'Brazilian E-commerce Dataset'}
                    </p>
                    <p className="text-xs text-blue-700">
                      {formatNumber(data.data_freshness?.records_processed || 0)} records processed • 
                      Updates every 30 seconds • 
                      Quality: {data.data_freshness?.data_quality || 'High'} • 
                      ML Models: {data.ml_performance?.models_active || 4} Active
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Zap className="w-4 h-4 text-yellow-500" />
                  <span className="text-xs font-medium text-blue-900">Real-time ML</span>
                </div>
              </div>
            </div>

            {/* Key Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Revenue */}
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <DollarSign className="w-6 h-6 text-green-600" />
                  </div>
                  <div className="flex items-center space-x-1">
                    {data.current_metrics.monthly_growth > 0 ? (
                      <TrendingUp className="w-4 h-4 text-green-500" />
                    ) : (
                      <TrendingDown className="w-4 h-4 text-red-500" />
                    )}
                    <span className={`text-xs font-medium ${
                      data.current_metrics.monthly_growth > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {data.current_metrics.monthly_growth > 0 ? '+' : ''}{data.current_metrics.monthly_growth.toFixed(1)}%
                    </span>
                  </div>
                </div>
                <h3 className="text-sm font-medium text-gray-600 mb-1">Total Revenue</h3>
                <p className="text-3xl font-bold text-gray-900 mb-2">
                  {formatCurrency(data.current_metrics.revenue)}
                </p>
                <div className="flex items-center space-x-2">
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div 
                      className="bg-green-500 h-1.5 rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(100, (data.current_metrics.revenue / 20000000) * 100)}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500">Target</span>
                </div>
              </div>

              {/* Orders */}
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <ShoppingCart className="w-6 h-6 text-blue-600" />
                  </div>
                  <Activity className="w-4 h-4 text-blue-500" />
                </div>
                <h3 className="text-sm font-medium text-gray-600 mb-1">Total Orders</h3>
                <p className="text-3xl font-bold text-gray-900 mb-2">
                  {formatNumber(data.current_metrics.orders)}
                </p>
                <p className="text-sm text-blue-600">Live processing active</p>
              </div>

              {/* AOV */}
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Target className="w-6 h-6 text-purple-600" />
                  </div>
                  <BarChart3 className="w-4 h-4 text-purple-500" />
                </div>
                <h3 className="text-sm font-medium text-gray-600 mb-1">Avg Order Value</h3>
                <p className="text-3xl font-bold text-gray-900 mb-2">
                  {formatCurrency(data.current_metrics.avg_order_value)}
                </p>
                <p className="text-sm text-purple-600">
                  {((data.current_metrics.avg_order_value / 150) * 100).toFixed(0)}% of target
                </p>
              </div>

              {/* Satisfaction */}
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 bg-yellow-100 rounded-lg">
                    <Star className="w-6 h-6 text-yellow-600" />
                  </div>
                  <CheckCircle className="w-4 h-4 text-green-500" />
                </div>
                <h3 className="text-sm font-medium text-gray-600 mb-1">Customer Satisfaction</h3>
                <p className="text-3xl font-bold text-gray-900 mb-2">
                  {data.current_metrics.customer_satisfaction.toFixed(1)}/5.0
                </p>
                <div className="flex items-center space-x-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <Star
                      key={star}
                      className={`w-4 h-4 ${
                        star <= Math.round(data.current_metrics.customer_satisfaction)
                          ? 'text-yellow-400 fill-current'
                          : 'text-gray-300'
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* ML Performance & AI Recommendations */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* ML Performance */}
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                  <Brain className="w-5 h-5 text-purple-600 mr-2" />
                  ML Model Performance
                </h3>
                {data.ml_performance && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-center p-3 bg-purple-50 rounded-lg">
                        <p className="text-2xl font-bold text-purple-600">{data.ml_performance.models_active}</p>
                        <p className="text-sm text-gray-600">Active Models</p>
                      </div>
                      <div className="text-center p-3 bg-green-50 rounded-lg">
                        <p className="text-2xl font-bold text-green-600">{(data.ml_performance.accuracy * 100).toFixed(1)}%</p>
                        <p className="text-sm text-gray-600">Accuracy</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-center p-3 bg-blue-50 rounded-lg">
                        <p className="text-2xl font-bold text-blue-600">{formatNumber(data.ml_performance.data_points_processed)}</p>
                        <p className="text-sm text-gray-600">Data Points</p>
                      </div>
                      <div className="text-center p-3 bg-orange-50 rounded-lg">
                        <p className="text-2xl font-bold text-orange-600">{data.ml_performance.anomalies_detected}</p>
                        <p className="text-sm text-gray-600">Anomalies</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* AI Recommendations */}
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                  <Zap className="w-5 h-5 text-yellow-600 mr-2" />
                  AI Recommendations
                </h3>
                <div className="space-y-3">
                  {data.ml_insights?.recommendations?.slice(0, 4).map((rec, index) => (
                    <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                      <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-xs font-medium text-blue-600">{index + 1}</span>
                      </div>
                      <p className="text-sm text-gray-700">{rec}</p>
                    </div>
                  )) || (
                    <div className="text-center py-4">
                      <Brain className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                      <p className="text-sm text-gray-500">AI recommendations loading...</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Alerts & Decisions */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* System Alerts */}
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                  <Shield className="w-5 h-5 text-red-600 mr-2" />
                  System Alerts
                </h3>
                <div className="space-y-3">
                  {data.alerts.slice(0, 3).map((alert) => (
                    <div key={alert.id} className="border-l-4 border-red-400 bg-red-50 p-3 rounded-r-lg">
                      <div className="flex items-center justify-between mb-1">
                        <h4 className="font-medium text-red-800 text-sm">{alert.title}</h4>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          alert.severity === 'critical' ? 'bg-red-200 text-red-800' :
                          alert.severity === 'high' ? 'bg-orange-200 text-orange-800' :
                          'bg-yellow-200 text-yellow-800'
                        }`}>
                          {alert.severity}
                        </span>
                      </div>
                      <p className="text-red-700 text-xs">{alert.message}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* AI Decisions */}
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                  <Target className="w-5 h-5 text-green-600 mr-2" />
                  AI Decisions
                </h3>
                <div className="space-y-3">
                  {data.recent_decisions.slice(0, 3).map((decision) => (
                    <div key={decision.id} className="border-l-4 border-green-400 bg-green-50 p-3 rounded-r-lg">
                      <div className="flex items-center justify-between mb-1">
                        <h4 className="font-medium text-green-800 text-sm">{decision.title}</h4>
                        <span className="text-xs text-green-600 font-medium">
                          {Math.round(decision.confidence_score * 100)}% confidence
                        </span>
                      </div>
                      <p className="text-green-700 text-xs">{decision.description}</p>
                      <p className="text-green-600 text-xs mt-1">
                        Impact: {formatCurrency(decision.financial_impact)}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="space-y-8">
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">ML Model Status</h3>
              {data.ml_insights?.ml_models && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {Object.entries(data.ml_insights.ml_models).map(([key, model]: [string, any]) => (
                    <div key={key} className="border rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 mb-2 capitalize">{key.replace('_', ' ')}</h4>
                      <p className="text-sm text-gray-600 mb-2">{model.model}</p>
                      <div className="flex items-center justify-between">
                        <span className={`px-2 py-1 rounded text-xs ${
                          model.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                          {model.status}
                        </span>
                        <span className="text-sm font-medium text-blue-600">
                          {(model.accuracy * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {data.ml_insights?.real_time_predictions && (
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4">Real-time Predictions</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <p className="text-2xl font-bold text-blue-600">
                      {formatCurrency(data.ml_insights.real_time_predictions.revenue_forecast_24h)}
                    </p>
                    <p className="text-sm text-gray-600">24h Revenue Forecast</p>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <p className="text-2xl font-bold text-green-600">
                      {formatNumber(data.ml_insights.real_time_predictions.order_volume_forecast)}
                    </p>
                    <p className="text-sm text-gray-600">Order Volume Forecast</p>
                  </div>
                  <div className="text-center p-4 bg-red-50 rounded-lg">
                    <p className="text-2xl font-bold text-red-600">
                      {data.ml_insights.real_time_predictions.churn_risk_customers}
                    </p>
                    <p className="text-sm text-gray-600">Churn Risk Customers</p>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <p className="text-2xl font-bold text-purple-600">
                      {data.ml_insights.real_time_predictions.upsell_opportunities}
                    </p>
                    <p className="text-sm text-gray-600">Upsell Opportunities</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'data' && (
          <div className="space-y-8">
            {/* CSV Data Sources */}
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Brazilian E-commerce Dataset Sources</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {dataSources.map((source, index) => (
                  <div key={index} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        <Database className="w-4 h-4 text-blue-500" />
                        <h4 className="font-medium text-gray-900">{source.name}</h4>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(source.status)}`}>
                        {source.status}
                      </span>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Records</span>
                        <span className="text-sm font-medium text-gray-900">{formatNumber(source.records)}</span>
                      </div>
                      
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Status</span>
                        <span className="text-sm text-blue-600">{source.lastSync}</span>
                      </div>
                      
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Quality</span>
                        <div className="flex items-center space-x-2">
                          <div className="w-12 h-2 bg-gray-200 rounded-full">
                            <div 
                              className="h-2 bg-green-500 rounded-full transition-all duration-300" 
                              style={{width: `${source.quality}%`}}
                            />
                          </div>
                          <span className="text-sm font-medium text-gray-900">{source.quality}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Data Pipeline Health */}
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Data Pipeline Health</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <CheckCircle className="w-8 h-8 text-green-600" />
                  </div>
                  <p className="font-semibold text-gray-900">Data Ingestion</p>
                  <p className="text-green-600 text-sm">Healthy</p>
                </div>
                
                <div className="text-center">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <Cpu className="w-8 h-8 text-blue-600" />
                  </div>
                  <p className="font-semibold text-gray-900">ML Processing</p>
                  <p className="text-blue-600 text-sm">Active</p>
                </div>
                
                <div className="text-center">
                  <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <Shield className="w-8 h-8 text-purple-600" />
                  </div>
                  <p className="font-semibold text-gray-900">Data Quality</p>
                  <p className="text-purple-600 text-sm">Validated</p>
                </div>
                
                <div className="text-center">
                  <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <Globe className="w-8 h-8 text-orange-600" />
                  </div>
                  <p className="font-semibold text-gray-900">Real-time Sync</p>
                  <p className="text-orange-600 text-sm">Live</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'agents' && (
          <div className="space-y-8">
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Multi-Agent System Status</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {data.agent_statuses.map((agent, index) => (
                  <div key={index} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-gray-900 capitalize">
                        {agent.agent_type.replace('_', ' ')}
                      </h4>
                      <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{agent.current_task}</p>
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-gray-500">Processed</span>
                      <span className="text-sm font-medium text-blue-600">
                        {formatNumber(agent.metrics.processed_count)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}