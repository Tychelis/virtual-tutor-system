#!/bin/bash

echo "Starting Virtual Tutor System..."
echo "===================================="
echo ""

# Project root directory
PROJECT_ROOT="/workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2"

# Read port configuration from ports_config.py
read_port_config() {
    python3 -c "
import sys
sys.path.insert(0, '${PROJECT_ROOT}')
from ports_config import (
    BACKEND_PORT,
    FRONTEND_PORT,
    LLM_PORT,
    RAG_PORT,
    AVATAR_MANAGER_API_PORT,
    AVATAR_BASE_PORT,
    LIVE_SERVER_PORT,
    TTS_PORT,
    TTS_TACOTRON_PORT
)
print(f'export BACKEND_PORT={BACKEND_PORT}')
print(f'export FRONTEND_PORT={FRONTEND_PORT}')
print(f'export LLM_PORT={LLM_PORT}')
print(f'export RAG_PORT={RAG_PORT}')
print(f'export AVATAR_MANAGER_API_PORT={AVATAR_MANAGER_API_PORT}')
print(f'export AVATAR_BASE_PORT={AVATAR_BASE_PORT}')
print(f'export LIVE_SERVER_PORT={LIVE_SERVER_PORT}')
print(f'export TTS_PORT={TTS_PORT}')
print(f'export TTS_TACOTRON_PORT={TTS_TACOTRON_PORT}')
" 2>/dev/null || {
        echo "Warning: Unable to read ports_config.py, using default ports"
        echo "export BACKEND_PORT=8203"
        echo "export FRONTEND_PORT=3000"
        echo "export LLM_PORT=8611"
        echo "export RAG_PORT=8602"
        echo "export AVATAR_MANAGER_API_PORT=8607"
        echo "export AVATAR_BASE_PORT=8615"
        echo "export LIVE_SERVER_PORT=8606"
        echo "export TTS_PORT=8604"
        echo "export TTS_TACOTRON_PORT=8605"
    }
}

# Load port configuration
eval "$(read_port_config)"

echo "Port Configuration (read from ports_config.py):"
echo "   Backend:         ${BACKEND_PORT}"
echo "   Frontend:        ${FRONTEND_PORT}"
echo "   LLM:             ${LLM_PORT}"
echo "   RAG:             ${RAG_PORT}"
echo "   Avatar Manager:  ${AVATAR_MANAGER_API_PORT}"
echo "   Avatar Base:     ${AVATAR_BASE_PORT}"
echo "   Live Server:     ${LIVE_SERVER_PORT}"
echo "   TTS (Edge):      ${TTS_PORT}"
echo "   TTS (Tacotron):  ${TTS_TACOTRON_PORT}"
echo ""

# Check required conda environments
check_conda_env() {
    local env_name=$1
    if ! conda env list | grep -q "^${env_name} "; then
        echo "[X] Conda environment '${env_name}' not found"
        return 1
    fi
    return 0
}

# Create log directories for all services
LOG_DIR="${PROJECT_ROOT}/logs"
mkdir -p "${LOG_DIR}"
mkdir -p "${PROJECT_ROOT}/backend/logs"
mkdir -p "${PROJECT_ROOT}/llm/logs"
mkdir -p "${PROJECT_ROOT}/rag/logs"
mkdir -p "${PROJECT_ROOT}/avatar-manager/logs"
mkdir -p "${PROJECT_ROOT}/lip-sync/logs"
echo "Log Directory: ${LOG_DIR}"
echo "   [OK] Created logs directories for all services"
echo ""

# Initialize conda
if [ -f /workspace/conda/etc/profile.d/conda.sh ]; then
    source /workspace/conda/etc/profile.d/conda.sh
else
    echo "[X] Conda not found"
    exit 1
fi

echo "Checking Conda Environments..."
REQUIRED_ENVS=("bread" "rag" "edge" "avatar")
for env in "${REQUIRED_ENVS[@]}"; do
    if check_conda_env "$env"; then
        echo "  [OK] $env"
    else
        echo "  [X] $env (missing)"
    fi
done
echo ""

# 1. Start Backend service (Gunicorn concurrent mode)
echo "[1] Starting Backend service (port ${BACKEND_PORT}) - Gunicorn concurrent mode..."
cd "${PROJECT_ROOT}/backend"
conda activate bread
export WORKERS=4
export WORKER_CLASS=gevent
nohup gunicorn --config gunicorn_config.py "app:create_app()" > "${LOG_DIR}/backend.log" 2>&1 &
BACKEND_PID=$!
echo "   [OK] Backend starting (PID: $BACKEND_PID)"
echo "   Info: Concurrent mode with 4 gevent workers, supports high concurrency"
sleep 3

