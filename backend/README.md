# Backend Service - API Gateway & Orchestration Layer

## 🎯 Overview

The Backend Service is the central orchestration layer of the Virtual Tutor System, acting as an API gateway that coordinates communication between the frontend, LLM service, RAG system, Avatar Manager, and WebRTC streaming. Built on Flask with production-ready Gunicorn deployment, it provides a comprehensive RESTful API with JWT authentication, Redis-based session management, and real-time streaming capabilities.

**Architecture Role**: Request Router → Service Orchestrator → Response Aggregator

## ✨ Key Features

### Core Capabilities
- **User Authentication & Authorization**
  - JWT-based stateless authentication
  - Role-based access control (Student/Tutor/Admin)
  - Email verification with rate limiting
  - Redis-backed token invalidation
  - Automatic token refresh mechanism

- **Real-Time Chat with Streaming**
  - Server-Sent Events (SSE) for streaming responses
  - LLM response streaming with incremental TTS forwarding
  - RAG context integration (document-aware responses)
  - Session persistence with SQLite
  - Multi-session management per user

- **Avatar Management & WebRTC Proxy**
  - User-avatar session mapping (Redis Hash for multi-worker consistency)
  - Dynamic port allocation per user
  - WebRTC request proxying with connection pooling
  - Avatar instance lifecycle management
  - Concurrent user support (instance sharing)

- **File Upload & RAG Integration**
  - Multi-format support (PDF, TXT, DOCX, images, audio)
  - Automatic document indexing to RAG service
  - User-specific file storage with timestamps
  - File metadata tracking in database

- **Production-Ready Deployment**
  - Gunicorn WSGI server with multi-worker support
  - HTTP connection pooling (httpx) for backend-to-service communication
  - Graceful shutdown and cleanup handlers
  - Comprehensive logging with request/response timing
  - Health check endpoints

- **Email Notification Service**
  - Flask-Mail integration with SMTP
  - Verification code generation and validation
  - Rate limiting (10-second cooldown)

## 📁 Project Structure

```
backend/
├── app.py                      # Application factory & initialization
│                               # - Extension setup (CORS, JWT, Mail, DB)
│                               # - Blueprint registration
│                               # - Error handlers & middleware
│                               # - HTTP client cleanup
├── config.py                   # Configuration management
│                               # - Environment variable loading (.env)
│                               # - JWT/Redis/Mail settings
│                               # - Database URI configuration
├── run.py                      # Development server entry point
├── gunicorn_config.py          # Production server configuration
│                               # - Multi-worker setup (4 workers default)
│                               # - Timeout & keepalive settings
│                               # - Logging configuration
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (secrets)
│
├── routes/                     # API endpoint blueprints
│   ├── auth.py                 # Authentication (/api/login, /api/register, /api/logout)
│   ├── chat.py                 # Chat & streaming (/api/chat, /api/chat/stream)
│   ├── avatar.py               # Avatar management (/api/avatar/*)
│   ├── user.py                 # User profile management
│   ├── upload.py               # File upload handling
│   ├── admin.py                # Admin operations
│   └── health.py               # Health check endpoints
│
├── models/                     # SQLAlchemy ORM models
│   ├── user.py                 # User, UserProfile, UserActionLog
│   ├── chat.py                 # Session, Message
│   └── notification.py         # Notification model
│
├── services/                   # Business logic & external integrations
│   ├── email_service.py        # SMTP email sending (Flask-Mail)
│   ├── redis_client.py         # Redis connection singleton
│   ├── verification_cache.py   # Verification code management
│   ├── avatar_session_manager.py  # User-avatar port mapping (Redis Hash)
│   └── http_client.py          # HTTP connection pool (httpx)
│
├── utils/                      # Utility functions
│   ├── token_utils.py          # JWT validation decorators
│   ├── refresh_token.py        # Token refresh logic
│   └── refresh_redis.py        # Redis TTL extension
│
├── instance/                   # Instance-specific data
│   └── app.db                  # SQLite database file
│
├── uploads/                    # User-uploaded files
│   └── {user_id}/              # Per-user directories
│
├── logs/                       # Application logs
│   ├── backend_access.log      # Gunicorn access logs
│   ├── backend_error.log       # Gunicorn error logs
│   └── error.log               # Application error logs
│
└── static/                     # Static assets
    └── avatars/                # Default avatar images
```

## 🏗️ Architecture & Technical Implementation

### System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      Frontend (React)                          │
│  • User authentication UI                                      │
│  • Chat interface with streaming display                       │
│  • Avatar selection & WebRTC video display                     │
└────────────────────┬───────────────────────────────────────────┘
                     │ HTTP/HTTPS + WebSocket (SSE)
                     ▼
