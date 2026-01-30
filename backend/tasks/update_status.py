#!/usr/bin/env /home/xinghua/workspace/share/conda/envs/bowen/bin/python3

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from services.redis_client import redis_client
from models.user import User, db

# Create Flask app for DB context
app = create_app()

def update_inactive_users():
    """Set users to 'inactive' if they have no active JWT in Redis."""
    with app.app_context():
        # Query all users currently marked as active
        users = User.query.filter(User.status == "active").all()
        for user in users:
            # If no token JTI is stored for this user, mark as inactive
            if not redis_client.get(f"user_token:{user.id}"):
                user.status = "inactive"
        db.session.commit()  # Persist changes

if __name__ == "__main__":
    update_inactive_users()
    print("Inactive users updated.")
