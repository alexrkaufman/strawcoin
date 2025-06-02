import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def cleanup_sessions_on_startup():
    """Clean up expired sessions when the app starts."""
    try:
        from flask import current_app

        if current_app:
            timeout_seconds = current_app.config.get("SESSION_TIMEOUT_SECONDS", 300)
            cleanup_expired_sessions(timeout_seconds)
    except Exception:
        pass  # Ignore errors during startup cleanup


def init_db():
    db = get_db()

    # Check if database exists and has tables
    tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    existing_tables = [table["name"] for table in tables]

    if not existing_tables:
        # Fresh database - create all tables
        with current_app.open_resource("schema.sql") as f:
            db.executescript(f.read().decode("utf8"))

        # Create initial snapshots for any existing users (shouldn't be any in fresh DB)
        create_balance_snapshots_for_all_users()
        click.echo("Created fresh database with all tables")
    else:
        # Existing database - check for missing tables and migrate
        required_tables = [
            "users",
            "transactions",
            "balance_snapshots",
            "active_sessions",
        ]
        missing_tables = [
            table for table in required_tables if table not in existing_tables
        ]

        # Check if users table needs is_performer column (only if users table exists)
        needs_performer_column = False
        if "users" not in missing_tables:
            user_columns = db.execute("PRAGMA table_info(users)").fetchall()
            column_names = [col["name"] for col in user_columns]
            needs_performer_column = "is_performer" not in column_names

        if missing_tables or needs_performer_column:
            if missing_tables:
                click.echo(
                    f"Found existing database, migrating missing tables: {missing_tables}"
                )
            if needs_performer_column:
                click.echo("Adding is_performer column to users table")

            # Add missing tables
            if "users" in missing_tables:
                db.execute("""
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        coin_balance INTEGER NOT NULL DEFAULT 10000,
                        is_performer BOOLEAN NOT NULL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                db.execute("CREATE INDEX idx_users_username ON users(username)")
                click.echo("Added users table")

            if "transactions" in missing_tables:
                db.execute("""
                    CREATE TABLE transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sender_id INTEGER NOT NULL,
                        recipient_id INTEGER NOT NULL,
                        amount INTEGER NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (sender_id) REFERENCES users (id),
                        FOREIGN KEY (recipient_id) REFERENCES users (id)
                    )
                """)
                db.execute("CREATE INDEX idx_transactions_sender ON transactions(sender_id)")
                db.execute("CREATE INDEX idx_transactions_recipient ON transactions(recipient_id)")
                db.execute("CREATE INDEX idx_transactions_timestamp ON transactions(timestamp)")
                click.echo("Added transactions table")

            if "balance_snapshots" in missing_tables:
                db.execute("""
                    CREATE TABLE balance_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        balance INTEGER NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
                db.execute(
                    "CREATE INDEX idx_balance_snapshots_user_time ON balance_snapshots(user_id, timestamp)"
                )
                db.execute(
                    "CREATE INDEX idx_balance_snapshots_timestamp ON balance_snapshots(timestamp)"
                )
                click.echo("Added balance_snapshots table")

            if "active_sessions" in missing_tables:
                db.execute("""
                    CREATE TABLE active_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        session_id TEXT UNIQUE NOT NULL,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (username) REFERENCES users (username)
                    )
                """)
                db.execute(
                    "CREATE INDEX idx_active_sessions_username ON active_sessions(username)"
                )
                db.execute(
                    "CREATE INDEX idx_active_sessions_session_id ON active_sessions(session_id)"
                )
                db.execute(
                    "CREATE INDEX idx_active_sessions_last_activity ON active_sessions(last_activity)"
                )
                click.echo("Added active_sessions table")

            # Add is_performer column to users table if missing
            if needs_performer_column:
                db.execute(
                    "ALTER TABLE users ADD COLUMN is_performer BOOLEAN NOT NULL DEFAULT 0"
                )
                click.echo("Added is_performer column to users table")

            db.commit()

            # Create initial snapshots for existing users
            users = db.execute("SELECT id, coin_balance FROM users").fetchall()
            if users:
                for user in users:
                    create_balance_snapshot(user["id"], user["coin_balance"])
                db.commit()
                click.echo(f"Created initial snapshots for {len(users)} existing users")
        else:
            click.echo("Database is up to date")


