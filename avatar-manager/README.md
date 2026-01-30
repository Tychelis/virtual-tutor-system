# Avatar Manager - Multi-Instance Management System

## 🎯 Overview

Avatar Manager is a production-grade service that orchestrates multiple concurrent avatar instances with intelligent resource management, enabling seamless multi-user support through instance pooling, dynamic port allocation, GPU memory optimization, and automatic lifecycle management.

**Current Configuration**: Maximum 5 concurrent avatars with auto-scaling and load balancing

## ✨ Key Features

### Core Capabilities
- **Instance Pooling & Sharing**: Intelligent avatar instance reuse when multiple users select the same avatar, reducing resource overhead
- **Dynamic Port Allocation**: Thread-safe port assignment with race condition prevention (8615-8619 range)
- **GPU Memory Management**: 
  - Real-time VRAM monitoring using NVML (pynvml)
  - Automatic GPU selection based on available memory
  - Primary GPU 1 (avoiding GPU 0 used by LLM services)
  - Backup GPU 0 for failover scenarios
- **Thread-Safe Operations**: 
  - Mutex locks protecting port allocation and instance creation
  - Atomic operations preventing concurrent conflicts
  - Race condition mitigation in multi-threaded environments
- **Health Monitoring**: 
  - Periodic health checks every 60 seconds
  - Process status verification
  - Socket binding validation with active polling
  - Auto-restart on failures with configurable timeout
- **Graceful Shutdown**: 
  - Connection counting per instance
  - Graceful termination with proper cleanup
  - Process tree termination (parent + all children)
  - 3-second GPU memory release wait time
- **Idle Timeout Management**: 
  - Automatic cleanup of unused instances after 30 minutes
  - Activity tracking per instance
  - Connection-safe shutdown (never closes active instances)
- **TTS Service Integration**:
  - On-demand TTS service startup based on avatar configuration
  - Multi-model support (EdgeTTS, Tacotron2, CosyVoice, SoVITS)
  - Automatic port mapping for different TTS models
  - Configuration-driven TTS selection per avatar

## 📁 File Structure

```
avatar-manager/
├── config.py                      # Configuration management
│                                  # - Port configuration (centralized)
│                                  # - GPU allocation settings
│                                  # - Timeouts and thresholds
│                                  # - Conda environment paths
├── manager.py                     # Core management logic
│                                  # - AvatarInstance class (instance metadata)
│                                  # - AvatarManager class (orchestration)
│                                  # - Port allocation with thread safety
│                                  # - GPU memory detection and allocation
│                                  # - Process lifecycle management
│                                  # - Instance pooling and sharing
│                                  # - Health checks and auto-restart
├── api.py                         # Flask REST API server
│                                  # - RESTful endpoints
│                                  # - Background tasks thread
│                                  # - CORS enabled for frontend
│                                  # - Request validation and error handling
├── monitor.py                     # GPU monitoring service
│                                  # - NVML integration (pynvml)
│                                  # - Real-time GPU stats collection
│                                  # - Memory/temperature/utilization tracking
│                                  # - Alert generation for thresholds
├── test_manager.py                # Comprehensive test suite
│                                  # - Basic functionality tests
│                                  # - Concurrent operation tests
│                                  # - Integration tests
├── test_concurrent_allocation.py  # Port allocation stress tests
├── start.sh                       # Service startup script
├── logs/                          # Log directory
│   ├── avatar_manager.log         # Main service logs
│   └── avatar_<id>_<port>.log     # Per-instance logs
└── README.md                      # Documentation (this file)
```

## 🏗️ Architecture & Technical Implementation

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                        │
│                                                             │
│  User selects avatar → API request to Backend              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend (Flask)                           │
│                                                             │
│  • User authentication & session management                │
│  • Avatar selection & WebRTC setup                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Avatar Manager (This Service)                  │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   API Layer │  │   Manager   │  │  Monitor    │       │
│  │   (api.py)  │  │ (manager.py)│  │(monitor.py) │       │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
│         │                │                 │               │
│         └────────────────┴─────────────────┘               │
│                          │                                 │
│              ┌───────────┴───────────┐                    │
│              │  Instance Pool        │                    │
│              │  ┌──────────────────┐ │                    │
│              │  │ Avatar Instance  │ │                    │
│              │  │ - ID, Port, GPU  │ │                    │
│              │  │ - Process, PID   │ │                    │
│              │  │ - Connections    │ │                    │
│              │  └──────────────────┘ │                    │
│              └───────────────────────┘                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  Lip-Sync Service                           │
│                                                             │
│  • MuseTalk model for avatar animation                     │
│  • WebRTC transport for real-time streaming                │
│  • TTS integration (EdgeTTS/Tacotron2/etc)                 │
│  • Per-instance process isolation                          │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. AvatarInstance Class
Represents a single avatar process instance with metadata:
```python
class AvatarInstance:
    - avatar_id: str           # Unique instance ID (e.g., "g_user_1")
    - real_avatar_name: str    # Actual avatar name (e.g., "g")
    - port: int                # WebRTC listening port
    - gpu_id: int              # Allocated GPU device ID
    - process: subprocess.Popen # Process handle
    - pid: int                 # Process ID
    - start_time: datetime     # Launch timestamp
    - last_activity: datetime  # Last activity timestamp
    - connections: int         # Active connection count
```

