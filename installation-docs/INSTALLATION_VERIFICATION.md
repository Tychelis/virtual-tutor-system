# Installation Documentation Verification and Corrections

This document records the verification results and necessary corrections for INSTALLATION_GUIDE.md.

---

## ✅ Verification Summary

### Verified Correct Content

1. **Conda Environments**
   - ✅ `bread`, `rag`, `avatar` environments all exist
   - ✅ Environment names match start_all.sh

2. **Dependency Files**
   - ✅ backend/requirements.txt exists and is usable
   - ✅ llm/requirements.txt exists and is usable
   - ✅ rag/requirements.txt exists and is usable
   - ✅ lip-sync/requirements.txt exists and is usable
   - ✅ avatar-manager/requirements.txt has been created
   - ✅ frontend/package.json exists and is usable

3. **Configuration Files**
   - ✅ scripts/ports_config.py exists
   - ✅ scripts/generate_frontend_config.py exists and is executable
   - ✅ backend/.env exists (but should not be committed to Git)

4. **Startup Scripts**
   - ✅ scripts/start_all.sh exists and is complete
   - ✅ scripts/stop_all.sh exists and is complete

---

## ⚠️ Issues Requiring Correction

### 1. Backend .env File Instructions

**Issue**:
- Documentation requires users to create `.env` file
- But project already has `backend/.env` file (containing real email password)
- This file should not be committed to Git

**Recommended Fix**:

#### Option A: Create .env.example Template (Recommended)

```bash
# Create template file
cd backend
cp .env .env.example

# Remove sensitive information from .env.example
sed -i 's/SECRET_KEY=.*/SECRET_KEY=your-secret-key-change-this/' .env.example
sed -i 's/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=your-jwt-secret-key-change-this/' .env.example
sed -i 's/MAIL_PASSWORD=.*/MAIL_PASSWORD=your-app-specific-password/' .env.example
sed -i 's/MAIL_USERNAME=.*/MAIL_USERNAME=your-email@gmail.com/' .env.example

# Add to .gitignore
echo "backend/.env" >> .gitignore
```

Then update documentation:
```markdown
### 3. Configure Environment Variables

Backend provides `.env.example` template file, copy and modify:

```bash
cd backend
cp .env.example .env
vim .env  # or use other editor
```

Then fill in your configuration...
```

#### Option B: Remove .env from Git (if already committed)

```bash
# Remove from Git history (keep local file)
git rm --cached backend/.env

# Add to .gitignore
echo "backend/.env" >> .gitignore

# Commit changes
git commit -m "Remove .env from version control"
```

---

### 2. Database Path Issue

**Current .env Configuration**:
```
DATABASE_URL=sqlite:////db/app.db   # persisted in Docker volume
```

**Issue**:
- Path `/db/app.db` is Docker container path
- Local installation should use relative path

**Recommended Fix**:

In `backend/config.py` already correctly configured:
```python
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASEDIR, 'instance', 'app.db')
```

`DATABASE_URL` in `.env` can be deleted or commented out (not used in config.py).

**Documentation should explain**:
```markdown
### 4. Initialize Database

Database will be automatically created at `backend/instance/app.db`. First run will auto-initialize.

For manual initialization:
```bash
mkdir -p backend/instance
python -c "from app import create_app; from models.user import db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized')"
```
```

---

### 3. Incomplete Redis Configuration Instructions

**Issue**:
- Documentation explains how to install and start Redis
- But doesn't explain how to configure Redis password (required for production)

**Recommended Addition**:

```markdown
### 2. Install Redis

#### Installation
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install redis-server

# macOS
brew install redis
```

#### Start (Development Environment)
```bash
# Foreground
redis-server

# Background
redis-server --daemonize yes

# Verify
redis-cli ping
# Should return: PONG
```

#### Configuration (Production Environment, Recommended)
```bash
# Edit Redis configuration file
sudo vim /etc/redis/redis.conf

# 1. Set password
requirepass your-strong-password

# 2. Bind address (local access only)
bind 127.0.0.1

# 3. Enable persistence
appendonly yes

# Restart Redis
sudo systemctl restart redis
```

#### Configure Redis Connection in .env
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-strong-password  # If password is set
REDIS_DB=0
```
```

---

### 4. Poppler Installation May Not Apply to All Systems

**Issue**:
- Documentation only mentions Ubuntu/Debian and macOS
- No mention of CentOS/RHEL or other distributions

**Recommended Addition**:

```markdown
### 4. System Dependencies

#### Poppler (for PDF processing)

```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# CentOS/RHEL
sudo yum install poppler-utils

# Fedora
sudo dnf install poppler-utils

# macOS
brew install poppler

# Using Conda (recommended, cross-platform)
conda install -c conda-forge poppler
```

#### FFmpeg (for audio/video processing)

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg libsm6 libxext6

# CentOS/RHEL
sudo yum install ffmpeg

# macOS
brew install ffmpeg

# Conda
conda install -c conda-forge ffmpeg
```
```

---

### 5. PyTorch Installation Needs More Detail

**Issue**:
- lip-sync requires PyTorch with CUDA
- Mentioned in documentation but not detailed enough

**Recommended Addition**:

```markdown
### 5. Install PyTorch (CUDA Version)

Lip-Sync module requires GPU acceleration, must install CUDA version of PyTorch.

#### 1. Check CUDA Version

```bash
nvidia-smi
# Check CUDA Version in top right corner
```

#### 2. Install Matching PyTorch Version

```bash
conda activate avatar

# CUDA 11.8
pip install torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2 --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1
pip install torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2 --index-url https://download.pytorch.org/whl/cu121

# CPU version (not recommended, poor performance)
pip install torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2
```