┌────────────────────────────────────────────────────────────────┐
│                Backend Service (This Layer)                    │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Flask App (Gunicorn: 4 workers)                         │ │
│  │  • Request routing & validation                          │ │
│  │  • JWT authentication middleware                         │ │
│  │  • Session management (Redis)                            │ │
│  │  • Response streaming (SSE)                              │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ SQLite DB    │  │ Redis Cache  │  │ File Storage │       │
│  │ • Users      │  │ • JWT tokens │  │ • Uploads    │       │
│  │ • Sessions   │  │ • Session IDs│  │ • User files │       │
│  │ • Messages   │  │ • Avatar map │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└────────────────────┬───────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┬───────────────┬─────────────┐
         │                       │               │             │
         ▼                       ▼               ▼             ▼
┌────────────────┐  ┌────────────────┐  ┌──────────────┐  ┌──────────────┐
│  LLM Service   │  │  RAG Service   │  │Avatar Manager│  │ Lip-Sync     │
│  (Port 8100)   │  │  (Port 8200)   │  │ (Port 8607)  │  │ (WebRTC)     │
│                │  │                │  │              │  │              │
│ • Qwen model   │  │ • Milvus DB    │  │ • Instance   │  │ • MuseTalk   │
│ • Chat stream  │  │ • Embedding    │  │   pooling    │  │ • TTS        │
│ • Context mgmt │  │ • Retrieval    │  │ • GPU alloc  │  │ • Streaming  │
└────────────────┘  └────────────────┘  └──────────────┘  └──────────────┘
```

### Core Components

#### 1. Application Factory (`app.py`)
Initializes Flask application with all extensions and configurations:

```python
def create_app():
    # Initialize extensions
    CORS(app)           # Enable cross-origin requests
    db.init_app(app)    # SQLAlchemy database
    JWTManager(app)     # JWT authentication
    mail.init_app(app)  # Email service
    
    # Register blueprints (API routes)
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(avatar_bp, url_prefix="/api")
    # ... more blueprints
    
    # Middleware: logging, token refresh
    @app.before_request
    def log_request_info():
        g.start_time = time.time()
        logging.info(f"{request.method} {request.path}")
    
    @app.after_request
    def attach_new_token(response):
        if hasattr(g, "new_token"):
            response.headers["X-New-Token"] = g.new_token
        return response
    
    # Error handlers
    @app.errorhandler(404)
    def handle_404(e): ...
    
    @app.errorhandler(Exception)
    def handle_exception(e): ...
    
    return app
```

#### 2. Authentication System (`routes/auth.py`)
JWT-based authentication with Redis token storage:

**Login Flow:**
```
1. User submits email + password
2. Backend validates credentials (bcrypt password check)
3. Generate JWT with role claim: create_access_token(identity=email, additional_claims={"role": user.role})
4. Store token in Redis: setex(f"token:{jti}", TTL, email)
5. Store user's active token: setex(f"user_token:{user.id}", TTL, jti)
6. Return token to frontend
```

**Token Validation:**
```python
@jwt_required()  # Validates JWT signature & expiry
@token_in_redis_required  # Custom decorator: checks token exists in Redis
def protected_endpoint():
    user_email = get_jwt_identity()
    # ... endpoint logic
```

**Logout:**
```
1. Extract JTI from JWT
2. Delete from Redis: delete(f"token:{jti}")
3. Set user status to inactive
```

#### 3. Real-Time Chat with Streaming (`routes/chat.py`)

**Streaming Architecture:**
```python
@chat_bp.route("/chat/stream", methods=["POST"])
@jwt_required()
def chat_stream():
    def generate():
        # 1. Retrieve RAG context (if document-related query)
        if should_use_rag(message):
            rag_context = requests.post(RAG_URL + "/retriever", ...).json()
        
        # 2. Stream LLM response (SSE)
        llm_response = requests.post(
            LLM_URL + "/chat/stream",
            json={"input": message, "session_id": session.id},
            stream=True
        )
        
        buffer = ""
        for line in llm_response.iter_lines():
            chunk = parse_sse_chunk(line)
            buffer += chunk
            
            # 3. Forward chunk to frontend
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            
            # 4. Forward to TTS when sentence complete
            if buffer.endswith((".", "!", "?")) or len(buffer.split()) >= 5:
                requests.post(
                    f"http://localhost:{avatar_port}/human",
                    json={"text": buffer, "sessionid": rtc_session_id}
                )
                buffer = ""
        
        # 5. Save to database after streaming completes
        db.session.add(Message(role="assistant", content=full_text))
        db.session.commit()
    
    return Response(generate(), mimetype='text/event-stream')
