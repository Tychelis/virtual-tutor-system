# TTS (Text-to-Speech) Service

## 📖 Overview

The TTS service is a **unified FastAPI-based gateway** that manages multiple Text-to-Speech models with dynamic model switching, voice cloning, and multi-timbre support. It provides a centralized API interface for the Virtual Tutor platform to generate natural speech from text.

### Key Features

- **🔄 Dynamic Model Switching** - Switch between 4 TTS models at runtime without restarting services
- **🎭 Multi-Model Support** - EdgeTTS, Tacotron2, CosyVoice2-0.5B, GPT-SoVITS
- **🎤 Voice Cloning** - One-shot voice cloning with reference audio (CosyVoice2, GPT-SoVITS)
- **🎵 Multi-Timbre Support** - 18+ pre-configured voices (male/female/Chinese)
- **⚡ GPU Acceleration** - Configurable GPU/CPU inference
- **🔌 RESTful API** - Clean HTTP API with health checks and status monitoring
- **📊 Performance Metrics** - Real-Time Factor (RTF) calculation for each generation
- **🎚️ Pitch Control** - Dynamic pitch adjustment (Tacotron2)
- **🌊 Streaming Output** - PCM audio streaming for real-time playback

## 🏗️ Architecture

### System Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    TTS Gateway (tts.py)                      │
│                    FastAPI on Port 8604                      │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Unified API Interface                                 │ │
│  │  • POST /tts/start       (Start TTS model)            │ │
│  │  • POST /tts/response    (Generate speech)            │ │
│  │  • GET  /tts/models      (List available models)      │ │
│  │  • POST /tts/choose_timbre (Select voice)             │ │
│  └────────────────────────────────────────────────────────┘ │
│                          ▼                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Model Manager                                         │ │
│  │  • Load model_info.json                                │ │
│  │  • Manage model lifecycle (start/stop)                 │ │
│  │  • Port allocation & process monitoring                │ │
│  │  • Timbre configuration                                │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────┐
│           TTS Model Servers (Dynamic Port 5033)              │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   EdgeTTS    │  │  Tacotron2   │  │ CosyVoice2   │     │
│  │   server.py  │  │  server.py   │  │  server.py   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐                                           │
│  │ GPT-SoVITS   │                                           │
│  │  server.py   │                                           │
│  └──────────────┘                                           │
│                                                              │
│  Common Endpoints:                                           │
│  • POST /generate            (Generate speech)               │
│  • GET  /health              (Health check)                  │
│  • POST /inference_zero_shot (Streaming output)              │
└──────────────────────────────────────────────────────────────┘
```

### Configuration Management

```
┌─────────────────────────────────────────────────────────┐
│                    config.json                          │
│  Runtime state (current model, port, PID, timbre)       │
│  • tts_server_port: 8604                                │
│  • current_tts_server: "edgeTTS"                        │
│  • tts_server_pid: 114535                               │
│  • tts_timbre: "FemaleA"                                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                 model_info.json                         │
│  Model metadata (env path, server path, timbres)        │
│  • full_name: Display name                              │
│  • clone: Voice cloning capability                      │
│  • license: Software license                            │
│  • env_path: Conda environment path                     │
│  • server_path: Model server script path                │
│  • status: "active" / "inactive"                        │
│  • timbres: Available voices                            │
│  • cur_timbre: Currently selected voice                 │
└─────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
tts/
├── tts.py                          # Main TTS gateway (Port 8604)
├── config.json                     # Runtime configuration (auto-generated)
├── model_info.json                 # Model metadata & capabilities
├── avatars.json                    # Avatar-timbre mapping
├── fast_startup.sh                 # Quick start script
│
├── edge/                           # EdgeTTS Model
│   ├── server.py                   # FastAPI server (Microsoft TTS wrapper)
│   ├── start.sh                    # Launch script
│   ├── env.sh                      # Environment setup
│   ├── logs/                       # Runtime logs
│   └── output/                     # Temporary audio files
│
├── taco/                           # Tacotron2 Model
│   ├── server.py                   # FastAPI server (SpeechBrain implementation)
│   ├── start.sh                    # Launch script
│   └── env.sh                      # Environment setup
│
├── cosyvoice/                      # CosyVoice2-0.5B Model
│   └── CosyVoice/
│       ├── server.py               # FastAPI server
│       ├── pretrained_models/      # Model weights
│       │   └── CosyVoice2-0.5B/
│       ├── third_party/            # Dependencies
│       │   └── Matcha-TTS/
│       ├── logs/
│       └── output/
│
├── sovits/                         # GPT-SoVITS Model
│   └── GPT-SoVITS/
│       ├── server.py               # FastAPI server
│       ├── GPT_SoVITS/             # Core model code
│       │   ├── configs/
│       │   │   └── tts_infer.yaml
│       │   └── TTS_infer_pack/
│       ├── logs/
│       └── output/
│
├── client_api/                     # Legacy client API (deprecated)
│   ├── client.py
│   └── output/
│
├── vit_fast/                       # VITS-Fast (experimental)
│
└── test/                           # Test scripts & demos
    ├── templates/
    │   └── index.html
    ├── main.py
    └── start_up.sh
