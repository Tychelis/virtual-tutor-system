# import os

# basedir = os.path.abspath(os.path.dirname(__file__))

# class Config:
#     """Application configuration settings."""

#     # ===== Basic settings =====
#     SECRET_KEY = 'super-secret-key'  # Flask secret key (should be changed in production)
#     SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'db', 'users.db')}"  # SQLite DB path
#     SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable modification tracking to save resources

#     # ===== JWT settings =====
#     JWT_SECRET_KEY = "your-jwt-secret"     # Secret key for signing JWTs
#     JWT_ACCESS_TOKEN_EXPIRES = 18000       # Token expiry time (in seconds) - 5 hours
#     JWT_COOKIE_CSRF_PROTECT = False        # Disable CSRF protection for JWT cookies

#     REDIS_TOKEN_TTL_SECONDS = 18000        # TTL for storing JWT token in Redis (in seconds)

#     # ===== Email settings =====
#     MAIL_SERVER = 'your email server'      # SMTP server address
#     MAIL_PORT = 587                         # SMTP port (587 for TLS)
#     MAIL_USE_TLS = True                     # Use TLS for email sending
#     MAIL_USERNAME = "your email username"   # SMTP account username
#     MAIL_PASSWORD = "your password"         # SMTP account password
#     MAIL_DEFAULT_SENDER = ("TutorNet", "your email")  # Default sender name and email
# config.py
import os
from dotenv import load_dotenv

load_dotenv()  # 保留

basedir = os.path.abspath(os.path.dirname(__file__))

def as_bool(v, default=False):
    if v is None:
        return default
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}

class Config:
    """Application configuration settings."""

    # ===== Basic settings =====
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")  # 用 env；开发期给一个安全但显眼的默认
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASEDIR, 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ===== JWT settings =====
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "18000"))
    JWT_COOKIE_CSRF_PROTECT = as_bool(os.getenv("JWT_COOKIE_CSRF_PROTECT"), False)

    REDIS_TOKEN_TTL_SECONDS = int(os.getenv("REDIS_TOKEN_TTL_SECONDS", "18000"))

    # ===== Email settings =====
    MAIL_SERVER = os.getenv("MAIL_SERVER", "")              # 不给假主机名
    MAIL_PORT = int(os.getenv("MAIL_PORT", "0"))            # 0 让错误更显眼
    MAIL_USE_TLS = as_bool(os.getenv("MAIL_USE_TLS"), False)
    MAIL_USE_SSL = as_bool(os.getenv("MAIL_USE_SSL"), False)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    # 既兼容只给地址，也兼容 "Name <addr>" 形式
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "")