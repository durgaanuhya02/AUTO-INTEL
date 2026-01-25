#!/usr/bin/env python3
"""
Test Real-time Updates
"""
import asyncio
import aiohttp
import json
from datetime import datetime

async def test_realtime_updates():
    """Test if real-time updates are working"""
    print("🔄 TESTING REAL-TIME UPDATES")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        print("📊 Collecting baseline values...")
        baseline_values = []
        
        # Collect 5 samples over 10 seconds
        for i in range(5):
            try:
                async with session.get("http://localhost:8001/api/v1/dashboard") as response:
                    if response.status == 200:
                        data = await response.json()
                        metrics = data['current_metrics']
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        
                        baseline_values.append({
                            'time': timestamp,
                            'revenue': metrics['revenue'],
                            'orders': metrics['orders'],
                            'satisfaction': metrics['customer_satisfaction'],
                            'growth': metrics['monthly_growth']
                        })
                        
                        print(f"   {timestamp}: Revenue=${metrics['revenue']:,.0f}, Orders={metrics['orders']:,}")
                        
                        if i < 4:
                            await asyncio.sleep(2)
                            
            except Exception as e:
                print(f"   Error: {e}")
        
        # Check for variations
        if len(baseline_values) >= 2:
            revenue_values = [v['revenue'] for v in baseline_values]
            orders_values = [v['orders'] for v in baseline_values]
            satisfaction_values = [v['satisfaction'] for v in baseline_values]
            
            revenue_variation = max(revenue_values) - min(revenue_values)
            orders_variation = max(orders_values) - min(orders_values)
            satisfaction_variation = max(satisfaction_values) - min(satisfaction_values)
            
            print(f"\n📈 VARIATION ANALYSIS:")
            print(f"   Revenue variation: ${revenue_variation:,.0f}")
            print(f"   Orders variation: {orders_variation:,}")
            print(f"   Satisfaction variation: {satisfaction_variation:.3f}")
            
            if revenue_variation > 0 or orders_variation > 0 or satisfaction_variation > 0:
                print("   ✅ REAL-TIME UPDATES WORKING!")
            else:
                print("   ❌ Values are still static")
        
        # Test ML insights
        print(f"\n🤖 TESTING ML INSIGHTS:")
        try:
            async with session.get("http://localhost:8001/api/v1/analytics/advanced") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    ml_insights = data.get('ml_insights', [])
                    anomalies = data.get('anomalies', [])
                    recommendations = data.get('recommendations', [])
                    
                    print(f"   ML Insights: {len(ml_insights)}")
                    print(f"   Anomalies: {len(anomalies)}")
                    print(f"   Recommendations: {len(recommendations)}")
                    
                    if ml_insights:
                        print("   ✅ ML INSIGHTS WORKING!")
                        for insight in ml_insights[:2]:
                            print(f"      - {insight.get('metric', 'Unknown')}: {insight.get('trend', 'N/A')} trend")
                    else:
                        print("   ❌ No ML insights generated")
                        
        except Exception as e:
            print(f"   Error: {e}")
        
        print(f"\n⏰ Waiting for next background update cycle (30 seconds)...")
        print("   The system updates every 30 seconds with new simulated values")
        print("   Check the dashboard in your browser to see live updates!")

if __name__ == "__main__":
    asyncio.run(test_realtime_updates())