```

**RAG Integration:**
- Detects document-related queries using keywords (e.g., "document", "file", "uploaded", "pdf")
- Retrieves top 5 relevant chunks from RAG service
- Prepends context to LLM prompt: `{user_message}\n\n=== CONTEXT FROM DOCUMENTS ===\n{rag_chunks}`

#### 4. Avatar Session Management (`services/avatar_session_manager.py`)

**Multi-Worker Consistency Challenge:**
- Gunicorn runs 4 workers (separate processes)
- Each worker has its own memory space
- User-avatar mapping must be shared across workers

**Solution: Redis Hash as Single Source of Truth**
```python
class AvatarSessionManager:
    REDIS_KEY = "avatar:user_mappings"  # Redis Hash key
    
    def set_user_avatar(self, user_id, avatar_id, port, instance_id):
        with self._lock:
            # 1. Update local memory (fast lookups)
            self.user_avatar_map[user_id] = {...}
            
            # 2. Atomic save to Redis Hash (multi-worker sync)
            redis.hset(self.REDIS_KEY, user_id, json.dumps({
                "avatar_id": avatar_id,
                "port": port,
                "instance_id": instance_id,
                "timestamp": time.time()
            }))
    
    def get_user_port(self, user_id):
        # Always read from Redis (avoid worker inconsistency)
        user_info_bytes = redis.hget(self.REDIS_KEY, user_id)
        if user_info_bytes:
            user_info = json.loads(user_info_bytes)
            return user_info['port']
        return None
```

**Avatar Switching Logic:**
```python
@avatar_bp.route("/avatar/start", methods=["POST"])
@jwt_required()
def forward_start_avatar():
    # 1. Check if user has existing avatar
    old_avatar = session_manager.get_user_avatar(user.id)
    
    # 2. If switching to different avatar, disconnect old one
    if old_avatar and old_avatar['avatar_id'] != new_avatar_name:
        requests.post(
            AVATAR_MANAGER_URL + "/avatar/disconnect",
            json={"avatar_name": old_avatar['avatar_id']}
        )
        session_manager.remove_user(user.id)
    
    # 3. Start new avatar instance
    response = requests.post(
        AVATAR_MANAGER_URL + "/avatar/start",
        json={
            "avatar_id": f"{avatar_name}_user_{user.id}",  # Unique instance ID
            "avatar_name": avatar_name  # Real avatar name (for pooling)
        }
    )
    
    # 4. Save mapping to Redis
    session_manager.set_user_avatar(user.id, avatar_name, port, instance_id)
    
    return jsonify({"port": port, "webrtc_url": "/api/webrtc/offer"})
```

#### 5. WebRTC Proxy (`routes/avatar.py`)

**Dynamic Port Routing:**
```python
@avatar_bp.route("/webrtc/<path:path>", methods=["GET", "POST"])
@jwt_required(optional=True)
def webrtc_proxy(path):
    # 1. Get user's avatar port from Redis
    port = AVATAR_BASE_PORT  # Default
    if current_user_email:
        user = User.query.filter_by(email=current_user_email).first()
        if user:
            # Read from Redis Hash (multi-worker safe)
            user_info = redis.hget('avatar:user_mappings', str(user.id))
            if user_info:
                port = json.loads(user_info)['port']
    
    # 2. Forward request to user's avatar port
    webrtc_url = f"http://localhost:{port}/{path}"
    response = http_client.post(webrtc_url, content=request.get_data())
    
    # 3. Return response to frontend
    return Response(response.content, status=response.status_code)
```

**Connection Pooling:**
- Uses `httpx.Client` with connection pool (max 100 connections)
- Reuses TCP connections for repeated requests
- Automatic cleanup on application shutdown

#### 6. File Upload & RAG Integration (`routes/chat.py`)

```python
@chat_bp.route("/chat/upload", methods=["POST"])
@jwt_required()
def upload_file():
    # 1. Validate file type
    file_ext = filename.rsplit('.', 1)[1].lower()
    if file_ext in ALLOWED_DOCS:  # pdf, txt, docx
        file_type = "document"
    
    # 2. Save file with timestamp
    file_path = f"uploads/{user.id}/{timestamp}_{filename}"
    file.save(file_path)
    
    # 3. Create database record
    message = Message(
        role="user",
        content=f"Uploaded {file_type}: {filename}",
        file_type=file_type,
        file_path=file_path
    )
    db.session.add(message)
    
    # 4. Send to RAG service for indexing
    if file_type == "document":
        with open(file_path, 'rb') as f:
            rag_response = requests.post(
                RAG_URL + "/user/upload",
                files={'file': (filename, f)},
                data={'user_id': str(user.id)}
            )
    
    return jsonify({"msg": "File uploaded and indexed"})
```

## 🚀 System Requirements

- **Python**: 3.10 or higher
- **Database**: SQLite (auto-created in `instance/app.db`)
- **Cache**: Redis 6.0+ (required for multi-worker session management)
- **Email**: SMTP server (for verification emails)
- **Dependencies**: See `requirements.txt`

## 🚀 Deployment Guide

### Prerequisites

1. **Redis Server**: Must be running and accessible
   ```bash
   # Install Redis (Ubuntu/Debian)
   sudo apt-get install redis-server
   
   # Start Redis
   redis-server &
   
   # Verify Redis is running
   redis-cli ping  # Should return: PONG
   ```

2. **Python Environment**: Python 3.10+
3. **SMTP Server**: For email verification (optional for development)

### Step 1: Install Dependencies

```bash
cd backend

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

