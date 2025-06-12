import os

from flask import Flask, abort, current_app, redirect, render_template, session, url_for, request, jsonify

from .auth import require_auth, require_quant
from .config import DevelopmentConfig, ProductionConfig
from .db import get_db, get_market_status, get_transaction_history, get_user_balance
from .scheduler import init_scheduler
from datetime import datetime, timedelta


def create_app(test_config=None):
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder="../static",
        template_folder="templates",
    )

    # Load configuration based on Flask's debug mode
    if test_config is not None:
        app.config.from_mapping(test_config)
    elif app.debug:
        app.config.from_object(DevelopmentConfig)
    else:
        app.config.from_object(ProductionConfig)

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    @app.context_processor
    def inject_sitename():
        return {"site_name": app.config["SITE_NAME"], "tagline": app.config["TAGLINE"]}

    @app.before_request
    def check_session_timeout():
        # Skip session check for static files and auth endpoints
        if request.endpoint and (
            request.endpoint.startswith('static') or 
            request.endpoint in ['auth.register', 'auth.login']
        ):
            return
        
        # Check if user has a session
        if 'username' in session:
            # Check if user is CHANCELLOR - they never expire
            current_username = session.get('username', '').upper()
            quant_username = app.config.get("QUANT_USERNAME", "CHANCELLOR").upper()
            if current_username == quant_username:
                return  # Skip all timeout checks for CHANCELLOR
            
            # Check if session has a timestamp
            if 'session_created' not in session:
                session.clear()
                if request.is_json:
                    return jsonify({"error": "Session expired", "status": "session_expired"}), 401
                return redirect(url_for('auth.register', expired=1))
            
            try:
                # Check if session is older than 60 seconds
                session_created = datetime.fromisoformat(session['session_created'])
                session_age = datetime.now() - session_created
                
                if session_age > timedelta(seconds=60):
                    # Session expired
                    session.clear()
                    if request.is_json:
                        return jsonify({"error": "Session expired", "status": "session_expired"}), 401
                    return redirect(url_for('auth.register', expired=1))
            except (ValueError, TypeError, KeyError):
                # Invalid session data, clear it
                session.clear()
                if request.is_json:
                    return jsonify({"error": "Session expired", "status": "session_expired"}), 401
                return redirect(url_for('auth.register', expired=1))

    @app.route("/")
    @require_auth
    def home_page():
        db = get_db()
        current_username = session.get("username")
        
        # Extra safety check - if username is None after auth, redirect to register
        if not current_username:
            session.clear()
            return redirect(url_for('auth.register', expired=1))

        # Redirect The CHANCELLOR to their terminal
        quant_username = app.config.get("QUANT_USERNAME", "CHANCELLOR")
        quant_enabled = app.config.get("QUANT_ENABLED", False)
        if quant_enabled and current_username == quant_username:
            return redirect(url_for("quant_terminal"))

        try:
            total_coins = db.execute(
                "SELECT SUM(coin_balance) as total FROM users"
            ).fetchone()
            user_count = db.execute("SELECT COUNT(*) as count FROM users").fetchone()
            transaction_volume = db.execute(
                "SELECT COUNT(*) as count, SUM(amount) as volume FROM transactions"
            ).fetchone()
            top_performers = db.execute(
                "SELECT username, coin_balance FROM users ORDER BY coin_balance DESC LIMIT 3"
            ).fetchall()

            # Get current user's data
            current_user_balance = (
                get_user_balance(current_username) if current_username else 0
            )
            recent_transactions = (
                get_transaction_history(current_username, 5) if current_username else []
            )

            # Get all users for recipient dropdown (including current user for self-dealing detection)
            all_users = db.execute(
                "SELECT username, is_performer FROM users ORDER BY username"
            ).fetchall()
            available_recipients = (
                [dict(user) for user in all_users] if all_users else []
            )

            # Get performer stats
            performer_count = db.execute(
                "SELECT COUNT(*) as count FROM users WHERE is_performer = 1"
            ).fetchone()
            audience_count = db.execute(
                "SELECT COUNT(*) as count FROM users WHERE is_performer = 0"
            ).fetchone()
            current_user_is_performer = db.execute(
                "SELECT is_performer FROM users WHERE username = ?", (current_username,)
            ).fetchone()

            market_cap = total_coins["total"] or 0
            stakeholder_count = user_count["count"] or 0
            tx_count = transaction_volume["count"] or 0
            volume = transaction_volume["volume"] or 0
            top_performers = (
                [dict(performer) for performer in top_performers]
                if top_performers
                else []
            )
        except Exception as e:
            current_app.logger.error(f"Database error in home_page: {e}")
            market_cap = stakeholder_count = tx_count = volume = 0
            top_performers = []
            current_user_balance = 0
            recent_transactions = []
            available_recipients = []
            performer_count = {"count": 0}
            audience_count = {"count": 0}
            current_user_is_performer = {"is_performer": 0}

        return render_template(
            "home.jinja2",
            title="Straw Coin - Revolutionary Comedy Market",
            page_class="home",
            market_cap=market_cap,
            stakeholder_count=stakeholder_count,
            volume=volume,
            tx_count=tx_count,
            top_performers=top_performers,
            current_username=current_username,
            current_user_balance=current_user_balance,
            recent_transactions=recent_transactions,
            available_recipients=available_recipients,
            performer_count=performer_count["count"],
            audience_count=audience_count["count"],
            current_user_is_performer=bool(current_user_is_performer["is_performer"])
            if current_user_is_performer
            else False,
            redistribution_enabled=app.config.get(
                "ENABLE_PERFORMER_REDISTRIBUTION", False
            ),
        )

    @app.route("/leaderboard")
    def leaderboard_page():
        current_username = session.get("username")
        current_user_balance = (
            get_user_balance(current_username) if current_username else 0
        )

        # Get current market status
        market_status = get_market_status()

        return render_template(
            "leaderboard.jinja2",
            title="Real-Time Leaderboard - Straw Coin Racing",
            page_class="leaderboard",
            current_username=current_username,
            current_user_balance=current_user_balance,
            market_status=market_status,
        )

    @app.route("/quant")
    @require_auth
    def quant_terminal():
        current_username = session.get("username")
        quant_username = app.config.get("QUANT_USERNAME", "CHANCELLOR")
        quant_enabled = app.config.get("QUANT_ENABLED", False)

        # Check if user is The CHANCELLOR
        if not quant_enabled or current_username != quant_username:
            abort(403)

        db = get_db()

        try:
            # Get all the market data that would normally be on home page
            total_coins = db.execute(
                "SELECT SUM(coin_balance) as total FROM users"
            ).fetchone()
            user_count = db.execute("SELECT COUNT(*) as count FROM users").fetchone()
            transaction_volume = db.execute(
                "SELECT COUNT(*) as count, SUM(amount) as volume FROM transactions"
            ).fetchone()
            top_performers = db.execute(
                "SELECT username, coin_balance FROM users ORDER BY coin_balance DESC LIMIT 5"
            ).fetchall()

            # Get current user's data
            current_user_balance = get_user_balance(current_username)
            recent_transactions = get_transaction_history(current_username, 10)

            # Get all users for manipulation targets
            all_users = db.execute(
                "SELECT username, coin_balance, is_performer, created_at FROM users ORDER BY coin_balance DESC"
            ).fetchall()

            # Get performer stats
            performer_count = db.execute(
                "SELECT COUNT(*) as count FROM users WHERE is_performer = 1"
            ).fetchone()
            audience_count = db.execute(
                "SELECT COUNT(*) as count FROM users WHERE is_performer = 0"
            ).fetchone()

            market_cap = total_coins["total"] or 0
            stakeholder_count = user_count["count"] or 0
            tx_count = transaction_volume["count"] or 0
            volume = transaction_volume["volume"] or 0
            top_performers = (
                [dict(performer) for performer in top_performers]
                if top_performers
                else []
            )
            all_users_list = [dict(user) for user in all_users] if all_users else []

        except Exception as e:
            current_app.logger.error(f"Database error in quant_terminal: {e}")
            market_cap = stakeholder_count = tx_count = volume = 0
            top_performers = []
            current_user_balance = 0
            recent_transactions = []
            all_users_list = []
            performer_count = {"count": 0}
            audience_count = {"count": 0}

        return render_template(
            "quant_terminal.jinja2",
            title="The CHANCELLOR - Market Manipulation Terminal",
            page_class="quant",
            current_username=current_username,
            quant_enabled=quant_enabled,
            # Market data from home page
            market_cap=market_cap,
            stakeholder_count=stakeholder_count,
            volume=volume,
            tx_count=tx_count,
            top_performers=top_performers,
            current_user_balance=current_user_balance,
            recent_transactions=recent_transactions,
            performer_count=performer_count["count"],
            audience_count=audience_count["count"],
            all_users=all_users_list,
            redistribution_enabled=app.config.get(
                "ENABLE_PERFORMER_REDISTRIBUTION", False
            ),
            market_status=get_market_status(),
        )

    @app.route("/chancellor-graph")
    @require_quant
    def chancellor_graph():
        """Chancellor-only stock graph showing top 5 performers over last 10 minutes."""
        current_username = session.get("username")
        
        return render_template(
            "chancellor_graph.jinja2",
            title="Chancellor's Market Oversight - Top 5 Performers",
            page_class="chancellor-graph",
            current_username=current_username,
        )

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template(
            "error.jinja2",
            page_class="error",
            error_icon="🚀💥",
            error_title="404 - Stock not found",
            error_description="The requested resource has been volatilized by market forces.",
        ), 404

    @app.errorhandler(403)
    def forbidden(error):
        return render_template(
            "error.jinja2",
            page_class="error",
            error_icon="🚫⚡",
            error_title="403 - Unknown User",
            error_description="Straw coin maintains regulatory compliance through know your customer procedures. Please log in.",
        ), 403

    @app.errorhandler(400)
    def insufficient_funds(error):
        return render_template(
            "error.jinja2",
            page_class="error",
            error_icon="🚫🪙🚫",
            error_title="400 - Insufficient Funds",
        ), 400

    @app.route("/self-dealing-warning")
    def self_dealing_warning():
        return render_template(
            "error.jinja2",
            page_class="error",
            error_icon="🏛️⚖️🏛️",
            error_title="SELF DEALING DETECTED",
            error_description="Your coins have been sent to the CHANCELLOR to fund market integrity efforts.",
        )

    @app.route("/market-manipulation")
    def market_manipulation_warning():
        return render_template(
            "error.jinja2",
            page_class="error",
            error_icon="🏛️⚖️🏛️",
            error_title="MARKET MANIPULATION DETECTED",
            error_description="""To maintain CHANCELLOR independence your transfer has been blocked.
            Other market maipulation such as self-dealing will result in confiscation.""",
        )

    # Register blueprints
    from . import api, auth, db

    app.register_blueprint(api.bp)
    app.register_blueprint(auth.bp)
    db.init_app(app)

    # Initialize performer redistribution scheduler
    init_scheduler(app)

    return app
