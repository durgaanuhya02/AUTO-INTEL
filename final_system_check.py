#!/usr/bin/env python3
"""
Final System Check - Verify everything is working
"""
import requests
import time
from datetime import datetime

def check_system():
    print("🚀 FINAL SYSTEM STATUS CHECK")
    print("=" * 50)
    
    # Check Backend Health
    try:
        response = requests.get("http://localhost:8001/api/v1/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend Health: {data['status']}")
            print(f"📊 Records Processed: {data['data_processing']['records_processed']:,}")
        else:
            print(f"❌ Backend Health: Error {response.status_code}")
    except Exception as e:
        print(f"❌ Backend Health: Connection failed")
    
    # Check Dashboard Data (try simple endpoint first)
    try:
        response = requests.get("http://localhost:8001/api/v1/dashboard", timeout=10)
        if response.status_code == 200:
            data = response.json()
            metrics = data['current_metrics']
            print(f"✅ Dashboard Data: Working")
            print(f"   💰 Revenue: ${metrics['revenue']:,.2f}")
            print(f"   📦 Orders: {metrics['orders']:,}")
            print(f"   📈 Growth: {metrics['monthly_growth']:+.1f}%")
        else:
            print(f"❌ Dashboard Data: Error {response.status_code}")
    except Exception as e:
        print(f"❌ Dashboard Data: {str(e)}")
    
    # Check Frontend
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        if response.status_code == 200:
            print(f"✅ Frontend: Accessible on port 3000")
        else:
            print(f"❌ Frontend: Error {response.status_code}")
    except Exception as e:
        print(f"❌ Frontend: Connection failed")
    
    print("\n" + "=" * 50)
    print("🌟 ACCESS YOUR SYSTEM:")
    print("   Frontend Dashboard: http://localhost:3000")
    print("   Backend API: http://localhost:8001")
    print("   Health Check: http://localhost:8001/api/v1/health")
    print("=" * 50)

if __name__ == "__main__":
    check_system()