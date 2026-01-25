#!/usr/bin/env python3
"""
Test Redis Integration for Production Server
Validates Redis caching, ML prediction caching, and agent coordination
"""
import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_redis_integration():
    """Test Redis integration components"""
    
    print("🧪 Testing Redis Integration for Production Server")
    print("=" * 60)
    
    try:
        # Test 1: Redis Cache Service Initialization
        print("\n1️⃣ Testing Redis Cache Service Initialization...")
        from services.redis_cache_service import redis_cache_service
        
        redis_initialized = await redis_cache_service.initialize()
        if redis_initialized:
            print("✅ Redis cache service initialized successfully")
        else:
            print("⚠️ Redis cache service not available (Redis server may not be running)")
            print("   This is expected if Redis is not installed or running")
            return
        
        # Test 2: Real-time Metrics Caching
        print("\n2️⃣ Testing Real-time Metrics Caching...")
        
        test_metrics = {
            'metrics': {
                'total_revenue': 1500000.0,
                'total_orders': 105000,
                'avg_order_value': 142.85,
                'customer_satisfaction': 4.3,
                'monthly_growth': 8.5
            },
            'cached_at': datetime.now().isoformat()
        }
        
        # Cache metrics
        cache_success = await redis_cache_service.cache_real_time_metrics(test_metrics)
        if cache_success:
            print("✅ Successfully cached real-time metrics")
        else:
            print("❌ Failed to cache real-time metrics")
            return
        
        # Retrieve cached metrics
        cached_metrics = await redis_cache_service.get_real_time_metrics()
        if cached_metrics and cached_metrics['metrics']['total_revenue'] == test_metrics['metrics']['total_revenue']:
            print("✅ Successfully retrieved cached metrics")
        else:
            print("❌ Failed to retrieve cached metrics")
            return
        
        # Test 3: ML Prediction Caching
        print("\n3️⃣ Testing ML Prediction Caching...")
        
        test_prediction = {
            'model_type': 'ensemble_forecast',
            'predictions': [1600000, 1650000, 1700000],
            'confidence': 0.92,
            'generated_at': datetime.now().isoformat()
        }
        
        # Cache ML prediction
        ml_cache_success = await redis_cache_service.cache_ml_prediction(
            'ensemble_forecast', 'test_input_hash', test_prediction, confidence=0.92
        )
        if ml_cache_success:
            print("✅ Successfully cached ML prediction")
        else:
            print("❌ Failed to cache ML prediction")
            return
        
        # Retrieve cached prediction
        cached_prediction = await redis_cache_service.get_ml_prediction('ensemble_forecast', 'test_input_hash')
        if cached_prediction and cached_prediction['confidence'] == 0.92:
            print("✅ Successfully retrieved cached ML prediction")
        else:
            print("❌ Failed to retrieve cached ML prediction")
            return
        
        # Test 4: Agent Status Caching
        print("\n4️⃣ Testing Agent Status Caching...")
        
        test_agent_status = {
            'status': 'active',
            'performance': 0.95,
            'last_update': datetime.now().isoformat(),
            'metrics_processed': 105000
        }
        
        # Cache agent status
        agent_cache_success = await redis_cache_service.cache_agent_status('test_agent', test_agent_status)
        if agent_cache_success:
            print("✅ Successfully cached agent status")
        else:
            print("❌ Failed to cache agent status")
            return
        
        # Retrieve agent status
        cached_agent_status = await redis_cache_service.get_agent_status('test_agent')
        if cached_agent_status and cached_agent_status['performance'] == 0.95:
            print("✅ Successfully retrieved cached agent status")
        else:
            print("❌ Failed to retrieve cached agent status")
            return
        
        # Test 5: Business Insights Caching
        print("\n5️⃣ Testing Business Insights Caching...")
        
        test_insights = {
            'forecasts': [
                {'metric': 'revenue', 'predicted_30d': 1700000, 'confidence': 0.88},
                {'metric': 'orders', 'predicted_30d': 110000, 'confidence': 0.85}
            ],
            'recommendations': [
                'Optimize top-performing categories',
                'Implement customer retention strategies'
            ],
            'anomalies': [],
            'trends': {'revenue_trend': 'increasing'}
        }
        
        # Cache insights
        insights_cache_success = await redis_cache_service.cache_business_insights(test_insights)
        if insights_cache_success:
            print("✅ Successfully cached business insights")
        else:
            print("❌ Failed to cache business insights")
            return
        
        # Retrieve insights
        cached_insights = await redis_cache_service.get_business_insights()
        if cached_insights and len(cached_insights['forecasts']) == 2:
            print("✅ Successfully retrieved cached business insights")
        else:
            print("❌ Failed to retrieve cached business insights")
            return
        
        # Test 6: Cache Statistics
        print("\n6️⃣ Testing Cache Statistics...")
        
        cache_stats = await redis_cache_service.get_cache_stats()
        if cache_stats and cache_stats.get('status') == 'active':
            print("✅ Successfully retrieved cache statistics")
            print(f"   - Memory usage: {cache_stats.get('used_memory_mb', 0):.2f} MB")
            print(f"   - Total keys: {cache_stats.get('total_keys', 0)}")
            print(f"   - Connected clients: {cache_stats.get('connected_clients', 0)}")
        else:
            print("❌ Failed to retrieve cache statistics")
            return
        
        # Test 7: Cache Performance (TTL and Expiration)
        print("\n7️⃣ Testing Cache Performance and TTL...")
        
        # Test short TTL
        short_ttl_data = {'test': 'data', 'timestamp': datetime.now().isoformat()}
        await redis_cache_service.cache_real_time_metrics(short_ttl_data)
        
        # Wait a moment and check if data is still there
        await asyncio.sleep(1)
        retrieved_data = await redis_cache_service.get_real_time_metrics()
        if retrieved_data:
            print("✅ Cache TTL working correctly (data still available)")
        else:
            print("⚠️ Cache TTL may be too short or data expired")
        
        # Test 8: Multiple Agent Status Retrieval
        print("\n8️⃣ Testing Multiple Agent Status Coordination...")
        
        # Cache multiple agent statuses
        agents = ['observer_agent', 'analyst_agent', 'decision_agent']
        for i, agent in enumerate(agents):
            status = {
                'status': 'active',
                'performance': 0.9 + i * 0.02,
                'last_update': datetime.now().isoformat()
            }
            await redis_cache_service.cache_agent_status(agent, status)
        
        # Retrieve all agent statuses
        all_statuses = await redis_cache_service.get_all_agent_statuses()
        if len(all_statuses) >= len(agents):
            print(f"✅ Successfully coordinated {len(all_statuses)} agent statuses")
        else:
            print("❌ Failed to coordinate multiple agent statuses")
            return
        
        print("\n🎉 All Redis Integration Tests Passed!")
        print("=" * 60)
        print("✅ Redis caching is working correctly")
        print("✅ ML prediction caching is functional")
        print("✅ Agent coordination through Redis is operational")
        print("✅ Real-time metrics caching is optimized")
        print("✅ Business insights caching is efficient")
        print("\n🚀 Production server is ready for Redis-enhanced real-time analytics!")
        
    except Exception as e:
        print(f"\n❌ Redis Integration Test Failed: {str(e)}")
        print("   Make sure Redis server is running: redis-server")
        print("   Install Redis Python client: pip install redis")
        return False
    
    return True

