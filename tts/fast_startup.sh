# ========= 1. 启动tts服务 =========
uvicorn tts:app --reload --port 8102
uvicorn tts:app --host 0.0.0.0 --port 8204

# ========= 2. 启动avatar服务 =========
conda activate nerfstream
cd /workspace/share/yuntao/LiveTalking

# ========= 2. 测试模型列表 =========
curl http://127.0.0.1:8204/tts/models

# ========= 3. 测试模型启动 =========
# cosyvoice
curl -X POST http://127.0.0.1:8204/tts/start \
  -F "model_name=cosyvoice" \
  -F "port=5033" \
  -F "use_gpu=true"

# edgeTTS
curl -X POST http://127.0.0.1:8204/tts/start \
  -F "model_name=edgeTTS" \
  -F "port=5033" \
  -F "use_gpu=true"

# tacotron
curl -X POST http://127.0.0.1:8102/tts/start \
  -F "model_name=tacotron" \
  -F "port=5033" \
  -F "use_gpu=true"

# sovits
curl -X POST http://127.0.0.1:8204/tts/start \
  -F "model_name=sovits" \
  -F "port=5033" \
  -F "use_gpu=true"

# ========= 测试模型音色切换 =========
curl -X POST http://127.0.0.1:8102/tts/choose_timbre \
  -F "model_name=edgeTTS" \
  -F "timbre=en-US-GuyNeural"

curl -X POST http://127.0.0.1:8102/tts/choose_timbre \
  -F "model_name=edgeTTS" \
  -F "timbre=en-US-EmmaNeural"

curl -X POST http://127.0.0.1:8102/tts/choose_timbre \
  -F "model_name=tacotron" \
  -F "timbre=55"

# ========= 测试TTS生成 =========
curl -X POST http://127.0.0.1:8102/tts/response \
  -F "tts_text=Hello this is TutorNet speaking. Do you want a cup of coffee?" \
  -F "prompt_text=The course name COMP9331 is simply compained 3331." \
  -F "prompt_wav=@ref.wav" \
  --output output.pcm

# 播放原始 PCM（注意指定参数）
sox -t raw -r 24000 -e signed -b 16 -c 1 output.pcm output.wav


# ======== 直接测试tts server (need to switch env) ========
conda activate edge
python edge_server.py --model_name edgeTTS --port 8102 --use_gpu True

curl -X POST http://127.0.0.1:8102/generate \
  -F "tts_text=Hello this is TutorNet speaking. Do you want a cup of coffee?" \
  -F "prompt_text=en-US-GuyNeural" \
  -F "prompt_wav=@ref.wav" \
  -o output.wav

conda activate cosyvoice
python taco_server.py --model_name tacotron --port 8102 --use_gpu True

curl -X POST http://127.0.0.1:8102/generate \
  -F "tts_text=Hello this is TutorNet speaking. Do you want a cup of coffee?" \
  -F "prompt_text=40" \
  -F "prompt_wav=@ref.wav" \
  -o output.wav

conda activate sovits
python so_server.py --model_name sovits --port 8102 --use_gpu True

curl -X POST http://127.0.0.1:8102/generate \
  -F "tts_text=Hello this is TutorNet speaking. Do you want a cup of coffee?" \
  -F "prompt_text=The course name COMP9331 is simply compained 3331." \
  -F "prompt_wav=@ref.wav" \
  -o output.wav


# ========= 测试avatar服务 =========
curl -X POST http://127.0.0.1:8204/switch_avatar \
  -F "avatar_id=avator_1" \
  -F "ref_file=data/audio/ref_liu.wav"