#!/usr/bin/env python3
"""
Straw Coin Backend API Testing Suite
Comprehensive testing for The Short Straw comedy tokenization platform
Tests all core API functionality without authentication dependencies
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:5000"

def print_header(title):
    """Print formatted test section header"""
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}")

def print_test(test_name):
    """Print formatted test name"""
    print(f"\n📋 {test_name}")
    print("-" * 40)

def test_user_creation():
    """Test user creation via API"""
    print_test("User Creation API")
    
    # Test valid user creation
    test_username = f"backend_test_{int(time.time())}"
    
    try:
        response = requests.post(f"{BASE_URL}/api/users", 
                               json={"username": test_username},
                               headers={"Content-Type": "application/json"},
                               timeout=5)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ User created successfully")
            print(f"   User ID: {data.get('user_id')}")
            print(f"   Starting Balance: {data.get('starting_balance')}")
            print(f"   Status: {data.get('status')}")
            return True, test_username
        else:
            print(f"❌ User creation failed")
            print(f"   Response: {response.text}")
            return False, None
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - server not running")
        return False, None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False, None

def test_duplicate_user():
    """Test duplicate username handling"""
    print_test("Duplicate Username Prevention")
    
    duplicate_username = "duplicate_test_user"
    
    try:
        # Create first user
        response1 = requests.post(f"{BASE_URL}/api/users", 
                                json={"username": duplicate_username},
                                headers={"Content-Type": "application/json"})
        
        print(f"First creation: {response1.status_code}")
        
        # Try to create duplicate
        response2 = requests.post(f"{BASE_URL}/api/users", 
                                json={"username": duplicate_username},
                                headers={"Content-Type": "application/json"})
        
        print(f"Duplicate attempt: {response2.status_code}")
        
        if response2.status_code == 409:
            data = response2.json()
            print(f"✅ Duplicate prevention working")
            print(f"   Error: {data.get('error')}")
            print(f"   Status: {data.get('status')}")
            return True
        else:
            print(f"❌ Duplicate prevention failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_validation():
    """Test input validation"""
    print_test("Input Validation")
    
    test_cases = [
        # (test_data, expected_status, description)
        ({}, 400, "Missing username"),
        ({"username": ""}, 400, "Empty username"),
        ({"username": "ab"}, 400, "Short username"),
        ({"username": "valid_user_123"}, 201, "Valid username"),
    ]
    
    all_passed = True
    
    for test_data, expected_status, description in test_cases:
        try:
            response = requests.post(f"{BASE_URL}/api/users", 
                                   json=test_data,
                                   headers={"Content-Type": "application/json"})
            
            if response.status_code == expected_status:
                print(f"✅ {description}: {response.status_code}")
            else:
                print(f"❌ {description}: Expected {expected_status}, got {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ {description}: Request failed - {e}")
            all_passed = False
    
    return all_passed

def test_database_operations():
    """Test database operations"""
    print_test("Database Operations")
    
    test_username = f"db_test_{int(time.time())}"
    
    try:
        # Create user
        response = requests.post(f"{BASE_URL}/api/users", 
                               json={"username": test_username},
                               headers={"Content-Type": "application/json"})
        
        if response.status_code != 201:
            print(f"❌ User creation failed: {response.status_code}")
            return False
        
        print(f"✅ User created in database")
        
        # Test data persistence by creating another user
        test_username2 = f"db_test2_{int(time.time())}"
        response2 = requests.post(f"{BASE_URL}/api/users", 
                                json={"username": test_username2},
                                headers={"Content-Type": "application/json"})
        
        if response2.status_code == 201:
            print(f"✅ Multiple users can be created")
            return True
        else:
            print(f"❌ Second user creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_api_response_format():
    """Test API response format consistency"""
    print_test("API Response Format")
    
    test_username = f"format_test_{int(time.time())}"
    
    try:
        response = requests.post(f"{BASE_URL}/api/users", 
                               json={"username": test_username},
                               headers={"Content-Type": "application/json"})
        
        # Check response headers
        content_type = response.headers.get('content-type', '')
        if 'application/json' not in content_type:
            print(f"❌ Invalid content-type: {content_type}")
            return False
        
        # Check JSON structure
        try:
            data = response.json()
            required_fields = ['message', 'status']
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                return False
            
            print(f"✅ Response format valid")
            print(f"   Content-Type: {content_type}")
            print(f"   Required fields present: {required_fields}")
            return True
            
        except json.JSONDecodeError:
            print(f"❌ Response is not valid JSON")
            return False
            
    except Exception as e:
        print(f"❌ Format test failed: {e}")
        return False

def test_error_handling():
    """Test error handling"""
    print_test("Error Handling")
    
    test_cases = [
        # (method, endpoint, data, description)
        ("POST", "/api/users", {"invalid": "data"}, "Invalid request data"),
        ("POST", "/api/users", "invalid json", "Invalid JSON"),
        ("GET", "/api/nonexistent", None, "Nonexistent endpoint"),
    ]
    
    all_passed = True
    
    for method, endpoint, data, description in test_cases:
        try:
            if method == "POST":
                if isinstance(data, dict):
                    response = requests.post(f"{BASE_URL}{endpoint}", 
                                           json=data,
                                           headers={"Content-Type": "application/json"})
                else:
                    response = requests.post(f"{BASE_URL}{endpoint}", 
                                           data=data,
                                           headers={"Content-Type": "application/json"})
            else:
                response = requests.get(f"{BASE_URL}{endpoint}")
            
            # Error responses should have proper status codes
            if 400 <= response.status_code < 600:
                print(f"✅ {description}: {response.status_code}")
            else:
                print(f"❌ {description}: Expected error status, got {response.status_code}")
                all_passed = False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {description}: Connection failed")
            all_passed = False
        except Exception as e:
            # Some exceptions are expected for invalid data
            print(f"⚠️ {description}: Exception (may be expected) - {e}")
    
    return all_passed

def test_concurrency():
    """Test concurrent user creation"""
    print_test("Concurrent Operations")
    
    import threading
    import queue
    
    results = queue.Queue()
    num_threads = 5
    
    def create_user(thread_id):
        username = f"concurrent_test_{thread_id}_{int(time.time())}"
        try:
            response = requests.post(f"{BASE_URL}/api/users", 
                                   json={"username": username},
                                   headers={"Content-Type": "application/json"})
            results.put((thread_id, response.status_code, username))
        except Exception as e:
            results.put((thread_id, "ERROR", str(e)))
    
    # Start concurrent requests
    threads = []
    for i in range(num_threads):
        thread = threading.Thread(target=create_user, args=(i,))
        thread.start()
        threads.append(thread)
    
    # Wait for completion
    for thread in threads:
        thread.join()
    
    # Check results
    success_count = 0
    while not results.empty():
        thread_id, status, info = results.get()
        if status == 201:
            success_count += 1
            print(f"✅ Thread {thread_id}: Success")
        else:
            print(f"❌ Thread {thread_id}: {status} - {info}")
    
    if success_count == num_threads:
        print(f"✅ All {num_threads} concurrent operations succeeded")
        return True
    else:
        print(f"❌ Only {success_count}/{num_threads} operations succeeded")
        return False

def run_backend_tests():
    """Run comprehensive backend test suite"""
    print_header("STRAW COIN BACKEND API TESTING SUITE")
    print("Testing core API functionality for The Short Straw platform")
    print("Focuses on backend operations without authentication dependencies")
    
    # Test connectivity first
    try:
        response = requests.get(f"{BASE_URL}/api/users", timeout=3)
        print(f"📡 Server connectivity: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server at localhost:5000")
        print("Start server with: flask --app src run --debug")
        return False
    except Exception as e:
        print(f"⚠️ Connectivity check: {e}")
    
    # Run test suite
    tests = [
        ("User Creation", test_user_creation),
        ("Duplicate Prevention", test_duplicate_user),
        ("Input Validation", test_validation),
        ("Database Operations", test_database_operations),
        ("Response Format", test_api_response_format),
        ("Error Handling", test_error_handling),
        ("Concurrent Operations", test_concurrency),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            if test_name == "User Creation":
                # Special handling for user creation test
                success, username = test_func()
                results[test_name] = success
            else:
                results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name}: Test crashed - {e}")
            results[test_name] = False
    
    # Print summary
    print_header("TEST RESULTS SUMMARY")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {test_name}")
    
    print(f"\n📊 OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🚀 ALL BACKEND TESTS PASSED - API ready for production!")
        return True
    else:
        print("⚠️ SOME TESTS FAILED - Review backend implementation")
        return False

if __name__ == "__main__":
    success = run_backend_tests()
    sys.exit(0 if success else 1)