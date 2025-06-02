import pytest
import json
from src import create_app
from src.db import get_db, init_db


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": ":memory:",
            "SECRET_KEY": "test-secret-key",
            "SESSION_TIMEOUT_SECONDS": 300,
            "SITE_NAME": "Test Straw Coin",
            "TAGLINE": "Test Trading Platform",
        }
    )

    with app.app_context():
        init_db()
        # Create test users
        db = get_db()
        db.execute(
            "INSERT INTO users (username, coin_balance) VALUES (?, ?)", ("alice", 5000)
        )
        db.execute(
            "INSERT INTO users (username, coin_balance) VALUES (?, ?)", ("bob", 3000)
        )
        db.execute(
            "INSERT INTO users (username, coin_balance) VALUES (?, ?)",
            ("charlie", 8000),
        )
        db.commit()

    yield app


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def authenticated_session(client):
    """Create an authenticated session for alice."""
    response = client.post(
        "/auth/login",
        json={"username": "alice"},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    return client


def test_home_page_shows_send_coins_for_authenticated_user(authenticated_session):
    """Test that the home page shows send coins feature for authenticated users."""
    response = authenticated_session.get("/")
    assert response.status_code == 200

    # Check that send coins section is present
    assert b"Send Coins to Fellow Comedians" in response.data
    assert b"sendCoinsForm" in response.data
    assert b"Quick Send:" in response.data

    # Check user balance display
    assert b"Welcome back, alice!" in response.data
    assert b"5,000 Straw Coins" in response.data


def test_home_page_shows_available_recipients(authenticated_session, app):
    """Test that available recipients are populated correctly."""
    response = authenticated_session.get("/")
    assert response.status_code == 200

    # Should show bob and charlie as options, but not alice (current user)
    assert b"bob" in response.data
    assert b"charlie" in response.data

    # Alice should not be in the recipient list
    response_text = response.data.decode("utf-8")
    recipient_options = response_text.count('option value="alice"')
    assert recipient_options == 0  # Alice shouldn't be in recipient dropdown


def test_send_coins_success(authenticated_session, app):
    """Test successful coin transfer."""
    # Send coins from alice to bob
    response = authenticated_session.post(
        "/api/transfer",
        json={"sender": "alice", "recipient": "bob", "amount": 1000},
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "success"
    assert "Transferred 1000 coins from alice to bob" in data["message"]

    # Verify balances updated
    with app.app_context():
        db = get_db()
        alice_balance = db.execute(
            "SELECT coin_balance FROM users WHERE username = ?", ("alice",)
        ).fetchone()
        bob_balance = db.execute(
            "SELECT coin_balance FROM users WHERE username = ?", ("bob",)
        ).fetchone()

        assert alice_balance["coin_balance"] == 4000  # 5000 - 1000
        assert bob_balance["coin_balance"] == 4000  # 3000 + 1000


def test_send_coins_insufficient_funds(authenticated_session):
    """Test transfer with insufficient funds."""
    response = authenticated_session.post(
        "/api/transfer",
        json={
            "sender": "alice",
            "recipient": "bob",
            "amount": 10000,  # More than alice has
        },
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["status"] == "insufficient_funds"


def test_send_coins_to_nonexistent_user(authenticated_session):
    """Test transfer to non-existent user."""
    response = authenticated_session.post(
        "/api/transfer",
        json={"sender": "alice", "recipient": "nonexistent", "amount": 100},
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 404
    data = json.loads(response.data)
    assert data["status"] == "user_not_found"


def test_send_coins_invalid_amount(authenticated_session):
    """Test transfer with invalid amounts."""
    # Test negative amount
    response = authenticated_session.post(
        "/api/transfer",
        json={"sender": "alice", "recipient": "bob", "amount": -100},
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["status"] == "invalid_amount"

    # Test zero amount
    response = authenticated_session.post(
        "/api/transfer",
        json={"sender": "alice", "recipient": "bob", "amount": 0},
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["status"] == "invalid_amount"


def test_self_transfer_blocked(authenticated_session):
    """Test that self-transfers are blocked."""
    response = authenticated_session.post(
        "/api/transfer",
        json={"sender": "alice", "recipient": "alice", "amount": 100},
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["status"] == "invalid_transfer"


def test_recent_transactions_display(authenticated_session, app):
    """Test that recent transactions are displayed correctly."""
    # Make a transfer first
    authenticated_session.post(
        "/api/transfer",
        json={"sender": "alice", "recipient": "bob", "amount": 500},
        headers={"Content-Type": "application/json"},
    )

    # Check home page shows the transaction
    response = authenticated_session.get("/")
    assert response.status_code == 200
    assert b"Your Recent Transactions" in response.data
    assert b"Sent to bob" in response.data
    assert b"-500" in response.data


def test_unauthenticated_user_no_send_coins(client):
    """Test that unauthenticated users don't see send coins feature."""
    # Try to access home page without authentication
    response = client.get("/")

    # Should redirect to register page
    assert response.status_code == 302
    assert "/register" in response.location


def test_quick_send_amounts_present(authenticated_session):
    """Test that quick send buttons are present with correct amounts."""
    response = authenticated_session.get("/")
    assert response.status_code == 200

    # Check quick send buttons
    assert b'data-amount="100"' in response.data
    assert b'data-amount="500"' in response.data
    assert b'data-amount="1000"' in response.data
    assert b"100 coins" in response.data
    assert b"500 coins" in response.data
    assert b"1,000 coins" in response.data


def test_market_stats_still_displayed(authenticated_session):
    """Test that market stats are still displayed with send coins feature."""
    response = authenticated_session.get("/")
    assert response.status_code == 200

    # Check that market stats are still present
    assert b"Market Cap" in response.data
    assert b"Active Stakeholders" in response.data
    assert b"Trading Volume" in response.data
    assert b"Market Leaders" in response.data
