'use client';

import { useState, useEffect } from 'react';
import { Activity, Cpu, HardDrive, Wifi, Clock, Zap } from 'lucide-react';

interface PerformanceMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_latency: number;
  response_time: number;
  uptime: number;
  active_connections: number;
  requests_per_minute: number;
  error_rate: number;
  timestamp: string;
}

export default function PerformanceMonitor({ className = '' }: { className?: string }) {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/v1/metrics/system');
      if (response.ok) {
        const data = await response.json();
        setMetrics(data);
      }
    } catch (error) {
      console.error('Error fetching performance metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (value: number, thresholds: { warning: number; critical: number }) => {
    if (value >= thresholds.critical) return 'text-red-600 bg-red-100';
    if (value >= thresholds.warning) return 'text-yellow-600 bg-yellow-100';
    return 'text-green-600 bg-green-100';
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="text-center py-8">
          <Activity className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-gray-900 mb-1">Performance Data Unavailable</h3>
          <p className="text-gray-500">Unable to fetch system performance metrics</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">System Performance</h3>
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span>Live</span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors duration-200">
          <div className="flex items-center justify-between mb-2">
            <Cpu className="w-5 h-5 text-blue-600" />
            <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(metrics.cpu_usage, { warning: 70, critical: 90 })}`}>
              {metrics.cpu_usage.toFixed(1)}%
            </span>
          </div>
          <h4 className="text-sm font-medium text-gray-900">CPU Usage</h4>
          <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${Math.min(metrics.cpu_usage, 100)}%` }}
            />
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors duration-200">
          <div className="flex items-center justify-between mb-2">
            <HardDrive className="w-5 h-5 text-green-600" />
            <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(metrics.memory_usage, { warning: 80, critical: 95 })}`}>
              {metrics.memory_usage.toFixed(1)}%
            </span>
          </div>
          <h4 className="text-sm font-medium text-gray-900">Memory</h4>
          <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-green-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${Math.min(metrics.memory_usage, 100)}%` }}
            />
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors duration-200">
          <div className="flex items-center justify-between mb-2">
            <Wifi className="w-5 h-5 text-purple-600" />
            <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(metrics.network_latency, { warning: 100, critical: 200 })}`}>
              {metrics.network_latency.toFixed(0)}ms
            </span>
          </div>
          <h4 className="text-sm font-medium text-gray-900">Latency</h4>
          <p className="text-xs text-gray-500 mt-1">Network response time</p>
        </div>

        <div className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors duration-200">
          <div className="flex items-center justify-between mb-2">
            <Zap className="w-5 h-5 text-yellow-600" />
            <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(metrics.response_time, { warning: 500, critical: 1000 })}`}>
              {metrics.response_time.toFixed(0)}ms
            </span>
          </div>
          <h4 className="text-sm font-medium text-gray-900">Response</h4>
          <p className="text-xs text-gray-500 mt-1">API response time</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <div className="flex items-center justify-center mb-2">
            <Clock className="w-4 h-4 text-gray-600 mr-1" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{formatUptime(metrics.uptime)}</p>
          <p className="text-xs text-gray-500">Uptime</p>
        </div>

        <div className="text-center">
          <div className="flex items-center justify-center mb-2">
            <Activity className="w-4 h-4 text-gray-600 mr-1" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{metrics.active_connections}</p>
          <p className="text-xs text-gray-500">Connections</p>
        </div>

        <div className="text-center">
          <p className="text-2xl font-bold text-gray-900">{metrics.requests_per_minute}</p>
          <p className="text-xs text-gray-500">Requests/min</p>
        </div>

        <div className="text-center">
          <p className={`text-2xl font-bold ${metrics.error_rate > 5 ? 'text-red-600' : 'text-green-600'}`}>
            {metrics.error_rate.toFixed(1)}%
          </p>
          <p className="text-xs text-gray-500">Error Rate</p>
        </div>
      </div>
    </div>
  );
}