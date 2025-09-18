#!/usr/bin/env python3
"""
Test script for EduGen AI Python Backend (Updated for Gemini API)
Run this script to test all endpoints locally
"""

import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:10000"

def check_environment():
    """Check if required environment variables are set"""
    print("Checking environment setup...")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("❌ GOOGLE_API_KEY not found in environment")
        print("Please create a .env file with your Google API key")
        return False
    else:
        print("✅ GOOGLE_API_KEY is configured")
        return True

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health test failed: {e}")
        return False

def test_chat():
    """Test chat endpoint"""
    print("\nTesting chat endpoint...")
    try:
        data = {"message": "What is 2+2?"}
        response = requests.post(f"{BASE_URL}/api/chat", json=data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {result.get('response', 'No response')[:100]}...")
        else:
            print(f"Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Chat test failed: {e}")
        return False

def test_quiz():
    """Test quiz generation endpoint"""
    print("\nTesting quiz generation endpoint...")
    try:
        data = {"topic": "Python programming", "count": 3}
        response = requests.post(f"{BASE_URL}/api/generate-quiz", json=data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            questions = result.get('questions', [])
            print(f"Generated {len(questions)} questions")
            if questions:
                print(f"Sample question: {questions[0]['text']}")
        else:
            print(f"Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Quiz test failed: {e}")
        return False

def test_text_to_speech():
    """Test text-to-speech endpoint"""
    print("\nTesting text-to-speech endpoint...")
    try:
        data = {"text": "Hello, this is a test of the text to speech functionality."}
        response = requests.post(f"{BASE_URL}/api/text-to-speech", json=data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Audio format: {result.get('format')}")
            print(f"Audio data length: {len(result.get('audio', ''))}")
        else:
            print(f"Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"TTS test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("EduGen AI Python Backend Test Suite (Gemini API)")
    print("=" * 50)
    
    print(f"Testing server at: {BASE_URL}")
    print("Make sure the server is running: python app.py")
    print()
    
    # Check environment first
    if not check_environment():
        print("\n❌ Environment check failed. Please set up your .env file with GOOGLE_API_KEY")
        return
    
    tests = [
        ("Health Check", test_health),
        ("Chat API (Gemini)", test_chat),
        ("Quiz Generation (Gemini)", test_quiz),
        ("Text-to-Speech", test_text_to_speech),
    ]
    
    results = []
    for test_name, test_func in tests:
        success = test_func()
        results.append((test_name, success))
        if not success:
            print(f"❌ {test_name} FAILED")
        else:
            print(f"✅ {test_name} PASSED")
        
        # Add delay between tests to respect rate limiting
        time.sleep(2)
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    if passed == total:
        print("\n🎉 All tests passed! Backend is ready for deployment with Gemini API.")
    else:
        print("\n⚠️  Some tests failed. Check the server logs and configuration.")
        print("Note: Make sure your GOOGLE_API_KEY is valid and has sufficient quota.")

if __name__ == "__main__":
    main()