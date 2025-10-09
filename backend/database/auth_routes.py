# backend/auth_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    jwt_required, get_jwt_identity, get_jwt
)
from database.db_config import get_mysql_connection
from database.models import User
from datetime import datetime, timedelta
import logging
import re

auth_bp = Blueprint('auth', _name_)
logger = logging.getLogger(_name_)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, "Valid"

def log_auth_action(user_id, action, success=True):
    """Log authentication actions for security audit"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        cursor.execute("""
            INSERT INTO auth_audit_log (user_id, action, ip_address, user_agent, success)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, action, ip_address, user_agent, success))
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to log auth action: {e}")

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        
        # Validation
        if not username or not email or not password:
            return jsonify({
                'success': False,
                'error': 'Username, email, and password are required'
            }), 400
        
        if len(username) < 3:
            return jsonify({
                'success': False,
                'error': 'Username must be at least 3 characters'
            }), 400
        
        if not validate_email(email):
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400
        
        is_valid, msg = validate_password(password)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': msg
            }), 400
        
        # Check if user exists
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT user_id FROM users WHERE username = %s OR email = %s", 
                      (username, email))
        existing_user = cursor.fetchone()
        
        if existing_user:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Username or email already exists'
            }), 409
        
        # Create new user
        password_hash = User.hash_password(password)
        
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, full_name, role)
            VALUES (%s, %s, %s, %s, 'user')
        """, (username, email, password_hash, full_name))
        
        user_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        # Log registration
        log_auth_action(user_id, 'REGISTER', True)
        
        logger.info(f"New user registered: {username}")
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'user': {
                'user_id': user_id,
                'username': username,
                'email': email,
                'full_name': full_name
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({
            'success': False,
            'error': 'Registration failed'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        username_or_email = data.get('username', '').strip().lower()
        password = data.get('password', '')
        
        if not username_or_email or not password:
            return jsonify({
                'success': False,
                'error': 'Username/email and password are required'
            }), 400
        
        # Find user
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT user_id, username, email, password_hash, full_name, role, is_active
            FROM users 
            WHERE (username = %s OR email = %s) AND is_active = TRUE
        """, (username_or_email, username_or_email))
        
        user_data = cursor.fetchone()
        
        if not user_data:
            log_auth_action(None, 'LOGIN_FAILED', False)
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Invalid credentials'
            }), 401
        
        # Verify password
        if not User.verify_password(user_data['password_hash'], password):
            log_auth_action(user_data['user_id'], 'LOGIN_FAILED', False)
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Invalid credentials'
            }), 401
        
        # Update last login
        cursor.execute("""
            UPDATE users SET last_login = NOW() WHERE user_id = %s
        """, (user_data['user_id'],))
        conn.commit()
        cursor.close()
        conn.close()
        
        # Create JWT tokens
        access_token = create_access_token(
            identity=user_data['user_id'],
            additional_claims={
                'username': user_data['username'],
                'role': user_data['role']
            }
        )
        
        refresh_token = create_refresh_token(identity=user_data['user_id'])
        
        # Log successful login
        log_auth_action(user_data['user_id'], 'LOGIN', True)
        
        logger.info(f"User logged in: {user_data['username']}")
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'user_id': user_data['user_id'],
                'username': user_data['username'],
                'email': user_data['email'],
                'full_name': user_data['full_name'],
                'role': user_data['role']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            'success': False,
            'error': 'Login failed'
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token"""
    try:
        user_id = get_jwt_identity()
        
        # Get user info
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT username, role FROM users WHERE user_id = %s AND is_active = TRUE
        """, (user_id,))
        
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user_data:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Create new access token
        access_token = create_access_token(
            identity=user_id,
            additional_claims={
                'username': user_data['username'],
                'role': user_data['role']
            }
        )
        
        return jsonify({
            'success': True,
            'access_token': access_token
        }), 200
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({
            'success': False,
            'error': 'Token refresh failed'
        }), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info"""
    try:
        user_id = get_jwt_identity()
        
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT user_id, username, email, full_name, role, created_at, last_login
            FROM users 
            WHERE user_id = %s AND is_active = TRUE
        """, (user_id,))
        
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user_data:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        return jsonify({
            'success': True,
            'user': user_data
        }), 200
        
    except Exception as e:
        logger.error(f"Get user error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get user info'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout endpoint (client should delete tokens)"""
    try:
        user_id = get_jwt_identity()
        log_auth_action(user_id, 'LOGOUT', True)
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({
            'success': False,
            'error': 'Logout failed'
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({
                'success': False,
                'error': 'Current and new password are required'
            }), 400
        
        # Validate new password
        is_valid, msg = validate_password(new_password)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': msg
            }), 400
        
        # Verify current password
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT password_hash FROM users WHERE user_id = %s
        """, (user_id,))
        
        user_data = cursor.fetchone()
        
        if not user_data or not User.verify_password(user_data['password_hash'], current_password):
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Current password is incorrect'
            }), 401
        
        # Update password
        new_password_hash = User.hash_password(new_password)
        
        cursor.execute("""
            UPDATE users SET password_hash = %s WHERE user_id = %s
        """, (new_password_hash, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        log_auth_action(user_id, 'PASSWORD_CHANGE', True)
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Change password error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to change password'
        }), 500