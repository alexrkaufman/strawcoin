-- Straw Coin Database Schema
-- Enterprise-grade data infrastructure for revolutionary comedy tokenization
-- Optimized for maximum scalability and shareholder value generation

-- Core stakeholder registry for The Short Straw economy
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    coin_balance INTEGER NOT NULL DEFAULT 10000,
    is_performer BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Comprehensive transaction ledger for market transparency and analytics
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL,
    recipient_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    request_text TEXT,
    transaction_type TEXT DEFAULT 'tip',
    status TEXT DEFAULT 'approved',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users (id),
    FOREIGN KEY (recipient_id) REFERENCES users (id)
);

-- Performance optimization indexes for high-frequency trading operations
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_transactions_sender ON transactions(sender_id);
CREATE INDEX idx_transactions_recipient ON transactions(recipient_id);
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);

-- Balance snapshots for real-time leaderboard tracking
CREATE TABLE balance_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    balance INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Index for efficient querying of balance history
CREATE INDEX idx_balance_snapshots_user_time ON balance_snapshots(user_id, timestamp);
CREATE INDEX idx_balance_snapshots_timestamp ON balance_snapshots(timestamp);

-- DEPRECATED: Active sessions table - no longer used after auth simplification
-- Kept for backwards compatibility during migration
-- This table can be safely dropped after all instances are updated
-- CREATE TABLE active_sessions (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     username TEXT NOT NULL,
--     session_id TEXT UNIQUE NOT NULL,
--     last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     FOREIGN KEY (username) REFERENCES users (username)
-- );

-- Market analytics view for real-time portfolio tracking
DROP VIEW IF EXISTS user_stats;
CREATE VIEW user_stats AS
SELECT
    u.username,
    u.coin_balance,
    u.created_at,
    COALESCE(sent.total_sent, 0) as total_sent,
    COALESCE(received.total_received, 0) as total_received,
    COALESCE(sent.transaction_count, 0) + COALESCE(received.transaction_count, 0) as total_transactions
FROM users u
LEFT JOIN (
    SELECT 
        sender_id,
        SUM(amount) as total_sent,
        COUNT(*) as transaction_count
    FROM transactions 
    GROUP BY sender_id
) sent ON u.id = sent.sender_id
LEFT JOIN (
    SELECT 
        recipient_id,
        SUM(amount) as total_received,
        COUNT(*) as transaction_count
    FROM transactions 
    GROUP BY recipient_id
) received ON u.id = received.recipient_id;