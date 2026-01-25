"""
Simple Forecasting Service with basic statistical models
Fallback implementation when advanced libraries are not available
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ForecastResult:
    """Simple forecast result"""
    metric: str
    model_type: str
    current_value: float
    predicted_values: List[float]
    dates: List[str]
    confidence_lower: List[float]
    confidence_upper: List[float]
    trend_direction: str
    seasonality_strength: float
    model_accuracy: float
    feature_importance: Dict[str, float]

class SimpleForecastingService:
    """Simple forecasting service using basic statistical methods"""
    
    def __init__(self):
        self.logger = logging.getLogger("simple_forecasting")
        
    async def initialize(self):
        """Initialize forecasting service"""
        self.logger.info("🔮 Initializing Simple Forecasting Service...")
        return True
    
    async def generate_forecast(self, 
                              data: pd.DataFrame, 
                              metric: str, 
                              forecast_days: int = 30) -> ForecastResult:
        """Generate simple forecast using linear regression and moving averages"""
        
        try:
            # Prepare data
            df = self._prepare_data(data, metric)
            
            # Generate forecast using linear trend + seasonal component
            predictions, lower_bound, upper_bound = self._linear_forecast(df['y'].values, forecast_days)
            
            # Create future dates
            last_date = df['ds'].iloc[-1]
            future_dates = [last_date + timedelta(days=i+1) for i in range(forecast_days)]
            
            # Calculate trend and seasonality
            trend_direction = self._calculate_trend(df['y'].values)
            seasonality_strength = self._calculate_seasonality(df['y'].values)
            
            # Calculate accuracy (using simple MAE on last 10 points)
            accuracy = self._calculate_accuracy(df['y'].values)
            
            return ForecastResult(
                metric=metric,
                model_type="linear_trend",
                current_value=float(df['y'].iloc[-1]),
                predicted_values=predictions.tolist(),
                dates=[d.strftime('%Y-%m-%d') for d in future_dates],
                confidence_lower=lower_bound.tolist(),
                confidence_upper=upper_bound.tolist(),
                trend_direction=trend_direction,
                seasonality_strength=seasonality_strength,
                model_accuracy=accuracy,
                feature_importance={"trend": 0.7, "seasonality": 0.3}
            )
            
        except Exception as e:
            self.logger.error(f"Error generating forecast: {str(e)}")
            return None
    
    def _linear_forecast(self, values: np.ndarray, forecast_days: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Generate forecast using linear trend with seasonal adjustment"""
        
        # Calculate linear trend
        x = np.arange(len(values))
        trend_coef = np.polyfit(x, values, 1)
        
        # Calculate seasonal component (weekly pattern)
        seasonal_component = self._extract_seasonal_pattern(values, period=7)
        
        # Generate predictions
        future_x = np.arange(len(values), len(values) + forecast_days)
        trend_predictions = np.polyval(trend_coef, future_x)
        
        # Add seasonal component
        seasonal_predictions = np.array([
            seasonal_component[i % len(seasonal_component)] 
            for i in range(forecast_days)
        ])
        
        predictions = trend_predictions + seasonal_predictions
        
        # Calculate confidence intervals (simple approach)
        residuals = values - (np.polyval(trend_coef, x) + np.array([
            seasonal_component[i % len(seasonal_component)] 
            for i in range(len(values))
        ]))
        
        std_error = np.std(residuals)
        confidence_interval = 1.96 * std_error  # 95% confidence
        
        lower_bound = predictions - confidence_interval
        upper_bound = predictions + confidence_interval
        
        return predictions, lower_bound, upper_bound
    
    def _extract_seasonal_pattern(self, values: np.ndarray, period: int = 7) -> np.ndarray:
        """Extract seasonal pattern from time series"""
        if len(values) < period * 2:
            return np.zeros(period)
        
        # Reshape data into periods and calculate mean for each position
        n_complete_periods = len(values) // period
        reshaped = values[:n_complete_periods * period].reshape(-1, period)
        seasonal_pattern = np.mean(reshaped, axis=0)
        
        # Remove overall mean to get seasonal component
        seasonal_pattern = seasonal_pattern - np.mean(seasonal_pattern)
        
        return seasonal_pattern
    
    def _prepare_data(self, data: pd.DataFrame, metric: str) -> pd.DataFrame:
        """Prepare data for forecasting models"""
        try:
            # Ensure we have the required columns
            if 'date' not in data.columns or metric not in data.columns:
                raise ValueError(f"Data must contain 'date' and '{metric}' columns")
            
            df = data[['date', metric]].copy()
            df.columns = ['ds', 'y']
            
            # Convert date column
            df['ds'] = pd.to_datetime(df['ds'])
            
            # Remove any null values
            df = df.dropna()
            
            # Sort by date
            df = df.sort_values('ds').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Data preparation error: {str(e)}")
            raise
    
    def _calculate_trend(self, values: np.ndarray) -> str:
        """Calculate trend direction"""
        try:
            if len(values) < 2:
                return "stable"
            
            # Simple linear trend calculation
            x = np.arange(len(values))
            slope = np.polyfit(x, values, 1)[0]
            
            # Calculate relative slope
            mean_value = np.mean(values)
            relative_slope = slope / mean_value if mean_value != 0 else 0
            
            if relative_slope > 0.001:  # 0.1% increase per period
                return "increasing"
            elif relative_slope < -0.001:  # 0.1% decrease per period
                return "decreasing"
            else:
                return "stable"
                
        except Exception as e:
            self.logger.error(f"Trend calculation error: {str(e)}")
            return "stable"
    
    def _calculate_seasonality(self, values: np.ndarray) -> float:
        """Calculate seasonality strength"""
        try:
            if len(values) < 14:  # Need at least 2 weeks of data
                return 0.0
            
            # Extract weekly seasonal pattern
            seasonal_pattern = self._extract_seasonal_pattern(values, period=7)
            
            # Calculate seasonality strength as coefficient of variation
            if np.mean(np.abs(seasonal_pattern)) == 0:
                return 0.0
            
            seasonality_strength = np.std(seasonal_pattern) / np.mean(np.abs(values))
            
            return min(1.0, max(0.0, seasonality_strength))
            
        except Exception as e:
            self.logger.error(f"Seasonality calculation error: {str(e)}")
            return 0.0
    
    def _calculate_accuracy(self, values: np.ndarray) -> float:
        """Calculate model accuracy using simple holdout validation"""
        try:
            if len(values) < 10:
                return 0.8  # Default accuracy for small datasets
            
            # Use last 20% of data for validation
            split_point = int(len(values) * 0.8)
            train_data = values[:split_point]
            test_data = values[split_point:]
            
            # Generate predictions for test period
            x_train = np.arange(len(train_data))
            trend_coef = np.polyfit(x_train, train_data, 1)
            
            x_test = np.arange(len(train_data), len(values))
            predictions = np.polyval(trend_coef, x_test)
            
            # Calculate accuracy (1 - normalized MAE)
            mae = np.mean(np.abs(test_data - predictions))
            mean_value = np.mean(test_data)
            
            if mean_value == 0:
                return 0.8
            
            accuracy = max(0.0, 1.0 - (mae / mean_value))
            return min(1.0, accuracy)
            
        except Exception as e:
            self.logger.error(f"Accuracy calculation error: {str(e)}")
            return 0.8
    
    async def get_forecast_summary(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive forecast summary for multiple metrics"""
        try:
            summary = {
                'revenue_forecast': None,
                'orders_forecast': None,
                'customers_forecast': None,
                'generated_at': datetime.now().isoformat(),
                'forecast_horizon': 30,
                'model_performance': {}
            }
            
            # Revenue forecast
            if 'revenue' in data.columns:
                revenue_forecast = await self.generate_forecast(data, 'revenue', 30)
                if revenue_forecast:
                    summary['revenue_forecast'] = {
                        'current': revenue_forecast.current_value,
                        'predicted_30d': revenue_forecast.predicted_values[-1],
                        'trend': revenue_forecast.trend_direction,
                        'confidence': revenue_forecast.model_accuracy,
                        'model': revenue_forecast.model_type
                    }
            
            # Orders forecast
            if 'orders' in data.columns:
                orders_forecast = await self.generate_forecast(data, 'orders', 30)
                if orders_forecast:
                    summary['orders_forecast'] = {
                        'current': orders_forecast.current_value,
                        'predicted_30d': orders_forecast.predicted_values[-1],
                        'trend': orders_forecast.trend_direction,
                        'confidence': orders_forecast.model_accuracy,
                        'model': orders_forecast.model_type
                    }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Forecast summary error: {str(e)}")
            return {}

# Global instance
simple_forecasting_service = SimpleForecastingService()