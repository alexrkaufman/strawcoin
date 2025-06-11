from functools import wraps
from datetime import datetime, timedelta

from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from .db import create_user, get_user_balance, get_user_performer_status

bp = Blueprint("auth", __name__)


def is_authenticated():
    # Check if user has a username in session
    if "username" not in session:
        return False
    
    # Check if session has a timestamp
    if "session_created" not in session:
        # No timestamp, invalid session
        session.clear()
        return False
    
    try:
        # Check if session is older than 60 seconds
        session_created = datetime.fromisoformat(session["session_created"])
        session_age = datetime.now() - session_created
        
        if session_age > timedelta(seconds=60):
            # Session expired
            session.clear()
            return False
    except (ValueError, TypeError):
        # Invalid session_created format, clear session
        session.clear()
        return False
    
    return True


def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            if request.is_json:
                return jsonify(
                    {"error": "Authentication required", "status": "session_expired"}
                ), 401
            return redirect(url_for("auth.register"))

        return f(*args, **kwargs)

    return decorated_function


def require_quant(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            if request.is_json:
                return jsonify(
                    {"error": "Authentication required", "status": "session_expired"}
                ), 401
            return redirect(url_for("auth.register"))

        # Check if user is The CHANCELLOR
        current_username = session.get("username")
        quant_username = current_app.config.get("QUANT_USERNAME", "CHANCELLOR")
        quant_enabled = current_app.config.get("QUANT_ENABLED", False)

        if (
            not quant_enabled
            or not current_username
            or current_username.upper() != quant_username.upper()
        ):
            if request.is_json:
                return jsonify(
                    {
                        "error": "Unauthorized - Quant access required",
                        "status": "unauthorized",
                    }
                ), 403
            return render_template("403.jinja2"), 403

        return f(*args, **kwargs)

    return decorated_function


@bp.route("/register")
def register():
    if is_authenticated():
        return redirect(url_for("home_page"))

    expired = request.args.get('expired', False)
    return render_template(
        "register.jinja2", 
        title="Join The Revolution - Straw Coin Registration",
        expired=expired
    )


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or "username" not in data:
        return jsonify(
            {"error": "Username required", "status": "invalid_credentials"}
        ), 400

    username = data["username"].strip().upper() if data["username"] else ""
    is_performer = data.get("is_performer", False)

    if not username or len(username) < 3:
        return jsonify(
            {
                "error": "Username must be at least 3 characters",
                "status": "validation_error",
            }
        ), 400

    balance = get_user_balance(username)
    performer_status = get_user_performer_status(username)

    if balance is None:
        user_id = create_user(username, is_performer)
        if user_id is None:
            return jsonify(
                {"error": "Username already exists", "status": "duplicate_stakeholder"}
            ), 409
        balance = 10000
        performer_status = is_performer

    # Set Flask session with timestamp
    session["username"] = username
    session["session_created"] = datetime.now().isoformat()
    session.permanent = False  # Use non-permanent session cookies

    user_type = "performer" if performer_status else "audience member"
    return jsonify(
        {
            "message": f"User {username} successfully registered as {user_type}",
            "username": username,
            "balance": balance,
            "is_performer": performer_status,
            "user_type": user_type,
            "status": "authentication_successful",
        }
    ), 200


@bp.route("/session-status")
def session_status():
    if not is_authenticated():
        return jsonify({"authenticated": False, "status": "session_expired"}), 401

    # Calculate remaining session time
    session_created = datetime.fromisoformat(session["session_created"])
    session_age = datetime.now() - session_created
    remaining_seconds = max(0, 60 - int(session_age.total_seconds()))
    
    return jsonify(
        {
            "authenticated": True,
            "username": session["username"],
            "status": "session_active",
            "remaining_seconds": remaining_seconds,
        }
    ), 200








@bp.route("/logout", methods=["POST"])
def logout():
    """Log out and clear session."""
    username = session.get("username", "Unknown")
    session.clear()

    return jsonify(
        {
            "message": f"User {username} successfully logged out",
            "status": "logout_successful",
        }
    ), 200
