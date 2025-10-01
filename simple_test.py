import requests
import json
import time

def simple_test():
    time.sleep(2)  # Wait for server to be ready
    
    try:
        # Test health endpoint
        print("🔍 Testing health endpoint...")
        health_response = requests.get("http://127.0.0.1:10000/api/health", timeout=5)
        print(f"Health: {health_response.status_code}")
        
        # Test chat endpoint
        print("🧪 Testing AI chat...")
        chat_data = {"message": "What is AI? Please answer with bullet points."}
        chat_response = requests.post(
            "http://127.0.0.1:10000/api/chat",
            headers={"Content-Type": "application/json"},
            json=chat_data,
            timeout=30
        )
        
        print(f"Chat Status: {chat_response.status_code}")
        if chat_response.status_code == 200:
            result = chat_response.json()
            print("🎉 AI Response:")
            print(result.get('response', 'No response'))
        else:
            print(f"❌ Error: {chat_response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    simple_test()