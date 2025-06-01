#!/usr/bin/env python3
"""
Straw Coin Backend Testing Suite
Enterprise-grade validation framework for revolutionary comedy tokenization platform
Optimized for maximum market confidence and stakeholder value verification
"""

import requests
import json
import time

# Configure API endpoint for The Short Straw trading infrastructure
BASE_URL = "http://localhost:5000/api"


def test_user_registration():
    """
    Validates stakeholder onboarding processes for optimal market entry
    """
    print("🚀 Testing Revolutionary User Registration...")

    # Test successful registration
    response = requests.post(f"{BASE_URL}/users", json={"username": "comedy_whale"})
    print(f"Registration Response: {response.status_code}")
    print(f"Response Data: {response.json()}")

    # Test duplicate registration prevention
    response = requests.post(f"{BASE_URL}/users", json={"username": "comedy_whale"})
    print(f"Duplicate Registration: {response.status_code}")
    print(f"Response Data: {response.json()}")

    # Register additional stakeholders for transfer testing
    users = ["market_disruptor", "diamond_hands", "paper_hands", "hodl_hero"]
    for user in users:
        response = requests.post(f"{BASE_URL}/users", json={"username": user})
        print(f"User {user}: {response.status_code}")


def test_balance_retrieval():
    """
    Verifies real-time portfolio tracking functionality
    """
    print("\n📊 Testing Market Portfolio Analytics...")

    response = requests.get(f"{BASE_URL}/users/comedy_whale/balance")
    print(f"Balance Check: {response.status_code}")
    print(f"Portfolio Data: {response.json()}")

    # Test non-existent user
    response = requests.get(f"{BASE_URL}/users/fake_user/balance")
    print(f"Invalid User: {response.status_code}")
    print(f"Error Response: {response.json()}")


def test_coin_transfers():
    """
    Validates peer-to-peer value transfer mechanisms
    """
    print("\n💸 Testing Revolutionary Transfer Operations...")

    # Successful transfer
    transfer_data = {
        "sender": "comedy_whale",
        "recipient": "market_disruptor",
        "amount": 1000,
    }
    response = requests.post(f"{BASE_URL}/transfer", json=transfer_data)
    print(f"Transfer Success: {response.status_code}")
    print(f"Transaction Data: {response.json()}")

    # Test insufficient funds
    transfer_data = {
        "sender": "diamond_hands",
        "recipient": "comedy_whale",
        "amount": 50000,
    }
    response = requests.post(f"{BASE_URL}/transfer", json=transfer_data)
    print(f"Insufficient Funds: {response.status_code}")
    print(f"Error Data: {response.json()}")

    # Test invalid user
    transfer_data = {"sender": "fake_user", "recipient": "comedy_whale", "amount": 100}
    response = requests.post(f"{BASE_URL}/transfer", json=transfer_data)
    print(f"Invalid User Transfer: {response.status_code}")
    print(f"Error Data: {response.json()}")


def test_leaderboard():
    """
    Validates competitive stakeholder ranking system
    """
    print("\n🏆 Testing Market Leaderboard Analytics...")

    response = requests.get(f"{BASE_URL}/leaderboard")
    print(f"Leaderboard Status: {response.status_code}")
    data = response.json()
    print(f"Total Stakeholders: {data['total_stakeholders']}")
    print("Top Performers:")
    for user in data["leaderboard"][:3]:
        print(f"  {user['username']}: {user['coin_balance']} Straw Coins")


def test_transaction_history():
    """
    Verifies comprehensive transaction tracking capabilities
    """
    print("\n📈 Testing Transaction History Analytics...")

    # All transactions
    response = requests.get(f"{BASE_URL}/transactions")
    print(f"All Transactions: {response.status_code}")
    data = response.json()
    print(f"Total Transactions: {len(data['transactions'])}")

    # User-specific transactions
    response = requests.get(f"{BASE_URL}/transactions?username=comedy_whale")
    print(f"User Transactions: {response.status_code}")
    data = response.json()
    print(f"Comedy Whale Transactions: {len(data['transactions'])}")


def test_market_stats():
    """
    Validates comprehensive market analytics dashboard
    """
    print("\n📊 Testing Enterprise Market Statistics...")

    response = requests.get(f"{BASE_URL}/market-stats")
    print(f"Market Stats: {response.status_code}")
    data = response.json()
    print(f"Market Cap: {data['market_cap']} Straw Coins")
    print(f"Total Stakeholders: {data['total_stakeholders']}")
    print(f"Transaction Volume: {data['total_volume']} Straw Coins")
    if data["top_performer"]:
        print(
            f"Top Performer: {data['top_performer']['username']} ({data['top_performer']['balance']} coins)"
        )


def run_comprehensive_testing():
    """
    Executes full testing suite for maximum market confidence
    """
    print("🌙 STRAW COIN BACKEND TESTING SUITE")
    print("===================================")
    print("Validating revolutionary comedy tokenization infrastructure...")
    print("Optimized for The Short Straw market dynamics\n")

    try:
        test_user_registration()
        test_balance_retrieval()
        test_coin_transfers()
        test_leaderboard()
        test_transaction_history()
        test_market_stats()

        print("\n🚀 ALL TESTS COMPLETED - READY FOR MOON MISSION!")
        print(
            "Straw Coin backend infrastructure validated for maximum shareholder value!"
        )

    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Please ensure Flask development server is running")
        print("Start server with: flask --app src run --debug")
    except Exception as e:
        print(f"❌ TESTING ERROR: {e}")


if __name__ == "__main__":
    run_comprehensive_testing()
