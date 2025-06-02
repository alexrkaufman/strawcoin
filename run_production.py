#!/usr/bin/env python3
"""
Straw Coin Production Startup Script
Ensures production configuration is loaded with correct session timeouts
"""

import os
import sys

def main():
    # Set production environment variables
    os.environ["FLASK_ENV"] = "production"
    os.environ["ENVIRONMENT"] = "production"
    os.environ["ENV"] = "production"
    
    # Import Flask app after setting environment
    from src import create_app
    
    app = create_app()
    
    # Verify production configuration
    timeout = app.config.get("SESSION_TIMEOUT_SECONDS", 0)
    debug = app.config.get("DEBUG", True)
    redistribution = app.config.get("ENABLE_PERFORMER_REDISTRIBUTION", False)
    
    print("🚀 Straw Coin Production Server")
    print("=" * 40)
    print(f"Session timeout: {timeout} seconds")
    print(f"Debug mode: {debug}")
    print(f"Performer redistribution: {redistribution}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'unknown')}")
    
    if timeout != 300:
        print("⚠️  WARNING: Expected 300s timeout for production!")
        print("Check your environment variables and configuration.")
        return 1
    
    if debug:
        print("⚠️  WARNING: Debug mode is still enabled!")
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