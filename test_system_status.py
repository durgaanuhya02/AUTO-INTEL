#!/usr/bin/env python3
"""
Quick System Status Test
"""
import requests
import json
from datetime import datetime

def test_backend():
    """Test backend API"""
    try:
        print("🔧 Testing Backend API...")
        response = requests.get('http://localhost:8001/api/v1/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend Status: {data['status']}")
            print(f"📊 Records Processed: {data['data_processing']['records_processed']:,}")
            return True
        else:
            print(f"❌ Backend Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend Connection Failed: {str(e)}")
        return False

def test_dashboard_data():
    """Test dashboard data endpoint"""
    try:
        print("\n📊 Testing Dashboard Data...")
        response = requests.get('http://localhost:8001/api/v1/dashboard', timeout=5)
        if response.status_code == 200:
            data = response.json()
            metrics = data['current_metrics']
            print(f"✅ Revenue: ${metrics['revenue']:,.2f}")
            print(f"✅ Orders: {metrics['orders']:,}")
            print(f"✅ Growth: {metrics['monthly_growth']:+.1f}%")
            print(f"✅ Satisfaction: {metrics['customer_satisfaction']:.1f}/5.0")
            return True
        else:
            print(f"❌ Dashboard Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Dashboard Connection Failed: {str(e)}")
        return False

def test_frontend():
    """Test frontend availability"""
    try:
        print("\n🌐 Testing Frontend...")
        response = requests.get('http://localhost:3001', timeout=10)
        if response.status_code == 200:
            print("✅ Frontend is accessible")
            return True
        else:
            print(f"❌ Frontend Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend Connection Failed: {str(e)}")
        return False

def main():
    print("🚀 AGENTIC AI SYSTEM STATUS CHECK")
    print("=" * 50)
    
    backend_ok = test_backend()
    dashboard_ok = test_dashboard_data()
    frontend_ok = test_frontend()
    
    print("\n" + "=" * 50)
    print("📋 SYSTEM STATUS SUMMARY:")
    print(f"🔧 Backend API: {'✅ RUNNING' if backend_ok else '❌ FAILED'}")
    print(f"📊 Dashboard Data: {'✅ ACTIVE' if dashboard_ok else '❌ FAILED'}")
    print(f"🌐 Frontend: {'✅ ACCESSIBLE' if frontend_ok else '❌ FAILED'}")
    
    if all([backend_ok, dashboard_ok, frontend_ok]):
        print("\n🎉 ALL SYSTEMS OPERATIONAL!")
        print("🌟 ACCESS YOUR DASHBOARD:")
        print("   Frontend: http://localhost:3001")
        print("   Backend API: http://localhost:8001")
        print("   Health Check: http://localhost:8001/api/v1/health")
    else:
        print("\n⚠️  SOME SYSTEMS NEED ATTENTION")
    
    print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()