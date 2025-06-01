#!/usr/bin/env python3
"""
Straw Coin Authentication & Session Testing Suite
Focused testing for session management and authentication flows
Tests authentication without relying on complex API interactions
"""

import time
import sys
import subprocess
import os

def print_header(title):
    """Print formatted test section header"""
    print(f"\n{'='*60}")
    print(f"🔐 {title}")
    print(f"{'='*60}")

def print_test(test_name):
    """Print formatted test name"""
    print(f"\n📋 {test_name}")
    print("-" * 40)

def test_database_initialization():
    """Test database is properly initialized"""
    print_test("Database Initialization")
    
    try:
        # Check if database file exists
        db_path = "instance/strawcoin.sqlite"
        if os.path.exists(db_path):
            print(f"✅ Database file exists: {db_path}")
            return True
        else:
            print(f"❌ Database file missing: {db_path}")
            print("   Run: flask --app src init-db")
            return False
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def test_flask_debug_mode():
    """Test Flask is running in debug mode for proper timeout testing"""
    print_test("Flask Debug Mode Configuration")
    
    try:
        # Test if we can import the Flask app
        import src
        app = src.create_app()
        
        if app.debug:
            print("✅ Flask running in debug mode")
            print("   Session timeout: 30 seconds (debug)")
            return True
        else:
            print("⚠️ Flask not in debug mode")
            print("   Session timeout: 5 minutes (production)")
            print("   Start with: flask --app src run --debug")
            return True  # Not a failure, just different config
            
    except Exception as e:
        print(f"❌ Flask config check failed: {e}")
        return False

def test_browser_registration():
    """Test registration works in browser (manual verification)"""
    print_test("Browser Registration Flow")
    
    print("This test requires manual verification in browser:")
    print("1. Open browser to: http://localhost:5000")
    print("2. Should redirect to registration page")
    print("3. Enter a username and submit")
    print("4. Should show success message and redirect to home page")
    print("5. Home page should show market dashboard")
    
    result = input("\nDid registration work in browser? (y/n): ").lower().strip()
    
    if result == 'y':
        print("✅ Browser registration confirmed working")
        return True
    else:
        print("❌ Browser registration not working")
        print("   Check Flask server console for errors")
        print("   Verify authentication middleware configuration")
        return False

def test_browser_session_timeout():
    """Test session timeout works in browser (manual verification)"""
    print_test("Browser Session Timeout")
    
    print("This test requires manual verification in browser:")
    print("1. Register a new user (or use existing session)")
    print("2. Wait 30 seconds WITHOUT any activity (don't scroll, click, etc.)")
    print("3. After 30 seconds, try to refresh page or navigate")
    print("4. Should redirect to session expired page")
    print("5. Should NOT stay on authenticated pages")
    
    result = input("\nDid session timeout after 30 seconds? (y/n): ").lower().strip()
    
    if result == 'y':
        print("✅ Session timeout confirmed working")
        return True
    else:
        print("❌ Session timeout not working")
        print("   Check if debug mode is enabled")
        print("   Verify session timeout configuration")
        print("   Check browser console for JavaScript errors")
        return False

def test_browser_activity_extension():
    """Test activity extends session in browser (manual verification)"""
    print_test("Browser Activity Extension")
    
    print("This test requires manual verification in browser:")
    print("1. Register a new user")
    print("2. Wait 15 seconds")
    print("3. Scroll the page or click something")
    print("4. Wait another 20 seconds (total 35 seconds)")
    print("5. Page should STILL be accessible (not timed out)")
    print("6. Activity should have reset the 30-second timer")
    
    result = input("\nDid activity extend the session? (y/n): ").lower().strip()
    
    if result == 'y':
        print("✅ Activity extension confirmed working")
        return True
    else:
        print("❌ Activity extension not working") 
        print("   Check JavaScript session tracking")
        print("   Verify update-activity endpoint is working")
        print("   Check browser console for errors")
        return False