**Key Dependencies:**
```
flask==3.1.1                  # Web framework
flask-cors==6.0.1             # CORS support
flask-jwt-extended==4.7.0     # JWT authentication
flask-sqlalchemy==3.1.1       # ORM
redis==5.0.3                  # Redis client
gunicorn==23.0.0              # WSGI server (production)
gevent==24.11.1               # Async worker (production)
httpx==0.28.1                 # HTTP client with connection pooling
requests==2.32.4              # HTTP requests
```

### Step 2: Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Flask & Security
SECRET_KEY=your-super-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRES=18000  # 5 hours in seconds
JWT_COOKIE_CSRF_PROTECT=false

# Redis Configuration
REDIS_TOKEN_TTL_SECONDS=18000  # Token TTL (5 hours)

# Email Configuration (SMTP)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=TutorNet <your-email@gmail.com>

# Production Settings (optional)
WORKERS=4                     # Gunicorn workers
WORKER_CLASS=sync             # Worker type (sync/gevent/eventlet)
THREADS=1                     # Threads per worker
```

**Security Notes:**
- Generate strong random keys for `SECRET_KEY` and `JWT_SECRET_KEY`:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- Never commit `.env` file to version control
- For Gmail SMTP, use App Passwords (not your account password)

### Step 3: Initialize Database

The database will be created automatically on first run, but you can manually initialize it:

```bash
python -c "from app import create_app; from models.user import db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized')"
```

This creates `instance/app.db` with the following tables:
- `user` - User accounts
- `user_profile` - User profiles
- `user_action_log` - Admin action logs
- `session` - Chat sessions
- `message` - Chat messages
- `notification` - User notifications

### Step 4: Run in Development Mode

```bash
# Option 1: Using Flask development server (single-threaded)
python run.py

# Option 2: Using startup script
./start_dev.sh

# Service will start on port 8000 (configured in scripts/ports_config.py)
```

**Development Server Features:**
- Auto-reload on code changes
- Detailed error pages
- Single-threaded (no concurrency issues)
- Not suitable for production

### Step 5: Run in Production Mode

```bash
# Option 1: Using Gunicorn with gevent workers (recommended)
gunicorn -c gunicorn_config.py app:app

# Option 2: Using production startup script
./start_production.sh

# Option 3: Custom Gunicorn command
gunicorn --bind 0.0.0.0:8000 \
         --workers 4 \
         --worker-class sync \
         --timeout 120 \
         --access-logfile logs/backend_access.log \
         --error-logfile logs/backend_error.log \
         app:app
```

**Production Configuration** (`gunicorn_config.py`):
```python
workers = 4                    # 4 worker processes
worker_class = 'sync'          # Worker type
worker_connections = 1000      # Max concurrent connections
timeout = 120                  # Request timeout (seconds)
keepalive = 5                  # Keep-alive timeout
max_requests = 1000            # Restart worker after N requests
graceful_timeout = 30          # Graceful shutdown timeout
preload_app = True             # Load app before forking workers
```

**Worker Types:**
- `sync`: Default, suitable for CPU-intensive tasks
- `gevent`: Coroutine-based, suitable for I/O-intensive (requires `pip install gevent`)
- `eventlet`: Alternative coroutine implementation (requires `pip install eventlet`)

### Step 6: Verify Deployment

```bash
# Check health endpoint
curl http://localhost:8000/api/health

# Expected response:
# {"status": "healthy", "timestamp": "2025-11-18T10:30:00"}

# Check Redis connection
redis-cli GET "token:test"  # Should not error

# Check logs
tail -f logs/backend_access.log
tail -f logs/backend_error.log
```

### Production Deployment with Systemd

Create a systemd service file `/etc/systemd/system/backend.service`:

```ini
[Unit]
Description=Virtual Tutor Backend Service
After=network.target redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn -c gunicorn_config.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable backend
sudo systemctl start backend
sudo systemctl status backend
```

### Docker Deployment (Optional)

The backend includes a `Dockerfile` for containerized deployment:

```bash
# Build image
docker build -t virtual-tutor-backend:latest .

# Run container
docker run -d \
  --name backend \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/instance:/app/instance \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/logs:/app/logs \
  virtual-tutor-backend:latest
```

## 📡 API Documentation

All APIs are prefixed with `/api` and require `Content-Type: application/json` (except file uploads which use `multipart/form-data`).

### Authentication Endpoints (`/api/auth`)

#### Register New User
```http
POST /api/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "code": "123456",           # From email verification
  "role": "student"           # Optional: student/tutor (default: student)
}

Response 201:
{
  "msg": "Registration successful"
}
```

#### Send Verification Code
```http
POST /api/send_verification
Content-Type: application/json

{
  "email": "user@example.com",
  "purpose": "register"        # or "reset_password"
}

Response 200:
{
  "msg": "Verification code sent."
}

