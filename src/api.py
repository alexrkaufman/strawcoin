from flask import Blueprint, request, jsonify
from .db import (
    create_user,
    get_user_balance,
    transfer_coins,
    get_all_users,
    get_transaction_history,
)
from .auth import require_auth

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/users", methods=["POST"])
def register_user():
    data = request.get_json()

    if not data or "username" not in data:
        return jsonify(
            {"error": "Username required", "status": "validation_error"}
        ), 400

    username = data["username"].strip()

    if not username or len(username) < 3:
        return jsonify(
            {
                "error": "Username must be at least 3 characters",
                "status": "validation_error",
            }
        ), 400

    user_id = create_user(username)

    if user_id is None:
        return jsonify(
            {"error": "Username already exists", "status": "duplicate_stakeholder"}
        ), 409

    return jsonify(
        {
            "message": f"User {username} successfully created",
            "user_id": user_id,
            "starting_balance": 10000,
            "status": "moon_mission_initiated",
        }
    ), 201


@bp.route("/users/<username>/balance", methods=["GET"])
@require_auth
def get_balance(username):
    balance = get_user_balance(username)

    if balance is None:
        return jsonify({"error": "User not found", "status": "user_not_found"}), 404

    return jsonify({"username": username, "balance": balance, "status": "success"})


@bp.route("/transfer", methods=["POST"])
@require_auth
def execute_transfer():
    data = request.get_json()

    required_fields = ["sender", "recipient", "amount"]
    if not data or not all(field in data for field in required_fields):
        return jsonify(
            {
                "error": "Transfer requires sender, recipient, and amount",
                "status": "invalid_format",
            }
        ), 400

    sender = data["sender"].strip()
    recipient = data["recipient"].strip()

    try:
        amount = int(data["amount"])
    except (ValueError, TypeError):
        return jsonify(
            {"error": "Amount must be integer", "status": "invalid_amount"}
        ), 400

    if sender == recipient:
        return jsonify(
            {"error": "Self-transfers not allowed", "status": "invalid_transfer"}
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
        "success": f"Transferred {amount} coins from {sender} to {recipient}",
        "insufficient_funds": f"{sender} has insufficient funds",
        "user_not_found": "User not found",
        "invalid_amount": "Amount must be positive",
        "transaction_failed": "Transaction failed",
    }

    return jsonify(
        {
            "message": messages.get(result, "Unknown error"),
            "status": result,
            "details": {"sender": sender, "recipient": recipient, "amount": amount}
            if result == "success"
            else None,
        }
    ), status_codes.get(result, 500)


@bp.route("/leaderboard", methods=["GET"])
@require_auth
def get_leaderboard():
    users = get_all_users()
    return jsonify(
        {"leaderboard": users, "total_users": len(users), "status": "success"}
    )


@bp.route("/transactions", methods=["GET"])
@require_auth
def get_transactions():
    username = request.args.get("username")
    limit = min(int(request.args.get("limit", 50)), 100)

    transactions = get_transaction_history(username, limit)

    return jsonify(
        {
            "transactions": transactions,
            "filter": username or "all_users",
            "limit": limit,
            "status": "success",
        }
    )


@bp.route("/market-stats", methods=["GET"])
@require_auth
def get_market_stats():
    from .db import get_db

    db = get_db()

    total_coins = db.execute("SELECT SUM(coin_balance) as total FROM users").fetchone()
    user_count = db.execute("SELECT COUNT(*) as count FROM users").fetchone()
    transaction_volume = db.execute(
        "SELECT COUNT(*) as count, SUM(amount) as volume FROM transactions"
    ).fetchone()
    top_performer = db.execute(
        "SELECT username, coin_balance FROM users ORDER BY coin_balance DESC LIMIT 1"
    ).fetchone()

    return jsonify(
        {
            "market_cap": total_coins["total"] or 0,
            "total_users": user_count["count"],
            "transaction_count": transaction_volume["count"] or 0,
            "total_volume": transaction_volume["volume"] or 0,
            "top_performer": {
                "username": top_performer["username"],
                "balance": top_performer["coin_balance"],
            }
            if top_performer
            else None,
            "status": "success",
        }
    )


@bp.route("/leaderboard-history", methods=["GET"])
@require_auth
def get_leaderboard_history():
    from .db import get_balance_history, get_current_leaderboard_with_snapshots

    # Get hours parameter, default to 0.5 hours (30 minutes)
    hours = float(request.args.get("hours", 0.5))
    hours = min(hours, 6.0)  # Limit to 6 hours max

    # Get historical data
    history = get_balance_history(hours)

    # Get current leaderboard to ensure we have recent snapshots
    current_leaders = get_current_leaderboard_with_snapshots()

    # Process data for chart format
    chart_data = {}
    time_points = set()

    # Process historical snapshots
    for snapshot in history:
        username = snapshot["username"]
        timestamp = snapshot["timestamp"]
        balance = snapshot["balance"]

        if username not in chart_data:
            chart_data[username] = {}

        chart_data[username][timestamp] = balance
        time_points.add(timestamp)

    # Sort time points
    time_points = sorted(list(time_points))

    # Format for Chart.js
    datasets = []
    colors = [
        "#FF6384",
        "#36A2EB",
        "#FFCE56",
        "#4BC0C0",
        "#9966FF",
        "#FF9F40",
        "#FF6384",
        "#C9CBCF",
        "#4BC0C0",
        "#FF6384",
    ]

    for i, username in enumerate(sorted(chart_data.keys())):
        user_data = []
        for timestamp in time_points:
            if timestamp in chart_data[username]:
                user_data.append({"x": timestamp, "y": chart_data[username][timestamp]})

        if user_data:  # Only include users with data
            datasets.append(
                {
                    "label": username,
                    "data": user_data,
                    "borderColor": colors[i % len(colors)],
                    "backgroundColor": colors[i % len(colors)] + "20",
                    "tension": 0.4,
                    "fill": False,
                }
            )

    return jsonify(
        {
            "datasets": datasets,
            "current_leaders": current_leaders[:10],  # Top 10
            "time_range_hours": hours,
            "total_data_points": len(time_points),
            "status": "success",
        }
    )


@bp.route("/leaderboard-snapshot", methods=["POST"])
@require_auth
def create_leaderboard_snapshot():
    from .db import create_balance_snapshots_for_all_users

    success = create_balance_snapshots_for_all_users()

    if success:
        return jsonify(
            {"message": "Balance snapshots created for all users", "status": "success"}
        ), 200
    else:
        return jsonify(
            {"error": "Failed to create balance snapshots", "status": "error"}
        ), 500


@bp.route("/leaderboard-realtime", methods=["GET"])
@require_auth
def get_realtime_leaderboard():
    from .db import get_current_leaderboard_with_snapshots

    leaders = get_current_leaderboard_with_snapshots()

    return jsonify(
        {
            "leaders": leaders,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "status": "success",
        }
    )
