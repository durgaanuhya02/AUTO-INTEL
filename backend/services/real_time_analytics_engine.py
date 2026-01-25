"""
Real-Time Analytics Engine with ML-Powered Forecasting
Provides fast, ML-driven analytics for real-time dashboards
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json

from .ml_service import MLService

@dataclass
class AnalyticsResult:
    """Real-time analytics result"""
    metric_name: str
    current_value: float
    predicted_value: float
    confidence_score: float
    trend_direction: str
    anomaly_score: float
    forecast_7d: List[float]
    forecast_30d: List[float]
    last_updated: str

class RealTimeAnalyticsEngine:
    """ML-powered real-time analytics engine"""

    def __init__(self):
        self.logger = logging.getLogger("real_time_analytics")
        self.ml_service = MLService()
        self.cache = {}
        self.cache_ttl = 30  # 30 seconds for real-time

    async def initialize(self):
        """Initialize the analytics engine"""
        self.logger.info("⚡ Initializing Real-Time Analytics Engine...")

        # Initialize ML service
        success = await self.ml_service.initialize()
        if not success:
            self.logger.warning("ML service initialization failed - using fallback analytics")

        self.logger.info("✅ Real-Time Analytics Engine initialized")
        return True

    async def get_real_time_metrics(self, metric_names: List[str] = None) -> Dict[str, AnalyticsResult]:
        """Get real-time analytics for specified metrics"""
        if metric_names is None:
            metric_names = ['revenue', 'orders', 'customer_satisfaction', 'conversion_rate']

        results = {}

        for metric in metric_names:
            try:
                # Check cache first
                cache_key = f"metric_{metric}"
                if cache_key in self.cache:
                    cached_result, timestamp = self.cache[cache_key]
                    if (datetime.now() - timestamp).seconds < self.cache_ttl:
                        results[metric] = cached_result
                        continue

                # Generate real-time analytics
                result = await self._generate_metric_analytics(metric)

                # Cache result
                self.cache[cache_key] = (result, datetime.now())
                results[metric] = result

            except Exception as e:
                self.logger.error(f"Error generating analytics for {metric}: {e}")
                # Return basic result
                results[metric] = AnalyticsResult(
                    metric_name=metric,
                    current_value=0.0,
                    predicted_value=0.0,
                    confidence_score=0.0,
                    trend_direction="unknown",
                    anomaly_score=0.0,
                    forecast_7d=[],
                    forecast_30d=[],
                    last_updated=datetime.now().isoformat()
                )

        return results

    async def _generate_metric_analytics(self, metric: str) -> AnalyticsResult:
        """Generate ML-powered analytics for a specific metric"""
        try:
            # Get current value (from cache or database)
            current_value = await self._get_current_metric_value(metric)

            # Get ML-powered forecast
            forecast_7d_result = await self.ml_service.predict_revenue_forecast(days_ahead=7)
            forecast_30d_result = await self.ml_service.predict_revenue_forecast(days_ahead=30)

            forecast_7d = forecast_7d_result.prediction[:7] if forecast_7d_result.prediction else []
            forecast_30d = forecast_30d_result.prediction[:30] if forecast_30d_result.prediction else []

            # Calculate predicted value (next day)
            predicted_value = forecast_7d[0] if forecast_7d else current_value * 1.02

            # Calculate trend direction
            if len(forecast_7d) >= 7:
                trend = (forecast_7d[-1] - forecast_7d[0]) / forecast_7d[0]
                if trend > 0.05:
                    trend_direction = "increasing"
                elif trend < -0.05:
                    trend_direction = "decreasing"
                else:
                    trend_direction = "stable"
            else:
                trend_direction = "stable"

            # Calculate anomaly score (simplified)
            anomaly_score = await self._calculate_anomaly_score(metric, current_value)

            # Confidence score from ML model
            confidence_score = forecast_7d_result.confidence if forecast_7d_result else 0.7

            return AnalyticsResult(
                metric_name=metric,
                current_value=current_value,
                predicted_value=predicted_value,
                confidence_score=confidence_score,
                trend_direction=trend_direction,
                anomaly_score=anomaly_score,
                forecast_7d=forecast_7d,
                forecast_30d=forecast_30d,
                last_updated=datetime.now().isoformat()
            )

        except Exception as e:
            self.logger.error(f"Error in metric analytics generation: {e}")
            raise

    async def _get_current_metric_value(self, metric: str) -> float:
        """Get current value for a metric"""
        # In production, this would query the database/cache
        # For demo, return mock values
        mock_values = {
            'revenue': 125000.0,
            'orders': 450.0,
            'customer_satisfaction': 4.2,
            'conversion_rate': 0.035
        }

        return mock_values.get(metric, 100.0)

    async def _calculate_anomaly_score(self, metric: str, current_value: float) -> float:
        """Calculate anomaly score using statistical methods"""
        # Simplified anomaly detection
        # In production, this would use ML models

        # Get historical values (mock)
        historical_avg = await self._get_historical_average(metric)
        historical_std = await self._get_historical_std(metric)

        if historical_std > 0:
            z_score = abs(current_value - historical_avg) / historical_std
            # Convert z-score to 0-1 scale (higher = more anomalous)
            anomaly_score = min(z_score / 3.0, 1.0)
        else:
            anomaly_score = 0.0

        return anomaly_score

    async def _get_historical_average(self, metric: str) -> float:
        """Get historical average for metric"""
        # Mock values
        averages = {
            'revenue': 120000.0,
            'orders': 420.0,
            'customer_satisfaction': 4.1,
            'conversion_rate': 0.032
        }
        return averages.get(metric, 100.0)

    async def _get_historical_std(self, metric: str) -> float:
        """Get historical standard deviation for metric"""
        # Mock values
        stds = {
            'revenue': 15000.0,
            'orders': 50.0,
            'customer_satisfaction': 0.3,
            'conversion_rate': 0.005
        }
        return stds.get(metric, 10.0)

    async def get_customer_insights(self) -> Dict[str, Any]:
        """Get ML-powered customer insights"""
        try:
            # Get customer segmentation
            customer_data = await self._get_customer_data()
            if not customer_data.empty:
                segmentation_result = await self.ml_service.predict_customer_segments(customer_data)

                # Get behavior predictions
                behavior_result = await self.ml_service.predict_customer_behavior(customer_data)

                return {
                    "segmentation": {
                        "segments": segmentation_result.prediction,
                        "segment_names": ["High-Value", "Regular", "Occasional", "At-Risk"],
                        "confidence": segmentation_result.confidence
                    },
                    "behavior_predictions": {
                        "churn_probabilities": behavior_result.prediction,
                        "confidence": behavior_result.confidence
                    },
                    "total_customers": len(customer_data),
                    "last_updated": datetime.now().isoformat()
                }
            else:
                return {"error": "No customer data available"}

        except Exception as e:
            self.logger.error(f"Error getting customer insights: {e}")
            return {"error": str(e)}

    async def _get_customer_data(self) -> pd.DataFrame:
        """Get customer data for analysis"""
        # In production, query database
        # Mock data for demo
        return pd.DataFrame({
            'total_orders': [15, 8, 3, 25, 12, 1],
            'total_spent': [2500, 1200, 300, 5000, 1800, 150],
            'avg_order_value': [167, 150, 100, 200, 150, 150],
            'days_since_last_order': [2, 7, 45, 1, 14, 90],
            'satisfaction_score': [4.5, 4.2, 3.8, 4.8, 4.0, 2.5]
        })

    async def get_price_optimization_recommendations(self) -> Dict[str, Any]:
        """Get ML-powered price optimization recommendations"""
        try:
            # Get product data
            product_data = await self._get_product_data()

            if not product_data.empty:
                optimization_result = await self.ml_service.predict_optimal_prices(product_data)

                recommendations = []
                for i, (idx, product) in enumerate(product_data.iterrows()):
                    if i < len(optimization_result.prediction):
                        optimal_price = optimization_result.prediction[i]
                        current_price = product['current_price']
                        change_percent = ((optimal_price - current_price) / current_price) * 100

                        recommendations.append({
                            "product_id": product.get('product_id', f"prod_{i}"),
                            "current_price": current_price,
                            "optimal_price": optimal_price,
                            "price_change_percent": change_percent,
                            "expected_impact": "revenue_increase" if change_percent > 0 else "volume_increase"
                        })

                return {
                    "recommendations": recommendations,
                    "confidence": optimization_result.confidence,
                    "total_products": len(product_data),
                    "last_updated": datetime.now().isoformat()
                }
            else:
                return {"error": "No product data available"}

        except Exception as e:
            self.logger.error(f"Error getting price recommendations: {e}")
            return {"error": str(e)}

    async def _get_product_data(self) -> pd.DataFrame:
        """Get product data for price optimization"""
        # Mock data
        return pd.DataFrame({
            'product_id': ['P001', 'P002', 'P003', 'P004', 'P005'],
            'current_price': [99.99, 149.99, 79.99, 199.99, 49.99],
            'competitor_price': [95.00, 155.00, 75.00, 189.99, 45.00],
            'demand_index': [1.2, 0.8, 1.5, 0.9, 1.8],
            'category_popularity': [0.8, 0.6, 0.9, 0.7, 0.85],
            'seasonal_factor': [1.0, 1.1, 0.9, 1.0, 1.2],
            'inventory_level': [0.7, 0.5, 0.8, 0.6, 0.9]
        })

    async def clear_cache(self):
        """Clear analytics cache"""
        self.cache.clear()
        self.logger.info("Analytics cache cleared")

    async def get_engine_status(self) -> Dict[str, Any]:
        """Get engine status and health"""
        ml_status = await self.ml_service.get_model_status()

        return {
            "status": "healthy",
            "cache_size": len(self.cache),
            "ml_models_available": ml_status.get("model_availability", {}),
            "last_cache_cleanup": datetime.now().isoformat(),
            "uptime": "active"
        }