@click.command("init-db")
@with_appcontext
def init_db_command():
    init_db()
    click.echo("Initialized Straw Coin database 🚀")


@click.command("reset-db")
@click.confirmation_option(
    prompt="Are you sure you want to reset the database? This will delete ALL data!"
)
@with_appcontext
def reset_db_command():
    """Reset the database by dropping all tables and recreating them."""
    db = get_db()

    # Drop all tables
    tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    for table in tables:
        db.execute(f"DROP TABLE IF EXISTS {table['name']}")

    # Drop all indexes
    indexes = db.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
    for index in indexes:
        if not index["name"].startswith("sqlite_"):  # Don't drop system indexes
            db.execute(f"DROP INDEX IF EXISTS {index['name']}")

    db.commit()

    # Recreate database
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))

    click.echo("🗑️  Database reset complete - all data deleted and tables recreated")


@click.command("reset-balances")
@click.confirmation_option(
    prompt="Are you sure you want to reset all user balances to 10,000?"
)
@with_appcontext
def reset_balances_command():
    """Reset all user balances to 10,000 coins."""
    db = get_db()

    try:
        # Reset all balances
        db.execute("UPDATE users SET coin_balance = 10000")

        # Clear all transactions
        db.execute("DELETE FROM transactions")

        # Clear all balance snapshots
        db.execute("DELETE FROM balance_snapshots")

        # Create fresh snapshots
        users = db.execute("SELECT id FROM users").fetchall()
        for user in users:
            create_balance_snapshot(user["id"], 10000)

        db.commit()
        click.echo(f"💰 Reset balances for {len(users)} users to 10,000 coins each")

    except Exception as e:
        db.rollback()
        click.echo(f"❌ Failed to reset balances: {e}")


@click.command("create-snapshots")
@with_appcontext
def create_snapshots_command():
    """Create balance snapshots for all users."""
    success = create_balance_snapshots_for_all_users()
    if success:
        click.echo("✅ Balance snapshots created for all users")
    else:
        click.echo("❌ Failed to create balance snapshots")


@click.command("cleanup-snapshots")
@click.option("--hours", default=6, help="Number of hours of snapshots to keep")
@with_appcontext
def cleanup_snapshots_command(hours):
    """Clean up old balance snapshots."""
    success = cleanup_old_snapshots(hours)
    if success:
        click.echo(f"✅ Cleaned up snapshots older than {hours} hours")
    else:
        click.echo("❌ Failed to clean up snapshots")


@click.command("cleanup-sessions")
@with_appcontext
def cleanup_sessions_command():
    """Clean up expired sessions."""
    timeout_seconds = current_app.config.get("SESSION_TIMEOUT_SECONDS", 300)
    success = cleanup_expired_sessions(timeout_seconds)
    if success:
        click.echo(f"✅ Cleaned up expired sessions (timeout: {timeout_seconds}s)")
    else:
        click.echo("❌ Failed to clean up expired sessions")


@click.command("list-sessions")
@with_appcontext
def list_sessions_command():
    """List all active sessions."""
    db = get_db()
    sessions = db.execute(
        "SELECT username, session_id, last_activity, created_at FROM active_sessions ORDER BY last_activity DESC"
    ).fetchall()

    if sessions:
        click.echo("Active Sessions:")
        for session in sessions:
            click.echo(
                f"  {session['username']} - Last activity: {session['last_activity']} (Created: {session['created_at']})"
            )
    else:
        click.echo("No active sessions")


@click.command("clear-sessions")
@click.confirmation_option(prompt="Are you sure you want to clear all active sessions?")
@with_appcontext
def clear_sessions_command():
    """Clear all active sessions."""
    db = get_db()
    try:
        count = db.execute("SELECT COUNT(*) as count FROM active_sessions").fetchone()[
            "count"
        ]
        db.execute("DELETE FROM active_sessions")
        db.commit()
        click.echo(f"✅ Cleared {count} active sessions")
    except Exception as e:
        click.echo(f"❌ Failed to clear sessions: {e}")


