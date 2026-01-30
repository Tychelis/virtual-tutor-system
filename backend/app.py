from flask import Flask, jsonify, send_from_directory, g, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models.user import db
from routes.auth import auth_bp
from routes.chat import chat_bp
from routes.user import user_bp
from routes.admin import admin_bp
from routes.upload import upload_bp
from routes.avatar import avatar_bp
from routes.health import health_bp
from services.email_service import mail
from services.http_client import cleanup_http_client
from sqlalchemy.engine import Engine
from sqlalchemy import event
import sqlite3
import os
import logging
import traceback
import atexit
import time

def create_app():
    """Application factory: configure app, extensions, and blueprints."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Init extensions
    CORS(app)          # Enable CORS for all routes
    db.init_app(app)   # Bind SQLAlchemy to app

        #  自动创建数据库（instance/app.db）
    with app.app_context():
        db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if db_uri.startswith("sqlite:///"):
            # 提取数据库文件路径
            db_file = db_uri.replace("sqlite:///", "")
            db_dir = os.path.dirname(db_file) or "."

            # 确保数据库目录存在（例如 instance/）
            os.makedirs(db_dir, exist_ok=True)

            # 如果数据库文件不存在，则创建
            if not os.path.exists(db_file):
                print(f"  Creating new database at {db_file} ...")
                db.create_all()

    JWTManager(app)    # Setup JWT
    mail.init_app(app) # Setup Flask-Mail

    # Register API blueprints (versioned under /api)
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(user_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api")
    app.register_blueprint(upload_bp, url_prefix="/api")
    app.register_blueprint(avatar_bp, url_prefix="/api")
    app.register_blueprint(health_bp, url_prefix="/api")

    #  同步Avatar Manager的实例映射（用于Backend重启后恢复）
    with app.app_context():
        try:
            from services.avatar_session_manager import get_avatar_session_manager
            session_manager = get_avatar_session_manager()
            synced = session_manager.sync_from_avatar_manager()
            if synced > 0:
                logging.info(f" Backend启动时同步了{synced}个Avatar映射")
        except Exception as e:
            logging.warning(f" Failed to sync avatar mappings on startup: {e}")

    @app.before_request
    def log_request_info():
        """记录每个请求的详细信息"""
        g.start_time = time.time()
        # 只记录非静态资源请求
        if not request.path.startswith('/static/'):
            logging.info(f" {request.method} {request.path} - IP: {request.remote_addr}")

    @app.after_request
    def attach_new_token(response):
        """Attach a refreshed JWT to the response header if present."""
        if hasattr(g, "new_token"):
            response.headers["X-New-Token"] = g.new_token
        
        # 记录响应信息
        if hasattr(g, 'start_time') and not request.path.startswith('/static/'):
            elapsed = time.time() - g.start_time
            logging.info(f" {request.method} {request.path} - Status: {response.status_code} - Time: {elapsed:.3f}s")
        
        return response

    @app.route("/static/avatars/<path:filename>")
    def serve_avatar(filename):
        """Serve avatar images from the /static/avatars directory."""
        return send_from_directory(os.path.join(app.root_path, "static", "avatars"), filename)

    @app.errorhandler(404)
    def handle_404(e):
        """Handle 404 errors with detailed logging."""
        logging.warning(f" 404 NOT FOUND: {request.method} {request.path} - IP: {request.remote_addr}")
        return jsonify({"msg": "Resource not found", "path": request.path}), 404

    @app.errorhandler(Exception)
    def handle_exception(e):
        """Global error handler: log traceback and return 500."""
        logging.error(f" Exception on {request.method} {request.path}: %s", traceback.format_exc())
        return jsonify({"msg": "Internal Server Error"}), 500

    # Register cleanup handler for HTTP client
    def cleanup_on_shutdown():
        """清理HTTP客户端连接池"""
        try:
            cleanup_http_client()
        except Exception as e:
            logging.error(f"Error during HTTP client cleanup: {e}")
    
    atexit.register(cleanup_on_shutdown)

    return app


# Enable SQLite foreign key constraints on each new connection
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
