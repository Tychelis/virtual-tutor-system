from models.user import db
from app import create_app

# Create the Flask application instance
app = create_app()

# Create all database tables within the application context
with app.app_context():
    db.create_all()  # Initialize database tables based on defined models
    print("Database initialized.")