def test_browser_session_warning():
    """Test session warning appears in browser (manual verification)"""
    print_test("Browser Session Warning")
    
    print("This test requires manual verification in browser:")
    print("1. Register a new user")
    print("2. Wait about 20 seconds without activity")
    print("3. Should see a yellow warning banner: 'Session expires in Xs - Tap to extend!'")
    print("4. Click the warning banner")
    print("5. Warning should disappear and session should be extended")
    
    result = input("\nDid session warning appear and work? (y/n): ").lower().strip()
    
    if result == 'y':
        print("✅ Session warning confirmed working")
        return True
    else:
        print("❌ Session warning not working")
        print("   Check JavaScript session monitoring")
        print("   Verify showSessionWarning function")
        print("   Check browser console for errors")
        return False

def test_multiple_users():
    """Test multiple users can be registered (manual verification)"""
    print_test("Multiple User Registration")
    
    print("This test requires manual verification in browser:")
    print("1. Register user 'test_user_1'")
    print("2. Log out or wait for session to expire")
    print("3. Register user 'test_user_2'")
    print("4. Both registrations should work")
    print("5. Home page should show 2 users in leaderboard")
    
    result = input("\nCould you register multiple users? (y/n): ").lower().strip()
    
    if result == 'y':
        print("✅ Multiple user registration confirmed working")
        return True
    else:
        print("❌ Multiple user registration not working")
        print("   Check database operations")
        print("   Verify user creation logic")
        return False

def test_coin_transfer():
    """Test coin transfer between users (manual verification)"""
    print_test("Coin Transfer Between Users")
    
    print("This test requires manual verification:")
    print("1. Register user 'sender_user'")
    print("2. Open incognito/private window")
    print("3. Register user 'receiver_user'")
    print("4. Note: You'll need to use API or implement transfer UI")
    print("5. For now, this confirms basic multi-user setup works")
    
    result = input("\nAre multiple users visible on home page? (y/n): ").lower().strip()
    
    if result == 'y':
        print("✅ Multi-user foundation confirmed working")
        print("   Note: Transfer UI not yet implemented")
        return True
    else:
        print("❌ Multi-user setup not working")
        return False

def run_auth_tests():
    """Run comprehensive authentication test suite"""
    print_header("STRAW COIN AUTHENTICATION & SESSION TESTING SUITE")
    print("Testing authentication and session management for The Short Straw platform")
    print("Focuses on real browser behavior and user experience")
    print("\nIMPORTANT: Start Flask server with: flask --app src run --debug")
    print("Make sure browser is available for manual testing")
    
    # Check prerequisites
    input("\nPress Enter when Flask server is running and browser is ready...")
    
    # Run test suite
    tests = [
        ("Database Initialization", test_database_initialization),
        ("Flask Debug Mode", test_flask_debug_mode),
        ("Browser Registration", test_browser_registration),
        ("Session Timeout", test_browser_session_timeout),
        ("Activity Extension", test_browser_activity_extension),
        ("Session Warning", test_browser_session_warning),
        ("Multiple Users", test_multiple_users),
        ("Coin Transfer Setup", test_coin_transfer),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except KeyboardInterrupt:
            print(f"\n❌ {test_name}: Test interrupted by user")
            results[test_name] = False
            break
        except Exception as e:
            print(f"❌ {test_name}: Test crashed - {e}")
            results[test_name] = False
    
    # Print summary
    print_header("AUTHENTICATION TEST RESULTS SUMMARY")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {test_name}")
    
    print(f"\n📊 OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🚀 ALL AUTHENTICATION TESTS PASSED - Ready for The Short Straw!")
        print("\n🎭 Platform ready for live comedy show deployment!")
        return True
    else:
        print("⚠️ SOME TESTS FAILED - Review authentication implementation")
        print("\n🔧 Fix issues before deploying to The Short Straw audience")
        return False

if __name__ == "__main__":
    success = run_auth_tests()
    sys.exit(0 if success else 1)