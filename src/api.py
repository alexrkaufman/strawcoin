from datetime import datetime

from flask import Blueprint, current_app, jsonify, request

from .auth import require_auth, require_quant
from .db import (
    create_user,
    get_all_users,
    get_audience_members,
    get_performers,
    get_transaction_history,
    get_user_balance,
    get_user_performer_status,
    performer_redistribution,
    set_user_performer_status,
    transfer_coins,
)

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/users", methods=["POST"])
def register_user():
    data = request.get_json()

    if not data or "username" not in data:
        return jsonify(
            {"error": "Username required", "status": "validation_error"}
        ), 400

    username = data["username"].strip().upper()

    if not username or len(username) < 3:
        return jsonify(
            {
                "error": "Username must be at least 3 characters",
                "status": "validation_error",
            }
        ), 400

    # Check if performer flag is provided
    is_performer = data.get("is_performer", False)

    user_id = create_user(username, is_performer)

    if user_id is None:
        return jsonify(
            {"error": "Username already exists", "status": "duplicate_stakeholder"}
        ), 409

    user_type = "performer" if is_performer else "audience member"
    return jsonify(
        {
            "message": f"User {username} successfully created as {user_type}",
            "user_id": user_id,
            "starting_balance": 10000,
            "is_performer": is_performer,
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

    # Convert usernames to uppercase for consistency
    sender = sender.upper()
    recipient = recipient.upper()

    # Check for self-transfers
    if sender == recipient:
        # Transfer the attempted amount to CHANCELLOR as penalty
        quant_username = current_app.config.get("QUANT_USERNAME", "CHANCELLOR")

        # Execute the insider trading penalty transfer
        penalty_result = transfer_coins(sender, quant_username, amount)

        return jsonify(
            {
                "redirect": "/self-dealing-warning",
                "status": "self_dealing_violation",
            }
        ), 302

    # Check if trying to pay CHANCELLOR directly (violates independence)
    quant_username = current_app.config.get("QUANT_USERNAME", "CHANCELLOR")
    if recipient == quant_username.upper():
        return jsonify(
            {
                "redirect": "/market-manipulation-warning",
                "status": "market_manipulation_warning",
            }
        ), 302

    result = transfer_coins(sender, recipient, amount)

    status_codes = {
        "success": 200,
        "insider_trading_violation": 302,
        "quant_independence_violation": 302,
        "insufficient_funds": 400,
        "invalid_amount": 400,
        "user_not_found": 404,
        "transaction_failed": 500,
    }
    messages = {
        "success": f"Transferred {amount} coins from {sender} to {recipient}",
        "insufficient_funds": f"{sender} has insufficient funds",
        "user_not_found": "User not found",
        "invalid_amount": "Amount must be positive",
        "transaction_failed": "Transaction failed",
        "chancellor_self_transfer_forbidden": "The CHANCELLOR cannot transfer coins to themselves",
        "insider_trading_violation": "Insider trading violation - coins confiscated",
        "quant_independence_violation": "CHANCELLOR cannot accept direct payments",
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
    import hashlib
    import random
    from datetime import datetime, timedelta

    from .db import get_balance_history, get_current_leaderboard_with_snapshots

    # Get hours parameter, default to 0.5 hours (30 minutes)
    hours = float(request.args.get("hours", 0.5))
    hours = min(hours, 6.0)  # Limit to 6 hours max

    # Get historical data
    history = get_balance_history(hours)

    # Get current leaderboard to ensure we have recent snapshots
    current_leaders = get_current_leaderboard_with_snapshots()

    # Process data for chart format with market-like fluctuations
    chart_data = {}
    time_points = set()

    # Process historical snapshots and add trading-style data points
    for snapshot in history:
        username = snapshot["username"]
        timestamp = snapshot["timestamp"]
        balance = snapshot["balance"]

        # Convert datetime to ISO string for Chart.js
        timestamp_str = (
            timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp)
        )

        if username not in chart_data:
            chart_data[username] = {}

        chart_data[username][timestamp_str] = balance
        time_points.add(timestamp_str)

    # Generate additional market-like data points for trading simulation
    time_points = sorted(list(time_points))
    if time_points:
        start_time = datetime.fromisoformat(
            time_points[0].replace("Z", "+00:00")
            if "Z" in time_points[0]
            else time_points[0]
        )
        end_time = datetime.fromisoformat(
            time_points[-1].replace("Z", "+00:00")
            if "Z" in time_points[-1]
            else time_points[-1]
        )

        # Add intermediate points every 30 seconds for smooth trading curves
        current_time = start_time
        interval = timedelta(seconds=30)

        enhanced_chart_data = {}
        for username in chart_data.keys():
            enhanced_chart_data[username] = {}

            # Get user's actual data points
            user_timestamps = sorted(chart_data[username].keys())

            # Create seed for consistent randomness per user
            user_seed = int(hashlib.md5(username.encode()).hexdigest()[:8], 16)
            user_random = random.Random(user_seed)

            current_time = start_time
            while current_time <= end_time:
                timestamp_str = current_time.isoformat()

                # Find the closest actual balance
                base_balance = 10000  # Default
                for ts in user_timestamps:
                    if ts <= timestamp_str:
                        base_balance = chart_data[username][ts]

                # Add market-like fluctuations (±2-5% volatility)
                volatility = user_random.uniform(0.02, 0.05)  # 2-5% volatility
                noise_factor = user_random.uniform(-volatility, volatility)

                # Add some trending behavior based on time
                time_factor = (
                    current_time - start_time
                ).total_seconds() / 3600  # hours
                trend = (
                    user_random.uniform(-0.01, 0.01) * time_factor
                )  # slight trend over time

                # Apply fluctuations
                fluctuated_balance = base_balance * (1 + noise_factor + trend)
                fluctuated_balance = max(
                    0, int(fluctuated_balance)
                )  # Ensure non-negative

                enhanced_chart_data[username][timestamp_str] = fluctuated_balance
                current_time += interval

    # Use enhanced data for chart
    chart_data = (
        enhanced_chart_data if "enhanced_chart_data" in locals() else chart_data
    )
    time_points = sorted(
        set().union(*[list(user_data.keys()) for user_data in chart_data.values()])
    )

    # Format for Chart.js with trading platform styling
    datasets = []
    trading_colors = [
        "#00D084",  # Green (bullish)
        "#F23645",  # Red (bearish)
        "#FFA726",  # Orange
        "#42A5F5",  # Blue
        "#AB47BC",  # Purple
        "#26C6DA",  # Cyan
        "#66BB6A",  # Light Green
        "#EF5350",  # Light Red
        "#FFCA28",  # Amber
        "#5C6BC0",  # Indigo
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
                    "borderColor": trading_colors[i % len(trading_colors)],
                    "backgroundColor": trading_colors[i % len(trading_colors)] + "10",
                    "tension": 0.1,  # Less smooth for more realistic trading curves
                    "fill": False,
                    "borderWidth": 2,
                    "pointRadius": 0,  # Hide points for cleaner trading look
                    "pointHoverRadius": 4,
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


@bp.route("/performers", methods=["GET"])
@require_auth
def get_performers_list():
    """Get all performers."""
    performers = get_performers()
    audience = get_audience_members()

    return jsonify(
        {
            "performers": performers,
            "audience_count": len(audience),
            "performer_count": len(performers),
            "status": "success",
        }
    )


@bp.route("/market-status", methods=["GET"])
@require_auth
def get_market_status_api():
    """Get current market status."""
    from .db import get_market_status

    market_status = get_market_status()

    return jsonify(
        {
            "status": "success",
            "market_status": market_status,
            "timestamp": datetime.now().isoformat(),
        }
    )


@bp.route("/performers/redistribute", methods=["POST"])
@require_auth
def trigger_performer_redistribution():
    """Manually trigger performer coin redistribution."""
    result = performer_redistribution()

    if result["success"]:
        return jsonify(
            {
                "message": f"Redistributed {result['total_redistributed']} coins from {result['performer_count']} performers to {result['audience_count']} audience members",
                "details": result,
                "status": "redistribution_successful",
            }
        ), 200
    else:
        return jsonify(
            {
                "error": result["message"],
                "status": "redistribution_failed",
            }
        ), 500


@bp.route("/users/<username>/performer-status", methods=["GET"])
@require_auth
def get_performer_status(username):
    """Get a user's performer status."""
    status = get_user_performer_status(username)

    if status is None:
        return jsonify({"error": "User not found", "status": "user_not_found"}), 404

    return jsonify(
        {
            "username": username,
            "is_performer": status,
            "user_type": "performer" if status else "audience_member",
            "status": "success",
        }
    )


@bp.route("/users/<username>/performer-status", methods=["PUT"])
@require_auth
def set_performer_status(username):
    """Set a user's performer status."""
    data = request.get_json()

    if not data or "is_performer" not in data:
        return jsonify(
            {"error": "is_performer field required", "status": "validation_error"}
        ), 400

    is_performer = bool(data["is_performer"])
    success = set_user_performer_status(username, is_performer)

    if not success:
        return jsonify(
            {"error": "Failed to update performer status", "status": "update_failed"}
        ), 500

    user_type = "performer" if is_performer else "audience_member"
    return jsonify(
        {
            "message": f"User {username} is now a {user_type}",
            "username": username,
            "is_performer": is_performer,
            "status": "status_updated",
        }
    ), 200


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


# THE QUANT - Market Manipulation API Endpoints
@bp.route("/quant/users", methods=["GET"])
@require_quant
def quant_get_users():
    """Get all users with their performer status for The Quant."""
    from .db import get_db

    db = get_db()
    users = db.execute(
        "SELECT username, coin_balance, is_performer, created_at FROM users ORDER BY username"
    ).fetchall()

    return jsonify(
        {
            "users": [dict(user) for user in users],
            "total_users": len(users),
            "quant": "CHANCELLOR",
            "status": "success",
        }
    )


@bp.route("/quant/users/<username>/performer-status", methods=["PUT"])
@require_quant
def quant_set_performer_status(username):
    """Set a user's performer status - The Quant's market manipulation."""
    data = request.get_json()

    if not data or "is_performer" not in data:
        return jsonify(
            {"error": "is_performer field required", "status": "validation_error"}
        ), 400

    is_performer = bool(data["is_performer"])
    reason = data.get("reason", "Market manipulation by The Quant")

    success = set_user_performer_status(username, is_performer)

    if not success:
        return jsonify(
            {"error": "Failed to update performer status", "status": "update_failed"}
        ), 500

    # Log the manipulation
    from .db import get_db

    db = get_db()
    try:
        db.execute(
            "INSERT INTO transactions (sender_id, recipient_id, amount, timestamp) VALUES (?, ?, ?, datetime('now')) ",
            (0, 0, 0),  # Special transaction for logging
        )
    except:
        pass  # Don't fail if logging fails

    user_type = "performer" if is_performer else "audience_member"
    return jsonify(
        {
            "message": f"The CHANCELLOR manipulated {username} to {user_type} status",
            "username": username,
            "is_performer": is_performer,
            "reason": reason,
            "manipulated_by": "CHANCELLOR",
            "status": "manipulation_successful",
        }
    ), 200


@bp.route("/quant/force-redistribution", methods=["POST"])
@require_quant
def quant_force_redistribution():
    """Force immediate coin redistribution from performers to audience - The Quant's market manipulation."""
    data = request.get_json() or {}
    multiplier = data.get("multiplier", 1)  # Default 1x redistribution
    reason = data.get("reason", "Forced redistribution by The Quant")

    # Validate multiplier
    if not isinstance(multiplier, (int, float)) or multiplier <= 0 or multiplier > 10:
        return jsonify(
            {
                "error": "Multiplier must be between 0.1 and 10",
                "status": "validation_error",
            }
        ), 400

    # Perform multiple redistributions based on multiplier
    total_redistributed = 0
    redistributions = []

    for i in range(int(multiplier)):
        result = performer_redistribution()
        if result["success"]:
            redistributions.append(result)
            total_redistributed += result["total_redistributed"]
        else:
            break

    # Handle fractional multiplier
    if multiplier % 1 != 0:
        fractional_part = multiplier % 1
        # Custom fractional redistribution logic here if needed
        pass

    if redistributions:
        return jsonify(
            {
                "message": f"The Quant forced {len(redistributions)} redistribution cycles",
                "total_redistributed": total_redistributed,
                "multiplier": multiplier,
                "reason": reason,
                "redistributions": redistributions,
                "manipulated_by": "CHANCELLOR",
                "status": "forced_redistribution_successful",
            }
        ), 200
    else:
        return jsonify(
            {
                "error": "No redistributions could be performed",
                "status": "redistribution_failed",
            }
        ), 500


@bp.route("/quant/force-transfer", methods=["POST"])
@require_quant
def quant_force_transfer():
    """Force transfers between users - The Quant's market manipulation power."""
    data = request.get_json()

    if (
        not data
        or "sender" not in data
        or "recipient" not in data
        or "amount" not in data
    ):
        return jsonify(
            {
                "error": "sender, recipient, and amount fields required",
                "status": "validation_error",
            }
        ), 400

    sender = data["sender"]
    recipient = data["recipient"]
    amount = data["amount"]
    reason = data.get("reason", "Forced transfer by The Quant")

    # Prevent The Quant from being involved in transfers they force
    from flask import session

    current_username = session.get("username")
    quant_username = current_app.config.get("QUANT_USERNAME", "CHANCELLOR")

    if sender == quant_username or recipient == quant_username:
        return jsonify(
            {
                "error": "The Quant cannot force transfers involving themselves",
                "status": "quant_transfer_forbidden",
            }
        ), 403

    if sender == recipient:
        return jsonify(
            {
                "error": "Cannot force transfer from user to themselves",
                "status": "invalid_transfer",
            }
        ), 400

    try:
        amount = int(amount)
    except (ValueError, TypeError):
        return jsonify(
            {"error": "Amount must be an integer", "status": "validation_error"}
        ), 400

    if amount <= 0:
        return jsonify(
            {"error": "Amount must be positive", "status": "invalid_amount"}
        ), 400

    # Use the existing transfer_coins function but bypass normal restrictions
    from .db import get_db

    db = get_db()

    # Get sender and recipient info
    sender_user = db.execute(
        "SELECT id, coin_balance FROM users WHERE username = ?", (sender,)
    ).fetchone()

    recipient_user = db.execute(
        "SELECT id FROM users WHERE username = ?", (recipient,)
    ).fetchone()

    if not sender_user:
        return jsonify(
            {"error": f"Sender '{sender}' not found", "status": "sender_not_found"}
        ), 404

    if not recipient_user:
        return jsonify(
            {
                "error": f"Recipient '{recipient}' not found",
                "status": "recipient_not_found",
            }
        ), 404

    if sender_user["coin_balance"] < amount:
        return jsonify(
            {
                "error": f"Sender '{sender}' has insufficient funds ({sender_user['coin_balance']} coins)",
                "status": "insufficient_funds",
            }
        ), 400

    try:
        # Perform the forced transfer
        db.execute(
            "UPDATE users SET coin_balance = coin_balance - ? WHERE username = ?",
            (amount, sender),
        )
        db.execute(
            "UPDATE users SET coin_balance = coin_balance + ? WHERE username = ?",
            (amount, recipient),
        )

        # Create transaction record with special note
        db.execute(
            "INSERT INTO transactions (sender_id, recipient_id, amount) VALUES (?, ?, ?)",
            (sender_user["id"], recipient_user["id"], amount),
        )

        db.commit()

        # Create balance snapshots
        from .db import create_balance_snapshot

        sender_new_balance = sender_user["coin_balance"] - amount
        recipient_new_balance = db.execute(
            "SELECT coin_balance FROM users WHERE username = ?", (recipient,)
        ).fetchone()["coin_balance"]

        create_balance_snapshot(sender_user["id"], sender_new_balance)
        create_balance_snapshot(recipient_user["id"], recipient_new_balance)

        return jsonify(
            {
                "message": f"The CHANCELLOR forced transfer of {amount} coins from {sender} to {recipient}",
                "sender": sender,
                "recipient": recipient,
                "amount": amount,
                "sender_new_balance": sender_new_balance,
                "recipient_new_balance": recipient_new_balance,
                "reason": reason,
                "manipulated_by": "CHANCELLOR",
                "status": "forced_transfer_successful",
            }
        ), 200

    except Exception as e:
        db.rollback()
        return jsonify(
            {"error": f"Forced transfer failed: {str(e)}", "status": "transfer_failed"}
        ), 500


@bp.route("/quant/performers-to-audience", methods=["POST"])
@require_quant
def quant_performers_to_audience():
    """Force all performers to send coins to all audience members - The CHANCELLOR's mass redistribution."""
    data = request.get_json() or {}
    amount_per_transfer = data.get("amount", 100)
    reason = data.get("reason", "Mass performer-to-audience transfer by The CHANCELLOR")

    try:
        amount_per_transfer = int(amount_per_transfer)
    except (ValueError, TypeError):
        return jsonify(
            {"error": "Amount must be an integer", "status": "validation_error"}
        ), 400

    if amount_per_transfer <= 0:
        return jsonify(
            {"error": "Amount must be positive", "status": "invalid_amount"}
        ), 400

    from .db import get_db

    db = get_db()

    # Get performers and audience (excluding The CHANCELLOR)
    quant_username = current_app.config.get("QUANT_USERNAME", "CHANCELLOR")

    performers = db.execute(
        "SELECT id, username, coin_balance FROM users WHERE is_performer = 1 AND username != ?",
        (quant_username,),
    ).fetchall()

    audience = db.execute(
        "SELECT id, username, coin_balance FROM users WHERE is_performer = 0 AND username != ?",
        (quant_username,),
    ).fetchall()

    if not performers or not audience:
        return jsonify(
            {
                "error": "Need at least one performer and one audience member",
                "status": "insufficient_users",
            }
        ), 400

    transfers = []
    failed_transfers = []

    try:
        for performer in performers:
            total_needed = amount_per_transfer * len(audience)
            if performer["coin_balance"] < total_needed:
                failed_transfers.append(
                    {
                        "performer": performer["username"],
                        "reason": f"Insufficient funds ({performer['coin_balance']} < {total_needed})",
                    }
                )
                continue

            # Transfer to each audience member
            for audience_member in audience:
                db.execute(
                    "UPDATE users SET coin_balance = coin_balance - ? WHERE id = ?",
                    (amount_per_transfer, performer["id"]),
                )
                db.execute(
                    "UPDATE users SET coin_balance = coin_balance + ? WHERE id = ?",
                    (amount_per_transfer, audience_member["id"]),
                )
                db.execute(
                    "INSERT INTO transactions (sender_id, recipient_id, amount) VALUES (?, ?, ?)",
                    (performer["id"], audience_member["id"], amount_per_transfer),
                )

                transfers.append(
                    {
                        "sender": performer["username"],
                        "recipient": audience_member["username"],
                        "amount": amount_per_transfer,
                    }
                )

        db.commit()

        # Create balance snapshots
        from .db import create_balance_snapshots_for_all_users

        create_balance_snapshots_for_all_users()

        return jsonify(
            {
                "message": f"The CHANCELLOR forced {len(transfers)} transfers from performers to audience",
                "transfers": transfers,
                "failed_transfers": failed_transfers,
                "amount_per_transfer": amount_per_transfer,
                "reason": reason,
                "manipulated_by": "CHANCELLOR",
                "status": "mass_transfer_successful",
            }
        ), 200

    except Exception as e:
        db.rollback()
        return jsonify(
            {
                "error": f"Mass transfer failed: {str(e)}",
                "status": "mass_transfer_failed",
            }
        ), 500


@bp.route("/quant/audience-to-performers", methods=["POST"])
@require_quant
def quant_audience_to_performers():
    """Force all audience members to send coins to all performers - The CHANCELLOR's reverse redistribution."""
    data = request.get_json() or {}
    amount_per_transfer = data.get("amount", 100)
    reason = data.get("reason", "Mass audience-to-performer transfer by The CHANCELLOR")

    try:
        amount_per_transfer = int(amount_per_transfer)
    except (ValueError, TypeError):
        return jsonify(
            {"error": "Amount must be an integer", "status": "validation_error"}
        ), 400

    if amount_per_transfer <= 0:
        return jsonify(
            {"error": "Amount must be positive", "status": "invalid_amount"}
        ), 400

    from .db import get_db

    db = get_db()

    # Get performers and audience (excluding The CHANCELLOR)
    quant_username = current_app.config.get("QUANT_USERNAME", "CHANCELLOR")

    performers = db.execute(
        "SELECT id, username, coin_balance FROM users WHERE is_performer = 1 AND username != ?",
        (quant_username,),
    ).fetchall()

    audience = db.execute(
        "SELECT id, username, coin_balance FROM users WHERE is_performer = 0 AND username != ?",
        (quant_username,),
    ).fetchall()

    if not performers or not audience:
        return jsonify(
            {
                "error": "Need at least one performer and one audience member",
                "status": "insufficient_users",
            }
        ), 400

    transfers = []
    failed_transfers = []

    try:
        for audience_member in audience:
            total_needed = amount_per_transfer * len(performers)
            if audience_member["coin_balance"] < total_needed:
                failed_transfers.append(
                    {
                        "audience_member": audience_member["username"],
                        "reason": f"Insufficient funds ({audience_member['coin_balance']} < {total_needed})",
                    }
                )
                continue

            # Transfer to each performer
            for performer in performers:
                db.execute(
                    "UPDATE users SET coin_balance = coin_balance - ? WHERE id = ?",
                    (amount_per_transfer, audience_member["id"]),
                )
                db.execute(
                    "UPDATE users SET coin_balance = coin_balance + ? WHERE id = ?",
                    (amount_per_transfer, performer["id"]),
                )
                db.execute(
                    "INSERT INTO transactions (sender_id, recipient_id, amount) VALUES (?, ?, ?)",
                    (audience_member["id"], performer["id"], amount_per_transfer),
                )

                transfers.append(
                    {
                        "sender": audience_member["username"],
                        "recipient": performer["username"],
                        "amount": amount_per_transfer,
                    }
                )

        db.commit()

        # Create balance snapshots
        from .db import create_balance_snapshots_for_all_users

        create_balance_snapshots_for_all_users()

        return jsonify(
            {
                "message": f"The CHANCELLOR forced {len(transfers)} transfers from audience to performers",
                "transfers": transfers,
                "failed_transfers": failed_transfers,
                "amount_per_transfer": amount_per_transfer,
                "reason": reason,
                "manipulated_by": "CHANCELLOR",
                "status": "reverse_mass_transfer_successful",
            }
        ), 200

    except Exception as e:
        db.rollback()
        return jsonify(
            {
                "error": f"Reverse mass transfer failed: {str(e)}",
                "status": "reverse_mass_transfer_failed",
            }
        ), 500


@bp.route("/quant/group-transfer", methods=["POST"])
@require_quant
def quant_group_transfer():
    """Handle mixed group transfers - group to individual or individual to group."""
    data = request.get_json()

    if (
        not data
        or "sender" not in data
        or "recipient" not in data
        or "amount" not in data
    ):
        return jsonify(
            {
                "error": "sender, recipient, and amount fields required",
                "status": "validation_error",
            }
        ), 400

    sender = data["sender"]
    recipient = data["recipient"]
    amount = data["amount"]
    reason = data.get("reason", "Group transfer by The Quant")

    try:
        amount = int(amount)
    except (ValueError, TypeError):
        return jsonify(
            {"error": "Amount must be an integer", "status": "validation_error"}
        ), 400

    if amount <= 0:
        return jsonify(
            {"error": "Amount must be positive", "status": "invalid_amount"}
        ), 400

    # Prevent The CHANCELLOR from being involved
    quant_username = current_app.config.get("QUANT_USERNAME", "CHANCELLOR")
    if sender == quant_username or recipient == quant_username or sender == recipient:
        return jsonify(
            {"error": "Invalid transfer configuration", "status": "invalid_transfer"}
        ), 400

    from .db import get_db

    db = get_db()

    transfers = []
    failed_transfers = []

    try:
        # Determine transfer type and get appropriate users
        if sender == "All Performers":
            # All performers to specific recipient
            senders = db.execute(
                "SELECT id, username, coin_balance FROM users WHERE is_performer = 1 AND username != ?",
                (quant_username,),
            ).fetchall()

            recipient_user = db.execute(
                "SELECT id, username FROM users WHERE username = ?", (recipient,)
            ).fetchone()

            if not recipient_user:
                return jsonify(
                    {
                        "error": f"Recipient '{recipient}' not found",
                        "status": "recipient_not_found",
                    }
                ), 404

            recipients = [recipient_user]

        elif sender == "All Audience":
            # All audience to specific recipient
            senders = db.execute(
                "SELECT id, username, coin_balance FROM users WHERE is_performer = 0 AND username != ?",
                (quant_username,),
            ).fetchall()

            recipient_user = db.execute(
                "SELECT id, username FROM users WHERE username = ?", (recipient,)
            ).fetchone()

            if not recipient_user:
                return jsonify(
                    {
                        "error": f"Recipient '{recipient}' not found",
                        "status": "recipient_not_found",
                    }
                ), 404

            recipients = [recipient_user]

        elif recipient == "All Performers":
            # Specific sender to all performers
            sender_user = db.execute(
                "SELECT id, username, coin_balance FROM users WHERE username = ?",
                (sender,),
            ).fetchone()

            if not sender_user:
                return jsonify(
                    {
                        "error": f"Sender '{sender}' not found",
                        "status": "sender_not_found",
                    }
                ), 404

            senders = [sender_user]
            recipients = db.execute(
                "SELECT id, username FROM users WHERE is_performer = 1 AND username != ?",
                (quant_username,),
            ).fetchall()

        elif recipient == "All Audience":
            # Specific sender to all audience
            sender_user = db.execute(
                "SELECT id, username, coin_balance FROM users WHERE username = ?",
                (sender,),
            ).fetchone()

            if not sender_user:
                return jsonify(
                    {
                        "error": f"Sender '{sender}' not found",
                        "status": "sender_not_found",
                    }
                ), 404

            senders = [sender_user]
            recipients = db.execute(
                "SELECT id, username FROM users WHERE is_performer = 0 AND username != ?",
                (quant_username,),
            ).fetchall()

        else:
            return jsonify(
                {
                    "error": "Invalid group transfer configuration",
                    "status": "invalid_configuration",
                }
            ), 400

        if not senders or not recipients:
            return jsonify(
                {
                    "error": "No valid senders or recipients found",
                    "status": "insufficient_users",
                }
            ), 400

        # Perform transfers
        for sender_user in senders:
            total_needed = amount * len(recipients)
            if sender_user["coin_balance"] < total_needed:
                failed_transfers.append(
                    {
                        "sender": sender_user["username"],
                        "reason": f"Insufficient funds ({sender_user['coin_balance']} < {total_needed})",
                    }
                )
                continue

            # Transfer to each recipient
            for recipient_user in recipients:
                db.execute(
                    "UPDATE users SET coin_balance = coin_balance - ? WHERE id = ?",
                    (amount, sender_user["id"]),
                )
                db.execute(
                    "UPDATE users SET coin_balance = coin_balance + ? WHERE id = ?",
                    (amount, recipient_user["id"]),
                )
                db.execute(
                    "INSERT INTO transactions (sender_id, recipient_id, amount) VALUES (?, ?, ?)",
                    (sender_user["id"], recipient_user["id"], amount),
                )

                transfers.append(
                    {
                        "sender": sender_user["username"],
                        "recipient": recipient_user["username"],
                        "amount": amount,
                    }
                )

        db.commit()

        # Create balance snapshots
        from .db import create_balance_snapshots_for_all_users

        create_balance_snapshots_for_all_users()

        return jsonify(
            {
                "message": f"The CHANCELLOR executed {len(transfers)} group transfers",
                "transfers": transfers,
                "failed_transfers": failed_transfers,
                "sender_type": sender,
                "recipient_type": recipient,
                "amount_per_transfer": amount,
                "reason": reason,
                "manipulated_by": "CHANCELLOR",
                "status": "group_transfer_successful",
            }
        ), 200

    except Exception as e:
        db.rollback()
        return jsonify(
            {
                "error": f"Group transfer failed: {str(e)}",
                "status": "group_transfer_failed",
            }
        ), 500


@bp.route("/quant/market-stats", methods=["GET"])
@require_quant
def quant_market_stats():
    """Get comprehensive market statistics for The Quant."""
    from .db import get_db

    db = get_db()

    # Get comprehensive stats
    stats = {}

    # Basic stats
    stats["total_coins"] = db.execute(
        "SELECT SUM(coin_balance) as total FROM users"
    ).fetchone()["total"]
    stats["total_users"] = db.execute("SELECT COUNT(*) as count FROM users").fetchone()[
        "count"
    ]
    stats["performers"] = db.execute(
        "SELECT COUNT(*) as count FROM users WHERE is_performer = 1"
    ).fetchone()["count"]
    stats["audience"] = db.execute(
        "SELECT COUNT(*) as count FROM users WHERE is_performer = 0"
    ).fetchone()["count"]

    # Transaction stats
    stats["total_transactions"] = db.execute(
        "SELECT COUNT(*) as count FROM transactions"
    ).fetchone()["count"]
    stats["total_volume"] = (
        db.execute("SELECT SUM(amount) as volume FROM transactions").fetchone()[
            "volume"
        ]
        or 0
    )

    # Top holders
    top_users = db.execute(
        "SELECT username, coin_balance, is_performer FROM users ORDER BY coin_balance DESC LIMIT 10"
    ).fetchall()
    stats["top_users"] = [dict(user) for user in top_users]

    # Recent transactions
    recent_txs = db.execute(
        """SELECT t.amount, t.timestamp, s.username as sender, r.username as recipient
           FROM transactions t
           LEFT JOIN users s ON t.sender_id = s.id
           LEFT JOIN users r ON t.recipient_id = r.id
           ORDER BY t.timestamp DESC LIMIT 20"""
    ).fetchall()
    stats["recent_transactions"] = [dict(tx) for tx in recent_txs]

    return jsonify(
        {
            "market_stats": stats,
            "quant": "CHANCELLOR",
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "status": "success",
        }
    )
