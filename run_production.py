#!/usr/bin/env python3
"""
Straw Coin Production Startup Script
Ensures production configuration is loaded with correct session timeouts
"""

import os
import sys

def main():
    # Import Flask app
    from src import create_app
    
    app = create_app()
    
    # Verify production configuration
    timeout = app.config.get("SESSION_TIMEOUT_SECONDS", 0)
    debug = app.debug
    redistribution = app.config.get("ENABLE_PERFORMER_REDISTRIBUTION", False)
    
    print("🚀 Straw Coin Production Server")
    print("=" * 40)
    print(f"Session timeout: {timeout} seconds")
    print(f"Debug mode: {debug}")
    print(f"Performer redistribution: {redistribution}")
    
    if timeout != 300:
        print("⚠️  WARNING: Expected 300s timeout for production!")
        print("Check that Flask is not running in debug mode.")
        return 1
    
    if debug:
        print("⚠️  WARNING: Debug mode is still enabled!")
        print("Run with 'flask run' (without --debug) for production mode.")
        return 1
    
    print("✅ Production configuration verified")
    print(f"Starting server on http://0.0.0.0:5000")
    print("Press Ctrl+C to stop")
    
    # Run the app
    try:
        app.run(host="0.0.0.0", port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        return 0

if __name__ == "__main__":
    sys.exit(main())