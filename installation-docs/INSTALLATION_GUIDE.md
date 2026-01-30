# Virtual Tutor System - Complete Installation Guide

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Environment Preparation](#environment-preparation)
3. [Backend Configuration](#backend-configuration)
4. [LLM Service Configuration](#llm-service-configuration)
5. [RAG Service Configuration](#rag-service-configuration)
6. [Avatar Manager Configuration](#avatar-manager-configuration)
7. [Lip-Sync Service Configuration](#lip-sync-service-configuration)
8. [Frontend Configuration](#frontend-configuration)
9. [Port Configuration Management](#port-configuration-management)
10. [Complete Startup Process](#complete-startup-process)
11. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Hardware Requirements
- **CPU**: 8 cores or more
- **Memory**: 32GB RAM minimum, 64GB+ recommended
- **GPU**: NVIDIA GPU with 40GB+ VRAM (A100 or A6000 recommended)
  - Must support CUDA 11.8 or higher
- **Storage**: 200GB+ available space (for models and databases)

### Software Requirements
- **Operating System**: Ubuntu 20.04+ / CentOS 7+ / macOS 12+
- **Python**: 3.10 or higher
- **Node.js**: 16.0+ or higher
- **Redis**: 6.0+ or higher
- **Ollama**: Latest version (for LLM)
- **Git**: For cloning the project

### NVIDIA Drivers and CUDA
```bash
# Check NVIDIA drivers
nvidia-smi

# Should display GPU information and CUDA version (11.8+ recommended)
```

### Note on Dockerisation Requirement
According to the course specification, the application is expected to be containerised using Docker unless an explicit exception is granted by the tutor. For this project, we discussed the requirement with our tutor in advance and received confirmation that an exception applies. The Phase I team reported that the hardware resource requirements of the full system are too high to be reliably containerised within the available infrastructure, and the client also confirmed that Dockerisation is not required from their side. As our Phase II work directly extends the existing Phase I codebase and deployment setup, we follow the same non-Docker deployment model, and we document Docker-based containerisation as future work rather than a current deliverable.

---

## Environment Preparation

### Virtual Environment Overview

This project uses **Conda** to manage Python environments for each module. The project requires **3 conda environments**:

| Environment Name | Purpose | Python Version | Modules |
|-----------------|---------|---------------|---------|
| `bread` | Backend service | 3.10 | backend/ |
| `rag` | RAG and LLM services | 3.12 | rag/, llm/ |
| `avatar` | Avatar-related services | 3.10 | avatar-manager/, lip-sync/ |

**Why share environments?**
- LLM and RAG: Share the same dependencies (Milvus client, embedding libraries, etc.)
- Avatar Manager and Lip-Sync: Share WebRTC and video processing dependencies

**Note**: The `scripts/start_all.sh` script depends on these conda environment names, so please follow the naming convention strictly.

### 1. Clone the Project
```bash
git clone https://github.com/mushanshanshan/capstone-project-25t3-9900-virtual-tutor-phase-2.git
cd capstone-project-25t3-9900-virtual-tutor-phase-2
```

### 2. Install Redis
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install redis-server

# macOS
brew install redis

# Start Redis
redis-server &

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

### 3. Install Ollama
```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama

# Start Ollama service
ollama serve &

# Download Qwen model (required for LLM service)
ollama pull qwen2.5:32b-instruct-q4_K_M
# Or use a different model based on your VRAM
```

### 4. System Dependencies
```bash
# Ubuntu/Debian - Poppler (for PDF processing)
sudo apt-get install poppler-utils

# Ubuntu/Debian - Other dependencies
sudo apt-get install ffmpeg libsm6 libxext6

# macOS
brew install poppler ffmpeg
```

---

## Backend Configuration

### 1. Create Conda Virtual Environment

**Recommended: Use conda environment** (consistent with start_all.sh script):

```bash
# Create bread conda environment
conda create -n bread python=3.10
conda activate bread

cd backend
```

**Or use venv** (if not using conda):

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

### 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create `backend/.env` file:

```bash
# ===== Flask Basic Configuration =====
SECRET_KEY=your-super-secret-key-change-this-in-production
# Generate strong key: python -c "import secrets; print(secrets.token_hex(32))"

# ===== JWT Configuration =====
JWT_SECRET_KEY=your-jwt-secret-key-change-this-too
JWT_ACCESS_TOKEN_EXPIRES=18000  # Token expiry (seconds) - 5 hours
JWT_COOKIE_CSRF_PROTECT=false

# ===== Redis Configuration =====
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_TOKEN_TTL_SECONDS=18000  # Token TTL in Redis (seconds)

# ===== Email Service Configuration (SMTP) =====
# Gmail example (requires app-specific password, not account password)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
MAIL_DEFAULT_SENDER=TutorNet <your-email@gmail.com>

# For other email providers, adjust accordingly
# Outlook: smtp-mail.outlook.com, port 587
# QQ Mail: smtp.qq.com, port 465 (SSL)

# ===== Production Environment Configuration (Optional) =====
WORKERS=4                     # Gunicorn worker count
WORKER_CLASS=sync             # Worker type (sync/gevent/eventlet)
THREADS=1                     # Threads per worker
```

**Important Security Notes**:
- ⚠️ Never commit `.env` file to Git
- ✅ Use strong random keys (at least 32 bytes)
- ✅ For Gmail, generate app-specific password: [Google App Passwords](https://myaccount.google.com/apppasswords)

### 4. Initialize Database
```bash
# Database will be auto-created on first run
# To manually initialize:
python -c "from app import create_app; from models.user import db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized successfully')"
```

### 5. Create Log Directory
```bash
mkdir -p logs
```

### 6. Verify Configuration
```bash
# Test Redis connection
python -c "import redis; r = redis.Redis(host='localhost', port=6379); print('Redis OK' if r.ping() else 'Redis Failed')"

# Test email configuration (optional)
python -c "
from flask_mail import Mail, Message
from app import create_app
app = create_app()
mail = Mail(app)
with app.app_context():
    print('Email configuration loaded successfully')
"
```

---

## LLM Service Configuration

### 1. Create Virtual Environment

**Recommended: Use conda environment** (shared with RAG):

```bash
# LLM and RAG share the rag conda environment
conda activate rag  # If rag environment already exists

cd llm
```

**If rag environment doesn't exist yet, create it first**:

```bash
conda create -n rag python=3.12
conda activate rag

# Install RAG dependencies
cd rag
conda install -c conda-forge poppler
pip install -r requirements.txt

# Install LLM dependencies
cd ../llm
pip install -r requirements.txt
```

**Or use venv** (not recommended, inconsistent with start_all.sh):

```bash
cd llm
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Milvus Connection

Edit `llm/milvus_config.py` (if you need to modify defaults):

```python
# Milvus API configuration
MILVUS_API_BASE = "http://localhost:8602"  # RAG service address
DEFAULT_K = 5  # Default retrieval count
REQUEST_TIMEOUT = 10  # Timeout (seconds)
```

### 4. Configure Ollama Model

Ensure Ollama service is running and model is downloaded:

```bash
# Check Ollama service
curl http://localhost:11434/api/tags

# If model not downloaded, download it
ollama pull qwen2.5:32b-instruct-q4_K_M

# Verify model availability
ollama list
```

### 5. Create Checkpoint Database Directory
```bash
# Checkpoint files will be auto-created, but ensure directory is writable
touch checkpoints.db
touch checkpoints_optimized.db
chmod 644 checkpoints*.db
```

### 6. Configure Environment Variables (Optional)

Create `llm/.env` (optional):

```bash
# LLM service port
LLM_PORT=8611

# Gunicorn configuration
WORKERS=4
WORKER_CLASS=sync
THREADS=2

# Ollama configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:32b-instruct-q4_K_M

# Redis configuration (for caching, optional)
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

## RAG Service Configuration

### 1. Create Virtual Environment
```bash
cd rag

# Recommended: use conda (requires poppler)
conda create -n rag python=3.12
conda activate rag

# Or use venv
python3 -m venv venv
source venv/bin/activate
```

### 2. Install System Dependencies
```bash
# Install Poppler (for PDF to image conversion)
conda install -c conda-forge poppler  # If using conda
# or
sudo apt-get install poppler-utils    # Ubuntu/Debian
```

### 3. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure RAG Mode

Edit `rag/config.py`:

```python
# RAG mode configuration
MODE = 0  # 0: Pure text mode (recommended, low GPU consumption)
          # 1: Multimodal mode (requires more GPU resources)

# Database path
EMBEDDED_DB_PATH = "./kb_test.db"  # Milvus Lite database file

# Embedding dimensions
CHUNK_EMBED_DIM = 384  # Text chunk embedding dimension
PAGE_EMBED_DIM = 128   # Page embedding dimension (MODE=1 only)

# Image storage directory
IMG_DIR = "./imgs"  # Page image storage path
```

**Mode Selection Recommendation**:
- **MODE=0 (Pure Text)**: Suitable for production, low GPU VRAM requirement (~4-8GB)
- **MODE=1 (Multimodal)**: Experimental feature, requires more GPU resources (~16-24GB)

### 5. Create Necessary Directories
```bash
mkdir -p imgs
mkdir -p milvus_kb
mkdir -p logs
```

### 6. Initialize Milvus Database
```bash
# Database will be auto-created on first run
# Can be initialized by uploading files
```

### 7. Configure Port (Optional)

Edit the port configuration at the bottom of `rag/app.py`:

```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8602, debug=False)
```

---

## Avatar Manager Configuration

### 1. Create Virtual Environment

**Recommended: Use conda environment** (shared with Lip-Sync):

```bash
# Avatar Manager and Lip-Sync share the avatar conda environment
conda create -n avatar python=3.10
conda activate avatar

cd avatar-manager
```

**Or use venv** (not recommended):

```bash
cd avatar-manager
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Ports and Service Addresses

Edit `avatar-manager/config.py`:

```python
# Avatar Manager configuration
AVATAR_MANAGER_PORT = 8607
AVATAR_BASE_PORT = 8615  # Avatar instance starting port

# Lip-Sync service path
LIP_SYNC_SERVICE_PATH = "/path/to/lip-sync"

# Redis configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379

# GPU configuration
GPU_IDS = [0, 1]  # List of available GPU IDs, adjust based on actual situation
MAX_CONNECTIONS_PER_INSTANCE = 5  # Maximum connections per instance
```

### 4. Create Log Directory
```bash
mkdir -p logs
```

### 5. Configure Avatar Metadata

Ensure there's an avatar configuration file in the `avatar-manager/` directory, or it will be read from the lip-sync service.

---

## Lip-Sync Service Configuration

### 1. Create Virtual Environment

**Recommended: Use conda environment** (shared with Avatar Manager):

```bash
# Use the same avatar conda environment as Avatar Manager
conda activate avatar

cd lip-sync
```

**Or use venv** (not recommended):

```bash
cd lip-sync
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: Lip-Sync has many dependencies, including:
- `torch` (PyTorch with CUDA)
- `opencv-python`
- `mediapipe`
- `aiortc` (WebRTC)
- Other computer vision libraries

### 3. Download Model Files

Lip-Sync requires multiple pretrained models. This is a **critical step** and the models are large (~2-3GB).

#### Method 1: Download Pre-packaged Models (Recommended)

```bash
# Download all models in one package from Google Drive
# URL: https://drive.google.com/file/d/18Cj9hTO5WcByMVQa2Q1OHKmK8JEsqISy/view?usp=sharing

# After downloading, extract to the models folder
cd lip-sync
unzip models.zip -d ./
# Or: tar -xzf models.tar.gz

# Expected structure:
# lip-sync/models/
# ├── musetalk/
# │   ├── musetalk_model.pth
# │   └── ...
# ├── wav2lip/
# │   ├── wav2lip_gan.pth
# │   └── ...
# └── ...
```

#### Method 2: Use MuseTalk's Download Script

If you need to download models separately or update them:

```bash
cd lip-sync

# Clone MuseTalk repository (if needed)
git clone https://github.com/TMElyralab/MuseTalk.git
cd MuseTalk

# Run the official download script
bash ./download_weights.sh

# This will download:
# - VAE weights
# - Face detection models
# - Audio feature extraction models
# - MuseTalk main model

# Move downloaded models to lip-sync/models/
cd ..
mkdir -p models/musetalk
cp -r MuseTalk/models/* models/musetalk/
```

#### Method 3: Manual Download (Advanced Users)

Download individual models from:
- **MuseTalk Models**: https://github.com/TMElyralab/MuseTalk#download-weights
- **Face Detection**: https://github.com/opencv/opencv/tree/master/data/haarcascades
- **Wav2Lip**: https://github.com/Rudrabha/Wav2Lip#getting-the-weights

**Required Models**:
```
lip-sync/models/
├── musetalk/
│   ├── musetalk.json
│   ├── pytorch_model.bin
│   └── sd-vae-ft-mse/
├── wav2lip/
│   └── wav2lip_gan.pth
├── dwpose/
│   ├── dw-ll_ucoco_384.pth
│   └── yolox_l.pth
└── face_detection/
    └── haarcascade_frontalface_default.xml
```

#### Verify Model Download

```bash
cd lip-sync

# Check if all required models exist
python -c "
import os
required_models = [
    'models/musetalk/pytorch_model.bin',
    'models/wav2lip/wav2lip_gan.pth',
    'models/dwpose/dw-ll_ucoco_384.pth'
]
for model in required_models:
    if os.path.exists(model):
        print(f'✓ {model}')
    else:
        print(f'✗ {model} MISSING!')
"
```

**Note**: Model files are large (~2-3GB total). Ensure you have sufficient disk space and a stable internet connection.

### 4. Configure Avatar Data

```bash
# Create avatar data directory
mkdir -p data/avatars

# Avatar configuration file
# Edit data/avatars/index.json to add avatar information
```

Example `data/avatars/index.json`:

```json
{
  "test_yongen": {
    "avatar_id": "test_yongen",
    "clone": false,
    "description": "Default test avatar",
    "status": "active",
    "timbre": "en-US-BrianNeural",
    "tts_model": "edgeTTS",
    "avatar_model": "musetalk",
    "face_image": "data/avatars/test_yongen/face.png",
    "idle_video": "data/avatars/test_yongen/idle.mp4"
  }
}
```

### 5. Configure TTS Services

Edit `lip-sync/tts_config_manager.py` or related configuration files:

```python
# TTS model configuration
TTS_MODELS = {
    "edgeTTS": {
        "port": 8604,
        "active": True
    },
    "tacotron2": {
        "port": 8605,
        "active": False  # Enable as needed
    },
    "CosyVoice": {
        "port": 8609,
        "active": False
    }
}
```

---

## Frontend Configuration

### 1. Install Node.js Dependencies
```bash
cd frontend

npm install
```

### 2. Configure API Endpoints

**Automatic Configuration (Recommended)**:

```bash
# Run from project root directory
cd ..  # Back to project root
python scripts/generate_frontend_config.py
```

This will auto-generate `frontend/src/config.js` based on `scripts/ports_config.py`.

**Manual Configuration**:

Edit `frontend/src/config.js`:

```javascript
const config = {
  // Backend API address
  BACKEND_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8203',
  
  // Avatar Manager address
  AVATAR_MANAGER_URL: 'http://localhost:8607',
  
  // Avatar instance base port
  AVATAR_BASE_PORT: 8615,
  
  // LLM service address
  LLM_URL: 'http://localhost:8611',
  
  // RAG service address
  RAG_URL: 'http://localhost:8602'
};

export default config;
```

### 3. Configure Environment Variables

Create `frontend/.env.development` (development environment):

```bash
# API Base URL
REACT_APP_API_BASE_URL=http://localhost:8203

# Development server configuration
PORT=3000
BROWSER=none  # Disable auto-opening browser (optional)
```

Create `frontend/.env.production` (production environment):

```bash
# Production environment API URL
REACT_APP_API_BASE_URL=https://your-domain.com/api

# Build optimization
GENERATE_SOURCEMAP=false
```

### 4. Configure Proxy (Development Environment, Optional)

If you need to avoid CORS issues during development, edit `frontend/package.json`:

```json
{
  "proxy": "http://localhost:8203"
}
```

---

## Port Configuration Management

### Unified Port Configuration File

All service ports are centrally managed in `scripts/ports_config.py`:

```python
# ===== Service Port Configuration =====

# Frontend
FRONTEND_PORT = 3000

# Backend
BACKEND_PORT = 8203

# LLM Service
LLM_PORT = 8611

# RAG Service
RAG_PORT = 8602

# Avatar Manager
AVATAR_MANAGER_PORT = 8607

# Avatar Instances (dynamically allocated)
AVATAR_BASE_PORT = 8615  # First instance: 8615, second: 8616, ...

# TTS Services
TTS_EDGE_PORT = 8604
TTS_TACOTRON_PORT = 8605
TTS_SOVITS_PORT = 8608
TTS_COSYVOICE_PORT = 8609

# Redis
REDIS_PORT = 6379

# Ollama
OLLAMA_PORT = 11434
```

### Steps to Modify Ports

1. **Edit port configuration**:
   ```bash
   vim scripts/ports_config.py
   # Modify needed ports
   ```

2. **Regenerate frontend configuration**:
   ```bash
   python scripts/generate_frontend_config.py
   ```

3. **Restart related services**:
   ```bash
   # Restart Backend
   cd backend && ./start_production.sh
   
   # Restart Frontend (development mode)
   cd frontend && npm start
   ```

For detailed guide, see: [PORT_CONFIG_GUIDE.md](./PORT_CONFIG_GUIDE.md)

---

## Complete Startup Process

### Method 1: Start Services Individually (Recommended for Development and Debugging)

#### 1. Start Basic Services

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Ollama
ollama serve
```

#### 2. Start Backend Services

```bash
# Terminal 3: Start RAG service
cd rag
conda activate rag  # Use rag conda environment
python app.py

# Terminal 4: Start LLM service
cd llm
conda activate rag  # LLM and RAG share the same environment
gunicorn --config gunicorn_config.py "api_interface_optimized:app"

# Terminal 5: Start Avatar Manager
cd avatar-manager
conda activate avatar  # Use avatar conda environment
python api.py  # Note: it's api.py not manager.py

# Terminal 6: Start Backend
cd backend
conda activate bread  # Use bread conda environment
gunicorn --config gunicorn_config.py "app:create_app()"
```

#### 3. Start Frontend

```bash
# Terminal 7: Start Frontend
cd frontend
npm start
```

#### 4. Access the System

Open browser and visit: `http://localhost:3000`

### Method 2: Use Startup Script (Production Environment)

The project already provides a complete startup script `scripts/start_all.sh`.

**Prerequisites**:
1. All conda environments have been created:
   - `bread` - Backend environment
   - `rag` - RAG and LLM environment (shared)
   - `avatar` - Avatar Manager and Lip-Sync environment

2. Initialize conda (if not configured):
```bash
# Add conda initialization to bash profile
if [ -f /workspace/conda/etc/profile.d/conda.sh ]; then
    source /workspace/conda/etc/profile.d/conda.sh
fi
```

**Create Required Conda Environments**:

```bash
# Backend environment
conda create -n bread python=3.10
conda activate bread
cd backend && pip install -r requirements.txt

# RAG environment (shared with LLM)
conda create -n rag python=3.12
conda activate rag
conda install -c conda-forge poppler  # PDF processing
cd rag && pip install -r requirements.txt
cd ../llm && pip install -r requirements.txt

# Avatar environment
conda create -n avatar python=3.10
conda activate avatar
cd lip-sync && pip install -r requirements.txt
cd ../avatar-manager && pip install -r requirements.txt

# Edge TTS environment (if needed)
conda create -n edge python=3.10
conda activate edge
pip install edge-tts
```

**Run Startup Script**:

```bash
# From project root directory
cd /workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2

# Ensure script is executable
chmod +x scripts/start_all.sh

# Start all services
./scripts/start_all.sh
```

**Script Features**:
- ✅ Automatically reads port configuration from `ports_config.py`
- ✅ Checks all required conda environments
- ✅ Starts all services in correct order
- ✅ Backend uses 4 gevent workers (high concurrency)
- ✅ LLM uses 2 sync workers + Gunicorn (concurrent conversations)
- ✅ Avatar Manager supports 5 concurrent instances
- ✅ Automatically creates log directory
- ✅ Displays service status and access URLs

### Stop All Services

The project already provides a complete stop script `scripts/stop_all.sh`.

**Basic Usage**:

```bash
# Normal stop (graceful shutdown)
./scripts/stop_all.sh

# Force stop (immediate kill)
./scripts/stop_all.sh -f

# Stop and clean logs
./scripts/stop_all.sh -f -c

# Quiet mode stop
./scripts/stop_all.sh -q

# View help
./scripts/stop_all.sh -h
```

**Script Features**:
 RAG → Backend)
- ✅ Graceful shutdown mode (SIGTERM first, then SIGKILL after waiting)
- ✅ Force mode (direct SIGKILL)
- ✅ Checks port release status
- ✅ Optional log cleanup
- ✅ Color output and detailed status reports

**Stop Individual Services**:

```bash
# Stop Backend
pkill -f "gunicorn.*app:create_app"

# Stop LLM
pkill -f "gunicorn.*api_interface_optimized"

# Stop RAG
pkill -f "python.*app.py.*rag"

# Stop Avatar Manager
pkill -f "python3.*api.py.*avatar-manager"

# Stop Frontend
pkill -f "react-scripts start"
```

---

## Troubleshooting

### 1. Redis Connection Failed

**Symptoms**:
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solutions**:
```bash
# Check if Redis is running
redis-cli ping

# If not running, start Redis
redis-server &

# Check port
sudo netstat -tlnp | grep 6379

# Test connection
python -c "import redis; r = redis.Redis(); print(r.ping())"
```

### 2. Ollama Model Not Found

**Symptoms**:
```
Error: model 'qwen2.5:32b-instruct-q4_K_M' not found
```

**Solutions**:
```bash
# Check downloaded models
ollama list

# Download required model
ollama pull qwen2.5:32b-instruct-q4_K_M

# If VRAM insufficient, use smaller model
ollama pull qwen2.5:14b-instruct-q4_K_M
```

### 3. GPU VRAM Insufficient

**Symptoms**:
```
RuntimeError: CUDA out of memory
```

**Solutions**:

**Option A**: Use smaller models
```bash
# LLM: use smaller quantized version
ollama pull qwen2.5:14b-instruct-q4_K_M

# RAG: switch to pure text mode
# Edit rag/config.py
MODE = 0  # instead of 1
```

**Option B**: Reduce concurrent services
```bash
# Only start necessary services
# For example: don't start Avatar/Lip-Sync first, only test chat functionality
```

**Option C**: Multi-GPU allocation
```python
# Edit avatar-manager/config.py
GPU_IDS = [0, 1]  # Use multiple GPUs

# Or specify at startup
CUDA_VISIBLE_DEVICES=0 python rag/app.py &
CUDA_VISIBLE_DEVICES=1 python llm/api_interface_optimized.py &
```

### 4. Port Already in Use

**Symptoms**:
```
OSError: [Errno 98] Address already in use
```

**Solutions**:
```bash
# Find process occupying the port
sudo lsof -i :8203  # Replace with specific port

# Kill process
kill -9 <PID>

# Or modify port configuration
vim scripts/ports_config.py
python scripts/generate_frontend_config.py
```

### 5. Frontend Cannot Connect to Backend (CORS)

**Symptoms**:
```
Access to fetch at 'http://localhost:8203/api/...' blocked by CORS policy
```

**Solutions**:

Check CORS configuration in `backend/app.py`:
```python
from flask_cors import CORS

# Should have this line
CORS(app)

# Or more specific configuration
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

### 6. Email Verification Code Not Sent

**Symptoms**:
```
SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')
```

**Solutions**:

**Gmail Users**:
1. Enable 2-Step Verification
2. Generate app-specific password: https://myaccount.google.com/apppasswords
3. Use app-specific password instead of account password

**QQ Mail Users**:
1. Enable SMTP service
2. Get authorization code
3. Use authorization code as password

Update `backend/.env`:
```bash
MAIL_SERVER=smtp.gmail.com  # or smtp.qq.com
MAIL_PORT=587               # Gmail: 587, QQ: 465
MAIL_USE_TLS=true          # Gmail: true, QQ: false
MAIL_USE_SSL=false         # Gmail: false, QQ: true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password  # Not account password!
```

### 7. Frontend White Screen/Cannot Load

**Symptoms**:
- Browser shows white screen
- Console shows `config is not defined`

**Solutions**:
```bash
# Regenerate configuration file
python scripts/generate_frontend_config.py

# Check if configuration file exists
cat frontend/src/config.js

# Restart frontend
cd frontend
npm start
```

### 8. WebRTC Connection Failed

**Symptoms**:
- Avatar video cannot display
- Console shows WebRTC offer failed

**Solutions**:

1. Check if Avatar Manager is running:
```bash
curl http://localhost:8607/health
```

2. Check if Avatar instance port is allocated:
```bash
redis-cli HGETALL "avatar:user_mappings"
```

3. Check firewall rules:
```bash
# Allow WebRTC port range
sudo ufw allow 8615:8700/tcp
sudo ufw allow 8615:8700/udp
```

### 9. Database Locked Error

**Symptoms**:
```
sqlite3.OperationalError: database is locked
```

**Solutions**:

**Option A**: Reduce Gunicorn workers
```python
# backend/gunicorn_config.py or llm/gunicorn_config.py
workers = 1  # Temporary solution, not recommended for production
```

**Option B**: Use gevent workers (recommended)
```python
# gunicorn_config.py
worker_class = 'gevent'
workers = 4

# Install gevent
pip install gevent
```

**Option C**: Switch to PostgreSQL (best for production)

### 10. File Upload Failed

**Symptoms**:
```
413 Request Entity Too Large
```

**Solutions**:

Increase upload limit:

**Backend**:
```python
# backend/app.py
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
```

**Nginx (if used)**:
```nginx
client_max_body_size 50M;
```

---

## Verify Installation

### Health Check Checklist

```bash
# 1. Redis
redis-cli ping
# Expected: PONG

# 2. Backend
curl http://localhost:8203/api/health
# Expected: {"status": "healthy", ...}

# 3. LLM Service
curl http://localhost:8611/health
# Expected: {"status": "healthy"}

# 4. RAG Service
curl http://localhost:8602/health
# Expected: {"status": "ok"}

# 5. Avatar Manager
curl http://localhost:8607/health
# Expected: {"status": "healthy"}

# 6. Frontend
curl http://localhost:3000
# Expected: HTML content

# 7. Ollama
ollama list
# Expected: Display list of downloaded models
```

### End-to-End Testing

1. **Registration/Login Test**:
   ```bash
   # Open browser
   # Visit http://localhost:3000
   # Click "Register" to register new account
   # Check email for verification code
   # Complete registration and login
   ```

2. **Chat Function Test**:
   ```bash
   # After login, send message:
   # "What is machine learning?"
   # Should see streaming response
   ```

3. **File Upload Test**:
   ```bash
   # Upload a PDF file
   # Wait for "File uploaded and indexed" prompt
   # Ask questions about the file
   ```

4. **Avatar Test** (requires GPU):
   ```bash
   # Select an Avatar
   # Click "Play" button
   # Should see Avatar video stream
   # Send message, Avatar should speak
   ```

---

## Performance Optimization Recommendations

### 1. Database Optimization
```bash
# SQLite optimization (development environment)
# backend/config.py
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Production environment recommends using PostgreSQL
```

### 2. Redis Persistence
```bash
# Edit redis.conf
appendonly yes
appendfsync everysec
```

### 3. Gunicorn Configuration
```python
# Adjust based on CPU cores
workers = multiprocessing.cpu_count() * 2 + 1

# Use gevent for handling concurrency
worker_class = 'gevent'
worker_connections = 1000
```

### 4. Frontend Build Optimization
```bash
# Production environment build
cd frontend
npm run build

# Deploy using serve
npm install -g serve
serve -s build -l 3000
```

---

## Security Checklist

- [ ] ✅ Changed all default keys (SECRET_KEY, JWT_SECRET_KEY)
- [ ] ✅ `.env` file added to `.gitignore`
- [ ] ✅ Email service using app-specific password
- [ ] ✅ Redis set password protection (production)
- [ ] ✅ Firewall configured correctly, only necessary ports open
- [ ] ✅ HTTPS enabled (production)
- [ ] ✅ CORS configured with whitelist domains (production)
- [ ] ✅ File upload limited size and type
- [ ] ✅ Database backed up regularly
- [ ] ✅ Log files rotated regularly

---

## Getting Help

If you encounter unresolved issues:

1. **Check Logs**:
   ```bash
   # Backend
   tail -f backend/logs/backend_error.log
   
   # LLM
   tail -f llm/logs/llm_error.log
   
   # RAG
   tail -f rag/logs/rag.log
   ```

2. **Check GitHub Issues**: [Project Issues Page](https://github.com/mushanshanshan/capstone-project-25t3-9900-virtual-tutor-phase-2/issues)

3. **Refer to Module Documentation**:
   - [Backend README](./backend/README.md)
   - [LLM README](./llm/README.md)
   - [RAG README](./rag/README.md)
   - [Frontend README](./frontend/README.md)

---

## Appendix

### A. Complete Environment Variables List

#### Backend (`backend/.env`)
```bash
SECRET_KEY=<random-key>
JWT_SECRET_KEY=<random-key>
JWT_ACCESS_TOKEN_EXPIRES=18000
JWT_COOKIE_CSRF_PROTECT=false
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_TOKEN_TTL_SECONDS=18000
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=<your-email>
MAIL_PASSWORD=<app-password>
MAIL_DEFAULT_SENDER=TutorNet <your-email>
WORKERS=4
WORKER_CLASS=sync
THREADS=1
```

#### Frontend (`.env.development` / `.env.production`)
```bash
REACT_APP_API_BASE_URL=http://localhost:8203
PORT=3000
GENERATE_SOURCEMAP=false  # Production only
```

### B. Default Port List

| Service | Port | Protocol |
|---------|------|----------|
| Frontend | 3000 | HTTP |
| Backend | 8203 | HTTP |
| LLM Service | 8611 | HTTP |
| RAG Service | 8602 | HTTP |
| Avatar Manager | 8607 | HTTP |
| Avatar Instance 1 | 8615 | HTTP/WebRTC |
| Avatar Instance 2 | 8616 | HTTP/WebRTC |
| ... | ... | ... |
| Edge-TTS | 8604 | HTTP |
| Tacotron | 8605 | HTTP |
| SoVITS | 8608 | HTTP |
| CosyVoice | 8609 | HTTP |
| Redis | 6379 | TCP |
| Ollama | 11434 | HTTP |

### C. Quick Command Reference

```bash
# Start all services
./scripts/start_all.sh

# Stop all services
./scripts/stop_all.sh

# Restart individual service (using correct conda environment)
# Backend
cd backend && pkill -f gunicorn && conda activate bread && gunicorn --config gunicorn_config.py "app:create_app()" &

# LLM
cd llm && pkill -f "api_interface_optimized" && conda activate rag && gunicorn --config gunicorn_config.py "api_interface_optimized:app" &

# RAG
cd rag && pkill -f "app.py.*rag" && conda activate rag && python app.py &

# Avatar Manager
cd avatar-manager && pkill -f "api.py" && conda activate avatar && python api.py &

# View all logs
tail -f backend/logs/*.log llm/logs/*.log rag/logs/*.log

# Clean database (use with caution!)
rm backend/instance/app.db llm/checkpoints*.db rag/kb_test.db

# Regenerate frontend configuration
python scripts/generate_frontend_config.py

# Test API connectivity
curl http://localhost:8203/api/health
curl http://localhost:8611/health
curl http://localhost:8602/health
```

---
