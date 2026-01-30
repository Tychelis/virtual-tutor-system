# Port Configuration Management

## 📋 Overview

This project uses **centralized port configuration**, where all service ports are managed in `ports_config.py`.

## 🎯 Modify Once, Apply Globally

### Steps to Modify Ports

1. **Edit `ports_config.py`**
   ```python
   # Example: Modify Backend port
   BACKEND_PORT = 8203  # Change to your desired port
   ```

2. **Regenerate frontend configuration** (if frontend-related ports are modified)
   ```bash
   python scripts/generate_frontend_config.py
   ```

3. **Restart related services**
   ```bash
   # Restart Backend
   cd backend && ./start_production.sh
   
   # Restart Frontend (if frontend port config is modified)
   cd frontend && npm start
   ```

## 📦 Managed Ports

### Core Services
- `BACKEND_PORT` (8203) - Backend API service
- `FRONTEND_PORT` (3000) - Frontend React application

### AI Services
- `LLM_PORT` (8611) - LLM service (optimized)
- `LLM_PORT_ORIGINAL` (8610) - LLM service (original)
- `RAG_PORT` (8602) - RAG service
- `MILVUS_PORT` (9090) - Milvus vector database

### Avatar Services
- `AVATAR_MANAGER_API_PORT` (8607) - Avatar Manager API
- `AVATAR_BASE_PORT` (8615) - Avatar instance starting port
- `LIVE_SERVER_PORT` (8606) - Live Server

### TTS Services
- `TTS_PORT` (8604) - Edge TTS (default)
- `TTS_TACOTRON_PORT` (8605) - Tacotron TTS
- `TTS_SOVITS_PORT` (8608) - SoVITS TTS
- `TTS_COSYVOICE_PORT` (8609) - CosyVoice TTS

### Infrastructure
- `REDIS_PORT` (6379) - Redis cache
- `OLLAMA_PORT` (11434) - Ollama service

## 🔧 Services Using Configuration

### Backend Python Services (Auto-read)
The following services **automatically** read configuration from `ports_config.py`:

- ✅ Backend API (`/backend`)
- ✅ LLM Service (`/llm`)
- ✅ RAG Service (`/rag`)
- ✅ Avatar Manager (`/avatar-manager`)
- ✅ All Backend Routes

### Frontend JavaScript (Requires Regeneration)
Frontend configuration is generated via script. After modifying ports, run:
```bash
python scripts/generate_frontend_config.py
```

This updates `frontend/src/config.js`, including:
- ✅ BACKEND_URL
- ✅ LIPSYNC_MANAGER_URL
- ✅ WEBRTC_URL
- ✅ TTS_URL

## 📝 Example: Changing Backend Port

Suppose you want to change Backend from 8203 to 9000:

1. **Modify `ports_config.py`**
   ```python
   BACKEND_PORT = 9000  # Was 8203
   ```

2. **Regenerate frontend configuration**
   ```bash
   python scripts/generate_frontend_config.py
   # Output: ✅ Generated frontend/src/config.js
   #         BACKEND_PORT: 9000
   ```

3. **Restart services**
   ```bash
   # Restart Backend
   cd backend
   pkill -f "gunicorn.*app:create_app"
   gunicorn --config gunicorn_config.py "app:create_app()"
   
   # Restart Frontend
   cd ../frontend
   npm start
   ```

4. **Done!** 🎉
   - Backend now listens on port 9000
   - Frontend automatically connects to port 9000
   - All related services automatically use the new port

## ⚠️ Important Notes

1. **Port Conflict Check**
   ```bash
   # Check if port is already in use
   netstat -tuln | grep 8203
   ```

2. **Firewall Rules**
   You may need to update firewall rules after modifying ports

3. **Docker Configuration**
   If using Docker, synchronize port mappings in `docker-compose.yml`

4. **Environment Variable Override**
   Frontend can override default configuration via `REACT_APP_API_BASE_URL`:
   ```bash
   REACT_APP_API_BASE_URL=http://custom-host:9000/api npm start
   ```

## 🚀 Quick Reference

```python
# ports_config.py - Get service URLs
from ports_config import get_backend_url, get_llm_url, get_avatar_manager_url

backend_url = get_backend_url()  # http://localhost:8203
llm_url = get_llm_url(use_optimized=True)  # http://localhost:8611
avatar_url = get_avatar_manager_url()  # http://localhost:8607
```

## 📚 Related Files

- `ports_config.py` - Main configuration file
- `scripts/generate_frontend_config.py` - Frontend configuration generator
- `frontend/src/config.js` - Frontend configuration (auto-generated)
- `frontend/src/services/chatService.js` - Uses frontend configuration
- `frontend/src/utils/request.js` - Uses frontend configuration
