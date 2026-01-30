# Conda Virtual Environment Configuration Quick Reference

This document provides a quick guide to creating and configuring all Conda virtual environments required for the project.

---

## 📋 Environment Overview

The project requires **3 Conda environments**:

| Environment Name | Python Version | Purpose | Modules Used |
|-----------------|----------------|---------|--------------|
| **bread** | 3.10 | Backend API service | `backend/` |
| **rag** | 3.12 | RAG retrieval + LLM dialogue | `rag/`, `llm/` |
| **avatar** | 3.10 | Avatar management + Digital human | `avatar-manager/`, `lip-sync/` |

---

## 🚀 One-Click Creation of All Environments

```bash
#!/bin/bash
# Save as setup_conda_envs.sh and run

# 1. Create Backend environment
echo "Creating bread environment..."
conda create -n bread python=3.10 -y
conda activate bread
cd backend && pip install -r requirements.txt
cd ..

# 2. Create RAG environment (includes LLM dependencies)
echo "Creating rag environment..."
conda create -n rag python=3.12 -y
conda activate rag
conda install -c conda-forge poppler -y  # PDF processing
cd rag && pip install -r requirements.txt
cd ../llm && pip install -r requirements.txt
cd ..

# 3. Create Avatar environment
echo "Creating avatar environment..."
conda create -n avatar python=3.10 -y
conda activate avatar
cd lip-sync && pip install -r requirements.txt
cd ../avatar-manager && pip install flask redis requests psutil
cd ..

echo "All conda environments created successfully!"
```

Usage:
```bash
chmod +x setup_conda_envs.sh
./setup_conda_envs.sh
```

---

## 📦 Creating Environments Individually

### 1. Backend Environment (`bread`)

```bash
# Create environment
conda create -n bread python=3.10 -y

# Activate environment
conda activate bread

# Install dependencies
cd backend
pip install -r requirements.txt

# Verify
python -c "import flask; import redis; print('Backend environment OK')"
```

**Main Dependencies**:
- Flask 3.1.1
- Flask-CORS 6.0.1
- Flask-JWT-Extended 4.7.0
- Flask-SQLAlchemy 3.1.1
- Redis 5.0.3
- Gunicorn 23.0.0
- gevent 24.11.1 (for concurrency)

---

### 2. RAG Environment (`rag`) - Includes LLM

```bash
# Create environment
conda create -n rag python=3.12 -y

# Activate environment
conda activate rag

# Install system dependencies (Poppler for PDF processing)
conda install -c conda-forge poppler -y

# Install RAG dependencies
cd rag
pip install -r requirements.txt

# Install LLM dependencies
cd ../llm
pip install -r requirements.txt

# Verify
python -c "
from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer
import ollama
print('RAG environment OK')
"
```

**Main Dependencies**:
- pymilvus 2.4.x (Milvus client)
- sentence-transformers 2.x (text embedding)
- colpali-engine (multimodal embedding, optional)
- langchain (LLM framework)
- langgraph (workflow orchestration)
- tavily-python (web search)

**Why do LLM and RAG share an environment?**
- LLM service needs to call RAG's Milvus client
- Share embedding models and dependency libraries
- Simplifies deployment and dependency management

---

### 3. Avatar Environment (`avatar`)

```bash
# Create environment
conda create -n avatar python=3.10 -y

# Activate environment
conda activate avatar

# Install Lip-Sync dependencies
cd lip-sync
pip install -r requirements.txt

# Install Avatar Manager dependencies
cd ../avatar-manager
pip install -r requirements.txt

# Verify
python -c "
import cv2
import mediapipe
import aiortc
print('Avatar environment OK')
"
```

**Main Dependencies**:
- torch (PyTorch + CUDA)
- opencv-python
- mediapipe
- aiortc (WebRTC)
- Flask (API service)
- Redis (state management)

**Why do Avatar Manager and Lip-Sync share an environment?**
- Avatar Manager needs to launch Lip-Sync instances
- Share WebRTC and video processing libraries
- Unified GPU resource management

---

## ✅ Environment Verification

### Check if All Environments Exist

```bash
conda env list | grep -E "bread|rag|avatar"
```

Expected output:
```
bread                    /path/to/conda/envs/bread
rag                      /path/to/conda/envs/rag
avatar                   /path/to/conda/envs/avatar
```

### Test Each Environment

```bash
# Test bread
conda activate bread
python -c "from flask import Flask; print('✓ bread OK')"

# Test rag
conda activate rag
python -c "from pymilvus import MilvusClient; print('✓ rag OK')"

# Test avatar
conda activate avatar
python -c "import cv2; print('✓ avatar OK')"
```

