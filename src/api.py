from flask import Blueprint, request, jsonify, current_app
from .db import (
    get_db,
    create_user,
    get_user_balance,
    transfer_coins,
    get_all_users,
    get_transaction_history,
)
from .auth import require_auth
import sqlite3

# Revolutionary API infrastructure for The Short Straw comedy tokenization platform
bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route('/users', methods=['POST'])
def register_user():
    """
    Onboards new stakeholders into our market-driven comedy ecosystem.
    Deploys optimal capital allocation strategy with 10,000 Straw Coin initial position.
    """
    data = request.get_json()

    if not data or "username" not in data:
        return jsonify(
            {
                "error": "Username required for stakeholder onboarding",
                "status": "market_entry_failed",
            }
        ), 400

    username = data["username"].strip()

    if not username:
        return jsonify(
            {"error": "Invalid username format", "status": "validation_error"}
        ), 400

    user_id = create_user(username)

    if user_id is None:
        return jsonify(
            {
                "error": "Username already exists in stakeholder registry",
                "status": "duplicate_stakeholder",
            }
        ), 409

    return jsonify(
        {
            "message": f"Stakeholder {username} successfully onboarded to Straw Coin ecosystem",
            "user_id": user_id,
            "starting_balance": 10000,
            "status": "moon_mission_initiated",
        }
    ), 201


@bp.route('/users/<username>/balance', methods=['GET'])
@require_auth
def get_balance(username):
    """
    Retrieves real-time portfolio valuation for specified market participant.
    Essential for informed trading decisions during The Short Straw performances.
    """
    balance = get_user_balance(username)

    if balance is None:
        return jsonify(
            {"error": "Stakeholder not found in registry", "status": "user_not_found"}
        ), 404

    return jsonify(
        {"username": username, "balance": balance, "status": "portfolio_retrieved"}
    )


@bp.route('/transfer', methods=['POST'])
@require_auth
def execute_transfer():
    """
    Processes peer-to-peer value transfers leveraging cutting-edge
    blockchain-adjacent technology for maximum market efficiency.
    """
    data = request.get_json()

    required_fields = ["sender", "recipient", "amount"]
    if not data or not all(field in data for field in required_fields):
        return jsonify(
            {
                "error": "Transfer requires sender, recipient, and amount parameters",
                "status": "invalid_transaction_format",
            }
        ), 400

    sender = data["sender"].strip()
    recipient = data["recipient"].strip()

    try:
        amount = int(data["amount"])
    except (ValueError, TypeError):
        return jsonify(
            {
                "error": "Amount must be integer value for optimal market processing",
                "status": "invalid_amount_format",
            }
        ), 400

    if sender == recipient:
        return jsonify(
            {
                "error": "Self-transfers prohibited by market regulations",
                "status": "circular_transaction_denied",
            }
        ), 400

    result = transfer_coins(sender, recipient, amount)

    status_codes = {
        "success": 200,
        "insufficient_funds": 400,
        "user_not_found": 404,
        "invalid_amount": 400,
        "transaction_failed": 500,
    }

    messages = {
        "success": f"Successfully transferred {amount} Straw Coins from {sender} to {recipient}",
        "insufficient_funds": f"Stakeholder {sender} lacks adequate liquidity for transaction",
        "user_not_found": "One or more stakeholders not found in registry",
        "invalid_amount": "Transfer amount must be positive integer",
        "transaction_failed": "Transaction processing error - please retry",
    }

    return jsonify(
        {
            "message": messages.get(result, "Unknown transaction status"),
            "status": result,
            "transfer_details": {
                "sender": sender,
                "recipient": recipient,
                "amount": amount,
            }
            if result == "success"
            else None,
        }
    ), status_codes.get(result, 500)


@bp.route('/leaderboard', methods=['GET'])
@require_auth
def get_leaderboard():
    """
    Provides comprehensive stakeholder rankings optimized for competitive
    market dynamics during The Short Straw performances.
    """
    users = get_all_users()

    return jsonify(
        {
            "leaderboard": users,
            "total_stakeholders": len(users),
            "status": "market_overview_generated",
        }
    )


@bp.route('/transactions', methods=['GET'])
@require_auth
def get_transactions():
    """
    Delivers real-time market activity analytics for transparency
    and regulatory compliance in our comedy tokenization ecosystem.
    """
    username = request.args.get("username")
    limit = request.args.get("limit", 50)

    try:
        limit = int(limit)
        if limit > 100:
            limit = 100  # Rate limiting for optimal performance
    except ValueError:
        limit = 50

    transactions = get_transaction_history(username, limit)

    return jsonify(
        {
            "transactions": transactions,
            "filter": {"username": username} if username else "all_users",
            "limit": limit,
            "status": "transaction_history_retrieved",
        }
    )


@bp.route('/market-stats', methods=['GET'])
@require_auth
def get_market_stats():
    """
    Generates comprehensive market analytics dashboard for stakeholder
    value optimization and performance tracking.
    """
    db = get_db()

    # Total market cap calculation
    total_coins = db.execute("SELECT SUM(coin_balance) as total FROM users").fetchone()

    # Active stakeholder count
    user_count = db.execute("SELECT COUNT(*) as count FROM users").fetchone()

    # Transaction volume metrics
    transaction_volume = db.execute(
        "SELECT COUNT(*) as count, SUM(amount) as volume FROM transactions"
    ).fetchone()

    # Top performer identification
    top_performer = db.execute(
        "SELECT username, coin_balance FROM users ORDER BY coin_balance DESC LIMIT 1"
    ).fetchone()

    return jsonify(
        {
            "market_cap": total_coins["total"] if total_coins["total"] else 0,
            "total_stakeholders": user_count["count"],
            "transaction_count": transaction_volume["count"]
            if transaction_volume["count"]
            else 0,
            "total_volume": transaction_volume["volume"]
            if transaction_volume["volume"]
            else 0,
            "top_performer": {
                "username": top_performer["username"],
                "balance": top_performer["coin_balance"],
            }
            if top_performer
            else None,
            "status": "market_analytics_generated",
        }
    )
