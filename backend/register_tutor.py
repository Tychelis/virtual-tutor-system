from getpass import getpass
from app import create_app
from models.user import User, UserProfile, db
from datetime import datetime

# Create Flask app instance for DB context
app = create_app()

def main():
    """CLI tool to register a new tutor account with profile."""
    with app.app_context():
        # Get tutor email
        email = input("Enter tutor email: ").strip()
        if User.query.filter_by(email=email).first():
            print("User already exists.")
            return

        # Prompt for password (hidden input)
        password = getpass("Enter password: ").strip()
        confirm = getpass("Confirm password: ").strip()
        if password != confirm:
            print("Passwords do not match.")
            return

        # Create User object (tutor role, inactive by default)
        user = User(
            email=email,
            role="tutor",
            status="inactive",
            created_at=datetime.utcnow(),
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # Ensure user.id is available for profile FK

        # Create associated UserProfile
        profile = UserProfile(
            user_id=user.id,
            username=email.split("@")[0],
            full_name="",
            phone="",
            avatar_url="/workspace/bowen/static/avatars/default.jpg",
            bio=""
        )
        db.session.add(profile)
        db.session.commit()

        print(f"Tutor registered: {email} with profile {profile.username}")

if __name__ == "__main__":
    main()
