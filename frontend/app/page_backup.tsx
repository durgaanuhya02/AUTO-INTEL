'use client';

import { useState, useEffect } from 'react';
import { 
  Brain, Shield, TrendingUp, TrendingDown, DollarSign, ShoppingCart, 
  Users, Activity, Database, BarChart3, AlertTriangle, CheckCircle,
  Clock, Zap, Target, Eye, MessageSquare, Settings, Globe, Cpu
} from 'lucide-react';

// Import components
import RealTimeMetrics from '../components/RealTimeMetrics';
import AlertPanel from '../components/AlertPanel';
import AgentStatus from '../components/AgentStatus';
import DecisionPanel from '../components/DecisionPanel';
import AdvancedAnalytics from '../components/AdvancedAnalytics';

// Import WebSocket hook (temporarily disabled)
// import { useWebSocket } from '../hooks/useWebSocket';

interface ProductionMetrics {
  revenue: number;
  orders: number;
  avg_order_value: number;
  customer_satisfaction: number;
  monthly_growth: number;
}

interface DataSource {
  name: string;
  status: 'healthy' | 'warning' | 'error';
  records: number;
  lastSync: string;
  quality: number;
}

export default function AgenticAIDashboard() {
  const [metrics, setMetrics] = useState<ProductionMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [activeTab, setActiveTab] = useState('overview');

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/v1/dashboard');
      if (response.ok) {
        const data = await response.json();
        setMetrics(data.current_metrics);
        setLastUpdate(new Date().toLocaleTimeString());
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Mock data sources for production-grade feel
  const [dataSources] = useState<DataSource[]>([
    { name: 'Orders', status: 'healthy', records: 99441, lastSync: '2 min ago', quality: 98.5 },
    { name: 'Customers', status: 'healthy', records: 99441, lastSync: '2 min ago', quality: 97.2 },
    { name: 'Products', status: 'healthy', records: 32951, lastSync: '5 min ago', quality: 99.1 },
    { name: 'Payments', status: 'warning', records: 103886, lastSync: '3 min ago', quality: 95.8 },
    { name: 'Reviews', status: 'healthy', records: 99224, lastSync: '1 min ago', quality: 96.7 },
    { name: 'Geolocation', status: 'healthy', records: 1000163, lastSync: '4 min ago', quality: 94.3 },
    { name: 'External APIs', status: 'healthy', records: 0, lastSync: 'Live', quality: 99.9 }
  ]);

  useEffect(() => {
    // Fetch initial data
    fetchDashboardData();
    
    // Set up polling as fallback (every 30 seconds)
    const interval = setInterval(fetchDashboardData, 30000);
    
    return () => clearInterval(interval);
  }, []);

  // WebSocket for real-time updates (temporarily disabled)
  // const { isConnected: wsConnected } = useWebSocket({
  //   url: 'ws://localhost:8001/ws/real-time',
  //   onMessage: (message) => {
  //     console.log('📡 Received WebSocket message:', message);
      
  //     if (message.type === 'real_time_update' || message.type === 'initial_data') {
  //       const data = message.data;
  //       if (data?.metrics) {
  //         setMetrics(data.metrics);
  //         setLastUpdate(new Date().toLocaleTimeString());
  //       }
  //     }
  //   },
  //   onConnect: () => {
  //     console.log('🔌 WebSocket connected - real-time updates enabled');
  //   },
  //   onDisconnect: () => {
  //     console.log('🔌 WebSocket disconnected - falling back to polling');
  //   },
  //   onError: (error) => {
  //     console.error('WebSocket error:', error);
  //   }
  // });

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
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <div className="relative">
            <div className="animate-spin rounded-full h-20 w-20 border-4 border-blue-400 border-t-transparent mx-auto mb-6"></div>
            <Brain className="w-8 h-8 text-blue-400 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
          </div>
          <h2 className="text-3xl font-bold text-white mb-2">Initializing Agentic AI System</h2>
          <p className="text-blue-200">Loading multi-agent decision intelligence platform...</p>
          <div className="mt-4 flex items-center justify-center space-x-2">
            <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
            <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
            <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
          </div>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', name: 'Executive Overview', icon: BarChart3, description: 'Real-time business pulse' },
    { id: 'agents', name: 'Agent Status', icon: Brain, description: 'Multi-agent architecture' },
    { id: 'decisions', name: 'AI Decisions', icon: Target, description: 'Decision intelligence' },
    { id: 'analytics', name: 'Advanced Analytics', icon: Activity, description: 'AI-augmented insights' },
    { id: 'data', name: 'Data Sources', icon: Database, description: 'Production data pipeline' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900">
      {/* Header - Command Center Style */}
      <header className="bg-black/20 backdrop-blur-lg border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <div className="w-14 h-14 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                  <Brain className="w-7 h-7 text-white" />
                </div>
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-black animate-pulse"></div>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">
                  Agentic AI Decision Intelligence Platform
                </h1>
                <p className="text-sm text-blue-200">
                  Real-time Control Center • {formatNumber(metrics?.orders || 0)} Orders • Multi-Agent Architecture Active
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2 bg-green-500/20 px-3 py-2 rounded-lg">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium text-green-300">Live Intelligence</span>
              </div>
              
              <div className="text-right">
                <p className="text-sm font-medium text-white">System Time</p>
                <p className="text-xs text-blue-200">{lastUpdate}</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-black/10 backdrop-blur-sm border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6">
          <nav className="flex space-x-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-3 py-4 px-6 font-medium text-sm transition-all duration-200 ${
                    activeTab === tab.id
                      ? 'bg-blue-500/20 text-blue-300 border-b-2 border-blue-400'
                      : 'text-gray-300 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <div className="text-left">
                    <div>{tab.name}</div>
                    <div className="text-xs opacity-70">{tab.description}</div>
                  </div>
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
            {/* Executive KPIs - Real-Time Business Pulse */}
            <div className="mb-6">
              <h2 className="text-xl font-bold text-white mb-2">Executive Overview - Real-Time Business Pulse</h2>
              <p className="text-blue-200 text-sm">Live business KPIs with AI-powered trend analysis and risk detection</p>
            </div>
            
            <RealTimeMetrics />
            
            {/* System Alerts - Proactive Intelligence */}
            <div className="mb-6">
              <h2 className="text-xl font-bold text-white mb-2">System Alerts - Proactive Intelligence</h2>
              <p className="text-blue-200 text-sm">AI agents continuously monitor and detect anomalies before they become critical</p>
            </div>
            
            <AlertPanel />
          </div>
        )}

        {activeTab === 'agents' && (
          <div className="space-y-8">
            <div className="mb-6">
              <h2 className="text-xl font-bold text-white mb-2">Multi-Agent Architecture in Action</h2>
              <p className="text-blue-200 text-sm">Transparent AI behavior - each agent has specific responsibilities and shows real-time activity</p>
            </div>
            
            <AgentStatus />
          </div>
        )}

        {activeTab === 'decisions' && (
          <div className="space-y-8">
            <div className="mb-6">
              <h2 className="text-xl font-bold text-white mb-2">AI-Recommended Actions</h2>
              <p className="text-blue-200 text-sm">When critical situations are detected, AI proposes concrete business actions with human-in-the-loop governance</p>
            </div>
            
            <DecisionPanel />
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="space-y-8">
            <div className="mb-6">
              <h2 className="text-xl font-bold text-white mb-2">AI-Augmented Insights</h2>
              <p className="text-blue-200 text-sm">Automated conversion of analytics into natural-language insights and recommendations</p>
            </div>
            
            <AdvancedAnalytics />
          </div>
        )}

        {activeTab === 'data' && (
          <div className="space-y-8">
            <div className="mb-6">
              <h2 className="text-xl font-bold text-white mb-2">Production-Grade Data Engineering</h2>
              <p className="text-blue-200 text-sm">Multiple live and batch data pipelines with health monitoring and quality indicators</p>
            </div>
            
            {/* Data Sources Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {dataSources.map((source, index) => (
                <div key={index} className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6 hover:bg-white/10 transition-all">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <Database className="w-5 h-5 text-blue-400" />
                      <h3 className="font-semibold text-white">{source.name}</h3>
                    </div>
                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(source.status)}`}>
                      {source.status}
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-300 text-sm">Records</span>
                      <span className="text-white font-medium">{formatNumber(source.records)}</span>
                    </div>
                    
                    <div className="flex justify-between">
                      <span className="text-gray-300 text-sm">Last Sync</span>
                      <span className="text-blue-300 text-sm">{source.lastSync}</span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-gray-300 text-sm">Quality</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-16 h-2 bg-gray-700 rounded-full">
                          <div 
                            className="h-2 bg-green-500 rounded-full" 
                            style={{width: `${source.quality}%`}}
                          ></div>
                        </div>
                        <span className="text-white text-sm font-medium">{source.quality}%</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Data Pipeline Status */}
            <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6">
              <h3 className="text-lg font-bold text-white mb-4">Data Pipeline Health</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
                    <CheckCircle className="w-6 h-6 text-green-400" />
                  </div>
                  <p className="text-white font-semibold">Ingestion</p>
                  <p className="text-green-400 text-sm">Healthy</p>
                </div>
                
                <div className="text-center">
                  <div className="w-12 h-12 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
                    <Cpu className="w-6 h-6 text-blue-400" />
                  </div>
                  <p className="text-white font-semibold">Processing</p>
                  <p className="text-blue-400 text-sm">Active</p>
                </div>
                
                <div className="text-center">
                  <div className="w-12 h-12 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
                    <Shield className="w-6 h-6 text-purple-400" />
                  </div>
                  <p className="text-white font-semibold">Quality</p>
                  <p className="text-purple-400 text-sm">Validated</p>
                </div>
                
                <div className="text-center">
                  <div className="w-12 h-12 bg-orange-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
                    <Globe className="w-6 h-6 text-orange-400" />
                  </div>
                  <p className="text-white font-semibold">Distribution</p>
                  <p className="text-orange-400 text-sm">Synced</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer - Production Ready Indicator */}
      <footer className="bg-black/20 backdrop-blur-lg border-t border-white/10 mt-12">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Zap className="w-4 h-4 text-yellow-400" />
                <span className="text-sm text-gray-300">Production-Grade Architecture</span>
              </div>
              <div className="flex items-center space-x-2">
                <Eye className="w-4 h-4 text-blue-400" />
                <span className="text-sm text-gray-300">Transparent AI Decisions</span>
              </div>
              <div className="flex items-center space-x-2">
                <Shield className="w-4 h-4 text-green-400" />
                <span className="text-sm text-gray-300">Human-in-the-Loop Governance</span>
              </div>
            </div>
            
            <div className="text-right">
              <p className="text-xs text-gray-400">
                AI-Powered Business Command Center • Built for Scale
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}