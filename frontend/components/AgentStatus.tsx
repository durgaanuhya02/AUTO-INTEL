'use client';

import { useState, useEffect } from 'react';
import { 
  Brain, Eye, TrendingUp, BarChart3, Shield, Cpu, 
  Activity, Clock, CheckCircle, AlertCircle, Zap, Target
} from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  type: string;
  status: 'active' | 'idle' | 'processing' | 'error';
  lastActivity: string;
  currentTask: string;
  performance: number;
  uptime: string;
  tasksCompleted: number;
}

export default function AgentStatus() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAgentStatus();
    const interval = setInterval(fetchAgentStatus, 15000); // Update every 15 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchAgentStatus = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/v1/agents/status');
      if (response.ok) {
        const data = await response.json();
        setAgents(data.agents || []);
      } else {
        // Mock agent data for demo
        setAgents([
          {
            id: 'alert-monitor',
            name: 'Alert Monitor Agent',
            type: 'Observer',
            status: 'active',
            lastActivity: new Date(Date.now() - 30000).toISOString(),
            currentTask: 'Monitoring revenue metrics for anomalies',
            performance: 98.5,
            uptime: '99.9%',
            tasksCompleted: 1247
          },
          {
            id: 'trend-predictor',
            name: 'Trend Predictor Agent',
            type: 'Analyst',
            status: 'processing',
            lastActivity: new Date(Date.now() - 120000).toISOString(),
            currentTask: 'Analyzing seasonal patterns in customer behavior',
            performance: 94.2,
            uptime: '99.7%',
            tasksCompleted: 892
          },
          {
            id: 'data-analyst',
            name: 'Data Analyst Agent',
            type: 'Processor',
            status: 'active',
            lastActivity: new Date(Date.now() - 45000).toISOString(),
            currentTask: 'Performing root-cause analysis on satisfaction decline',
            performance: 96.8,
            uptime: '99.8%',
            tasksCompleted: 2156
          },
          {
            id: 'decision-engine',
            name: 'Decision Engine Agent',
            type: 'Governor',
            status: 'idle',
            lastActivity: new Date(Date.now() - 300000).toISOString(),
            currentTask: 'Awaiting critical decision points',
            performance: 99.1,
            uptime: '100%',
            tasksCompleted: 543
          },
          {
            id: 'simulation-agent',
            name: 'Simulation Agent',
            type: 'Predictor',
            status: 'processing',
            lastActivity: new Date(Date.now() - 60000).toISOString(),
            currentTask: 'Running ML-driven demand forecasting scenarios',
            performance: 91.7,
            uptime: '99.5%',
            tasksCompleted: 678
          }
        ]);
      }
    } catch (error) {
      console.error('Error fetching agent status:', error);
      // Mock data on error
      setAgents([
        {
          id: 'alert-monitor',
          name: 'Alert Monitor Agent',
          type: 'Observer',
          status: 'active',
          lastActivity: new Date().toISOString(),
          currentTask: 'Continuous monitoring active',
          performance: 98.5,
          uptime: '99.9%',
          tasksCompleted: 1247
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'processing': return <Cpu className="w-5 h-5 text-blue-400 animate-spin" />;
      case 'idle': return <Clock className="w-5 h-5 text-gray-400" />;
      case 'error': return <AlertCircle className="w-5 h-5 text-red-400" />;
      default: return <Activity className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-400 bg-green-500/20';
      case 'processing': return 'text-blue-400 bg-blue-500/20';
      case 'idle': return 'text-gray-400 bg-gray-500/20';
      case 'error': return 'text-red-400 bg-red-500/20';
      default: return 'text-gray-400 bg-gray-500/20';
    }
  };

  const getAgentTypeIcon = (type: string) => {
    switch (type) {
      case 'Observer': return <Eye className="w-6 h-6" />;
      case 'Analyst': return <Brain className="w-6 h-6" />;
      case 'Processor': return <BarChart3 className="w-6 h-6" />;
      case 'Governor': return <Shield className="w-6 h-6" />;
      case 'Predictor': return <TrendingUp className="w-6 h-6" />;
      default: return <Cpu className="w-6 h-6" />;
    }
  };

  const getAgentTypeColor = (type: string) => {
    switch (type) {
      case 'Observer': return 'bg-blue-500/20 text-blue-400';
      case 'Analyst': return 'bg-purple-500/20 text-purple-400';
      case 'Processor': return 'bg-green-500/20 text-green-400';
      case 'Governor': return 'bg-orange-500/20 text-orange-400';
      case 'Predictor': return 'bg-pink-500/20 text-pink-400';
      default: return 'bg-gray-500/20 text-gray-400';
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const activityTime = new Date(timestamp);
    const diffMs = now.getTime() - activityTime.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.floor(diffHours / 24)}d ago`;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6 animate-pulse">
            <div className="h-6 bg-white/10 rounded mb-4"></div>
            <div className="h-4 bg-white/10 rounded mb-2"></div>
            <div className="h-3 bg-white/10 rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Agent Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-green-500/10 backdrop-blur-sm rounded-lg border border-green-500/20 p-4">
          <div className="flex items-center space-x-2 mb-2">
            <CheckCircle className="w-5 h-5 text-green-400" />
            <span className="text-green-400 font-medium">Active</span>
          </div>
          <p className="text-2xl font-bold text-white">
            {agents.filter(a => a.status === 'active').length}
          </p>
        </div>
        
        <div className="bg-blue-500/10 backdrop-blur-sm rounded-lg border border-blue-500/20 p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Cpu className="w-5 h-5 text-blue-400" />
            <span className="text-blue-400 font-medium">Processing</span>
          </div>
          <p className="text-2xl font-bold text-white">
            {agents.filter(a => a.status === 'processing').length}
          </p>
        </div>
        
        <div className="bg-gray-500/10 backdrop-blur-sm rounded-lg border border-gray-500/20 p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Clock className="w-5 h-5 text-gray-400" />
            <span className="text-gray-400 font-medium">Idle</span>
          </div>
          <p className="text-2xl font-bold text-white">
            {agents.filter(a => a.status === 'idle').length}
          </p>
        </div>
        
        <div className="bg-purple-500/10 backdrop-blur-sm rounded-lg border border-purple-500/20 p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Target className="w-5 h-5 text-purple-400" />
            <span className="text-purple-400 font-medium">Total Tasks</span>
          </div>
          <p className="text-2xl font-bold text-white">
            {agents.reduce((sum, agent) => sum + agent.tasksCompleted, 0)}
          </p>
        </div>
      </div>

      {/* Agent Details */}
      <div className="space-y-4">
        {agents.map((agent) => (
          <div
            key={agent.id}
            className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6 hover:bg-white/10 transition-all"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-4">
                <div className={`p-3 rounded-lg ${getAgentTypeColor(agent.type)}`}>
                  {getAgentTypeIcon(agent.type)}
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">{agent.name}</h3>
                  <div className="flex items-center space-x-4 mt-1">
                    <span className="text-sm text-blue-300">{agent.type} Agent</span>
                    <div className="flex items-center space-x-1">
                      <Clock className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-300">Last activity: {formatTimeAgo(agent.lastActivity)}</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <div className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(agent.status)}`}>
                  {agent.status.toUpperCase()}
                </div>
                {getStatusIcon(agent.status)}
              </div>
            </div>
            
            <div className="mb-4">
              <p className="text-sm text-gray-300 mb-2">Current Task:</p>
              <p className="text-white">{agent.currentTask}</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white/5 rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-300">Performance</span>
                  <span className="text-sm font-medium text-white">{agent.performance}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-green-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${agent.performance}%` }}
                  ></div>
                </div>
              </div>
              
              <div className="bg-white/5 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">Uptime</span>
                  <span className="text-sm font-medium text-green-400">{agent.uptime}</span>
                </div>
              </div>
              
              <div className="bg-white/5 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">Tasks Completed</span>
                  <span className="text-sm font-medium text-blue-400">{agent.tasksCompleted.toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Multi-Agent Architecture Info */}
      <div className="bg-gradient-to-r from-purple-500/10 to-blue-500/10 rounded-xl border border-purple-500/20 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white">Multi-Agent Architecture</h3>
          <div className="flex items-center space-x-2">
            <Zap className="w-5 h-5 text-yellow-400" />
            <span className="text-yellow-400 text-sm font-medium">Transparent AI Behavior</span>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
              <Eye className="w-6 h-6 text-blue-400" />
            </div>
            <p className="text-white font-semibold text-sm">Observer</p>
            <p className="text-blue-400 text-xs">Continuous monitoring</p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
              <Brain className="w-6 h-6 text-purple-400" />
            </div>
            <p className="text-white font-semibold text-sm">Analyst</p>
            <p className="text-purple-400 text-xs">Pattern analysis</p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
              <BarChart3 className="w-6 h-6 text-green-400" />
            </div>
            <p className="text-white font-semibold text-sm">Processor</p>
            <p className="text-green-400 text-xs">Data processing</p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-orange-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
              <Shield className="w-6 h-6 text-orange-400" />
            </div>
            <p className="text-white font-semibold text-sm">Governor</p>
            <p className="text-orange-400 text-xs">Decision control</p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-pink-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
              <TrendingUp className="w-6 h-6 text-pink-400" />
            </div>
            <p className="text-white font-semibold text-sm">Predictor</p>
            <p className="text-pink-400 text-xs">Future modeling</p>
          </div>
        </div>
      </div>
    </div>
  );
}