#!/usr/bin/env python3
"""
Quick test to verify Gemini API integration
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gemini_connection():
    """Test basic Gemini API connection"""
    
    # Check if API key is set
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY environment variable not set!")
        print("Please create a .env file with your Google API key:")
        print("GOOGLE_API_KEY=your_api_key_here")
        return False
    
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Initialize model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Test with a simple prompt
        print("🧪 Testing Gemini API connection...")
        response = model.generate_content("Say hello and confirm you are working")
        
        print("✅ Gemini API is working!")
        print(f"Response: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ Gemini API test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Gemini API Connection Test")
    print("=" * 50)
    
    success = test_gemini_connection()
    
    if success:
        print("\n🎉 Your backend is ready to use Gemini API!")
    else:
        print("\n⚠️ Please check your API key and try again.")