@click.command("migrate-db")
@with_appcontext
def migrate_db_command():
    """Migrate database to add missing tables (now handled automatically by init-db)."""
    click.echo(
        '⚠️  migrate-db is deprecated. Use "flask init-db" instead - it now handles migrations automatically.'
    )
    init_db()


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(reset_db_command)
    app.cli.add_command(reset_balances_command)
    app.cli.add_command(create_snapshots_command)
    app.cli.add_command(cleanup_snapshots_command)
    app.cli.add_command(cleanup_sessions_command)
    app.cli.add_command(list_sessions_command)
    app.cli.add_command(clear_sessions_command)
    app.cli.add_command(redistribute_performer_coins_command)
    app.cli.add_command(set_performer_command)
    app.cli.add_command(list_performers_command)
    app.cli.add_command(migrate_db_command)
    app.cli.add_command(create_quant_command)
    app.cli.add_command(run_production_command)


def create_user(username, is_performer=False):
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO users (username, coin_balance, is_performer) VALUES (?, ?, ?)",
            (username, 10000, is_performer),
        )
        user_id = cursor.lastrowid

        # Create initial balance snapshot
        create_balance_snapshot(user_id, 10000)

        db.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None


def get_user_balance(username):
    db = get_db()
    user = db.execute(
        "SELECT coin_balance FROM users WHERE username = ?", (username,)
    ).fetchone()
    return user["coin_balance"] if user else None


def transfer_coins(sender_username, recipient_username, amount):
    if amount <= 0:
        return "invalid_amount"

    # Prevent The Quant from sending coins to themselves
    quant_username = current_app.config.get("QUANT_USERNAME", "TheQuant")
    if sender_username == quant_username and recipient_username == quant_username:
        return "quant_self_transfer_forbidden"

    db = get_db()

    sender = db.execute(
        "SELECT id, coin_balance FROM users WHERE username = ?", (sender_username,)
    ).fetchone()

    recipient = db.execute(
        "SELECT id FROM users WHERE username = ?", (recipient_username,)
    ).fetchone()

    if not sender or not recipient:
        return "user_not_found"

    if sender["coin_balance"] < amount:
        return "insufficient_funds"

    try:
        db.execute(
            "UPDATE users SET coin_balance = coin_balance - ? WHERE username = ?",
            (amount, sender_username),
        )
        db.execute(
            "UPDATE users SET coin_balance = coin_balance + ? WHERE username = ?",
            (amount, recipient_username),
        )
        db.execute(
            "INSERT INTO transactions (sender_id, recipient_id, amount) VALUES (?, ?, ?)",
            (sender["id"], recipient["id"], amount),
        )
        db.commit()

        # Create balance snapshots after successful transaction
        sender_new_balance = sender["coin_balance"] - amount
        recipient_new_balance = db.execute(
            "SELECT coin_balance FROM users WHERE username = ?", (recipient_username,)
        ).fetchone()["coin_balance"]

        create_balance_snapshot(sender["id"], sender_new_balance)
        create_balance_snapshot(recipient["id"], recipient_new_balance)

        return "success"
    except sqlite3.Error:
        db.rollback()
        return "transaction_failed"


def get_all_users():
    db = get_db()
    users = db.execute(
        "SELECT username, coin_balance FROM users ORDER BY coin_balance DESC"
    ).fetchall()
    return [dict(user) for user in users]


