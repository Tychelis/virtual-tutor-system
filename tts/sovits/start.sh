PORT=${1:-50000}

cd /workspace/chengxin/tts/sovits/GPT-SoVITS
uvicorn server:app --host 0.0.0.0 --port $PORT --workers 1
