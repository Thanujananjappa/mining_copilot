# backend/database/models.py
from datetime import datetime
from flask_bcrypt import generate_password_hash, check_password_hash

class User:
    """User model for authentication"""
    
    def __init__(self, user_id=None, username=None, email=None, password_hash=None, 
                 full_name=None, role='user', created_at=None, last_login=None):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.full_name = full_name
        self.role = role
        self.created_at = created_at or datetime.utcnow()
        self.last_login = last_login
    
    @staticmethod
    def hash_password(password):
        """Hash a password for storing"""
        return generate_password_hash(password).decode('utf-8')
    
    @staticmethod
    def verify_password(password_hash, password):
        """Verify a stored password against one provided by user"""
        return check_password_hash(password_hash, password)
    
    def to_dict(self):
        """Convert user object to dictionary (excluding password)"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }