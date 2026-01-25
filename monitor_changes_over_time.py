#!/usr/bin/env python3
"""
Monitor Changes Over Time
"""
import asyncio
import aiohttp
import json
from datetime import datetime

async def monitor_changes_over_time():
    """Monitor how alerts and decisions change over multiple update cycles"""
    print("🔄 MONITORING CHANGES OVER TIME")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        
        samples = []
        
        for cycle in range(4):  # Monitor 4 update cycles (2 minutes)
            try:
                async with session.get("http://localhost:8001/api/v1/dashboard") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        sample = {
                            'cycle': cycle + 1,
                            'time': datetime.now().strftime("%H:%M:%S"),
                            'metrics': data['current_metrics'],
                            'alerts': data.get('alerts', []),
                            'decisions': data.get('recent_decisions', [])
                        }
                        samples.append(sample)
                        
                        print(f"\n📊 CYCLE {cycle + 1} - {sample['time']}")
                        print("-" * 40)
                        
                        metrics = sample['metrics']
                        print(f"💰 Revenue: ${metrics['revenue']:,.0f}")
                        print(f"📦 Orders: {metrics['orders']:,}")
                        print(f"📈 Growth: {metrics['monthly_growth']:+.1f}%")
                        print(f"⭐ Satisfaction: {metrics['customer_satisfaction']:.1f}/5.0")
                        
                        # Show alerts with IDs
                        alerts = sample['alerts']
                        print(f"\n🚨 Alerts ({len(alerts)}):")
                        if alerts:
                            for alert in alerts:
                                print(f"   ID:{alert.get('id', 'N/A')} - {alert.get('title', 'Unknown')}")
                                print(f"   Value: {alert.get('metric_value', 'N/A')} | Threshold: {alert.get('threshold', 'N/A')}")
                        else:
                            print("   None")
                        
                        # Show decisions with IDs
                        decisions = sample['decisions']
                        print(f"\n💡 Decisions ({len(decisions)}):")
                        if decisions:
                            for decision in decisions:
                                print(f"   ID:{decision.get('id', 'N/A')} - {decision.get('title', 'Unknown')}")
                                print(f"   Impact: ${decision.get('financial_impact', 0):,.0f}")
                        else:
                            print("   None")
                        
                        if cycle < 3:  # Wait for next cycle
                            print(f"\n⏳ Waiting 35 seconds for next update...")
                            await asyncio.sleep(35)
                            
            except Exception as e:
                print(f"❌ Error in cycle {cycle + 1}: {e}")
        
        # Analyze changes
        print(f"\n📈 CHANGE ANALYSIS")
        print("=" * 60)
        
        if len(samples) >= 2:
            revenue_changes = []
            order_changes = []
            alert_changes = []
            decision_changes = []
            
            for i in range(1, len(samples)):
                prev = samples[i-1]
                curr = samples[i]
                
                # Track metric changes
                revenue_change = curr['metrics']['revenue'] - prev['metrics']['revenue']
                order_change = curr['metrics']['orders'] - prev['metrics']['orders']
                
                revenue_changes.append(revenue_change)
                order_changes.append(order_change)
                
                # Track alert changes
                prev_alert_titles = {alert.get('title') for alert in prev['alerts']}
                curr_alert_titles = {alert.get('title') for alert in curr['alerts']}
                
                alert_change = len(prev_alert_titles.symmetric_difference(curr_alert_titles))
                alert_changes.append(alert_change)
                
                # Track decision changes
                prev_decision_titles = {decision.get('title') for decision in prev['decisions']}
                curr_decision_titles = {decision.get('title') for decision in curr['decisions']}
                
                decision_change = len(prev_decision_titles.symmetric_difference(curr_decision_titles))
                decision_changes.append(decision_change)
                
                print(f"Cycle {i} → {i+1}:")
                print(f"   Revenue change: ${revenue_change:,.0f}")
                print(f"   Order change: {order_change:,}")
                print(f"   Alert changes: {alert_change}")
                print(f"   Decision changes: {decision_change}")
                print()
            
            # Summary
            total_revenue_variation = max([s['metrics']['revenue'] for s in samples]) - min([s['metrics']['revenue'] for s in samples])
            total_order_variation = max([s['metrics']['orders'] for s in samples]) - min([s['metrics']['orders'] for s in samples])
            total_alert_changes = sum(alert_changes)
            total_decision_changes = sum(decision_changes)
            
            print(f"🎯 SUMMARY:")
            print(f"   Total revenue variation: ${total_revenue_variation:,.0f}")
            print(f"   Total order variation: {total_order_variation:,}")
            print(f"   Total alert changes: {total_alert_changes}")
            print(f"   Total decision changes: {total_decision_changes}")
            
            if total_revenue_variation > 100000 or total_order_variation > 1000:
                print(f"   ✅ Metrics are changing significantly")
                if total_alert_changes == 0 and total_decision_changes == 0:
                    print(f"   ❌ PROBLEM: Alerts and decisions are NOT changing despite metric changes")
                    print(f"   🔧 ISSUE: Alert/decision logic may be too static or thresholds too wide")
                else:
                    print(f"   ✅ Alerts and decisions are responding to changes")
            else:
                print(f"   ⚠️  Metric changes are small - may not trigger alert/decision changes")

if __name__ == "__main__":
    asyncio.run(monitor_changes_over_time())