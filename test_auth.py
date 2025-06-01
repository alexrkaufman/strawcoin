#!/usr/bin/env python3
"""
Straw Coin Authentication Testing Suite
Validates mobile-optimized registration and session management for The Short Straw platform
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_registration_flow():
    """
    Tests complete stakeholder onboarding flow from registration to authenticated access
    """
    print("🚀 Testing Revolutionary Registration Flow...")
    
    # Test 1: Register new user via login endpoint
    print("\n1. Testing unified registration/login endpoint...")
    test_username = f"test_trader_{int(time.time())}"
    
    response = requests.post(f"{BASE_URL}/login", 
                           json={"username": test_username},
                           headers={"Content-Type": "application/json"})
    
    print(f"Registration Response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data}")
        
        # Extract session cookie for subsequent requests
        session_cookie = response.cookies.get('straw_coin_session')
        print(f"Session Cookie: {session_cookie is not None}")
        
        return session_cookie, test_username
    else:
        print(f"Registration Failed: {response.text}")
        return None, None

def test_authenticated_access(session_cookie, username):
    """
    Tests authenticated access to protected endpoints
    """
    print("\n2. Testing authenticated access...")
    
    if not session_cookie:
        print("No session cookie available for testing")
        return
    
    cookies = {'straw_coin_session': session_cookie}
    
    # Test home page access
    response = requests.get(f"{BASE_URL}/", cookies=cookies)
    print(f"Home Page Access: {response.status_code}")
    
    # Test API access
    response = requests.get(f"{BASE_URL}/api/market-stats", cookies=cookies)
    print(f"Market Stats API: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Market Data: {data}")

def test_session_status(session_cookie):
    """
    Tests session monitoring and status endpoints
    """
    print("\n3. Testing session status monitoring...")
    
    if not session_cookie:
        print("No session cookie available for testing")
        return
    
    cookies = {'straw_coin_session': session_cookie}
    
    response = requests.get(f"{BASE_URL}/session-status", cookies=cookies)
    print(f"Session Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Session Data: {data}")

def test_duplicate_registration():
    """
    Tests duplicate username handling
    """
    print("\n4. Testing duplicate username prevention...")
    
    # Try to register same username twice
    test_username = "duplicate_test_user"
    
    # First registration
    response1 = requests.post(f"{BASE_URL}/login", 
                            json={"username": test_username},
                            headers={"Content-Type": "application/json"})
    print(f"First Registration: {response1.status_code}")
    
    # Second registration (should handle existing user)
    response2 = requests.post(f"{BASE_URL}/login", 
                            json={"username": test_username},
                            headers={"Content-Type": "application/json"})
    print(f"Second Registration: {response2.status_code}")
    if response2.status_code == 200:
        data = response2.json()
        print(f"Existing User Login: {data}")

def test_unauthenticated_access():
    """
    Tests protection of authenticated endpoints
    """
    print("\n5. Testing unauthenticated access protection...")
    
    # Try to access home page without authentication
    response = requests.get(f"{BASE_URL}/")
    print(f"Unauthenticated Home Access: {response.status_code}")
    print(f"Redirect Location: {response.url}")
    
    # Try to access API without authentication
    response = requests.get(f"{BASE_URL}/api/market-stats")
    print(f"Unauthenticated API Access: {response.status_code}")

def test_invalid_registration():
    """
    Tests validation and error handling
    """
    print("\n6. Testing validation and error handling...")
    
    # Test missing username
    response = requests.post(f"{BASE_URL}/login", 
                           json={},
                           headers={"Content-Type": "application/json"})
    print(f"Missing Username: {response.status_code}")
    if response.status_code != 200:
        print(f"Error Response: {response.json()}")
    
    # Test short username
    response = requests.post(f"{BASE_URL}/login", 
                           json={"username": "ab"},
                           headers={"Content-Type": "application/json"})
    print(f"Short Username: {response.status_code}")
    if response.status_code != 200:
        print(f"Error Response: {response.json()}")
    
    # Test empty username
    response = requests.post(f"{BASE_URL}/login", 
                           json={"username": ""},
                           headers={"Content-Type": "application/json"})
    print(f"Empty Username: {response.status_code}")
    if response.status_code != 200:
        print(f"Error Response: {response.json()}")

def run_comprehensive_auth_testing():
    """
    Executes complete authentication system validation
    """
    print("🌙 STRAW COIN AUTHENTICATION TESTING SUITE")
    print("==========================================")
    print("Validating mobile-optimized stakeholder onboarding for The Short Straw\n")
    
    try:
        # Test main registration flow
        session_cookie, username = test_registration_flow()
        
        # Test authenticated access if registration succeeded
        if session_cookie:
            test_authenticated_access(session_cookie, username)
            test_session_status(session_cookie)
        
        # Test edge cases
        test_duplicate_registration()
        test_unauthenticated_access()
        test_invalid_registration()
        
        print("\n🚀 AUTHENTICATION TESTING COMPLETED!")
        print("Ready for maximum stakeholder onboarding during The Short Straw!")
        
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Please ensure Flask development server is running")
        print("Start server with: flask --app src run --debug")
    except Exception as e:
        print(f"❌ TESTING ERROR: {e}")

if __name__ == "__main__":
    run_comprehensive_auth_testing()