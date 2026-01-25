#!/usr/bin/env python3
"""
Test 30-second Real-time Updates
"""
import asyncio
import aiohttp
import json
from datetime import datetime

async def test_30_second_updates():
    """Test if values change over 30-second intervals"""
    print("🔄 TESTING 30-SECOND UPDATE CYCLES")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        print("📊 Collecting values over 90 seconds (3 update cycles)...")
        values_over_time = []
        
        # Collect 4 samples over 90 seconds (should see 3 updates)
        for i in range(4):
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
                            'satisfaction': metrics['customer_satisfaction'],
                            'growth': metrics['monthly_growth']
                        })
                        
                        print(f"   {timestamp}: Revenue=${metrics['revenue']:,.0f}, Orders={metrics['orders']:,}, Growth={metrics['monthly_growth']:+.1f}%")
                        
                        if i < 3:  # Wait 30 seconds between samples
                            print(f"   ⏳ Waiting 30 seconds for next update cycle...")
                            await asyncio.sleep(30)
                            
            except Exception as e:
                print(f"   Error: {e}")
        
        # Analyze changes
        if len(values_over_time) >= 2:
            print(f"\n📈 CHANGE ANALYSIS:")
            
            for i in range(1, len(values_over_time)):
                prev = values_over_time[i-1]
                curr = values_over_time[i]
                
                revenue_change = curr['revenue'] - prev['revenue']
                orders_change = curr['orders'] - prev['orders']
                satisfaction_change = curr['satisfaction'] - prev['satisfaction']
                
                print(f"   Update {i}: Revenue change: ${revenue_change:,.0f}, Orders change: {orders_change:,}")
                
                if abs(revenue_change) > 0 or abs(orders_change) > 0:
                    print(f"   ✅ Values changed in update cycle {i}")
                else:
                    print(f"   ❌ No change detected in update cycle {i}")
            
            # Overall assessment
            all_revenues = [v['revenue'] for v in values_over_time]
            all_orders = [v['orders'] for v in values_over_time]
            
            revenue_variation = max(all_revenues) - min(all_revenues)
            orders_variation = max(all_orders) - min(all_orders)
            
            print(f"\n🎯 OVERALL ASSESSMENT:")
            print(f"   Total revenue variation: ${revenue_variation:,.0f}")
            print(f"   Total orders variation: {orders_variation:,}")
            
            if revenue_variation > 0 or orders_variation > 0:
                print("   ✅ REAL-TIME UPDATES ARE WORKING!")
                print("   📊 Values are changing every 30 seconds as expected")
            else:
                print("   ❌ Real-time updates not working - values remain static")

if __name__ == "__main__":
    asyncio.run(test_30_second_updates())