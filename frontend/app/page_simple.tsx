'use client';

import { useState, useEffect } from 'react';

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/dashboard');
        const result = await response.json();
        setData(result);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Agentic AI Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-blue-600 rounded"></div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  Agentic AI Business Decision System
                </h1>
                <p className="text-sm text-gray-500">
                  Demo Mode - Autonomous decision-making with human oversight
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Revenue</h3>
            <p className="text-2xl font-bold text-gray-900">
              ${data?.current_metrics?.revenue?.toLocaleString() || '0'}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Orders</h3>
            <p className="text-2xl font-bold text-gray-900">
              {data?.current_metrics?.orders?.toLocaleString() || '0'}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Customer Satisfaction</h3>
            <p className="text-2xl font-bold text-gray-900">
              {data?.current_metrics?.customer_satisfaction?.toFixed(1) || '0.0'}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Delivery Delay</h3>
            <p className="text-2xl font-bold text-gray-900">
              {data?.current_metrics?.delivery_delay?.toFixed(1) || '0.0'} days
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Churn Risk</h3>
            <p className="text-2xl font-bold text-gray-900">
              {((data?.current_metrics?.churn_risk || 0) * 100).toFixed(1)}%
            </p>
          </div>
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column */}
          <div className="lg:col-span-2 space-y-6">
            {/* Alerts */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Active Alerts</h2>
              <div className="space-y-3">
                {data?.alerts?.map((alert: any, index: number) => (
                  <div key={index} className="p-4 rounded-lg border-l-4 border-yellow-500 bg-yellow-50">
                    <h4 className="text-sm font-medium text-gray-900 mb-1">
                      {alert.title}
                    </h4>
                    <p className="text-sm text-gray-600">
                      {alert.description}
                    </p>
                  </div>
                )) || <p className="text-gray-500">No active alerts</p>}
              </div>
            </div>

            {/* AI Decisions */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">AI Decisions</h2>
              <div className="space-y-4">
                {data?.recent_decisions?.map((decision: any, index: number) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">{decision.title}</h4>
                    <p className="text-sm text-gray-600 mb-3">{decision.description}</p>
                    <div className="flex items-center justify-between">
                      <div className="flex space-x-4 text-sm">
                        <span>Confidence: {(decision.confidence_score * 100).toFixed(0)}%</span>
                        <span>Impact: ${Math.abs(decision.financial_impact).toLocaleString()}</span>
                      </div>
                      {decision.requires_approval && (
                        <div className="flex space-x-2">
                          <button className="px-3 py-1 bg-red-600 text-white text-sm rounded">
                            Reject
                          </button>
                          <button className="px-3 py-1 bg-green-600 text-white text-sm rounded">
                            Approve
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )) || <p className="text-gray-500">No recent decisions</p>}
              </div>
            </div>
          </div>

          {/* Right Column */}
          <div className="space-y-6">
            {/* Agent Status */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Agent Status</h2>
              <div className="space-y-3">
                {data?.agent_statuses?.map((agent: any, index: number) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <h4 className="font-medium text-gray-900">
                        {agent.agent_type.charAt(0).toUpperCase() + agent.agent_type.slice(1)} Agent
                      </h4>
                      <p className="text-sm text-gray-600">{agent.current_task || 'Idle'}</p>
                    </div>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      agent.status === 'active' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {agent.status}
                    </span>
                  </div>
                )) || <p className="text-gray-500">No agent data</p>}
              </div>
            </div>

            {/* System Health */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">System Health</h2>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Mode</span>
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                    Demo
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">AI Agents</span>
                  <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                    {data?.agent_statuses?.length || 0} Active
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Active Alerts</span>
                  <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                    {data?.alerts?.length || 0}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}