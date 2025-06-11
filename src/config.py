import os
from datetime import timedelta


class Config:
    """Base configuration"""

    SECRET_KEY = (
        os.environ.get("SECRET_KEY") or "straw_coin_revolutionary_session_key_2024"
    )
    DATABASE = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "instance", "strawcoin.sqlite"
    )

    # Session configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_NAME = "straw_coin_session"

    # Site metadata
    SITE_NAME = "Straw Coin"
    TAGLINE = "Revolutionizing Comedy Market Dynamics - Where Shareholder Value Meets Live Entertainment Excellence"

    # Performer redistribution settings
    ENABLE_PERFORMER_REDISTRIBUTION = False
    PERFORMER_REDISTRIBUTION_INTERVAL = 60  # seconds
    PERFORMER_COIN_LOSS_PER_INTERVAL = (
        5  # coins from each performer to each audience member per interval
    )
    # Dynamic redistribution amount (can be updated at runtime)
    CURRENT_REDISTRIBUTION_AMOUNT = 5  # Default amount

    # The Chancellor - Special market manipulation user
    QUANT_USERNAME = "CHANCELLOR"
    QUANT_ENABLED = True

    # Market status - controls when redistributions occur
    MARKET_OPEN = True
    MARKET_OPEN_HOURS = {
        "start": 18,  # 6 PM
        "end": 23,  # 11 PM
    }

    # Market status override (can be toggled at runtime)
    MARKET_OPEN_OVERRIDE = None  # None = use time-based, True/False = force open/closed


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True
    SESSION_COOKIE_SECURE = False

    # Enable redistribution in development for testing
    ENABLE_PERFORMER_REDISTRIBUTION = True


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False
    SESSION_COOKIE_SECURE = True

    # Enable redistribution in production
    ENABLE_PERFORMER_REDISTRIBUTION = True


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
