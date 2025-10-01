#!/usr/bin/env python3
"""
Debug script to test environment before starting the main app
"""
import os
import sys

def debug_environment():
    """Debug the deployment environment"""
    print("🔍 Environment Debug Information")
    print("=" * 50)
    
    # Python version
    print(f"🐍 Python version: {sys.version}")
    
    # Environment variables (excluding sensitive ones)
    print("\n📋 Environment variables:")
    for key in sorted(os.environ.keys()):
        if any(term in key.lower() for term in ['proxy', 'http', 'curl', 'request']):
            print(f"  {key}: {os.environ[key]}")
    
    # Check if GROQ_API_KEY exists
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        print(f"✅ GROQ_API_KEY found (length: {len(groq_key)})")
    else:
        print("❌ GROQ_API_KEY not found")
    
    # Test Groq import and initialization
    try:
        print("\n🧪 Testing Groq import...")
        from groq import Groq
        import groq
        print(f"✅ Groq imported successfully")
        print(f"📦 Groq version: {getattr(groq, '__version__', 'unknown')}")
        
        if groq_key:
            print("\n🧪 Testing Groq client initialization...")
            client = Groq(api_key=groq_key)
            print("✅ Groq client created successfully")
        
    except Exception as e:
        print(f"❌ Groq test failed: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")
    
    print("\n" + "=" * 50)
    print("🚀 Starting main application...")

if __name__ == "__main__":
    debug_environment()
    
    # Import and run the main app
    try:
        import app
        print("✅ Main app imported successfully")
    except Exception as e:
        print(f"❌ Failed to import main app: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")
        sys.exit(1)