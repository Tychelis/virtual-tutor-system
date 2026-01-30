from flask_jwt_extended import get_jwt_identity, get_jwt, verify_jwt_in_request
from services.redis_client import redis_client
from flask import jsonify
from functools import wraps
from config import Config

def refresh_redis_only(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        jti = get_jwt()["jti"]
        user_id = get_jwt_identity()

        if not redis_client.exists(f"token:{jti}"):
            return jsonify(msg="Session expired. Please login again."), 401

        redis_client.expire(f"token:{jti}", Config.REDIS_TOKEN_TTL_SECONDS)
        redis_client.expire(f"user_token:{user_id}", Config.REDIS_TOKEN_TTL_SECONDS)

        return fn(*args, **kwargs)
    return wrapper
