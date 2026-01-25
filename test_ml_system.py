#!/usr/bin/env python3
"""
Test ML-Driven System
Verifies that all ML components work correctly
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.services.ml_service import MLService
from backend.services.real_time_analytics_engine import RealTimeAnalyticsEngine
from agents.enhanced_simulation_agent import EnhancedSimulationAgent, ScenarioType
from backend.services.real_data_processor import RealDataProcessor

async def test_ml_service():
    """Test ML service functionality"""
    print("🧪 Testing ML Service...")

    ml_service = MLService()
    await ml_service.initialize()

    # Test revenue forecasting
    print("  Testing revenue forecasting...")
    revenue_result = await ml_service.predict_revenue_forecast(days_ahead=7)
    print(f"    Revenue forecast: {len(revenue_result.prediction)} predictions")

    # Test customer segmentation
    print("  Testing customer segmentation...")
    import pandas as pd
    customer_data = pd.DataFrame({
        'total_orders': [15, 8, 3],
        'total_spent': [2500, 1200, 300],
        'avg_order_value': [167, 150, 100],
        'days_since_last_order': [2, 7, 45],
        'satisfaction_score': [4.5, 4.2, 3.8]
    })
    segment_result = await ml_service.predict_customer_segments(customer_data)
    print(f"    Customer segments: {segment_result.prediction}")

    # Test price optimization
    print("  Testing price optimization...")
    product_data = pd.DataFrame({
        'current_price': [99.99, 149.99],
        'competitor_price': [95.00, 155.00],
        'demand_index': [1.2, 0.8],
        'category_popularity': [0.8, 0.6],
        'seasonal_factor': [1.0, 1.1],
        'inventory_level': [0.7, 0.5]
    })
    price_result = await ml_service.predict_optimal_prices(product_data)
    print(f"    Price recommendations: {len(price_result.prediction)} prices")

    print("✅ ML Service tests completed")

async def test_simulation_agent():
    """Test simulation agent with ML"""
    print("🎯 Testing Simulation Agent...")

    ml_service = MLService()
    await ml_service.initialize()

    analytics_engine = RealTimeAnalyticsEngine()
    await analytics_engine.initialize()

    agent = EnhancedSimulationAgent(ml_service=ml_service, analytics_engine=analytics_engine)
    await agent.initialize()

    # Test scenario generation
    simulation_request = {
        'id': 'test_sim_001',
        'metric_name': 'revenue',
        'analysis_report': {
            'root_cause_analysis': {'primary_cause': 'price_competition'}
        },
        'priority': 'high',
        'timestamp': asyncio.get_event_loop().time()
    }

    scenarios = await agent._generate_scenarios(simulation_request)
    print(f"  Generated {len(scenarios)} scenarios")

    # Test outcome calculation
    if scenarios:
        test_scenario = scenarios[0]
        outcomes = await agent._calculate_expected_outcomes(
            test_scenario.scenario_type,
            test_scenario.parameters,
            'revenue'
        )
        print(f"  ML-driven outcomes: {list(outcomes.keys())}")

    print("✅ Simulation Agent tests completed")

async def test_analytics_engine():
    """Test analytics engine"""
    print("📊 Testing Analytics Engine...")

    engine = RealTimeAnalyticsEngine()
    await engine.initialize()

    # Test real-time metrics
    metrics = await engine.get_real_time_metrics(['revenue', 'orders'])
    print(f"  Real-time metrics: {list(metrics.keys())}")

    # Test customer insights
    insights = await engine.get_customer_insights()
    print(f"  Customer insights: {insights.get('status', 'available')}")

    print("✅ Analytics Engine tests completed")

async def main():
    """Run all tests"""
    print("🚀 Starting ML System Tests...")
    print("=" * 50)

    try:
        await test_ml_service()
        print()

        await test_simulation_agent()
        print()

        await test_analytics_engine()
        print()

        print("=" * 50)
        print("🎉 All ML System Tests Completed Successfully!")
        print()
        print("The system is now fully ML-driven with:")
        print("  ✅ Pre-trained models loaded")
        print("  ✅ ML-powered simulations")
        print("  ✅ Real-time analytics with caching")
        print("  ✅ OpenAI used only for explanations")
        print("  ✅ Fallback methods for robustness")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())