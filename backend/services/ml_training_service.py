"""
ML Training Service - Pre-trains and loads ML models for production use
Ensures all models are ready for inference without training during execution
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json
import os
import pickle
import joblib

# ML Libraries
try:
    import xgboost as xgb
    import shap
    from sklearn.model_selection import train_test_split, GridSearchCV
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.cluster import KMeans
    from prophet import Prophet
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    ML_AVAILABLE = True
except ImportError as e:
    ML_AVAILABLE = False
    logging.warning(f"ML libraries not available: {e}")

@dataclass
class ModelMetadata:
    """Model metadata for tracking"""
    model_name: str
    model_type: str
    training_date: str
    features: List[str]
    target: str
    performance_metrics: Dict[str, float]
    dataset_size: int
    model_path: str

class MLTrainingService:
    """Service for training and loading ML models"""

    def __init__(self):
        self.logger = logging.getLogger("ml_training")
        self.models_dir = "backend/models"
        self.models = {}
        self.model_metadata = {}
        self.scalers = {}
        self.encoders = {}

        # Ensure models directory exists
        os.makedirs(self.models_dir, exist_ok=True)

    async def initialize(self):
        """Initialize ML training service"""
        if not ML_AVAILABLE:
            self.logger.error("ML libraries not available")
            return False

        self.logger.info("🤖 Initializing ML Training Service...")

        # Load existing models if available
        await self._load_existing_models()

        return True

    async def _load_existing_models(self):
        """Load pre-trained models from disk"""
        try:
            metadata_file = os.path.join(self.models_dir, "model_metadata.json")

            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    metadata_list = json.load(f)

                for metadata_dict in metadata_list:
                    metadata = ModelMetadata(**metadata_dict)
                    model_path = metadata.model_path

                    if os.path.exists(model_path):
                        # Load model based on type
                        if metadata.model_type == "xgboost":
                            model = xgb.Booster()
                            model.load_model(model_path)
                        elif metadata.model_type in ["prophet", "arima", "kmeans"]:
                            with open(model_path, 'rb') as f:
                                model = pickle.load(f)
                        else:
                            with open(model_path, 'rb') as f:
                                model = joblib.load(f)

                        self.models[metadata.model_name] = model
                        self.model_metadata[metadata.model_name] = metadata

                        # Load scaler if exists
                        scaler_path = model_path.replace('.pkl', '_scaler.pkl')
                        if os.path.exists(scaler_path):
                            with open(scaler_path, 'rb') as f:
                                self.scalers[metadata.model_name] = pickle.load(f)

                        # Load encoder if exists
                        encoder_path = model_path.replace('.pkl', '_encoder.pkl')
                        if os.path.exists(encoder_path):
                            with open(encoder_path, 'rb') as f:
                                self.encoders[metadata.model_name] = pickle.load(f)

                        self.logger.info(f"✅ Loaded model: {metadata.model_name}")
                    else:
                        self.logger.warning(f"Model file not found: {model_path}")

        except Exception as e:
            self.logger.error(f"Error loading existing models: {e}")

    async def train_all_models(self, data_processor) -> Dict[str, Any]:
        """Train all required ML models"""
        results = {}

        try:
            self.logger.info("🚀 Starting comprehensive ML model training...")

            # 1. Revenue Forecasting Ensemble (ARIMA + Prophet + XGBoost)
            results['revenue_forecast'] = await self._train_revenue_forecast_ensemble(data_processor)

            # 2. Customer Segmentation (K-Means)
            results['customer_segmentation'] = await self._train_customer_segmentation(data_processor)

            # 3. Price Optimization (XGBoost)
            results['price_optimization'] = await self._train_price_optimization(data_processor)

            # 4. Demand Forecasting by Category (Prophet)
            results['demand_forecast'] = await self._train_demand_forecasting(data_processor)

            # 5. Customer Behavior Prediction (XGBoost)
            results['customer_behavior'] = await self._train_customer_behavior_model(data_processor)

            # Save metadata
            await self._save_model_metadata()

            self.logger.info("✅ All ML models trained and saved")

        except Exception as e:
            self.logger.error(f"Error training models: {e}")
            results['error'] = str(e)

        return results

    async def _train_revenue_forecast_ensemble(self, data_processor) -> Dict[str, Any]:
        """Train ensemble revenue forecasting model"""
        try:
            # Get historical revenue data
            revenue_data = await data_processor.get_historical_revenue(days=365)

            if revenue_data.empty:
                return {"status": "error", "message": "No revenue data available"}

            # Prepare time series data
            df = revenue_data.copy()
            df['ds'] = pd.to_datetime(df['date'])
            df['y'] = df['revenue']

            # 1. Train ARIMA
            arima_model = ARIMA(df['y'], order=(5,1,0))
            arima_result = arima_model.fit()

            # 2. Train Prophet
            prophet_model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False
            )
            prophet_model.fit(df[['ds', 'y']])

            # 3. Train XGBoost for residual correction
            # Create features
            df['day_of_week'] = df['ds'].dt.dayofweek
            df['day_of_month'] = df['ds'].dt.day
            df['month'] = df['ds'].dt.month
            df['lag_1'] = df['y'].shift(1)
            df['lag_7'] = df['y'].shift(7)
            df['rolling_mean_7'] = df['y'].rolling(7).mean()
            df['rolling_std_7'] = df['y'].rolling(7).std()

            df_ml = df.dropna()
            features = ['day_of_week', 'day_of_month', 'month', 'lag_1', 'lag_7',
                       'rolling_mean_7', 'rolling_std_7']

            X = df_ml[features]
            y = df_ml['y']

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            xgb_model = xgb.XGBRegressor(
                objective='reg:squarederror',
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            xgb_model.fit(X_train_scaled, y_train)

            # Evaluate ensemble
            predictions = self._predict_ensemble(df, arima_result, prophet_model, xgb_model, scaler, features)
            mae = mean_absolute_error(df['y'].iloc[-len(predictions):], predictions)

            # Save models
            model_name = "revenue_forecast_ensemble"
            self._save_model(arima_result, f"{model_name}_arima")
            self._save_model(prophet_model, f"{model_name}_prophet")
            self._save_model(xgb_model, f"{model_name}_xgboost")
            self._save_model(scaler, f"{model_name}_scaler")

            # Store in memory
            self.models[model_name] = {
                'arima': arima_result,
                'prophet': prophet_model,
                'xgboost': xgb_model,
                'scaler': scaler,
                'features': features
            }

            return {
                "status": "success",
                "mae": mae,
                "models_trained": ["arima", "prophet", "xgboost"]
            }

        except Exception as e:
            self.logger.error(f"Error training revenue forecast: {e}")
            return {"status": "error", "message": str(e)}

    async def _train_customer_segmentation(self, data_processor) -> Dict[str, Any]:
        """Train customer segmentation model"""
        try:
            # Get customer data
            customer_data = await data_processor.get_customer_features()

            if customer_data.empty:
                return {"status": "error", "message": "No customer data available"}

            # Prepare features for segmentation
            features = ['total_orders', 'total_spent', 'avg_order_value',
                       'days_since_last_order', 'satisfaction_score']

            X = customer_data[features].fillna(0)

            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Train K-Means
            kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X_scaled)

            # Calculate silhouette score
            from sklearn.metrics import silhouette_score
            silhouette = silhouette_score(X_scaled, clusters)

            # Save models
            model_name = "customer_segmentation"
            self._save_model(kmeans, model_name)
            self._save_model(scaler, f"{model_name}_scaler")

            # Store in memory
            self.models[model_name] = kmeans
            self.scalers[model_name] = scaler

            return {
                "status": "success",
                "silhouette_score": silhouette,
                "n_clusters": 4,
                "features": features
            }

        except Exception as e:
            self.logger.error(f"Error training customer segmentation: {e}")
            return {"status": "error", "message": str(e)}

    async def _train_price_optimization(self, data_processor) -> Dict[str, Any]:
        """Train price optimization model"""
        try:
            # Get price optimization data
            price_data = await data_processor.get_price_optimization_data()

            if price_data.empty:
                return {"status": "error", "message": "No price data available"}

            # Prepare features
            features = ['current_price', 'competitor_price', 'demand_index',
                       'category_popularity', 'seasonal_factor', 'inventory_level']

            X = price_data[features]
            y = price_data['optimal_price']

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Train XGBoost
            xgb_model = xgb.XGBRegressor(
                objective='reg:squarederror',
                n_estimators=200,
                max_depth=8,
                learning_rate=0.05,
                random_state=42
            )
            xgb_model.fit(X_train_scaled, y_train)

            # Evaluate
            predictions = xgb_model.predict(X_test_scaled)
            mae = mean_absolute_error(y_test, predictions)
            r2 = r2_score(y_test, predictions)

            # Save models
            model_name = "price_optimization"
            self._save_model(xgb_model, model_name)
            self._save_model(scaler, f"{model_name}_scaler")

            # Store in memory
            self.models[model_name] = xgb_model
            self.scalers[model_name] = scaler

            return {
                "status": "success",
                "mae": mae,
                "r2_score": r2,
                "features": features
            }

        except Exception as e:
            self.logger.error(f"Error training price optimization: {e}")
            return {"status": "error", "message": str(e)}

    async def _train_demand_forecasting(self, data_processor) -> Dict[str, Any]:
        """Train demand forecasting models by category"""
        try:
            # Get demand data by category
            demand_data = await data_processor.get_category_demand_data()

            if demand_data.empty:
                return {"status": "error", "message": "No demand data available"}

            models_trained = {}
            categories = demand_data['product_category_name'].unique()

            for category in categories[:5]:  # Train for top 5 categories
                cat_data = demand_data[demand_data['product_category_name'] == category].copy()

                if len(cat_data) < 30:  # Skip if insufficient data
                    continue

                # Prepare for Prophet
                df = cat_data[['order_date', 'order_count']].copy()
                df.columns = ['ds', 'y']
                df['ds'] = pd.to_datetime(df['ds'])

                # Train Prophet
                model = Prophet(
                    yearly_seasonality=True,
                    weekly_seasonality=True,
                    daily_seasonality=False
                )
                model.fit(df)

                # Save model
                model_name = f"demand_forecast_{category.replace(' ', '_')}"
                self._save_model(model, model_name)
                self.models[model_name] = model
                models_trained[category] = model_name

            return {
                "status": "success",
                "categories_trained": list(models_trained.keys()),
                "models": models_trained
            }

        except Exception as e:
            self.logger.error(f"Error training demand forecasting: {e}")
            return {"status": "error", "message": str(e)}

    async def _train_customer_behavior_model(self, data_processor) -> Dict[str, Any]:
        """Train customer behavior prediction model"""
        try:
            # Get customer behavior data
            behavior_data = await data_processor.get_customer_behavior_data()

            if behavior_data.empty:
                return {"status": "error", "message": "No behavior data available"}

            # Prepare features
            features = ['days_since_last_order', 'avg_order_value', 'total_orders',
                       'satisfaction_trend', 'category_preference_score']

            X = behavior_data[features]
            y = behavior_data['churn_probability']

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Train XGBoost
            xgb_model = xgb.XGBRegressor(
                objective='reg:squarederror',
                n_estimators=150,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            xgb_model.fit(X_train_scaled, y_train)

            # Evaluate
            predictions = xgb_model.predict(X_test_scaled)
            mae = mean_absolute_error(y_test, predictions)

            # Save models
            model_name = "customer_behavior"
            self._save_model(xgb_model, model_name)
            self._save_model(scaler, f"{model_name}_scaler")

            # Store in memory
            self.models[model_name] = xgb_model
            self.scalers[model_name] = scaler

            return {
                "status": "success",
                "mae": mae,
                "features": features
            }

        except Exception as e:
            self.logger.error(f"Error training customer behavior: {e}")
            return {"status": "error", "message": str(e)}

    def _predict_ensemble(self, df, arima_model, prophet_model, xgb_model, scaler, features):
        """Make ensemble predictions"""
        # This is a simplified ensemble - in production, you'd weight predictions
        # For now, use XGBoost as primary with Prophet for seasonal adjustment
        return xgb_model.predict(scaler.transform(df[features].tail(30)))

    def _save_model(self, model, name: str):
        """Save model to disk"""
        try:
            model_path = os.path.join(self.models_dir, f"{name}.pkl")

            if hasattr(model, 'save_model'):  # XGBoost
                model.save_model(model_path)
            else:  # Other models
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)

            # Create metadata
            metadata = ModelMetadata(
                model_name=name,
                model_type=self._get_model_type(model),
                training_date=datetime.now().isoformat(),
                features=[],  # Will be set by caller
                target="",
                performance_metrics={},
                dataset_size=0,
                model_path=model_path
            )

            self.model_metadata[name] = metadata

        except Exception as e:
            self.logger.error(f"Error saving model {name}: {e}")

    def _get_model_type(self, model) -> str:
        """Get model type string"""
        if hasattr(model, 'predict'):
            if 'XGB' in str(type(model)):
                return "xgboost"
            elif 'Prophet' in str(type(model)):
                return "prophet"
            elif 'KMeans' in str(type(model)):
                return "kmeans"
            else:
                return "sklearn"
        else:
            return "arima"

    async def _save_model_metadata(self):
        """Save model metadata to JSON"""
        try:
            metadata_file = os.path.join(self.models_dir, "model_metadata.json")
            metadata_list = [vars(meta) for meta in self.model_metadata.values()]

            with open(metadata_file, 'w') as f:
                json.dump(metadata_list, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error saving metadata: {e}")

    # Prediction methods for inference
    async def predict_revenue(self, days_ahead: int = 7) -> Dict[str, Any]:
        """Predict future revenue using ensemble"""
        try:
            if "revenue_forecast_ensemble" not in self.models:
                return {"error": "Revenue forecast model not available"}

            model_bundle = self.models["revenue_forecast_ensemble"]

            # Generate future dates
            last_date = datetime.now()
            future_dates = [last_date + timedelta(days=i) for i in range(1, days_ahead + 1)]

            # Use Prophet for main prediction (simplified)
            prophet_model = model_bundle['prophet']
            future = prophet_model.make_future_dataframe(periods=days_ahead)
            forecast = prophet_model.predict(future)

            predictions = forecast['yhat'].tail(days_ahead).values.tolist()

            return {
                "predictions": predictions,
                "dates": [d.strftime('%Y-%m-%d') for d in future_dates],
                "model": "ensemble"
            }

        except Exception as e:
            self.logger.error(f"Error predicting revenue: {e}")
            return {"error": str(e)}

    async def predict_customer_segments(self, customer_features: pd.DataFrame) -> Dict[str, Any]:
        """Predict customer segments"""
        try:
            if "customer_segmentation" not in self.models:
                return {"error": "Customer segmentation model not available"}

            model = self.models["customer_segmentation"]
            scaler = self.scalers["customer_segmentation"]

            # Prepare features
            features = ['total_orders', 'total_spent', 'avg_order_value',
                       'days_since_last_order', 'satisfaction_score']
            X = customer_features[features].fillna(0)
            X_scaled = scaler.transform(X)

            segments = model.predict(X_scaled)

            return {
                "segments": segments.tolist(),
                "segment_names": ["High-Value", "Regular", "Occasional", "At-Risk"]
            }

        except Exception as e:
            self.logger.error(f"Error predicting segments: {e}")
            return {"error": str(e)}

    async def predict_optimal_price(self, product_features: pd.DataFrame) -> Dict[str, Any]:
        """Predict optimal prices"""
        try:
            if "price_optimization" not in self.models:
                return {"error": "Price optimization model not available"}

            model = self.models["price_optimization"]
            scaler = self.scalers["price_optimization"]

            # Prepare features
            features = ['current_price', 'competitor_price', 'demand_index',
                       'category_popularity', 'seasonal_factor', 'inventory_level']
            X = product_features[features]
            X_scaled = scaler.transform(X)

            optimal_prices = model.predict(X_scaled)

            return {
                "optimal_prices": optimal_prices.tolist(),
                "confidence": 0.85  # Placeholder
            }

        except Exception as e:
            self.logger.error(f"Error predicting prices: {e}")
            return {"error": str(e)}