# Scripts Directory

Utility scripts for managing the Virtual Tutor System.

---

## 🚀 Main Scripts

### `start_all.sh`
Start all system services in the correct order.

```bash
./scripts/start_all.sh
```

**Services started:**
- Backend API (port 8203)
- RAG Service (port 8602)
- Ollama (port 11434)
- LLM Service (port 8611)
- Avatar Manager (port 8607)
- Avatar Config Service (port 8610)
- Frontend (port 3000)

**Logs:** All logs stored in `logs/` directory

---

### `stop_all.sh`
Stop all running services.

```bash
./scripts/stop_all.sh

# Force stop (kill -9)
./scripts/stop_all.sh force
```

Stops services by port number and cleans up processes.

---

### `stop_all_avatars.sh`
Stop all avatar instances only.

```bash
./scripts/stop_all_avatars.sh
```

Terminates avatar processes on ports 8615-8619.

---

## ⚙️ Configuration Scripts

### `ports_config.py`
**Centralized port configuration** for all services.

```python
# ports_config.py
BACKEND_PORT = 8203
LLM_SERVICE_PORT = 8611
RAG_SERVICE_PORT = 8602
AVATAR_MANAGER_PORT = 8607
# ... and more
```

**To change ports:**
1. Edit `ports_config.py`
2. Run `python generate_frontend_config.py`
3. Restart services

---

### `generate_frontend_config.py`
Generate frontend config from `ports_config.py`.

```bash
python scripts/generate_frontend_config.py
```

**Output:** `frontend/src/config.js`

Ensures frontend and backend use the same port configuration.

---

## 📁 Directory Structure

```
scripts/
├── start_all.sh                 # Start all services
├── stop_all.sh                  # Stop all services
├── stop_all_avatars.sh          # Stop avatars only
├── ports_config.py              # Port configuration
├── generate_frontend_config.py  # Generate frontend config
├── backend/                     # Backend scripts
├── llm/                         # LLM scripts
├── rag/                         # RAG scripts
├── avatar-manager/              # Avatar management scripts
└── lip-sync/                    # Avatar lip-sync scripts
```

---

## 🔧 Usage Examples

### Start System
```bash
./scripts/start_all.sh
```

### Stop System
```bash
./scripts/stop_all.sh
```

### Restart System
```bash
./scripts/stop_all.sh && sleep 3 && ./scripts/start_all.sh
```

### Change Ports
```bash
# 1. Edit ports
vim scripts/ports_config.py

# 2. Regenerate config
python scripts/generate_frontend_config.py

# 3. Restart
./scripts/stop_all.sh && ./scripts/start_all.sh
```

### Stop Only Avatars
```bash
./scripts/stop_all_avatars.sh
```

---

## 📝 Notes

- **Conda Required**: Scripts use conda environments (`bread`, `rag`, `avatar`)
- **Logs Auto-Created**: All log directories created automatically
- **Port Conflicts**: Scripts check for port conflicts before starting
- **Background Processes**: Services run as background processes (nohup)
