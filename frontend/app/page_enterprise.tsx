'use client';

import { useState, useEffect } from 'react';
import { Upload, Database, TrendingUp, Settings, Brain, Users, Target } from 'lucide-react';
import AgentStatus from '../components/AgentStatus';
import DecisionPanel from '../components/DecisionPanel';
import AlertPanel from '../components/AlertPanel';
import MetricCard from '../components/MetricCard';
import ProductionAnalytics from '../components/ProductionAnalytics';
import DataSources from '../components/DataSources';
import EnterpriseSettings from '../components/EnterpriseSettings';
import AdvancedForecasting from '../components/AdvancedForecasting';
import { apiClient, wsClient } from '../lib/api';
import { DashboardData } from '../types';
import CSVUpload from '../components/CSVUpload';
import NotificationSystem, { useNotifications } from '../components/NotificationSystem';

export default function EnterpriseDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [enterpriseMetrics, setEnterpriseMetrics] = useState<any>({});
  const [integrationStatus, setIntegrationStatus] = useState<any>({});
  const [analyticsStatus, setAnalyticsStatus] = useState<any>({});
  
  const { notifications, addNotification, removeNotification } = useNotifications();

  useEffect(() => {
    fetchDashboardData();
    fetchEnterpriseData();
    setupWebSocket();
    
    // Refresh data every 30 seconds
    const interval = setInterval(() => {
      fetchDashboardData();
      fetchEnterpriseData();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Use production backend with real data
      const response = await fetch('http://localhost:8001/api/v1/dashboard');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      setData(result as DashboardData);
      
      addNotification({
        type: 'success',
        title: 'Real Data Updated',
        message: `Processed ${result.current_metrics?.orders || 0} orders from Brazilian E-commerce Dataset`,
        duration: 3000
      });
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      addNotification({
        type: 'error',
        title: 'Data Connection Error',
        message: 'Failed to fetch real-time data. Check if production server is running.',
        duration: 5000
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchEnterpriseData = async () => {
    try {
      // Fetch real-time analytics from production backend
      const analyticsResponse = await fetch('http://localhost:8001/api/v1/analytics/real-time');
      if (analyticsResponse.ok) {
        const analytics = await analyticsResponse.json();
        setEnterpriseMetrics(analytics.revenue_analytics || {});
        setAnalyticsStatus({
          running: true,
          last_update: new Date().toISOString(),
          data_source: 'Brazilian E-commerce Dataset'
        });
      }

      // Fetch business insights
      const insightsResponse = await fetch('http://localhost:8001/api/v1/insights/business');
      if (insightsResponse.ok) {
        setIntegrationStatus({
          'data_processing': { status: 'connected', enabled: true, last_check: new Date().toISOString() },
          'analytics_engine': { status: 'connected', enabled: true, last_check: new Date().toISOString() },
          'real_time_insights': { status: 'connected', enabled: true, last_check: new Date().toISOString() },
          'brazilian_ecommerce': { status: 'connected', enabled: true, last_check: new Date().toISOString() }
        });
      }
    } catch (error) {
      console.error('Error fetching enterprise data:', error);
      setIntegrationStatus({
        'data_processing': { status: 'disconnected', enabled: false, last_check: new Date().toISOString() },
        'analytics_engine': { status: 'disconnected', enabled: false, last_check: new Date().toISOString() }
      });
    }
  };

  const setupWebSocket = async () => {
    try {
      await wsClient.connect();
      
      wsClient.on('agent_update', (updateData) => {
        console.log('Agent update received:', updateData);
        fetchDashboardData();
      });

      wsClient.on('new_alert', (alertData) => {
        console.log('New alert received:', alertData);
        fetchDashboardData();
      });

      wsClient.on('new_decision', (decisionData) => {
        console.log('New decision received:', decisionData);
        fetchDashboardData();
      });
    } catch (error) {
      console.error('WebSocket connection failed:', error);
    }
  };

  const handleApproveDecision = async (decisionId: number, approved: boolean, comments?: string) => {
    try {
      await apiClient.approveDecision(
        decisionId.toString(),
        approved,
        'dashboard_user',
        comments
      );
      fetchDashboardData();
    } catch (error) {
      console.error('Error approving decision:', error);
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
    { id: 'overview', name: 'Executive Overview', icon: TrendingUp },
    { id: 'analytics', name: 'Advanced Analytics', icon: Brain },
    { id: 'forecasting', name: 'AI Forecasting', icon: Target },
    { id: 'integrations', name: 'Data Sources', icon: Database },
    { id: 'data-upload', name: 'Data Upload', icon: Upload },
    { id: 'settings', name: 'Settings', icon: Settings }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <NotificationSystem 
        notifications={notifications} 
        onDismiss={removeNotification} 
      />
      
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
                  Brazilian E-commerce Dataset • Real-time Insights • {data?.current_metrics?.orders ? data.current_metrics.orders.toLocaleString() : '0'} Orders Processed
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium text-gray-700">Live Data</span>
              </div>
              
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">
                  {data?.current_metrics?.revenue ? formatCurrency(data.current_metrics.revenue) : '$0'}
                </p>
                <p className="text-xs text-gray-500">Total Revenue</p>
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
            {/* Real-time Data Banner */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                  <div>
                    <p className="text-lg font-semibold text-blue-900">
                      Live Data from Brazilian E-commerce Dataset
                    </p>
                    <p className="text-sm text-blue-700">
                      Processing {data?.current_metrics?.orders ? data.current_metrics.orders.toLocaleString() : '0'} real orders • 
                      Revenue: {data?.current_metrics?.revenue ? formatCurrency(data.current_metrics.revenue) : '$0'} • 
                      Last update: {new Date().toLocaleTimeString()}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-blue-900">Data Quality: High</p>
                  <p className="text-xs text-blue-700">Real-time processing</p>
                </div>
              </div>
            </div>

            {/* Key Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <MetricCard
                title="Total Revenue"
                value={data?.current_metrics?.revenue || 0}
                format="currency"
                trend={data?.trends?.revenue || []}
              />
              <MetricCard
                title="Total Orders"
                value={data?.current_metrics?.orders || 0}
                format="number"
                trend={data?.trends?.orders || []}
              />
              <MetricCard
                title="Avg Order Value"
                value={data?.current_metrics?.avg_order_value || 0}
                format="currency"
                trend={[]}
              />
              <MetricCard
                title="Customer Satisfaction"
                value={data?.current_metrics?.customer_satisfaction || 0}
                format="number"
                trend={data?.trends?.customer_satisfaction || []}
              />
            </div>

            {/* Charts and Panels */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                <AlertPanel alerts={data?.alerts || []} />
                <DecisionPanel 
                  decisions={data?.recent_decisions || []} 
                  onApprove={handleApproveDecision}
                />
              </div>
              
              <div className="space-y-6">
                <AgentStatus agents={data?.agent_statuses || []} />
                
                {/* System Health */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Mode</span>
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                        Production
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Data Source</span>
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                        Brazilian E-commerce
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Analytics Engine</span>
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                        Running
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">System Status</span>
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                        Operational
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'analytics' && (
          <ProductionAnalytics />
        )}

        {activeTab === 'forecasting' && (
          <AdvancedForecasting />
        )}

        {activeTab === 'integrations' && (
          <DataSources />
        )}

        {activeTab === 'data-upload' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Data Upload & ML Training</h2>
              <p className="text-gray-600 mb-6">
                Upload CSV files to train custom ML models for your business data.
              </p>
              
              <CSVUpload onUploadComplete={(result) => {
                console.log('Model training completed:', result);
                fetchEnterpriseData();
              }} />
            </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <EnterpriseSettings />
        )}
      </main>
    </div>
  );
}