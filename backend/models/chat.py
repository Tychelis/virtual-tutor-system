from .user import db
from datetime import datetime

# Session table: stores conversation sessions for each user
class Session(db.Model):
    __tablename__ = 'session'

    id = db.Column(db.Integer, primary_key=True)  # Primary key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Owner of the session
    title = db.Column(db.String(120))  # Optional session title
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Creation timestamp
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Last update timestamp
    is_favorite = db.Column(db.Boolean, default=False)  # Mark as favorite
    message_count = db.Column(db.Integer, default=0)  # Number of messages in the session
    messages = db.relationship("Message", backref="session", cascade="all, delete-orphan")
    # Relationship to messages; deleting a session deletes all its messages


# Message table: stores individual messages in a session
class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True)  # Primary key
    session_id = db.Column(
        db.Integer,
        db.ForeignKey('session.id', ondelete='CASCADE'),  # Belongs to a session; delete if session is deleted
        nullable=False
    )
    role = db.Column(db.String(20), nullable=False)  # Message sender: "user" or "assistant"
    file_type = db.Column(db.String(20))  # Type of file attached (if any)
    file_path = db.Column(db.String(200))  # Path to the attached file
    content = db.Column(db.Text, nullable=True)  # Text content of the message
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp of message creation