Response 429:  # Rate limited
{
  "msg": "Please wait 10 seconds before requesting again"
}
```

#### Login
```http
POST /api/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

Response 200:
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

Response 401:
{
  "msg": "Invalid credentials"
}
```

#### Check Token Status
```http
GET /api/token_status
Authorization: Bearer <JWT_TOKEN>

Response 200:
{
  "expires_in_seconds": 14523,
  "expires_in_minutes": 242.05
}
```

#### Update Password
```http
POST /api/update_password
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "code": "123456",           # From email verification
  "new_password": "NewPass456!"
}

Response 200:
{
  "msg": "Password updated successfully"
}
```

#### Logout
```http
POST /api/logout
Authorization: Bearer <JWT_TOKEN>

Response 200:
{
  "msg": "Logged out successfully."
}
```

---

### Chat Endpoints (`/api/chat`)

#### Send Message with Streaming
```http
POST /api/chat/stream
Authorization: Bearer <JWT_TOKEN>
Content-Type: multipart/form-data
Accept: text/event-stream

Form Data:
- message: "Explain quantum computing"
- session_id: 123 (optional, creates new if omitted)

Response: Server-Sent Events (SSE)
data: {"status": "streaming", "chunk": "Quantum"}
data: {"status": "streaming", "chunk": " computing"}
data: {"status": "streaming", "chunk": " is..."}
...
data: {"status": "complete", "session_id": 123, "text": "Quantum computing is..."}
```

**Features:**
- Streams LLM response in real-time
- Automatically retrieves RAG context for document-related queries
- Forwards text to TTS in small chunks (5-8 words) for low latency
- Saves conversation to database after completion

**RAG Activation Keywords:**
```
'document', 'file', 'uploaded', 'pdf', 'doc', 'content', 'paper',
'according to', 'based on', 'in the document', 'repo', 'requirement'
```

#### Upload File (with RAG Indexing)
```http
POST /api/chat/upload
Authorization: Bearer <JWT_TOKEN>
Content-Type: multipart/form-data

Form Data:
- file: <binary>
- session_id: 123 (optional)

Response 200:
{
  "msg": "File uploaded successfully",
  "session_id": 123,
  "message_id": 456,
  "file_path": "uploads/1/20251118_103045_document.pdf",
  "file_type": "document",
  "filename": "document.pdf",
  "rag_indexed": true          # Document sent to RAG service
}
```

**Supported File Types:**
- **Documents**: `pdf`, `txt`, `docx` (auto-indexed to RAG)
- **Images**: `png`, `jpg`, `jpeg`
- **Audio**: `wav`, `mp3`, `m4a`

#### Get User Files
```http
GET /api/user_files
Authorization: Bearer <JWT_TOKEN>

Response 200:
{
  "msg": "Files retrieved successfully",
  "total": 5,
  "files": [
    {
      "id": 456,
      "filename": "document.pdf",
      "file_type": "document",
      "file_path": "uploads/1/20251118_103045_document.pdf",
      "content": "Uploaded document: document.pdf",
      "created_at": "2025-11-18T10:30:45",
      "session_id": 123,
      "size": 102400
    }
  ]
}
```

#### Create New Chat Session
```http
POST /api/chat/new
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "title": "Quantum Computing Discussion"
}

Response 201:
{
  "session_id": 123
}
```

#### List Chat Sessions
```http
GET /api/chat/history
Authorization: Bearer <JWT_TOKEN>

Response 200:
[
  {
    "id": 123,
    "title": "Quantum Computing Discussion",
    "created_at": "2025-11-18T10:00:00",
    "updated_at": "2025-11-18T10:30:00",
    "message_count": 8,
    "is_favorite": false
  }
]
```

#### Get Messages in Session
```http
GET /api/message/list?session_id=123
Authorization: Bearer <JWT_TOKEN>

Response 200:
[
  {
    "role": "user",
    "content": "Explain quantum computing",
    "created_at": "2025-11-18T10:30:00",
    "file_type": null,
    "file_path": null
  },
  {
    "role": "assistant",
    "content": "Quantum computing is...",
    "created_at": "2025-11-18T10:30:15",
    "file_type": null,
    "file_path": null
  }
]
```

#### Set Session as Favorite
```http
POST /api/chat/123/favorite
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "is_favorite": true
}

Response 200:
{
  "msg": "Favorite status updated",
  "session_id": 123,
  "is_favorite": true
}
```

#### Delete Chat Session
```http
DELETE /api/chat/123
Authorization: Bearer <JWT_TOKEN>

Response 200:
{
  "msg": "Session 123 deleted"
}
```

#### Save WebRTC Session ID
```http
POST /api/sessionid
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "sessionid": 1
}

Response 200: (Empty body)
```

---

### Avatar Endpoints (`/api/avatar`)

#### Get Available Avatars
```http
GET /api/avatar/list
Authorization: Bearer <JWT_TOKEN>

