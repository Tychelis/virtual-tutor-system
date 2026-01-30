from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, get_jwt, jwt_required, get_jti, get_jwt_identity
from models.user import User, db, UserProfile, UserActionLog
from datetime import datetime, timezone
from services.email_service import send_verification_email
from services.verification_cache import generate_code, store_code, can_send_code, verify_code, delete_code
from services.redis_client import redis_client
from utils.token_utils import token_in_redis_required

# Blueprint for authentication-related routes
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user, create and store JWT in Redis."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify(msg="Invalid credentials"), 401

    # Invalidate old token if exists
    old_token_key = f"user_token:{user.id}"
    old_token_jti = redis_client.get(old_token_key)
    if old_token_jti:
        redis_client.delete(f"token:{old_token_jti}")
        redis_client.delete(old_token_key)

    # Create new access token with role claim
    access_token = create_access_token(identity=user.email, additional_claims={"role": user.role})
    from flask_jwt_extended.utils import decode_token
    jti = decode_token(access_token)["jti"]

    # Store token in Redis with TTL
    ttl = current_app.config["REDIS_TOKEN_TTL_SECONDS"]
    redis_client.setex(f"token:{jti}", ttl, user.email)
    redis_client.setex(f"user_token:{user.id}", ttl, jti)

    # Store optional session ID for tracking
    session_id = request.headers.get("sessionid") or request.json.get("sessionid")
    if session_id:
        redis_client.setex(f"sessionid:{user.id}", ttl, session_id)

    # Update user status and last login
    user.status = "active"
    user.last_login = datetime.utcnow()
    db.session.commit()

    return jsonify(token=access_token), 200


@auth_bp.route('/token_status', methods=['GET'])
@jwt_required()
@token_in_redis_required
def token_status():
    """Return remaining lifetime of the current JWT."""
    jwt_data = get_jwt()
    exp_timestamp = jwt_data["exp"]
    now = datetime.now(timezone.utc).timestamp()
    remaining = int(exp_timestamp - now)

    return jsonify({
        "expires_in_seconds": max(0, remaining),
        "expires_in_minutes": round(max(0, remaining) / 60, 2)
    })


@auth_bp.route("/send_verification", methods=["POST"])
def send_code():
    """Send a verification code via email."""
    data = request.get_json()
    email = data.get("email")
    purpose = data.get("purpose")

    if not email:
        return jsonify({"msg": "Email required"}), 400

    # Prevent duplicate registration
    if purpose == "register" and User.query.filter_by(email=email).first():
        return jsonify({"msg": "This email is already registered."}), 409

    # Throttle requests
    if not can_send_code(email):
        return jsonify({"msg": "Please wait 10 seconds before requesting again"}), 429

    # Generate and send code
    code = generate_code()
    store_code(email, code)
    send_verification_email(email, code)
    return jsonify({"msg": "Verification code sent."}), 200


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user after verifying code."""
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    code = data.get("code")
    role = data.get("role", "student")

    if not all([email, password, code]):
        return jsonify({"msg": "Missing fields"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "This email is already registered."}), 409

    if not verify_code(email, code):
        return jsonify({"msg": "Invalid or expired verification code."}), 401

    delete_code(email)

    # Create User and Profile
    user = User(email=email, role=role)
    user.set_password(password)
    db.session.add(user)

    profile = UserProfile(
        user=user,
        username=email.split("@")[0],
        full_name="",
        bio="",
        avatar_url="/workspace/bowen/static/avatars/default.jpg",
        phone=''
    )
    db.session.add(profile)
    db.session.commit()

    return jsonify({"msg": "Registration successful"}), 201


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Invalidate current JWT and set user status to inactive."""
    token = get_jwt()["jti"]
    redis_client.delete(f"token:{token}")
    user_email = get_jwt_identity()

    user = User.query.filter_by(email=user_email).first()
    if user:
        user.status = "inactive"
        db.session.commit()

    return jsonify(msg="Logged out successfully."), 200


@auth_bp.route("/update_password", methods=["POST"])
@jwt_required()
def update_password():
    """Update user password after verifying code."""
    user_email = get_jwt_identity()
    data = request.get_json()
    code = data.get("code")
    new_password = data.get("new_password")

    if not all([user_email, code, new_password]):
        return jsonify({"msg": "Missing required fields"}), 400

    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    if not verify_code(user_email, code):
        return jsonify({"msg": "Invalid or expired verification code"}), 400

    # Update password
    user.set_password(new_password)

    # Log password change
    log = UserActionLog(
        operator_email=user_email,
        action="update",
        role=user.role,
        target_user_id=user.id,
        target_user_email=user.email,
        details={"password": "<changed>"},
        timestamp=datetime.utcnow()
    )
    db.session.add(log)

    delete_code(user_email)
    db.session.commit()

    return jsonify({"msg": "Password updated successfully"}), 200
