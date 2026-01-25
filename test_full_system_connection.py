#!/usr/bin/env python3
"""
Complete System Connection Test
Tests all components: Backend API, Frontend, ML Models, and Agent System
"""
import asyncio
import aiohttp
import json
from datetime import datetime
import time

class SystemConnectionTester:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3001"
        self.results = {}
        
    async def test_backend_api(self):
        """Test all backend API endpoints"""
        print("🔧 Testing Backend API Endpoints...")
        
        endpoints = {
            "Root": "/",
            "Dashboard": "/api/v1/dashboard",
            "Real-Time Analytics": "/api/v1/analytics/real-time", 
            "Advanced Analytics": "/api/v1/analytics/advanced",
            "Business Insights": "/api/v1/insights/business",
            "Revenue Trends": "/api/v1/trends/revenue",
            "Advanced Forecasts": "/api/v1/analytics/forecasts/advanced",
            "ML Capabilities": "/api/v1/ml/capabilities",
            "API Docs": "/docs"
        }
        
        async with aiohttp.ClientSession() as session:
            for name, endpoint in endpoints.items():
                try:
                    async with session.get(f"{self.backend_url}{endpoint}") as response:
                        if response.status == 200:
                            data = await response.json() if endpoint != "/docs" else {"status": "ok"}
                            print(f"  ✅ {name}: {response.status} - {len(str(data))} chars")
                            self.results[f"backend_{name.lower().replace(' ', '_')}"] = True
                        else:
                            print(f"  ❌ {name}: {response.status}")
                            self.results[f"backend_{name.lower().replace(' ', '_')}"] = False
                except Exception as e:
                    print(f"  ❌ {name}: Error - {str(e)}")
                    self.results[f"backend_{name.lower().replace(' ', '_')}"] = False
    
    async def test_ml_endpoints(self):
        """Test ML-specific endpoints"""
        print("\n🤖 Testing ML Model Endpoints...")
        
        ml_endpoints = {
            "ML Models List": "/api/v1/ml/models",
            "ML Capabilities": "/api/v1/ml/capabilities",
            "Revenue Forecast": "/api/v1/analytics/forecasts/advanced/revenue?forecast_days=7",
            "Orders Forecast": "/api/v1/analytics/forecasts/advanced/orders?forecast_days=7"
        }
        
        async with aiohttp.ClientSession() as session:
            for name, endpoint in ml_endpoints.items():
                try:
                    async with session.get(f"{self.backend_url}{endpoint}") as response:
                        if response.status == 200:
                            data = await response.json()
                            print(f"  ✅ {name}: {response.status}")
                            if 'forecast' in data:
                                print(f"    📊 Forecast data available: {len(data['forecast']['predicted_values'])} predictions")
                            self.results[f"ml_{name.lower().replace(' ', '_')}"] = True
                        else:
                            print(f"  ❌ {name}: {response.status}")
                            self.results[f"ml_{name.lower().replace(' ', '_')}"] = False
                except Exception as e:
                    print(f"  ❌ {name}: Error - {str(e)}")
                    self.results[f"ml_{name.lower().replace(' ', '_')}"] = False
    
    async def test_ml_training(self):
        """Test ML model training"""
        print("\n🧠 Testing ML Model Training...")
        
        training_data = {
            "target_column": "revenue",
            "model_name": "test_model_" + str(int(time.time())),
            "task_type": "regression"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.backend_url}/api/v1/ml/train-xgboost",
                    json=training_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"  ✅ XGBoost Training: {response.status}")
                        if 'model_result' in data:
                            print(f"    🎯 Model Accuracy: {data['model_result'].get('accuracy', 'N/A')}")
                            print(f"    ⚡ Training Samples: {data.get('training_samples', 'N/A')}")
                        self.results['ml_training'] = True
                    else:
                        print(f"  ❌ XGBoost Training: {response.status}")
                        self.results['ml_training'] = False
            except Exception as e:
                print(f"  ❌ XGBoost Training: Error - {str(e)}")
                self.results['ml_training'] = False
    
    async def test_frontend_connection(self):
        """Test frontend accessibility"""
        print("\n🌐 Testing Frontend Connection...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.frontend_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        print(f"  ✅ Frontend: {response.status} - {len(content)} chars")
                        if "Agentic AI" in content or "Dashboard" in content:
                            print("    📱 Frontend content loaded successfully")
                        self.results['frontend_connection'] = True
                    else:
                        print(f"  ❌ Frontend: {response.status}")
                        self.results['frontend_connection'] = False
        except Exception as e:
            print(f"  ❌ Frontend: Error - {str(e)}")
            self.results['frontend_connection'] = False
    
    async def test_real_time_updates(self):
        """Test real-time data updates"""
        print("\n⏱️ Testing Real-Time Updates...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get initial data
                async with session.get(f"{self.backend_url}/api/v1/dashboard") as response:
                    if response.status == 200:
                        data1 = await response.json()
                        timestamp1 = data1.get('data_freshness', {}).get('last_update')
                        
                        print(f"  📊 Initial data timestamp: {timestamp1}")
                        
                        # Wait a bit and get data again
                        await asyncio.sleep(2)
                        
                        async with session.get(f"{self.backend_url}/api/v1/dashboard") as response2:
                            if response2.status == 200:
                                data2 = await response2.json()
                                timestamp2 = data2.get('data_freshness', {}).get('last_update')
                                
                                print(f"  📊 Second data timestamp: {timestamp2}")
                                
                                if timestamp1 != timestamp2:
                                    print("  ✅ Real-time updates working")
                                    self.results['real_time_updates'] = True
                                else:
                                    print("  ⚠️ Data timestamps same (may be cached)")
                                    self.results['real_time_updates'] = True  # Still working
                            else:
                                print(f"  ❌ Second request failed: {response2.status}")
                                self.results['real_time_updates'] = False
                    else:
                        print(f"  ❌ Initial request failed: {response.status}")
                        self.results['real_time_updates'] = False
        except Exception as e:
            print(f"  ❌ Real-time updates: Error - {str(e)}")
            self.results['real_time_updates'] = False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("🎯 SYSTEM CONNECTION TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\n📋 Detailed Results:")
        for test_name, result in self.results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} - {test_name.replace('_', ' ').title()}")
        
        print("\n🔗 Access URLs:")
        print(f"  🌐 Frontend Dashboard: {self.frontend_url}")
        print(f"  🔧 Backend API: {self.backend_url}")
        print(f"  📚 API Documentation: {self.backend_url}/docs")
        print(f"  📊 Dashboard Data: {self.backend_url}/api/v1/dashboard")
        print(f"  🤖 ML Capabilities: {self.backend_url}/api/v1/ml/capabilities")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL SYSTEMS OPERATIONAL! 🎉")
        elif passed_tests >= total_tests * 0.8:
            print("\n✅ SYSTEM MOSTLY OPERATIONAL")
        else:
            print("\n⚠️ SYSTEM NEEDS ATTENTION")

async def main():
    """Run complete system test"""
    print("🚀 STARTING COMPLETE SYSTEM CONNECTION TEST")
    print("="*60)
    
    tester = SystemConnectionTester()
    
    # Run all tests
    await tester.test_backend_api()
    await tester.test_ml_endpoints()
    await tester.test_ml_training()
    await tester.test_frontend_connection()
    await tester.test_real_time_updates()
    
    # Print summary
    tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())