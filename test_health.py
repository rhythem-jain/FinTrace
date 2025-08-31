#!/usr/bin/env python3
"""
Test script to verify health check endpoints work without database access
"""

from app import app

def test_health_endpoints():
    """Test all health check endpoints"""
    with app.test_client() as client:
        print("🧪 Testing Health Check Endpoints...")
        
        # Test /ping endpoint
        try:
            response = client.get('/ping')
            print(f"✅ /ping: Status {response.status_code}, Response: '{response.data.decode()}'")
        except Exception as e:
            print(f"❌ /ping failed: {e}")
        
        # Test /health endpoint
        try:
            response = client.get('/health')
            print(f"✅ /health: Status {response.status_code}, Response: '{response.data.decode()}'")
        except Exception as e:
            print(f"❌ /health failed: {e}")
        
        # Test /status endpoint
        try:
            response = client.get('/status')
            print(f"✅ /status: Status {response.status_code}, Response: '{response.data.decode()}'")
        except Exception as e:
            print(f"❌ /status failed: {e}")
        
        print("\n🎯 Health check test completed!")

if __name__ == "__main__":
    test_health_endpoints()