```

## 🚀 Installation & Deployment

### Prerequisites

- **Python**: 3.8 or higher
- **Conda**: Anaconda or Miniconda
- **CUDA**: 11.8+ (optional, for GPU acceleration)
- **OS**: Linux (Ubuntu 20.04+ recommended)

### Step 1: Install Conda Environment

```bash
# Create base environment
conda create -n edge python=3.8 -y
conda activate edge

# Install dependencies for all models (shared environment)
pip install fastapi uvicorn httpx psutil edge-tts pydub
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install soundfile numpy librosa speechbrain

# For CosyVoice2 (if using)
pip install torchaudio IPython

# For GPT-SoVITS (if using)
pip install traceback
```

### Step 2: Download Model Weights

**CosyVoice2-0.5B:**
```bash
cd cosyvoice/CosyVoice/pretrained_models
# Download from official repository
# Place CosyVoice2-0.5B model files here
```

**GPT-SoVITS:**
```bash
cd sovits/GPT-SoVITS/GPT_SoVITS
# Download pretrained models
# Place model checkpoints in this directory
```

**Tacotron2 & EdgeTTS:**
- No manual downloads needed (uses SpeechBrain & Microsoft online API)

### Step 3: Configure Model Information

Edit `model_info.json` to match your environment:

```json
{
  "edgeTTS": {
    "full_name": "edgeTTS",
    "clone": false,
    "license": "MIT",
    "env_path": "/workspace/conda/envs/edge",      // ← Update this path
    "server_path": "/path/to/tts/edge/server.py",  // ← Update this path
    "status": "active",
    "timbres": ["Default", "MaleA", "FemaleA", ...],
    "cur_timbre": "FemaleA"
  }
}
```

### Step 4: Start TTS Gateway

```bash
cd tts

# Start the main TTS gateway on port 8604
uvicorn tts:app --host 0.0.0.0 --port 8604

# Or use the quick start script
bash fast_startup.sh
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8604
```

### Step 5: Start a TTS Model

```bash
# Option A: Use API to start model
curl -X POST "http://localhost:8604/tts/start" \
  -F "model_name=edgeTTS" \
  -F "port=5033" \
  -F "use_gpu=false"

# Option B: Use Python
import requests
response = requests.post('http://localhost:8604/tts/start', data={
    'model_name': 'edgeTTS',
    'port': 5033,
    'use_gpu': False
})
print(response.json())
```

**Response:**
```json
{
  "status": "success",
  "message": "TTS server 'edgeTTS' started successfully.",
  "port": 5033,
  "model_name": "edgeTTS",
  "use_gpu": false,
  "timbre": "FemaleA"
}
```

### Step 6: Generate Speech

```bash
curl -X POST "http://localhost:8604/tts/response" \
  -F "tts_text=Hello, welcome to the virtual tutor system!"

# Save to file
curl -X POST "http://localhost:8604/tts/response" \
  -F "tts_text=Hello world" \
  -o output.pcm