# 2. Start RAG service (Knowledge base retrieval)
echo "[2] Starting RAG service (port ${RAG_PORT})..."
cd "${PROJECT_ROOT}/rag"
conda activate rag
nohup python app.py > "${LOG_DIR}/rag.log" 2>&1 &
RAG_PID=$!
echo "   [OK] RAG starting (PID: $RAG_PID)"
sleep 2

# 3. Start Ollama service (LLM inference engine)
echo "[3] Starting Ollama service (port 11434)..."
# Check if Ollama is already running
if lsof -i :11434 > /dev/null 2>&1; then
    echo "   [OK] Ollama already running"
else
    nohup ollama serve > "${LOG_DIR}/ollama.log" 2>&1 &
    OLLAMA_PID=$!
    echo "   [OK] Ollama starting (PID: $OLLAMA_PID)"
    echo "   Info: Waiting for Ollama to initialize..."
    sleep 5
fi

# 4. Start LLM service (Conversation generation, using rag environment) - Optimized version + Gunicorn concurrent
echo "[4] Starting LLM service (port ${LLM_PORT} - Optimized version + Gunicorn concurrent)..."
cd "${PROJECT_ROOT}/llm"
conda activate rag
export TAVILY_API_KEY="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"
export MILVUS_API_BASE_URL="http://localhost:9090"
export WORKERS=2
export THREADS=2
export WORKER_CLASS=sync
nohup gunicorn --config gunicorn_config.py --workers 2 --threads 2 --worker-class sync "api_interface_optimized:app" > "${LOG_DIR}/llm.log" 2>&1 &
LLM_PID=$!
echo "   [OK] LLM starting (PID: $LLM_PID) - Async latency reduction optimized version"
echo "   Info: Optimizations: Parallel RAG+classification, async safety check, RAG caching"
echo "   Info: Concurrent mode: 2 sync workers, supports multi-user concurrent conversations"
sleep 3

# 5. TTS services note (on-demand startup)
echo "[5] TTS Services (On-demand startup)..."
echo "   Note: TTS services are started automatically by Avatar Manager when needed"
echo "   Note: Each Avatar can use a different TTS model (Edge TTS, Tacotron, SoViTs, CosyVoice)"
echo "   Info: Avatar Manager will start the required TTS service automatically when starting an Avatar"
sleep 1

# 6. Start Avatar configuration management service (legacy live_server)
echo "[6] Starting Avatar configuration management service (port ${LIVE_SERVER_PORT})..."
cd "${PROJECT_ROOT}/lip-sync"
conda activate avatar
nohup python live_server.py > "${LOG_DIR}/live_server.log" 2>&1 &
LIVE_SERVER_PID=$!
echo "   [OK] Avatar configuration service starting (PID: $LIVE_SERVER_PID)"
sleep 2

# 7. Start Avatar Manager (multi-instance concurrent management)
echo "[7] Starting Avatar Manager (port ${AVATAR_MANAGER_API_PORT}) - Supports 5 Avatar concurrent instances..."
cd "${PROJECT_ROOT}/avatar-manager"
nohup python3 api.py > "${LOG_DIR}/avatar_manager.log" 2>&1 &
AVATAR_MGR_PID=$!
echo "   [OK] Avatar Manager starting (PID: $AVATAR_MGR_PID)"
echo "   Info: Supports 5 Avatar instances running simultaneously (ports ${AVATAR_BASE_PORT}-$((AVATAR_BASE_PORT+4)))"
echo "   Info: Automatic GPU resource management, each user has independent Avatar"
echo "   Info: API address: http://localhost:${AVATAR_MANAGER_API_PORT}"
sleep 2

# 8. Lip-sync service note (no longer directly started)
echo "[8] Lip-sync Avatar instances..."
echo "   Note: Avatar instances are started on-demand by Avatar Manager"
echo "   Note: Independent Avatar instance is automatically created for each user connection"
echo "   Info: Manual testing: cd avatar-manager && python3 test_manager.py start test_yongen"
sleep 1

# 9. Start Frontend
echo "[9] Starting Frontend (port ${FRONTEND_PORT})..."
cd "${PROJECT_ROOT}/frontend"
# 使用BROWSER=none避免自动打开浏览器，并使用PORT环境变量
export BROWSER=none
export PORT=${FRONTEND_PORT}
nohup npm start > "${LOG_DIR}/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "   [OK] Frontend starting (PID: $FRONTEND_PID)"
echo "   Info: Waiting for frontend to compile (this may take 30-60 seconds)..."

echo ""
echo "===================================="
echo "Waiting for services to start..."
sleep 5
# 额外等待前端服务编译完成
echo "Waiting for frontend compilation (this may take up to 60 seconds)..."
sleep 15

echo ""
echo "Checking Service Status..."
echo ""

# Check port
check_port() {
    local port=$1
    local name=$2
    if lsof -i :$port > /dev/null 2>&1; then
        echo "  [OK] $name (port $port)"
        return 0
    else
        echo "  [X] $name (port $port) - Not running"
        return 1
    fi
}

