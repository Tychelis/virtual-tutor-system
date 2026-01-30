#!/usr/bin/env python3
"""
Generate Test Token Helper Script

This script creates a test user and generates a JWT token.
Run this ONCE in the bread conda environment, then you can run 
other tests in any Python environment using the saved token.

Usage:
    conda activate bread
    python test/generate_test_token.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from app import create_app
    from models.user import User, UserProfile, db
    from flask_jwt_extended import create_access_token, get_jti
    from services.redis_client import redis_client
    
    TEST_USER_EMAIL = "test@example.com"
    TEST_USER_PASSWORD = "password123"
    
    print("=" * 70)
    print("Generating Test Token")
    print("=" * 70)
    
    app = create_app()
    
    with app.app_context():
        # Check if user exists
        user = User.query.filter_by(email=TEST_USER_EMAIL).first()
        
        if not user:
            # Create user
            user = User(email=TEST_USER_EMAIL, role="student", status="active")
            user.set_password(TEST_USER_PASSWORD)
            db.session.add(user)
            
            # Create profile
            profile = UserProfile(
                user=user,
                username="testuser",
                full_name="Test User",
                bio="Test user for integration testing"
            )
            db.session.add(profile)
            db.session.commit()
            print(f"✅ Test user created: {TEST_USER_EMAIL}")
        else:
            print(f"ℹ️  Test user already exists: {TEST_USER_EMAIL}")
        
        user_id = user.id
        
        # Generate JWT token
        token = create_access_token(identity=TEST_USER_EMAIL)
        
        # Store token in Redis (required for validation)
        jti = get_jti(token)
        redis_client.setex(f"token:{jti}", 18000, "valid")  # 5 hours TTL
        
        print(f"✅ JWT token generated and stored in Redis")
        print(f"\nUser ID: {user_id}")
        print(f"Token (valid for 5 hours):")
        print(f"{token}")
        
        # Save to file for other tests to use
        token_file = os.path.join(os.path.dirname(__file__), '.test_token')
        with open(token_file, 'w') as f:
            f.write(f"{token}\n{user_id}\n")
        
        print(f"\n✅ Token saved to: {token_file}")
        print(f"\nNow you can run other tests in any Python environment:")
        print(f"   python test/test_rag_integration.py")
        print("=" * 70)

except ModuleNotFoundError as e:
    print(f"❌ Error: {e}")
    print()
    print("This script must run in the 'bread' conda environment:")
    print("   conda activate bread")
    print("   python test/generate_test_token.py")
    sys.exit(1)
