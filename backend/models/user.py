from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# User table: stores account credentials, roles, and status
class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)  # Primary key
    email = db.Column(db.String(80), unique=True, nullable=False)  # User email (unique)
    password_hash = db.Column(db.String(128), nullable=False)  # Hashed password
    role = db.Column(db.String(20), nullable=False, default="student")  # User role: "student", "tutor", etc.
    status = db.Column(db.String(20), default="inactive")  # Account status
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Account creation timestamp
    last_login = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Last login timestamp

    # Relationships
    sessions = db.relationship('Session', backref='user', cascade='all, delete-orphan')  # User's sessions
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')  # One-to-one profile
    notifications = db.relationship('Notification', backref='user', cascade='all, delete-orphan')  # User notifications

    # Password management
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)  # Hash and store password

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)  # Verify password


# UserProfile table: stores personal information for a user
class UserProfile(db.Model):
    __tablename__ = 'user_profile'

    id = db.Column(db.Integer, primary_key=True)  # Primary key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)  # Linked to User table
    username = db.Column(db.String(50))  # Display username
    full_name = db.Column(db.String(50))  # Full legal name
    bio = db.Column(db.Text)  # Personal biography
    avatar_url = db.Column(db.String(200))  # Profile picture URL
    phone = db.Column(db.String(20))  # Contact phone number
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Creation timestamp
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Last update timestamp
    # gender = db.Column(db.String(10))
    # birthdate = db.Column(db.Date)
    # location = db.Column(db.String(100))


# UserActionLog table: stores logs of administrative actions taken on users
class UserActionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Primary key
    operator_email = db.Column(db.String(120), nullable=False)  # Email of the person performing the action
    role = db.Column(db.String(120), nullable=False)  # Role of the operator
    action = db.Column(db.String(20), nullable=False)  # Action type: "update", "delete"

    target_user_id = db.Column(db.Integer, nullable=False)  # ID of the affected user
    target_user_email = db.Column(db.String(120))  # Email of the affected user

    reason = db.Column(db.Text)  # Reason for the action (for delete)
    details = db.Column(db.JSON)  # Details of changes (for update)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Action timestamp


# Safeguard table: stores safety classification logs for guardrail checks
class Safeguard(db.Model):
    __tablename__ = 'safeguard'

    id = db.Column(db.Integer, primary_key=True)  # Primary key
    user_id = db.Column(db.Integer, nullable=False)  # ID of the user who made the request
    username = db.Column(db.String(50))  # Username of the user
    guardrail = db.Column(db.Text)  # Content safety classification and original input
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Log timestamp