Response 200:
{
  "test_yongen": {
    "clone": false,
    "description": "Professional tutor avatar",
    "status": "active",
    "timbre": "en-US-BrianNeural",
    "tts_model": "edgeTTS",
    "avatar_model": "musetalk"
  },
  "g": {
    "clone": true,
    "description": "Custom cloned avatar",
    "status": "active",
    "timbre": "",
    "tts_model": "CosyVoice",
    "avatar_model": "musetalk"
  }
}
```

#### Start Avatar Instance
```http
POST /api/avatar/start
Authorization: Bearer <JWT_TOKEN>
Content-Type: multipart/form-data

Form Data:
- avatar_name: "test_yongen"

Response 200:
{
  "status": "success",
  "avatar_id": "test_yongen_user_1",
  "port": 8615,
  "webrtc_url": "/api/webrtc/offer",
  "gpu": 1,
  "connections": 1,
  "is_new_instance": true,
  "message": "Avatar started successfully (port 8615, connections: 1)"
}
```

**Behavior:**
- Creates unique instance ID: `{avatar_name}_user_{user_id}`
- Automatically disconnects user's previous avatar if switching
- Saves user-avatar mapping to Redis Hash (multi-worker safe)
- Returns WebRTC proxy URL (frontend doesn't need to know port)

#### Disconnect from Avatar
```http
POST /api/avatar/disconnect
Authorization: Bearer <JWT_TOKEN>

Response 200:
{
  "status": "success",
  "message": "Disconnected from avatar test_yongen"
}
```

**Behavior:**
- Calls Avatar Manager's disconnect API (reduces connection count)
- Clears user-avatar mapping from Redis
- Does not force-stop instance (graceful shutdown)

#### Get Avatar Preview Image
```http
POST /api/avatar/preview
Authorization: Bearer <JWT_TOKEN>
Content-Type: multipart/form-data

Form Data:
- avatar_name: "test_yongen"

Response 200:
Content-Type: image/png
<binary image data>
```

#### Add New Avatar (Tutor Only)
```http
POST /api/avatar/add
Authorization: Bearer <JWT_TOKEN>
Content-Type: multipart/form-data

Form Data:
- name: "my_custom_avatar"
- avatar_blur: "false"
- support_clone: "true"
- timbre: "custom_voice"
- tts_model: "CosyVoice"
- avatar_model: "musetalk"
- description: "My custom avatar"
- prompt_face: <image file>
- prompt_voice: <audio file>

Response 200:
{
  "status": "success",
  "message": "Avatar created successfully",
  "avatar_name": "my_custom_avatar"
}

Response 403:  # Non-tutor user
{
  "msg": "Permission denied"
}
```

#### Delete Avatar (Tutor Only)
```http
POST /api/avatar/delete
Authorization: Bearer <JWT_TOKEN>
Content-Type: multipart/form-data

Form Data:
- name: "my_custom_avatar"

Response 200:
{
  "status": "success",
  "message": "Avatar deleted successfully"
}
```

#### WebRTC Proxy (Dynamic Port Routing)
```http
POST /api/webrtc/offer
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "sdp": "v=0\no=- ...",
  "type": "offer"
}

