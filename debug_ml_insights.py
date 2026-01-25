#!/usr/bin/env python3
"""
Debug ML Insights
"""
import asyncio
import aiohttp
import json

async def debug_ml_insights():
    """Debug ML insights generation"""
    print("🔍 DEBUGGING ML INSIGHTS")
    print("=" * 40)
    
    async with aiohttp.ClientSession() as session:
        
        # Test advanced analytics
        try:
            async with session.get("http://localhost:8001/api/v1/analytics/advanced") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    print("📊 Advanced Analytics Response:")
                    print(f"   Status: {data.get('status')}")
                    print(f"   ML Insights: {len(data.get('ml_insights', []))}")
                    print(f"   Anomalies: {len(data.get('anomalies', []))}")
                    print(f"   Recommendations: {len(data.get('recommendations', []))}")
                    
                    # Print actual content
                    ml_insights = data.get('ml_insights', [])
                    if ml_insights:
                        print("\n🔮 ML Insights Details:")
                        for i, insight in enumerate(ml_insights):
                            print(f"   {i+1}. {insight}")
                    else:
                        print("\n❌ No ML insights found")
                    
                    anomalies = data.get('anomalies', [])
                    if anomalies:
                        print("\n🚨 Anomalies Details:")
                        for i, anomaly in enumerate(anomalies):
                            print(f"   {i+1}. {anomaly}")
                    else:
                        print("\n❌ No anomalies found")
                    
                    recommendations = data.get('recommendations', [])
                    if recommendations:
                        print("\n💡 Recommendations Details:")
                        for i, rec in enumerate(recommendations):
                            print(f"   {i+1}. {rec}")
                    else:
                        print("\n❌ No recommendations found")
                        
                else:
                    print(f"❌ API returned {response.status}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_ml_insights())