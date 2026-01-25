'use client';

import { useState, useEffect } from 'react';
import { 
  AlertTriangle, TrendingDown, TrendingUp, Clock, Brain, 
  Shield, Zap, CheckCircle, XCircle, AlertCircle, Eye
} from 'lucide-react';

interface Alert {
  id: string;
  type: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  timestamp: string;
  agent: string;
  confidence: number;
  impact: string;
  status: 'active' | 'acknowledged' | 'resolved';
}

export default function AlertPanel() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAlerts = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/v1/alerts');
      if (response.ok) {
        const data = await response.json();
        setAlerts(data.alerts || []);
      } else {
        // Mock alerts for demo when API is not available
        setAlerts([
          {
            id: '1',
            type: 'critical',
            title: 'Revenue Anomaly Detected',
            description: 'Sudden 15% drop in revenue detected in the last 2 hours. Pattern analysis suggests external market factors.',
            timestamp: new Date(Date.now() - 1800000).toISOString(),
            agent: 'Alert Monitor Agent',
            confidence: 94.5,
            impact: 'High - Potential $50K daily impact',
            status: 'active'
          },
          {
            id: '2',
            type: 'high',
            title: 'Customer Satisfaction Decline',
            description: 'Customer satisfaction score dropped below 4.0 threshold. Correlation with delivery delays identified.',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            agent: 'Trend Predictor Agent',
            confidence: 87.2,
            impact: 'Medium - Customer retention risk',
            status: 'acknowledged'
          },
          {
            id: '3',
            type: 'medium',
            title: 'Order Volume Spike',
            description: 'Unusual 25% increase in order volume detected. Monitoring for capacity constraints.',
            timestamp: new Date(Date.now() - 7200000).toISOString(),
            agent: 'Data Analyst Agent',
            confidence: 78.9,
            impact: 'Low - Positive revenue indicator',
            status: 'resolved'
          }
        ]);
      }
    } catch (error) {
      console.error('Error fetching alerts:', error);
      // Mock alerts for demo
      setAlerts([
        {
          id: '1',
          type: 'critical',
          title: 'Revenue Anomaly Detected',
          description: 'AI detected unusual revenue pattern requiring immediate attention.',
          timestamp: new Date(Date.now() - 1800000).toISOString(),
          agent: 'Alert Monitor Agent',
          confidence: 94.5,
          impact: 'High - Potential business impact',
          status: 'active'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'critical': return <XCircle className="w-5 h-5 text-red-500" />;
      case 'high': return <AlertTriangle className="w-5 h-5 text-orange-500" />;
      case 'medium': return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case 'low': return <CheckCircle className="w-5 h-5 text-blue-500" />;
      default: return <AlertCircle className="w-5 h-5 text-gray-500" />;
    }
  };

  const getAlertColor = (type: string) => {
    switch (type) {
      case 'critical': return 'border-red-500/50 bg-red-500/5';
      case 'high': return 'border-orange-500/50 bg-orange-500/5';
      case 'medium': return 'border-yellow-500/50 bg-yellow-500/5';
      case 'low': return 'border-blue-500/50 bg-blue-500/5';
      default: return 'border-gray-500/50 bg-gray-500/5';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-red-400 bg-red-500/20';
      case 'acknowledged': return 'text-yellow-400 bg-yellow-500/20';
      case 'resolved': return 'text-green-400 bg-green-500/20';
      default: return 'text-gray-400 bg-gray-500/20';
    }
  };

  const getAgentIcon = (agent: string) => {
    if (agent.includes('Monitor')) return <Eye className="w-4 h-4" />;
    if (agent.includes('Predictor')) return <TrendingUp className="w-4 h-4" />;
    if (agent.includes('Analyst')) return <Brain className="w-4 h-4" />;
    return <Shield className="w-4 h-4" />;
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const alertTime = new Date(timestamp);
    const diffMs = now.getTime() - alertTime.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.floor(diffHours / 24)}d ago`;
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6 animate-pulse">
            <div className="h-4 bg-white/10 rounded mb-3"></div>
            <div className="h-6 bg-white/10 rounded mb-2"></div>
            <div className="h-3 bg-white/10 rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Alert Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-red-500/10 backdrop-blur-sm rounded-lg border border-red-500/20 p-4">
          <div className="flex items-center space-x-2 mb-2">
            <XCircle className="w-5 h-5 text-red-400" />
            <span className="text-red-400 font-medium">Critical</span>
          </div>
          <p className="text-2xl font-bold text-white">
            {alerts.filter(a => a.type === 'critical' && a.status === 'active').length}
          </p>
        </div>
        
        <div className="bg-orange-500/10 backdrop-blur-sm rounded-lg border border-orange-500/20 p-4">
          <div className="flex items-center space-x-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-orange-400" />
            <span className="text-orange-400 font-medium">High</span>
          </div>
          <p className="text-2xl font-bold text-white">
            {alerts.filter(a => a.type === 'high' && a.status === 'active').length}
          </p>
        </div>
        
        <div className="bg-yellow-500/10 backdrop-blur-sm rounded-lg border border-yellow-500/20 p-4">
          <div className="flex items-center space-x-2 mb-2">
            <AlertCircle className="w-5 h-5 text-yellow-400" />
            <span className="text-yellow-400 font-medium">Medium</span>
          </div>
          <p className="text-2xl font-bold text-white">
            {alerts.filter(a => a.type === 'medium' && a.status === 'active').length}
          </p>
        </div>
        
        <div className="bg-green-500/10 backdrop-blur-sm rounded-lg border border-green-500/20 p-4">
          <div className="flex items-center space-x-2 mb-2">
            <CheckCircle className="w-5 h-5 text-green-400" />
            <span className="text-green-400 font-medium">Resolved</span>
          </div>
          <p className="text-2xl font-bold text-white">
            {alerts.filter(a => a.status === 'resolved').length}
          </p>
        </div>
      </div>

      {/* Alert List */}
      <div className="space-y-4">
        {alerts.length === 0 ? (
          <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-8 text-center">
            <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
            <h3 className="text-lg font-medium text-white mb-1">All Systems Normal</h3>
            <p className="text-gray-300">No active alerts detected by AI monitoring agents</p>
          </div>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className={`bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6 hover:bg-white/10 transition-all ${getAlertColor(alert.type)}`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  {getAlertIcon(alert.type)}
                  <div>
                    <h3 className="text-lg font-semibold text-white">{alert.title}</h3>
                    <div className="flex items-center space-x-4 mt-1">
                      <div className="flex items-center space-x-1 text-blue-300">
                        {getAgentIcon(alert.agent)}
                        <span className="text-sm">{alert.agent}</span>
                      </div>
                      <div className="flex items-center space-x-1 text-gray-300">
                        <Clock className="w-4 h-4" />
                        <span className="text-sm">{formatTimeAgo(alert.timestamp)}</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  <div className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(alert.status)}`}>
                    {alert.status.toUpperCase()}
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-300">Confidence</p>
                    <p className="text-lg font-bold text-white">{alert.confidence}%</p>
                  </div>
                </div>
              </div>
              
              <p className="text-gray-300 mb-4">{alert.description}</p>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Zap className="w-4 h-4 text-yellow-400" />
                  <span className="text-sm text-yellow-400 font-medium">{alert.impact}</span>
                </div>
                
                <div className="flex space-x-2">
                  {alert.status === 'active' && (
                    <>
                      <button className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-lg text-sm hover:bg-blue-500/30 transition-colors">
                        Acknowledge
                      </button>
                      <button className="px-3 py-1 bg-green-500/20 text-green-300 rounded-lg text-sm hover:bg-green-500/30 transition-colors">
                        Resolve
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* AI Monitoring Status */}
      <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-xl border border-blue-500/20 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white">AI Monitoring Status</h3>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-green-400 text-sm font-medium">Active Monitoring</span>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
              <Eye className="w-6 h-6 text-blue-400" />
            </div>
            <p className="text-white font-semibold">Continuous Observation</p>
            <p className="text-blue-400 text-sm">24/7 metric monitoring</p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
              <Brain className="w-6 h-6 text-purple-400" />
            </div>
            <p className="text-white font-semibold">Pattern Recognition</p>
            <p className="text-purple-400 text-sm">Anomaly detection active</p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
              <Shield className="w-6 h-6 text-green-400" />
            </div>
            <p className="text-white font-semibold">Proactive Response</p>
            <p className="text-green-400 text-sm">Instant alert generation</p>
          </div>
        </div>
      </div>
    </div>
  );
}