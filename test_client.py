#!/usr/bin/env python3
"""
Test the Flask app using test client
"""

from app import app

def test_with_client():
    """Test endpoints using Flask test client"""
    print("🧪 Testing with Flask Test Client")
    print("=" * 40)
    
    with app.test_client() as client:
        # Test health endpoint
        print("1. Testing Health Endpoint...")
        response = client.get('/api/health')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"   Model: {data.get('model')}")
            print(f"   Version: {data.get('version')}")
            print("   ✅ Health check passed!")
        else:
            print("   ❌ Health check failed!")
        
        # Test chat endpoint
        print("\n2. Testing Chat Endpoint...")
        chat_data = {"message": "What is 2+2?"}
        response = client.post('/api/chat', 
                               json=chat_data,
                               content_type='application/json')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"   Response: {data.get('response', 'No response')[:100]}...")
            print("   ✅ Chat test passed!")
        else:
            print(f"   ❌ Chat test failed: {response.get_data(as_text=True)}")
    
    print("\n🎉 Test client testing complete!")

if __name__ == "__main__":
    test_with_client()