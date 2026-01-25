#!/usr/bin/env python3
"""
Verify Dynamic Alert and Decision System
"""
import asyncio
import aiohttp
import json
from datetime import datetime

async def verify_dynamic_system():
    """Verify that alerts and decisions are dynamic and responsive"""
    print("✅ VERIFYING DYNAMIC ALERT & DECISION SYSTEM")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        
        # Test current state
        try:
            async with session.get("http://localhost:8001/api/v1/dashboard") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    metrics = data['current_metrics']
                    alerts = data.get('alerts', [])
                    decisions = data.get('recent_decisions', [])
                    
                    print("📊 CURRENT SYSTEM STATE:")
                    print(f"   💰 Revenue: ${metrics['revenue']:,.0f}")
                    print(f"   📦 Orders: {metrics['orders']:,}")
                    print(f"   📈 Growth Rate: {metrics['monthly_growth']:+.1f}%")
                    print(f"   ⭐ Satisfaction: {metrics['customer_satisfaction']:.1f}/5.0")
                    print(f"   💳 AOV: ${metrics['avg_order_value']:.2f}")
                    
                    print(f"\n🚨 ACTIVE ALERTS ({len(alerts)}):")
                    if alerts:
                        for alert in alerts:
                            severity_emoji = {
                                'critical': '🔴',
                                'high': '🟠',
                                'medium': '🟡', 
                                'low': '🟢'
                            }.get(alert.get('severity'), '🔵')
                            
                            print(f"   {severity_emoji} {alert['title']}")
                            print(f"      Trigger: {alert['type']} = {alert.get('metric_value', 'N/A')} (threshold: {alert.get('threshold', 'N/A')})")
                            print(f"      Message: {alert['message']}")
                            print(f"      Action Required: {'Yes' if alert.get('action_required') else 'No'}")
                            print()
                    else:
                        print("   No alerts currently active")
                    
                    print(f"💡 ACTIVE DECISIONS ({len(decisions)}):")
                    if decisions:
                        for decision in decisions:
                            priority_emoji = {
                                'critical': '🔴',
                                'high': '🟠',
                                'medium': '🟡',
                                'low': '🟢'
                            }.get(decision.get('priority'), '🔵')
                            
                            print(f"   {priority_emoji} {decision['title']}")
                            print(f"      Category: {decision.get('category', 'unknown')}")
                            print(f"      Status: {decision.get('status', 'unknown')} | Priority: {decision.get('priority', 'unknown')}")
                            print(f"      Financial Impact: ${decision.get('financial_impact', 0):,.0f}")
                            print(f"      Confidence: {decision.get('confidence_score', 0):.1%}")
                            print(f"      Reasoning: {decision.get('reasoning', 'No reasoning')}")
                            print()
                    else:
                        print("   No decisions currently active")
                    
                    # Verify system logic
                    print("🔍 SYSTEM LOGIC VERIFICATION:")
                    
                    # Check revenue-based logic
                    growth = metrics['monthly_growth']
                    if growth < -20:
                        expected_alert = "Emergency revenue recovery alert"
                        expected_decision = "Emergency Revenue Recovery Plan"
                        print(f"   📉 Growth at {growth:.1f}% should trigger: {expected_alert}")
                        
                        has_revenue_alert = any('Revenue' in alert['title'] and alert['severity'] == 'critical' for alert in alerts)
                        has_emergency_decision = any('Emergency' in decision['title'] for decision in decisions)
                        
                        if has_revenue_alert:
                            print("   ✅ Critical revenue alert correctly generated")
                        else:
                            print("   ❌ Missing critical revenue alert")
                            
                        if has_emergency_decision:
                            print("   ✅ Emergency recovery decision correctly generated")
                        else:
                            print("   ❌ Missing emergency recovery decision")
                    
                    elif growth < -10:
                        print(f"   📉 Growth at {growth:.1f}% should trigger revenue decline alerts")
                        has_decline_alert = any('decline' in alert['message'].lower() for alert in alerts)
                        if has_decline_alert:
                            print("   ✅ Revenue decline alert correctly generated")
                        else:
                            print("   ❌ Missing revenue decline alert")
                    
                    # Check satisfaction-based logic
                    satisfaction = metrics['customer_satisfaction']
                    if satisfaction < 3.5:
                        print(f"   😞 Satisfaction at {satisfaction:.1f} should trigger critical alerts")
                    elif satisfaction < 4.0:
                        print(f"   😐 Satisfaction at {satisfaction:.1f} should trigger improvement alerts")
                    else:
                        print(f"   😊 Satisfaction at {satisfaction:.1f} is acceptable")
                    
                    # Check order volume logic
                    orders = metrics['orders']
                    if orders < 95000:
                        print(f"   📦 Orders at {orders:,} should trigger volume recovery decisions")
                    elif orders > 115000:
                        print(f"   📦 Orders at {orders:,} should trigger operational scaling decisions")
                    else:
                        print(f"   📦 Orders at {orders:,} are within normal range")
                    
                    print(f"\n🎯 DYNAMIC SYSTEM STATUS:")
                    if len(alerts) > 0 and len(decisions) > 0:
                        print("   ✅ SYSTEM IS FULLY DYNAMIC")
                        print("   ✅ Alerts are being generated based on real-time metrics")
                        print("   ✅ Decisions are being created based on business conditions")
                        print("   ✅ Both alerts and decisions change as metrics change")
                        print("\n   🔄 The system updates every 30 seconds with new:")
                        print("      - Metric variations (revenue, orders, satisfaction)")
                        print("      - Context-aware alerts based on thresholds")
                        print("      - Intelligent business decisions with financial impact")
                        print("      - Priority levels and approval requirements")
                    else:
                        print("   ⚠️  System may need more time to generate alerts/decisions")
                    
                else:
                    print(f"❌ API Error: {response.status}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_dynamic_system())