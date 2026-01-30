from flask_jwt_extended import get_jwt, verify_jwt_in_request
from functools import wraps
from flask import jsonify
from services.redis_client import redis_client

def token_in_redis_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        token = get_jwt()["jti"]
        if not redis_client.exists(f"token:{token}"):
            return jsonify(msg="Token is invalid or expired."), 401
        return fn(*args, **kwargs)
    return wrapper
