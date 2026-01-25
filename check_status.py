#!/usr/bin/env python3
"""
Status checker for the Agentic AI system
"""
import requests
import json
from datetime import datetime

def check_backend():
    """Check backend status"""
    try:
        # Check health endpoint
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Backend Health Check: PASSED")
            print(f"   Status: {health_data.get('status')}")
            print(f"   Mode: {health_data.get('mode')}")
            print(f"   Note: {health_data.get('note')}")
        else:
            print("❌ Backend Health Check: FAILED")
            return False
        
        # Check dashboard API
        response = requests.get("http://localhost:8000/api/v1/dashboard", timeout=5)
        if response.status_code == 200:
            dashboard_data = response.json()
            print("✅ Dashboard API: WORKING")
            print(f"   Current Metrics: {len(dashboard_data.get('current_metrics', {}))} metrics")
            print(f"   Alerts: {len(dashboard_data.get('alerts', []))} active")
            print(f"   Decisions: {len(dashboard_data.get('recent_decisions', []))} recent")
            print(f"   Agents: {len(dashboard_data.get('agent_statuses', []))} agents")
        else:
            print("❌ Dashboard API: FAILED")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Backend: NOT RUNNING (Connection refused)")
        return False
    except Exception as e:
        print(f"❌ Backend: ERROR ({str(e)})")
        return False

def check_frontend():
    """Check frontend status"""
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend: RUNNING")
            print("   Next.js application is accessible")
            return True
        else:
            print(f"❌ Frontend: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Frontend: NOT RUNNING (Connection refused)")
        return False
    except Exception as e:
        print(f"❌ Frontend: ERROR ({str(e)})")
        return False

def main():
    print("=" * 60)
    print("🚀 AGENTIC AI BUSINESS DECISION SYSTEM - STATUS CHECK")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    backend_ok = check_backend()
    print()
    frontend_ok = check_frontend()
    print()
    
    print("=" * 60)
    if backend_ok and frontend_ok:
        print("🎉 SYSTEM STATUS: ALL SERVICES RUNNING")
        print()
        print("🌐 Access Points:")
        print("   • Frontend Dashboard: http://localhost:3000")
        print("   • Backend API: http://localhost:8000")
        print("   • API Documentation: http://localhost:8000/docs")
        print()
        print("🎮 Demo Features:")
        print("   • Real-time dashboard with mock data")
        print("   • Interactive charts and metrics")
        print("   • AI decision recommendations")
        print("   • Alert management system")
        print("   • Agent status monitoring")
        print()
        print("⌨️  Keyboard Shortcuts (in dashboard):")
        print("   • R - Refresh dashboard")
        print("   • T - Trigger analysis")
        print("   • H - Show help")
        print("   • Esc - Close modals")
    else:
        print("⚠️  SYSTEM STATUS: SOME SERVICES NOT RUNNING")
        print()
        if not backend_ok:
            print("🔧 To start backend:")
            print("   cd backend && venv\\Scripts\\python main_demo.py")
        if not frontend_ok:
            print("🔧 To start frontend:")
            print("   cd frontend && npm run dev")
    
    print("=" * 60)

if __name__ == "__main__":
    main()