#### 2. AvatarManager Class
Central orchestration engine with thread-safe operations:
- **Instance Registry**: Dict[str, AvatarInstance] for fast lookups
- **Avatar Mapping**: Dict[str, str] for real_name → instance_id resolution
- **Port Allocation**: 
  - Thread mutex lock protecting allocation
  - Set of allocating ports to prevent races
  - System-level port availability check using psutil
  - Socket binding verification with active polling
- **GPU Allocation**:
  - NVML-based memory inspection
  - Free memory threshold checking (11GB default)
  - Automatic fallback to backup GPU
  - Round-robin when NVML unavailable

#### 3. Port Allocation Algorithm
**Problem**: Prevent concurrent requests from allocating the same port

**Solution**: Multi-layer validation with locks
```python
def _allocate_port(self, exclude_port=None) -> int:
    with self._lock:  # Critical section
        # 1. Collect used ports from manager registry
        used_ports = {inst.port for inst in self.instances.values()}
        
        # 2. Add ports currently being allocated
        used_ports.update(self._allocating_ports)
        
        # 3. Iterate through port range
        for i in range(MAX_AVATARS):
            port = BASE_PORT + i
            
            # 4. Skip if in manager registry
            if port in used_ports:
                continue
            
            # 5. Check system-level availability (psutil)
            if not self._is_port_available(port):
                continue
            
            # 6. Double-check manager registry (race prevention)
            if port in {inst.port for inst in self.instances.values()}:
                continue
            
            # 7. Mark as allocating immediately
            self._allocating_ports.add(port)
            return port
```

#### 4. Socket Binding Verification
**Problem**: subprocess may crash before binding to port, leading to dangling allocations

**Solution**: Active polling with timeout
```python
def _wait_for_port_binding(self, port: int, timeout: int = 30) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Attempt to connect to the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            if result == 0:  # Connection successful = port is listening
                return True
        except Exception:
            pass
        
        time.sleep(0.1)  # 100ms poll interval
    
    return False  # Timeout reached
```

#### 5. Instance Pooling & Sharing
**Feature**: Multiple users can share the same avatar instance

**Implementation**:
- `avatar_map`: Maps real avatar name to instance_id
- When user requests avatar "g":
  1. Check if "g" exists in avatar_map
  2. If yes, retrieve existing instance and increment connections
  3. If no, create new instance and register in avatar_map
- On disconnect:
  1. Decrement connections counter
  2. Only stop instance when connections reach 0

#### 6. Graceful Shutdown with Process Tree Termination
**Problem**: Avatar processes spawn child processes (TTS, WebRTC, etc.)

**Solution**: Recursive process tree termination
```python
def stop(self, avatar_id: str, force: bool = True):
    # 1. Get process handle
    parent = psutil.Process(instance.pid)
    
    # 2. Find all children recursively
    children = parent.children(recursive=True)
    
    # 3. Kill all children first
    for child in children:
        os.kill(child.pid, signal.SIGKILL)
    
    # 4. Kill parent process
    os.kill(instance.pid, signal.SIGKILL)
    
    # 5. Wait 3 seconds for GPU memory release
    time.sleep(3)
    
    # 6. Cleanup registry and log files
    del self.instances[avatar_id]
    del self.avatar_map[real_avatar_name]
    os.remove(log_file_path)
```

#### 7. TTS Service On-Demand Startup
**Feature**: Automatically start required TTS service based on avatar config

