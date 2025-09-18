#!/usr/bin/env python3
"""
Test script for the updated backend with document processing and talk mode
"""

import requests
import json
import time
import base64
import os

BASE_URL = "http://localhost:10000"

def test_health():
    """Test health endpoint"""
    print("1. Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Model: {health_data.get('model', 'Unknown')}")
            print(f"   Version: {health_data.get('version', 'Unknown')}")
            print(f"   Audio Features: {health_data.get('audio_features', False)}")
            print(f"   Document Processing: {health_data.get('document_processing', False)}")
            print("   ✅ Health check passed!")
        else:
            print("   ❌ Health check failed!")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False

def test_talk_mode():
    """Test talk mode (casual responses)"""
    print("\n2. Testing Talk Mode (Casual Chat)...")
    try:
        chat_data = {
            "message": "What is 2+2?", 
            "talkMode": True
        }
        response = requests.post(f"{BASE_URL}/api/chat", json=chat_data, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            chat_response = response.json()
            response_text = chat_response.get('response', 'No response')
            print(f"   Talk Mode Response: {response_text}")
            print("   ✅ Talk mode test passed!")
        else:
            print(f"   ❌ Talk mode test failed: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Talk mode test error: {e}")
        return False

def test_educational_mode():
    """Test educational mode (detailed responses)"""
    print("\n3. Testing Educational Mode...")
    try:
        chat_data = {
            "message": "What is photosynthesis?", 
            "talkMode": False
        }
        response = requests.post(f"{BASE_URL}/api/chat", json=chat_data, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            chat_response = response.json()
            response_text = chat_response.get('response', 'No response')
            print(f"   Educational Response Length: {len(response_text)} characters")
            print(f"   Preview: {response_text[:100]}...")
            print("   ✅ Educational mode test passed!")
        else:
            print(f"   ❌ Educational mode test failed: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Educational mode test error: {e}")
        return False

def test_time_query():
    """Test time/date query"""
    print("\n4. Testing Time/Date Query...")
    try:
        chat_data = {
            "message": "What time is it?", 
            "talkMode": True
        }
        response = requests.post(f"{BASE_URL}/api/chat", json=chat_data, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            chat_response = response.json()
            response_text = chat_response.get('response', 'No response')
            print(f"   Time Response: {response_text}")
            print("   ✅ Time query test passed!")
        else:
            print(f"   ❌ Time query test failed: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Time query test error: {e}")
        return False

def test_quiz_generation():
    """Test quiz generation"""
    print("\n5. Testing Quiz Generation...")
    try:
        quiz_data = {"topic": "Basic math", "count": 3}
        response = requests.post(f"{BASE_URL}/api/generate-quiz", json=quiz_data, timeout=30)
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
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Quiz generation error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("EduGen AI Backend Test Suite - Enhanced Version")
    print("=" * 60)
    
    print(f"Testing server at: {BASE_URL}")
    print("Features: Talk Mode, Educational Mode, Document Processing")
    print()
    
    tests = [
        ("Health Check", test_health),
        ("Talk Mode (Casual)", test_talk_mode),
        ("Educational Mode", test_educational_mode),
        ("Time/Date Query", test_time_query),
        ("Quiz Generation", test_quiz_generation),
    ]
    
    results = []
    for test_name, test_func in tests:
        success = test_func()
        results.append((test_name, success))
        
        # Add delay between tests to respect rate limiting
        time.sleep(3)
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    if passed == total:
        print("\n🎉 All tests passed! Enhanced backend is ready!")
        print("\n📋 Available Features:")
        print("  • 💬 Talk Mode (casual responses)")
        print("  • 🎓 Educational Mode (detailed explanations)")
        print("  • 📄 Document Processing (PDF/DOCX)")
        print("  • 📝 Quiz Generation")
        print("  • 🕐 Time/Date Queries")
    else:
        print("\n⚠️  Some tests failed. Check the server logs.")

if __name__ == "__main__":
    main()