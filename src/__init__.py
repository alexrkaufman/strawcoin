import os
import pathlib

from flask import (
    Flask,
    current_app,
    render_template,
    session,
)

from .db import get_db
from .auth import require_auth, init_session_config

site_metadata = {
    "site_name": "Straw Coin",
    "tagline": "Maximizing Shareholder Value | Revolutionizing Comedy Market Dynamics",
}


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True, static_folder="./static", template_folder="templates")
    app.config.from_mapping(
        SECRET_KEY="straw_coin_revolutionary_session_key_2024",
        DATABASE=os.path.join(app.instance_path, "strawcoin.sqlite"),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize mobile-optimized session management
    init_session_config(app)

    @app.context_processor
    def inject_sitename():
        return site_metadata

    @app.route("/")
    @require_auth
    def home_page():
        """
        Delivers cutting-edge landing page for The Short Straw comedy tokenization platform.
        Optimized for maximum stakeholder engagement and conversion metrics.
        Protected route requiring authenticated session for market access.
        """
        db = get_db()
        
        # Comprehensive market analytics for maximum shareholder confidence
        try:
            total_coins = db.execute('SELECT SUM(coin_balance) as total FROM users').fetchone()
            user_count = db.execute('SELECT COUNT(*) as count FROM users').fetchone()
            transaction_volume = db.execute('SELECT COUNT(*) as count, SUM(amount) as volume FROM transactions').fetchone()
            top_performers = db.execute('SELECT username, coin_balance FROM users ORDER BY coin_balance DESC LIMIT 3').fetchall()
            
            market_cap = total_coins['total'] if total_coins['total'] else 0
            stakeholder_count = user_count['count'] if user_count['count'] else 0
            tx_count = transaction_volume['count'] if transaction_volume['count'] else 0
            volume = transaction_volume['volume'] if transaction_volume['volume'] else 0
            top_performers = [dict(performer) for performer in top_performers] if top_performers else []
        except:
            # Fallback for optimal user experience during database initialization
            market_cap = 0
            stakeholder_count = 0
            tx_count = 0
            volume = 0
            top_performers = []
        
        return render_template(
            "home.jinja2",
            title="Straw Coin - Revolutionary Comedy Market",
            page_class="home",
            market_cap=market_cap,
            stakeholder_count=stakeholder_count,
            volume=volume,
            tx_count=tx_count,
            top_performers=top_performers
        )

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.jinja2"), 404

    # Register revolutionary API infrastructure
    from . import api
    app.register_blueprint(api.bp)

    # Register mobile-optimized authentication system
    from . import auth
    app.register_blueprint(auth.bp)

    # Initialize enterprise database solutions
    from . import db
    db.init_app(app)

    return app