**Implementation**:
```python
def _check_and_start_tts_service(self, tts_model: str) -> bool:
    # 1. Get TTS port for model (EdgeTTS=5002, Tacotron=5005, etc)
    tts_port = get_tts_port_for_model(tts_model)
    
    # 2. Check if port is already listening
    for conn in psutil.net_connections():
        if conn.laddr.port == tts_port and conn.status == LISTEN:
            return True  # Already running
    
    # 3. Read model_info.json for TTS config
    with open('tts/model_info.json') as f:
        model_infos = json.load(f)
    
    # 4. Build startup command with conda environment
    cmd = f"source conda.sh && python {server_path} --port {tts_port}"
    
    # 5. Launch TTS service in background
    subprocess.Popen(cmd, shell=True)
    
    # 6. Wait for port to become available
    for i in range(30):
        if check_port_listening(tts_port):
            return True
        time.sleep(1)
    
    return False
```

## 🚀 Quick Start

### Prerequisites

1. **Python Environment**: Python 3.8+
2. **GPU**: NVIDIA GPU with CUDA support (optional but recommended)
3. **Conda**: Miniconda or Anaconda installed at `/workspace/conda`
4. **Lip-Sync Service**: Must be installed in adjacent directory (`../lip-sync`)
5. **Avatar Data**: Avatar models in `../lip-sync/data/avatars/`

### 1. Install Dependencies

```bash
# Install Python packages
pip install flask flask-cors psutil nvidia-ml-py3

# Verify pynvml installation (GPU monitoring)
python -c "import pynvml; pynvml.nvmlInit(); print('NVML OK')"

# Check GPU availability
nvidia-smi
```

### 2. Configure Environment

Edit `config.py` to match your setup:
```python
# Adjust GPU settings
PRIMARY_GPU = 1      # Your primary GPU ID
BACKUP_GPU = 0       # Fallback GPU

# Adjust capacity
MAX_AVATARS = 5      # Max concurrent instances

# Adjust paths if needed
LIP_SYNC_PATH = '/path/to/lip-sync'
CONDA_ENV = '/path/to/conda/envs/avatar'
```

### 3. Start Service

```bash
cd avatar-manager

# Option 1: Using startup script
./start.sh

# Option 2: Direct Python execution
python3 api.py

# Option 3: Background daemon
nohup python3 api.py > logs/api.log 2>&1 &
```

Service will start on port **8607** (configured in `ports_config.py`).

### 4. Verify Service Health

```bash
# Check API health
curl http://localhost:8607/health

# Expected output:
# {
#   "status": "healthy",
#   "service": "avatar-manager",
#   "version": "1.0.0"
# }

# View system status
curl http://localhost:8607/status | jq .
```

### 5. Run Tests

```bash
# Basic functionality test
python3 test_manager.py

# Health check only
python3 test_manager.py health

# View current status
python3 test_manager.py status

# List running avatars
python3 test_manager.py list

# Start specific avatar (assuming "test_yongen" exists)
python3 test_manager.py start test_yongen_user_1 test_yongen

# Stop avatar
python3 test_manager.py stop test_yongen_user_1

# Concurrent stress test
python3 test_manager.py concurrent

# Port allocation stress test
python3 test_concurrent_allocation.py
```

## 📡 API Endpoints

### Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-11-17T10:30:00"
}
```

### Start Avatar (with Instance Pooling)
```bash
POST /avatar/start
Content-Type: application/json

{
  "avatar_id": "g_user_1",      # Unique instance ID
  "avatar_name": "g"            # Real avatar name (can be shared)
}
```

**Key Features:**
- **Instance Reuse**: If another user already uses avatar "g", returns the same instance
- **Connection Counting**: Tracks number of active connections per instance
- **Auto-Start**: Launches new instance only if no existing instance for that avatar
- **Port Allocation**: Dynamically assigns available ports (8615-8619)

**Response:**
```json
{
  "status": "success",
  "message": "Avatar reused successfully",
  "data": {
    "avatar_id": "g_user_1",
    "port": 8615,
    "gpu": 1,
    "webrtc_url": "http://localhost:8615/offer",
    "connections": 2,
    "is_new": false
  }
}
```

### Disconnect Avatar (Graceful Shutdown)
```bash
POST /avatar/disconnect
Content-Type: application/json

{
  "avatar_name": "g"    # Real avatar name
}
```

**Behavior:**
- Decrements connection count by 1
- Only stops instance when connections reach 0
- Enables safe multi-user disconnection

### Stop Avatar (Force Terminate)
```bash
POST /avatar/stop
Content-Type: application/json

