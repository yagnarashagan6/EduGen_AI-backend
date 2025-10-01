"""
Minimal Groq client test - for Render deployment debugging
"""
import os

# Clear ALL possible proxy-related environment variables
proxy_vars = [
    'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
    'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy',
    'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE'
]

for var in proxy_vars:
    if var in os.environ:
        del os.environ[var]

def test_minimal_groq():
    """Test Groq with absolute minimal configuration"""
    try:
        print("Starting minimal Groq test...")
        
        # Get API key
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("❌ GROQ_API_KEY not found in environment")
            return False
        
        print(f"✅ API key found (length: {len(api_key)})")
        
        # Import Groq
        from groq import Groq
        print("✅ Groq imported")
        
        # Initialize with absolute minimal params
        client = Groq(api_key=api_key)
        print("✅ Groq client created")
        
        # Test API call
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        print("✅ API call successful")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_minimal_groq()