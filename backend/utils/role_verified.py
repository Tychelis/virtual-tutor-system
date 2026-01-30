from functools import wraps
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from flask import jsonify

def role_required(required_role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            role = get_jwt().get("role")
            if role != required_role:
                return jsonify(msg=f"Access restricted to {required_role}"), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