Response: (Proxied from user's avatar instance)
```

**Behavior:**
- Extracts user ID from JWT
- Looks up user's avatar port in Redis Hash
- Forwards request to `http://localhost:{port}/offer`
- Returns response to frontend
- Enables concurrent users without port conflicts

#### Get TTS Models
```http
GET /api/tts/models
Authorization: Bearer <JWT_TOKEN>

Response 200:
{
  "EdgeTTS": {
    "full_name": "Microsoft EdgeTTS",
    "clone": false,
    "status": "active",
    "license": "free",
    "timbres": ["en-US-BrianNeural", "en-US-JennyNeural", ...],
    "cur_timbre": "en-US-BrianNeural"
  },
  "CosyVoice": {
    "full_name": "CosyVoice",
    "clone": true,
    "status": "active",
    "license": "MIT",
    "timbres": null,
    "cur_timbre": null
  }
}
```

---

### LLM Endpoints (`/api/llm`)

#### Activate LLM Model
```http
POST /api/llm/activate
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "model": "qwen2.5-32b-instruct"
}

Response 200:
{
  "status": "success",
  "message": "Model activated",
  "model": "qwen2.5-32b-instruct"
}
```

---

### Health Check Endpoints (`/api/health`)

#### Service Health
```http
GET /api/health

Response 200:
{
  "status": "healthy",
  "service": "backend",
  "timestamp": "2025-11-18T10:30:00",
  "database": "connected",
  "redis": "connected"
}
```

## 🔧 Troubleshooting

### Issue 1: Redis Connection Failed

**Symptoms:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solutions:**
```bash
# Check if Redis is running
redis-cli ping

# Start Redis if not running
redis-server &

# Check Redis port (default: 6379)
sudo netstat -nltp | grep 6379

# Test connection
python -c "import redis; r = redis.Redis(host='localhost', port=6379); print(r.ping())"
```

**Note:** Redis is **required** for multi-worker deployments. Cannot be disabled.

---

### Issue 2: Database Locked Error

**Symptoms:**
```
sqlite3.OperationalError: database is locked
```

**Cause:** SQLite doesn't handle concurrent writes well with multiple Gunicorn workers.

**Solutions:**

**Option A:** Reduce workers (not recommended for production)
```python
# gunicorn_config.py
workers = 1  # Single worker avoids locking
```

**Option B:** Use gevent workers (recommended)
```python
# gunicorn_config.py
worker_class = 'gevent'
workers = 4
```

**Option C:** Switch to PostgreSQL (best for production)
```bash
# Install PostgreSQL driver
pip install psycopg2-binary

# Update .env
DATABASE_URL=postgresql://user:pass@localhost/tutordb
```

---

### Issue 3: Email Verification Not Sending

**Symptoms:**
- `send_verification_email()` fails silently
- No verification code received

**Debug Steps:**
```bash
# Test SMTP connection
python -c "
from flask_mail import Mail, Message
from app import create_app
app = create_app()
mail = Mail(app)
with app.app_context():
    msg = Message('Test', recipients=['test@example.com'], body='Test')
    mail.send(msg)
    print('Email sent successfully')
"
```

**Common Issues:**
- **Gmail**: Must use App Password (not account password)
  - Enable 2FA → Generate App Password → Use in `.env`
- **Port Blocked**: Some ISPs block port 587/465
  - Try alternative SMTP providers (SendGrid, Mailgun)
- **TLS/SSL Mismatch**: Check `MAIL_USE_TLS` and `MAIL_USE_SSL` settings

---

### Issue 4: JWT Token Not Recognized

**Symptoms:**
```json
{
  "msg": "Token has expired",
  "msg": "Token not found in Redis"
}
```

**Causes & Solutions:**

**A) Token Expired:**
```bash
# Increase token lifetime in .env
JWT_ACCESS_TOKEN_EXPIRES=36000  # 10 hours
REDIS_TOKEN_TTL_SECONDS=36000
```

**B) Token Not in Redis:**
- Redis was restarted (tokens cleared)
- Worker mismatch (token stored by worker 1, validated by worker 2)
- Solution: User must re-login

**C) Clock Skew:**
```bash
# Synchronize system time
sudo ntpdate -s time.nist.gov
```

---

### Issue 5: WebRTC Proxy 502 Bad Gateway

**Symptoms:**
```json
{
  "msg": "Proxy error: Connection refused"
}
```

**Causes:**

**A) Avatar Not Started:**
```bash
# Check if avatar instance is running
curl http://localhost:8000/api/avatar/list

# Start avatar first
curl -X POST http://localhost:8000/api/avatar/start \
  -H "Authorization: Bearer <token>" \
  -F "avatar_name=test_yongen"
```

**B) Wrong Port in Redis:**
```bash
# Check user-avatar mapping
redis-cli HGETALL "avatar:user_mappings"

# Should show: "user_id" -> {"port": 8615, ...}
```

**C) Avatar Manager Down:**
```bash
# Check Avatar Manager status
curl http://localhost:8607/health

# Restart Avatar Manager if needed
cd avatar-manager && python api.py
```

---

### Issue 6: File Upload Fails (RAG Indexing Error)

**Symptoms:**
```json
{
  "rag_indexed": false,
  "rag_error": "RAG service error: Connection refused"
}
```

**Note:** File upload will still succeed, but document won't be searchable.

**Solutions:**
```bash
# Check if RAG service is running
curl http://localhost:8200/health

# Start RAG service
cd rag && python app.py

# Check logs for RAG errors
tail -f rag/logs/rag.log
```

---

### Issue 7: Streaming Response Hangs

**Symptoms:**
- Frontend receives first chunk, then stops
- Browser shows "pending" indefinitely

**Causes & Solutions:**

**A) LLM Service Timeout:**
```python
# Increase timeout in routes/chat.py
llm_response = requests.post(
    ...,
    stream=True,
    timeout=180.0  # Increase from 60 to 180 seconds
)
```

**B) Buffering Issue:**
```python
# Ensure SSE headers are set
return Response(
    generate(),
    mimetype='text/event-stream',
    headers={
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',  # Disable nginx buffering
        'Connection': 'keep-alive'
    }
)
```

**C) Nginx Reverse Proxy:**
```nginx
# Add to nginx config
location /api/chat/stream {
    proxy_pass http://backend;
    proxy_buffering off;
    proxy_read_timeout 300s;
    proxy_http_version 1.1;
}
```

---

### Issue 8: High Memory Usage (Multi-Worker)

**Symptoms:**
- Memory usage grows over time
- OOM killer terminates workers

**Solutions:**

**A) Enable Worker Recycling:**
```python
# gunicorn_config.py
max_requests = 1000  # Restart after 1000 requests
max_requests_jitter = 100  # Randomize restart
```

