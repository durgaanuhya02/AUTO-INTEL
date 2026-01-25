#!/usr/bin/env python3
"""
Test Frontend-Backend Connection
"""
import asyncio
import aiohttp
import json

async def test_frontend_backend_connection():
    """Test if frontend can connect to backend APIs"""
    print("🔗 TESTING FRONTEND-BACKEND CONNECTION")
    print("=" * 50)
    
    # Test all the endpoints that the frontend uses
    endpoints = [
        ('/dashboard', 'Dashboard Data'),
        ('/analytics/real-time', 'Real-time Analytics'),
        ('/analytics/advanced', 'Advanced Analytics'),
        ('/health', 'Health Check'),
        ('/insights/business', 'Business Insights')
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint, name in endpoints:
            try:
                url = f"http://localhost:8001/api/v1{endpoint}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ {name}: Status {response.status} - Data received")
                        
                        # Check for specific data that frontend expects
                        if endpoint == '/dashboard':
                            if 'current_metrics' in data:
                                metrics = data['current_metrics']
                                print(f"      Revenue: ${metrics.get('revenue', 0):,.0f}")
                                print(f"      Orders: {metrics.get('orders', 0):,}")
                            else:
                                print("      ❌ Missing current_metrics in response")
                        
                        elif endpoint == '/analytics/real-time':
                            if 'revenue_analytics' in data:
                                print(f"      Revenue Analytics: Available")
                            else:
                                print("      ❌ Missing revenue_analytics in response")
                    else:
                        print(f"   ❌ {name}: Status {response.status}")
                        
            except Exception as e:
                print(f"   ❌ {name}: Connection Error - {str(e)}")
    
    # Test CORS by simulating a browser request
    print(f"\n🌐 TESTING CORS CONFIGURATION")
    print("-" * 30)
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                'Origin': 'http://localhost:3001',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            async with session.options('http://localhost:8001/api/v1/dashboard', headers=headers) as response:
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
                }
                
                print(f"   CORS Status: {response.status}")
                for header, value in cors_headers.items():
                    if value:
                        print(f"   {header}: {value}")
                    else:
                        print(f"   ❌ Missing: {header}")
                        
                if cors_headers['Access-Control-Allow-Origin']:
                    print("   ✅ CORS configured correctly")
                else:
                    print("   ❌ CORS not configured properly")
                    
    except Exception as e:
        print(f"   ❌ CORS Test Error: {str(e)}")
    
    print(f"\n📋 SUMMARY")
    print("-" * 20)
    print("If all endpoints show ✅, the backend is working correctly.")
    print("If you see 'cannot fetch real time data' in the browser:")
    print("1. Check browser console for specific error messages")
    print("2. Ensure both servers are running:")
    print("   - Backend: http://localhost:8001")
    print("   - Frontend: http://localhost:3001")
    print("3. Check for any firewall or network issues")
    print("4. Try refreshing the browser page")

if __name__ == "__main__":
    asyncio.run(test_frontend_backend_connection())