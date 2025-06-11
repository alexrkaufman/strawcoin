import os
from re import PatternError

from flask import Flask, abort, current_app, redirect, render_template, url_for

from .auth import require_auth
from .config import DevelopmentConfig, ProductionConfig
from .db import get_db
from .scheduler import init_scheduler


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

    @app.route("/")
    @require_auth
    def home_page():
        from flask import session

        from .db import get_transaction_history, get_user_balance

        db = get_db()
        current_username = session.get("username")

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

            # Get all users for recipient dropdown (excluding current user)
            all_users = db.execute(
                "SELECT username FROM users WHERE username != ? ORDER BY username",
                (current_username,),
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
        from flask import session

        from .db import get_market_status, get_user_balance

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
        from flask import session

        from .db import get_transaction_history, get_user_balance

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
        )

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("error.jinja2", error_icon="🚀💥", error_number=404), 404

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("error.jinja2", error_icon="🚫⚡", error_number=403), 403

    @app.route("/insider-trading-warning")
    @require_auth
    def insider_trading_warning():
        """Display insider trading violation warning page."""
        from datetime import datetime

        from flask import request, session

        username = session.get("username", "Unknown")
        amount = request.args.get("amount", 0)

        return render_template(
            "insider_trading_warning.jinja2",
            username=username,
            amount=amount,
            timestamp=int(datetime.now().timestamp()),
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        )

    @app.route("/quant-independence-warning")
    @require_auth
    def quant_independence_warning():
        """Display Quant independence protection warning page."""
        from flask import request, session

        username = session.get("username", "Unknown")
        amount = request.args.get("amount", 0)

        return render_template(
            "quant_independence_warning.jinja2", username=username, amount=amount
        )

    @app.route("/debug/config")
    def debug_config():
        """Debug endpoint to check which configuration is loaded."""
        config_info = {
            "session_timeout_seconds": app.config.get("SESSION_TIMEOUT_SECONDS"),
            "debug": app.debug,
            "config_class": app.config.__class__.__name__
            if hasattr(app.config, "__class__")
            else "unknown",
            "redistribution_enabled": app.config.get("ENABLE_PERFORMER_REDISTRIBUTION"),
            "session_cookie_secure": app.config.get("SESSION_COOKIE_SECURE"),
        }

        from flask import jsonify

        return jsonify(config_info)

    # Register blueprints
    from . import api, auth, db

    app.register_blueprint(api.bp)
    app.register_blueprint(auth.bp)
    db.init_app(app)

    # Clean up expired sessions on startup
    with app.app_context():
        db.cleanup_sessions_on_startup()

    # Initialize performer redistribution scheduler
    init_scheduler(app)

    return app
