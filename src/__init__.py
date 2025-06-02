import os

from flask import Flask, render_template

from .auth import require_auth
from .config import DevelopmentConfig, ProductionConfig
from .db import get_db


def create_app(test_config=None):
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder="./static",
        template_folder="templates",
    )

    # Load configuration
    env = os.environ.get("FLASK_ENV", "development")
    if env == "production":
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    if test_config:
        app.config.from_mapping(test_config)

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
        )

    @app.route("/leaderboard")
    @require_auth
    def leaderboard_page():
        from flask import session

        from .db import get_user_balance

        current_username = session.get("username")
        current_user_balance = (
            get_user_balance(current_username) if current_username else 0
        )

        return render_template(
            "leaderboard.jinja2",
            title="Real-Time Leaderboard - Straw Coin Racing",
            page_class="leaderboard",
            current_username=current_username,
            current_user_balance=current_user_balance,
        )

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.jinja2"), 404

    # Register blueprints
    from . import api, auth, db

    app.register_blueprint(api.bp)
    app.register_blueprint(auth.bp)
    db.init_app(app)

    return app
