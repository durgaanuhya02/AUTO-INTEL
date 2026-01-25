#!/usr/bin/env python3
"""
Demo Script for Agentic AI Business Decision System
Simulates realistic business scenarios for demonstration purposes
"""

import asyncio
import aiohttp
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List

class AgenticAIDemo:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_system_health(self) -> bool:
        """Check if the system is running and healthy"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ System Status: {health_data.get('status', 'unknown')}")
                    print(f"   Redis: {'✅' if health_data.get('redis_healthy') else '❌'}")
                    print(f"   Agents: {health_data.get('agents_active', 'unknown')}")
                    return health_data.get('status') == 'healthy'
                return False
        except Exception as e:
            print(f"❌ System health check failed: {e}")
            return False
    
    async def trigger_revenue_anomaly(self):
        """Simulate a revenue drop anomaly"""
        print("\n🔍 SCENARIO 1: Revenue Drop Detection")
        print("=" * 50)
        
        # Trigger a significant revenue drop
        anomaly_data = {
            "metric_type": "revenue",
            "current_value": 8500.0,  # Significant drop from normal ~15000
            "description": "Simulated revenue drop for demo"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/agents/trigger",
                json=anomaly_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Revenue anomaly triggered: {result.get('status')}")
                    print(f"   Current Value: ${anomaly_data['current_value']:,.2f}")
                    print(f"   Expected: ~$15,000 (43% drop detected)")
                    return True
                else:
                    print(f"❌ Failed to trigger anomaly: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Error triggering anomaly: {e}")
            return False
    
    async def trigger_churn_risk_spike(self):
        """Simulate a customer churn risk increase"""
        print("\n⚠️  SCENARIO 2: Customer Churn Risk Spike")
        print("=" * 50)
        
        anomaly_data = {
            "metric_type": "churn_risk",
            "current_value": 0.28,  # High churn risk (normal ~0.15)
            "description": "Customer satisfaction issues leading to churn risk"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/agents/trigger",
                json=anomaly_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Churn risk anomaly triggered: {result.get('status')}")
                    print(f"   Current Risk: {anomaly_data['current_value']:.1%}")
                    print(f"   Normal Range: ~15% (87% increase detected)")
                    return True
                else:
                    print(f"❌ Failed to trigger churn anomaly: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Error triggering churn anomaly: {e}")
            return False
    
    async def monitor_agent_activity(self, duration: int = 30):
        """Monitor agent activity for a specified duration"""
        print(f"\n🤖 Monitoring Agent Activity ({duration}s)")
        print("=" * 50)
        
        start_time = time.time()
        while time.time() - start_time < duration:
            try:
                async with self.session.get(f"{self.base_url}/api/v1/agents/status") as response:
                    if response.status == 200:
                        status_data = await response.json()
                        agents = status_data.get('agents', {})
                        
                        print(f"\r⏱️  Time: {int(time.time() - start_time)}s | ", end="")
                        for agent_name, agent_data in agents.items():
                            status = agent_data.get('status', 'unknown')
                            emoji = {
                                'active': '🟢',
                                'processing': '🟡', 
                                'idle': '⚪',
                                'error': '🔴'
                            }.get(status.lower(), '⚫')
                            print(f"{agent_name}: {emoji} ", end="")
                        
                        print("", end="", flush=True)
                        
            except Exception as e:
                print(f"\r❌ Error monitoring agents: {e}", end="", flush=True)
            
            await asyncio.sleep(2)
        
        print("\n")
    
    async def check_decisions(self) -> List[Dict[str, Any]]:
        """Check for AI decisions made by the system"""
        try:
            async with self.session.get(f"{self.base_url}/api/v1/decisions") as response:
                if response.status == 200:
                    data = await response.json()
                    decisions = data.get('decisions', [])
                    
                    if decisions:
                        print(f"\n🧠 AI DECISIONS GENERATED ({len(decisions)} total)")
                        print("=" * 50)
                        
                        for i, decision in enumerate(decisions[:3], 1):  # Show top 3
                            print(f"\n{i}. {decision.get('decision_title', 'Unknown Decision')}")
                            print(f"   Scenario: {decision.get('recommended_scenario', 'N/A')}")
                            print(f"   Confidence: {decision.get('confidence_score', 0):.1%}")
                            print(f"   Impact: ${abs(decision.get('financial_impact', 0)):,.2f}")
                            print(f"   Status: {decision.get('final_status', 'unknown').upper()}")
                            
                            if decision.get('action') == 'request_human_approval':
                                print("   🔔 REQUIRES HUMAN APPROVAL")
                    
                    return decisions
                else:
                    print(f"❌ Failed to fetch decisions: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Error checking decisions: {e}")
            return []
    
    async def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for active alerts"""
        try:
            async with self.session.get(f"{self.base_url}/api/v1/alerts") as response:
                if response.status == 200:
                    data = await response.json()
                    alerts = data.get('alerts', [])
                    
                    if alerts:
                        print(f"\n🚨 ACTIVE ALERTS ({len(alerts)} total)")
                        print("=" * 50)
                        
                        for i, alert in enumerate(alerts[:5], 1):  # Show top 5
                            severity = alert.get('severity', 'unknown')
                            emoji = {
                                'critical': '🔴',
                                'high': '🟠',
                                'medium': '🟡',
                                'low': '🔵'
                            }.get(severity, '⚫')
                            
                            print(f"{i}. {emoji} {alert.get('title', 'Unknown Alert')}")
                            print(f"   {alert.get('description', 'No description')}")
                            print(f"   Agent: {alert.get('agent_type', 'unknown')}")
                            print(f"   Metric: {alert.get('metric_type', 'unknown')}")
                    
                    return alerts
                else:
                    print(f"❌ Failed to fetch alerts: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Error checking alerts: {e}")
            return []
    
    async def simulate_human_approval(self, decisions: List[Dict[str, Any]]):
        """Simulate human approval process"""
        pending_decisions = [d for d in decisions if d.get('final_status') == 'pending']
        
        if not pending_decisions:
            print("\n✅ No decisions pending approval")
            return
        
        print(f"\n👤 HUMAN APPROVAL SIMULATION")
        print("=" * 50)
        
        for decision in pending_decisions[:2]:  # Approve first 2
            decision_id = decision.get('decision_id', 'unknown')
            title = decision.get('decision_title', 'Unknown Decision')
            
            # Simulate approval decision based on confidence and impact
            confidence = decision.get('confidence_score', 0)
            impact = abs(decision.get('financial_impact', 0))
            
            # Auto-approve high confidence, low impact decisions
            should_approve = confidence > 0.7 and impact < 15000
            
            approval_data = {
                "decision_id": decision_id,
                "approved": should_approve,
                "approver": "Demo User",
                "comments": f"Demo approval - Confidence: {confidence:.1%}, Impact: ${impact:,.2f}"
            }
            
            try:
                async with self.session.post(
                    f"{self.base_url}/api/v1/approve-decision",
                    json=approval_data
                ) as response:
                    if response.status == 200:
                        status = "✅ APPROVED" if should_approve else "❌ REJECTED"
                        print(f"{status}: {title}")
                        print(f"   Reason: {approval_data['comments']}")
                    else:
                        print(f"❌ Failed to process approval: {response.status}")
            except Exception as e:
                print(f"❌ Error processing approval: {e}")
    
    async def get_dashboard_summary(self):
        """Get and display dashboard summary"""
        try:
            async with self.session.get(f"{self.base_url}/api/v1/dashboard") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"\n📊 DASHBOARD SUMMARY")
                    print("=" * 50)
                    
                    # Current metrics
                    metrics = data.get('current_metrics', {})
                    print(f"Revenue: ${metrics.get('revenue', 0):,.2f}")
                    print(f"Orders: {metrics.get('orders', 0):,}")
                    print(f"Customer Satisfaction: {metrics.get('customer_satisfaction', 0):.1f}/5.0")
                    print(f"Churn Risk: {metrics.get('churn_risk', 0):.1%}")
                    print(f"Delivery Delay: {metrics.get('delivery_delay', 0):.1f} days")
                    
                    # System status
                    agents = data.get('agent_statuses', [])
                    active_agents = len([a for a in agents if a.get('status') == 'active'])
                    print(f"\nActive Agents: {active_agents}/{len(agents)}")
                    
                    alerts = data.get('alerts', [])
                    decisions = data.get('recent_decisions', [])
                    print(f"Active Alerts: {len(alerts)}")
                    print(f"Recent Decisions: {len(decisions)}")
                    
                    return data
                else:
                    print(f"❌ Failed to fetch dashboard: {response.status}")
                    return None
        except Exception as e:
            print(f"❌ Error fetching dashboard: {e}")
            return None

