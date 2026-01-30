import os
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from models.user import User, db, UserProfile, UserActionLog
from models.notification import Notification
from sqlalchemy import desc
from datetime import datetime
from services.verification_cache import generate_code, store_code, can_send_code, verify_code, delete_code

# Blueprint for user profile and notification management
user_bp = Blueprint("user", __name__)

ALLOWED_IMAGE = {"png", "jpg", "jpeg"}


def allowed_file(filename):
    """Check if uploaded file has an allowed image extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE


@user_bp.route("/user/profile", methods=["GET"])
@jwt_required()
def get_user_info():
    """Retrieve the current user's profile information."""
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()

    if not user or not user.profile:
        return jsonify({"msg": "User or profile not found"}), 404

    return jsonify({
        "email": user.email,
        "username": user.profile.username,
        "full_name": user.profile.full_name,
        "avatar_url": user.profile.avatar_url,
        "bio": user.profile.bio,
        "role": user.role
    }), 200


@user_bp.route("/user/profile", methods=["POST"])
@jwt_required()
def update_user_info():
    """Update the current user's profile information and log changes."""
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()

    if not user or not user.profile:
        return jsonify({"msg": "User or profile not found"}), 404

    data = request.get_json()
    changes = {}

    for field in ["username", "full_name", "phone", "bio"]:
        old = getattr(user.profile, field)
        new = data.get(field, old)
        if old != new:
            changes[field] = [old, new]
            setattr(user.profile, field, new)

    if changes:
        log = UserActionLog(
            operator_email=user_email,
            action="update",
            role=user.role,
            target_user_id=user.id,
            target_user_email=user.email,
            details=changes,
            timestamp=datetime.utcnow()
        )
        db.session.add(log)

    db.session.commit()
    return jsonify(msg="User profile updated successfully"), 200


@user_bp.route("/user/avatar", methods=["POST"])
@jwt_required()
def upload_avatar():
    """Upload and update the current user's avatar."""
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    user_profile = user.profile

    file = request.files.get("avatar")
    if not file or not allowed_file(file.filename):
        return jsonify(msg="Invalid file type."), 400

    filename = secure_filename(file.filename)
    save_dir = os.path.join(current_app.root_path, "static", "avatars")
    os.makedirs(save_dir, exist_ok=True)

    file_path = os.path.join(save_dir, f"user_{user.id}.jpg")
    file.save(file_path)

    avatar_url = f"/static/avatars/user_{user.id}.jpg"
    user_profile.avatar_url = avatar_url

    log = UserActionLog(
        operator_email=user_email,
        action="update",
        role=user.role,
        target_user_id=user.id,
        target_user_email=user.email,
        details={"avatar_url": avatar_url},
        timestamp=datetime.utcnow()
    )

    db.session.add(log)
    db.session.commit()

    return jsonify(msg="Avatar uploaded successfully.", avatar_url=avatar_url), 200


@user_bp.route("/user/notifications", methods=["GET"])
@jwt_required()
def get_notifications():
    """Retrieve the current user's notifications (with optional filters)."""
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    unread_only = request.args.get("unread_only", "false").lower() == "true"

    query = Notification.query.filter_by(user_id=user.id)
    if unread_only:
        query = query.filter_by(is_read=False)

    total = query.count()
    unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    notifications = query.order_by(desc(Notification.created_at)).paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "type": n.type,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat()
            } for n in notifications.items
        ],
        "total": total,
        "unread_count": unread_count,
        "page": page,
        "limit": limit
    }), 200


@user_bp.route("/user/notifications/<int:notification_id>/read", methods=["PUT"])
@jwt_required()
def mark_notification_read(notification_id):
    """Mark a notification as read."""
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    notif = Notification.query.filter_by(id=notification_id, user_id=user.id).first()
    if not notif:
        return jsonify({"msg": "Notification not found"}), 404

    notif.is_read = True
    db.session.commit()

    return jsonify({"msg": "Notification marked as read"}), 200


@user_bp.route("/user/delete_account", methods=["DELETE"])
@jwt_required()
def delete_account():
    """Delete the current user's account after verification code check."""
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    data = request.get_json()

    if not user:
        return jsonify({"msg": "User not found"}), 404

    if not data or "code" not in data:
        return jsonify({"msg": "Verification code is required"}), 400

    code = data["code"]
    if not verify_code(user_email, code):
        return jsonify({"msg": "Invalid or expired verification code"}), 400

    log = UserActionLog(
        operator_email=user_email,
        action="delete",
        role=user.role,
        target_user_id=user.id,
        target_user_email=user.email,
        details={
            "full_name": user.profile.full_name if user.profile else None,
            "role": user.role,
            "status": user.status
        },
        timestamp=datetime.utcnow()
    )
    db.session.add(log)

    db.session.delete(user)
    delete_code(user_email)
    db.session.commit()

    return jsonify({"msg": "Account deleted successfully"}), 200
