# ============================================================================
# Core service ports
# ============================================================================

# Backend API service
BACKEND_PORT = 8203

# Frontend React app
FRONTEND_PORT = 3000

# ============================================================================
# AI service ports
# ============================================================================

# LLM service (optimized, recommended)
LLM_PORT = 8611
# LLM service (original, fallback)
LLM_PORT_ORIGINAL = 8610

# RAG service
RAG_PORT = 8602

# Milvus vector database (used by RAG)
MILVUS_PORT = 9090

# ============================================================================
# Avatar-related service ports
# ============================================================================

# Avatar Manager API service
AVATAR_MANAGER_API_PORT = 8607

# Avatar base port (instances are assigned starting from this port)
AVATAR_BASE_PORT = 8615

# Live Server (Avatar management)
LIVE_SERVER_PORT = 8606

# ============================================================================
# TTS service ports
# ============================================================================

# TTS service (Edge TTS, default)
TTS_PORT = 8604

# TTS service (Tacotron TTS)
TTS_TACOTRON_PORT = 8605

# TTS service (SoVITS TTS)
TTS_SOVITS_PORT = 8608

# TTS service (CosyVoice TTS)
TTS_COSYVOICE_PORT = 8609

# TTS model-to-port mapping (for on-demand startup)
TTS_MODEL_PORTS = {
    'edgeTTS': TTS_PORT,
    'edgetts': TTS_PORT,
    'tacotron': TTS_TACOTRON_PORT,
    'sovits': TTS_SOVITS_PORT,
    'cosyvoice': TTS_COSYVOICE_PORT,
}

def get_tts_port_for_model(model_name: str) -> int:
    """Get the corresponding port by TTS model name"""
    # Normalize model name
    model_lower = model_name.lower()
    return TTS_MODEL_PORTS.get(model_lower, TTS_PORT)

# ============================================================================
# Infrastructure ports
# ============================================================================

# Redis cache service
REDIS_PORT = 6379

# Ollama service
OLLAMA_PORT = 11434

# ============================================================================
# Helper functions: generate service URLs
# ============================================================================

def get_backend_url(host='localhost'):
    """Get Backend API URL"""
    return f"http://{host}:{BACKEND_PORT}"

def get_llm_url(host='localhost', use_optimized=True):
    """Get LLM service URL"""
    port = LLM_PORT if use_optimized else LLM_PORT_ORIGINAL
    return f"http://{host}:{port}"

def get_rag_url(host='localhost'):
    """Get RAG service URL"""
    return f"http://{host}:{RAG_PORT}"

def get_avatar_manager_url(host='localhost'):
    """Get Avatar Manager API URL"""
    return f"http://{host}:{AVATAR_MANAGER_API_PORT}"

def get_avatar_url(host='localhost', port=None):
    """Get Avatar instance URL"""
    if port is None:
        port = AVATAR_BASE_PORT
    return f"http://{host}:{port}"

def get_tts_url(host='localhost'):
    """Get TTS service URL"""
    return f"http://{host}:{TTS_PORT}"

def get_live_server_url(host='localhost'):
    """Get Live Server URL"""
    return f"http://{host}:{LIVE_SERVER_PORT}"

# ============================================================================
# Port list (for checking port usage)
# ============================================================================

ALL_PORTS = {
    'backend': BACKEND_PORT,
    'frontend': FRONTEND_PORT,
    'llm': LLM_PORT,
    'llm_original': LLM_PORT_ORIGINAL,
    'rag': RAG_PORT,
    'milvus': MILVUS_PORT,
    'avatar_manager': AVATAR_MANAGER_API_PORT,
    'avatar_base': AVATAR_BASE_PORT,
    'live_server': LIVE_SERVER_PORT,
    'tts': TTS_PORT,
    'tts_tacotron': TTS_TACOTRON_PORT,
    'tts_sovits': TTS_SOVITS_PORT,
    'tts_cosyvoice': TTS_COSYVOICE_PORT,
    'redis': REDIS_PORT,
    'ollama': OLLAMA_PORT,
}