**B) Reduce Worker Count:**
```python
# gunicorn_config.py
workers = 2  # Reduce from 4 to 2
```

**C) Use Memory Profiler:**
```bash
# Install profiler
pip install memory_profiler

# Profile endpoint
python -m memory_profiler app.py
```

---

### Issue 9: CORS Errors in Frontend

**Symptoms:**
```
Access to fetch at 'http://localhost:8000/api/login' has been blocked by CORS policy
```

**Solutions:**

**A) Check CORS Configuration:**
```python
# app.py
CORS(app)  # Should enable CORS for all routes
```

**B) Frontend Using Wrong Origin:**
```javascript
// Ensure frontend uses correct backend URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

**C) Preflight Request Failing:**
```bash
# Test OPTIONS request
curl -X OPTIONS http://localhost:8000/api/login \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -v
```

---

### Issue 10: Database Migration Needed

**Symptoms:**
```
sqlalchemy.exc.OperationalError: no such column: user.new_field
```

**Cause:** Database schema doesn't match models after code changes.

**Solutions:**

**A) Recreate Database (Development Only):**
```bash
# CAUTION: Deletes all data
rm instance/app.db
python -c "from app import create_app; from models.user import db; app = create_app(); app.app_context().push(); db.create_all()"
```

**B) Use Alembic (Production):**
```bash
# Install Alembic
pip install alembic

# Initialize migrations
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Add new field"

# Apply migration
alembic upgrade head
```

---

## 📊 Monitoring & Logging

### Log Files

```
logs/
├── backend_access.log    # Gunicorn access logs (all HTTP requests)
├── backend_error.log     # Gunicorn error logs (worker crashes, exceptions)
└── error.log             # Application error logs
```

### Real-Time Monitoring

```bash
# Watch access logs
tail -f logs/backend_access.log

# Watch error logs
tail -f logs/backend_error.log

# Filter for errors
grep ERROR logs/backend_error.log | tail -20

# Monitor Redis
redis-cli MONITOR

# Monitor database connections
watch -n 1 'lsof -i :8000 | wc -l'
```

### Health Check Endpoints

```bash
# Backend health
curl http://localhost:8000/api/health

# Check all services
curl http://localhost:8000/api/health     # Backend
curl http://localhost:8100/health          # LLM
curl http://localhost:8200/health          # RAG
curl http://localhost:8607/health          # Avatar Manager
```

### Performance Metrics

```bash
# Request latency (from logs)
awk '/Time:/ {sum+=$NF; count++} END {print "Avg:", sum/count "s"}' logs/backend_access.log

# Top slow endpoints
grep "Time:" logs/backend_access.log | sort -k9 -n | tail -20

# Error rate
echo "Total: $(wc -l < logs/backend_access.log)"
echo "Errors: $(grep -E "(500|502|504)" logs/backend_access.log | wc -l)"
```

---

## 🧪 Testing

### Manual API Testing

```bash
# Test registration flow
curl -X POST http://localhost:8000/api/send_verification \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","purpose":"register"}'

curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","code":"123456"}'

# Test login
TOKEN=$(curl -s -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}' \
  | jq -r '.token')

# Test protected endpoint
curl http://localhost:8000/api/chat/history \
  -H "Authorization: Bearer $TOKEN"
```

### Automated Testing

```bash
# Install pytest
pip install pytest pytest-flask

# Run tests
cd backend
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v

# Run with coverage
pytest --cov=. --cov-report=html tests/
```

---

## 📝 Best Practices

### Security

1. **Never hardcode secrets** - Use `.env` file
2. **Use strong JWT secrets** - Minimum 32 random bytes
3. **Enable HTTPS in production** - Use reverse proxy (nginx)
4. **Validate all inputs** - Prevent SQL injection, XSS
5. **Rate limit endpoints** - Prevent abuse (e.g., verification codes)
6. **Sanitize file uploads** - Check file types, scan for malware
7. **Use CORS whitelist** - Don't allow all origins in production

### Performance

1. **Use connection pooling** - httpx.Client for backend-to-service requests
2. **Enable caching** - Redis for frequently accessed data
3. **Optimize database queries** - Use indexes, avoid N+1 queries
4. **Compress responses** - Enable gzip in nginx
5. **Use CDN for static assets** - Offload avatar images, etc.
6. **Monitor slow queries** - Log queries >100ms

### Scalability

1. **Horizontal scaling** - Run multiple backend instances behind load balancer
2. **Stateless design** - Store session data in Redis, not in-memory
3. **Database connection pooling** - SQLAlchemy default: 5 connections/worker
4. **Asynchronous tasks** - Use Celery for long-running operations
5. **Microservices** - Already split into Backend/LLM/RAG/Avatar

---

**Version**: 2.0.0  
**Last Updated**: 2025-11-18  
**Maintainer**: Virtual Tutor Development Team


