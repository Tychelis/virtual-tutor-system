from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import db, User, UserProfile, UserActionLog
from sqlalchemy import or_
from datetime import datetime, timedelta

# Blueprint for admin-related routes
admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/users", methods=["GET"])
@jwt_required()
def get_user_list():
    """Retrieve paginated list of users with optional filters."""
    user_email = get_jwt_identity()
    admin_user = User.query.filter_by(email=user_email).first()

    # Permission check: only tutors can access
    if not admin_user or admin_user.role.lower() != "tutor":
        return jsonify({"msg": "Permission denied"}), 403

    # Query parameters
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    search = request.args.get("search", "")
    role_filter = request.args.get("role")
    status_filter = request.args.get("status")

    # Base query with join on profile for search
    query = User.query.join(UserProfile).order_by(User.created_at.desc())

    if search:
        query = query.filter(or_(
            User.email.ilike(f"%{search}%"),
            UserProfile.username.ilike(f"%{search}%"),
            UserProfile.full_name.ilike(f"%{search}%")
        ))

    if role_filter:
        query = query.filter(User.role == role_filter)
    if status_filter:
        query = query.filter(User.status == status_filter)

    total = query.count()
    users = query.offset((page - 1) * limit).limit(limit).all()

    def format_user(user):
        """Format user and profile data for JSON response."""
        profile = user.profile or UserProfile()
        return {
            "id": f"U{user.id:03d}",
            "email": user.email,
            "username": profile.username or "",
            "full_name": profile.full_name or "",
            "phone": profile.phone or "",
            "bio": profile.bio or "",
            "avatar": profile.avatar_url or "",
            "role": user.role,
            "status": user.status,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        }

    return jsonify({
        "users": [format_user(user) for user in users],
        "total": total,
        "page": page,
        "limit": limit
    }), 200


@admin_bp.route("/admin/users", methods=["POST"])
@jwt_required()
def create_user():
    """Create a new user with profile."""
    admin_email = get_jwt_identity()
    admin = User.query.filter_by(email=admin_email).first()

    # Only tutors can create users
    if not admin or admin.role.lower() != "tutor":
        return jsonify({"msg": "Permission denied"}), 403

    data = request.get_json()
    required_fields = ["email", "password", "username", "role"]
    if not all(field in data for field in required_fields):
        return jsonify({"msg": "Missing required fields"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"msg": "User already exists"}), 409

    # Create User
    new_user = User(
        email=data["email"],
        role=data.get("role", "student"),
        status="active"
    )
    new_user.set_password(data["password"])
    db.session.add(new_user)
    db.session.flush()  # Get ID before creating profile

    # Create UserProfile
    new_profile = UserProfile(
        user_id=new_user.id,
        username=data.get("username"),
        full_name=data.get("full_name", ""),
        phone=data.get("phone", ""),
        bio=data.get("bio", ""),
        avatar_url=data.get("avatar_url", "/workspace/bowen/static/avatars/default.jpg"),
    )

    db.session.add(new_profile)
    db.session.commit()

    return jsonify({
        "msg": "User created successfully",
        "user_id": f"{new_user.id:03d}"
    }), 201


