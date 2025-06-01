import sqlite3
import click
from flask import current_app, g
from flask.cli import with_appcontext


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('init-db')
@with_appcontext
def init_db_command():
    init_db()
    click.echo('Initialized Straw Coin database 🚀')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


def create_user(username):
    db = get_db()
    try:
        cursor = db.execute(
            'INSERT INTO users (username, coin_balance) VALUES (?, ?)',
            (username, 10000)
        )
        db.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None


def get_user_balance(username):
    db = get_db()
    user = db.execute(
        'SELECT coin_balance FROM users WHERE username = ?',
        (username,)
    ).fetchone()
    return user['coin_balance'] if user else None


def transfer_coins(sender_username, recipient_username, amount):
    if amount <= 0:
        return 'invalid_amount'
    
    db = get_db()
    
    sender = db.execute(
        'SELECT id, coin_balance FROM users WHERE username = ?',
        (sender_username,)
    ).fetchone()
    
    recipient = db.execute(
        'SELECT id FROM users WHERE username = ?',
        (recipient_username,)
    ).fetchone()
    
    if not sender or not recipient:
        return 'user_not_found'
    
    if sender['coin_balance'] < amount:
        return 'insufficient_funds'
    
    try:
        db.execute(
            'UPDATE users SET coin_balance = coin_balance - ? WHERE username = ?',
            (amount, sender_username)
        )
        db.execute(
            'UPDATE users SET coin_balance = coin_balance + ? WHERE username = ?',
            (amount, recipient_username)
        )
        db.execute(
            'INSERT INTO transactions (sender_id, recipient_id, amount) VALUES (?, ?, ?)',
            (sender['id'], recipient['id'], amount)
        )
        db.commit()
        return 'success'
    except sqlite3.Error:
        db.rollback()
        return 'transaction_failed'


def get_all_users():
    db = get_db()
    users = db.execute(
        'SELECT username, coin_balance FROM users ORDER BY coin_balance DESC'
    ).fetchall()
    return [dict(user) for user in users]


def get_transaction_history(username=None, limit=50):
    db = get_db()
    
    if username:
        transactions = db.execute(
            '''
            SELECT t.amount, t.timestamp, sender.username as sender, recipient.username as recipient
            FROM transactions t
            JOIN users sender ON t.sender_id = sender.id
            JOIN users recipient ON t.recipient_id = recipient.id
            WHERE sender.username = ? OR recipient.username = ?
            ORDER BY t.timestamp DESC LIMIT ?
            ''',
            (username, username, limit)
        ).fetchall()
    else:
        transactions = db.execute(
            '''
            SELECT t.amount, t.timestamp, sender.username as sender, recipient.username as recipient
            FROM transactions t
            JOIN users sender ON t.sender_id = sender.id
            JOIN users recipient ON t.recipient_id = recipient.id
            ORDER BY t.timestamp DESC LIMIT ?
            ''',
            (limit,)
        ).fetchall()
    
    return [dict(transaction) for transaction in transactions]
