'use client';

import { useState, useEffect } from 'react';
import { 
  TrendingUp, Brain, BarChart3, Calendar, Target, ArrowUpRight, 
  ArrowDownRight, RefreshCw, Download, AlertCircle, CheckCircle
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart, ComposedChart } from 'recharts';

interface ForecastData {
  metric: string;
  model_type: string;
  current_value: number;
  predicted_values: number[];
  dates: string[];
  confidence_lower: number[];
  confidence_upper: number[];
  trend_direction: string;
  seasonality_strength: number;
  model_accuracy: number;
  feature_importance: Record<string, number>;
}

interface ForecastSummary {
  revenue_forecast: {
    current: number;
    predicted_30d: number;
    trend: string;
    confidence: number;
    model: string;
  } | null;
  orders_forecast: {
    current: number;
    predicted_30d: number;
    trend: string;
    confidence: number;
    model: string;
  } | null;
  generated_at: string;
  forecast_horizon: number;
}

export default function AdvancedForecasting() {
  const [forecastSummary, setForecastSummary] = useState<ForecastSummary | null>(null);
  const [selectedForecast, setSelectedForecast] = useState<ForecastData | null>(null);
  const [selectedMetric, setSelectedMetric] = useState('revenue');
  const [forecastDays, setForecastDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchForecastSummary();
    fetchDetailedForecast(selectedMetric);
    const interval = setInterval(() => {
      fetchForecastSummary();
      fetchDetailedForecast(selectedMetric);
    }, 60000); // Update every minute
    return () => clearInterval(interval);
  }, [selectedMetric]);

  const fetchForecastSummary = async () => {
    try {
      setError(null);
      const response = await fetch('http://localhost:8001/api/v1/analytics/forecasts/advanced');
      if (response.ok) {
        const data = await response.json();
        setForecastSummary(data.forecasts);
        setLastUpdate(new Date().toLocaleTimeString());
      } else {
        throw new Error(`API returned ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error fetching forecast summary:', error);
      setError(`Failed to load forecast summary: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const fetchDetailedForecast = async (metric: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(
        `http://localhost:8001/api/v1/analytics/forecasts/advanced/${metric}?forecast_days=${forecastDays}`
      );
      if (response.ok) {
        const data = await response.json();
        setSelectedForecast(data.forecast);
      } else {
        throw new Error(`API returned ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error fetching detailed forecast:', error);
      setError(`Failed to load detailed forecast: ${error instanceof Error ? error.message : 'Unknown error'}`);
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

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('en-US').format(Math.round(value));
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing':
        return <ArrowUpRight className="w-5 h-5 text-green-500" />;
      case 'decreasing':
        return <ArrowDownRight className="w-5 h-5 text-red-500" />;
      default:
        return <Target className="w-5 h-5 text-gray-500" />;
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'increasing':
        return 'text-green-600 bg-green-50';
      case 'decreasing':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const prepareChartData = () => {
    if (!selectedForecast) return [];
    
    return selectedForecast.dates.map((date, index) => ({
      date: new Date(date).toLocaleDateString(),
      predicted: selectedForecast.predicted_values[index],
      lower: selectedForecast.confidence_lower[index],
      upper: selectedForecast.confidence_upper[index],
    }));
  };

  if (loading && !forecastSummary) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            <div className="h-4 bg-gray-200 rounded w-4/6"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-700 font-medium">Error</span>
          </div>
          <p className="text-red-600 mt-2">{error}</p>
          <button
            onClick={() => {
              setError(null);
              fetchForecastSummary();
              fetchDetailedForecast(selectedMetric);
            }}
            className="mt-3 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm"
          >
            Retry
          </button>
        </div>
      )}

      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <TrendingUp className="w-8 h-8" />
            <div>
              <h2 className="text-2xl font-bold">Advanced Forecasting</h2>
              <p className="text-purple-100">AI-powered predictions with confidence intervals</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-purple-100">Last Updated</div>
            <div className="font-semibold">{lastUpdate}</div>
          </div>
        </div>
      </div>

      {/* Forecast Summary Cards */}
      {forecastSummary && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Revenue Forecast */}
          {forecastSummary.revenue_forecast && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <Brain className="w-6 h-6 text-green-600" />
                  <h3 className="text-lg font-semibold">Revenue Forecast</h3>
                </div>
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${getTrendColor(forecastSummary.revenue_forecast.trend)}`}>
                  {getTrendIcon(forecastSummary.revenue_forecast.trend)}
                  <span className="ml-1 capitalize">{forecastSummary.revenue_forecast.trend}</span>
                </div>
              </div>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Current</span>
                  <span className="font-bold text-lg">{formatCurrency(forecastSummary.revenue_forecast.current)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">30-Day Prediction</span>
                  <span className="font-bold text-lg text-blue-600">{formatCurrency(forecastSummary.revenue_forecast.predicted_30d)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Model Confidence</span>
                  <span className="font-semibold">{(forecastSummary.revenue_forecast.confidence * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Model Type</span>
                  <span className="font-semibold capitalize">{forecastSummary.revenue_forecast.model}</span>
                </div>
              </div>
            </div>
          )}

          {/* Orders Forecast */}
          {forecastSummary.orders_forecast && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <BarChart3 className="w-6 h-6 text-blue-600" />
                  <h3 className="text-lg font-semibold">Orders Forecast</h3>
                </div>
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${getTrendColor(forecastSummary.orders_forecast.trend)}`}>
                  {getTrendIcon(forecastSummary.orders_forecast.trend)}
                  <span className="ml-1 capitalize">{forecastSummary.orders_forecast.trend}</span>
                </div>
              </div>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Current</span>
                  <span className="font-bold text-lg">{formatNumber(forecastSummary.orders_forecast.current)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">30-Day Prediction</span>
                  <span className="font-bold text-lg text-blue-600">{formatNumber(forecastSummary.orders_forecast.predicted_30d)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Model Confidence</span>
                  <span className="font-semibold">{(forecastSummary.orders_forecast.confidence * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Model Type</span>
                  <span className="font-semibold capitalize">{forecastSummary.orders_forecast.model}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Detailed Forecast Controls */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-semibold">Detailed Forecast Analysis</h3>
          <div className="flex items-center space-x-4">
            <select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="revenue">Revenue</option>
              <option value="orders">Orders</option>
              <option value="customers">Customers</option>
            </select>
            <select
              value={forecastDays}
              onChange={(e) => setForecastDays(Number(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={7}>7 Days</option>
              <option value={14}>14 Days</option>
              <option value={30}>30 Days</option>
              <option value={60}>60 Days</option>
              <option value={90}>90 Days</option>
            </select>
            <button
              onClick={() => fetchDetailedForecast(selectedMetric)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center space-x-2"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Forecast Chart */}
        {selectedForecast && (
          <div className="space-y-6">
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={prepareChartData()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value, name) => [
                      selectedMetric === 'revenue' ? formatCurrency(Number(value)) : formatNumber(Number(value)),
                      name
                    ]}
                  />
                  <Area
                    type="monotone"
                    dataKey="upper"
                    stackId="1"
                    stroke="none"
                    fill="#dbeafe"
                    fillOpacity={0.6}
                  />
                  <Area
                    type="monotone"
                    dataKey="lower"
                    stackId="1"
                    stroke="none"
                    fill="#ffffff"
                    fillOpacity={1}
                  />
                  <Line
                    type="monotone"
                    dataKey="predicted"
                    stroke="#2563eb"
                    strokeWidth={3}
                    dot={{ fill: '#2563eb', strokeWidth: 2, r: 4 }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* Forecast Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-600">Current Value</div>
                <div className="text-xl font-bold">
                  {selectedMetric === 'revenue' 
                    ? formatCurrency(selectedForecast.current_value)
                    : formatNumber(selectedForecast.current_value)
                  }
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-600">Trend Direction</div>
                <div className="flex items-center space-x-2">
                  {getTrendIcon(selectedForecast.trend_direction)}
                  <span className="font-semibold capitalize">{selectedForecast.trend_direction}</span>
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-600">Model Accuracy</div>
                <div className="text-xl font-bold">{(selectedForecast.model_accuracy * 100).toFixed(1)}%</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-600">Seasonality</div>
                <div className="text-xl font-bold">{(selectedForecast.seasonality_strength * 100).toFixed(1)}%</div>
              </div>
            </div>
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Generating forecast...</span>
          </div>
        )}
      </div>
    </div>
  );
}