#### 3. Verify Installation

```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda}')"
```

Expected output:
```
PyTorch: 2.2.2
CUDA available: True
CUDA version: 11.8  # or your CUDA version
```
```

---

### 6. Email Configuration Should Be More User-Friendly

**Issue**:
- Many users don't know how to generate Gmail app-specific password
- No configuration provided for other email providers

**Recommended Addition**:

```markdown
### Gmail Configuration Steps (Detailed)

#### 1. Enable Two-Factor Authentication
1. Visit https://myaccount.google.com/security
2. Click "2-Step Verification"
3. Follow instructions to complete setup

#### 2. Generate App-Specific Password
1. Visit https://myaccount.google.com/apppasswords
2. Select "Mail" and your device
3. Click "Generate"
4. Copy the generated 16-digit password (format: xxxx xxxx xxxx xxxx)

#### 3. Configure .env
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=xxxx xxxx xxxx xxxx  # App-specific password, not account password
MAIL_DEFAULT_SENDER=TutorNet <your-email@gmail.com>
```

### QQ Mail Configuration

#### 1. Enable SMTP Service
1. Login to QQ Mail web version
2. Settings → Account → POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV Services
3. Enable "POP3/SMTP Service" or "IMAP/SMTP Service"
4. Get authorization code

#### 2. Configure .env
```bash
MAIL_SERVER=smtp.qq.com
MAIL_PORT=465
MAIL_USE_TLS=false
MAIL_USE_SSL=true
MAIL_USERNAME=your-qq-number@qq.com
MAIL_PASSWORD=your-authorization-code  # Authorization code
MAIL_DEFAULT_SENDER=TutorNet <your-qq-number@qq.com>
```

### Outlook/Hotmail Configuration

```bash
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=your-email@outlook.com
MAIL_PASSWORD=your-account-password
MAIL_DEFAULT_SENDER=TutorNet <your-email@outlook.com>
```

### 163 Mail Configuration

```bash
MAIL_SERVER=smtp.163.com
MAIL_PORT=465
MAIL_USE_TLS=false
MAIL_USE_SSL=true
MAIL_USERNAME=your-email@163.com
MAIL_PASSWORD=your-authorization-code
MAIL_DEFAULT_SENDER=TutorNet <your-email@163.com>
```
```

---

### 7. Startup Script Path Issue

**Issue**:
- `./scripts/start_all.sh` in documentation needs to run from project root
- But doesn't clearly state current working directory

**Recommended Fix**:

```markdown
### Method 2: Use Startup Script (Production Environment)

**Run Startup Script**:

```bash
# Navigate to project root (important!)
cd /workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2

# Or if you're in a project subdirectory
cd $(git rev-parse --show-toplevel)  # Git project root

# Ensure script is executable
chmod +x scripts/start_all.sh

# Start all services
./scripts/start_all.sh
```

**Note**: Must run from project root directory, otherwise path errors will occur.
```

---

### 8. Node.js and npm Version Requirements

**Issue**:
- Only mentions Node.js 16+
- React 19 may require newer npm version

**Recommended Addition**:

```markdown
### Software Requirements
- **Operating System**: Ubuntu 20.04+ / CentOS 7+ / macOS 12+
- **Python**: 3.10 or higher
- **Node.js**: 16.0+ or higher (18+ LTS recommended)
- **npm**: 8.0+ or higher (9+ recommended)
- **Redis**: 6.0+ or higher
- **Ollama**: Latest version (for LLM)
- **Git**: For cloning project

#### Check Versions
```bash
python3 --version    # Should be >= 3.10
node --version       # Should be >= v16.0.0
npm --version        # Should be >= 8.0.0
redis-server --version  # Should be >= 6.0
git --version
```

#### Update npm (if needed)
```bash
npm install -g npm@latest
```
```

---

## 📝 Recommended Improvement Checklist

### High Priority

1. [ ] Create `backend/.env.example` template file
2. [ ] Add `backend/.env` to `.gitignore`
3. [ ] Add Redis password configuration instructions
4. [ ] Detail PyTorch CUDA version installation
5. [ ] Clearly specify script working directory requirements

### Medium Priority

6. [ ] Add configuration examples for more email providers
7. [ ] Add dependency installation commands for different Linux distributions
8. [ ] Add version check commands
9. [ ] Explain database auto-creation mechanism

### Low Priority

10. [ ] Add troubleshooting decision tree
11. [ ] Provide video tutorial links (if available)
12. [ ] Add performance optimization recommendations
13. [ ] Provide Docker Compose configuration (optional)

---

## 🧪 Test Verification Script

The verification script `scripts/verify_installation.sh` has been created to verify installation success.

**Usage**:
```bash
chmod +x scripts/verify_installation.sh
./scripts/verify_installation.sh
```

**Features**:
- ✅ Checks system requirements (Python, Node.js, Redis, Ollama, etc.)
- ✅ Verifies NVIDIA GPU and CUDA
- ✅ Checks project structure completeness
- ✅ Verifies configuration files exist
- ✅ Checks conda environments
- ✅ Tests if services are running
- ✅ Color-coded output (green=OK, red=error, yellow=warning)
- ✅ Returns exit code 0 on success, 1 on failure

---

## 📚 Related Documentation

- [INSTALLATION_GUIDE.md](./INSTALLATION_GUIDE.md) - Needs updates based on this document
- [CONDA_ENVIRONMENTS.md](./CONDA_ENVIRONMENTS.md)
- [DEPENDENCIES.md](./DEPENDENCIES.md)
- [PORT_CONFIG_GUIDE.md](../PORT_CONFIG_GUIDE.md)

---