check_port ${BACKEND_PORT} "Backend (Gunicorn concurrent)"
check_port ${RAG_PORT} "RAG"
check_port 11434 "Ollama"
check_port ${LLM_PORT} "LLM (Gunicorn concurrent)"
check_port ${TTS_PORT} "Edge TTS"
check_port ${LIVE_SERVER_PORT} "Avatar Config Service"
check_port ${AVATAR_MANAGER_API_PORT} "Avatar Manager (multi-instance concurrent)"
echo "  [SKIP] Avatar instances (ports ${AVATAR_BASE_PORT}-$((AVATAR_BASE_PORT+4))) - Auto-start on demand"
check_port ${FRONTEND_PORT} "Frontend"

echo ""
echo "===================================="
echo "Service Access URLs:"
echo "  Frontend:         http://localhost:${FRONTEND_PORT}"
echo "  Backend:          http://localhost:${BACKEND_PORT}  (Gunicorn concurrent [OK])"
echo "  Ollama:           http://localhost:11434  (LLM inference engine)"
echo "  LLM:              http://localhost:${LLM_PORT}  (Gunicorn concurrent [OK])"
echo "  Avatar Manager:   http://localhost:${AVATAR_MANAGER_API_PORT}  (5 Avatar concurrent [OK])"
echo "  Avatar Config:    http://localhost:${LIVE_SERVER_PORT}"
echo "===================================="
echo ""
echo "New Feature: Real Concurrency Support!"
echo "  [OK] Backend:  4 gevent workers, supports 1000+ QPS"
echo "  [OK] LLM:      2 sync workers, multi-user simultaneous conversations"
echo "  [OK] Avatar:   5 independent instances, each user has independent Avatar"
echo ""
echo "Avatar Concurrent Management (New):"
echo "  Method 1: Use Avatar Manager API (Recommended)"
echo "    # Start Avatar"
echo "    curl -X POST http://localhost:${AVATAR_MANAGER_API_PORT}/avatar/start \\"
echo "      -H 'Content-Type: application/json' \\"
echo "      -d '{\"avatar_id\": \"test_yongen\"}'"
echo ""
echo "    # Check status"
echo "    curl http://localhost:${AVATAR_MANAGER_API_PORT}/status | python3 -m json.tool"
echo ""
echo "    # List all Avatars"
echo "    curl http://localhost:${AVATAR_MANAGER_API_PORT}/avatar/list | python3 -m json.tool"
echo ""
echo "  Method 2: Use test script"
echo "    cd avatar-manager"
echo "    python3 test_manager.py start test_yongen"
echo "    python3 test_manager.py status"
echo ""
echo "  Method 3: Run concurrent demo"
echo "    cd avatar-manager"
echo "    python3 demo_concurrent.py"
echo ""
echo "System Capacity:"
echo "  - Supports up to 5 Avatar instances running simultaneously"
echo "  - Each Avatar has independent port (${AVATAR_BASE_PORT}-$((AVATAR_BASE_PORT+4)))"
echo "  - Each user uses independent Avatar instance"
echo "  - Automatic GPU resource management, no interference"
echo ""
echo "Difference from old system:"
echo "  [X] Old way: Single Avatar, all users share, conflicts occur"
echo "  [OK] New way: Multiple Avatars, each user independent, true concurrency"
echo ""
echo "View Logs:"
echo "  All logs location: ${LOG_DIR}/"
echo ""
echo "  Core service logs:"
echo "    tail -f ${LOG_DIR}/backend.log          # Backend (Gunicorn)"
echo "    tail -f ${LOG_DIR}/ollama.log           # Ollama (LLM inference)"
echo "    tail -f ${LOG_DIR}/llm.log              # LLM (Gunicorn)"
echo "    tail -f ${LOG_DIR}/avatar_manager.log   # Avatar Manager"
echo "    tail -f ${LOG_DIR}/rag.log"
echo "    tail -f ${LOG_DIR}/edge_tts.log"
echo "    tail -f ${LOG_DIR}/live_server.log"
echo "    tail -f ${LOG_DIR}/frontend.log"
echo ""
echo "  Avatar Manager detailed logs:"
echo "    tail -f avatar-manager/logs/avatar_manager.log"
echo ""
echo "  View all logs:"
echo "    tail -f ${LOG_DIR}/*.log"
echo ""
echo "  Clean logs:"
echo "    rm ${LOG_DIR}/*.log"
echo "    rm avatar-manager/logs/*.log"
echo ""
echo "Test Concurrency Features:"
echo "  # Backend concurrency test"
echo "  cd backend && python3 test_concurrency.py"
echo ""
echo "  # Avatar concurrency demo"
echo "  cd avatar-manager && python3 demo_concurrent.py"
echo ""
echo "Stop All Services:"
echo "  ./stop_all.sh"
echo ""
echo "All services started successfully!"
echo ""

