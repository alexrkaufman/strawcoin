import threading
import time
from datetime import datetime
from flask import current_app
import logging


class PerformerRedistributionScheduler:
    """Background scheduler for automatic performer coin redistribution and balance snapshots."""

    def __init__(self, app=None):
        self.app = app
        self.running = False
        self.redistribution_thread = None
        self.snapshot_thread = None
        self.redistribution_interval = 60  # 60 seconds = 1 minute
        self.snapshot_interval = 10  # 10 seconds for balance snapshots

    def init_app(self, app):
        """Initialize the scheduler with a Flask app."""
        self.app = app

    def start(self):
        """Start the background redistribution and snapshot schedulers."""
        if self.running:
            return

        self.running = True
        
        # Start redistribution thread
        self.redistribution_thread = threading.Thread(target=self._run_redistribution_scheduler, daemon=True)
        self.redistribution_thread.start()
        
        # Start snapshot thread
        self.snapshot_thread = threading.Thread(target=self._run_snapshot_scheduler, daemon=True)
        self.snapshot_thread.start()

        if self.app:
            with self.app.app_context():
                current_app.logger.info(
                    "🎭 Started performer redistribution scheduler (60 second intervals)"
                )
                current_app.logger.info(
                    "📸 Started balance snapshot scheduler (10 second intervals)"
                )

    def stop(self):
        """Stop the background schedulers."""
        self.running = False
        
        if self.redistribution_thread:
            self.redistribution_thread.join(timeout=5)
        
        if self.snapshot_thread:
            self.snapshot_thread.join(timeout=5)

        if self.app:
            with self.app.app_context():
                current_app.logger.info("🛑 Stopped performer redistribution scheduler")
                current_app.logger.info("🛑 Stopped balance snapshot scheduler")

    def _run_redistribution_scheduler(self):
        """Redistribution scheduler loop - runs in background thread."""
        while self.running:
            try:
                # Wait for the interval
                time.sleep(self.redistribution_interval)

                if not self.running:
                    break

                # Perform redistribution within app context
                if self.app:
                    with self.app.app_context():
                        self._perform_redistribution()

            except Exception as e:
                if self.app:
                    with self.app.app_context():
                        current_app.logger.error(f"❌ Redistribution scheduler error: {e}")
                else:
                    print(f"Redistribution scheduler error: {e}")
    
    def _run_snapshot_scheduler(self):
        """Snapshot scheduler loop - runs in background thread."""
        while self.running:
            try:
                # Perform snapshot within app context
                if self.app:
                    with self.app.app_context():
                        self._create_balance_snapshots()
                
                # Wait for the interval
                time.sleep(self.snapshot_interval)

                if not self.running:
                    break

            except Exception as e:
                if self.app:
                    with self.app.app_context():
                        current_app.logger.error(f"❌ Snapshot scheduler error: {e}")
                else:
                    print(f"Snapshot scheduler error: {e}")

    def _perform_redistribution(self):
        """Perform the actual coin redistribution."""
        try:
            from .db import (
                performer_redistribution,
                is_market_open,
            )

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

    def _create_balance_snapshots(self):
        """Create balance snapshots for all users."""
        try:
            from .db import create_balance_snapshots_for_all_users
            
            result = create_balance_snapshots_for_all_users()
            if result:
                current_app.logger.debug("📸 Created balance snapshots for all users")
            else:
                current_app.logger.warning("⚠️ Failed to create balance snapshots")
                
        except Exception as e:
            current_app.logger.error(f"❌ Balance snapshot error: {e}")


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