async def run_demo():
    """Run the complete demo scenario"""
    print("🚀 AGENTIC AI BUSINESS DECISION SYSTEM DEMO")
    print("=" * 60)
    print("This demo simulates realistic business scenarios to showcase")
    print("the autonomous AI decision-making capabilities.\n")
    
    async with AgenticAIDemo() as demo:
        # 1. Check system health
        if not await demo.check_system_health():
            print("❌ System is not healthy. Please start the system first.")
            print("Run: python setup.py or start.bat/start.sh")
            return
        
        # 2. Get initial dashboard state
        await demo.get_dashboard_summary()
        
        # 3. Trigger first scenario - Revenue drop
        await demo.trigger_revenue_anomaly()
        
        # 4. Monitor agent activity
        print("\n⏳ Waiting for agents to process the anomaly...")
        await demo.monitor_agent_activity(20)
        
        # 5. Check for alerts and decisions
        alerts = await demo.check_alerts()
        decisions = await demo.check_decisions()
        
        # 6. Trigger second scenario - Churn risk
        await demo.trigger_churn_risk_spike()
        
        # 7. Monitor more agent activity
        print("\n⏳ Processing second anomaly...")
        await demo.monitor_agent_activity(15)
        
        # 8. Check updated alerts and decisions
        await demo.check_alerts()
        updated_decisions = await demo.check_decisions()
        
        # 9. Simulate human approval process
        await demo.simulate_human_approval(updated_decisions)
        
        # 10. Final dashboard summary
        await demo.get_dashboard_summary()
        
        print(f"\n🎉 DEMO COMPLETE!")
        print("=" * 60)
        print("Key Highlights:")
        print("✅ Multi-agent system detected and analyzed anomalies")
        print("✅ AI generated decision scenarios with confidence scores")
        print("✅ Human-in-the-loop governance enforced approval policies")
        print("✅ Real-time dashboard updated with live agent status")
        print("\nAccess the dashboard at: http://localhost:3000")
        print("API documentation at: http://localhost:8000/docs")

if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("Make sure the system is running: python setup.py")