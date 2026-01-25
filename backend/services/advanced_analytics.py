import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List, Optional, Tuple
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import json

from ..core.database import AsyncSessionLocal, get_redis
from ..models.database_models import Metric

class AdvancedAnalytics:
    """
    Advanced analytics engine for real-time business intelligence.
    Provides predictive analytics, customer segmentation, and advanced forecasting.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("advanced_analytics")
        self.redis_client = None
        self.models = {}
        self.scalers = {}
        self.running = False
        
        # Model configurations
        self.model_configs = {
            "revenue_forecast": {
                "model_type": "random_forest",
                "features": ["hour_of_day", "day_of_week", "month", "historical_avg", "trend"],
                "target": "revenue",
                "retrain_interval": 86400,  # 24 hours
                "forecast_horizon": 168  # 7 days in hours
            },
            "churn_prediction": {
                "model_type": "random_forest",
                "features": ["recency", "frequency", "monetary", "satisfaction_score", "support_tickets"],
                "target": "churn_probability",
                "retrain_interval": 43200,  # 12 hours
                "forecast_horizon": 720  # 30 days in hours
            },
            "demand_forecast": {
                "model_type": "random_forest",
                "features": ["seasonality", "trend", "external_factors", "promotions"],
                "target": "demand",
                "retrain_interval": 21600,  # 6 hours
                "forecast_horizon": 168
            }
        }
    
    async def initialize(self):
        """Initialize the advanced analytics engine"""
        self.redis_client = await get_redis()
        await self._load_or_train_models()
        self.logger.info("Advanced analytics engine initialized")
    
    async def start_analytics_engine(self):
        """Start the analytics engine with all background tasks"""
        if self.running:
            return
        
        self.running = True
        self.logger.info("Starting advanced analytics engine...")
        
        tasks = [
            asyncio.create_task(self._continuous_forecasting()),
            asyncio.create_task(self._customer_segmentation_analysis()),
            asyncio.create_task(self._anomaly_detection_advanced()),
            asyncio.create_task(self._model_retraining_scheduler()),
            asyncio.create_task(self._business_intelligence_reports())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Error in analytics engine: {e}")
        finally:
            self.running = False
    
    async def _load_or_train_models(self):
        """Load existing models or train new ones"""
        for model_name, config in self.model_configs.items():
            try:
                # Try to load existing model
                model_data = await self.redis_client.get(f"ml_model:{model_name}")
                if model_data:
                    self.models[model_name] = joblib.loads(model_data)
                    self.logger.info(f"Loaded existing model: {model_name}")
                else:
                    # Train new model
                    await self._train_model(model_name, config)
                    self.logger.info(f"Trained new model: {model_name}")
            
            except Exception as e:
                self.logger.error(f"Error loading/training model {model_name}: {e}")
    
    async def _train_model(self, model_name: str, config: Dict[str, Any]):
        """Train a machine learning model"""
        try:
            # Get training data
            training_data = await self._get_training_data(model_name, config)
            
            if training_data is None or len(training_data) < 100:
                self.logger.warning(f"Insufficient data for training {model_name}")
                return
            
            # Prepare features and target
            X, y = await self._prepare_features_target(training_data, config)
            
            if X is None or y is None:
                self.logger.warning(f"Could not prepare features for {model_name}")
                return
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            self.scalers[model_name] = scaler
            
            # Train model
            if config["model_type"] == "random_forest":
                model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                )
            else:
                model = RandomForestRegressor(n_estimators=100, random_state=42)
            
            model.fit(X_scaled, y)
            self.models[model_name] = model
            
            # Save model to Redis
            model_data = joblib.dumps(model)
            await self.redis_client.set(f"ml_model:{model_name}", model_data, ex=86400)
            
            # Save scaler
            scaler_data = joblib.dumps(scaler)
            await self.redis_client.set(f"ml_scaler:{model_name}", scaler_data, ex=86400)
            
            # Calculate and store model metrics
            predictions = model.predict(X_scaled)
            mae = mean_absolute_error(y, predictions)
            mse = mean_squared_error(y, predictions)
            
            model_metrics = {
                "mae": mae,
                "mse": mse,
                "rmse": np.sqrt(mse),
                "training_samples": len(X),
                "features": config["features"],
                "trained_at": datetime.utcnow().isoformat()
            }
            
            await self.redis_client.set(
                f"ml_metrics:{model_name}",
                json.dumps(model_metrics, default=str),
                ex=86400
            )
            
            self.logger.info(f"Model {model_name} trained successfully. MAE: {mae:.2f}, RMSE: {np.sqrt(mse):.2f}")
            
        except Exception as e:
            self.logger.error(f"Error training model {model_name}: {e}")
    
    async def _get_training_data(self, model_name: str, config: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """Get training data for a specific model"""
        try:
            # Get historical data from database
            async with AsyncSessionLocal() as session:
                # Get data from last 30 days for training
                start_date = datetime.utcnow() - timedelta(days=30)
                
                # This would be a more complex query in production
                # For now, we'll simulate getting the data
                
                if model_name == "revenue_forecast":
                    return await self._get_revenue_training_data(session, start_date)
                elif model_name == "churn_prediction":
                    return await self._get_churn_training_data(session, start_date)
                elif model_name == "demand_forecast":
                    return await self._get_demand_training_data(session, start_date)
                
        except Exception as e:
            self.logger.error(f"Error getting training data for {model_name}: {e}")
            return None
    
    async def _get_revenue_training_data(self, session, start_date: datetime) -> pd.DataFrame:
        """Get revenue training data"""
        # In production, this would query your actual database
        # For now, we'll generate synthetic training data
        
        dates = pd.date_range(start=start_date, end=datetime.utcnow(), freq='H')
        data = []
        
        for date in dates:
            # Simulate realistic revenue patterns
            hour_of_day = date.hour
            day_of_week = date.weekday()
            month = date.month
            
            # Base revenue with patterns
            base_revenue = 1000
            hourly_multiplier = 1.0 + 0.5 * np.sin(2 * np.pi * hour_of_day / 24)
            weekly_multiplier = 1.2 if day_of_week < 5 else 0.8  # Weekday vs weekend
            monthly_multiplier = 1.0 + 0.1 * np.sin(2 * np.pi * month / 12)
            
            revenue = base_revenue * hourly_multiplier * weekly_multiplier * monthly_multiplier
            revenue += np.random.normal(0, 100)  # Add noise
            
            data.append({
                'timestamp': date,
                'hour_of_day': hour_of_day,
                'day_of_week': day_of_week,
                'month': month,
                'revenue': max(0, revenue),
                'historical_avg': base_revenue,
                'trend': 1.0
            })
        
        return pd.DataFrame(data)
    
    async def _get_churn_training_data(self, session, start_date: datetime) -> pd.DataFrame:
        """Get churn prediction training data"""
        # Simulate customer data for churn prediction
        n_customers = 1000
        data = []
        
        for i in range(n_customers):
            recency = np.random.exponential(30)  # Days since last purchase
            frequency = np.random.poisson(5)  # Number of purchases
            monetary = np.random.lognormal(4, 1)  # Total spent
            satisfaction_score = np.random.normal(4, 0.8)  # 1-5 scale
            support_tickets = np.random.poisson(1)  # Number of support tickets
            
            # Calculate churn probability based on features
            churn_score = (
                0.3 * min(recency / 60, 1) +  # Higher recency = higher churn
                0.2 * max(0, 1 - frequency / 10) +  # Lower frequency = higher churn
                0.2 * max(0, 1 - monetary / 1000) +  # Lower monetary = higher churn
                0.2 * max(0, 1 - satisfaction_score / 5) +  # Lower satisfaction = higher churn
                0.1 * min(support_tickets / 5, 1)  # More tickets = higher churn
            )
            
            data.append({
                'customer_id': i,
                'recency': recency,
                'frequency': frequency,
                'monetary': monetary,
                'satisfaction_score': satisfaction_score,
                'support_tickets': support_tickets,
                'churn_probability': min(1, max(0, churn_score))
            })
        
        return pd.DataFrame(data)
    
    async def _get_demand_training_data(self, session, start_date: datetime) -> pd.DataFrame:
        """Get demand forecasting training data"""
        dates = pd.date_range(start=start_date, end=datetime.utcnow(), freq='H')
        data = []
        
        for date in dates:
            seasonality = 1.0 + 0.3 * np.sin(2 * np.pi * date.dayofyear / 365)
            trend = 1.0 + 0.001 * (date - start_date).days
            external_factors = np.random.normal(1, 0.1)
            promotions = 1.5 if np.random.random() < 0.1 else 1.0  # 10% chance of promotion
            
            demand = 100 * seasonality * trend * external_factors * promotions
            demand += np.random.normal(0, 10)
            
            data.append({
                'timestamp': date,
                'seasonality': seasonality,
                'trend': trend,
                'external_factors': external_factors,
                'promotions': promotions,
                'demand': max(0, demand)
            })
        
        return pd.DataFrame(data)
    
    async def _prepare_features_target(self, data: pd.DataFrame, config: Dict[str, Any]) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Prepare features and target variables for training"""
        try:
            features = config["features"]
            target = config["target"]
            
            # Check if all required columns exist
            missing_features = [f for f in features if f not in data.columns]
            if missing_features:
                self.logger.warning(f"Missing features: {missing_features}")
                return None, None
            
            if target not in data.columns:
                self.logger.warning(f"Missing target: {target}")
                return None, None
            
            X = data[features].values
            y = data[target].values
            
            # Remove any rows with NaN values
            mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
            X = X[mask]
            y = y[mask]
            
            return X, y
            
        except Exception as e:
            self.logger.error(f"Error preparing features and target: {e}")
            return None, None
    
    async def _continuous_forecasting(self):
        """Continuously generate forecasts for business metrics"""
        while self.running:
            try:
                for model_name, config in self.model_configs.items():
                    if model_name in self.models:
                        forecast = await self._generate_forecast(model_name, config)
                        if forecast:
                            await self._store_forecast(model_name, forecast)
                
                await asyncio.sleep(300)  # Generate forecasts every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error in continuous forecasting: {e}")
                await asyncio.sleep(600)
    
    async def _generate_forecast(self, model_name: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate forecast for a specific model"""
        try:
            model = self.models.get(model_name)
            scaler = self.scalers.get(model_name)
            
            if not model or not scaler:
                return None
            
            # Prepare forecast features
            forecast_features = await self._prepare_forecast_features(model_name, config)
            if forecast_features is None:
                return None
            
            # Scale features
            forecast_features_scaled = scaler.transform(forecast_features)
            
            # Generate predictions
            predictions = model.predict(forecast_features_scaled)
            
            # Create forecast timestamps
            forecast_horizon = config["forecast_horizon"]
            start_time = datetime.utcnow()
            timestamps = [start_time + timedelta(hours=i) for i in range(forecast_horizon)]
            
            forecast = {
                "model_name": model_name,
                "predictions": predictions.tolist(),
                "timestamps": [ts.isoformat() for ts in timestamps],
                "generated_at": start_time.isoformat(),
                "horizon_hours": forecast_horizon
            }
            
            return forecast
            
        except Exception as e:
            self.logger.error(f"Error generating forecast for {model_name}: {e}")
            return None
    
    async def _prepare_forecast_features(self, model_name: str, config: Dict[str, Any]) -> Optional[np.ndarray]:
        """Prepare features for forecasting"""
        try:
            forecast_horizon = config["forecast_horizon"]
            features = config["features"]
            
            # Generate future feature values
            future_features = []
            start_time = datetime.utcnow()
            
            for i in range(forecast_horizon):
                future_time = start_time + timedelta(hours=i)
                
                if model_name == "revenue_forecast":
                    feature_row = [
                        future_time.hour,  # hour_of_day
                        future_time.weekday(),  # day_of_week
                        future_time.month,  # month
                        1000,  # historical_avg (would be calculated from data)
                        1.0  # trend (would be calculated from data)
                    ]
                elif model_name == "churn_prediction":
                    # For churn, we'd typically predict for existing customers
                    # This is a simplified example
                    feature_row = [30, 5, 500, 4.0, 1]  # Average customer profile
                elif model_name == "demand_forecast":
                    seasonality = 1.0 + 0.3 * np.sin(2 * np.pi * future_time.timetuple().tm_yday / 365)
                    feature_row = [
                        seasonality,  # seasonality
                        1.0,  # trend
                        1.0,  # external_factors
                        1.0   # promotions
                    ]
                else:
                    continue
                
                future_features.append(feature_row)
            
            return np.array(future_features)
            
        except Exception as e:
            self.logger.error(f"Error preparing forecast features for {model_name}: {e}")
            return None
    
    async def _store_forecast(self, model_name: str, forecast: Dict[str, Any]):
        """Store forecast results"""
        try:
            # Store in Redis for real-time access
            await self.redis_client.set(
                f"forecast:{model_name}",
                json.dumps(forecast, default=str),
                ex=3600  # Expire after 1 hour
            )
            
            # Publish forecast update
            await self.redis_client.publish(
                "forecast_updates",
                json.dumps({
                    "type": "forecast_update",
                    "model_name": model_name,
                    "forecast": forecast
                }, default=str)
            )
            
            self.logger.info(f"Stored forecast for {model_name}")
            
        except Exception as e:
            self.logger.error(f"Error storing forecast for {model_name}: {e}")
    
    async def _customer_segmentation_analysis(self):
        """Perform customer segmentation analysis"""
        while self.running:
            try:
                # Get customer data
                customer_data = await self._get_customer_data()
                
                if customer_data is not None and len(customer_data) > 10:
                    # Perform RFM analysis
                    segments = await self._perform_rfm_analysis(customer_data)
                    
                    # Store segmentation results
                    await self._store_segmentation_results(segments)
                
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                self.logger.error(f"Error in customer segmentation: {e}")
                await asyncio.sleep(3600)
    
    async def _get_customer_data(self) -> Optional[pd.DataFrame]:
        """Get customer data for segmentation"""
        # In production, this would query your customer database
        # For now, we'll generate synthetic customer data
        
        n_customers = 500
        data = []
        
        for i in range(n_customers):
            recency = np.random.exponential(30)
            frequency = np.random.poisson(5)
            monetary = np.random.lognormal(4, 1)
            
            data.append({
                'customer_id': f'cust_{i}',
                'recency': recency,
                'frequency': frequency,
                'monetary': monetary
            })
        
        return pd.DataFrame(data)
    
    async def _perform_rfm_analysis(self, customer_data: pd.DataFrame) -> Dict[str, Any]:
        """Perform RFM (Recency, Frequency, Monetary) analysis"""
        try:
            # Calculate RFM scores
            customer_data['R_score'] = pd.qcut(customer_data['recency'], 5, labels=[5,4,3,2,1])
            customer_data['F_score'] = pd.qcut(customer_data['frequency'].rank(method='first'), 5, labels=[1,2,3,4,5])
            customer_data['M_score'] = pd.qcut(customer_data['monetary'], 5, labels=[1,2,3,4,5])
            
            # Create RFM segments
            customer_data['RFM_Score'] = (
                customer_data['R_score'].astype(str) + 
                customer_data['F_score'].astype(str) + 
                customer_data['M_score'].astype(str)
            )
            
            # Define segment names
            def segment_customers(row):
                if row['RFM_Score'] in ['555', '554', '544', '545', '454', '455', '445']:
                    return 'Champions'
                elif row['RFM_Score'] in ['543', '444', '435', '355', '354', '345', '344', '335']:
                    return 'Loyal Customers'
                elif row['RFM_Score'] in ['512', '511', '422', '421', '412', '411', '311']:
                    return 'Potential Loyalists'
                elif row['RFM_Score'] in ['533', '532', '531', '523', '522', '521', '515', '514', '513', '425', '424', '413', '414', '415', '315', '314', '313']:
                    return 'New Customers'
                elif row['RFM_Score'] in ['155', '154', '144', '214', '215', '115', '114']:
                    return 'At Risk'
                elif row['RFM_Score'] in ['155', '154', '144', '214', '215', '115', '114']:
                    return 'Cannot Lose Them'
                else:
                    return 'Others'
            
            customer_data['Segment'] = customer_data.apply(segment_customers, axis=1)
            
            # Calculate segment statistics
            segment_stats = customer_data.groupby('Segment').agg({
                'customer_id': 'count',
                'recency': 'mean',
                'frequency': 'mean',
                'monetary': 'mean'
            }).round(2)
            
            return {
                'segment_counts': segment_stats['customer_id'].to_dict(),
                'segment_stats': segment_stats.to_dict(),
                'total_customers': len(customer_data),
                'analysis_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in RFM analysis: {e}")
            return {}
    
    async def _store_segmentation_results(self, segments: Dict[str, Any]):
        """Store customer segmentation results"""
        try:
            await self.redis_client.set(
                "customer_segments",
                json.dumps(segments, default=str),
                ex=7200  # Expire after 2 hours
            )
            
            # Publish segmentation update
            await self.redis_client.publish(
                "segmentation_updates",
                json.dumps({
                    "type": "segmentation_update",
                    "segments": segments
                }, default=str)
            )
            
            self.logger.info("Stored customer segmentation results")
            
        except Exception as e:
            self.logger.error(f"Error storing segmentation results: {e}")
    
    async def _anomaly_detection_advanced(self):
        """Advanced anomaly detection using multiple algorithms"""
        while self.running:
            try:
                # Get recent metrics
                recent_metrics = await self._get_recent_metrics_for_anomaly_detection()
                
                if recent_metrics:
                    anomalies = await self._detect_advanced_anomalies(recent_metrics)
                    
                    if anomalies:
                        await self._store_anomaly_results(anomalies)
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error in advanced anomaly detection: {e}")
                await asyncio.sleep(600)
    
    async def _get_recent_metrics_for_anomaly_detection(self) -> Optional[pd.DataFrame]:
        """Get recent metrics for anomaly detection"""
        try:
            async with AsyncSessionLocal() as session:
                # Get last 24 hours of data
                start_time = datetime.utcnow() - timedelta(hours=24)
                
                # This would be a proper database query in production
                # For now, simulate recent metrics
                timestamps = pd.date_range(start=start_time, end=datetime.utcnow(), freq='5min')
                data = []
                
                for ts in timestamps:
                    # Simulate metrics with occasional anomalies
                    revenue = 1000 + 200 * np.sin(2 * np.pi * ts.hour / 24) + np.random.normal(0, 50)
                    
                    # Inject anomalies occasionally
                    if np.random.random() < 0.02:  # 2% chance of anomaly
                        revenue *= np.random.choice([0.3, 2.5])  # Drop or spike
                    
                    data.append({
                        'timestamp': ts,
                        'revenue': revenue,
                        'orders': max(1, int(revenue / 75 + np.random.normal(0, 5))),
                        'customer_satisfaction': min(5, max(1, 4.2 + np.random.normal(0, 0.3)))
                    })
                
                return pd.DataFrame(data)
                
        except Exception as e:
            self.logger.error(f"Error getting recent metrics: {e}")
            return None
    
    async def _detect_advanced_anomalies(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies using advanced algorithms"""
        anomalies = []
        
        try:
            # Isolation Forest for multivariate anomaly detection
            features = ['revenue', 'orders', 'customer_satisfaction']
            X = data[features].values
            
            # Remove any NaN values
            mask = ~np.isnan(X).any(axis=1)
            X_clean = X[mask]
            data_clean = data[mask]
            
            if len(X_clean) < 10:
                return anomalies
            
            # Fit Isolation Forest
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            anomaly_labels = iso_forest.fit_predict(X_clean)
            
            # Find anomalies
            anomaly_indices = np.where(anomaly_labels == -1)[0]
            
            for idx in anomaly_indices:
                row = data_clean.iloc[idx]
                
                anomalies.append({
                    'timestamp': row['timestamp'].isoformat(),
                    'type': 'multivariate_anomaly',
                    'metrics': {
                        'revenue': row['revenue'],
                        'orders': row['orders'],
                        'customer_satisfaction': row['customer_satisfaction']
                    },
                    'anomaly_score': iso_forest.decision_function(X_clean[idx:idx+1])[0],
                    'detection_method': 'isolation_forest'
                })
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Error in advanced anomaly detection: {e}")
            return []
    
    async def _store_anomaly_results(self, anomalies: List[Dict[str, Any]]):
        """Store anomaly detection results"""
        try:
            # Store in Redis
            await self.redis_client.lpush(
                "advanced_anomalies",
                *[json.dumps(anomaly, default=str) for anomaly in anomalies]
            )
            await self.redis_client.ltrim("advanced_anomalies", 0, 99)  # Keep last 100
            
            # Publish anomaly alerts
            for anomaly in anomalies:
                await self.redis_client.publish(
                    "anomaly_alerts",
                    json.dumps({
                        "type": "advanced_anomaly",
                        "anomaly": anomaly
                    }, default=str)
                )
            
            self.logger.info(f"Stored {len(anomalies)} advanced anomalies")
            
        except Exception as e:
            self.logger.error(f"Error storing anomaly results: {e}")
    
    async def _model_retraining_scheduler(self):
        """Schedule model retraining based on performance degradation"""
        while self.running:
            try:
                for model_name, config in self.model_configs.items():
                    # Check if model needs retraining
                    needs_retraining = await self._check_model_performance(model_name)
                    
                    if needs_retraining:
                        self.logger.info(f"Retraining model: {model_name}")
                        await self._train_model(model_name, config)
                
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                self.logger.error(f"Error in model retraining scheduler: {e}")
                await asyncio.sleep(3600)
    
    async def _check_model_performance(self, model_name: str) -> bool:
        """Check if model performance has degraded and needs retraining"""
        try:
            # Get model metrics
            metrics_data = await self.redis_client.get(f"ml_metrics:{model_name}")
            if not metrics_data:
                return True  # No metrics, needs training
            
            metrics = json.loads(metrics_data)
            trained_at = datetime.fromisoformat(metrics["trained_at"])
            
            # Check if model is too old
            if datetime.utcnow() - trained_at > timedelta(days=7):
                return True
            
            # In production, you'd also check prediction accuracy against recent data
            # and retrain if performance has degraded significantly
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking model performance for {model_name}: {e}")
            return False
    
    async def _business_intelligence_reports(self):
        """Generate business intelligence reports"""
        while self.running:
            try:
                # Generate daily BI report
                report = await self._generate_bi_report()
                
                if report:
                    await self._store_bi_report(report)
                
                await asyncio.sleep(86400)  # Generate daily
                
            except Exception as e:
                self.logger.error(f"Error generating BI reports: {e}")
                await asyncio.sleep(86400)
    
    async def _generate_bi_report(self) -> Optional[Dict[str, Any]]:
        """Generate comprehensive business intelligence report"""
        try:
            report = {
                'report_date': datetime.utcnow().isoformat(),
                'summary': {},
                'forecasts': {},
                'segments': {},
                'anomalies': {},
                'recommendations': []
            }
            
            # Get current metrics summary
            current_metrics = {}
            for metric_type in ['revenue', 'orders', 'customer_satisfaction', 'churn_risk']:
                metric_data = await self.redis_client.get(f"current_metric:{metric_type}")
                if metric_data:
                    current_metrics[metric_type] = json.loads(metric_data)
            
            report['summary'] = current_metrics
            
            # Get forecasts
            for model_name in self.model_configs.keys():
                forecast_data = await self.redis_client.get(f"forecast:{model_name}")
                if forecast_data:
                    report['forecasts'][model_name] = json.loads(forecast_data)
            
            # Get customer segments
            segments_data = await self.redis_client.get("customer_segments")
            if segments_data:
                report['segments'] = json.loads(segments_data)
            
            # Get recent anomalies
            anomalies_data = await self.redis_client.lrange("advanced_anomalies", 0, 9)
            report['anomalies'] = [json.loads(a) for a in anomalies_data]
            
            # Generate recommendations
            report['recommendations'] = await self._generate_recommendations(report)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating BI report: {e}")
            return None
    
    async def _generate_recommendations(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate business recommendations based on analysis"""
        recommendations = []
        
        try:
            # Analyze forecasts for recommendations
            forecasts = report.get('forecasts', {})
            
            if 'revenue_forecast' in forecasts:
                revenue_forecast = forecasts['revenue_forecast']
                predictions = revenue_forecast.get('predictions', [])
                
                if predictions:
                    # Check for declining revenue trend
                    if len(predictions) >= 24:  # At least 24 hours of forecast
                        recent_avg = np.mean(predictions[:24])
                        future_avg = np.mean(predictions[24:48]) if len(predictions) >= 48 else recent_avg
                        
                        if future_avg < recent_avg * 0.95:  # 5% decline
                            recommendations.append({
                                'type': 'revenue_decline_warning',
                                'priority': 'high',
                                'title': 'Revenue Decline Predicted',
                                'description': f'Revenue forecast shows {((recent_avg - future_avg) / recent_avg * 100):.1f}% decline in next 24 hours',
                                'suggested_actions': [
                                    'Launch promotional campaign',
                                    'Review pricing strategy',
                                    'Increase marketing spend'
                                ]
                            })
            
            # Analyze customer segments for recommendations
            segments = report.get('segments', {})
            segment_counts = segments.get('segment_counts', {})
            
            if 'At Risk' in segment_counts and segment_counts['At Risk'] > 0:
                at_risk_count = segment_counts['At Risk']
                total_customers = segments.get('total_customers', 1)
                at_risk_percentage = (at_risk_count / total_customers) * 100
                
                if at_risk_percentage > 15:  # More than 15% at risk
                    recommendations.append({
                        'type': 'customer_retention_alert',
                        'priority': 'medium',
                        'title': 'High Customer Churn Risk',
                        'description': f'{at_risk_percentage:.1f}% of customers are at risk of churning',
                        'suggested_actions': [
                            'Launch retention campaign for at-risk customers',
                            'Improve customer service response times',
                            'Offer loyalty rewards'
                        ]
                    })
            
            # Analyze anomalies for recommendations
            anomalies = report.get('anomalies', [])
            recent_anomalies = [a for a in anomalies if 
                              datetime.fromisoformat(a['timestamp']) > datetime.utcnow() - timedelta(hours=6)]
            
            if len(recent_anomalies) > 3:
                recommendations.append({
                    'type': 'anomaly_investigation',
                    'priority': 'high',
                    'title': 'Multiple Anomalies Detected',
                    'description': f'{len(recent_anomalies)} anomalies detected in the last 6 hours',
                    'suggested_actions': [
                        'Investigate system performance',
                        'Check for external factors affecting business',
                        'Review recent changes to operations'
                    ]
                })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return []
    
    async def _store_bi_report(self, report: Dict[str, Any]):
        """Store business intelligence report"""
        try:
            # Store in Redis
            await self.redis_client.set(
                "latest_bi_report",
                json.dumps(report, default=str),
                ex=172800  # Expire after 2 days
            )
            
            # Store in daily reports list
            report_date = datetime.utcnow().strftime('%Y-%m-%d')
            await self.redis_client.set(
                f"bi_report:{report_date}",
                json.dumps(report, default=str),
                ex=2592000  # Expire after 30 days
            )
            
            # Publish BI report update
            await self.redis_client.publish(
                "bi_reports",
                json.dumps({
                    "type": "bi_report_generated",
                    "report": report
                }, default=str)
            )
            
            self.logger.info("Stored business intelligence report")
            
        except Exception as e:
            self.logger.error(f"Error storing BI report: {e}")
    
    async def get_analytics_status(self) -> Dict[str, Any]:
        """Get status of the analytics engine"""
        try:
            model_status = {}
            for model_name in self.model_configs.keys():
                metrics_data = await self.redis_client.get(f"ml_metrics:{model_name}")
                if metrics_data:
                    metrics = json.loads(metrics_data)
                    model_status[model_name] = {
                        'trained': True,
                        'mae': metrics.get('mae'),
                        'rmse': metrics.get('rmse'),
                        'training_samples': metrics.get('training_samples'),
                        'trained_at': metrics.get('trained_at')
                    }
                else:
                    model_status[model_name] = {'trained': False}
            
            return {
                'running': self.running,
                'models': model_status,
                'total_models': len(self.model_configs),
                'trained_models': len([m for m in model_status.values() if m.get('trained', False)])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting analytics status: {e}")
            return {'error': str(e)}

# Global instance
advanced_analytics = AdvancedAnalytics()