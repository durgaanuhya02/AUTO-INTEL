'use client';

import { useState, useEffect } from 'react';
import { AGENT_API_URL } from '../lib/config';
import { DashboardDecision, toDecision, upsertById } from '../lib/adapters';
import { useRealtime } from '../hooks/useWebSocket';
import LiveStatusBadge from './LiveStatusBadge';
import { 
  Target, Brain, CheckCircle, Clock, AlertTriangle, 
  TrendingUp, DollarSign, Users, Zap, ThumbsUp, ThumbsDown,
  Eye, Shield, MessageSquare
} from 'lucide-react';

type Decision = DashboardDecision;

export default function DecisionPanel() {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDecisions();
    const interval = setInterval(fetchDecisions, 30000);
    return () => clearInterval(interval);
  }, []);

  const { status } = useRealtime({
    new_decision: (data) => {
      const decision = toDecision(data);
      if (decision) setDecisions((prev) => upsertById(prev, decision));
    },
  });

  const [acting, setActing] = useState<string | null>(null);

  const submitReview = async (decisionId: string, approved: boolean) => {
    setActing(decisionId);
    try {
      const params = new URLSearchParams({
        decision_id: decisionId,
        approved: String(approved),
        approver: 'dashboard-user',
      });
      const response = await fetch(`${AGENT_API_URL}/approve-decision?${params}`, { method: 'POST' });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `HTTP ${response.status}`);
      }
      setError(null);
      // The governance agent records the outcome and pushes it over the WebSocket; refetch as a fallback.
      setTimeout(fetchDecisions, 1500);
    } catch (err) {
      console.error('Error submitting review:', err);
      setError(err instanceof Error ? err.message : 'unknown error');
    } finally {
      setActing(null);
    }
  };

  const fetchDecisions = async () => {
    try {
      const response = await fetch(`${AGENT_API_URL}/decisions`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      const latestById = new Map<string, DashboardDecision>();
      for (const raw of data.decisions || []) {
        const decision = toDecision(raw);
        if (decision && !latestById.has(decision.id)) latestById.set(decision.id, decision); // list is newest-first
      }
      setDecisions(Array.from(latestById.values()));
      setError(null);
    } catch (err) {
      // Never substitute made-up decisions: keep the last real data and surface the failure.
      console.error('Error fetching decisions:', err);
      setError(err instanceof Error ? err.message : 'unknown error');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return <Clock className="w-5 h-5 text-yellow-400" />;
      case 'approved': return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'rejected': return <AlertTriangle className="w-5 h-5 text-red-400" />;
      case 'implemented': return <CheckCircle className="w-5 h-5 text-blue-400" />;
      default: return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'text-yellow-400 bg-yellow-500/20';
      case 'approved': return 'text-green-400 bg-green-500/20';
      case 'rejected': return 'text-red-400 bg-red-500/20';
      case 'implemented': return 'text-blue-400 bg-blue-500/20';
      default: return 'text-gray-400 bg-gray-500/20';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'pricing': return <DollarSign className="w-5 h-5" />;
      case 'inventory': return <Target className="w-5 h-5" />;
      case 'marketing': return <Users className="w-5 h-5" />;
      case 'operations': return <TrendingUp className="w-5 h-5" />;
      default: return <Brain className="w-5 h-5" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'pricing': return 'bg-green-500/20 text-green-400';
      case 'inventory': return 'bg-blue-500/20 text-blue-400';
      case 'marketing': return 'bg-purple-500/20 text-purple-400';
      case 'operations': return 'bg-orange-500/20 text-orange-400';
      default: return 'bg-gray-500/20 text-gray-400';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'text-green-400';
      case 'medium': return 'text-yellow-400';
      case 'high': return 'text-red-400';
      default: return 'text-gray-400';
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

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const decisionTime = new Date(timestamp);
    const diffMs = now.getTime() - decisionTime.getTime();
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
      <LiveStatusBadge status={status} error={error} />

      {/* Decision Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-yellow-500/10 backdrop-blur-sm rounded-lg border border-yellow-500/20 p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Clock className="w-5 h-5 text-yellow-400" />
            <span className="text-yellow-400 font-medium">Pending</span>
          </div>
          <p className="text-2xl font-bold text-white">
            {decisions.filter(d => d.status === 'pending').length}
          </p>
        </div>
        
        <div className="bg-green-500/10 backdrop-blur-sm rounded-lg border border-green-500/20 p-4">
          <div className="flex items-center space-x-2 mb-2">
            <CheckCircle className="w-5 h-5 text-green-400" />
            <span className="text-green-400 font-medium">Approved</span>
          </div>
          <p className="text-2xl font-bold text-white">
            {decisions.filter(d => d.status === 'approved').length}
          </p>
        </div>
        
        <div className="bg-blue-500/10 backdrop-blur-sm rounded-lg border border-blue-500/20 p-4">
          <div className="flex items-center space-x-2 mb-2">
            <CheckCircle className="w-5 h-5 text-blue-400" />
            <span className="text-blue-400 font-medium">Implemented</span>
          </div>
          <p className="text-2xl font-bold text-white">
            {decisions.filter(d => d.status === 'implemented').length}
          </p>
        </div>
        
        <div className="bg-purple-500/10 backdrop-blur-sm rounded-lg border border-purple-500/20 p-4">
          <div className="flex items-center space-x-2 mb-2">
            <DollarSign className="w-5 h-5 text-purple-400" />
            <span className="text-purple-400 font-medium">Total Value</span>
          </div>
          <p className="text-2xl font-bold text-white">
            {formatCurrency(decisions.reduce((sum, d) => sum + d.estimatedValue, 0))}
          </p>
        </div>
      </div>

      {/* Decision List */}
      <div className="space-y-4">
        {decisions.length === 0 ? (
          <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-8 text-center">
            <Brain className="w-12 h-12 text-blue-400 mx-auto mb-3" />
            <h3 className="text-lg font-medium text-white mb-1">No Decisions Pending</h3>
            <p className="text-gray-300">AI agents are monitoring for optimization opportunities</p>
          </div>
        ) : (
          decisions.map((decision) => (
            <div
              key={decision.id}
              className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6 hover:bg-white/10 transition-all"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-4">
                  <div className={`p-3 rounded-lg ${getCategoryColor(decision.category)}`}>
                    {getCategoryIcon(decision.category)}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">{decision.title}</h3>
                    <div className="flex items-center space-x-4 mt-1">
                      <div className="flex items-center space-x-1 text-blue-300">
                        <Brain className="w-4 h-4" />
                        <span className="text-sm">{decision.agent}</span>
                      </div>
                      <div className="flex items-center space-x-1 text-gray-300">
                        <Clock className="w-4 h-4" />
                        <span className="text-sm">{formatTimeAgo(decision.timestamp)}</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  <div className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(decision.status)}`}>
                    {decision.status.toUpperCase()}
                  </div>
                  {getStatusIcon(decision.status)}
                </div>
              </div>
              
              <p className="text-gray-300 mb-4">{decision.description}</p>
              
              <div className="bg-white/5 rounded-lg p-4 mb-4">
                <h4 className="text-sm font-medium text-white mb-2">Recommended Action:</h4>
                <p className="text-blue-300">{decision.action}</p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="bg-white/5 rounded-lg p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-300">Confidence</span>
                    <span className="text-sm font-medium text-white">{decision.confidence}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2 mt-1">
                    <div 
                      className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${decision.confidence}%` }}
                    ></div>
                  </div>
                </div>
                
                <div className="bg-white/5 rounded-lg p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-300">Est. Value</span>
                    <span className="text-sm font-medium text-green-400">{formatCurrency(decision.estimatedValue)}</span>
                  </div>
                </div>
                
                <div className="bg-white/5 rounded-lg p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-300">Risk Level</span>
                    <span className={`text-sm font-medium ${getRiskColor(decision.riskLevel)}`}>
                      {decision.riskLevel.toUpperCase()}
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="mb-4">
                <h4 className="text-sm font-medium text-white mb-2">Expected Impact:</h4>
                <p className="text-green-400 text-sm">{decision.impact}</p>
              </div>
              
              <div className="mb-4">
                <h4 className="text-sm font-medium text-white mb-2">AI Reasoning:</h4>
                <p className="text-gray-300 text-sm">{decision.reasoning}</p>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Zap className="w-4 h-4 text-yellow-400" />
                  <span className="text-sm text-yellow-400 font-medium">Human-in-the-Loop Governance</span>
                </div>
                
                <div className="flex space-x-2">
                  {decision.status === 'pending' && (
                    <>
                      <button onClick={() => submitReview(decision.id, true)} disabled={acting === decision.id} className="flex items-center space-x-1 px-3 py-1 disabled:opacity-50 bg-green-500/20 text-green-300 rounded-lg text-sm hover:bg-green-500/30 transition-colors">
                        <ThumbsUp className="w-4 h-4" />
                        <span>Approve</span>
                      </button>
                      <button onClick={() => submitReview(decision.id, false)} disabled={acting === decision.id} className="flex items-center space-x-1 px-3 py-1 disabled:opacity-50 bg-red-500/20 text-red-300 rounded-lg text-sm hover:bg-red-500/30 transition-colors">
                        <ThumbsDown className="w-4 h-4" />
                        <span>Reject</span>
                      </button>
                      <button disabled title="Not available yet" className="flex items-center space-x-1 px-3 py-1 opacity-40 cursor-not-allowed bg-blue-500/20 text-blue-300 rounded-lg text-sm hover:bg-blue-500/30 transition-colors">
                        <MessageSquare className="w-4 h-4" />
                        <span>Discuss</span>
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Decision Intelligence Info */}
      <div className="bg-gradient-to-r from-green-500/10 to-blue-500/10 rounded-xl border border-green-500/20 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white">Decision Intelligence System</h3>
          <div className="flex items-center space-x-2">
            <Shield className="w-5 h-5 text-green-400" />
            <span className="text-green-400 text-sm font-medium">Human Oversight Active</span>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
              <Brain className="w-6 h-6 text-blue-400" />
            </div>
            <p className="text-white font-semibold">AI Proposes</p>
            <p className="text-blue-400 text-sm">Data-driven recommendations</p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
              <Eye className="w-6 h-6 text-green-400" />
            </div>
            <p className="text-white font-semibold">Humans Review</p>
            <p className="text-green-400 text-sm">Expert validation & approval</p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
              <Target className="w-6 h-6 text-purple-400" />
            </div>
            <p className="text-white font-semibold">System Executes</p>
            <p className="text-purple-400 text-sm">Automated implementation</p>
          </div>
        </div>
      </div>
    </div>
  );
}