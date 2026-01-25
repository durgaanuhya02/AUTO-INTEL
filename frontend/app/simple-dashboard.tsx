'use client';

import { useState, useEffect } from 'react';
import { 
  Brain, Shield, BarChart3, CheckCircle, DollarSign, ShoppingCart, 
  Star, TrendingUp, TrendingDown, Activity, Target, Database
} from 'lucide-react';

interface DashboardData {
  current_metrics: {
    revenue: number;
    orders: number;
    avg_order_value: number;
    customer_satisfaction: number;
    monthly_growth: number;
  };
  alerts: Array<{
    id: number;
    title: string;
    message: string;
    severity: string;
    timestamp: string;
  }>;
  recent_decisions: Array<{
    id: number;
    title: string;
    description: string;
    status: string;
    confidence_score: number;
  }>;
  agent_statuses: Array<{
    agent_type: string;
    status: string;
    current_task: string;
    metrics: { processed_count: number };
  }>;
}

export default function SimpleDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<string>('');

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
      }
    } catch (error) {
      console.error('Error fetching data:', error);
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
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-20 w-20 border-4 border-blue-400 border-t-transparent mx-auto mb-6"></div>
          <h2 className="text-3xl font-bold text-white mb-2">Loading Agentic AI System</h2>
          <p className="text-blue-200">Initializing real-time analytics...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-white mb-2">Connection Error</h2>
          <p className="text-blue-200">Unable to connect to backend server</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900">
      {/* Header */}
      <header className="bg-black/20 backdrop-blur-lg border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-14 h-14 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <Brain className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">
                  Agentic AI Analytics Platform
                </h1>
                <p className="text-sm text-blue-200">
                  Real-time Intelligence • {formatNumber(data.current_metrics.orders)} Orders • Live Data
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2 bg-green-500/20 px-3 py-2 rounded-lg">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium text-green-300">Live</span>
              </div>
              
              <div className="text-right">
                <p className="text-sm font-medium text-white">Last Update</p>
                <p className="text-xs text-blue-200">{lastUpdate}</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Revenue */}
          <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-2 bg-green-100/20 rounded-lg">
                <DollarSign className="w-6 h-6 text-green-400" />
              </div>
              {data.current_metrics.monthly_growth > 0 ? (
                <TrendingUp className="w-4 h-4 text-green-400" />
              ) : (
                <TrendingDown className="w-4 h-4 text-red-400" />
              )}
            </div>
            <h3 className="text-sm font-medium text-gray-300 mb-1">Total Revenue</h3>
            <p className="text-3xl font-bold text-white mb-2">
              {formatCurrency(data.current_metrics.revenue)}
            </p>
            <p className={`text-sm ${data.current_metrics.monthly_growth > 0 ? 'text-green-400' : 'text-red-400'}`}>
              {data.current_metrics.monthly_growth > 0 ? '+' : ''}{data.current_metrics.monthly_growth.toFixed(1)}% growth
            </p>
          </div>

          {/* Orders */}
          <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-2 bg-blue-100/20 rounded-lg">
                <ShoppingCart className="w-6 h-6 text-blue-400" />
              </div>
              <Activity className="w-4 h-4 text-blue-400" />
            </div>
            <h3 className="text-sm font-medium text-gray-300 mb-1">Total Orders</h3>
            <p className="text-3xl font-bold text-white mb-2">
              {formatNumber(data.current_metrics.orders)}
            </p>
            <p className="text-sm text-blue-400">Processing live orders</p>
          </div>

          {/* AOV */}
          <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-2 bg-purple-100/20 rounded-lg">
                <Target className="w-6 h-6 text-purple-400" />
              </div>
              <BarChart3 className="w-4 h-4 text-purple-400" />
            </div>
            <h3 className="text-sm font-medium text-gray-300 mb-1">Avg Order Value</h3>
            <p className="text-3xl font-bold text-white mb-2">
              {formatCurrency(data.current_metrics.avg_order_value)}
            </p>
            <p className="text-sm text-purple-400">Per transaction</p>
          </div>

          {/* Satisfaction */}
          <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="p-2 bg-yellow-100/20 rounded-lg">
                <Star className="w-6 h-6 text-yellow-400" />
              </div>
              <CheckCircle className="w-4 h-4 text-green-400" />
            </div>
            <h3 className="text-sm font-medium text-gray-300 mb-1">Customer Satisfaction</h3>
            <p className="text-3xl font-bold text-white mb-2">
              {data.current_metrics.customer_satisfaction.toFixed(1)}/5.0
            </p>
            <div className="flex items-center space-x-1">
              {[1, 2, 3, 4, 5].map((star) => (
                <Star
                  key={star}
                  className={`w-4 h-4 ${
                    star <= Math.round(data.current_metrics.customer_satisfaction)
                      ? 'text-yellow-400 fill-current'
                      : 'text-gray-600'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Alerts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center">
              <Shield className="w-5 h-5 text-yellow-400 mr-2" />
              System Alerts
            </h3>
            <div className="space-y-3">
              {data.alerts.slice(0, 3).map((alert) => (
                <div key={alert.id} className="bg-white/5 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="font-medium text-white text-sm">{alert.title}</h4>
                    <span className={`px-2 py-1 rounded text-xs ${
                      alert.severity === 'critical' ? 'bg-red-500/20 text-red-300' :
                      alert.severity === 'high' ? 'bg-orange-500/20 text-orange-300' :
                      'bg-yellow-500/20 text-yellow-300'
                    }`}>
                      {alert.severity}
                    </span>
                  </div>
                  <p className="text-gray-300 text-xs">{alert.message}</p>
                </div>
              ))}
            </div>
          </div>

          {/* AI Decisions */}
          <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center">
              <Brain className="w-5 h-5 text-purple-400 mr-2" />
              AI Decisions
            </h3>
            <div className="space-y-3">
              {data.recent_decisions.slice(0, 3).map((decision) => (
                <div key={decision.id} className="bg-white/5 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="font-medium text-white text-sm">{decision.title}</h4>
                    <span className="text-xs text-blue-300">
                      {Math.round(decision.confidence_score * 100)}% confidence
                    </span>
                  </div>
                  <p className="text-gray-300 text-xs">{decision.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Agent Status */}
        <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center">
            <Database className="w-5 h-5 text-green-400 mr-2" />
            Multi-Agent System Status
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {data.agent_statuses.map((agent, index) => (
              <div key={index} className="bg-white/5 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-white capitalize">
                    {agent.agent_type.replace('_', ' ')}
                  </h4>
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                </div>
                <p className="text-gray-300 text-sm mb-1">{agent.current_task}</p>
                <p className="text-blue-300 text-xs">
                  Processed: {formatNumber(agent.metrics.processed_count)}
                </p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}