{
  "avatar_id": "test_yongen",
  "force": true    # true=immediate, false=check connections
}
```

### List All Avatars
```bash
GET /avatar/list
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "avatar_id": "g_user_1",
      "real_avatar_name": "g",
      "port": 8615,
      "gpu": 1,
      "running": true,
      "connections": 2,
      "uptime_seconds": 3600
    }
  ]
}
```

### Get System Status
```bash
GET /status
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "manager": {
      "running": 2,
      "max": 5,
      "available": 3
    },
    "gpu": [
      {
        "gpu_id": 1,
        "name": "NVIDIA A100",
        "memory": {
          "total_gb": 40.0,
          "used_gb": 12.5,
          "free_gb": 27.5,
          "usage_percent": 31.3
        }
      }
    ]
  }
}
```

### Get Avatar Info
```bash
GET /avatar/info/<avatar_id>
```

### Restart Avatar
```bash
POST /avatar/restart
Content-Type: application/json

{
  "avatar_id": "test_yongen"
}
```

### Stop All Avatars
```bash
POST /avatar/stop-all
```

## ⚙️ Configuration

### Core Configuration (`config.py`)

```python
# ============================================================================
# Capacity & Resource Limits
# ============================================================================
MAX_AVATARS = 5          # Maximum concurrent avatar instances
                         # Recommendation: 5 instances * ~4GB VRAM = 20GB total

# ============================================================================
# GPU Allocation Strategy
# ============================================================================
PRIMARY_GPU = 1          # Primary GPU ID (1 = second GPU)
                         # Note: GPU 0 typically reserved for LLM services
BACKUP_GPU = 0           # Fallback GPU when primary is full
                         # Manager automatically selects GPU with most free VRAM

# ============================================================================
# Port Configuration (Centralized)
# ============================================================================
# All ports imported from scripts/ports_config.py for consistency
API_PORT = AVATAR_MANAGER_API_PORT  # 8607 - Manager REST API
BASE_PORT = AVATAR_BASE_PORT        # 8615 - Avatar instance base port
                                     # Instances use: 8615, 8616, 8617, 8618, 8619

# ============================================================================
# Avatar Startup Configuration
# ============================================================================
AVATAR_CONFIG = {
    'transport': 'webrtc',     # Transport protocol (webrtc/rtmp)
    'model': 'musetalk',       # Avatar animation model
    'max_session': 100,        # Max WebRTC sessions per instance
    'tts': 'edgetts',          # Default TTS engine (overridden by avatar config)
    'tts_server': f'http://127.0.0.1:{TTS_PORT}'  # TTS service endpoint
}

# ============================================================================
# Timeout & Lifecycle Management
# ============================================================================
STARTUP_TIMEOUT = 30           # Avatar process startup timeout (seconds)
                               # Includes: process launch + socket binding
IDLE_TIMEOUT = 1800            # Auto-close idle instances after 30 minutes
                               # Set to 0 to disable idle cleanup
HEALTH_CHECK_INTERVAL = 60     # Background health check frequency (seconds)

# ============================================================================
# Paths & Environment
# ============================================================================
LIP_SYNC_PATH = '../lip-sync'                      # Lip-sync service directory
AVATAR_DATA_PATH = '../lip-sync/data/avatars'      # Avatar model storage
CONDA_INIT = '/workspace/conda/etc/profile.d/conda.sh'  # Conda initialization script
CONDA_ENV = '/workspace/conda/envs/avatar'         # Conda environment path

# ============================================================================
# Logging
# ============================================================================
LOG_FILE = 'logs/avatar_manager.log'  # Main service log
LOG_LEVEL = 'INFO'                     # DEBUG/INFO/WARNING/ERROR

# Per-instance logs: logs/avatar_{id}_{port}.log
# Example: logs/avatar_g_user_1_8615.log