def get_transaction_history(username=None, limit=50):
    db = get_db()

    if username:
        transactions = db.execute(
            """
            SELECT t.amount, t.timestamp, sender.username as sender, recipient.username as recipient
            FROM transactions t
            JOIN users sender ON t.sender_id = sender.id
            JOIN users recipient ON t.recipient_id = recipient.id
            WHERE sender.username = ? OR recipient.username = ?
            ORDER BY t.timestamp DESC LIMIT ?
            """,
            (username, username, limit),
        ).fetchall()
    else:
        transactions = db.execute(
            """
            SELECT t.amount, t.timestamp, sender.username as sender, recipient.username as recipient
            FROM transactions t
            JOIN users sender ON t.sender_id = sender.id
            JOIN users recipient ON t.recipient_id = recipient.id
            ORDER BY t.timestamp DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(transaction) for transaction in transactions]


def create_balance_snapshot(user_id, balance):
    """Create a balance snapshot for tracking historical data."""
    db = get_db()
    try:
        db.execute(
            "INSERT INTO balance_snapshots (user_id, balance) VALUES (?, ?)",
            (user_id, balance),
        )
        db.commit()
        return True
    except sqlite3.Error:
        return False


def create_balance_snapshots_for_all_users():
    """Create balance snapshots for all users at the current time."""
    db = get_db()
    try:
        users = db.execute("SELECT id, coin_balance FROM users").fetchall()
        for user in users:
            db.execute(
                "INSERT INTO balance_snapshots (user_id, balance) VALUES (?, ?)",
                (user["id"], user["coin_balance"]),
            )
        db.commit()
        return True
    except sqlite3.Error:
        return False


def get_balance_history(hours_back=0.5):
    """Get balance history for all users over the specified time period."""
    db = get_db()

    # Get snapshots from the last X hours
    snapshots = db.execute(
        """
        SELECT bs.timestamp, u.username, bs.balance
        FROM balance_snapshots bs
        JOIN users u ON bs.user_id = u.id
        WHERE bs.timestamp >= datetime('now', '-' || ? || ' hours')
        ORDER BY bs.timestamp ASC
        """,
        (hours_back,),
    ).fetchall()

    return [dict(snapshot) for snapshot in snapshots]


def get_current_leaderboard_with_snapshots():
    """Get current leaderboard with latest balance snapshots."""
    db = get_db()

    # Get current balances and create snapshots if none exist recently
    users = db.execute(
        """
        SELECT u.id, u.username, u.coin_balance, u.created_at,
               bs.timestamp as last_snapshot
        FROM users u
        LEFT JOIN (
            SELECT user_id, MAX(timestamp) as timestamp
            FROM balance_snapshots
            GROUP BY user_id
        ) bs ON u.id = bs.user_id
        ORDER BY u.coin_balance DESC
        """
    ).fetchall()

    # Create snapshots for users who don't have recent ones (within last 5 minutes)
    current_time = db.execute("SELECT datetime('now') as now").fetchone()["now"]

    for user in users:
        if (
            not user["last_snapshot"]
            or db.execute(
                "SELECT (julianday(?) - julianday(?)) * 24 * 60 as minutes_diff",
                (current_time, user["last_snapshot"]),
            ).fetchone()["minutes_diff"]
            > 5
        ):
            create_balance_snapshot(user["id"], user["coin_balance"])

    return [dict(user) for user in users]


def cleanup_old_snapshots(hours_to_keep=6):
    """Clean up balance snapshots older than specified hours."""
    db = get_db()
    try:
        db.execute(
            "DELETE FROM balance_snapshots WHERE timestamp < datetime('now', '-' || ? || ' hours')",
            (hours_to_keep,),
        )
        db.commit()
        return True
    except sqlite3.Error:
        return False


def create_session(username, session_id):
    """Create an active session record for a user."""
    db = get_db()
    try:
        db.execute(
            "INSERT INTO active_sessions (username, session_id, last_activity) VALUES (?, ?, datetime('now'))",
            (username, session_id),
        )
        db.commit()
        return True
    except sqlite3.Error:
        return False


def update_session_activity(session_id):
    """Update the last activity time for a session."""
    db = get_db()
    try:
        db.execute(
            "UPDATE active_sessions SET last_activity = datetime('now') WHERE session_id = ?",
            (session_id,),
        )
        db.commit()
        return True
    except sqlite3.Error:
        return False


def remove_session(session_id):
    """Remove a session record."""
    db = get_db()
    try:
        db.execute("DELETE FROM active_sessions WHERE session_id = ?", (session_id,))
        db.commit()
        return True
    except sqlite3.Error:
        return False


def cleanup_expired_sessions(timeout_seconds):
    """Remove sessions that have been inactive for longer than the timeout."""
    db = get_db()
    try:
        db.execute(
            "DELETE FROM active_sessions WHERE last_activity < datetime('now', '-' || ? || ' seconds')",
            (timeout_seconds,),
        )
        db.commit()
        return True
    except sqlite3.Error:
        return False


def has_active_session(username):
    """Check if a user has an active session."""
    from flask import current_app

    db = get_db()

    # First cleanup expired sessions
    timeout_seconds = current_app.config.get("SESSION_TIMEOUT_SECONDS", 300)
    cleanup_expired_sessions(timeout_seconds)

    # Check for active sessions
    session = db.execute(
        "SELECT session_id FROM active_sessions WHERE username = ? AND last_activity > datetime('now', '-' || ? || ' seconds')",
        (username, timeout_seconds),
    ).fetchone()

    return session is not None


def get_active_session_count():
    """Get the total number of active sessions."""
    from flask import current_app

    db = get_db()
    timeout_seconds = current_app.config.get("SESSION_TIMEOUT_SECONDS", 300)

    # First cleanup expired sessions
    cleanup_expired_sessions(timeout_seconds)

    # Count active sessions
    count = db.execute(
        "SELECT COUNT(*) as count FROM active_sessions WHERE last_activity > datetime('now', '-' || ? || ' seconds')",
        (timeout_seconds,),
    ).fetchone()

    return count["count"] if count else 0


def get_user_session_id(username):
    """Get the session ID for a user if they have an active session."""
    from flask import current_app

    db = get_db()
    timeout_seconds = current_app.config.get("SESSION_TIMEOUT_SECONDS", 300)

    session = db.execute(
        "SELECT session_id FROM active_sessions WHERE username = ? AND last_activity > datetime('now', '-' || ? || ' seconds')",
        (username, timeout_seconds),
    ).fetchone()

    return session["session_id"] if session else None


def get_session_info(session_id):
    """Get session information by session ID."""
    db = get_db()
    session = db.execute(
        "SELECT username, last_activity, created_at FROM active_sessions WHERE session_id = ?",
        (session_id,),
    ).fetchone()

    return dict(session) if session else None


def set_user_performer_status(username, is_performer):
    """Set a user's performer status."""
    db = get_db()
    try:
        db.execute(
            "UPDATE users SET is_performer = ? WHERE username = ?",
            (is_performer, username),
        )
        db.commit()
        return True
    except sqlite3.Error:
        return False


def get_user_performer_status(username):
    """Get a user's performer status."""
    db = get_db()
    user = db.execute(
        "SELECT is_performer FROM users WHERE username = ?", (username,)
    ).fetchone()
    return bool(user["is_performer"]) if user else None


def get_performers():
    """Get all performers."""
    db = get_db()
    performers = db.execute(
        "SELECT username, coin_balance FROM users WHERE is_performer = 1"
    ).fetchall()
    return [dict(performer) for performer in performers]


def get_audience_members():
    """Get all audience members (non-performers)."""
    db = get_db()
    audience = db.execute(
        "SELECT username, coin_balance FROM users WHERE is_performer = 0"
    ).fetchall()
    return [dict(member) for member in audience]


def performer_redistribution():
    """Redistribute 5 coins from each performer to every audience member."""
    db = get_db()

    # Get all performers and audience members
    performers = db.execute(
        "SELECT id, username, coin_balance FROM users WHERE is_performer = 1"
    ).fetchall()

    # Get audience members but exclude The Quant
    quant_username = current_app.config.get("QUANT_USERNAME", "TheQuant")
    audience = db.execute(
        "SELECT id, username, coin_balance FROM users WHERE is_performer = 0 AND username != ?",
        (quant_username,)
    ).fetchall()

    if not performers or not audience:
        return {"success": False, "message": "No performers or audience members found"}

    audience_count = len(audience)
    performer_count = len(performers)
    coins_per_performer_to_each_audience = 5
    total_coins_needed_per_performer = coins_per_performer_to_each_audience * audience_count
    total_coins_redistributed = 0

    try:
        # Start transaction
        for performer in performers:
            # Check if performer has enough coins
            if performer["coin_balance"] < total_coins_needed_per_performer:
                continue  # Skip performers who don't have enough coins

            # Deduct total coins from performer
            db.execute(
                "UPDATE users SET coin_balance = coin_balance - ? WHERE id = ?",
                (total_coins_needed_per_performer, performer["id"]),
            )

            # Give 5 coins to each audience member
            for audience_member in audience:
                # Add coins to audience member
                db.execute(
                    "UPDATE users SET coin_balance = coin_balance + ? WHERE id = ?",
                    (coins_per_performer_to_each_audience, audience_member["id"]),
                )
                
                # Create transaction record
                db.execute(
                    "INSERT INTO transactions (sender_id, recipient_id, amount) VALUES (?, ?, ?)",
                    (performer["id"], audience_member["id"], coins_per_performer_to_each_audience),
                )

            total_coins_redistributed += total_coins_needed_per_performer

        db.commit()

        # Create balance snapshots for all users after redistribution
        create_balance_snapshots_for_all_users()

        return {
            "success": True,
            "performer_count": performer_count,
            "audience_count": audience_count,
            "coins_per_performer_to_each_audience": coins_per_performer_to_each_audience,
            "total_coins_needed_per_performer": total_coins_needed_per_performer,
            "total_redistributed": total_coins_redistributed,
        }

    except sqlite3.Error as e:
        db.rollback()
        return {"success": False, "message": f"Database error: {e}"}


@click.command("redistribute-performer-coins")
@with_appcontext
def redistribute_performer_coins_command():
    """Manually trigger performer coin redistribution."""
    result = performer_redistribution()
    if result["success"]:
        click.echo(
            f"✅ Redistributed {result['total_redistributed']} coins from {result['performer_count']} performers to {result['audience_count']} audience members"
        )
        click.echo(f"   Each performer lost {result['total_coins_needed_per_performer']} coins")
        click.echo(
            f"   Each audience member gained {result['coins_per_performer_to_each_audience']} coins from each performer"
        )
    else:
        click.echo(f"❌ Redistribution failed: {result['message']}")


@click.command("set-performer")
@click.argument("username")
@click.option(
    "--performer/--audience",
    default=True,
    help="Set as performer (default) or audience member",
)
@with_appcontext
def set_performer_command(username, performer):
    """Set a user's performer status."""
    success = set_user_performer_status(username, performer)
    if success:
        status = "performer" if performer else "audience member"
        click.echo(f"✅ Set {username} as {status}")
    else:
        click.echo(f"❌ Failed to set performer status for {username}")


@click.command("list-performers")
@with_appcontext
def list_performers_command():
    """List all performers."""
    performers = get_performers()
    audience = get_audience_members()

    if performers:
        click.echo("🎭 Performers:")
        for performer in performers:
            click.echo(f"  {performer['username']} - {performer['coin_balance']} coins")
    else:
        click.echo("No performers found")

    if audience:
        click.echo(f"\n👥 Audience Members ({len(audience)}):")
        for member in audience[:5]:  # Show first 5
            click.echo(f"  {member['username']} - {member['coin_balance']} coins")
        if len(audience) > 5:
            click.echo(f"  ... and {len(audience) - 5} more")
    else:
        click.echo("No audience members found")


@click.command("create-quant")
@with_appcontext
def create_quant_command():
    """Create The Quant user with proper settings (0 coins, audience member)."""
    quant_username = current_app.config.get("QUANT_USERNAME", "TheQuant")
    
    # Check if The Quant already exists
    db = get_db()
    existing = db.execute(
        "SELECT username FROM users WHERE username = ?", (quant_username,)
    ).fetchone()
    
    if existing:
        click.echo(f"❌ {quant_username} already exists")
        return
    
    # Create The Quant user
    user_id = create_user(quant_username, is_performer=False)
    if user_id:
        # Set balance to 0 (they should start with no coins)
        db.execute('UPDATE users SET coin_balance = 0 WHERE username = ?', (quant_username,))
        db.commit()
        click.echo(f"✅ Created {quant_username} with 0 coins (audience member)")
    else:
        click.echo(f"❌ Failed to create {quant_username}")


@click.command("run-production")
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=5000, help="Port to bind to")
def run_production_command(host, port):
    """Run the app in production mode with correct configuration."""
    import os
    
    # Set production environment variables
    os.environ["FLASK_ENV"] = "production"
    os.environ["ENVIRONMENT"] = "production"
    
    click.echo("🚀 Starting Straw Coin in production mode...")
    click.echo(f"   Host: {host}")
    click.echo(f"   Port: {port}")
    click.echo(f"   Session timeout: 5 minutes (300 seconds)")
    click.echo(f"   Debug mode: OFF")
    click.echo(f"   Performer redistribution: ON")
    
    # Import here to ensure environment variables are set
    from . import create_app
    app = create_app()
    
    # Verify production config is loaded
    timeout = app.config.get("SESSION_TIMEOUT_SECONDS", 0)
    if timeout == 300:
        click.echo("✅ Production configuration loaded successfully")
    else:
        click.echo(f"⚠️  Warning: Session timeout is {timeout}s (expected 300s)")
    
    # Run the app
    app.run(host=host, port=port, debug=False)