```

## 🎙️ TTS Models

### 1. EdgeTTS (Microsoft)

**Overview:**
- Microsoft Edge's internal TTS service wrapper
- **No GPU required** - runs on CPU
- 18+ pre-configured voices (English & Chinese)
- Fastest inference time (RTF < 0.1)
- Ideal for real-time applications

**Technical Details:**
- **Framework**: Python `edge-tts` SDK
- **Voice Cloning**: ❌ No (fixed voices only)
- **Language Support**: English, Chinese
- **Timbres**: 
  - English Male: MaleA-F (6 voices)
  - English Female: FemaleA-F (6 voices)
  - Chinese Male: ChineseMaleA-B
  - Chinese Female: ChineseFemaleA-B

**Implementation (`edge/server.py`):**
```python
async def generate_edge_tts(text: str, voice: str = "en-US-GuyNeural") -> bytes:
    communicate = edge_tts.Communicate(text, voice)
    out_buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            out_buf.write(chunk["data"])
    return out_buf.getvalue()
```

**Timbre Mapping:**
```python
EDGE_TIMVRES_MAP = {
    "MaleA": "en-US-GuyNeural",
    "FemaleA": "en-US-EmmaNeural",
    "ChineseMaleA": "zh-CN-YunjianNeural",
    "ChineseFemaleA": "zh-CN-XiaoxiaoNeural",
    ...
}
```

**Use Case:** Default TTS for low-latency applications

---

### 2. Tacotron2 (Google)

**Overview:**
- End-to-end Seq2Seq TTS architecture
- SpeechBrain implementation with HiFi-GAN vocoder
- **GPU recommended** (10x faster than CPU)
- Pitch control via sampling rate adjustment
- Good quality for English speech

**Technical Details:**
- **Framework**: SpeechBrain + PyTorch
- **Voice Cloning**: ❌ No
- **Language Support**: English only
- **Timbres**: 5 pitch levels (MaleA/B, FemaleA/B, Default)
- **Vocoder**: HiFi-GAN

**Architecture:**
```
Text → Tacotron2 Encoder → Attention → Decoder → Mel-Spectrogram
                                                          ↓
                                                    HiFi-GAN Vocoder
                                                          ↓
                                                    Audio Waveform (24kHz)
```

**Implementation (`taco/server.py`):**
```python
def generate_tts(tts_text: str, sample_rate: int):
    mel_output, mel_length, alignment = tacotron2.encode_text(tts_text)
    waveforms = hifi_gan.decode_batch(mel_output)
    duration = waveforms.shape[-1] / sample_rate
    buffer = io.BytesIO()
    torchaudio.save(buffer, waveforms.squeeze(1).cpu(), sample_rate, format="wav")
    return buffer.getvalue(), duration
```

**Pitch Control:**
- `prompt_text` parameter controls pitch (0-100)
- 0-50: Lower pitch (0.5x-0.8x speed)
- 50: Default pitch (1.0x)
- 50-100: Higher pitch (0.8x-2.0x speed)

**Use Case:** High-quality English speech with pitch customization

---

### 3. CosyVoice2-0.5B (Alibaba)

**Overview:**
- Transformer-based large language model for TTS
- **500M parameters** (lightweight version)
- **Voice cloning** with reference audio
- Natural prosody and emotion
- GPU required (VRAM: 4GB+)

**Technical Details:**
- **Framework**: PyTorch + Custom Transformer
- **Voice Cloning**: ✅ Yes (one-shot, 3-10s reference audio)
- **Language Support**: Multilingual (English, Chinese)
- **Sample Rate**: 16kHz → 24kHz (auto-resampling)

**Architecture:**
```
Reference Audio (3-10s) → Phoneme Encoder → Cross-Attention
                                                    ↓
Text → Phoneme Sequence → Transformer Decoder → Mel-Spectrogram
                                                    ↓
                                              Built-in Vocoder
                                                    ↓
                                              Audio Waveform
```

**Implementation (`cosyvoice/CosyVoice/server.py`):**
```python
def generate_tts(tts_text: str, ref_wav_bytes: bytes, prompt_text: str) -> bytes:
    ref_audio_buf = io.BytesIO(ref_wav_bytes)
    prompt_speech, sr = torchaudio.load(ref_audio_buf)
    
    # Resample to 16kHz
    resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
    prompt_speech = resampler(prompt_speech)
    
    # Generate with instruct mode
    chunks = list(model.inference_instruct2(
        tts_text, "", prompt_speech, stream=False
    ))
    waveform = chunks[0]["tts_speech"]
    
    out_buf = io.BytesIO()
    torchaudio.save(out_buf, waveform, model.sample_rate, format="wav")
    return out_buf.getvalue()
