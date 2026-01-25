#!/usr/bin/env python3
"""
Diagnose ML System and Time Series Issues
"""
import asyncio
import aiohttp
import json
from datetime import datetime

async def diagnose_ml_system():
    """Diagnose the ML system and time series functionality"""
    print("🔍 DIAGNOSING ML SYSTEM AND TIME SERIES")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Check if values change over time
        print("\n1️⃣  TESTING VALUE CHANGES OVER TIME")
        print("-" * 40)
        
        values_over_time = []
        for i in range(3):
            try:
                async with session.get("http://localhost:8001/api/v1/dashboard") as response:
                    if response.status == 200:
                        data = await response.json()
                        metrics = data['current_metrics']
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        
                        values_over_time.append({
                            'time': timestamp,
                            'revenue': metrics['revenue'],
                            'orders': metrics['orders'],
                            'growth': metrics['monthly_growth']
                        })
                        
                        print(f"   {timestamp}: Revenue=${metrics['revenue']:,.0f}, Orders={metrics['orders']:,}, Growth={metrics['monthly_growth']:+.1f}%")
                        
                        if i < 2:  # Wait between calls
                            await asyncio.sleep(2)
                            
            except Exception as e:
                print(f"   Error: {e}")
        
        # Check if values are changing
        if len(values_over_time) >= 2:
            revenue_changed = values_over_time[0]['revenue'] != values_over_time[-1]['revenue']
            orders_changed = values_over_time[0]['orders'] != values_over_time[-1]['orders']
            
            if revenue_changed or orders_changed:
                print("   ✅ Values are changing over time (GOOD)")
            else:
                print("   ❌ Values are STATIC - not updating (PROBLEM)")
        
        # Test 2: Check time series data
        print("\n2️⃣  TESTING TIME SERIES DATA")
        print("-" * 40)
        
        try:
            async with session.get("http://localhost:8001/api/v1/trends/revenue") as response:
                if response.status == 200:
                    data = await response.json()
                    trend_data = data.get('data', [])
                    print(f"   Revenue trend points: {len(trend_data)}")
                    
                    if trend_data:
                        print(f"   Date range: {trend_data[0]['date']} to {trend_data[-1]['date']}")
                        values = [point['value'] for point in trend_data[-5:]]
                        print(f"   Last 5 values: {values}")
                        
                        # Check if values vary
                        unique_values = len(set(values))
                        if unique_values > 1:
                            print("   ✅ Time series has variation (GOOD)")
                        else:
                            print("   ❌ Time series values are identical (PROBLEM)")
                    else:
                        print("   ❌ No time series data available")
                else:
                    print(f"   ❌ Time series API returned {response.status}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 3: Check ML service
        print("\n3️⃣  TESTING ML SERVICE")
        print("-" * 40)
        
        try:
            async with session.get("http://localhost:8001/api/v1/analytics/advanced") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ML Analytics status: {data.get('status', 'unknown')}")
                    
                    analytics = data.get('advanced_analytics', {})
                    forecasts = analytics.get('forecasts', [])
                    anomalies = analytics.get('anomalies', [])
                    
                    print(f"   Forecasts available: {len(forecasts)}")
                    print(f"   Anomalies detected: {len(anomalies)}")
                    
                    if len(forecasts) == 0 and len(anomalies) == 0:
                        print("   ❌ ML service not generating insights (PROBLEM)")
                    else:
                        print("   ✅ ML service generating insights (GOOD)")
                else:
                    print(f"   ❌ ML Analytics API returned {response.status}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 4: Check real-time updates
        print("\n4️⃣  TESTING REAL-TIME UPDATES")
        print("-" * 40)
        
        try:
            async with session.get("http://localhost:8001/api/v1/analytics/real-time") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    revenue_analytics = data.get('revenue_analytics', {})
                    forecast = revenue_analytics.get('forecast', {})
                    
                    print(f"   Real-time revenue: ${revenue_analytics.get('total_revenue', 0):,.0f}")
                    print(f"   Growth rate: {revenue_analytics.get('growth_rate', 0):+.1f}%")
                    print(f"   Next month forecast: ${forecast.get('next_month', 0):,.0f}")
                    print(f"   Forecast confidence: {forecast.get('confidence', 0):.1%}")
                    
                    if forecast.get('next_month', 0) > 0:
                        print("   ✅ Real-time forecasting working (GOOD)")
                    else:
                        print("   ❌ Real-time forecasting not working (PROBLEM)")
                else:
                    print(f"   ❌ Real-time API returned {response.status}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 5: Check forecasting service
        print("\n5️⃣  TESTING FORECASTING SERVICE")
        print("-" * 40)
        
        try:
            async with session.get("http://localhost:8001/api/v1/analytics/forecasts/advanced") as response:
                if response.status == 200:
                    data = await response.json()
                    forecasts = data.get('forecasts', {})
                    
                    revenue_forecast = forecasts.get('revenue_forecast')
                    orders_forecast = forecasts.get('orders_forecast')
                    
                    if revenue_forecast:
                        print(f"   Revenue forecast: ${revenue_forecast['current']:,.0f} → ${revenue_forecast['predicted_30d']:,.0f}")
                        print(f"   Revenue trend: {revenue_forecast['trend']}")
                        print(f"   Revenue confidence: {revenue_forecast['confidence']:.1%}")
                    
                    if orders_forecast:
                        print(f"   Orders forecast: {orders_forecast['current']:,.0f} → {orders_forecast['predicted_30d']:,.0f}")
                        print(f"   Orders trend: {orders_forecast['trend']}")
                        print(f"   Orders confidence: {orders_forecast['confidence']:.1%}")
                    
                    if revenue_forecast and orders_forecast:
                        print("   ✅ Advanced forecasting working (GOOD)")
                    else:
                        print("   ❌ Advanced forecasting incomplete (PROBLEM)")
                else:
                    print(f"   ❌ Forecasting API returned {response.status}")
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSIS SUMMARY")
    print("=" * 60)
    print("Issues to check:")
    print("1. Are dashboard values updating every 30 seconds?")
    print("2. Does time series data show realistic variation?")
    print("3. Are ML models generating insights and predictions?")
    print("4. Is real-time data processing working?")
    print("5. Are forecasts using actual time-series patterns?")

if __name__ == "__main__":
    asyncio.run(diagnose_ml_system())