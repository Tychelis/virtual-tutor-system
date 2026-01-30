# Project Dependencies Overview

This document provides a comprehensive overview of all dependency files in the Virtual Tutor System project.

---

## 📋 Dependency Files Summary

| Module | Dependency File | Package Manager | Python Version |
|--------|----------------|-----------------|----------------|
| Backend | `backend/requirements.txt` | pip | 3.10 |
| LLM Service | `llm/requirements.txt` | pip | 3.12 |
| RAG Service | `rag/requirements.txt` | pip | 3.12 |
| Avatar Manager | `avatar-manager/requirements.txt` | pip | 3.10 |
| Lip-Sync | `lip-sync/requirements.txt` | pip | 3.10 |
| Frontend | `frontend/package.json` | npm | N/A (Node.js) |

---

## 🔧 Backend Dependencies

**File**: `backend/requirements.txt`  
**Conda Environment**: `bread`  
**Python Version**: 3.10

### Core Dependencies

```
Flask==3.1.1                    # Web framework
Flask-CORS==6.0.1               # Cross-origin resource sharing
Flask-JWT-Extended==4.7.0       # JWT authentication
Flask-Mail==0.10.0              # Email service
Flask-SQLAlchemy==3.1.1         # Database ORM
```

### Production Server

```
gunicorn==23.0.0                # WSGI server
gevent==24.11.1                 # Async I/O (for concurrent requests)
```

### Database & Caching

```
redis==5.0.3                    # Redis client
SQLAlchemy==2.0.36              # Database toolkit
```

### Utilities

```
python-dotenv==1.0.1            # Environment variable management
requests==2.32.3                # HTTP library
PyJWT==2.10.1                   # JWT token handling
```

### Installation

```bash
conda activate bread
cd backend
pip install -r requirements.txt
```

---

## 🤖 LLM Service Dependencies

**File**: `llm/requirements.txt`  
**Conda Environment**: `rag` (shared with RAG)  
**Python Version**: 3.12

### Core LLM Framework

```
langchain==0.3.12               # LLM framework
langchain-community==0.3.10     # Community integrations
langchain-core==0.3.25          # Core functionality
langchain-ollama==0.2.1         # Ollama integration
langgraph==0.2.60               # Workflow orchestration
langgraph-checkpoint==2.0.10    # Checkpoint management
```

### Vector Database

```
pymilvus==2.5.1                 # Milvus client (RAG integration)
```

### Search Integration

```
tavily-python==0.5.0            # Web search API
```

### Web Server

```
flask==3.1.1                    # API server
gunicorn==23.0.0                # Production server
```

### Utilities

```
requests==2.32.3                # HTTP requests
python-dotenv==1.0.1            # Environment variables
```

### Installation

```bash
conda activate rag
cd llm
pip install -r requirements.txt
```

**Note**: LLM and RAG share the `rag` conda environment because they use common dependencies (Milvus client, embedding models).

---

## 📚 RAG Service Dependencies

**File**: `rag/requirements.txt`  
**Conda Environment**: `rag` (shared with LLM)  
**Python Version**: 3.12

### Vector Database

```
pymilvus==2.5.1                 # Milvus Lite client
```

### Embedding Models

```
sentence-transformers==2.7.0    # Text embedding
transformers==4.46.3            # Hugging Face models
torch==2.2.2                    # PyTorch
```

### Document Processing

```
PyMuPDF==1.25.1                 # PDF parsing
pdf2image==1.17.0               # PDF to image conversion
Pillow==11.0.0                  # Image processing
```

### Multimodal (Optional - MODE=1 only)

```
colpali-engine==0.3.2           # Multimodal retrieval
```

### Web Server

```
flask==3.1.1                    # API server
flask-cors==6.0.1               # CORS support
```

### Utilities

```
python-dotenv==1.0.1            # Environment management
numpy==1.26.4                   # Numerical computing
```

### System Dependencies

**Poppler** (required for PDF to image conversion):

```bash
# Conda (recommended)
conda install -c conda-forge poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler
```

### Installation

```bash
conda activate rag
conda install -c conda-forge poppler -y
cd rag
pip install -r requirements.txt
```

---

## 🎭 Avatar Manager Dependencies

**File**: `avatar-manager/requirements.txt`  
**Conda Environment**: `avatar`  
**Python Version**: 3.10

### Web Framework

```
flask==3.0.0                    # API server
flask-cors==4.0.0               # CORS support
```

### Redis Integration

```
redis==5.0.3                    # State management
```

### System Monitoring

```
psutil==5.9.8                   # Process and system monitoring
```

### HTTP Client

```
requests==2.32.3                # HTTP requests to Lip-Sync
```

### Installation

```bash
conda activate avatar
cd avatar-manager
pip install -r requirements.txt
```

---

## 💋 Lip-Sync Service Dependencies

**File**: `lip-sync/requirements.txt`  
**Conda Environment**: `avatar` (shared with Avatar Manager)  
**Python Version**: 3.10

### Deep Learning

```
torch==2.2.2                    # PyTorch (CUDA version)
torchvision==0.17.2             # Vision utilities
torchaudio==2.2.2               # Audio utilities
```

**Note**: Install PyTorch with CUDA support:

```bash
# CUDA 11.8
pip install torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2 --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1
pip install torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2 --index-url https://download.pytorch.org/whl/cu121
```

### Computer Vision

```
opencv-python==4.10.0.84        # Image/video processing
mediapipe==0.10.14              # Face detection & landmarks
face-alignment==1.4.1           # Face alignment
```

### WebRTC

```
aiortc==1.9.0                   # WebRTC implementation
aiohttp==3.10.10                # Async HTTP server
```

### Audio Processing

```
librosa==0.10.2.post1           # Audio analysis
soundfile==0.12.1               # Audio I/O
pydub==0.25.1                   # Audio manipulation
```

### Speech Synthesis (TTS)

```
edge-tts==6.1.18                # Edge TTS
```

### Utilities

```
numpy==1.26.4                   # Numerical computing
Pillow==10.4.0                  # Image processing
requests==2.32.3                # HTTP client
python-dotenv==1.0.1            # Environment variables
```

### Installation

```bash
conda activate avatar
cd lip-sync
pip install -r requirements.txt
```

**Model Files Required**:
- MuseTalk models (~2-3GB)
- Wav2Lip models
- Face detection models

See `lip-sync/README.md` for model download instructions.

---

## 🎨 Frontend Dependencies

**File**: `frontend/package.json`  
**Package Manager**: npm  
**Node.js**: 16+ (18+ recommended)

### Core Framework

```json
"react": "^19.0.0"              // UI library
"react-dom": "^19.0.0"          // React DOM renderer
"react-scripts": "5.0.1"        // Build tooling
```

### Routing

```json
"react-router-dom": "^7.1.1"    // Client-side routing
```

### HTTP Client

```json
"axios": "^1.7.9"               // HTTP requests
```

### UI Components & Styling

```json
"@mui/material": "^6.3.1"       // Material-UI components
"@mui/icons-material": "^6.3.1" // Material icons
"@emotion/react": "^11.14.0"    // CSS-in-JS
"@emotion/styled": "^11.14.0"   // Styled components
```

### Utilities

```json
"dayjs": "^1.11.13"             // Date manipulation
"react-markdown": "^9.0.3"      // Markdown rendering
"remark-gfm": "^4.0.0"          // GitHub Flavored Markdown
```

### Development Tools

```json
"@testing-library/react": "^16.1.0"  // Testing
"@testing-library/jest-dom": "^6.6.3" // Jest matchers
"@testing-library/user-event": "^14.5.2" // User event simulation
```

### Installation

```bash
cd frontend
npm install
```

### Scripts

```bash
npm start           # Start development server (port 3000)
npm run build       # Build for production
npm test            # Run tests
npm run eject       # Eject from Create React App
```

---

## 🔄 Dependency Update Strategy

### Check for Updates

```bash
# Python packages
conda activate bread  # or rag/avatar
pip list --outdated

# npm packages
cd frontend
npm outdated
```

### Update Dependencies

```bash
# Python - update all
pip install -r requirements.txt --upgrade

# Python - update specific package
pip install flask --upgrade

# npm - update all
npm update

# npm - update specific package
npm install react@latest
```

### Verify After Update

```bash
# Python
python -c "import flask; print(flask.__version__)"

# npm
npm list react
```

---

## ⚠️ Important Notes

### 1. Conda Environment Sharing

- **LLM + RAG** share the `rag` environment
- **Avatar Manager + Lip-Sync** share the `avatar` environment
- This reduces duplication and simplifies management

### 2. CUDA Compatibility

- Lip-Sync requires PyTorch with CUDA support
- Match CUDA version with your GPU drivers
- Check with `nvidia-smi` before installing

### 3. System Dependencies

Some Python packages require system-level dependencies:

```bash
# Ubuntu/Debian
sudo apt-get install -y \
    poppler-utils \
    ffmpeg \
    libsm6 \
    libxext6 \
    build-essential

# macOS
brew install poppler ffmpeg
```

### 4. Version Pinning

All dependencies use specific versions (`==`) to ensure reproducibility. When updating, test thoroughly before deploying.

### 5. Frontend Build

The frontend `node_modules` can be large (~500MB). Add to `.gitignore`:

```gitignore
frontend/node_modules/
frontend/build/
```

---

## 🔗 Related Documentation

- [INSTALLATION_GUIDE.md](./INSTALLATION_GUIDE.md) - Complete installation instructions
- [CONDA_ENVIRONMENTS.md](./CONDA_ENVIRONMENTS.md) - Conda environment setup
- [Backend README](../backend/README.md) - Backend-specific documentation
- [Frontend README](../frontend/README.md) - Frontend-specific documentation

---

## 📦 Complete Installation Command Reference

```bash
# 1. Create all conda environments
conda create -n bread python=3.10 -y
conda create -n rag python=3.12 -y
conda create -n avatar python=3.10 -y

# 2. Install Backend
conda activate bread
cd backend && pip install -r requirements.txt

# 3. Install RAG & LLM
conda activate rag
conda install -c conda-forge poppler -y
cd rag && pip install -r requirements.txt
cd ../llm && pip install -r requirements.txt

# 4. Install Avatar services
conda activate avatar
cd lip-sync && pip install -r requirements.txt
cd ../avatar-manager && pip install -r requirements.txt

# 5. Install Frontend
cd frontend && npm install
```