# ============================================================================
# Monitoring
# ============================================================================
ENABLE_MONITORING = True       # Enable GPU monitoring (requires pynvml)
MONITOR_INTERVAL = 10          # GPU stats collection interval (seconds)
```

### Port Management Strategy

**Centralized Configuration:**
- All ports defined in `scripts/ports_config.py`
- Single source of truth for all services
- Automatic propagation to frontend via `generate_frontend_config.py`

**Port Ranges:**
```
Service                 Port Range       Purpose
-----------------------------------------------------
Avatar Manager API      8607             REST API endpoints
Avatar Instances        8615-8619        WebRTC per-instance (5 slots)
TTS EdgeTTS             5002             EdgeTTS service
TTS Tacotron2           5005             Tacotron2 service
TTS CosyVoice           5006             CosyVoice service
TTS SoVITS              5007             SoVITS service
Backend API             8000             Main backend service
Frontend Dev Server     3000             React dev server
LLM Service             8100             Language model API
```

**Port Conflict Resolution:**
- Manager checks system-level port availability via `psutil`
- Thread locks prevent concurrent allocation conflicts
- Socket binding verification ensures process actually listening
- See [PORT_CONFIG_GUIDE.md](../PORT_CONFIG_GUIDE.md) for details

### Avatar-Specific Configuration

Each avatar can have custom settings in `{AVATAR_DATA_PATH}/{avatar_name}/config.json`:

```json
{
  "tts_model": "edgeTTS",           // TTS engine: edgeTTS/Tacotron2/CosyVoice/SoVITS
  "timbre": "en-US-BrianNeural",    // Voice timbre (TTS-specific)
  "avatar_model": "musetalk",       // Animation model
  "transport": "webrtc",            // Transport protocol
  "max_session": 100                // Concurrent session limit
}
```

**TTS Model Name Normalization:**
- `TacoTron2`, `TacoTron`, `tacotron2` → `tacotron`
- `EdgeTTS`, `edgeTTS`, `edge` → `edgetts`
- `CosyVoice`, `cosyvoice2` → `cosyvoice`
- `SoVITS`, `GPT-SoVITS` → `sovits`

**TTS Port Mapping:**
```python
def get_tts_port_for_model(tts_model: str) -> int:
    mapping = {
        'edgetts': 5002,
        'tacotron': 5005,
        'cosyvoice': 5006,
        'sovits': 5007
    }
    return mapping.get(tts_model, 5002)  # Default to EdgeTTS
```

## 📊 Monitoring & Health Checks

### Real-time Monitoring

```bash
curl http://localhost:8607/status
```

**Monitored Metrics:**
- Avatar instance count and availability
- GPU memory usage per GPU
- Individual instance health status
- Connection counts per avatar
- Uptime statistics

### Automatic Health Checks

- **Frequency**: Every 60 seconds (configurable)
- **Port Availability**: Checks if avatar ports respond
- **Process Status**: Verifies avatar processes are running
- **Auto-Restart**: Automatically restarts failed instances
- **GPU Memory**: Monitors VRAM to prevent OOM

### Idle Instance Cleanup

- **Idle Detection**: Tracks last activity time per instance
- **Auto-Shutdown**: Closes avatars idle for 30+ minutes
- **Connection-Safe**: Never closes avatars with active connections
- **Configurable**: Set `IDLE_TIMEOUT = 0` to disable

## 🔧 Troubleshooting

### Issue 1: Startup Failure

**Possible Causes:**
- Incorrect lip-sync path
- Avatar ID doesn't exist
- GPU unavailable
- Conda environment not found

**Solutions:**
```bash
# Verify lip-sync path
ls ../lip-sync/app.py

# Check available avatars
ls ../lip-sync/data/avatars/

# Check GPU status
nvidia-smi

# Verify conda environment
conda env list | grep avatar
```

### Issue 2: Port Already in Use

**Solutions:**
```bash
# Option 1: Modify BASE_PORT or API_PORT in ports_config.py
# Then regenerate frontend config
python scripts/generate_frontend_config.py

# Option 2: Kill process using the port
lsof -i :8607
kill <PID>
```

### Issue 3: GPU Out of Memory

**Solutions:**
- Reduce `MAX_AVATARS` in config.py
- Use GPU 1 instead of GPU 0 (set `PRIMARY_GPU = 1`)
- Close other GPU processes
- Enable model quantization
- Monitor with `nvidia-smi` before starting

### Issue 4: Instance Won't Stop

**Cause:** Zombie processes or untracked PIDs

**Solution:**
```bash
# Force kill all avatar processes
pkill -f "app.py.*--avatar_id"

# Or use stop-all endpoint
curl -X POST http://localhost:8607/avatar/stop-all
```

### Issue 5: Redis Connection Error

**Cause:** Backend expects Redis for user-avatar mappings

**Solution:**
```bash
# Start Redis if not running
redis-server &

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

## 📝 Important Notes

1. **Avatar Names**: Must exist in `lip-sync/data/avatars/` directory
2. **Port Range**: Uses BASE_PORT to BASE_PORT+MAX_AVATARS-1 (8615-8619)
3. **GPU Allocation**: 
   - Primary GPU 1 (avoid GPU 0 used by LLM)
   - Backup GPU 0 if GPU 1 unavailable