```

**Model Loading:**
```python
model = CosyVoice2(
    model_dir="pretrained_models/CosyVoice2-0.5B",
    load_jit=False,
    load_trt=False,
    load_vllm=False,
    fp16=False
)
```

**Use Case:** Voice cloning for personalized avatars

---

### 4. GPT-SoVITS (Community)

**Overview:**
- GPT + So-VITS hybrid architecture
- **Voice cloning** with few-shot samples
- Highest quality output (naturalness + clarity)
- GPU required (VRAM: 6GB+)
- Slower inference (RTF: 0.5-1.5)

**Technical Details:**
- **Framework**: PyTorch + Custom GPT + So-VITS
- **Voice Cloning**: ✅ Yes (one-shot, 5-15s reference audio)
- **Language Support**: English, Chinese
- **Sample Rate**: Dynamic → 24kHz (auto-resampling)
- **Configuration**: `GPT_SoVITS/configs/tts_infer.yaml`

**Architecture:**
```
Reference Audio + Prompt Text → Speaker Encoder → Speaker Embedding
                                                          ↓
Text → GPT Encoder → Acoustic Features → So-VITS Decoder
                                                          ↓
                                                   Audio Waveform
```

**Implementation (`sovits/GPT-SoVITS/server.py`):**
```python
def generate_tts_sovits(tts_text: str, ref_wav_bytes: bytes, prompt_text: str) -> bytes:
    # Save reference audio to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
        tmp_wav.write(ref_wav_bytes)
        ref_audio_path = tmp_wav.name
    
    req = {
        "text": tts_text,
        "text_lang": 'en',
        "ref_audio_path": ref_audio_path,
        "prompt_text": prompt_text,
        "prompt_lang": 'en',
        "top_k": 5,
        "top_p": 1.0,
        "temperature": 1.0,
        "speed_factor": 1.0,
        "repetition_penalty": 1.35,
        "sample_steps": 32,
        ...
    }
    
    generator = sovits_model.run(req)
    sr, audio = next(generator)
    
    # Resample to 24kHz
    audio_tensor = torch.from_numpy(audio)
    if sr != 24000:
        resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=24000)
        audio_tensor = resampler(audio_tensor)
    
    return audio_bytes
```

**Configuration Parameters:**
- `top_k`, `top_p`, `temperature`: Control randomness
- `repetition_penalty`: Avoid repeated patterns
- `speed_factor`: Adjust speaking speed (0.5-2.0)
- `fragment_interval`: Pause between sentences

**Use Case:** Highest quality voice cloning for premium avatars

## 🔌 API Documentation

### Base URL
```
http://localhost:8604
```

---

### 1. Start TTS Model

**Endpoint:** `POST /tts/start`

**Description:** Start a specific TTS model on a given port. If a model is already running, it will be stopped first.

**Request Parameters (Form-Data):**
```
model_name  (string, required) - Model name: "edgeTTS", "tacotron", "cosyvoice", "sovits"
port        (int, optional)    - Port number (default: 5033)
use_gpu     (bool, optional)   - Use GPU acceleration (default: true)
```

**Example Request:**
```bash
curl -X POST "http://localhost:8604/tts/start" \
  -F "model_name=edgeTTS" \
  -F "port=5033" \
  -F "use_gpu=false"
```

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "TTS server 'edgeTTS' started successfully.",
  "port": 5033,
  "model_name": "edgeTTS",
  "use_gpu": false,
  "timbre": "FemaleA"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid model name or port already in use
- `500 Internal Server Error` - Model startup timeout (>60s)

---

### 2. Generate Speech

**Endpoint:** `POST /tts/response`

**Description:** Generate speech from text using the currently running TTS model. Returns audio in PCM format.

**Request Parameters (Form-Data):**
```
tts_text    (string, required)     - Text to convert to speech
prompt_text (string, optional)     - Voice timbre or reference text (model-specific)
prompt_wav  (file, optional)       - Reference audio for voice cloning (CosyVoice2, GPT-SoVITS)
```

**Example Request (No Cloning):**
```bash
curl -X POST "http://localhost:8604/tts/response" \
  -F "tts_text=Hello, welcome to the virtual tutor system!" \
  -o output.pcm
