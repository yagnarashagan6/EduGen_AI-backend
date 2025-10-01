import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def test_groq_directly():
    """Test Groq API directly to see if the issue is with the API key or configuration"""
    
    # Get API key from environment
    api_key = os.getenv("GROQ_API_KEY")
    print(f"🔑 API Key found: {'Yes' if api_key else 'No'}")
    if api_key:
        print(f"🔑 API Key (first 10 chars): {api_key[:10]}...")
    
    try:
        # Initialize Groq client
        print("🔧 Initializing Groq client...")
        client = Groq(api_key=api_key)
        print("✅ Groq client initialized successfully!")
        
        # Test API call
        print("🧪 Testing API call...")
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": "Say hello in one sentence."}
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        print("✅ API call successful!")
        print(f"📥 Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"❌ Error type: {type(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Groq API directly...\n")
    success = test_groq_directly()
    
    if success:
        print("\n🎉 Groq API is working correctly!")
    else:
        print("\n⚠️ Groq API test failed.")