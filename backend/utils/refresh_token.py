from flask_jwt_extended import get_jwt_identity, get_jwt, create_access_token, verify_jwt_in_request
from services.redis_client import redis_client
from flask import g, jsonify
from functools import wraps
from config import Config
from flask_jwt_extended.utils import decode_token


def refresh_token_and_redis(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        jti = get_jwt()["jti"]
        user_id = get_jwt_identity()

        if not redis_client.exists(f"token:{jti}"):
            return jsonify(msg="Session expired. Please login again."), 401

        # redis_client.expire(f"token:{jti}", Config.JWT_ACCESS_TOKEN_EXPIRES)
        # redis_client.expire(f"user:{user_id}", Config.JWT_ACCESS_TOKEN_EXPIRES)
        redis_client.delete(f"token:{jti}")
        redis_client.delete(f"user_token:{user_id}")

        new_token = create_access_token(identity=user_id, additional_claims={"role": get_jwt().get("role")})
        new_jti = decode_token(new_token)["jti"]
        g.new_token = new_token

        redis_client.setex(f"token:{new_jti}", Config.JWT_ACCESS_TOKEN_EXPIRES, user_id)
        redis_client.setex(f"user_token:{user_id}", Config.JWT_ACCESS_TOKEN_EXPIRES, new_jti)
        return fn(*args, **kwargs)
    return wrapper


