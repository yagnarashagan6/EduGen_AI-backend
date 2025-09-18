#!/usr/bin/env python3
"""
Simple test for the running server
"""

import requests
import time
import json

def test_endpoints():
    """Test all endpoints"""
    base_url = "http://localhost:10000"
    
    print("🧪 Testing EduGen AI Backend Endpoints")
    print("=" * 50)
    
    # Test health endpoint
    try:
        print("1. Testing Health Endpoint...")
        response = requests.get(f"{base_url}/api/health", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Model: {health_data.get('model', 'Unknown')}")
            print(f"   Version: {health_data.get('version', 'Unknown')}")
            print("   ✅ Health check passed!")
        else:
            print("   ❌ Health check failed!")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # Test chat endpoint
    try:
        print("\n2. Testing Chat Endpoint...")
        chat_data = {"message": "What is 2+2? Give a short answer."}
        response = requests.post(f"{base_url}/api/chat", json=chat_data, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            chat_response = response.json()
            print(f"   Response: {chat_response.get('response', 'No response')[:100]}...")
            print("   ✅ Chat endpoint passed!")
        else:
            print(f"   ❌ Chat endpoint failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Chat endpoint error: {e}")
    
    # Test quiz endpoint
    try:
        print("\n3. Testing Quiz Generation...")
        quiz_data = {"topic": "Basic math", "count": 3}
        response = requests.post(f"{base_url}/api/generate-quiz", json=quiz_data, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            quiz_response = response.json()
            questions = quiz_response.get('questions', [])
            print(f"   Generated {len(questions)} questions")
            if questions:
                print(f"   Sample: {questions[0].get('text', 'No text')[:50]}...")
            print("   ✅ Quiz generation passed!")
        else:
            print(f"   ❌ Quiz generation failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Quiz generation error: {e}")
    
    print("\n🎉 Testing complete!")

if __name__ == "__main__":
    test_endpoints()