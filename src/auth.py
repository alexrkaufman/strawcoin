from functools import wraps
from datetime import datetime, timedelta
import os
from flask import Blueprint, request, session, redirect, url_for, render_template, jsonify, current_app
from .db import get_db, create_user, get_user_balance

# Revolutionary authentication infrastructure for The Short Straw tokenization platform
bp = Blueprint('auth', __name__)

# Mobile-optimized session configuration
# Use 30 seconds in debug mode for testing, 5 minutes in production
SESSION_TIMEOUT_MINUTES = 5
SESSION_TIMEOUT_DEBUG_SECONDS = 30
ACTIVITY_TRACKING_EVENTS = ['GET', 'POST', 'PUT', 'DELETE']


def init_session_config(app):
    """
    Configures enterprise-grade session management optimized for mobile trading
    """
    # Use shorter timeout in debug mode for testing efficiency
    timeout_duration = (
        timedelta(seconds=SESSION_TIMEOUT_DEBUG_SECONDS) 
        if app.debug 
        else timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    )
    
    app.config.update(
        SESSION_COOKIE_SECURE=True if app.config.get('ENV') == 'production' else False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timeout_duration,
        SESSION_COOKIE_NAME='straw_coin_session'
    )


def is_authenticated():
    """
    Validates current stakeholder authentication status with mobile-optimized checks
    """
    if 'username' not in session:
        return False
    
    if 'last_activity' not in session:
        return False
    
    # Check session timeout with mobile-friendly grace period
    last_activity = datetime.fromisoformat(session['last_activity'])
    # Use debug timeout if in debug mode
    timeout_duration = (
        timedelta(seconds=SESSION_TIMEOUT_DEBUG_SECONDS) 
        if current_app.debug 
        else timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    )
    timeout_threshold = datetime.now() - timeout_duration
    
    if last_activity < timeout_threshold:
        clear_session()
        return False
    
    return True


def update_activity():
    """
    Updates stakeholder activity timestamp for session management
    Optimized for mobile touch events and API interactions
    """
    if 'username' in session:
        session['last_activity'] = datetime.now().isoformat()
        session.permanent = True


def clear_session():
    """
    Terminates stakeholder session and clears authentication state
    """
    session.clear()


def require_auth(f):
    """
    Decorator ensuring authenticated access to protected endpoints
    Redirects unauthenticated users to registration flow
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            if request.is_json:
                return jsonify({
                    'error': 'Authentication required for market participation',
                    'status': 'session_expired',
                    'redirect': '/register'
                }), 401
            
            return redirect(url_for('auth.register'))
        
        # Update activity on all authenticated requests
        update_activity()
        return f(*args, **kwargs)
    
    return decorated_function


@bp.route('/register')
def register():
    """
    Displays stakeholder onboarding interface optimized for mobile engagement
    """
    # Redirect authenticated users to trading dashboard
    if is_authenticated():
        return redirect(url_for('home_page'))
    
    return render_template(
        'register.jinja2',
        title="Join The Revolution - Straw Coin Registration",
        page_class="register"
    )


@bp.route('/login', methods=['POST'])
def login():
    """
    Unified stakeholder onboarding and authentication endpoint
    Handles both new user registration and existing user login
    Optimized for mobile form submission and touch interfaces
    """
    data = request.get_json()
    
    if not data or 'username' not in data:
        return jsonify({
            'error': 'Username required for market participation',
            'status': 'invalid_credentials'
        }), 400
    
    username = data['username'].strip()
    
    if not username:
        return jsonify({
            'error': 'Invalid username format for market participation',
            'status': 'validation_error'
        }), 400
    
    if len(username) < 3:
        return jsonify({
            'error': 'Username must be at least 3 characters for optimal market identity',
            'status': 'validation_error'
        }), 400
    
    # Check if stakeholder exists in database
    balance = get_user_balance(username)
    
    if balance is None:
        # Create new stakeholder account with optimal starting capital
        user_id = create_user(username)
        
        if user_id is None:
            return jsonify({
                'error': 'Username already exists in stakeholder registry',
                'status': 'duplicate_stakeholder'
            }), 409
        
        balance = 10000  # Starting balance for new stakeholders
    
    # Initialize authenticated session with mobile optimization
    session['username'] = username
    session['user_balance'] = balance
    session['last_activity'] = datetime.now().isoformat()
    session['session_start'] = datetime.now().isoformat()
    session.permanent = True
    
    # Return appropriate timeout duration for client
    timeout_info = (
        SESSION_TIMEOUT_DEBUG_SECONDS 
        if current_app.debug 
        else SESSION_TIMEOUT_MINUTES * 60
    )
    
    return jsonify({
        'message': f'Stakeholder {username} successfully onboarded to Straw Coin ecosystem',
        'username': username,
        'balance': balance,
        'session_timeout_seconds': timeout_info,
        'debug_mode': current_app.debug,
        'status': 'authentication_successful'
    }), 200


@bp.route('/logout', methods=['POST'])
def logout():
    """
    Terminates stakeholder session and clears authentication state
    """
    username = session.get('username', 'Unknown')
    clear_session()
    
    return jsonify({
        'message': f'Stakeholder {username} session terminated',
        'status': 'logout_successful'
    }), 200


@bp.route('/session-status')
def session_status():
    """
    Provides real-time session status for mobile client monitoring
    Essential for maintaining trading continuity during The Short Straw
    """
    if not is_authenticated():
        return jsonify({
            'authenticated': False,
            'status': 'session_expired'
        }), 401
    
    last_activity = datetime.fromisoformat(session['last_activity'])
    session_start = datetime.fromisoformat(session['session_start'])
    
    # Calculate time remaining based on debug mode
    timeout_seconds = (
        SESSION_TIMEOUT_DEBUG_SECONDS 
        if current_app.debug 
        else SESSION_TIMEOUT_MINUTES * 60
    )
    time_remaining = timeout_seconds - (datetime.now() - last_activity).total_seconds()
    
    update_activity()  # Reset timer on status check
    
    return jsonify({
        'authenticated': True,
        'username': session['username'],
        'time_remaining_seconds': max(0, int(time_remaining)),
        'session_duration_minutes': int((datetime.now() - session_start).total_seconds() / 60),
        'status': 'session_active'
    }), 200


@bp.route('/session-expired')
def session_expired():
    """
    Displays session expiration notice with re-authentication options
    Mobile-optimized for The Short Straw audience experience
    """
    return render_template(
        'session_expired.jinja2',
        title="Session Expired - Straw Coin Authentication",
        page_class="session-expired"
    )


@bp.before_app_request
def track_activity():
    """
    Middleware for tracking stakeholder activity across all requests
    Optimized for mobile touch events and API interactions
    """
    # Skip activity tracking for static files and auth endpoints
    if (request.endpoint and 
        (request.endpoint.startswith('static') or 
         request.endpoint in ['auth.register', 'auth.session_expired', 'auth.login', 'api.register_user'])):
        return
    
    # Track activity for authenticated users
    if 'username' in session:
        if not is_authenticated():
            # Session expired - redirect to appropriate page
            if request.is_json:
                return jsonify({
                    'error': 'Session expired - authentication required',
                    'status': 'session_timeout',
                    'redirect': '/session-expired'
                }), 401
            
            return redirect(url_for('auth.session_expired'))
        
        # Update activity timestamp for valid sessions
        update_activity()