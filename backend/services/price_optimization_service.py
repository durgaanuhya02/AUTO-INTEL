"""
XGBoost Price Optimization Service
Advanced price optimization using XGBoost with SHAP explainability
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json

# XGBoost and SHAP imports
try:
    import xgboost as xgb
    import shap
    from sklearn.model_selection import train_test_split, GridSearchCV
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logging.warning("XGBoost or SHAP not available. Install: pip install xgboost shap")

@dataclass
class PriceOptimizationResult:
    """Price optimization result with recommendations"""
    product_id: str
    current_price: float
    optimal_price: float
    price_change_percent: float
    predicted_demand: float
    predicted_revenue: float
    confidence_score: float
    price_elasticity: float
    feature_importance: Dict[str, float]
    shap_values: Dict[str, float]
    recommendations: List[str]

@dataclass
class PriceSegmentAnalysis:
    """Price segment analysis result"""
    segment_name: str
    price_range: Tuple[float, float]
    demand_sensitivity: float
    revenue_potential: float
    customer_count: int
    optimal_strategy: str

class PriceOptimizationService:
    """Advanced price optimization using XGBoost and SHAP"""
    
    def __init__(self):
        self.logger = logging.getLogger("price_optimization")
        self.models = {}
        self.scalers = {}
        self.label_encoders = {}
        self.shap_explainers = {}
        self.feature_names = []
        
        # Price optimization parameters
        self.price_bounds = {
            'min_discount': 0.05,  # Maximum 5% discount
            'max_markup': 0.30,    # Maximum 30% markup
            'price_steps': 0.01    # 1% price steps
        }
        
    async def initialize(self):
        """Initialize price optimization service"""
        if not XGBOOST_AVAILABLE:
            self.logger.error("XGBoost and SHAP libraries not available")
            return False
        
        self.logger.info("🎯 Initializing XGBoost Price Optimization Service...")
        
        # Initialize SHAP
        shap.initjs()
        
        return True
    
    async def train_price_optimization_model(self, 
                                           training_data: pd.DataFrame,
                                           target_column: str = 'revenue') -> Dict[str, Any]:
        """Train XGBoost model for price optimization"""
        
        try:
            self.logger.info("🚀 Training XGBoost price optimization model...")
            
            # Prepare features and target
            X, y, feature_names = self._prepare_price_features(training_data, target_column)
            self.feature_names = feature_names
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            self.scalers['price_model'] = scaler
            
            # XGBoost hyperparameter tuning
            param_grid = {
                'n_estimators': [100, 200, 300],
                'max_depth': [3, 6, 9],
                'learning_rate': [0.01, 0.1, 0.2],
                'subsample': [0.8, 0.9, 1.0],
                'colsample_bytree': [0.8, 0.9, 1.0]
            }
            
            # Create XGBoost regressor
            xgb_model = xgb.XGBRegressor(
                objective='reg:squarederror',
                random_state=42,
                n_jobs=-1
            )
            
            # Grid search for best parameters
            self.logger.info("🔍 Performing hyperparameter optimization...")
            grid_search = GridSearchCV(
                xgb_model, 
                param_grid, 
                cv=5, 
                scoring='neg_mean_squared_error',
                n_jobs=-1,
                verbose=1
            )
            
            grid_search.fit(X_train_scaled, y_train)
            best_model = grid_search.best_estimator_
            
            # Train final model
            best_model.fit(X_train_scaled, y_train)
            self.models['price_model'] = best_model
            
            # Make predictions
            y_train_pred = best_model.predict(X_train_scaled)
            y_test_pred = best_model.predict(X_test_scaled)
            
            # Calculate metrics
            train_mae = mean_absolute_error(y_train, y_train_pred)
            test_mae = mean_absolute_error(y_test, y_test_pred)
            train_r2 = r2_score(y_train, y_train_pred)
            test_r2 = r2_score(y_test, y_test_pred)
            
            # Create SHAP explainer
            self.logger.info("🔍 Creating SHAP explainer...")
            explainer = shap.TreeExplainer(best_model)
            self.shap_explainers['price_model'] = explainer
            
            # Calculate SHAP values for sample
            sample_size = min(100, len(X_test_scaled))
            shap_values = explainer.shap_values(X_test_scaled[:sample_size])
            
            # Feature importance from XGBoost
            feature_importance = dict(zip(feature_names, best_model.feature_importances_))
            
            # SHAP feature importance (mean absolute SHAP values)
            shap_importance = dict(zip(
                feature_names, 
                np.mean(np.abs(shap_values), axis=0)
            ))
            
            model_info = {
                'model_type': 'XGBoost',
                'best_params': grid_search.best_params_,
                'feature_names': feature_names,
                'metrics': {
                    'train_mae': train_mae,
                    'test_mae': test_mae,
                    'train_r2': train_r2,
                    'test_r2': test_r2
                },
                'feature_importance': feature_importance,
                'shap_importance': shap_importance,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'trained_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ Model trained successfully! Test R²: {test_r2:.3f}, Test MAE: {test_mae:.2f}")
            
            return model_info
            
        except Exception as e:
            self.logger.error(f"Error training price optimization model: {str(e)}")
            raise
    
    def _prepare_price_features(self, data: pd.DataFrame, target_column: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Prepare features for price optimization model"""
        
        # Create comprehensive feature set for price optimization
        features_df = pd.DataFrame()
        
        # Price-related features
        if 'price' in data.columns:
            features_df['price'] = data['price']
            features_df['price_log'] = np.log1p(data['price'])
        
        # Demand features
        if 'quantity' in data.columns:
            features_df['quantity'] = data['quantity']
            features_df['quantity_log'] = np.log1p(data['quantity'])
        
        # Product features
        if 'product_category' in data.columns:
            le = LabelEncoder()
            features_df['product_category_encoded'] = le.fit_transform(data['product_category'].fillna('unknown'))
            self.label_encoders['product_category'] = le
        
        # Customer features
        if 'customer_segment' in data.columns:
            le = LabelEncoder()
            features_df['customer_segment_encoded'] = le.fit_transform(data['customer_segment'].fillna('unknown'))
            self.label_encoders['customer_segment'] = le
        
        # Temporal features
        if 'date' in data.columns:
            dates = pd.to_datetime(data['date'])
            features_df['day_of_week'] = dates.dt.dayofweek
            features_df['month'] = dates.dt.month
            features_df['quarter'] = dates.dt.quarter
            features_df['is_weekend'] = (dates.dt.dayofweek >= 5).astype(int)
        
        # Market features
        if 'competitor_price' in data.columns:
            features_df['competitor_price'] = data['competitor_price']
            features_df['price_vs_competitor'] = data['price'] / data['competitor_price'].replace(0, np.nan)
        
        # Economic features
        if 'market_demand' in data.columns:
            features_df['market_demand'] = data['market_demand']
        
        # Interaction features
        if 'price' in features_df.columns and 'quantity' in features_df.columns:
            features_df['price_quantity_interaction'] = features_df['price'] * features_df['quantity']
        
        # Fill missing values
        features_df = features_df.fillna(features_df.median())
        
        # Get target variable
        y = data[target_column].values
        
        # Remove rows with missing target
        valid_mask = ~np.isnan(y)
        X = features_df[valid_mask].values
        y = y[valid_mask]
        
        feature_names = features_df.columns.tolist()
        
        return X, y, feature_names
    
    async def optimize_price(self, 
                           product_data: Dict[str, Any],
                           optimization_objective: str = 'revenue') -> PriceOptimizationResult:
        """Optimize price for a specific product"""
        
        try:
            if 'price_model' not in self.models:
                raise ValueError("Price optimization model not trained")
            
            model = self.models['price_model']
            scaler = self.scalers['price_model']
            explainer = self.shap_explainers['price_model']
            
            current_price = product_data.get('price', 100.0)
            
            # Generate price scenarios
            price_scenarios = self._generate_price_scenarios(current_price)
            
            # Evaluate each price scenario
            best_price = current_price
            best_score = -float('inf')
            best_prediction = None
            best_shap_values = None
            
            for test_price in price_scenarios:
                # Create feature vector for this price
                feature_vector = self._create_feature_vector(product_data, test_price)
                feature_vector_scaled = scaler.transform([feature_vector])
                
                # Predict outcome
                prediction = model.predict(feature_vector_scaled)[0]
                
                # Calculate optimization score based on objective
                if optimization_objective == 'revenue':
                    score = prediction  # Assuming model predicts revenue
                elif optimization_objective == 'profit':
                    cost = product_data.get('cost', current_price * 0.7)
                    score = prediction - cost
                else:
                    score = prediction
                
                if score > best_score:
                    best_score = score
                    best_price = test_price
                    best_prediction = prediction
                    
                    # Calculate SHAP values for best price
                    best_shap_values = explainer.shap_values([feature_vector_scaled[0]])
            
            # Calculate price elasticity
            price_elasticity = self._calculate_price_elasticity(
                product_data, current_price, model, scaler
            )
            
            # Get feature importance and SHAP values
            feature_importance = dict(zip(self.feature_names, model.feature_importances_))
            shap_values_dict = dict(zip(self.feature_names, best_shap_values[0])) if best_shap_values is not None else {}
            
            # Generate recommendations
            recommendations = self._generate_price_recommendations(
                current_price, best_price, price_elasticity, feature_importance
            )
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                product_data, price_elasticity, feature_importance
            )
            
            return PriceOptimizationResult(
                product_id=product_data.get('product_id', 'unknown'),
                current_price=current_price,
                optimal_price=best_price,
                price_change_percent=((best_price - current_price) / current_price) * 100,
                predicted_demand=product_data.get('quantity', 0),
                predicted_revenue=best_prediction,
                confidence_score=confidence_score,
                price_elasticity=price_elasticity,
                feature_importance=feature_importance,
                shap_values=shap_values_dict,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Error optimizing price: {str(e)}")
            raise
    
    def _generate_price_scenarios(self, current_price: float) -> List[float]:
        """Generate price scenarios for optimization"""
        
        min_price = current_price * (1 - self.price_bounds['min_discount'])
        max_price = current_price * (1 + self.price_bounds['max_markup'])
        step = current_price * self.price_bounds['price_steps']
        
        scenarios = []
        price = min_price
        while price <= max_price:
            scenarios.append(round(price, 2))
            price += step
        
        return scenarios
    
    def _create_feature_vector(self, product_data: Dict[str, Any], price: float) -> List[float]:
        """Create feature vector for prediction"""
        
        features = []
        
        # Price features
        features.append(price)  # price
        features.append(np.log1p(price))  # price_log
        
        # Quantity features
        quantity = product_data.get('quantity', 10)
        features.append(quantity)  # quantity
        features.append(np.log1p(quantity))  # quantity_log
        
        # Categorical features (encoded)
        features.append(product_data.get('product_category_encoded', 0))
        features.append(product_data.get('customer_segment_encoded', 0))
        
        # Temporal features
        now = datetime.now()
        features.append(now.weekday())  # day_of_week
        features.append(now.month)  # month
        features.append((now.month - 1) // 3 + 1)  # quarter
        features.append(1 if now.weekday() >= 5 else 0)  # is_weekend
        
        # Market features
        competitor_price = product_data.get('competitor_price', price * 1.1)
        features.append(competitor_price)  # competitor_price
        features.append(price / competitor_price if competitor_price > 0 else 1.0)  # price_vs_competitor
        
        # Market demand
        features.append(product_data.get('market_demand', 1.0))
        
        # Interaction features
        features.append(price * quantity)  # price_quantity_interaction
        
        return features
    
    def _calculate_price_elasticity(self, 
                                  product_data: Dict[str, Any], 
                                  current_price: float,
                                  model, 
                                  scaler) -> float:
        """Calculate price elasticity of demand"""
        
        try:
            # Test small price changes
            price_increase = current_price * 1.01  # 1% increase
            price_decrease = current_price * 0.99   # 1% decrease
            
            # Create feature vectors
            features_base = self._create_feature_vector(product_data, current_price)
            features_up = self._create_feature_vector(product_data, price_increase)
            features_down = self._create_feature_vector(product_data, price_decrease)
            
            # Scale features
            features_base_scaled = scaler.transform([features_base])
            features_up_scaled = scaler.transform([features_up])
            features_down_scaled = scaler.transform([features_down])
            
            # Predict outcomes
            pred_base = model.predict(features_base_scaled)[0]
            pred_up = model.predict(features_up_scaled)[0]
            pred_down = model.predict(features_down_scaled)[0]
            
            # Calculate elasticity
            if pred_base > 0:
                elasticity_up = ((pred_up - pred_base) / pred_base) / 0.01
                elasticity_down = ((pred_base - pred_down) / pred_base) / 0.01
                elasticity = (elasticity_up + elasticity_down) / 2
            else:
                elasticity = -1.0  # Default elasticity
            
            return elasticity
            
        except Exception as e:
            self.logger.error(f"Error calculating price elasticity: {str(e)}")
            return -1.0
    
    def _generate_price_recommendations(self, 
                                      current_price: float,
                                      optimal_price: float,
                                      price_elasticity: float,
                                      feature_importance: Dict[str, float]) -> List[str]:
        """Generate actionable price recommendations"""
        
        recommendations = []
        
        price_change = ((optimal_price - current_price) / current_price) * 100
        
        # Price change recommendations
        if abs(price_change) < 1:
            recommendations.append("✅ Current price is near optimal - maintain current pricing")
        elif price_change > 5:
            recommendations.append(f"📈 Consider increasing price by {price_change:.1f}% to ${optimal_price:.2f}")
            recommendations.append("⚠️ Monitor demand closely after price increase")
        elif price_change < -5:
            recommendations.append(f"📉 Consider decreasing price by {abs(price_change):.1f}% to ${optimal_price:.2f}")
            recommendations.append("💰 Price reduction may increase volume and total revenue")
        
        # Elasticity-based recommendations
        if price_elasticity > -0.5:
            recommendations.append("🔒 Demand is price inelastic - price increases have minimal impact on volume")
        elif price_elasticity < -2.0:
            recommendations.append("⚡ Demand is highly price elastic - small price changes significantly affect volume")
        
        # Feature-based recommendations
        top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:3]
        
        for feature, importance in top_features:
            if 'competitor' in feature.lower():
                recommendations.append("🎯 Monitor competitor pricing closely - it significantly impacts optimal price")
            elif 'market_demand' in feature.lower():
                recommendations.append("📊 Market demand is a key factor - adjust pricing based on demand cycles")
            elif 'category' in feature.lower():
                recommendations.append("🏷️ Product category influences pricing - consider category-specific strategies")
        
        return recommendations
    
    def _calculate_confidence_score(self, 
                                  product_data: Dict[str, Any],
                                  price_elasticity: float,
                                  feature_importance: Dict[str, float]) -> float:
        """Calculate confidence score for price optimization"""
        
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on data quality
        if 'competitor_price' in product_data:
            confidence += 0.1
        if 'market_demand' in product_data:
            confidence += 0.1
        if 'quantity' in product_data and product_data['quantity'] > 0:
            confidence += 0.1
        
        # Adjust based on price elasticity
        if -2.0 <= price_elasticity <= -0.5:  # Reasonable elasticity range
            confidence += 0.1
        
        # Adjust based on feature importance distribution
        if len(feature_importance) > 0:
            max_importance = max(feature_importance.values())
            if max_importance < 0.5:  # No single feature dominates
                confidence += 0.1
        
        return min(1.0, confidence)
    
    async def analyze_price_segments(self, data: pd.DataFrame) -> List[PriceSegmentAnalysis]:
        """Analyze price segments and their characteristics"""
        
        try:
            if 'price' not in data.columns:
                raise ValueError("Price column required for segment analysis")
            
            # Create price segments
            data['price_segment'] = pd.qcut(data['price'], q=5, labels=['Low', 'Low-Mid', 'Mid', 'Mid-High', 'High'])
            
            segments = []
            
            for segment_name in ['Low', 'Low-Mid', 'Mid', 'Mid-High', 'High']:
                segment_data = data[data['price_segment'] == segment_name]
                
                if len(segment_data) == 0:
                    continue
                
                # Calculate segment metrics
                price_range = (segment_data['price'].min(), segment_data['price'].max())
                
                # Calculate demand sensitivity (price elasticity for segment)
                if len(segment_data) > 10:
                    demand_sensitivity = self._calculate_segment_elasticity(segment_data)
                else:
                    demand_sensitivity = -1.0
                
                # Calculate revenue potential
                revenue_potential = segment_data.get('revenue', segment_data['price'] * segment_data.get('quantity', 1)).sum()
                
                customer_count = len(segment_data)
                
                # Determine optimal strategy
                optimal_strategy = self._determine_segment_strategy(
                    segment_name, demand_sensitivity, revenue_potential, customer_count
                )
                
                segments.append(PriceSegmentAnalysis(
                    segment_name=segment_name,
                    price_range=price_range,
                    demand_sensitivity=demand_sensitivity,
                    revenue_potential=revenue_potential,
                    customer_count=customer_count,
                    optimal_strategy=optimal_strategy
                ))
            
            return segments
            
        except Exception as e:
            self.logger.error(f"Error analyzing price segments: {str(e)}")
            return []
    
    def _calculate_segment_elasticity(self, segment_data: pd.DataFrame) -> float:
        """Calculate price elasticity for a segment"""
        
        try:
            if 'quantity' not in segment_data.columns:
                return -1.0
            
            # Simple elasticity calculation using correlation
            price_changes = segment_data['price'].pct_change().dropna()
            quantity_changes = segment_data['quantity'].pct_change().dropna()
            
            if len(price_changes) > 5 and len(quantity_changes) > 5:
                correlation = np.corrcoef(price_changes, quantity_changes)[0, 1]
                elasticity = correlation * (quantity_changes.std() / price_changes.std())
                return elasticity
            
            return -1.0
            
        except Exception as e:
            return -1.0
    
    def _determine_segment_strategy(self, 
                                  segment_name: str,
                                  demand_sensitivity: float,
                                  revenue_potential: float,
                                  customer_count: int) -> str:
        """Determine optimal pricing strategy for segment"""
        
        if segment_name == 'High':
            if demand_sensitivity > -0.5:
                return "Premium pricing - customers are price insensitive"
            else:
                return "Value-based pricing - justify premium with quality"
        
        elif segment_name == 'Low':
            if customer_count > 100:
                return "Volume pricing - focus on market penetration"
            else:
                return "Competitive pricing - attract price-sensitive customers"
        
        elif segment_name in ['Mid', 'Mid-High', 'Low-Mid']:
            if abs(demand_sensitivity) > 1.5:
                return "Dynamic pricing - demand is elastic, optimize frequently"
            else:
                return "Stable pricing - maintain consistent pricing strategy"
        
        return "Monitor and adjust - insufficient data for specific strategy"
    
    async def get_shap_explanation(self, 
                                 product_data: Dict[str, Any],
                                 prediction_type: str = 'price_optimization') -> Dict[str, Any]:
        """Get SHAP explanation for a prediction"""
        
        try:
            if 'price_model' not in self.shap_explainers:
                raise ValueError("SHAP explainer not available")
            
            explainer = self.shap_explainers['price_model']
            scaler = self.scalers['price_model']
            
            # Create feature vector
            current_price = product_data.get('price', 100.0)
            feature_vector = self._create_feature_vector(product_data, current_price)
            feature_vector_scaled = scaler.transform([feature_vector])
            
            # Calculate SHAP values
            shap_values = explainer.shap_values(feature_vector_scaled)
            
            # Create explanation
            explanation = {
                'prediction_type': prediction_type,
                'base_value': explainer.expected_value,
                'prediction': self.models['price_model'].predict(feature_vector_scaled)[0],
                'feature_contributions': {},
                'top_positive_features': [],
                'top_negative_features': [],
                'feature_values': dict(zip(self.feature_names, feature_vector))
            }
            
            # Feature contributions
            for i, (feature_name, shap_value) in enumerate(zip(self.feature_names, shap_values[0])):
                explanation['feature_contributions'][feature_name] = {
                    'shap_value': float(shap_value),
                    'feature_value': float(feature_vector[i]),
                    'contribution_percent': float(shap_value / sum(np.abs(shap_values[0])) * 100)
                }
            
            # Sort features by impact
            sorted_features = sorted(
                explanation['feature_contributions'].items(),
                key=lambda x: abs(x[1]['shap_value']),
                reverse=True
            )
            
            # Top positive and negative contributors
            for feature_name, contrib in sorted_features:
                if contrib['shap_value'] > 0:
                    explanation['top_positive_features'].append({
                        'feature': feature_name,
                        'impact': contrib['shap_value'],
                        'value': contrib['feature_value']
                    })
                else:
                    explanation['top_negative_features'].append({
                        'feature': feature_name,
                        'impact': contrib['shap_value'],
                        'value': contrib['feature_value']
                    })
            
            # Limit to top 5 each
            explanation['top_positive_features'] = explanation['top_positive_features'][:5]
            explanation['top_negative_features'] = explanation['top_negative_features'][:5]
            
            return explanation
            
        except Exception as e:
            self.logger.error(f"Error generating SHAP explanation: {str(e)}")
            raise

# Global instance
price_optimization_service = PriceOptimizationService()