@admin_bp.route("/admin/users/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_user(user_id):
    """Update user and profile info, log changes."""
    admin_email = get_jwt_identity()
    admin = User.query.filter_by(email=admin_email).first()

    if not admin or admin.role.lower() != "tutor":
        return jsonify({"msg": "Permission denied"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"msg": "Missing request data"}), 400

    if not user.profile:
        user.profile = UserProfile(user_id=user.id)

    # Track changes for logging
    changes = {}

    for field in ["role", "status"]:
        old, new = getattr(user, field), data.get(field, getattr(user, field))
        if old != new:
            changes[field] = [old, new]
            setattr(user, field, new)

    for field in ["username"]:
        old, new = getattr(user.profile, field), data.get(field, getattr(user.profile, field))
        if old != new:
            changes[field] = [old, new]
            setattr(user.profile, field, new)

    if changes:
        log = UserActionLog(
            operator_email=admin_email,
            role=admin.role,
            action="update",
            target_user_id=user.id,
            target_user_email=user.email,
            details=changes,
            timestamp=datetime.utcnow()
        )
        db.session.add(log)

    db.session.commit()
    return jsonify({"msg": "User updated successfully"}), 200


@admin_bp.route("/admin/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    """Delete a user and log the action."""
    admin_email = get_jwt_identity()
    admin = User.query.filter_by(email=admin_email).first()

    if not admin or admin.role.lower() != "tutor":
        return jsonify({"msg": "Permission denied"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    reason = request.json.get("reason", "") if request.is_json else ""
    log = UserActionLog(
        operator_email=admin_email,
        role=admin.role,
        action="delete",
        target_user_id=user.id,
        target_user_email=user.email,
        reason=reason,
        details={
            "role": user.role,
            "email": user.email,
            "full_name": user.profile.full_name if user.profile else None
        },
        timestamp=datetime.utcnow()
    )
    db.session.add(log)
    db.session.delete(user)
    db.session.commit()

    return jsonify({"msg": "User deleted successfully"}), 200


@admin_bp.route("/admin/models", methods=["GET"])
@jwt_required()
def get_models():
    """Return mock model list (demo purpose)."""
    admin_email = get_jwt_identity()
    admin = User.query.filter_by(email=admin_email).first()
    if not admin or admin.role.lower() != "tutor":
        return jsonify({"msg": "Permission denied"}), 403

    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))

    mock_models = [
        {"id": "M001", "name": "mistral-nemo:12b-instruct-2407-fp16", "type": "LLM", "status": "Active"},
        {"id": "M002", "name": "llama3.1:8b-instruct-q4_K_M", "type": "LLM", "status": "Inactive"}
    ]

    return jsonify({"models": mock_models, "total": len(mock_models), "page": page, "limit": limit}), 200


@admin_bp.route("/admin/knowledge", methods=["GET"])
@jwt_required()
def get_knowledge_list():
    """Return mock knowledge base list (demo purpose)."""
    admin_email = get_jwt_identity()
    admin = User.query.filter_by(email=admin_email).first()
    if not admin or admin.role.lower() != "tutor":
        return jsonify({"msg": "Permission denied"}), 403

    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))

    mock_knowledge = [
        {"id": "K001", "name": "Machine Learning Basics", "type": "Tutorial", "status": "Active",
         "tag_color": "green", "selected": True, "created_at": "2024-01-01T00:00:00Z"},
        {"id": "K002", "name": "Python Cheat Sheet", "type": "Reference", "status": "Active",
         "tag_color": "yellow", "selected": False, "created_at": "2024-02-01T00:00:00Z"}
    ]

    return jsonify({"knowledge": mock_knowledge, "total": len(mock_knowledge), "page": page, "limit": limit}), 200


@admin_bp.route("/admin/user-action-logs", methods=["GET"])
@jwt_required()
def get_user_action_logs():
    """Retrieve paginated list of user action logs."""
    admin_email = get_jwt_identity()
    admin = User.query.filter_by(email=admin_email).first()
    if not admin or admin.role.lower() != "tutor":
        return jsonify({"msg": "Permission denied"}), 403

    # Optional filters
    operator_email = request.args.get("operator_email")
    target_user_email = request.args.get("target_user_email")
    action = request.args.get("action")
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("per_page", 20, type=int)

    query = UserActionLog.query
    if operator_email:
        query = query.filter(UserActionLog.operator_email == operator_email)
    if target_user_email:
        query = query.filter(UserActionLog.target_user_email == target_user_email)
    if action:
        query = query.filter(UserActionLog.action == action)

    query = query.order_by(UserActionLog.timestamp.desc())
    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    logs = [{
        "id": log.id,
        "operator_email": log.operator_email,
        "action": log.action,
        "target_user_id": log.target_user_id,
        "target_user_email": log.target_user_email,
        "reason": log.reason,
        "details": log.details,
        "timestamp": log.timestamp.isoformat()
    } for log in pagination.items]

    return jsonify({"total": pagination.total, "page": page, "per_page": limit, "logs": logs}), 200
