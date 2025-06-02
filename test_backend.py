#!/usr/bin/env python3
"""
Straw Coin Backend API Testing Suite
Tests core API functionality for The Short Straw platform
"""

import requests
import time
import sys

BASE_URL = "http://localhost:5000"


def test_user_creation():
    test_username = f"test_{int(time.time())}"
    response = requests.post(
        f"{BASE_URL}/api/users",
        json={"username": test_username},
        headers={"Content-Type": "application/json"},
    )

    if response.status_code == 201:
        print("✅ User creation working")
        return True
    else:
        print(f"❌ User creation failed: {response.status_code}")
        return False


def test_duplicate_user():
    duplicate_username = "duplicate_test"

    # Create first user
    requests.post(f"{BASE_URL}/api/users", json={"username": duplicate_username})

    # Try duplicate
    response = requests.post(
        f"{BASE_URL}/api/users", json={"username": duplicate_username}
    )

    if response.status_code == 409:
        print("✅ Duplicate prevention working")
        return True
    else:
        print(f"❌ Duplicate prevention failed: {response.status_code}")
        return False


def test_validation():
    test_cases = [
        ({}, 400),
        ({"username": ""}, 400),
        ({"username": "ab"}, 400),
        ({"username": "valid_user"}, 201),
    ]

    for test_data, expected_status in test_cases:
        response = requests.post(f"{BASE_URL}/api/users", json=test_data)
        if response.status_code != expected_status:
            print(f"❌ Validation failed for {test_data}")
            return False

    print("✅ Input validation working")
    return True


def test_database_operations():
    test_username1 = f"db_test1_{int(time.time())}"
    test_username2 = f"db_test2_{int(time.time())}"

    response1 = requests.post(
        f"{BASE_URL}/api/users", json={"username": test_username1}
    )
    response2 = requests.post(
        f"{BASE_URL}/api/users", json={"username": test_username2}
    )

    if response1.status_code == 201 and response2.status_code == 201:
        print("✅ Database operations working")
        return True
    else:
        print("❌ Database operations failed")
        return False


def test_api_response_format():
    test_username = f"format_test_{int(time.time())}"
    response = requests.post(f"{BASE_URL}/api/users", json={"username": test_username})

    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        print(f"❌ Invalid content-type: {content_type}")
        return False

    try:
        data = response.json()
        required_fields = ["message", "status"]
        if all(field in data for field in required_fields):
            print("✅ Response format valid")
            return True
        else:
            print("❌ Missing required fields")
            return False
    except:
        print("❌ Response is not valid JSON")
        return False


def test_error_handling():
    # Test invalid data
    response = requests.post(f"{BASE_URL}/api/users", json={"invalid": "data"})
    if 400 <= response.status_code < 600:
        print("✅ Error handling working")
        return True
    else:
        print("❌ Error handling failed")
        return False


def test_concurrency():
    import threading

    results = []
    num_threads = 3

    def create_user(thread_id):
        username = f"concurrent_{thread_id}_{int(time.time())}"
        response = requests.post(f"{BASE_URL}/api/users", json={"username": username})
        results.append(response.status_code == 201)

    threads = []
    for i in range(num_threads):
        thread = threading.Thread(target=create_user, args=(i,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    if all(results):
        print("✅ Concurrent operations working")
        return True
    else:
        print("❌ Concurrent operations failed")
        return False


def run_backend_tests():
    print("🚀 STRAW COIN BACKEND TESTS")
    print("=" * 40)

    # Test connectivity
    try:
        requests.get(f"{BASE_URL}/api/users", timeout=3)
        print("✅ Server responding")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server")
        print("Start with: flask --app src run --debug")
        return False

    # Run tests
    tests = [
        ("User Creation", test_user_creation),
        ("Duplicate Prevention", test_duplicate_user),
        ("Input Validation", test_validation),
        ("Database Operations", test_database_operations),
        ("Response Format", test_api_response_format),
        ("Error Handling", test_error_handling),
        ("Concurrent Operations", test_concurrency),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        try:
            results.append(test_func())
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append(False)

    # Summary
    passed = sum(results)
    total = len(results)
    print(f"\n📊 RESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("🚀 ALL TESTS PASSED")
        return True
    else:
        print("⚠️ SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    success = run_backend_tests()
    sys.exit(0 if success else 1)
