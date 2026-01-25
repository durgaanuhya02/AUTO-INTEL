#!/usr/bin/env python3
"""
Debug Dashboard Response
"""
import asyncio
import aiohttp
import json

async def debug_dashboard_response():
    """Debug the dashboard API response"""
    print("🔍 DEBUGGING DASHBOARD API RESPONSE")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8001/api/v1/dashboard") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    print("📊 RESPONSE STRUCTURE:")
                    print(f"   Keys: {list(data.keys())}")
                    
                    if 'alerts' in data:
                        alerts = data['alerts']
                        print(f"\n🚨 ALERTS SECTION:")
                        print(f"   Type: {type(alerts)}")
                        print(f"   Length: {len(alerts)}")
                        if alerts:
                            print(f"   Sample alert: {alerts[0]}")
                        else:
                            print("   No alerts in response")
                    else:
                        print("\n❌ No 'alerts' key in response")
                    
                    if 'recent_decisions' in data:
                        decisions = data['recent_decisions']
                        print(f"\n💡 DECISIONS SECTION:")
                        print(f"   Type: {type(decisions)}")
                        print(f"   Length: {len(decisions)}")
                        if decisions:
                            print(f"   Sample decision: {decisions[0]}")
                        else:
                            print("   No decisions in response")
                    else:
                        print("\n❌ No 'recent_decisions' key in response")
                    
                    # Check current metrics
                    if 'current_metrics' in data:
                        metrics = data['current_metrics']
                        print(f"\n📈 CURRENT METRICS:")
                        for key, value in metrics.items():
                            print(f"   {key}: {value}")
                    
                else:
                    print(f"❌ API Error: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    
        except Exception as e:
            print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_dashboard_response())