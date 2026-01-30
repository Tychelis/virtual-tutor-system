#!/usr/bin/env python3
"""
Test script for file upload functionality
Direct test without going through registration/login flow
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import requests
import json
from io import BytesIO

# Configuration
BASE_URL = "http://localhost:8203/api"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "password123"

def create_test_user_and_token():
    """Create test user directly in database and generate JWT token"""
    print("\n[0] Creating test user and generating token...")
    
    try:
        from app import create_app
        from models.user import User, UserProfile, db
        from flask_jwt_extended import create_access_token, get_jti
        from services.redis_client import redis_client
        
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
                    bio="Test user for file upload testing"
                )
                db.session.add(profile)
                db.session.commit()
                print(f"✅ Test user created: {TEST_USER_EMAIL}")
            else:
                print(f"ℹ️  Test user already exists: {TEST_USER_EMAIL}")
            
            # Generate JWT token
            token = create_access_token(identity=TEST_USER_EMAIL)
            
            # Store token in Redis (required for validation)
            jti = get_jti(token)
            redis_client.setex(f"token:{jti}", 18000, "valid")  # 5 hours TTL
            
            print(f"✅ JWT token generated and stored in Redis")
            print(f"   Token: {token[:30]}...")
            return token
            
    except Exception as e:
        print(f"❌ Error creating user/token: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_file_upload():
    """Test the file upload endpoint"""
    print("=" * 60)
    print("Testing File Upload Functionality")
    print("=" * 60)
    
    # Step 1: Create test user and get token (bypassing login)
    token = create_test_user_and_token()
    
    if not token:
        print("❌ Cannot proceed without token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Create a test file
    print("\n[2] Creating test file...")
    test_file_content = b"This is a test PDF file content."
    test_file = BytesIO(test_file_content)
    test_file.name = "test_document.pdf"
    
    files = {'file': ('test_document.pdf', test_file, 'application/pdf')}
    data = {'session_id': ''}  # Empty for new session
    
    # Step 3: Upload the file
    print("\n[3] Uploading file...")
    upload_response = requests.post(
        f"{BASE_URL}/chat/upload",
        headers=headers,
        files=files,
        data=data
    )
    
    print(f"Status Code: {upload_response.status_code}")
    print(f"Response: {json.dumps(upload_response.json(), indent=2)}")
    
    if upload_response.status_code == 200:
        print("✅ File upload successful!")
        upload_data = upload_response.json()
        session_id = upload_data.get("session_id")
        
        # Step 4: Get user files
        print("\n[4] Getting user files list...")
        files_response = requests.get(
            f"{BASE_URL}/user_files",
            headers=headers
        )
        
        print(f"Status Code: {files_response.status_code}")
        print(f"Response: {json.dumps(files_response.json(), indent=2)}")
        
        if files_response.status_code == 200:
            print("✅ Successfully retrieved user files!")
        else:
            print(f"❌ Failed to retrieve user files")
    else:
        print(f"❌ File upload failed!")
        print(f"Error: {upload_response.text}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_file_upload()
