import time
import random

# In-memory store for verification codes
# Structure: { email: { "code": str, "timestamp": float, "last_sent": float } }
_verification_store = {}


def generate_code():
    """Generate a 6-digit numeric verification code as a string."""
    return f"{random.randint(100000, 999999)}"


def can_send_code(email):
    """
    Check if a verification code can be sent to this email.
    Rate limit: 10 seconds between sends.
    """
    entry = _verification_store.get(email)
    if entry is None:
        return True
    return time.time() - entry["last_sent"] >= 10


def store_code(email, code):
    """Store the verification code and timestamps for an email."""
    _verification_store[email] = {
        "code": code,
        "timestamp": time.time(),   # When the code was generated
        "last_sent": time.time()    # When the code was last sent
    }


def verify_code(email, user_code):
    """
    Verify if the provided code matches and is not expired.
    Expiry: 5 minutes (300 seconds).
    """
    entry = _verification_store.get(email)
    if not entry:
        return False
    if time.time() - entry["timestamp"] > 300:
        return False
    return entry["code"] == user_code


def delete_code(email):
    """Delete the verification code entry for an email."""
    _verification_store.pop(email, None)