```

**Example Request (With Voice Cloning):**
```bash
# Start CosyVoice2 first
curl -X POST "http://localhost:8604/tts/start" \
  -F "model_name=cosyvoice" \
  -F "port=5033"

# Generate with reference audio
curl -X POST "http://localhost:8604/tts/response" \
  -F "tts_text=This is a cloned voice" \
  -F "prompt_text=This is the reference text" \
  -F "prompt_wav=@reference.wav" \
  -o cloned_output.pcm
```

**Response (200 OK):**
- Content-Type: `application/octet-stream`
- Body: Raw PCM audio data (16-bit, 24kHz, mono)

**Model-Specific Behavior:**
- **EdgeTTS**: `prompt_text` is ignored (uses `cur_timbre` from config)
- **Tacotron2**: `prompt_text` is pitch level (0-100)
- **CosyVoice2**: `prompt_text` + `prompt_wav` for voice cloning
- **GPT-SoVITS**: `prompt_text` + `prompt_wav` for voice cloning

**Error Responses:**
- `503 Service Unavailable` - No TTS server running (call `/tts/start` first)
- `500 Internal Server Error` - TTS generation failed

---

### 3. List Available Models

**Endpoint:** `GET /tts/models`

**Description:** Get information about all available TTS models, including capabilities and available timbres.

**Example Request:**
```bash
curl -X GET "http://localhost:8604/tts/models"
```

**Response (200 OK):**
```json
{
  "edgeTTS": {
    "full_name": "edgeTTS",
    "clone": false,
    "status": "active",
    "license": "MIT",
    "timbres": [
      "Default", "MaleA", "MaleB", "MaleC", "MaleD", "MaleE", "MaleF",
      "FemaleA", "FemaleB", "FemaleC", "FemaleD", "FemaleE", "FemaleF",
      "ChineseMaleA", "ChineseMaleB", "ChineseFemaleA", "ChineseFemaleB"
    ],
    "cur_timbre": "FemaleA"
  },
  "tacotron": {
    "full_name": "TacoTron2",
    "clone": false,
    "status": "active",
    "license": "MIT",
    "timbres": ["Default", "MaleA", "MaleB", "FemaleA", "FemaleB"],
    "cur_timbre": "Default"
  },
  "cosyvoice": {
    "full_name": "CosyVoice2",
    "clone": true,
    "status": "active",
    "license": "MIT",
    "timbres": [],
    "cur_timbre": ""
  },
  "sovits": {
    "full_name": "GPT-SoViTs",
    "clone": true,
    "status": "active",
    "license": "MIT",
    "timbres": ["The course name COMP9331 is simply compained 3331."],
    "cur_timbre": "The course name COMP9331 is simply compained 3331."
  }
}
```

**Field Descriptions:**
- `full_name`: Display name of the model
- `clone`: Whether the model supports voice cloning
- `status`: "active" or "inactive"
- `license`: Software license
- `timbres`: List of available pre-configured voices (empty for cloning models)
- `cur_timbre`: Currently selected voice

---

### 4. Choose Timbre

**Endpoint:** `POST /tts/choose_timbre`

**Description:** Select a specific timbre/voice for a model. Only works for models without voice cloning (EdgeTTS, Tacotron2).

**Request Parameters (Form-Data):**
```
model_name  (string, required) - Model name
timbre      (string, required) - Timbre name from available list
```

**Example Request:**
```bash
curl -X POST "http://localhost:8604/tts/choose_timbre" \
  -F "model_name=edgeTTS" \
  -F "timbre=MaleC"
