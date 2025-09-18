#!/usr/bin/env python3
"""
Test the updated talk mode functionality
"""

import os
import sys
import datetime
from app import app

# Set environment variable for testing
os.environ['GOOGLE_API_KEY'] = 'AIzaSyDJQsaP2sY1KxQWP1x3Q1z3Q1z3Q1z3Q1z'

def test_talk_mode_responses():
    """Test talk mode for short responses"""
    print("🧪 Testing Talk Mode vs Educational Mode")
    print("=" * 50)
    
    test_questions = [
        "What is 2+2?",
        "Tell me a joke",
        "What is photosynthesis?",
        "What time is it?"
    ]
    
    with app.test_client() as client:
        for question in test_questions:
            print(f"\n📝 Question: {question}")
            
            # Test Talk Mode
            talk_response = client.post('/api/chat', 
                                       json={"message": question, "talkMode": True},
                                       content_type='application/json')
            
            if talk_response.status_code == 200:
                talk_data = talk_response.get_json()
                talk_text = talk_data.get('response', '')
                print(f"🗣️  Talk Mode ({len(talk_text)} chars): {talk_text}")
            else:
                print(f"❌ Talk mode failed: {talk_response.status_code}")
            
            # Test Educational Mode (only for non-time questions)
            if "time" not in question.lower() and "date" not in question.lower():
                edu_response = client.post('/api/chat', 
                                          json={"message": question, "talkMode": False},
                                          content_type='application/json')
                
                if edu_response.status_code == 200:
                    edu_data = edu_response.get_json()
                    edu_text = edu_data.get('response', '')
                    print(f"🎓 Educational Mode ({len(edu_text)} chars): {edu_text[:100]}...")
                else:
                    print(f"❌ Educational mode failed: {edu_response.status_code}")
            
            print("-" * 50)

def test_date_time_handling():
    """Test date/time handling"""
    print("\n🕐 Testing Date/Time Handling")
    print("=" * 30)
    
    time_questions = ["What time is it?", "What's the date?", "Tell me the current time"]
    
    with app.test_client() as client:
        for question in time_questions:
            response = client.post('/api/chat', 
                                  json={"message": question, "talkMode": True},
                                  content_type='application/json')
            
            if response.status_code == 200:
                data = response.get_json()
                response_text = data.get('response', '')
                print(f"📅 {question} → {response_text}")
            else:
                print(f"❌ Failed: {response.status_code}")

if __name__ == "__main__":
    print("🚀 Testing Enhanced Talk Mode")
    test_talk_mode_responses()
    test_date_time_handling()
    print("\n✅ Testing completed!")