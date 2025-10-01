#!/usr/bin/env python3
"""
Debug script to test Groq client initialization
"""
import os
import sys

def debug_groq():
    print("🔍 Debugging Groq Client Initialization")
    print("=" * 50)
    
    # Check Python version
    print(f"🐍 Python version: {sys.version}")
    
    # Check if API key is available
    api_key = os.getenv("GROQ_API_KEY")
    print(f"🔑 GROQ_API_KEY found: {'✅ Yes' if api_key else '❌ No'}")
    if api_key:
        print(f"🔑 API Key length: {len(api_key)}")
        print(f"🔑 API Key preview: {api_key[:10]}...{api_key[-5:]}")
    
    # Check environment variables that might interfere
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
    print("\n🌐 Proxy Environment Variables:")
    for var in proxy_vars:
        value = os.environ.get(var)
        print(f"   {var}: {value if value else 'Not set'}")
    
    # Clear proxy variables
    print("\n🧹 Clearing proxy environment variables...")
    for var in proxy_vars:
        os.environ.pop(var, None)
    
    # Try to import and initialize Groq
    try:
        print("\n📦 Importing Groq...")
        from groq import Groq
        print("✅ Groq imported successfully")
        
        print("🔧 Initializing Groq client...")
        client = Groq(api_key=api_key)
        print("✅ Groq client initialized successfully!")
        
        # Test a simple API call
        print("\n🧪 Testing API call...")
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Say hello!"}],
            temperature=0.7,
            max_tokens=50
        )
        print("✅ API call successful!")
        print(f"📝 Response: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"📋 Error type: {type(e)}")
        import traceback
        print("📋 Full traceback:")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded .env file")
    except ImportError:
        print("⚠️  python-dotenv not available, using system environment")
    
    success = debug_groq()
    if success:
        print("\n🎉 All tests passed! Groq client should work fine.")
    else:
        print("\n💥 Tests failed. Check the errors above.")