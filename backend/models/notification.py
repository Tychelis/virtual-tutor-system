from .user import db
from datetime import datetime

# Notification table: stores system/user notifications
class Notification(db.Model):
    __tablename__ = 'notification'

    id = db.Column(db.Integer, primary_key=True)  # Primary key
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE'),  # Notification belongs to a user; delete if user is deleted
        nullable=False
    )
    title = db.Column(db.Text, nullable=False)  # Short notification title
    message = db.Column(db.Text, nullable=False)  # Detailed notification content
    type = db.Column(db.String(20), default='info')  # Notification type: 'info', 'warning', 'alert'
    is_read = db.Column(db.Boolean, default=False)  # Whether the notification has been read
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp of creation
