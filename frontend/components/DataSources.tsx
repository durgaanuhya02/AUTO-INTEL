'use client';

import { useState, useEffect } from 'react';
import { 
  Database, Server, Cloud, Wifi, WifiOff, CheckCircle, AlertCircle, 
  Clock, Settings, RefreshCw, Plus, Edit, Trash2, Eye, Activity,
  Shield, Key, Globe, HardDrive, Zap, BarChart3
} from 'lucide-react';

interface DataSource {
  id: string;
  name: string;
  type: string;
  status: 'connected' | 'disconnected' | 'error' | 'syncing';
  enabled: boolean;
  last_sync: string;
  records_count: number;
  data_quality: 'high' | 'medium' | 'low';
  connection_health: number;
  description: string;
}

export default function DataSources() {
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSource, setSelectedSource] = useState<DataSource | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    fetchDataSources();
    const interval = setInterval(fetchDataSources, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDataSources = async () => {
    try {
      // Simulate real data sources from our Brazilian E-commerce dataset
      const mockSources: DataSource[] = [
        {
          id: 'olist_orders',
          name: 'Orders Dataset',
          type: 'CSV File',
          status: 'connected',
          enabled: true,
          last_sync: new Date().toISOString(),
          records_count: 99441,
          data_quality: 'high',
          connection_health: 98,
          description: 'Primary orders data from Brazilian e-commerce platform'
        },
        {
          id: 'olist_customers',
          name: 'Customers Dataset',
          type: 'CSV File',
          status: 'connected',
          enabled: true,
          last_sync: new Date().toISOString(),
          records_count: 99441,
          data_quality: 'high',
          connection_health: 95,
          description: 'Customer information and demographics'
        },
        {
          id: 'olist_products',
          name: 'Products Catalog',
          type: 'CSV File',
          status: 'connected',
          enabled: true,
          last_sync: new Date().toISOString(),
          records_count: 32951,
          data_quality: 'high',
          connection_health: 92,
          description: 'Product catalog with categories and specifications'
        },
        {
          id: 'olist_reviews',
          name: 'Customer Reviews',
          type: 'CSV File',
          status: 'connected',
          enabled: true,
          last_sync: new Date().toISOString(),
          records_count: 99224,
          data_quality: 'high',
          connection_health: 89,
          description: 'Customer reviews and satisfaction scores'
        },
        {
          id: 'olist_payments',
          name: 'Payment Data',
          type: 'CSV File',
          status: 'connected',
          enabled: true,
          last_sync: new Date().toISOString(),
          records_count: 103886,
          data_quality: 'high',
          connection_health: 94,
          description: 'Payment methods and transaction details'
        },
        {
          id: 'olist_geolocation',
          name: 'Geolocation Data',
          type: 'CSV File',
          status: 'syncing',
          enabled: true,
          last_sync: new Date(Date.now() - 300000).toISOString(),
          records_count: 1000163,
          data_quality: 'medium',
          connection_health: 87,
          description: 'Geographic coordinates for delivery optimization'
        },
        {
          id: 'external_api',
          name: 'External Analytics API',
          type: 'REST API',
          status: 'disconnected',
          enabled: false,
          last_sync: new Date(Date.now() - 86400000).toISOString(),
          records_count: 0,
          data_quality: 'low',
          connection_health: 0,
          description: 'Third-party analytics integration (optional)'
        }
      ];
      
      setDataSources(mockSources);
    } catch (error) {
      console.error('Error fetching data sources:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'syncing':
        return <RefreshCw className="w-5 h-5 text-blue-600 animate-spin" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      default:
        return <WifiOff className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'bg-green-100 text-green-800';
      case 'syncing':
        return 'bg-blue-100 text-blue-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'CSV File':
        return <HardDrive className="w-5 h-5 text-blue-600" />;
      case 'REST API':
        return <Globe className="w-5 h-5 text-purple-600" />;
      case 'Database':
        return <Database className="w-5 h-5 text-green-600" />;
      default:
        return <Server className="w-5 h-5 text-gray-600" />;
    }
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-gray-200 rounded w-1/3"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="h-48 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <div className="bg-gradient-to-r from-indigo-600 to-blue-600 rounded-xl p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Data Sources</h1>
            <p className="text-indigo-100 text-lg">
              Manage and monitor your data connections and integrations
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <p className="text-sm text-indigo-100">Active Sources</p>
              <p className="text-2xl font-bold">
                {dataSources.filter(s => s.status === 'connected').length}
              </p>
            </div>
            <button 
              onClick={() => setShowAddModal(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-white/20 rounded-lg hover:bg-white/30 transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Add Source</span>
            </button>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-green-100 rounded-xl">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <span className="text-2xl font-bold text-green-600">
              {dataSources.filter(s => s.status === 'connected').length}
            </span>
          </div>
          <h3 className="font-semibold text-gray-900">Connected</h3>
          <p className="text-sm text-gray-500">Active data sources</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-blue-100 rounded-xl">
              <Activity className="w-6 h-6 text-blue-600" />
            </div>
            <span className="text-2xl font-bold text-blue-600">
              {dataSources.filter(s => s.status === 'syncing').length}
            </span>
          </div>
          <h3 className="font-semibold text-gray-900">Syncing</h3>
          <p className="text-sm text-gray-500">Currently updating</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-orange-100 rounded-xl">
              <BarChart3 className="w-6 h-6 text-orange-600" />
            </div>
            <span className="text-2xl font-bold text-orange-600">
              {dataSources.reduce((sum, s) => sum + s.records_count, 0).toLocaleString()}
            </span>
          </div>
          <h3 className="font-semibold text-gray-900">Total Records</h3>
          <p className="text-sm text-gray-500">Across all sources</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-purple-100 rounded-xl">
              <Shield className="w-6 h-6 text-purple-600" />
            </div>
            <span className="text-2xl font-bold text-purple-600">
              {Math.round(dataSources.reduce((sum, s) => sum + s.connection_health, 0) / dataSources.length)}%
            </span>
          </div>
          <h3 className="font-semibold text-gray-900">Health Score</h3>
          <p className="text-sm text-gray-500">Average connection health</p>
        </div>
      </div>

      {/* Data Sources Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {dataSources.map((source) => (
          <div key={source.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                {getTypeIcon(source.type)}
                <div>
                  <h3 className="font-semibold text-gray-900">{source.name}</h3>
                  <p className="text-sm text-gray-500">{source.type}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {getStatusIcon(source.status)}
                <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(source.status)}`}>
                  {source.status}
                </span>
              </div>
            </div>

            <p className="text-sm text-gray-600 mb-4">{source.description}</p>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Records</span>
                <span className="text-sm font-medium text-gray-900">
                  {formatNumber(source.records_count)}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Data Quality</span>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  source.data_quality === 'high' ? 'bg-green-100 text-green-800' :
                  source.data_quality === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {source.data_quality}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Health</span>
                <div className="flex items-center space-x-2">
                  <div className="w-16 bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        source.connection_health >= 90 ? 'bg-green-500' :
                        source.connection_health >= 70 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${source.connection_health}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-600">{source.connection_health}%</span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Last Sync</span>
                <span className="text-xs text-gray-600">
                  {new Date(source.last_sync).toLocaleString()}
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-100">
              <div className="flex items-center space-x-2">
                <button 
                  onClick={() => setSelectedSource(source)}
                  className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                >
                  <Eye className="w-4 h-4" />
                </button>
                <button className="p-2 text-gray-400 hover:text-green-600 transition-colors">
                  <Edit className="w-4 h-4" />
                </button>
                <button className="p-2 text-gray-400 hover:text-red-600 transition-colors">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              
              <label className="relative inline-flex items-center cursor-pointer">
                <input 
                  type="checkbox" 
                  className="sr-only peer" 
                  checked={source.enabled}
                  onChange={() => {}}
                />
                <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        ))}
      </div>

      {/* Connection Health Overview */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Connection Health Overview</h2>
        <div className="space-y-4">
          {dataSources.map((source) => (
            <div key={source.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-4">
                {getTypeIcon(source.type)}
                <div>
                  <h3 className="font-medium text-gray-900">{source.name}</h3>
                  <p className="text-sm text-gray-500">{formatNumber(source.records_count)} records</p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="w-32 bg-gray-200 rounded-full h-3">
                  <div 
                    className={`h-3 rounded-full transition-all duration-500 ${
                      source.connection_health >= 90 ? 'bg-green-500' :
                      source.connection_health >= 70 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${source.connection_health}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-gray-900 w-12">
                  {source.connection_health}%
                </span>
                {getStatusIcon(source.status)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}