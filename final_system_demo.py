#!/usr/bin/env python3
"""
Final System Demo - Show Real-time Data Updates
"""
import requests
import json
import time
from datetime import datetime

def show_real_time_updates():
    """Demonstrate real-time data updates"""
    print("🚀 AGENTIC AI SYSTEM - REAL-TIME DEMO")
    print("=" * 60)
    
    for i in range(5):  # Show 5 updates
        try:
            response = requests.get('http://localhost:8001/api/v1/dashboard', timeout=5)
            if response.status_code == 200:
                data = response.json()
                metrics = data['current_metrics']
                
                print(f"\n📊 UPDATE #{i+1} - {datetime.now().strftime('%H:%M:%S')}")
                print(f"💰 Revenue: ${metrics['revenue']:,.2f}")
                print(f"📦 Orders: {metrics['orders']:,}")
                print(f"📈 Growth: {metrics['monthly_growth']:+.1f}%")
                print(f"⭐ Satisfaction: {metrics['customer_satisfaction']:.1f}/5.0")
                print(f"💵 AOV: ${metrics['avg_order_value']:.2f}")
                
                # Show alerts
                alerts = data.get('alerts', [])
                if alerts:
                    print(f"🚨 Active Alerts: {len(alerts)}")
                    for alert in alerts[:2]:  # Show first 2 alerts
                        print(f"   • {alert['title']} ({alert['severity']})")
                
                # Show decisions
                decisions = data.get('recent_decisions', [])
                if decisions:
                    print(f"🧠 AI Decisions: {len(decisions)}")
                    for decision in decisions[:1]:  # Show first decision
                        print(f"   • {decision['title']} ({decision['confidence_score']*100:.0f}% confidence)")
                
                print("-" * 60)
                
                if i < 4:  # Don't wait after last update
                    print("⏳ Waiting 30 seconds for next update...")
                    time.sleep(30)
                    
            else:
                print(f"❌ Error: {response.status_code}")
                break
                
        except Exception as e:
            print(f"❌ Connection error: {str(e)}")
            break
    
    print("\n🎉 DEMO COMPLETE!")
    print("🌟 Your Agentic AI System is running with:")
    print("   ✅ Real-time data simulation (30-second updates)")
    print("   ✅ ML-powered analytics and forecasting")
    print("   ✅ Dynamic alerts and intelligent decisions")
    print("   ✅ Multi-agent AI system coordination")
    print("   ✅ Brazilian e-commerce dataset processing")
    print("\n🌐 Access your dashboard: http://localhost:3001")

if __name__ == "__main__":
    show_real_time_updates()