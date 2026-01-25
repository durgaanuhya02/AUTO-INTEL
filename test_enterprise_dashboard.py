#!/usr/bin/env python3
"""
Test script to verify the enterprise dashboard is working properly
"""
import requests
import json
import time

def test_backend_endpoints():
    """Test all backend endpoints"""
    base_url = "http://localhost:8001"
    
    endpoints = [
        "/",
        "/api/v1/dashboard",
        "/api/v1/metrics/real-time",
        "/api/v1/enterprise/integrations/status",
        "/api/v1/analytics/status",
        "/api/v1/metrics/system",
        "/health"
    ]
    
    print("Testing Backend Endpoints...")
    print("=" * 50)
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint} - OK")
            else:
                print(f"❌ {endpoint} - Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint} - Error: {str(e)}")
    
    print("\n" + "=" * 50)

def test_frontend_accessibility():
    """Test if frontend is accessible"""
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is accessible at http://localhost:3000")
        else:
            print(f"❌ Frontend returned status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend not accessible: {str(e)}")

def main():
    print("Enterprise Dashboard Test Suite")
    print("=" * 50)
    
    # Test backend
    test_backend_endpoints()
    
    # Test frontend
    print("\nTesting Frontend...")
    print("=" * 50)
    test_frontend_accessibility()
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("\nTo access the Enterprise Dashboard:")
    print("1. Backend API: http://localhost:8001")
    print("2. Frontend: http://localhost:3000")
    print("3. Enterprise Dashboard: http://localhost:3000 (main page)")

if __name__ == "__main__":
    main()