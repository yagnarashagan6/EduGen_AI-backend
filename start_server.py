#!/usr/bin/env python3
"""
Simple server launcher that ensures the server stays running
"""

import os
import sys
import time

# Add the current directory to the path
sys.path.insert(0, os.getcwd())

# Import and run the app
from app import app

if __name__ == "__main__":
    print("🚀 Starting EduGen AI Backend Server...")
    print("=" * 50)
    
    # Check environment
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found!")
        sys.exit(1)
    
    print(f"✅ API Key configured: {api_key[:20]}...")
    
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Starting server on port {port}")
    
    try:
        app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)