import threading
import time
from datetime import datetime
from flask import current_app
import logging


class PerformerRedistributionScheduler:
    """Background scheduler for automatic performer coin redistribution."""

    def __init__(self, app=None):
        self.app = app
        self.running = False
        self.thread = None
        self.interval = 60  # 60 seconds = 1 minute

    def init_app(self, app):
        """Initialize the scheduler with a Flask app."""
        self.app = app

    def start(self):
        """Start the background redistribution scheduler."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()

        if self.app:
            with self.app.app_context():
                current_app.logger.info(
                    "🎭 Started performer redistribution scheduler (60 second intervals)"
                )

    def stop(self):
        """Stop the background scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

        if self.app:
            with self.app.app_context():
                current_app.logger.info("🛑 Stopped performer redistribution scheduler")

    def _run_scheduler(self):
        """Main scheduler loop - runs in background thread."""
        while self.running:
            try:
                # Wait for the interval
                time.sleep(self.interval)

                if not self.running:
                    break

                # Perform redistribution within app context
                if self.app:
                    with self.app.app_context():
                        self._perform_redistribution()

            except Exception as e:
                if self.app:
                    with self.app.app_context():
                        current_app.logger.error(f"❌ Scheduler error: {e}")
                else:
                    print(f"Scheduler error: {e}")

    def _perform_redistribution(self):
        """Perform the actual coin redistribution."""
        try:
            from .db import (
                performer_redistribution,
                cleanup_expired_sessions,
                is_market_open,
            )

            # Clean up expired sessions first
            timeout_seconds = current_app.config.get("SESSION_TIMEOUT_SECONDS", 300)
            cleanup_expired_sessions(timeout_seconds)

            # Check if market is open before performing redistribution
            if not is_market_open():
                current_app.logger.info("🔴 Market closed - redistribution paused")
                return

            # Perform redistribution
            result = performer_redistribution()

            if result["success"]:
                current_app.logger.info(
                    f"💰 Redistribution: {result['total_redistributed']} coins "
                    f"from {result['performer_count']} performers "
                    f"to {result['audience_count']} audience members"
                )
            else:
                current_app.logger.warning(
                    f"⚠️ Redistribution failed: {result['message']}"
                )

        except Exception as e:
            current_app.logger.error(f"❌ Redistribution error: {e}")


# Global scheduler instance
scheduler = PerformerRedistributionScheduler()


def init_scheduler(app):
    """Initialize and start the performer redistribution scheduler."""
    scheduler.init_app(app)

    # Only start if explicitly enabled in config
    if app.config.get("ENABLE_PERFORMER_REDISTRIBUTION", False):
        scheduler.start()

        # Register cleanup on app teardown
        @app.teardown_appcontext
        def stop_scheduler(error):
            if error:
                scheduler.stop()
