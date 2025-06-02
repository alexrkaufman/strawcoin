from functools import wraps
from datetime import datetime, timedelta
import secrets
from flask import (
    Blueprint,
    request,
    session,
    redirect,
    url_for,
    render_template,
    jsonify,
    current_app,
)
from .db import (
    create_user, 
    get_user_balance, 
    has_active_session, 
    create_session, 
    update_session_activity, 
    remove_session,
    get_user_performer_status
)

bp = Blueprint("auth", __name__)


def is_authenticated():
    if "username" not in session or "last_activity" not in session:
        return False

    last_activity = datetime.fromisoformat(session["last_activity"])
    timeout_threshold = datetime.now() - timedelta(
        seconds=current_app.config["SESSION_TIMEOUT_SECONDS"]
    )

    if last_activity < timeout_threshold:
        session.clear()
        return False

    return True


def update_activity():
    if "username" in session and "session_id" in session:
        session["last_activity"] = datetime.now().isoformat()
        session.permanent = True
        # Update session activity in database
        update_session_activity(session["session_id"])


def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            if request.is_json:
                return jsonify(
                    {"error": "Authentication required", "status": "session_expired"}
                ), 401
            return redirect(url_for("auth.register"))

        update_activity()
        return f(*args, **kwargs)

    return decorated_function


@bp.route("/register")
def register():
    if is_authenticated():
        return redirect(url_for("home_page"))

    return render_template(
        "register.jinja2", title="Join The Revolution - Straw Coin Registration"
    )


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or "username" not in data:
        return jsonify(
            {"error": "Username required", "status": "invalid_credentials"}
        ), 400

    username = data["username"].strip()
    is_performer = data.get("is_performer", False)

    if not username or len(username) < 3:
        return jsonify(
            {
                "error": "Username must be at least 3 characters",
                "status": "validation_error",
            }
        ), 400

    # Check for active session before allowing login
    if has_active_session(username):
        return jsonify(
            {
                "error": f"User {username} is already logged in. Only one session per user is allowed.",
                "status": "session_conflict"
            }
        ), 409

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
    else:
        # Create balance snapshot for existing user login
        from .db import get_db, create_balance_snapshot

        db = get_db()
        user = db.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if user:
            create_balance_snapshot(user["id"], balance)

    # Generate unique session ID
    session_id = secrets.token_urlsafe(32)
    
    # Create session record in database
    if not create_session(username, session_id):
        return jsonify(
            {"error": "Failed to create session", "status": "session_error"}
        ), 500

    session["username"] = username
    session["user_balance"] = balance
    session["session_id"] = session_id
    session["last_activity"] = datetime.now().isoformat()
    session["session_start"] = datetime.now().isoformat()
    session.permanent = True

    user_type = "performer" if performer_status else "audience member"
    return jsonify(
        {
            "message": f"User {username} successfully registered as {user_type}",
            "username": username,
            "balance": balance,
            "is_performer": performer_status,
            "user_type": user_type,
            "session_timeout_seconds": current_app.config["SESSION_TIMEOUT_SECONDS"],
            "debug_mode": current_app.debug,
            "status": "authentication_successful",
        }
    ), 200


@bp.route("/session-status")
def session_status():
    if not is_authenticated():
        return jsonify({"authenticated": False, "status": "session_expired"}), 401

    last_activity = datetime.fromisoformat(session["last_activity"])
    time_remaining = (
        current_app.config["SESSION_TIMEOUT_SECONDS"]
        - (datetime.now() - last_activity).total_seconds()
    )

    return jsonify(
        {
            "authenticated": True,
            "username": session["username"],
            "time_remaining_seconds": max(0, int(time_remaining)),
            "status": "session_active",
        }
    ), 200


@bp.route("/session-expired")
def session_expired():
    return render_template(
        "session_expired.jinja2", title="Session Expired - Straw Coin"
    )


@bp.route("/update-activity", methods=["POST"])
def update_activity_endpoint():
    if not is_authenticated():
        return jsonify({"error": "Session expired", "status": "session_expired"}), 401

    update_activity()

    return jsonify(
        {
            "message": "Activity updated",
            "time_remaining_seconds": current_app.config["SESSION_TIMEOUT_SECONDS"],
            "status": "activity_updated",
        }
    ), 200


@bp.route("/logout", methods=["POST"])
def logout():
    """Manually log out and clean up session."""
    if "session_id" in session:
        remove_session(session["session_id"])
    
    username = session.get("username", "Unknown")
    session.clear()
    
    return jsonify(
        {
            "message": f"User {username} successfully logged out",
            "status": "logout_successful"
        }
    ), 200


@bp.before_app_request
def track_activity():
    public_endpoints = [
        "auth.register",
        "auth.session_expired", 
        "auth.login",
        "auth.logout",
        "auth.session_status",
        "auth.update_activity_endpoint",
        "api.register_user",
    ]

    if request.endpoint and (
        request.endpoint.startswith("static") or request.endpoint in public_endpoints
    ):
        return

    if "username" in session:
        if not is_authenticated():
            # Clean up session record if session expired
            if "session_id" in session:
                remove_session(session["session_id"])
            session.clear()
            
            if request.is_json:
                return jsonify(
                    {"error": "Session expired", "status": "session_timeout"}
                ), 401
            return redirect(url_for("auth.session_expired"))
        update_activity()
