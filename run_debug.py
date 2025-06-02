import os
import sys
import argparse
from src import create_app

def main():
    """Run the app in debug mode with development configuration."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run Straw Coin in debug mode')
    parser.add_argument('--port', '-p', type=int, default=5001, 
                       help='Port to run on (default: 5001)')
    parser.add_argument('--host', default='127.0.0.1',
                       help='Host to bind to (default: 127.0.0.1)')
    args = parser.parse_args()
    
    print("🐛 Starting Straw Coin in DEBUG mode...")
    print("=" * 40)
    
    # Force debug mode
    os.environ['FLASK_DEBUG'] = '1'
    
    # Import and create app
    app = create_app()
    
    # Force development config
    from src.config import DevelopmentConfig
    app.config.from_object(DevelopmentConfig)
    
    # Display debug configuration
    print(f"   Debug mode: ON")
    print(f"   Session timeout: {app.config.get('SESSION_TIMEOUT_SECONDS')} seconds")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Performer redistribution: {app.config.get('ENABLE_PERFORMER_REDISTRIBUTION', False)}")
    print("=" * 40)
    print("📝 Debug session timeout is 30 seconds for easy testing")
    print("🔄 Auto-reload enabled - code changes will restart server")
    print(f"🌐 Access at: http://{args.host}:{args.port}")
    print("=" * 40)
    
    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=True,
            use_reloader=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Debug server stopped")
    except Exception as e:
        print(f"❌ Error starting debug server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()