```

**Response (200 OK):**
```json
{
  "model_name": "edgeTTS",
  "timbres": [
    "Default", "MaleA", "MaleB", "MaleC", "MaleD", "MaleE", "MaleF",
    "FemaleA", "FemaleB", "FemaleC", "FemaleD", "FemaleE", "FemaleF",
    "ChineseMaleA", "ChineseMaleB", "ChineseFemaleA", "ChineseFemaleB"
  ],
  "cur_timbre": "MaleC"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid model name or timbre not in available list
- `500 Internal Server Error` - Failed to update configuration

---

## 🔄 Typical Workflow

### Scenario 1: Using Pre-Configured Voices (EdgeTTS)

```python
import requests

# 1. Start EdgeTTS model
response = requests.post('http://localhost:8604/tts/start', data={
    'model_name': 'edgeTTS',
    'port': 5033,
    'use_gpu': False
})
print(response.json())
# {"status": "success", "model_name": "edgeTTS", ...}

# 2. Choose a female voice
response = requests.post('http://localhost:8604/tts/choose_timbre', data={
    'model_name': 'edgeTTS',
    'timbre': 'FemaleB'
})
print(response.json())
# {"model_name": "edgeTTS", "cur_timbre": "FemaleB"}

# 3. Generate speech
response = requests.post('http://localhost:8604/tts/response', data={
    'tts_text': 'Hello! How can I help you today?'
})

# 4. Save audio
with open('output.pcm', 'wb') as f:
    f.write(response.content)

# 5. Convert PCM to WAV (optional)
import subprocess
subprocess.run([
    'ffmpeg', '-f', 's16le', '-ar', '24000', '-ac', '1',
    '-i', 'output.pcm', 'output.wav'
])
```

---

### Scenario 2: Voice Cloning (CosyVoice2)

```python
import requests

# 1. Start CosyVoice2 model (requires GPU)
response = requests.post('http://localhost:8604/tts/start', data={
    'model_name': 'cosyvoice',
    'port': 5033,
    'use_gpu': True
})
print(response.json())

# 2. Prepare reference audio (3-10 seconds)
reference_audio_path = 'reference_voice.wav'
reference_text = 'This is the reference text spoken in the audio.'

# 3. Generate cloned speech
with open(reference_audio_path, 'rb') as ref_file:
    response = requests.post('http://localhost:8604/tts/response', 
        data={
            'tts_text': 'This is a test of voice cloning technology.',
            'prompt_text': reference_text
        },
        files={
            'prompt_wav': ref_file
        }
    )

# 4. Save cloned audio
with open('cloned_output.pcm', 'wb') as f:
    f.write(response.content)
```

---

### Scenario 3: Model Switching

```python
import requests

# Current: EdgeTTS running
# Want to: Switch to GPT-SoVITS

# 1. Start new model (old model auto-stops)
response = requests.post('http://localhost:8604/tts/start', data={
    'model_name': 'sovits',
    'port': 5033,
    'use_gpu': True
})
print(response.json())
# Old EdgeTTS process is killed automatically

# 2. Generate with new model
with open('reference.wav', 'rb') as ref_file:
    response = requests.post('http://localhost:8604/tts/response',
        data={
            'tts_text': 'Testing GPT-SoVITS voice cloning.',
            'prompt_text': 'The course name COMP9331 is simply compained 3331.'
        },
        files={'prompt_wav': ref_file}
    )

with open('sovits_output.pcm', 'wb') as f:
    f.write(response.content)
```

---

## 🔧 Troubleshooting

### Issue 1: Port Already in Use

**Symptoms:**
```json
{
  "detail": "Port 5033 is already in use. Please choose a different port."
}
```

**Solution:**
```bash
# Find process using the port
sudo lsof -i :5033

# Kill the process
kill -9 <PID>

# Or use a different port
curl -X POST "http://localhost:8604/tts/start" \
  -F "model_name=edgeTTS" \
  -F "port=5034"
```

---

### Issue 2: Model Startup Timeout

**Symptoms:**
```json
{
  "detail": "TTS 模型服务启动超时（超过 60 秒）"
}
```

**Solutions:**
1. Check conda environment path in `model_info.json`
2. Verify model server script exists: `server_path`
3. Test model server manually:
```bash
conda activate edge
python edge/server.py --model_name edgeTTS --port 5033 --use_gpu false
```
4. Check logs in `edge/logs/` or `cosyvoice/logs/`

---

### Issue 3: No TTS Server Running

**Symptoms:**
```json
{
  "detail": "No TTS server is currently running."
}
```

**Solution:**
```bash
# Start a model first
curl -X POST "http://localhost:8604/tts/start" \
  -F "model_name=edgeTTS" \
  -F "port=5033"

# Then generate speech
curl -X POST "http://localhost:8604/tts/response" \
  -F "tts_text=test"
```

---

### Issue 4: CUDA Out of Memory (GPU Models)

**Symptoms:**
```
RuntimeError: CUDA out of memory. Tried to allocate 512.00 MiB
```

**Solutions:**
1. Use smaller model:
   - CosyVoice2-0.5B (4GB VRAM) instead of GPT-SoVITS (6GB)
   - Tacotron2 (2GB VRAM)
2. Reduce batch size in model config
3. Enable CPU mode:
```bash
curl -X POST "http://localhost:8604/tts/start" \
  -F "model_name=cosyvoice" \
  -F "use_gpu=false"
```
4. Clear GPU cache:
```python
import torch
torch.cuda.empty_cache()
```

---

### Issue 5: Poor Voice Cloning Quality

**Symptoms:**
- Robotic voice
- Wrong accent
- Unnatural prosody

**Solutions:**
1. **Reference Audio Requirements:**
   - Duration: 3-10 seconds (CosyVoice2), 5-15 seconds (GPT-SoVITS)
   - Quality: Clean, no background noise
   - Format: WAV, 16kHz or 24kHz, mono
   - Content: Clear speech matching prompt_text

2. **Improve Reference Audio:**
```bash
# Convert to proper format
ffmpeg -i input.mp3 -ar 24000 -ac 1 -sample_fmt s16 reference.wav

# Remove noise (optional)
ffmpeg -i input.wav -af "highpass=f=200, lowpass=f=3000" clean.wav
```

3. **Adjust Model Parameters (GPT-SoVITS):**
   - Increase `sample_steps`: 32 → 64 (slower but better)
   - Lower `temperature`: 1.0 → 0.7 (more stable)
   - Adjust `repetition_penalty`: 1.35 → 1.5 (less repetition)

---

### Issue 6: EdgeTTS Wrong Voice

**Symptoms:**
- Selected "FemaleA" but got male voice
- Timbre change not taking effect

**Solution:**
```bash
# Check current configuration
curl -X GET "http://localhost:8604/tts/models"

# Choose correct timbre
curl -X POST "http://localhost:8604/tts/choose_timbre" \
  -F "model_name=edgeTTS" \
  -F "timbre=FemaleA"

# Restart model to apply changes (may not be necessary)
curl -X POST "http://localhost:8604/tts/start" \
  -F "model_name=edgeTTS" \
  -F "port=5033"
```

---

### Issue 7: PCM Audio Not Playable

**Symptoms:**
- Downloaded `.pcm` file won't play
- Media players don't recognize format

**Solution:**
```bash
# Convert PCM to WAV
ffmpeg -f s16le -ar 24000 -ac 1 -i output.pcm output.wav

# Or use Python
import wave
import numpy as np

with open('output.pcm', 'rb') as f:
    pcm_data = f.read()

pcm_array = np.frombuffer(pcm_data, dtype=np.int16)

with wave.open('output.wav', 'wb') as wav_file:
    wav_file.setnchannels(1)  # Mono
    wav_file.setsampwidth(2)  # 16-bit
    wav_file.setframerate(24000)  # 24kHz
    wav_file.writeframes(pcm_data)
```

---

## 📊 Performance Benchmarks

### Real-Time Factor (RTF)

RTF = Generation Time / Audio Duration

Lower is better. RTF < 1.0 means real-time generation.

| Model          | GPU (RTX 3090) | CPU (Intel i9) | VRAM Usage |
|----------------|----------------|----------------|------------|
| EdgeTTS        | 0.05-0.08      | 0.08-0.12      | N/A        |
| Tacotron2      | 0.15-0.25      | 1.5-2.5        | 2 GB       |
| CosyVoice2-0.5B| 0.30-0.50      | 3.0-5.0        | 4 GB       |
| GPT-SoVITS     | 0.50-1.20      | 5.0-10.0       | 6 GB       |

**Test Conditions:**
- Input: 20-word English sentence
- Reference audio: 5 seconds (for cloning models)
- Batch size: 1

---

## 🎯 Model Selection Guide

| Use Case                          | Recommended Model | Reason                          |
|-----------------------------------|-------------------|---------------------------------|
| Real-time chat                    | EdgeTTS           | Fastest, no GPU required        |
| High-quality English TTS          | Tacotron2         | Good balance of quality & speed |
| Personalized avatars (fast)       | CosyVoice2-0.5B   | Fast voice cloning, 4GB VRAM    |
| Premium voice cloning             | GPT-SoVITS        | Best quality, needs 6GB VRAM    |
| Multilingual support              | EdgeTTS           | 18+ voices (EN + CN)            |
| Pitch-adjustable voices           | Tacotron2         | 5 pitch levels                  |
| Low-resource servers (CPU only)   | EdgeTTS           | No GPU required                 |
| Production deployment             | EdgeTTS           | Most stable, lowest RTF         |

---

## 🛠️ Development Guide

### Adding a New TTS Model

1. **Create model directory:**
```bash
mkdir tts/my_model
cd tts/my_model
```

2. **Implement server.py:**
```python
from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import Response
import uvicorn

app = FastAPI()

@app.post("/generate")
async def tts_generate(
    tts_text: str = Form(...),
    prompt_text: str = Form(""),
    prompt_wav: UploadFile = File(...)
):
    # Your TTS logic here
    audio_bytes = your_tts_function(tts_text)
    return Response(content=audio_bytes, media_type="audio/wav")

@app.get("/health")
def health():
    return {"status": "running"}

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', type=str, required=True)
    parser.add_argument('--port', type=int, default=5033)
    parser.add_argument('--use_gpu', type=str, default='True')
    args = parser.parse_args()
    
    use_gpu = args.use_gpu.lower() == 'true'
    print(f"Starting {args.model_name} on port {args.port}, GPU: {use_gpu}")
    
    uvicorn.run(app, host="0.0.0.0", port=args.port)
```

3. **Add to model_info.json:**
```json
{
  "my_model": {
    "full_name": "My Custom TTS Model",
    "clone": false,
    "license": "MIT",
    "env_path": "/path/to/conda/env",
    "server_path": "/path/to/tts/my_model/server.py",
    "status": "active",
    "timbres": ["Default", "MaleA", "FemaleA"],
    "cur_timbre": "Default"
  }
}
```

4. **Test the model:**
```bash
# Start model via gateway
curl -X POST "http://localhost:8604/tts/start" \
  -F "model_name=my_model" \
  -F "port=5033"

# Generate speech
curl -X POST "http://localhost:8604/tts/response" \
  -F "tts_text=Hello world" \
  -o test_output.pcm
```

---

## 📚 References

### Research Papers

1. **Tacotron2:**
   - [Natural TTS Synthesis by Conditioning WaveNet on Mel Spectrogram Predictions](https://arxiv.org/abs/1712.05884)
   - Google Research, 2017

2. **HiFi-GAN:**
   - [HiFi-GAN: Generative Adversarial Networks for Efficient and High Fidelity Speech Synthesis](https://arxiv.org/abs/2010.05646)
   - 2020

3. **CosyVoice:**
   - [CosyVoice: A Scalable Multilingual Zero-shot Text-to-speech Synthesizer](https://arxiv.org/abs/2407.05407)
   - Alibaba Group, 2024

4. **GPT-SoVITS:**
   - Community-driven project combining GPT and So-VITS architectures
   - [GitHub Repository](https://github.com/RVC-Boss/GPT-SoVITS)

### Official Documentation

- **EdgeTTS SDK**: https://github.com/rany2/edge-tts
- **SpeechBrain**: https://speechbrain.github.io/
- **FastAPI**: https://fastapi.tiangolo.com/
- **PyTorch**: https://pytorch.org/docs/stable/index.html

---

**Version**: 2.0.0  
**Last Updated**: 2025-11-18  
**Maintainer**: Virtual Tutor Development Team
