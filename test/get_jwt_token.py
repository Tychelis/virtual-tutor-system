#!/usr/bin/env python3
"""
JWT Token Retrieval Tool
Used to login to the system and obtain JWT token for latency testing

By default, uses configured account for automatic login
Use --interactive parameter for manual account input
"""

import requests
import json
import sys
import os

def get_jwt_token(email, password, backend_url="http://localhost:8203"):
    """
    Login with email and password to obtain JWT token
    
    Args:
        email: User email
        password: User password
        backend_url: Backend service URL
    
    Returns:
        str: JWT token, returns None if failed
    """
    print(f" Logging in...")
    print(f"   Email: {email}")
    print(f"   Backend: {backend_url}")
    
    try:
        # Send login request
        response = requests.post(
            f"{backend_url}/api/login",
            json={
                "email": email,
                "password": password
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            
            if token:
                print(f"\n Login successful!")
                print(f"\n JWT Token:")
                print(f"{'='*70}")
                print(token)
                print(f"{'='*70}")
                
                # Save to file
                token_file = os.path.join(os.path.dirname(__file__), '.jwt_token')
                with open(token_file, 'w') as f:
                    f.write(token)
                
                print(f"\n Token saved to: {token_file}")
                print(f"   (Can be automatically read during testing)")
                
                # Display token info
                print_token_info(token, backend_url)
                
                return token
            else:
                print(f"\n Login failed: No token in response")
                return None
                
        elif response.status_code == 401:
            print(f"\n Login failed: Incorrect email or password")
            return None
        else:
            print(f"\n Login failed: HTTP {response.status_code}")
            print(f"   {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"\n Connection failed: Cannot connect to Backend service")
        print(f"   Please ensure Backend service is running: {backend_url}")
        return None
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def print_token_info(token, backend_url):
    """Display token information"""
    print(f"\n Token Information:")
    
    # Try to get token status
    try:
        response = requests.get(
            f"{backend_url}/api/token_status",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Valid for: {data.get('expires_in_minutes', 'N/A')} minutes")
            print(f"   Remaining: {data.get('expires_in_seconds', 'N/A')} seconds")
        else:
            print(f"   Unable to retrieve token status")
    except:
        pass


def load_saved_token():
    """Load saved token"""
    token_file = os.path.join(os.path.dirname(__file__), '.jwt_token')
    
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            token = f.read().strip()
        
        if token:
            print(f" Found saved token")
            return token
    
    return None


def interactive_login():
    """Interactive login"""
    print("\n" + "="*70)
    print("   JWT Token Retrieval Tool")
    print("="*70)
    
    # Check if there's a saved token
    saved_token = load_saved_token()
    if saved_token:
        print(f"\n Found saved token")
        use_saved = input("   Use saved token? (Y/n): ").strip().lower()
        
        if use_saved != 'n':
            print(f"\n Using saved token:")
            print(f"{'='*70}")
            print(saved_token)
            print(f"{'='*70}")
            return saved_token
    
    print(f"\nPlease enter login information:")
    
    # Get user input
    email = input("  Email: ").strip()
    if not email:
        print(" Email cannot be empty")
        return None
    
    import getpass
    try:
        password = getpass.getpass("  Password: ")
    except:
        # If getpass is not available (some environments), use regular input
        password = input("  Password: ")
    
    if not password:
        print(" Password cannot be empty")
        return None
    
    # Backend URL (optional)
    print(f"\n  Backend URL [default: http://localhost:8203]:")
    backend_url = input("  ").strip() or "http://localhost:8203"
    
    print()
    
    # Login to get token
    return get_jwt_token(email, password, backend_url)


def main():
    """Main function"""
    # Default account configuration
    DEFAULT_EMAIL = "z5519138@ad.unsw.edu.au"
    DEFAULT_PASSWORD = "Xwl010907!"
    DEFAULT_BACKEND_URL = "http://localhost:8203"
    
    # If command line arguments are provided
    if len(sys.argv) >= 2:
        if sys.argv[1] == "--interactive":
            # Force interactive input
            token = interactive_login()
        else:
            # Use command line arguments
            email = sys.argv[1]
            password = sys.argv[2] if len(sys.argv) >= 3 else DEFAULT_PASSWORD
            backend_url = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_BACKEND_URL
            
            token = get_jwt_token(email, password, backend_url)
    else:
        # Use default account for automatic login
        print(f"   Using default account: {DEFAULT_EMAIL}")
        print(f"   Tip: Use --interactive parameter for manual account input\n")
        
        token = get_jwt_token(DEFAULT_EMAIL, DEFAULT_PASSWORD, DEFAULT_BACKEND_URL)
    
    if token:
        print(f"\n Usage Tips:")
        print(f"   1. Token saved to .jwt_token file")
        print(f"   2. Will be automatically read during latency tests")
        print(f"\n   Run tests directly:")
        print(f"   python test_e2e_latency.py")
        print(f"   python test_avatar_video_latency.py")
        print(f"\n   Environment variable method:")
        print(f"   export JWT_TOKEN=$(cat latency_tests/.jwt_token)")
        print(f"\n" + "="*70 + "\n")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n Cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