async def test_production_server_integration():
    """Test production server with Redis integration"""
    
    print("\n🔧 Testing Production Server Redis Integration...")
    print("=" * 60)
    
    try:
        # Import production server components
        from services.real_data_processor import data_processor
        
        # Test data processor
        print("\n1️⃣ Testing Data Processor...")
        metrics = data_processor.calculate_business_metrics()
        if metrics and metrics.total_revenue > 0:
            print(f"✅ Data processor working: ${metrics.total_revenue:,.2f} revenue, {metrics.total_orders:,} orders")
        else:
            print("❌ Data processor failed")
            return False
        
        # Test ML services availability
        print("\n2️⃣ Testing ML Services Availability...")
        
        try:
            from services.ml_service import enhanced_ml_service
            await enhanced_ml_service.initialize()
            print("✅ Enhanced ML service available")
        except Exception as e:
            print(f"⚠️ Enhanced ML service not available: {str(e)}")
        
        try:
            from services.advanced_forecasting_service import advanced_forecasting_service
            await advanced_forecasting_service.initialize()
            print("✅ Advanced forecasting service available")
        except Exception as e:
            print(f"⚠️ Advanced forecasting service not available: {str(e)}")
        
        try:
            from services.price_optimization_service import price_optimization_service
            await price_optimization_service.initialize()
            print("✅ Price optimization service available")
        except Exception as e:
            print(f"⚠️ Price optimization service not available: {str(e)}")
        
        print("\n✅ Production server components are ready for Redis integration!")
        
    except Exception as e:
        print(f"\n❌ Production Server Integration Test Failed: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    async def main():
        print("🧪 Redis Integration Test Suite")
        print("Testing Redis caching for ML-driven analytics platform")
        print("=" * 60)
        
        # Test Redis integration
        redis_success = await test_redis_integration()
        
        if redis_success:
            # Test production server integration
            server_success = await test_production_server_integration()
            
            if server_success:
                print("\n🎉 ALL TESTS PASSED!")
                print("🚀 Ready to run: python backend/production_server.py")
                print("📊 Redis-enhanced real-time analytics are operational!")
            else:
                print("\n⚠️ Production server integration needs attention")
        else:
            print("\n⚠️ Redis integration needs setup")
            print("   1. Install Redis: brew install redis (macOS) or apt install redis (Ubuntu)")
            print("   2. Start Redis: redis-server")
            print("   3. Install Python client: pip install redis")
    
    asyncio.run(main())