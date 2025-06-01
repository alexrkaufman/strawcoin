#!/usr/bin/env python3
"""
Straw Coin Authentication & Session Testing Suite
Manual browser testing for session management
"""

import os
import sys

def test_database_initialization():
    db_path = "instance/strawcoin.sqlite"
    if os.path.exists(db_path):
        print("✅ Database file exists")
        return True
    else:
        print("❌ Database file missing - Run: flask --app src init-db")
        return False

def test_flask_debug_mode():
    try:
        import src
        app = src.create_app()
        if app.debug:
            print("✅ Flask in debug mode (30s timeout)")
        else:
            print("⚠️ Flask in production mode (5min timeout)")
        return True
    except Exception as e:
        print(f"❌ Flask config check failed: {e}")
        return False

def test_browser_registration():
    print("Manual test: Browser Registration")
    print("1. Open browser to: http://localhost:5000")
    print("2. Should redirect to registration page")
    print("3. Enter username and submit")
    print("4. Should redirect to home page with dashboard")
    
    result = input("\nDid registration work? (y/n): ").lower().strip()
    
    if result == 'y':
        print("✅ Browser registration working")
        return True
    else:
        print("❌ Browser registration failed")
        return False

def test_browser_session_timeout():
    print("Manual test: Session Timeout")
    print("1. Register a user")
    print("2. Wait 30 seconds WITHOUT activity")
    print("3. Try to refresh or navigate")
    print("4. Should redirect to session expired page")
    
    result = input("\nDid session timeout work? (y/n): ").lower().strip()
    
    if result == 'y':
        print("✅ Session timeout working")
        return True
    else:
        print("❌ Session timeout failed")
        return False

def test_browser_activity_extension():
    print("Manual test: Activity Extension")
    print("1. Register a user")
    print("2. Wait 15 seconds")
    print("3. Scroll or click something")
    print("4. Wait another 20 seconds (total 35s)")
    print("5. Should still be accessible")
    
    result = input("\nDid activity extend session? (y/n): ").lower().strip()
    
    if result == 'y':
        print("✅ Activity extension working")
        return True
    else:
        print("❌ Activity extension failed")
        return False

def test_browser_session_warning():
    print("Manual test: Session Warning")
    print("1. Register a user")
    print("2. Wait ~20 seconds without activity")
    print("3. Should see warning banner")
    print("4. Click banner to extend session")
    
    result = input("\nDid warning appear and work? (y/n): ").lower().strip()
    
    if result == 'y':
        print("✅ Session warning working")
        return True
    else:
        print("❌ Session warning failed")
        return False

def test_multiple_users():
    print("Manual test: Multiple Users")
    print("1. Register 'test_user_1'")
    print("2. Wait for session to expire")
    print("3. Register 'test_user_2'")
    print("4. Check leaderboard shows both users")
    
    result = input("\nCan you register multiple users? (y/n): ").lower().strip()
    
    if result == 'y':
        print("✅ Multiple users working")
        return True
    else:
        print("❌ Multiple users failed")
        return False

def test_home_page_data():
    print("Manual test: Home Page Data")
    print("1. Register multiple users")
    print("2. Check home page shows:")
    print("   - Market cap")
    print("   - User count")
    print("   - Leaderboard")
    
    result = input("\nDoes home page show data correctly? (y/n): ").lower().strip()
    
    if result == 'y':
        print("✅ Home page data working")
        return True
    else:
        print("❌ Home page data failed")
        return False

def run_auth_tests():
    print("🔐 STRAW COIN AUTHENTICATION TESTS")
    print("=" * 40)
    print("Manual browser testing for The Short Straw platform")
    print("Start Flask with: flask --app src run --debug")
    
    input("\nPress Enter when server is ready...")
    
    tests = [
        ("Database", test_database_initialization),
        ("Debug Mode", test_flask_debug_mode),
        ("Registration", test_browser_registration),
        ("Session Timeout", test_browser_session_timeout),
        ("Activity Extension", test_browser_activity_extension),
        ("Session Warning", test_browser_session_warning),
        ("Multiple Users", test_multiple_users),
        ("Home Page Data", test_home_page_data),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            results.append(test_func())
        except KeyboardInterrupt:
            print(f"❌ Test interrupted")
            results.append(False)
            break
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    print(f"\n📊 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🚀 ALL TESTS PASSED - Ready for The Short Straw!")
        return True
    else:
        print("⚠️ SOME TESTS FAILED")
        return False

if __name__ == "__main__":
    success = run_auth_tests()
    sys.exit(0 if success else 1)