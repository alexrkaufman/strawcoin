#!/usr/bin/env python3
"""
Test script to verify session conflict detection
Tests that multiple logins with the same username are prevented
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_session_conflict():
    """Test that multiple sessions for the same user are prevented"""
    print("🔐 Testing Session Conflict Detection")
    print("=" * 40)
    
    username = "test_conflict_user"
    
    # Clear any existing sessions first
    print("1. Clearing any existing sessions...")
    clear_sessions()
    
    # First login - should succeed
    print(f"2. First login attempt for '{username}'...")
    response1 = login_user(username)
    
    if response1 and response1.get("status") == "authentication_successful":
        print("✅ First login successful")
        session1_cookies = response1.get("cookies")
    else:
        print("❌ First login failed")
        return False
    
    # Second login attempt - should fail with session conflict
    print(f"3. Second login attempt for '{username}' (should fail)...")
    response2 = login_user(username)
    
    if response2 and response2.get("status") == "session_conflict":
        print("✅ Second login correctly blocked - session conflict detected")
        return True
    else:
        print(f"❌ Second login should have failed but got: {response2}")
        return False

def test_session_timeout_allows_new_login():
    """Test that after session timeout, new login is allowed"""
    print("\n⏰ Testing Session Timeout Recovery")
    print("=" * 40)
    
    username = "test_timeout_user"
    
    # Clear any existing sessions first
    print("1. Clearing any existing sessions...")
    clear_sessions()
    
    # First login
    print(f"2. First login for '{username}'...")
    response1 = login_user(username)
    
    if not response1 or response1.get("status") != "authentication_successful":
        print("❌ First login failed")
        return False
    
    print("✅ First login successful")
    
    # Wait for session to timeout (development timeout is 30 seconds)
    print("3. Waiting for session timeout (35 seconds)...")
    time.sleep(35)
    
    # Try login again - should succeed now
    print(f"4. Second login attempt after timeout...")
    response2 = login_user(username)
    
    if response2 and response2.get("status") == "authentication_successful":
        print("✅ Login after timeout successful - session conflict resolved")
        return True
    else:
        print(f"❌ Login after timeout failed: {response2}")
        return False

def login_user(username):
    """Attempt to login a user"""
    try:
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/login",
            json={"username": username},
            headers={"Content-Type": "application/json"}
        )
        
        data = response.json()
        data["cookies"] = dict(session.cookies)
        return data
        
    except Exception as e:
        print(f"Login error: {e}")
        return None

def clear_sessions():
    """Clear all active sessions using Flask CLI"""
    import subprocess
    try:
        result = subprocess.run(
            ["flask", "--app", "src", "clear-sessions", "--yes"],
            cwd=".",
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("Sessions cleared")
        else:
            print(f"Failed to clear sessions: {result.stderr}")
    except Exception as e:
        print(f"Could not clear sessions: {e}")

def test_manual_logout():
    """Test manual logout functionality"""
    print("\n🚪 Testing Manual Logout")
    print("=" * 40)
    
    username = "test_logout_user"
    
    # Clear sessions first
    print("1. Clearing sessions...")
    clear_sessions()
    
    # Login
    print(f"2. Login for '{username}'...")
    response1 = login_user(username)
    
    if not response1 or response1.get("status") != "authentication_successful":
        print("❌ Login failed")
        return False
    
    print("✅ Login successful")
    
    # Logout
    print("3. Attempting logout...")
    try:
        session = requests.Session()
        # Set cookies from login
        for key, value in response1.get("cookies", {}).items():
            session.cookies.set(key, value)
            
        logout_response = session.post(f"{BASE_URL}/logout")
        logout_data = logout_response.json()
        
        if logout_data.get("status") == "logout_successful":
            print("✅ Logout successful")
        else:
            print(f"❌ Logout failed: {logout_data}")
            return False
            
    except Exception as e:
        print(f"Logout error: {e}")
        return False
    
    # Try to login again - should succeed now
    print(f"4. Login again after logout...")
    response2 = login_user(username)
    
    if response2 and response2.get("status") == "authentication_successful":
        print("✅ Login after logout successful")
        return True
    else:
        print(f"❌ Login after logout failed: {response2}")
        return False

def main():
    print("🧪 STRAW COIN SESSION CONFLICT TESTS")
    print("Make sure Flask server is running: flask --app src run --debug")
    
    input("\nPress Enter when server is ready...")
    
    tests = [
        ("Session Conflict Detection", test_session_conflict),
        ("Session Timeout Recovery", test_session_timeout_allows_new_login),
        ("Manual Logout", test_manual_logout)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        try:
            result = test_func()
            results.append(result)
            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} CRASHED: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    print(f"\n{'='*50}")
    print(f"📊 FINAL RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🚀 ALL TESTS PASSED - Session conflict detection working!")
        return True
    else:
        print("⚠️ SOME TESTS FAILED - Check implementation")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)