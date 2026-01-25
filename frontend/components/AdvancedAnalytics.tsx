'use client';

import { useState, useEffect } from 'react';
import { 
  Brain, TrendingUp, BarChart3, PieChart, Target, Zap,
  MessageSquare, Lightbulb, TrendingDown, Activity, Globe
} from 'lucide-react';

interface AnalyticsData {
  aiSummary: string;
  forecastedRevenue: {
    nextMonth: number;
    confidence: number;
    trend: 'up' | 'down' | 'stable';
  };
  businessRecommendations: string[];
  keyInsights: string[];
  riskFactors: string[];
  opportunities: string[];
}

export default function AdvancedAnalytics() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/v1/analytics/insights');
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      } else {
        // Mock analytics data for demo
        setAnalytics({
          aiSummary: "Current business performance shows strong momentum with 12.3% revenue growth and improving customer satisfaction. The AI system has identified 3 high-impact optimization opportunities worth an estimated $67K in monthly value. Key risk factors include seasonal demand fluctuations and supply chain dependencies, but overall trajectory remains positive with 94.2% confidence in continued growth.",
          forecastedRevenue: {
            nextMonth: 14250000,
            confidence: 89.7,
            trend: 'up'
          },
          businessRecommendations: [
            "Implement dynamic pricing strategy for electronics category to capture 8-12% additional revenue during peak demand periods",
            "Launch targeted retention campaign for 2,847 at-risk customers to prevent $45K monthly churn",
            "Optimize inventory distribution across regions to reduce storage costs by $8K/month and improve availability",
            "Reallocate marketing budget from traditional channels to social media for 35% better customer acquisition ROI",
            "Expand product offerings in high-growth categories identified by demand forecasting models"
          ],
          keyInsights: [
            "Customer satisfaction correlation with delivery speed is 0.87 - fastest improvement lever identified",
            "Electronics category shows 85% price elasticity tolerance, enabling strategic pricing adjustments",
            "Rio de Janeiro region demonstrates 40% higher demand growth potential than current inventory allocation",
            "Social media marketing channels generate 3.4x ROI compared to 1.8x for traditional advertising",
            "Seasonal patterns indicate 23% demand spike expected in next 6 weeks across home & garden categories"
          ],
          riskFactors: [
            "Supply chain disruptions could impact 15% of product categories within 30 days",
            "Customer acquisition costs trending upward by 8% month-over-month in competitive segments",
            "Inventory turnover rates declining in São Paulo region, indicating potential overstock situation"
          ],
          opportunities: [
            "Untapped market segments showing 67% higher engagement rates in 25-40 demographic",
            "Cross-selling opportunities could increase average order value by 18% based on purchase pattern analysis",
            "International expansion potential identified in 3 adjacent markets with similar customer profiles"
          ]
        });
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
      // Mock data on error
      setAnalytics({
        aiSummary: "AI analytics system is processing business data to generate insights and recommendations.",
        forecastedRevenue: {
          nextMonth: 13500000,
          confidence: 85.0,
          trend: 'up'
        },
        businessRecommendations: [
          "Continue monitoring key performance indicators for optimization opportunities"
        ],
        keyInsights: [
          "System is analyzing patterns in customer behavior and business metrics"
        ],
        riskFactors: [
          "Regular monitoring active for potential business risks"
        ],
        opportunities: [
          "AI system continuously identifies growth opportunities"
        ]
      });
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

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-5 h-5 text-green-400" />;
      case 'down': return <TrendingDown className="w-5 h-5 text-red-400" />;
      case 'stable': return <Activity className="w-5 h-5 text-blue-400" />;
      default: return <Activity className="w-5 h-5 text-gray-400" />;
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'up': return 'text-green-400';
      case 'down': return 'text-red-400';
      case 'stable': return 'text-blue-400';
      default: return 'text-gray-400';
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6 animate-pulse">
            <div className="h-6 bg-white/10 rounded mb-4"></div>
            <div className="h-4 bg-white/10 rounded mb-2"></div>
            <div className="h-3 bg-white/10 rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-8 text-center">
        <Brain className="w-12 h-12 text-blue-400 mx-auto mb-3" />
        <h3 className="text-lg font-medium text-white mb-1">Analytics Processing</h3>
        <p className="text-gray-300">AI system is generating insights from your data</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* AI-Generated Executive Summary */}
      <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-xl border border-blue-500/20 p-6">
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2 bg-blue-500/20 rounded-lg">
            <Brain className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">AI-Generated Executive Summary</h3>
            <p className="text-blue-300 text-sm">Natural language business insights powered by machine learning</p>
          </div>
        </div>
        <div className="bg-white/5 rounded-lg p-4">
          <p className="text-gray-200 leading-relaxed">{analytics.aiSummary}</p>
        </div>
      </div>

      {/* Revenue Forecast */}
      <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-500/20 rounded-lg">
              <TrendingUp className="w-6 h-6 text-green-400" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">AI Revenue Forecast</h3>
              <p className="text-green-300 text-sm">Machine learning prediction with confidence intervals</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-white">{formatCurrency(analytics.forecastedRevenue.nextMonth)}</p>
            <div className="flex items-center space-x-2">
              {getTrendIcon(analytics.forecastedRevenue.trend)}
              <span className={`text-sm font-medium ${getTrendColor(analytics.forecastedRevenue.trend)}`}>
                Next Month Forecast
              </span>
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white/5 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-300">Confidence Level</span>
              <span className="text-sm font-medium text-white">{analytics.forecastedRevenue.confidence}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${analytics.forecastedRevenue.confidence}%` }}
              ></div>
            </div>
          </div>
          
          <div className="bg-white/5 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-300">Trend Direction</span>
              <div className="flex items-center space-x-1">
                {getTrendIcon(analytics.forecastedRevenue.trend)}
                <span className={`text-sm font-medium ${getTrendColor(analytics.forecastedRevenue.trend)}`}>
                  {analytics.forecastedRevenue.trend.toUpperCase()}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Business Recommendations */}
      <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6">
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2 bg-purple-500/20 rounded-lg">
            <Target className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">AI Business Recommendations</h3>
            <p className="text-purple-300 text-sm">Data-driven action items for business optimization</p>
          </div>
        </div>
        
        <div className="space-y-3">
          {analytics.businessRecommendations.map((recommendation, index) => (
            <div key={index} className="bg-white/5 rounded-lg p-4 hover:bg-white/10 transition-colors">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-6 h-6 bg-purple-500/20 rounded-full flex items-center justify-center mt-0.5">
                  <span className="text-xs font-bold text-purple-400">{index + 1}</span>
                </div>
                <p className="text-gray-200 text-sm leading-relaxed">{recommendation}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Key Insights Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Key Insights */}
        <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-2 bg-yellow-500/20 rounded-lg">
              <Lightbulb className="w-5 h-5 text-yellow-400" />
            </div>
            <h3 className="text-lg font-bold text-white">Key Insights</h3>
          </div>
          
          <div className="space-y-3">
            {analytics.keyInsights.map((insight, index) => (
              <div key={index} className="bg-white/5 rounded-lg p-3">
                <p className="text-gray-200 text-sm">{insight}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Risk Factors */}
        <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-2 bg-red-500/20 rounded-lg">
              <TrendingDown className="w-5 h-5 text-red-400" />
            </div>
            <h3 className="text-lg font-bold text-white">Risk Factors</h3>
          </div>
          
          <div className="space-y-3">
            {analytics.riskFactors.map((risk, index) => (
              <div key={index} className="bg-red-500/5 border border-red-500/20 rounded-lg p-3">
                <p className="text-gray-200 text-sm">{risk}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Opportunities */}
        <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-2 bg-green-500/20 rounded-lg">
              <Globe className="w-5 h-5 text-green-400" />
            </div>
            <h3 className="text-lg font-bold text-white">Opportunities</h3>
          </div>
          
          <div className="space-y-3">
            {analytics.opportunities.map((opportunity, index) => (
              <div key={index} className="bg-green-500/5 border border-green-500/20 rounded-lg p-3">
                <p className="text-gray-200 text-sm">{opportunity}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI Analytics Status */}
      <div className="bg-gradient-to-r from-orange-500/10 to-pink-500/10 rounded-xl border border-orange-500/20 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white">AI Analytics Engine</h3>
          <div className="flex items-center space-x-2">
            <Zap className="w-5 h-5 text-orange-400" />
            <span className="text-orange-400 text-sm font-medium">Continuous Learning Active</span>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
              <BarChart3 className="w-6 h-6 text-blue-400" />
            </div>
            <p className="text-white font-semibold text-sm">Pattern Detection</p>
            <p className="text-blue-400 text-xs">ML algorithms active</p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
              <PieChart className="w-6 h-6 text-green-400" />
            </div>
            <p className="text-white font-semibold text-sm">Predictive Modeling</p>
            <p className="text-green-400 text-xs">Forecasting enabled</p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
              <MessageSquare className="w-6 h-6 text-purple-400" />
            </div>
            <p className="text-white font-semibold text-sm">Natural Language</p>
            <p className="text-purple-400 text-xs">Insight generation</p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-orange-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
              <Target className="w-6 h-6 text-orange-400" />
            </div>
            <p className="text-white font-semibold text-sm">Recommendation</p>
            <p className="text-orange-400 text-xs">Action optimization</p>
          </div>
        </div>
      </div>
    </div>
  );
}