#!/usr/bin/env python3
"""
Quick test for enhanced features
"""

from app import app

def test_health():
    """Test health endpoint"""
    with app.test_client() as client:
        response = client.get('/api/health')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"Model: {data.get('model')}")
            print(f"Version: {data.get('version')}")
            print(f"Document Processing: {data.get('document_processing')}")
            print(f"Audio Features: {data.get('audio_features')}")

def test_talk_mode():
    """Test talk mode"""
    with app.test_client() as client:
        response = client.post('/api/chat', 
                               json={"message": "What is 2+2?", "talkMode": True},
                               content_type='application/json')
        print(f"\nTalk Mode Status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            response_text = data.get('response', '')
            print(f"Talk Mode Response: {response_text}")
            print(f"Response Length: {len(response_text)} characters")

def test_educational_mode():
    """Test educational mode"""
    with app.test_client() as client:
        response = client.post('/api/chat', 
                               json={"message": "What is photosynthesis?", "talkMode": False},
                               content_type='application/json')
        print(f"\nEducational Mode Status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            response_text = data.get('response', '')
            print(f"Educational Response Length: {len(response_text)} characters")
            print(f"Preview: {response_text[:150]}...")

if __name__ == "__main__":
    print("🧪 Testing Enhanced Backend Features")
    print("=" * 40)
    
    test_health()
    test_talk_mode()
    test_educational_mode()
    
    print("\n✅ Enhanced backend tests completed!")