4. **Resource Requirements**: 
   - ~4GB VRAM per avatar instance
   - ~5GB RAM per avatar instance
   - Ensure 20GB+ free VRAM for 5 concurrent avatars
5. **Instance Pooling**:
   - Same `avatar_name` = reused instance
   - Different `avatar_id` but same `avatar_name` = shared instance
   - Connection counting prevents premature shutdown
6. **Thread Safety**:
   - Port allocation uses locks to prevent race conditions
   - Redis Hash ensures multi-worker consistency

## 🎓 Usage Examples

### Python Client Example

```python
import requests

BASE_URL = "http://localhost:8607"

# Start avatar with instance pooling
response = requests.post(
    f"{BASE_URL}/avatar/start",
    json={
        "avatar_id": "test_yongen_user_1",  # Unique instance ID
        "avatar_name": "test_yongen"         # Real avatar name
    }
)

if response.status_code == 200:
    data = response.json()['data']
    print(f"Avatar Started:")
    print(f"  Instance ID: {data['avatar_id']}")
    print(f"  Port: {data['port']}")
    print(f"  WebRTC URL: {data['webrtc_url']}")
    print(f"  Connections: {data['connections']}")
    print(f"  Is New: {data['is_new']}")

# Check system status
response = requests.get(f"{BASE_URL}/status")
status = response.json()['data']
print(f"Running: {status['manager']['running']}/{status['manager']['max']}")

# Graceful disconnect (decrements connection count)
requests.post(
    f"{BASE_URL}/avatar/disconnect",
    json={"avatar_name": "test_yongen"}
)

# Force stop (ignores connections)
requests.post(
    f"{BASE_URL}/avatar/stop",
    json={"avatar_id": "test_yongen_user_1", "force": True}
)
```

### cURL Examples

```bash
# Start avatar
curl -X POST http://localhost:8607/avatar/start \
  -H "Content-Type: application/json" \
  -d '{
    "avatar_id": "test_yongen_user_1",
    "avatar_name": "test_yongen"
  }'

# Get status
curl http://localhost:8607/status | jq .

# List all avatars
curl http://localhost:8607/avatar/list | jq .

# Disconnect gracefully
curl -X POST http://localhost:8607/avatar/disconnect \
  -H "Content-Type: application/json" \
  -d '{"avatar_name": "test_yongen"}'

# Force stop
curl -X POST http://localhost:8607/avatar/stop \
  -H "Content-Type: application/json" \
  -d '{"avatar_id": "test_yongen_user_1", "force": true}'
```

### Multi-User Scenario Example

```python
# User 1 starts avatar "g"
requests.post(BASE_URL + "/avatar/start", json={
    "avatar_id": "g_user_1",
    "avatar_name": "g"
})
# Result: New instance on port 8615, connections=1

# User 2 starts same avatar "g"
requests.post(BASE_URL + "/avatar/start", json={
    "avatar_id": "g_user_2", 
    "avatar_name": "g"
})
# Result: Reuses port 8615, connections=2

# User 1 disconnects
requests.post(BASE_URL + "/avatar/disconnect", json={
    "avatar_name": "g"
})
# Result: connections=1, instance still running

# User 2 disconnects
requests.post(BASE_URL + "/avatar/disconnect", json={
    "avatar_name": "g"
})
# Result: connections=0, instance auto-closes after idle timeout
```

## � Backend Integration

### Integration with Flask Backend

Modify `backend/routes/avatar.py` to use Avatar Manager:

