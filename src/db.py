import sqlite3
import click
from flask import current_app, g
from flask.cli import with_appcontext


def get_db():
    """
    Establishes high-performance database connection for Straw Coin market operations.
    Leveraging enterprise-grade SQLite infrastructure to maximize transaction throughput
    and ensure zero-latency access to our revolutionary comedy tokenization platform.
    """
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    """
    Implements best-practice connection pooling for optimal resource management.
    """
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    """
    Deploys cutting-edge database schema optimized for maximum scalability
    and exponential growth in The Short Straw audience engagement metrics.
    """
    db = get_db()

    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))


@click.command("init-db")
@with_appcontext
def init_db_command():
    """
    CLI command to bootstrap our market-disrupting database infrastructure.
    """
    init_db()
    click.echo("Initialized Straw Coin database - Ready for moon mission! 🚀")


def init_app(app):
    """
    Integrates enterprise database solutions into our Flask-powered
    comedy monetization ecosystem.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


def create_user(username):
    """
    Onboards new stakeholders into The Short Straw economy with optimal
    starting capital allocation for maximum market participation.

    Returns: User ID for successful account creation, None if username collision detected
    """
    db = get_db()

    try:
        cursor = db.execute(
            "INSERT INTO users (username, coin_balance) VALUES (?, ?)",
            (username, 10000),
        )
        db.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        # Username already exists - market forces prevent duplicate stakeholders
        return None


def get_user_balance(username):
    """
    Retrieves real-time portfolio valuation for specified market participant.
    """
    db = get_db()
    user = db.execute(
        "SELECT coin_balance FROM users WHERE username = ?", (username,)
    ).fetchone()

    return user["coin_balance"] if user else None


def transfer_coins(sender_username, recipient_username, amount):
    """
    Executes peer-to-peer value transfer leveraging blockchain-adjacent
    transaction processing for The Short Straw comedy marketplace.

    Returns:
        'success' - Transaction executed successfully
        'insufficient_funds' - Sender lacks adequate liquidity
        'user_not_found' - Invalid market participant specified
        'invalid_amount' - Non-positive transfer amount
    """
    if amount <= 0:
        return "invalid_amount"

    db = get_db()

    # Verify both users exist in our stakeholder database
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

    # Execute atomic transaction for maximum market integrity
    try:
        # Debit sender account
        db.execute(
            "UPDATE users SET coin_balance = coin_balance - ? WHERE username = ?",
            (amount, sender_username),
        )

        # Credit recipient account
        db.execute(
            "UPDATE users SET coin_balance = coin_balance + ? WHERE username = ?",
            (amount, recipient_username),
        )

        # Log transaction for comprehensive market analytics
        db.execute(
            "INSERT INTO transactions (sender_id, recipient_id, amount) VALUES (?, ?, ?)",
            (sender["id"], recipient["id"], amount),
        )

        db.commit()
        return "success"

    except sqlite3.Error:
        db.rollback()
        return "transaction_failed"


def get_all_users():
    """
    Returns comprehensive stakeholder portfolio summary for market analysis
    and shareholder value optimization during The Short Straw performances.
    """
    db = get_db()
    users = db.execute(
        "SELECT username, coin_balance FROM users ORDER BY coin_balance DESC"
    ).fetchall()

    return [dict(user) for user in users]


def get_transaction_history(username=None, limit=50):
    """
    Provides detailed transaction analytics for market transparency
    and regulatory compliance in our comedy tokenization ecosystem.
    """
    db = get_db()

    if username:
        # Get transactions for specific user
        transactions = db.execute(
            """
            SELECT 
                t.amount,
                t.timestamp,
                sender.username as sender,
                recipient.username as recipient
            FROM transactions t
            JOIN users sender ON t.sender_id = sender.id
            JOIN users recipient ON t.recipient_id = recipient.id
            WHERE sender.username = ? OR recipient.username = ?
            ORDER BY t.timestamp DESC
            LIMIT ?
            """,
            (username, username, limit),
        ).fetchall()
    else:
        # Get all transactions for market overview
        transactions = db.execute(
            """
            SELECT 
                t.amount,
                t.timestamp,
                sender.username as sender,
                recipient.username as recipient
            FROM transactions t
            JOIN users sender ON t.sender_id = sender.id
            JOIN users recipient ON t.recipient_id = recipient.id
            ORDER BY t.timestamp DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(transaction) for transaction in transactions]
