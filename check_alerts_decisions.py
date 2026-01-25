#!/usr/bin/env python3
"""
Check Current Alerts and Decisions
"""
import asyncio
import aiohttp
import json

async def check_alerts_decisions():
    """Check current alerts and decisions"""
    print("🚨 CHECKING CURRENT ALERTS AND DECISIONS")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8001/api/v1/dashboard") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Show current metrics
                    metrics = data['current_metrics']
                    print("📊 CURRENT METRICS:")
                    print(f"   💰 Revenue: ${metrics['revenue']:,.0f}")
                    print(f"   📦 Orders: {metrics['orders']:,}")
                    print(f"   📈 Growth: {metrics['monthly_growth']:+.1f}%")
                    print(f"   ⭐ Satisfaction: {metrics['customer_satisfaction']:.1f}/5.0")
                    print(f"   💳 AOV: ${metrics['avg_order_value']:.2f}")
                    
                    # Show alerts
                    alerts = data.get('alerts', [])
                    print(f"\n🚨 ALERTS ({len(alerts)}):")
                    if alerts:
                        for i, alert in enumerate(alerts, 1):
                            severity_icon = {
                                'critical': '🔴',
                                'high': '🟠', 
                                'medium': '🟡',
                                'low': '🟢'
                            }.get(alert.get('severity', 'medium'), '🔵')
                            
                            print(f"   {i}. {severity_icon} {alert.get('title', 'Unknown')}")
                            print(f"      Message: {alert.get('message', 'No message')}")
                            print(f"      Type: {alert.get('type', 'unknown')} | Severity: {alert.get('severity', 'unknown')}")
                            if 'metric_value' in alert:
                                print(f"      Metric Value: {alert['metric_value']} | Threshold: {alert.get('threshold', 'N/A')}")
                            print()
                    else:
                        print("   No alerts currently active")
                    
                    # Show decisions
                    decisions = data.get('recent_decisions', [])
                    print(f"💡 DECISIONS ({len(decisions)}):")
                    if decisions:
                        for i, decision in enumerate(decisions, 1):
                            priority_icon = {
                                'critical': '🔴',
                                'high': '🟠',
                                'medium': '🟡',
                                'low': '🟢'
                            }.get(decision.get('priority', 'medium'), '🔵')
                            
                            print(f"   {i}. {priority_icon} {decision.get('title', 'Unknown Decision')}")
                            print(f"      Description: {decision.get('description', 'No description')}")
                            print(f"      Status: {decision.get('status', 'unknown')} | Priority: {decision.get('priority', 'unknown')}")
                            print(f"      Financial Impact: ${decision.get('financial_impact', 0):,.0f}")
                            print(f"      Confidence: {decision.get('confidence_score', 0):.1%} | Category: {decision.get('category', 'unknown')}")
                            print(f"      Reasoning: {decision.get('reasoning', 'No reasoning provided')}")
                            print()
                    else:
                        print("   No decisions currently available")
                    
                    # Analysis
                    print("🔍 ANALYSIS:")
                    if metrics['monthly_growth'] < -20:
                        print("   📉 Critical revenue decline should trigger emergency decisions")
                    elif metrics['monthly_growth'] < -10:
                        print("   📉 Revenue decline should trigger recovery strategies")
                    elif metrics['monthly_growth'] > 15:
                        print("   📈 Strong growth should trigger scaling decisions")
                    
                    if metrics['customer_satisfaction'] < 3.5:
                        print("   😞 Critical satisfaction should trigger emergency plans")
                    elif metrics['customer_satisfaction'] < 4.0:
                        print("   😐 Low satisfaction should trigger improvement plans")
                    
                    if metrics['total_orders'] < 95000:
                        print("   📦 Low order volume should trigger marketing decisions")
                    elif metrics['total_orders'] > 115000:
                        print("   📦 High order volume should trigger operational decisions")
                    
                else:
                    print(f"❌ API Error: {response.status}")
                    
        except Exception as e:
            print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_alerts_decisions())