```python
import requests
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

avatar_bp = Blueprint('avatar', __name__)
AVATAR_MANAGER_URL = "http://localhost:8607"

@avatar_bp.route("/avatar/connect", methods=["POST"])
@jwt_required()
def connect_avatar():
    """Connect user to avatar instance with pooling support"""
    user_id = get_jwt_identity()
    avatar_name = request.json.get('avatar_name')  # Real avatar name (e.g., "g")
    
    if not avatar_name:
        return jsonify({'status': 'error', 'message': 'avatar_name required'}), 400
    
    # Generate unique instance ID for this user-avatar combination
    instance_id = f"{avatar_name}_user_{user_id}"
    
    try:
        # Request Avatar Manager to start/reuse instance
        response = requests.post(
            f"{AVATAR_MANAGER_URL}/avatar/start",
            json={
                'avatar_id': instance_id,      # Unique instance ID
                'avatar_name': avatar_name     # Real avatar name (for pooling)
            },
            timeout=35  # Slightly longer than STARTUP_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()['data']
            
            # Store user-avatar mapping in database/Redis
            save_user_avatar_mapping(user_id, instance_id, data['port'])
            
            return jsonify({
                'status': 'success',
                'port': data['port'],
                'webrtc_url': data['webrtc_url'],
                'connections': data['connections'],
                'is_new_instance': data.get('is_new', True)
            })
        else:
            error = response.json()
            return jsonify({
                'status': 'error',
                'message': error.get('message', 'Failed to start avatar')
            }), 400
            
    except requests.Timeout:
        return jsonify({
            'status': 'error',
            'message': 'Avatar startup timeout (30s)'
        }), 504
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Avatar Manager unreachable: {str(e)}'
        }), 503


@avatar_bp.route("/avatar/disconnect", methods=["POST"])
@jwt_required()
def disconnect_avatar():
    """Gracefully disconnect from avatar (decrements connection count)"""
    user_id = get_jwt_identity()
    avatar_name = request.json.get('avatar_name')
    
    try:
        # Request graceful disconnect (not force stop)
        response = requests.post(
            f"{AVATAR_MANAGER_URL}/avatar/disconnect",
            json={'avatar_name': avatar_name},
            timeout=10
        )
        
        if response.status_code == 200:
            # Remove user-avatar mapping
            remove_user_avatar_mapping(user_id)
            return jsonify({'status': 'success'})
        else:
            error = response.json()
            return jsonify({
                'status': 'error',
                'message': error.get('message')
            }), 400
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 503


@avatar_bp.route("/avatar/status", methods=["GET"])
@jwt_required()
def get_avatar_status():
    """Get current avatar status for user"""
    user_id = get_jwt_identity()
    
    # Retrieve user's avatar mapping
    mapping = get_user_avatar_mapping(user_id)
    if not mapping:
        return jsonify({'status': 'no_avatar'}), 200
    
    try:
        response = requests.get(
            f"{AVATAR_MANAGER_URL}/avatar/info/{mapping['instance_id']}",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()['data']
            return jsonify({
                'status': 'connected',
                'avatar': data
            })
        else:
            return jsonify({'status': 'disconnected'}), 200
            
    except Exception:
        return jsonify({'status': 'error'}), 503


# Helper functions (implement based on your storage choice)
def save_user_avatar_mapping(user_id, instance_id, port):
    """Store user-avatar mapping in Redis/Database"""
    # Example using Redis:
    # redis_client.hset(f'user_avatar:{user_id}', mapping={
    #     'instance_id': instance_id,
    #     'port': port,
    #     'connected_at': datetime.now().isoformat()
    # })
    pass

def remove_user_avatar_mapping(user_id):
    """Remove user-avatar mapping"""
    # redis_client.delete(f'user_avatar:{user_id}')
    pass

def get_user_avatar_mapping(user_id):
    """Retrieve user's current avatar mapping"""
    # return redis_client.hgetall(f'user_avatar:{user_id}')
    pass
```

### Frontend Integration

```typescript
// src/services/avatarService.ts
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface AvatarConnection {
  port: number;
  webrtc_url: string;
  connections: number;
  is_new_instance: boolean;
}

export const avatarService = {
  /**
   * Connect to avatar instance (with pooling)
   */
  async connect(avatarName: string): Promise<AvatarConnection> {
    const response = await axios.post(
      `${API_BASE}/api/avatar/connect`,
      { avatar_name: avatarName },
      { 
        headers: { 'Authorization': `Bearer ${getToken()}` },
        timeout: 35000  // 35 second timeout
      }
    );
    return response.data;
  },

  /**
   * Disconnect from avatar (graceful)
   */
  async disconnect(avatarName: string): Promise<void> {
    await axios.post(
      `${API_BASE}/api/avatar/disconnect`,
      { avatar_name: avatarName },
      { headers: { 'Authorization': `Bearer ${getToken()}` } }
    );
  },

  /**
   * Get current avatar connection status
   */
  async getStatus(): Promise<any> {
    const response = await axios.get(
      `${API_BASE}/api/avatar/status`,
      { headers: { 'Authorization': `Bearer ${getToken()}` } }
    );
    return response.data;
  }
};

// Usage in React component:
// const handleConnect = async () => {
//   try {
//     const connection = await avatarService.connect('test_yongen');
//     console.log(`Connected to ${connection.webrtc_url}`);
//     console.log(`${connection.connections} active connections`);
//   } catch (error) {
//     console.error('Failed to connect:', error);
//   }
// };
```

## 📊 Monitoring & Debugging

### Real-Time Monitoring Dashboard

