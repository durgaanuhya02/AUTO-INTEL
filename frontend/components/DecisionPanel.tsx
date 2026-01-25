'use client';

import { useState, useEffect } from 'react';
import { 
  Target, Brain, CheckCircle, Clock, AlertTriangle, 
  TrendingUp, DollarSign, Users, Zap, ThumbsUp, ThumbsDown,
  Eye, Shield, MessageSquare
} from 'lucide-react';

interface Decision {
  id: string;
  title: string;
  description: string;
  action: string;
  confidence: number;
  impact: string;
  reasoning: string;
  status: 'pending' | 'approved' | 'rejected' | 'implemented';
  timestamp: string;
  agent: string;
  category: 'pricing' | 'inventory' | 'marketing' | 'operations';
  estimatedValue: number;
  riskLevel: 'low' | 'medium' | 'high';
}

export default function DecisionPanel() {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDecisions();
    const interval = setInterval(fetchDecisions, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDecisions = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/v1/decisions');
      if (response.ok) {
        const data = await response.json();
        setDecisions(data.decisions || []);
      } else {
        // Mock decisions for demo
        setDecisions([
          {
            id: '1',
            title: 'Dynamic Pricing Adjustment',
            description: 'Implement 8% price increase for high-demand electronics category',
            action: 'Increase prices for electronics by 8% during peak hours (6-9 PM)',
            confidence: 92.3,
            impact: 'Revenue increase of $12,000-15,000 per week',
            reasoning: 'ML analysis shows 85% price elasticity tolerance in electronics. Historical data indicates 8% increase yields optimal revenue without significant demand drop.',
            status: 'pending',
            timestamp: new Date(Date.now() - 1800000).toISOString(),
            agent: 'Price Optimization Agent',
            category: 'pricing',
            estimatedValue: 13500,
            riskLevel: 'low'
          },
          {
            id: '2',
            title: 'Customer Retention Campaign',
            description: 'Launch targeted retention campaign for at-risk customers',
            action: 'Send personalized 15% discount offers to 2,847 at-risk customers',
            confidence: 87.6,
            impact: 'Prevent 60-70% customer churn, retain $45K monthly revenue',
            reasoning: 'Churn prediction model identifies customers with 78% likelihood to leave. Similar campaigns showed 68% retention success rate.',
            status: 'approved',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            agent: 'Customer Analytics Agent',
            category: 'marketing',
            estimatedValue: 45000,
            riskLevel: 'medium'
          },
          {
            id: '3',
            title: 'Inventory Rebalancing',
            description: 'Redistribute slow-moving inventory across regions',
            action: 'Transfer 1,200 units from São Paulo to Rio de Janeiro warehouses',
            confidence: 94.1,
            impact: 'Reduce storage costs by $8,000/month, improve availability',
            reasoning: 'Demand forecasting shows 40% higher demand in Rio region. Current São Paulo inventory has 120-day turnover vs 45-day optimal.',
            status: 'implemented',
            timestamp: new Date(Date.now() - 7200000).toISOString(),
            agent: 'Supply Chain Agent',
            category: 'operations',
            estimatedValue: 8000,
            riskLevel: 'low'
          },
          {
            id: '4',
            title: 'Marketing Budget Reallocation',
            description: 'Shift budget from low-performing channels to high-ROI channels',
            action: 'Move $25K from traditional ads to social media and influencer marketing',
            confidence: 89.4,
            impact: 'Increase customer acquisition by 35%, improve ROI from 2.1x to 3.4x',
            reasoning: 'Attribution analysis shows social media generates 3.4x ROI vs 1.8x for traditional channels. Target demographic (25-40) shows 67% higher engagement on social platforms.',
            status: 'rejected',
            timestamp: new Date(Date.now() - 10800000).toISOString(),
            agent: 'Marketing Intelligence Agent',
            category: 'marketing',
            estimatedValue: 25000,
            riskLevel: 'medium'
          }
        ]);
      }
    } catch (error) {
      console.error('Error fetching decisions:', error);
      // Mock data on error
      setDecisions([
        {
          id: '1',
          title: 'AI-Recommended Action Available',
          description: 'System has identified optimization opportunities',
          action: 'Review AI recommendations for business improvements',
          confidence: 85.0,
          impact: 'Potential business optimization',
          reasoning: 'Multiple improvement opportunities detected',
          status: 'pending',
          timestamp: new Date().toISOString(),
          agent: 'Decision Engine',
          category: 'operations',
          estimatedValue: 0,
          riskLevel: 'low'
        }
      ]);
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
                      <button className="flex items-center space-x-1 px-3 py-1 bg-green-500/20 text-green-300 rounded-lg text-sm hover:bg-green-500/30 transition-colors">
                        <ThumbsUp className="w-4 h-4" />
                        <span>Approve</span>
                      </button>
                      <button className="flex items-center space-x-1 px-3 py-1 bg-red-500/20 text-red-300 rounded-lg text-sm hover:bg-red-500/30 transition-colors">
                        <ThumbsDown className="w-4 h-4" />
                        <span>Reject</span>
                      </button>
                      <button className="flex items-center space-x-1 px-3 py-1 bg-blue-500/20 text-blue-300 rounded-lg text-sm hover:bg-blue-500/30 transition-colors">
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