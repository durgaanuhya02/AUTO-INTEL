import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
import logging
from typing import Dict, Any, List, Optional
import os

class OlistDataProcessor:
    def __init__(self, data_path: str = "data"):
        self.data_path = data_path
        self.logger = logging.getLogger("data_processor")
        self.datasets = {}
        self.processed_metrics = {}
        
    async def initialize(self):
        """Initialize and load all Olist datasets"""
        try:
            await self._load_datasets()
            await self._preprocess_data()
            self.logger.info("Data processor initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize data processor: {e}")
            raise
    
    async def _load_datasets(self):
        """Load all CSV files from the data directory"""
        dataset_files = {
            'customers': 'olist_customers_dataset.csv',
            'orders': 'olist_orders_dataset.csv',
            'order_items': 'olist_order_items_dataset.csv',
            'order_payments': 'olist_order_payments_dataset.csv',
            'order_reviews': 'olist_order_reviews_dataset.csv',
            'products': 'olist_products_dataset.csv',
            'sellers': 'olist_sellers_dataset.csv',
            'geolocation': 'olist_geolocation_dataset.csv',
            'category_translation': 'product_category_name_translation.csv'
        }
        
        for name, filename in dataset_files.items():
            file_path = os.path.join(self.data_path, filename)
            if os.path.exists(file_path):
                try:
                    self.datasets[name] = pd.read_csv(file_path)
                    self.logger.info(f"Loaded {name}: {len(self.datasets[name])} records")
                except Exception as e:
                    self.logger.error(f"Error loading {filename}: {e}")
            else:
                self.logger.warning(f"File not found: {file_path}")
    
    async def _preprocess_data(self):
        """Preprocess the data for real-time simulation"""
        if 'orders' not in self.datasets:
            self.logger.error("Orders dataset not found")
            return
        
        # Convert date columns
        orders_df = self.datasets['orders'].copy()
        date_columns = ['order_purchase_timestamp', 'order_approved_at', 
                       'order_delivered_carrier_date', 'order_delivered_customer_date', 
                       'order_estimated_delivery_date']
        
        for col in date_columns:
            if col in orders_df.columns:
                orders_df[col] = pd.to_datetime(orders_df[col], errors='coerce')
        
        # Merge with order items and payments for comprehensive data
        if 'order_items' in self.datasets and 'order_payments' in self.datasets:
            # Aggregate order items
            order_items_agg = self.datasets['order_items'].groupby('order_id').agg({
                'price': 'sum',
                'freight_value': 'sum',
                'order_item_id': 'count'
            }).rename(columns={'order_item_id': 'item_count'})
            
            # Aggregate payments
            payments_agg = self.datasets['order_payments'].groupby('order_id').agg({
                'payment_value': 'sum',
                'payment_installments': 'mean'
            })
            
            # Merge everything
            orders_df = orders_df.merge(order_items_agg, on='order_id', how='left')
            orders_df = orders_df.merge(payments_agg, on='order_id', how='left')
        
        # Add reviews if available
        if 'order_reviews' in self.datasets:
            reviews_agg = self.datasets['order_reviews'].groupby('order_id').agg({
                'review_score': 'mean'
            })
            orders_df = orders_df.merge(reviews_agg, on='order_id', how='left')
        
        self.datasets['processed_orders'] = orders_df
        self.logger.info(f"Preprocessed orders: {len(orders_df)} records")
    
    async def get_daily_metrics(self, target_date: datetime) -> Dict[str, float]:
        """Calculate business metrics for a specific date"""
        if 'processed_orders' not in self.datasets:
            return {}
        
        df = self.datasets['processed_orders']
        
        # Filter orders for the target date
        date_str = target_date.strftime('%Y-%m-%d')
        daily_orders = df[df['order_purchase_timestamp'].dt.strftime('%Y-%m-%d') == date_str]
        
        if len(daily_orders) == 0:
            return self._get_default_metrics()
        
        # Calculate metrics
        metrics = {}
        
        # Revenue
        metrics['revenue'] = daily_orders['payment_value'].sum() if 'payment_value' in daily_orders.columns else 0
        
        # Order count
        metrics['orders'] = len(daily_orders)
        
        # Average order value
        metrics['avg_order_value'] = metrics['revenue'] / metrics['orders'] if metrics['orders'] > 0 else 0
        
        # Customer satisfaction (from reviews)
        if 'review_score' in daily_orders.columns:
            metrics['customer_satisfaction'] = daily_orders['review_score'].mean()
        else:
            metrics['customer_satisfaction'] = 4.0  # Default
        
        # Delivery delay calculation
        delivered_orders = daily_orders.dropna(subset=['order_delivered_customer_date', 'order_estimated_delivery_date'])
        if len(delivered_orders) > 0:
            delivery_delays = (delivered_orders['order_delivered_customer_date'] - 
                             delivered_orders['order_estimated_delivery_date']).dt.days
            metrics['delivery_delay'] = delivery_delays.mean()
        else:
            metrics['delivery_delay'] = 2.0  # Default
        
        # Churn risk (simplified calculation based on review scores and delivery delays)
        churn_indicators = 0
        total_indicators = 0
        
        if 'review_score' in daily_orders.columns:
            low_satisfaction = (daily_orders['review_score'] < 3).sum()
            churn_indicators += low_satisfaction
            total_indicators += len(daily_orders.dropna(subset=['review_score']))
        
        if len(delivered_orders) > 0:
            late_deliveries = (delivery_delays > 5).sum()
            churn_indicators += late_deliveries
            total_indicators += len(delivered_orders)
        
        metrics['churn_risk'] = churn_indicators / total_indicators if total_indicators > 0 else 0.1
        
        return metrics
    
    def _get_default_metrics(self) -> Dict[str, float]:
        """Return default metrics when no data is available"""
        return {
            'revenue': 15000.0,
            'orders': 150,
            'avg_order_value': 100.0,
            'customer_satisfaction': 4.0,
            'delivery_delay': 2.0,
            'churn_risk': 0.15
        }
    
    async def simulate_real_time_stream(self, start_date: Optional[datetime] = None) -> Dict[str, float]:
        """Simulate real-time data stream by cycling through historical data"""
        if start_date is None:
            start_date = datetime(2017, 1, 1)  # Olist data starts around 2016-2017
        
        # Calculate which day we should simulate based on current time
        days_since_start = (datetime.utcnow() - start_date).days
        
        # Cycle through available data (assuming 2 years of data)
        cycle_day = days_since_start % 730  # 2 years
        target_date = start_date + timedelta(days=cycle_day)
        
        metrics = await self.get_daily_metrics(target_date)
        
        # Add some real-time variation to make it more realistic
        variation_factor = 1.0 + np.random.normal(0, 0.05)  # 5% random variation
        
        for key in ['revenue', 'orders', 'avg_order_value']:
            if key in metrics:
                metrics[key] *= variation_factor
        
        # Add time-of-day effects
        current_hour = datetime.utcnow().hour
        if 9 <= current_hour <= 17:  # Business hours
            metrics['revenue'] *= 1.2
            metrics['orders'] = int(metrics['orders'] * 1.2)
        elif 18 <= current_hour <= 22:  # Evening peak
            metrics['revenue'] *= 1.1
            metrics['orders'] = int(metrics['orders'] * 1.1)
        else:  # Night/early morning
            metrics['revenue'] *= 0.7
            metrics['orders'] = int(metrics['orders'] * 0.7)
        
        return metrics
    
    async def get_historical_trends(self, metric: str, days: int = 30) -> List[float]:
        """Get historical trend data for a specific metric"""
        if 'processed_orders' not in self.datasets:
            return [100.0] * days  # Default trend
        
        df = self.datasets['processed_orders']
        
        # Get the last N days of data
        end_date = df['order_purchase_timestamp'].max()
        start_date = end_date - timedelta(days=days)
        
        trend_data = []
        current_date = start_date
        
        while current_date <= end_date:
            daily_metrics = await self.get_daily_metrics(current_date)
            trend_data.append(daily_metrics.get(metric, 0))
            current_date += timedelta(days=1)
        
        # Pad with default values if not enough data
        while len(trend_data) < days:
            trend_data.insert(0, trend_data[0] if trend_data else 100.0)
        
        return trend_data[-days:]  # Return exactly the requested number of days
    
    async def detect_anomalies_in_data(self) -> List[Dict[str, Any]]:
        """Detect anomalies in the historical data"""
        anomalies = []
        
        if 'processed_orders' not in self.datasets:
            return anomalies
        
        df = self.datasets['processed_orders']
        
        # Group by date and calculate daily metrics
        df['date'] = df['order_purchase_timestamp'].dt.date
        daily_stats = df.groupby('date').agg({
            'payment_value': 'sum',
            'order_id': 'count',
            'review_score': 'mean'
        }).rename(columns={'order_id': 'order_count'})
        
        # Detect revenue anomalies
        revenue_mean = daily_stats['payment_value'].mean()
        revenue_std = daily_stats['payment_value'].std()
        
        revenue_anomalies = daily_stats[
            (daily_stats['payment_value'] < revenue_mean - 2 * revenue_std) |
            (daily_stats['payment_value'] > revenue_mean + 2 * revenue_std)
        ]
        
        for date, row in revenue_anomalies.iterrows():
            anomalies.append({
                'date': str(date),
                'metric': 'revenue',
                'value': row['payment_value'],
                'expected': revenue_mean,
                'type': 'high' if row['payment_value'] > revenue_mean else 'low'
            })
        
        return anomalies
    
    async def get_customer_segments(self) -> Dict[str, Any]:
        """Analyze customer segments from the data"""
        if 'customers' not in self.datasets or 'processed_orders' not in self.datasets:
            return {}
        
        customers_df = self.datasets['customers']
        orders_df = self.datasets['processed_orders']
        
        # Merge customer data with orders
        customer_orders = orders_df.merge(customers_df, on='customer_id', how='left')
        
        # Calculate customer metrics
        customer_metrics = customer_orders.groupby('customer_id').agg({
            'payment_value': ['sum', 'mean', 'count'],
            'review_score': 'mean'
        }).round(2)
        
        # Flatten column names
        customer_metrics.columns = ['total_spent', 'avg_order_value', 'order_count', 'avg_rating']
        
        # Segment customers
        segments = {
            'high_value': len(customer_metrics[customer_metrics['total_spent'] > customer_metrics['total_spent'].quantile(0.8)]),
            'medium_value': len(customer_metrics[
                (customer_metrics['total_spent'] > customer_metrics['total_spent'].quantile(0.4)) &
                (customer_metrics['total_spent'] <= customer_metrics['total_spent'].quantile(0.8))
            ]),
            'low_value': len(customer_metrics[customer_metrics['total_spent'] <= customer_metrics['total_spent'].quantile(0.4)]),
            'frequent_buyers': len(customer_metrics[customer_metrics['order_count'] > 2]),
            'at_risk': len(customer_metrics[customer_metrics['avg_rating'] < 3])
        }
        
        return segments

# Global data processor instance
data_processor = OlistDataProcessor()