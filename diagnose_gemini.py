#!/usr/bin/env python3
"""
Detailed Gemini API diagnostic test
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def diagnose_gemini_setup():
    """Detailed diagnosis of Gemini API setup"""
    
    print("🔍 Diagnosing Gemini API Setup...")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY environment variable not set!")
        return False
    
    print(f"✅ API Key found: {api_key[:20]}...")
    print(f"   Length: {len(api_key)} characters")
    print(f"   Starts with: {api_key[:5]}")
    
    # Check key format
    if not api_key.startswith("AIza"):
        print("⚠️  Warning: API key doesn't start with 'AIza' - might be wrong format")
    else:
        print("✅ API key format looks correct")
    
    try:
        # Configure Gemini
        print("\n🔧 Configuring Gemini API...")
        genai.configure(api_key=api_key)
        print("✅ API configured successfully")
        
        # Test with list models first (less likely to fail)
        print("\n📋 Testing model list access...")
        models = list(genai.list_models())
        print(f"✅ Found {len(models)} available models")
        
        # Find available generative models
        generative_models = [m for m in models if 'generateContent' in m.supported_generation_methods]
        print(f"✅ Found {len(generative_models)} generative models")
        
        if generative_models:
            print("Available models:")
            for model in generative_models[:3]:  # Show first 3
                print(f"  - {model.name}")
        
        # Test actual generation
        print("\n🧪 Testing content generation...")
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say 'Hello, Gemini is working!'")
        
        print("✅ Content generation successful!")
        print(f"Response: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        
        # Additional troubleshooting info
        print("\n🔧 Troubleshooting Tips:")
        print("1. Make sure you created the API key from: https://makersuite.google.com/app/apikey")
        print("2. Ensure the Generative Language API is enabled in your Google Cloud project")
        print("3. Check that your API key has the correct permissions")
        print("4. Try creating a new API key if this one doesn't work")
        
        return False

if __name__ == "__main__":
    success = diagnose_gemini_setup()
    
    if success:
        print("\n🎉 Gemini API is working perfectly!")
    else:
        print("\n❌ Gemini API setup needs attention")