# Virtual Tutor System

An intelligent AI tutoring system featuring real-time digital avatar interactions, RAG-enhanced conversations, and multi-user concurrent support. Built with React, Flask, WebRTC, and LangGraph, the system delivers low-latency streaming responses with synchronized lip-sync animations.

**Key Highlights:**
- 🎭 **Real-time Digital Avatars**: WebRTC-powered avatars with MuseTalk lip-sync
- 💬 **Streaming AI Chat**: Sub-second response time with RAG retrieval
- 👥 **Multi-User Support**: Concurrent avatar instances with isolated sessions
- 📚 **Knowledge Base Integration**: Milvus vector DB + web search
- 🔊 **Multiple TTS Engines**: Edge-TTS, Tacotron, SoVITS, CosyVoice
- 🎯 **Production Ready**: Multi-worker architecture with Redis coordination

---

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Core Features](#core-features)
- [System Components](#system-components)
- [Testing](#testing)
- [Installation](#installation)
- [Configuration](#configuration)
- [Hardware Requirements](#hardware-requirements)
- [Team & References](#team--references)

---

## Quick Start

### Prerequisites
- **Hardware**: NVIDIA GPU with 40GB+ VRAM (recommended)
- **Software**: Python 3.10+, Node.js 16+, Redis, Ollama
- **Network**: Ports 3000, 6379, 8203, 8602, 8607, 8611, 8615-8619

### Launch Services

```bash
# 1. Start Redis
redis-server &

# 2. Start LLM Service (AI chat backend)
cd llm && gunicorn --config gunicorn_config.py "api_interface_optimized:app" &

# 3. Start RAG Service (knowledge retrieval)
cd rag && python app.py &

# 4. Start Avatar Manager (digital human orchestration)
cd avatar-manager && python manager.py &

# 5. Start Backend API (main application server)
cd backend && gunicorn --config gunicorn_config.py "app:create_app()" &

# 6. Start Frontend (user interface)
cd frontend && npm start
```

### Access the System

Open your browser to **http://localhost:3000**

**Test Credentials:**
- Email: `test@example.com`
- Password: `password123`

---

## Architecture Overview

### Service Communication Flow

```
┌──────────────────────────────────────────────────────────┐
│                    Frontend (React)                       │
│                  http://localhost:3000                    │
│  • Real-time chat interface with streaming responses     │
│  • WebRTC video avatar display                           │
│  • File upload for knowledge base documents              │
└──────────────────┬───────────────────────────────────────┘
                   │ HTTP/SSE/WebRTC
                   ↓
┌──────────────────────────────────────────────────────────┐
│            Backend API (Flask + Gunicorn)                 │
│               http://localhost:8203                       │
│  • JWT authentication & session management               │
│  • WebRTC proxy to avatar instances                      │
│  • File upload & RAG indexing coordination               │
│  • Redis-based multi-worker state sync                   │
└────┬─────────┬──────────┬──────────┬─────────────────────┘
     │         │          │          │
     ↓         ↓          ↓          ↓
┌─────────┐ ┌──────┐ ┌────────────┐ ┌──────┐
│   LLM   │ │ RAG  │ │  Avatar    │ │Redis │
│ Service │ │      │ │  Manager   │ │      │
│  :8611  │ │:8602 │ │   :8607    │ │:6379 │
└─────────┘ └──────┘ └──────┬─────┘ └──────┘
                            │ Spawns
                            ↓
                   ┌─────────────────┐
                   │ Avatar Instances│
                   │  (Ports 8615+)  │
                   │  • MuseTalk     │
                   │  • WebRTC       │
                   │  • TTS          │
                   └─────────────────┘
```

### Key Design Patterns

1. **Multi-Worker Backend**: 4 Gunicorn sync workers with Redis state coordination
2. **Avatar Instance Pooling**: One isolated avatar instance per user
3. **Streaming Architecture**: SSE for chat, incremental TTS forwarding
4. **WebRTC Proxy**: Backend routes avatar traffic by user authentication
5. **Centralized Port Config**: Single `ports_config.py` for all services

---

## Core Features

### 1. Real-time Interactive Digital Avatars

**What It Does:**
- Displays photorealistic AI tutors with synchronized lip movements
- Supports multiple concurrent users with isolated avatar sessions
- Automatically launches avatar instances on WebRTC connection

**Technical Implementation:**
- **Avatar Engine**: MuseTalk for facial animation generation
- **Streaming**: WebRTC for low-latency video/audio transmission
- **TTS Integration**: Real-time speech synthesis with Edge-TTS/Tacotron
- **Session Management**: Redis-based user-to-avatar port mapping

**Usage:**
```javascript
// Frontend initiates avatar connection
const response = await fetch(`${BACKEND_URL}/api/avatar/start`, {
    method: 'POST',
    body: new URLSearchParams({avatar_name: 'test_yongen'})
});

// Backend returns WebRTC endpoint
{
    "port": 8615,
    "webrtc_url": "http://localhost:8615/offer",
    "is_new_instance": true
}
```

### 2. Streaming AI Chat with RAG

**What It Does:**
- Provides instant, context-aware responses to student questions
- Retrieves relevant information from uploaded documents
- Falls back to web search for real-time information
- Displays responses word-by-word as they're generated

**Technical Implementation:**
- **LLM Backend**: LangGraph orchestration with Ollama models
- **Vector DB**: Milvus for semantic document retrieval
- **Web Search**: Tavily API for external knowledge
- **Streaming**: Server-Sent Events (SSE) for real-time text delivery
- **Performance**: ~0.8s Time-To-First-Token (TTFT)

**RAG Workflow:**
```python
# 1. User uploads document
POST /api/file/upload
→ File stored in uploads/{user_id}/
→ RAG service indexes content into Milvus

# 2. User asks question
GET /api/llm/chat?query="What is machine learning?"
→ RAG retrieves relevant chunks from user's documents
→ LLM generates response with retrieved context
→ Response streams back via SSE

# 3. Parallel TTS forwarding
→ Every 5 words, text sent to avatar TTS endpoint
→ Avatar speaks while text displays on screen
```

### 3. Multi-User Concurrent Support

**What It Does:**
- Allows multiple students to use avatars simultaneously
- Each user gets their own isolated avatar session
- Prevents cross-user interference and resource conflicts

**Technical Implementation:**
- **Instance Naming**: `{avatar_name}_user_{user_id}` (e.g., `test_yongen_user_1`)
- **Port Allocation**: Dynamic ports starting from base 8615
- **GPU Management**: Automatic GPU selection based on memory availability
- **Redis Coordination**: Shared state across multiple backend workers

**Example:**
```python
# User 1 connects to test_yongen
→ Avatar instance: test_yongen_user_1, Port: 8615, GPU: 0

# User 2 connects to test_yongen
→ Avatar instance: test_yongen_user_2, Port: 8616, GPU: 1

# User 3 connects to test_two
→ Avatar instance: test_two_user_3, Port: 8617, GPU: 0
```

### 4. Knowledge Base Integration

**What It Does:**
- Stores and retrieves information from uploaded documents
- Supports PDF, TXT, DOCX file formats
- Enables personalized AI tutoring based on course materials

**Technical Implementation:**
- **Document Processing**: Text extraction with pypdf, python-docx
- **Embedding**: Sentence transformers for vector representations
- **Storage**: Milvus vector database with user/public collections
- **Retrieval**: Cosine similarity search with configurable top-k

**Supported Operations:**
```bash
# Upload document and auto-index
POST /api/file/upload
→ Files stored in uploads/{user_id}/
→ Automatically indexed into Milvus

# Query with RAG retrieval
GET /api/llm/chat?query="Explain neural networks"
→ Searches user's documents first
→ Falls back to public knowledge base
→ Uses web search if no matches found

# Direct RAG search (debugging)
POST /api/rag/search
{
    "query": "machine learning types",
    "top_k": 3,
    "user_id": "13"
}
```

---

## System Components

### Frontend (`frontend/`)
**Technology**: React 19.1.0, WebRTC, Server-Sent Events

**Key Features:**
- Responsive chat interface with streaming message display
- WebRTC video avatar integration with connection management
- File upload with drag-and-drop support
- Session history and conversation management
- Tab lock mechanism to prevent multi-tab conflicts

**Files:**
- `src/components/ChatInterface.js` - Main chat UI
- `src/components/VideoAvatar.js` - WebRTC avatar display
- `src/services/webrtcService.js` - WebRTC connection logic
- `src/config.js` - Auto-generated from `ports_config.py`

---

### Backend (`backend/`)
**Technology**: Flask, Gunicorn (4 workers), SQLAlchemy, Redis

**Key Features:**
- JWT authentication with role-based access control
- RESTful API for chat, file upload, avatar management
- WebRTC proxy to route avatar traffic by user
- Redis-based session and avatar mapping storage
- Health check endpoints for all services

**Main Endpoints:**
```
POST   /api/auth/login          # User authentication
POST   /api/file/upload         # Upload documents for RAG
GET    /api/llm/chat            # Streaming chat responses (SSE)
POST   /api/avatar/start        # Launch avatar instance
GET    /api/avatar/list         # Get running avatars
POST   /api/avatar/stop         # Stop avatar instance
```

**Files:**
- `app.py` - Flask application factory
- `routes/auth.py` - Authentication endpoints
- `routes/llm.py` - Chat and RAG integration
- `routes/avatar.py` - Avatar management proxy
- `models/user.py` - User database model

---

### LLM Service (`llm/`)
**Technology**: LangGraph, Ollama, Tavily Search API

**Key Features:**
- LangGraph workflow for intelligent query routing
- Determines if query needs RAG, web search, or direct answer
- Streaming response generation with chunk-by-chunk delivery
- Content safety filtering for inappropriate questions
- Session-aware conversation history

**Workflow:**
```
User Query → Query Classification → Tool Selection
                                    ↓
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
              RAG Retrieval   Web Search   Direct Answer
                    │               │               │
                    └───────────────┼───────────────┘
                                    ↓
                          LLM Response Generation
                                    ↓
                         Streaming to Frontend
```

**Files:**
- `ai_assistant_optimized.py` - Main LangGraph orchestration
- `api_interface_optimized.py` - FastAPI/Flask endpoints
- `milvus_api_client.py` - RAG retrieval integration

---

### RAG Service (`rag/`)
**Technology**: Milvus, SentenceTransformers, ChromaDB

**Key Features:**
- Document embedding and vector storage
- Semantic similarity search
- User-specific and public knowledge bases
- Multimodal support (text, images)

**API:**
```
POST /api/upload_file          # Index document into Milvus
POST /api/search               # Semantic search
GET  /api/list_files           # List indexed documents
POST /api/delete_file          # Remove from knowledge base
```

**Files:**
- `app.py` - Flask API server
- `embedding.py` - SentenceTransformer embeddings
- `retriever.py` - Milvus client wrapper
- `kb_manager.py` - Knowledge base management

---

### Avatar Manager (`avatar-manager/`)
**Technology**: Python subprocess management, Redis, psutil

**Key Features:**
- Launch and terminate avatar instances
- Dynamic port and GPU allocation
- Health monitoring and auto-restart
- Multi-worker safe with Redis coordination

**API:**
```
POST /avatar/start             # Launch avatar for user
POST /avatar/stop              # Terminate avatar instance
GET  /avatar/list              # List running avatars
GET  /avatar/status            # System status (GPU, memory)
GET  /health                   # Service health check
```

**Files:**
- `api.py` - Flask REST API
- `manager.py` - Avatar lifecycle management
- `monitor.py` - GPU monitoring

---

### Lip-Sync Module (`lip-sync/`)
**Technology**: MuseTalk, PyTorch, WebRTC (aiortc)

**Key Features:**
- Real-time facial animation generation
- Audio-driven lip-sync with multiple TTS engines
- WebRTC video streaming
- Concurrent multi-session support

**Files:**
- `app.py` - Main avatar server
- `musereal.py` - MuseTalk integration
- `ttsreal.py` - TTS integration (Edge-TTS, Tacotron)
- `webrtc.py` - WebRTC signaling and streaming

---

### TTS Module (`tts/`)
**Technology**: Edge-TTS, Tacotron2, SoVITS, CosyVoice

**Key Features:**
- Multiple TTS engine support
- Voice cloning capability
- REST API for text-to-speech conversion
- Hot-swappable TTS models

**Supported Engines:**
- **Edge-TTS**: Microsoft voices, 50+ languages
- **Tacotron2**: Custom voice training
- **GPT-SoVITS**: Few-shot voice cloning
- **CosyVoice**: High-quality multilingual synthesis

**Files:**
- `tts.py` - Unified TTS API server
- `edgetts_server.py` - Edge-TTS service
- `tacotron_server.py` - Tacotron service

---

## Testing

The `test/` directory contains comprehensive test suites for all components. Tests are designed to be **independent** and can run in any order.

### Quick Test Overview

| Test File | Purpose | Environment | Auth Required |
|-----------|---------|-------------|---------------|
| `generate_test_token.py` ⭐ | Generate JWT token (one-time setup) | `bread` | No |
| `test_concurrency.py` ⭐ | Backend performance & QPS | Any | No |
| `test_rag_integration.py` ⭐ | RAG workflow end-to-end | Any | Yes (from file) |
| `test_manager.py` ⭐ | Avatar management | Any | No |
| `test_current.py` ⭐ | LLM service performance | Any | No |

⭐ = Recommended/Frequently used

### Running Tests

```bash
# 1. One-time setup: Generate authentication token
conda activate bread
python test/generate_test_token.py

# 2. Run tests (any Python environment)
python test/test_concurrency.py quick      # Backend QPS test
python test/test_rag_integration.py        # RAG workflow test
python test/test_manager.py                # Avatar management test
python test/test_current.py                # LLM latency test
```

### Test Results Interpretation

**Backend Performance Test (`test_concurrency.py`)**:
```
======================================================================
 Concurrent Test Results
======================================================================
 Successful Requests: 100/100 (100.0%)
 QPS (Queries Per Second): 1106.5
 Average Response Time: 0.007s

 Performance Evaluation: Excellent (high-performance configuration)
======================================================================
```

**Performance Ratings:**
- **Excellent**: QPS > 80 (production-ready)
- **Good**: QPS 30-80 (acceptable)
- **Fair**: QPS 10-30 (might need optimization)
- **Poor**: QPS < 10 (check configuration)

**RAG Integration Test (`test_rag_integration.py`)**:
```
======================================================================
Testing RAG Integration with File Upload and Chat
======================================================================

[1] Loading authentication token... ✅
[2] Creating test PDF content... ✅
[3] Uploading file to backend... ✅
    - File path: uploads/13/20251123_ml_tutorial.txt
    - RAG indexed: true
[4] Waiting for RAG indexing... ✅
[5] Asking question about uploaded content... ✅
    - Response contains context from document: ✅
[6] Testing direct RAG retrieval... ✅
    - Retrieved 3 relevant chunks

======================================================================
Test completed! All checks passed.
======================================================================
```

**Avatar Management Test (`test_manager.py`)**:
```
======================================================================
 Avatar Manager Basic Function Test
======================================================================

Found 3 available avatar(s):
  - test_yongen
  - test_two
  - avatar_001

Starting Avatar: test_yongen
 Started successfully:
   PID: 12345
   Port: 8615
   GPU: 0
   WebRTC: http://localhost:8615/webrtc

======================================================================
System Status:
======================================================================
  Running Avatars: 1/10
  GPU 0: NVIDIA GeForce RTX 3090
    Memory: 2.1GB / 24.0GB (8.8%)
    Temperature: 45°C
```

**LLM Performance Test (`test_current.py`)**:
```
======================================================================
 LLM Service Performance Test
======================================================================

Question: What is machine learning?

 Time to First Token (TTFT): 0.856s
 Total Time: 3.245s
 Response Speed: 130.4 chars/sec
 Response Length: 423 characters

 Performance Evaluation: Excellent! TTFT 0.86s < 1 second
======================================================================
```

For detailed test documentation, see [test/README.md](./test/README.md).

---

## Installation

This project uses modular architecture where each component can be installed and run independently. Services communicate via network APIs.

### Installation Overview

Each module has its own `README.md` with detailed setup instructions:

- **Backend**: [backend/README.md](./backend/README.md)
- **Frontend**: [frontend/README.md](./frontend/README.md)
- **LLM Service**: [llm/README.md](./llm/README.md)
- **RAG Service**: [rag/README.md](./rag/README.md)
- **Avatar Manager**: [avatar-manager/README.md](./avatar-manager/README.md)
- **Lip-Sync Module**: [lip-sync/README.md](./lip-sync/README.md)
- **TTS Module**: [tts/README.md](./tts/README.md)

### Common Dependencies

**System Requirements:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip nodejs npm redis-server \
    libsndfile1 ffmpeg git curl

# Install Ollama (for LLM service)
curl -fsSL https://ollama.com/install.sh | sh
```

**Python Environments:**
```bash
# Create conda environments
conda create -n bread python=3.10  # Backend
conda create -n rag python=3.10    # RAG service
conda create -n avatar python=3.10 # Avatar-related
```

**Redis:**
```bash
# Start Redis server
redis-server &

# Verify it's running
redis-cli ping  # Should return "PONG"
```

### Deployment Note: Why No Docker?

This project does not use Docker containerization for the following reasons:

1. **High Hardware Requirements**: LLM and video generation modules require ~40GB GPU VRAM, exceeding typical Docker host GPU capabilities
2. **Client Preference**: Project stakeholders explicitly requested non-containerized deployment for easier integration with existing infrastructure
3. **Approved by Course Coordinator**: Dr. Basem Suleiman officially approved detailed installation documentation as equivalent to Docker deployment

For production deployment, comprehensive installation scripts and documentation are provided.

---

## Configuration

### Port Configuration

All service ports are centrally managed in `ports_config.py`. To change ports:

1. **Edit** `ports_config.py` - Modify desired port numbers
2. **Regenerate** frontend config: `python scripts/generate_frontend_config.py`
3. **Restart** affected services

**Default Ports:**
```python
# ports_config.py
FRONTEND_PORT = 3000
BACKEND_PORT = 8203
LLM_SERVICE_PORT = 8611
RAG_SERVICE_PORT = 8602
AVATAR_MANAGER_PORT = 8607
AVATAR_BASE_PORT = 8615  # Avatars use 8615, 8616, 8617...
TTS_EDGETTS_PORT = 8604
TTS_TACOTRON_PORT = 8605
REDIS_PORT = 6379
```

For detailed instructions, see [PORT_CONFIG_GUIDE.md](./PORT_CONFIG_GUIDE.md).

### Environment Variables

**Backend** (`.env`):
```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_EXPIRY_HOURS=5

# Service URLs
LLM_SERVICE_URL=http://localhost:8611
RAG_SERVICE_URL=http://localhost:8602
AVATAR_MANAGER_URL=http://localhost:8607

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

**LLM Service** (`.env`):
```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Tavily Web Search
TAVILY_API_KEY=your-tavily-api-key

# Milvus RAG
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

**Frontend** (`src/config.js` - auto-generated):
```javascript
export default {
    BACKEND_URL: 'http://localhost:8203',
    AVATAR_MANAGER_URL: 'http://localhost:8607',
    AVATAR_BASE_PORT: 8615
};
```

---

## Hardware Requirements

### Minimum Requirements (Basic Functionality)
- **CPU**: Intel i5 / AMD Ryzen 5 (4+ cores)
- **RAM**: 16GB
- **GPU**: NVIDIA GTX 1660 Ti (6GB VRAM)
- **Storage**: 50GB SSD
- **Network**: 10 Mbps

**Limitations**: Can run 1-2 concurrent avatars, slower LLM responses

### Recommended Requirements (Full Performance)
- **CPU**: Intel i7 / AMD Ryzen 7 (8+ cores)
- **RAM**: 32GB
- **GPU**: NVIDIA RTX 3090 (24GB VRAM) or RTX 4090 (24GB VRAM)
- **Storage**: 100GB NVMe SSD
- **Network**: 50 Mbps

**Benefits**: Supports 10+ concurrent avatars, <1s LLM response time

### Production Requirements (High Load)
- **CPU**: Intel Xeon / AMD EPYC (16+ cores)
- **RAM**: 64GB
- **GPU**: 2x NVIDIA RTX A6000 (48GB VRAM each)
- **Storage**: 500GB NVMe SSD (RAID 1)
- **Network**: 1 Gbps

**Benefits**: Supports 50+ concurrent users, GPU redundancy

### GPU Memory Breakdown
- **LLM Service**: 8-16GB (depends on model size)
- **Avatar Instance**: 2-3GB per avatar
- **TTS Models**: 1-2GB (Tacotron/SoVITS)
- **System Overhead**: 2-4GB

**Example**: With 24GB GPU, you can run:
- 1x LLM (10GB) + 4x Avatars (12GB) + TTS (2GB)

---

## References

**Text-to-Speech Engines:**
- [Edge-TTS](https://github.com/rany2/edge-tts) - Microsoft Neural TTS
- [Tacotron2](https://pytorch.org/hub/nvidia_deeplearningexamples_tacotron2/) - NVIDIA Deep Learning
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) - Voice Cloning
- [CosyVoice](https://github.com/FunAudioLLM/CosyVoice) - Multilingual TTS

**Lip-Sync & Avatar:**
- [MuseTalk](https://github.com/TMElyralab/MuseTalk) - Audio-driven Facial Animation
- [LiveTalking](https://github.com/lipku/LiveTalking) - Real-time Avatar System

**LLM & RAG:**
- [LangGraph](https://github.com/langchain-ai/langgraph) - LLM Workflow Orchestration
- [Ollama](https://ollama.com/) - Local LLM Inference
- [Milvus](https://milvus.io/) - Vector Database
- [Tavily](https://tavily.com/) - Web Search API

**Frameworks & Libraries:**
- [React](https://react.dev/) - Frontend UI
- [Flask](https://flask.palletsprojects.com/) - Backend API
- [WebRTC](https://webrtc.org/) - Real-time Communication
- [Redis](https://redis.io/) - Session Store & Coordination

---

## License

This project is developed for educational purposes as part of UNSW COMP9900 coursework.

**Academic Use Only** - Not for commercial distribution.

---

## Documentation

Comprehensive project documentation is available in the `doc/` folder:

- **User Manual**: Complete system usage guide with feature explanations
- **Technical Documentation**: Architecture design, data flow, algorithm details
- **API Documentation**: Detailed API reference with examples
- **Test Documentation**: Test cases, methods, and result analyses
- **System Integration Tests**: End-to-end testing and performance validation

---

## Support & Troubleshooting

### Common Issues

**Problem**: "Service unavailable" errors

**Solution**: Check all services are running
```bash
curl http://localhost:8203/api/health  # Backend
curl http://localhost:8611/health      # LLM
curl http://localhost:8602/health      # RAG
curl http://localhost:8607/health      # Avatar Manager
```

**Problem**: WebRTC connection fails

**Solution**: 
1. Check avatar instance is running: `python test/test_manager.py list`
2. Verify port is accessible: `netstat -tuln | grep 8615`
3. Check browser console for errors

**Problem**: RAG retrieval returns no results

**Solution**:
1. Verify file was indexed: Check `rag_indexed: true` in upload response
2. Wait 2-3 seconds after upload before querying
3. Test direct RAG API: `POST http://localhost:8602/api/search`

**Problem**: Slow LLM responses (TTFT > 3s)

**Solution**:
1. Check GPU availability: `nvidia-smi`
2. Verify Ollama is using GPU: `ollama list`
3. Test LLM directly: `python test/test_current.py`

For more troubleshooting, see [test/README.md](./test/README.md) section "Troubleshooting".

---

**Last Updated**: November 24, 2025  
**Version**: 2.0  
**Build**: Phase 2 Production Release