---

## 🔄 Environment Management

### Activate Environment

```bash
# Activate Backend environment
conda activate bread

# Activate RAG/LLM environment
conda activate rag

# Activate Avatar environment
conda activate avatar

# Deactivate current environment
conda deactivate
```

### Update Environment

```bash
# Update Backend dependencies
conda activate bread
cd backend
pip install -r requirements.txt --upgrade

# Update RAG dependencies
conda activate rag
cd rag
pip install -r requirements.txt --upgrade
cd ../llm
pip install -r requirements.txt --upgrade

# Update Avatar dependencies
conda activate avatar
cd lip-sync
pip install -r requirements.txt --upgrade
```

### Delete Environment

```bash
# Delete single environment
conda env remove -n bread

# Delete all project environments
conda env remove -n bread -y
conda env remove -n rag -y
conda env remove -n avatar -y
```

### Export Environment Configuration

```bash
# Export bread environment
conda activate bread
conda env export > backend_environment.yml

# Export rag environment
conda activate rag
conda env export > rag_environment.yml

# Export avatar environment
conda activate avatar
conda env export > avatar_environment.yml
```

### Create Environment from Configuration File

```bash
# Create from YAML file
conda env create -f backend_environment.yml
conda env create -f rag_environment.yml
conda env create -f avatar_environment.yml
```

---

## 🐛 Common Issues

### 1. Conda Not Found

**Symptoms**:
```
conda: command not found
```

**Solution**:
```bash
# Initialize conda
if [ -f /workspace/conda/etc/profile.d/conda.sh ]; then
    source /workspace/conda/etc/profile.d/conda.sh
elif [ -f ~/anaconda3/etc/profile.d/conda.sh ]; then
    source ~/anaconda3/etc/profile.d/conda.sh
elif [ -f ~/miniconda3/etc/profile.d/conda.sh ]; then
    source ~/miniconda3/etc/profile.d/conda.sh
fi

# Add to ~/.bashrc to make it permanent
echo 'source /path/to/conda/etc/profile.d/conda.sh' >> ~/.bashrc
```

### 2. Poppler Installation Failed

**Symptoms**:
```
PackagesNotFoundError: poppler
```

**Solution**:
```bash
# Method 1: Use conda-forge channel
conda install -c conda-forge poppler -y

# Method 2: Use system package manager
# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler
```

### 3. PyTorch CUDA Version Mismatch

**Symptoms**:
```
RuntimeError: CUDA error: no kernel image is available
```

**Solution**:
```bash
# Check CUDA version
nvidia-smi

# Uninstall old version
pip uninstall torch torchvision torchaudio

# Reinstall matching version (CUDA 11.8 example)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Or CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 4. Package Not Found After Environment Activation

**Symptoms**:
```
ModuleNotFoundError: No module named 'flask'
```

**Cause**: Dependencies not installed correctly

**Solution**:
```bash
# Ensure you're in the correct environment
conda activate bread

# Check environment location
which python
which pip

# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep flask
```

### 5. start_all.sh Cannot Find Environment

**Symptoms**:
```
[X] Conda environment 'bread' not found
```

**Solution**:
```bash
# Ensure environment names match exactly (case-sensitive)
conda env list

# If environment name is wrong, rename or recreate
# No direct rename command, need to recreate:
conda create -n bread --clone old_env_name
conda env remove -n old_env_name
```

---

## 📝 Best Practices

### 1. Environment Isolation

✅ **Recommended**: Use separate conda environment for each service
```bash
conda activate bread  # Only for Backend
```

❌ **Not Recommended**: Mix environments
```bash
conda activate bread
cd llm  # May be missing dependencies
```

### 2. Dependency Management

✅ **Recommended**: Regularly update requirements.txt
```bash
conda activate bread
pip freeze > requirements.txt
```

✅ **Recommended**: Use fixed versions
```
flask==3.1.1  # Fixed version
```

❌ **Not Recommended**: Use broad versions
```
flask>=3.0  # May cause compatibility issues
```

### 3. Environment Backup

Regularly export environment configurations:
```bash
# Export after each major update
conda activate bread
conda env export > envs/bread_$(date +%Y%m%d).yml
```

### 4. Test-Driven

After updating dependencies, run tests:
```bash
conda activate bread
cd backend
pytest tests/
```

---

## 🔗 Related Documentation

- [Complete Installation Guide](./INSTALLATION_GUIDE.md)
- [Port Configuration Guide](../PORT_CONFIG_GUIDE.md)
- [Project Main README](../README.md)
- [Backend README](../backend/README.md)
- [LLM README](../llm/README.md)
- [RAG README](../rag/README.md)
