#!/usr/bin/env python3
"""
Test script for performer redistribution system
Tests automatic coin redistribution from performers to audience members
"""

import requests
import json
import time
import subprocess

BASE_URL = "http://localhost:5000"

def run_flask_command(command):
    """Run a Flask CLI command"""
    try:
        result = subprocess.run(
            ["flask", "--app", "src"] + command.split(),
            cwd=".",
            capture_output=True,
            text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def clear_all_data():
    """Reset database for clean testing"""
    print("🗑️ Clearing all data...")
    success, stdout, stderr = run_flask_command("reset-db --yes")
    if success:
        print("✅ Database reset")
    else:
        print(f"❌ Database reset failed: {stderr}")
    return success

def create_test_users():
    """Create test performers and audience members"""
    print("👥 Creating test users...")
    
    # Create performers
    performers = ["comedian1", "comedian2"]
    audience = ["viewer1", "viewer2", "viewer3"]
    
    try:
        from src import create_app
        from src.db import create_user
        
        app = create_app()
        with app.app_context():
            # Create performers
            for performer in performers:
                create_user(performer, is_performer=True)
                print(f"   Created performer: {performer}")
            
            # Create audience members
            for viewer in audience:
                create_user(viewer, is_performer=False)
                print(f"   Created audience: {viewer}")
                
        return True
    except Exception as e:
        print(f"❌ Failed to create users: {e}")
        return False

def check_initial_balances():
    """Verify initial balances are correct"""
    print("💰 Checking initial balances...")
    
    success, stdout, stderr = run_flask_command("list-performers")
    if success:
        print("✅ Initial balances verified")
        print(stdout)
        return True
    else:
        print(f"❌ Failed to check balances: {stderr}")
        return False

def test_manual_redistribution():
    """Test manual redistribution command"""
    print("🔄 Testing manual redistribution...")
    
    success, stdout, stderr = run_flask_command("redistribute-performer-coins")
    if success:
        print("✅ Manual redistribution successful")
        print(stdout)
        return True
    else:
        print(f"❌ Manual redistribution failed: {stderr}")
        return False

def check_balances_after_redistribution():
    """Check balances after redistribution"""
    print("📊 Checking balances after redistribution...")
    
    success, stdout, stderr = run_flask_command("list-performers")
    if success:
        print("✅ Post-redistribution balances:")
        print(stdout)
        return True
    else:
        print(f"❌ Failed to check post-redistribution balances: {stderr}")
        return False

def test_api_endpoints():
    """Test performer-related API endpoints"""
    print("🌐 Testing API endpoints...")
    
    try:
        # Test performers list endpoint
        session = requests.Session()
        
        # Login as a test user first
        login_response = session.post(
            f"{BASE_URL}/login",
            json={"username": "viewer1"},
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return False
        
        # Test performers API
        performers_response = session.get(f"{BASE_URL}/api/performers")
        if performers_response.status_code == 200:
            data = performers_response.json()
            print(f"✅ Performers API: {data['performer_count']} performers, {data['audience_count']} audience")
        else:
            print(f"❌ Performers API failed: {performers_response.text}")
            return False
        
        # Test manual redistribution API
        redistribution_response = session.post(f"{BASE_URL}/api/performers/redistribute")
        if redistribution_response.status_code == 200:
            data = redistribution_response.json()
            print(f"✅ Redistribution API: {data['message']}")
        else:
            print(f"❌ Redistribution API failed: {redistribution_response.text}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False

def test_performer_status_change():
    """Test changing user performer status"""
    print("🔄 Testing performer status changes...")
    
    # Change viewer1 to performer
    success, stdout, stderr = run_flask_command("set-performer viewer1 --performer")
    if not success:
        print(f"❌ Failed to set performer status: {stderr}")
        return False
    
    print("✅ Changed viewer1 to performer")
    
    # Change back to audience
    success, stdout, stderr = run_flask_command("set-performer viewer1 --audience")
    if not success:
        print(f"❌ Failed to set audience status: {stderr}")
        return False
    
    print("✅ Changed viewer1 back to audience")
    return True

def test_automatic_redistribution():
    """Test that automatic redistribution is working"""
    print("⏰ Testing automatic redistribution (waiting 65 seconds)...")
    
    # Get initial balances
    try:
        from src import create_app
        from src.db import get_performers, get_audience_members
        
        app = create_app()
        with app.app_context():
            initial_performers = get_performers()
            initial_audience = get_audience_members()
            
            print(f"Initial state - Performers: {len(initial_performers)}, Audience: {len(initial_audience)}")
            
            if initial_performers:
                print(f"Performer balance before: {initial_performers[0]['coin_balance']}")
            if initial_audience:
                print(f"Audience balance before: {initial_audience[0]['coin_balance']}")
        
        # Wait for automatic redistribution (should happen every 60 seconds)
        print("Waiting 65 seconds for automatic redistribution...")
        time.sleep(65)
        
        # Check balances again
        with app.app_context():
            final_performers = get_performers()
            final_audience = get_audience_members()
            
            if final_performers and initial_performers:
                balance_change = final_performers[0]['coin_balance'] - initial_performers[0]['coin_balance']
                print(f"Performer balance after: {final_performers[0]['coin_balance']} (change: {balance_change})")
                
                if balance_change <= -5:
                    print("✅ Automatic redistribution working - performer lost coins")
                    return True
                else:
                    print(f"❌ Expected performer to lose at least 5 coins, but change was {balance_change}")
                    return False
            else:
                print("❌ Could not verify automatic redistribution")
                return False
                
    except Exception as e:
        print(f"❌ Automatic redistribution test error: {e}")
        return False

def main():
    print("🧪 STRAW COIN PERFORMER SYSTEM TESTS")
    print("=" * 50)
    print("Make sure Flask server is running: flask --app src run --debug")
    
    input("\nPress Enter when server is ready...")
    
    tests = [
        ("Clear Database", clear_all_data),
        ("Create Test Users", create_test_users),
        ("Check Initial Balances", check_initial_balances),
        ("Test Manual Redistribution", test_manual_redistribution),
        ("Check Post-Redistribution Balances", check_balances_after_redistribution),
        ("Test API Endpoints", test_api_endpoints),
        ("Test Status Changes", test_performer_status_change),
        ("Test Automatic Redistribution", test_automatic_redistribution),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            results.append(result)
            
            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
                
        except KeyboardInterrupt:
            print(f"⏹️ Test interrupted by user")
            break
        except Exception as e:
            print(f"❌ {test_name} CRASHED: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    print(f"\n{'='*50}")
    print(f"📊 FINAL RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🚀 ALL TESTS PASSED - Performer system working!")
        return True
    else:
        print("⚠️ SOME TESTS FAILED - Check implementation")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)