```bash
# Watch system status in real-time
watch -n 2 'curl -s http://localhost:8607/status | jq .'

# Monitor GPU usage
watch -n 1 nvidia-smi

# Monitor logs
tail -f logs/avatar_manager.log

# Monitor specific avatar instance
tail -f logs/avatar_g_user_1_8615.log
```

### Key Metrics to Monitor

1. **Instance Count**: `running / max` - should not reach limit frequently
2. **GPU Memory**: Monitor per-GPU VRAM usage via `/status` endpoint
3. **Connection Count**: Total connections across all instances
4. **Shared Avatars**: Number of avatars with >1 connection
5. **Port Allocation**: Ensure no port conflicts or allocation failures

### Common Monitoring Queries

```bash
# Check if service is healthy
curl http://localhost:8607/health

# Get detailed system status
curl http://localhost:8607/status | jq '.data.manager'

# List all running avatars
curl http://localhost:8607/avatar/list | jq '.data[] | {id: .avatar_id, port: .port, connections: .connections}'

# Get specific avatar info
curl http://localhost:8607/avatar/info/test_yongen | jq .

# Check GPU statistics
curl http://localhost:8607/status | jq '.data.gpu'
```

### Log Analysis

```bash
# Check for errors in last hour
grep ERROR logs/avatar_manager.log | tail -20

# Monitor port allocation conflicts
grep "端口.*已被占用" logs/avatar_manager.log

# Track avatar lifecycle events
grep "启动成功\|停止成功\|重启" logs/avatar_manager.log

# Find GPU allocation decisions
grep "Allocated GPU" logs/avatar_manager.log

# Monitor connection sharing
grep "复用现有Avatar\|连接数" logs/avatar_manager.log
```

---

## 🧪 Testing & Validation

### Unit Tests

```bash
# Test port allocation (stress test)
python test_concurrent_allocation.py

# Expected: All allocations succeed without conflicts
```

### Integration Tests

```bash
# Basic functionality test
python test_manager.py

# Concurrent operations test (launches 3 avatars simultaneously)
python test_manager.py concurrent
```

### Performance Benchmarks

**Startup Time:**
- Cold start: ~10-15 seconds (includes model loading)
- Warm start (pooling): <1 second (reuse existing instance)

**Resource Usage per Instance:**
- VRAM: ~4GB (depends on model)
- RAM: ~5GB
- CPU: 1-2 cores (during inference)

**Capacity Limits:**
- Max instances: 5 (configurable)
- Max connections per instance: 100 (WebRTC sessions)
- Total system capacity: 500 concurrent users (5 × 100)

---

## 📝 Best Practices

### Production Deployment

1. **Use Process Manager**:
   ```bash
   # Use systemd or supervisor for production
   [Unit]
   Description=Avatar Manager Service
   After=network.target
   
   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/path/to/avatar-manager
   ExecStart=/usr/bin/python3 api.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

2. **Configure Log Rotation**:
   ```bash
   # /etc/logrotate.d/avatar-manager
   /path/to/avatar-manager/logs/*.log {
       daily
       rotate 7
       compress
       delaycompress
       missingok
       notifempty
   }
   ```

3. **Set Resource Limits**:
   ```bash
   # Prevent runaway processes
   ulimit -n 4096      # Max open files
   ulimit -u 2048      # Max processes
   ```

4. **Enable HTTPS** (if exposing externally):
   ```bash
   # Use nginx as reverse proxy
   location /avatar-manager/ {
       proxy_pass http://localhost:8607/;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
   }
   ```

### Performance Optimization

1. **Adjust GPU Memory**: Lower `required_mb` threshold in `_allocate_gpu()` if OOM occurs
2. **Increase Idle Timeout**: For high-traffic periods, increase `IDLE_TIMEOUT` to reduce cold starts
3. **Tune Health Checks**: Reduce `HEALTH_CHECK_INTERVAL` for faster failure detection
4. **Connection Pooling**: Use instance pooling to reduce memory overhead

### Security Considerations

1. **Authentication**: Add JWT validation to API endpoints
2. **Rate Limiting**: Prevent abuse of `/avatar/start` endpoint
3. **Input Validation**: Sanitize `avatar_id` and `avatar_name` parameters
4. **CORS**: Restrict CORS origins in production
5. **Firewall**: Block direct access to avatar instance ports (8615-8619)

---

**Version**: 2.0.0  
**Last Updated**: 2025-11-18  
**Maintainer**: Virtual Tutor Development Team





