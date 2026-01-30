# Test Suite Documentation

Comprehensive test scripts for the Virtual Tutor System, covering backend services, LLM performance, RAG integration, avatar management, and system configuration validation.

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Test Files Description](#test-files-description)
- [Authentication & Setup Tests](#authentication--setup-tests)
- [Backend Tests](#backend-tests)
- [LLM Tests](#llm-tests)
- [RAG Integration Tests](#rag-integration-tests)
- [Avatar Management Tests](#avatar-management-tests)
- [System Configuration Tests](#system-configuration-tests)
- [Running Tests](#running-tests)
- [Troubleshooting](#troubleshooting)
- [Test Files Summary](#test-files-summary)

---

## Overview

This directory contains three main test suites for the Virtual Tutor System:

1. **TTS Generation Tests** (`test_tts_generation.py`) - Validates text-to-speech service configuration
2. **Video Generation Tests** (`test_video_generation.py`) - Checks video generation components
3. **LLM Response Tests** (`test_llm_response.py`) - Validates large language model integration

These are **pre-check tests** designed to verify system configuration and dependencies, rather than full functional tests.

---

## Prerequisites

### Required Services

Ensure these services are running before testing:

| Service | URL | Purpose |
|---------|-----|---------|
| Backend | `http://localhost:8203` | Main API server |
| LLM Service | `http://localhost:8611` | AI assistant |
| RAG Service | `http://localhost:8602` | Document retrieval |
| Avatar Manager | `http://localhost:8607` | Avatar orchestration |

### Conda Environments

Different tests require different environments:

- **bread**: Backend tests (Flask, SQLAlchemy, JWT)
- **rag**: RAG service tests
- **avatar**: Avatar-related tests

---

## Quick Start

```bash
# 1. Generate test token (one-time setup, valid 5 hours)
conda activate bread
python test/generate_test_token.py

# 2. Run any test (works in any Python environment)
python test/test_concurrency.py quick       # Backend performance
python test/test_rag_integration.py         # RAG workflow
python test/test_manager.py                 # Avatar management
python test/test_current.py                 # LLM performance
```

---

## Test Files Description

### System Configuration Tests

#### 1. `test_tts_generation.py`

**Purpose**: Validate EdgeTTS and Tacotron TTS model configurations

**Test Items**:
- ✓ EdgeTTS service check - Verifies EdgeTTS service running on port 8604
- ✓ Tacotron service check - Verifies Tacotron service running on port 8604
- ✓ Configuration file check - Validates config.json and model_info.json exist
- ✓ File structure check - Verifies TTS server directories exist

**Expected Results**:
- 4/4 passed: System fully configured
- 2-3/4 passed: Need to start TTS services
- <2/4 passed: Need to install dependencies or check configuration

**Usage**:
```bash
python test_tts_generation.py
```

---

#### 2. `test_video_generation.py`

**Purpose**: Validate video generation component configuration and dependencies

**Test Items**:
- ✓ Avatar availability check - Verifies test_yongen and test_two avatars exist
- ✓ Backend service check - Verifies backend API running on port 8203
- ✓ Avatar service check - Verifies avatar manager and app.py exist
- ✓ Database check - Validates database files or storage directories exist
- ✓ Multimedia library check - Validates librosa, soundfile, moviepy, etc.

**Expected Results**:
- 5/5 passed: Video generation fully ready
- <3/5 passed: Need installation or configuration

**Usage**:
```bash
python test_video_generation.py
```

---

#### 3. `test_llm_response.py`

**Purpose**: Validate large language model integration and configuration

**Test Items**:
- ✓ LLM service check - Verifies LLM service is running
- ✓ Backend integration check - Validates LLM routes and configuration exist
- ✓ Dependency check - Verifies ollama, transformers, torch, langchain libraries
- ✓ Configuration check - Validates .env or config files exist
- ✓ Model check - Verifies model directories and files exist
- ✓ Database check - Validates conversation storage database

**Expected Results**:
- 6/6 passed: LLM fully ready
- 4-5/6 passed: Some dependencies missing or models not downloaded
- <4/6 passed: Need LLM service configuration

**Usage**:
```bash
python test_llm_response.py
```

---

## Authentication & Setup Tests

### `generate_test_token.py` ⭐ 

**Purpose**: Create test user and generate JWT token (one-time setup)

**Environment**: `bread` conda environment (required)

**Usage**:
```bash
conda activate bread
python test/generate_test_token.py
```

**What it does**:
- Creates test user: `test@example.com` / `password123`
- Generates JWT token (valid 5 hours)
- Stores token in Redis for validation
- Saves to `.test_token` file

**Output Example**:
```
======================================================================
Generating Test Token
======================================================================

ℹ️  Test user already exists: test@example.com
✅ JWT token generated and stored in Redis

User ID: 13
Token (valid for 5 hours):
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

✅ Token saved to: /workspace/.../test/.test_token

Now you can run other tests in any Python environment:
   python test/test_rag_integration.py
======================================================================
```

**Note**: After running this once, other tests can run in any Python environment for 5 hours!

---

### `get_jwt_token.py`

**Purpose**: Retrieve JWT token for existing users

**Environment**: Any Python

**Usage**:
```bash
# Interactive mode
python test/get_jwt_token.py --interactive

# Use default account
python test/get_jwt_token.py

# Specify custom account
python test/get_jwt_token.py user@example.com password123
```

**Features**:
- Login with existing credentials
- Save token to `.jwt_token` file
- Display token validity information
- Use saved token or login fresh

---

## Backend Tests

### `test_file_upload.py`

**Purpose**: Test file upload functionality

**Environment**: `bread` (required - uses backend imports)

**Usage**:
```bash
conda activate bread
python test/test_file_upload.py
```

**What it tests**:
1. Creates test user and JWT token automatically
2. Uploads test PDF document
3. Verifies file storage
4. Retrieves user files list

**Success Indicators**:
- ✅ Status Code: 200
- ✅ File saved to `uploads/` directory
- ✅ User files retrieved successfully

---

### `test_concurrency.py` ⭐

**Purpose**: Test Backend concurrent performance

**Environment**: Any Python

**Usage**:
```bash
# Quick test (10 requests, 2 concurrency)
python test/test_concurrency.py quick

# Interactive mode (choose scenario)
python test/test_concurrency.py
```

**Test Scenarios**:
1. **Light**: 50 requests, 5 concurrency
2. **Medium**: 100 requests, 10 concurrency (recommended)
3. **Heavy**: 200 requests, 20 concurrency
4. **Extreme**: 500 requests, 50 concurrency
5. **Custom**: User-defined parameters

**Metrics Measured**:
- Success rate (%)
- QPS (Queries Per Second)
- Response time: average, min, max, median, std dev
- Throughput (successful requests/sec)

**Performance Ratings**:
- **Excellent**: QPS > 80 (high-performance configuration)
- **Good**: QPS 30-80 (meets production requirements)
- **Fair**: QPS 10-30 (might be using sync workers)
- **Poor**: QPS < 10 (might be Flask dev server)

**Example Output**:
```
======================================================================
 Concurrent Test
======================================================================
Test URL: http://localhost:8203/api/health
Total Requests: 100
Concurrency: 10
...

======================================================================
 Test Results
======================================================================
 Successful Requests: 100/100 (100.0%)
 Failed Requests: 0

  Response Time Statistics:
   Average: 0.007s
   Min: 0.004s
   Max: 0.015s
   Median: 0.007s
   Std Dev: 0.002s

 Performance Metrics:
   Total Time: 0.901s
   QPS (Queries Per Second): 1106.5
   Throughput: 1106.5 req/s

 Performance Evaluation:
   Rating:  Excellent (high-performance configuration)
   Suggestion: Outstanding performance!
```

---

## LLM Tests

### `test_current.py` ⭐

**Purpose**: Test currently running LLM service performance

**Environment**: Any Python

**Usage**:
```bash
# Default question
python test/test_current.py

# Custom question
python test/test_current.py "What is deep learning?"
```

**Features**:
- Auto-detects running LLM service (port 8610 or 8611)
- Measures Time to First Token (TTFT)
- Tracks streaming response
- Displays performance metrics
- Shows response preview

**Metrics**:
- **TTFT** (Time to First Token)
- **Total Time**
- **Response Speed** (chars/sec)
- **Chunk Count**

**Performance Evaluation**:
- **Excellent**: TTFT < 1 second
- **Good**: TTFT < 2 seconds
- **Acceptable**: TTFT < 3 seconds
- **Slow**: TTFT > 3 seconds

**Example Output**:
```
======================================================================
 LLM Service Performance Test
======================================================================

 Detecting running LLM services...
 Found running service: Optimized (8611)

======================================================================
 Testing: Optimized (8611)
======================================================================
Question: What is machine learning?

 Time to First Token (TTFT): 0.856s
   Received 20 chunks...
   Received 40 chunks...
 Completed!
   Total time: 3.245s
   Total chunks: 52
   Response length: 423 characters

======================================================================
 Performance Metrics
======================================================================
Time to First Token (TTFT): 0.856s
Total Time:                 3.245s
Response Speed:             130.4 chars/sec

 Performance Evaluation:
   Excellent! TTFT 0.86s < 1 second

 Response Preview:
----------------------------------------------------------------------
Machine learning is a subset of artificial intelligence that enables 
systems to learn and improve from experience without being explicitly 
programmed...
----------------------------------------------------------------------
```

---

### `test_llm_latency.py`

**Purpose**: Test LLM API latency and performance

**Environment**: Any Python

**Usage**:
```bash
# Default question
python test/test_llm_latency.py

# Custom question
python test/test_llm_latency.py "Explain neural networks"
```

**What it tests**:
- LLM service on port 8611
- Streaming response handling
- Time to First Token (TTFT)
- Total response time
- Response quality and preview

---

### `test_llm_response.py`

**Purpose**: Test LLM response generation

**Environment**: Any Python

**Usage**:
```bash
python test/test_llm_response.py
```

---

## RAG Integration Tests

### `test_rag_integration.py` ⭐

**Purpose**: Test complete RAG (Retrieval-Augmented Generation) workflow

**Environment**: Any Python (after token generation)

**Prerequisites**:
```bash
# First time: Generate token in bread environment
conda activate bread
python test/generate_test_token.py

# Then run test in any environment
python test/test_rag_integration.py
```

**Complete Workflow**:
1. ✅ Load saved authentication token
2. ✅ Upload machine learning tutorial document
3. ✅ Verify RAG indexing (`rag_indexed: true`)
4. ✅ Ask question about uploaded content
5. ✅ Verify LLM response uses RAG context
6. ✅ Test direct RAG retrieval API

**Test Document Content**:
- Machine Learning fundamentals
- Three types: Supervised, Unsupervised, Reinforcement Learning
- Key concepts: Training data, Features, Labels, Models

**Success Indicators**:
- File upload: HTTP 200
- RAG indexing: `rag_indexed: true`
- Chat response: Contains relevant context from document
- RAG retrieval: Returns matching documents

**Example Output**:
```
======================================================================
Testing RAG Integration with File Upload and Chat
======================================================================

[1] Loading authentication token...
✅ Token loaded from file
   User ID: 13
   Token: eyJhbGciOiJIUzI1NiIsInR5cCI6Ik...

[2] Creating test PDF content...

[3] Uploading file to backend...
Status Code: 200
Response: {
  "file_path": "uploads/13/20251123_100250_ml_tutorial.txt",
  "msg": "File uploaded successfully",
  "rag_indexed": true,
  "session_id": 104
}
✅ File uploaded successfully!
✅ Document indexed in RAG!

[4] Waiting for RAG indexing...

[5] Asking question about uploaded content...
Question: What are the three types of machine learning?
Streaming response:
----------------------------------------------------------------------
The three primary types of machine learning are:

1. **Supervised Learning**: This involves training a model using 
   labeled data...
2. **Unsupervised Learning**: Here, the model is trained using 
   unlabeled data...
3. **Reinforcement Learning**: In this type, an agent learns to make 
   decisions by interacting with an environment...
----------------------------------------------------------------------

[6] Testing direct RAG retrieval...
✅ RAG returned 3 results:

  1. Machine Learning Tutorial What is Machine Learning? ...
  2. Machine Learning Tutorial What is Machine Learning? ...
  3. Machine Learning Tutorial What is Machine Learning? ...

======================================================================
Test completed!
======================================================================

📊 Summary:
  - File upload: ✅
  - RAG indexing: ✅
  - Chat response: ✅
  - Response contains context: ✅
```

---

## Avatar Management Tests

### `test_manager.py` ⭐

**Purpose**: Test Avatar Manager functionality

**Environment**: Any Python

**Usage**:
```bash
# Basic test (auto-detects available avatars)
python test/test_manager.py

# Concurrent test (test multiple avatars)
python test/test_manager.py concurrent

# Individual operations
python test/test_manager.py health          # Health check
python test/test_manager.py list            # List running avatars
python test/test_manager.py status          # System status
python test/test_manager.py start <id>      # Start specific avatar
python test/test_manager.py stop <id>       # Stop specific avatar
```

**Key Features**:
- **Auto-discovery**: Scans `lip-sync/data/avatars/` for available avatars
- **Lifecycle testing**: Start, monitor, and stop avatars
- **GPU monitoring**: Displays GPU status and memory usage
- **Concurrent handling**: Test multiple avatars simultaneously

**What it tests**:
1. API health check
2. Avatar startup (PID, Port, GPU assignment, WebRTC URL)
3. List running avatars
4. System status (GPU memory, distribution)
5. Avatar shutdown
6. Concurrent avatar management

**Success Indicators**:
- ✅ Avatar started with valid PID and port
- ✅ GPU assigned correctly
- ✅ WebRTC URL generated
- ✅ System status shows accurate metrics

**Example Output**:
```
======================================================================
 Avatar Manager Basic Function Test
======================================================================

======================================================================
Test 1: API Health Check
======================================================================
 API healthy: avatar-manager v1.0

 Found 3 available avatar(s):
   - avatar_001
   - avatar_002
   - avatar_003

======================================================================
Test 2: Start Avatar (avatar_001)
======================================================================

Starting Avatar: avatar_001
 Started successfully:
   PID: 12345
   Port: 8701
   GPU: 0
   WebRTC: http://localhost:8701/webrtc

======================================================================
Currently Running Avatars:
======================================================================
  • avatar_001
    - Port: 8701
    - GPU: 0
    - Uptime: 5s

======================================================================
System Status:
======================================================================

Avatar Manager:
  Running: 1/10
  Available: 9
  GPU Distribution: {'0': 1, '1': 0}

GPU Status:
  GPU 0: NVIDIA GeForce RTX 3090
    Memory: 2.1GB / 24.0GB (8.8%)
    Temperature: 45°C

======================================================================
Test 3: Stop Avatar
======================================================================

Stopping Avatar: avatar_001
 Stopped successfully

======================================================================
 Basic Test Completed
======================================================================
```

---

## System Configuration Tests

### Test Configuration Files

These tests check the following configuration files:

```
/workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/
├── tts/
│   ├── config.json                 # TTS configuration
│   ├── model_info.json            # Model information
│   └── edge/taco/sovits/          # TTS server directories
├── lip-sync/
│   ├── data/avatars/
│   │   ├── test_yongen/config.json
│   │   └── test_two/config.json
│   └── app.py                     # Avatar application
├── backend/
│   ├── main.py                    # Backend main program
│   ├── config.py/.env             # Configuration files
│   └── routes/llm.py              # LLM routes
└── avatar-manager/
    └── manager.py                 # Avatar manager
```

---

## Running Tests

### Complete Test Suite

```bash
# 1. One-time setup (generate token)
conda activate bread
python test/generate_test_token.py

# 2. Backend tests (require bread environment)
conda activate bread
python test/test_file_upload.py

# 3. Performance tests (any environment)
python test/test_concurrency.py quick
python test/test_current.py

# 4. Integration tests (any environment)
python test/test_rag_integration.py

# 5. Avatar tests (any environment)
python test/test_manager.py

# 6. System configuration tests
python test/test_tts_generation.py
python test/test_video_generation.py
python test/test_llm_response.py
```

### Quick Test Run

```bash
# Generate token once
conda activate bread
python test/generate_test_token.py

# Run multiple tests (all in standard Python)
python test/test_concurrency.py quick  &&  \
python test/test_rag_integration.py    &&  \
python test/test_manager.py            &&  \
python test/test_current.py
```

### Run All Configuration Tests

```bash
# Method 1: Run comprehensive test script
python run_all_tests.py

# Method 2: Run individually
python test_tts_generation.py
python test_video_generation.py
python test_llm_response.py
```

---

## Troubleshooting

### Error: "No module named 'flask'"

**Problem**: Running test that requires backend imports in wrong environment

**Solution**:
```bash
# Option 1: Use bread environment
conda activate bread
python test/generate_test_token.py

# Option 2: For API-only tests, generate token first
conda activate bread
python test/generate_test_token.py
# Now can run in any environment
python test/test_rag_integration.py
```

---

### Error: "Cannot proceed without token"

**Problem**: JWT token not generated or expired (5-hour validity)

**Solution**:
```bash
conda activate bread
python test/generate_test_token.py
```

---

### Error: "Service unavailable" / Connection Errors

**Problem**: Required service not running

**Check services**:
```bash
curl http://localhost:8203/api/health    # Backend
curl http://localhost:8611/health        # LLM
curl http://localhost:8602/health        # RAG
curl http://localhost:8607/health        # Avatar Manager
```

**Start services**:
```bash
# Start all services
./scripts/start_all.sh

# Or start individually
cd backend && python run.py
cd llm && python api_interface_optimized.py
cd rag && python app.py
cd avatar-manager && python api.py
```

---

### TTS Service Failures

**Problem**: EdgeTTS/Tacotron service check fails

**Solution**:
```bash
# 1. Start TTS service
cd /workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2
python tts/tts.py

# 2. Verify service is running
netstat -tuln | grep 5033  # EdgeTTS
netstat -tuln | grep 8604  # Tacotron
```

---

### Backend Service Failures

**Problem**: Backend service check fails

**Solution**:
```bash
# 1. Start backend service
cd /workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/backend
python main.py

# 2. Verify service is running
netstat -tuln | grep 20000
```

---

### Missing Modules

**Problem**: Some Python modules not installed

**Solution**:
```bash
# Install missing modules
pip install edge-tts
pip install opencv-python numpy scipy pillow
pip install librosa soundfile moviepy
pip install ollama transformers torch langchain
```

---

### Error: "No available avatars found"

**Problem**: Avatar Manager test cannot find avatars

**Solution**:
```bash
# Check avatar directory
ls -la lip-sync/data/avatars/

# Ensure avatars exist with config.json files
```

---

### Error: Token Expired

**Problem**: JWT token validity expired (after 5 hours)

**Solution**:
```bash
conda activate bread
python test/generate_test_token.py
```

---

### Test Hangs or Timeout

**Problem**: Service not responding or slow

**Solutions**:
1. Check service logs for errors
2. Verify service is running on correct port
3. Increase timeout in test script if needed
4. Restart services

---

## Test Files Summary

| File | Purpose | Environment | Auth Required |
|------|---------|-------------|---------------|
| `generate_test_token.py` ⭐ | Generate JWT token | bread | No |
| `get_jwt_token.py` | Retrieve JWT token | Any | No |
| `test_file_upload.py` | File upload test | bread | Self-generates |
| `test_concurrency.py` ⭐ | Backend performance | Any | No |
| `test_current.py` ⭐ | LLM service test | Any | No |
| `test_llm_latency.py` | LLM performance | Any | No |
| `test_llm_response.py` | LLM response test | Any | No |
| `test_rag_integration.py` ⭐ | RAG workflow | Any | Yes (from file) |
| `test_manager.py` ⭐ | Avatar management | Any | No |
| `test_tts_generation.py` | TTS configuration | Any | No |
| `test_video_generation.py` | Video generation | Any | No |

⭐ = Recommended/Frequently used

---

## Test Result Interpretation

### ✓ PASSED
- Green checkmark indicates component is correctly configured
- Related services/modules are properly installed
- Component is ready for use

### ✗ FAILED
- Red X indicates component configuration is incomplete
- Action required to fix the issue
- System may not be able to use this functionality

### ⚠ WARNING
- Yellow warning indicates optional features or configuration
- System may still work but with limited functionality
- Recommended but not mandatory to fix

---

## Important Notes

1. **Port Requirements**: Ensure the following ports are not occupied:
   - 5033 (EdgeTTS)
   - 8604 (Tacotron)
   - 20000 (Backend)
   - Other LLM service ports

2. **Python Version**: Recommended Python 3.8+

3. **Dependency Installation**: Some tests may require specific system libraries:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-dev libsndfile1
   ```

4. **GPU Support**: Some components may require GPU:
   - Tacotron: GPU recommended
   - LLM: GPU acceleration recommended
   - System can still run without GPU but slower

---

## Extended Testing

After these pre-check tests, you can run integration tests:

```python
# Example: Test TTS generation
import requests

response = requests.post('http://127.0.0.1:20000/tts/response',
    data={
        'tts_text': 'Hello world',
        'prompt_text': None,
        'prompt_wav': None
    })

# Verify audio format
assert response.status_code == 200
assert response.content[:4] == b'RIFF'  # WAV format
```

---

## Notes

### Token Management
- Test tokens are valid for **5 hours**
- Tokens stored in Redis with TTL
- Saved to `.test_token` file for reuse
- Multiple tests can share the same token

### Test User
- **Email**: `test@example.com`
- **Password**: `password123`
- **Role**: `student`
- Auto-created by token generation script

### Test Independence
Tests are designed to be independent and can run in any order. However:
- `test_rag_integration.py` requires token generation first
- Avatar tests require avatars to be present in `lip-sync/data/avatars/`
- Performance tests require services to be running

---

## Feedback and Improvements

If you find any issues or have suggestions for improvement:

1. Check error messages in test output
2. Review relevant service log files
3. Verify configuration file contents
4. Ensure all dependencies are correctly installed

---

**Last Updated**: November 24, 2025  
**Version**: 2.0
