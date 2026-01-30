import os
import mimetypes
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from models.user import User, db
import requests

# Blueprint for file upload and management routes
upload_bp = Blueprint("upload", __name__)

# Allowed MIME types for document uploads
ALLOWED_DOCUMENT_MIME = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
}


@upload_bp.route("/upload", methods=["POST"])
@jwt_required()
def dispatch_upload():
    """Handle file upload and forward to role-specific service."""
    # Debug logs for incoming request
    print("==== new request ====")
    print("[Headers]", dict(request.headers))
    print("[Form]", request.form.to_dict())
    print("[Files]")
    for key, file in request.files.items():
        print(f"{key}: filename={file.filename}, content_type={file.content_type}")

    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()
    if not user:
        return jsonify(msg="User not found."), 404

    # Forward to different endpoints based on role
    if user.role == "student":
        forward_url = "http://localhost:9090/user/upload"
    elif user.role == "tutor":
        forward_url = "http://localhost:9090/admin/upload"
    else:
        return jsonify(msg="Invalid role"), 403

    f = request.files.get("file")
    if not f:
        return jsonify(msg="No file provided"), 400

    files = {'file': (f.filename, f.stream, f.mimetype)}
    data = request.form.to_dict()
    data['user_id'] = str(user.id)

    try:
        response = requests.post(forward_url, files=files, data=data, timeout=30)
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify(msg=f"Upload forward failed: {str(e)}"), 500


@upload_bp.route("/upload/<file_name>", methods=["DELETE"])
@jwt_required()
def delete_file(file_name):
    """Delete a file by forwarding request to role-specific service."""
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()
    if not user:
        return jsonify(msg="User not found"), 404

    user_id = str(user.id)
    if user.role == "student":
        forward_url = "http://localhost:9090/user/delete"
        form_data = {"user_id": user_id, "source_name": file_name}
    elif user.role == "tutor":
        forward_url = "http://localhost:9090/admin/delete"
        form_data = {"source_name": file_name}
    else:
        return jsonify(msg="Invalid role"), 403

    try:
        response = requests.post(forward_url, data=form_data, timeout=10)
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify(msg="Delete forward failed", error=str(e)), 500


@upload_bp.route("/upload/users", methods=["GET"])
@jwt_required()
def fetch_all_users():
    """Fetch all users (tutor-only)."""
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()
    if not user or user.role != "tutor":
        return jsonify(msg="Permission denied: Only tutors can access user list."), 403

    try:
        response = requests.get("http://localhost:9090/api/users", timeout=10)
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify(msg="Failed to fetch users", error=str(e)), 500


@upload_bp.route("/user_files", methods=["GET"])
@jwt_required()
def fetch_user_files():
    """Fetch list of files uploaded by the current user."""
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()
    if not user:
        return jsonify(msg="User not found"), 404

    try:
        response = requests.get(
            "http://localhost:9090/api/user_files",
            params={"user_id": user.id},
            timeout=10
        )
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify(msg="Failed to fetch user files", error=str(e)), 500


@upload_bp.route("/public_files", methods=["GET"])
@jwt_required()
def fetch_public_files():
    """Fetch list of public files (tutor-only)."""
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()
    if not user or user.role != "tutor":
        return jsonify(msg="Permission denied: Only tutors can access public files."), 403

    try:
        response = requests.get("http://localhost:9090/api/public_files", timeout=10)
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify(msg="Failed to fetch public files", error=str(e)), 500
