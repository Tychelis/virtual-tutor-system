from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import Response
import os
import sys
import torch
import tempfile
import traceback
import torchaudio
import numpy as np
import soundfile as sf
from soundfile import info as sf_info
import argparse
# 添加 GPT-SoVITS 模块路径
import sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "GPT_SoVITS")
sys.path.append(BASE_DIR)
sys.path.append(MODEL_DIR)


# 获取当前文件的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 修正 os.getcwd() 被 sv.py 用作路径前缀的问题
os.chdir(BASE_DIR)  # sv.py 中使用 os.getcwd() 拼接相对路径，必须这样做

# 设置 sys.path，确保模块可以 import
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "GPT_SoVITS"))

from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config
print(">>> Initializing GPT-SoVITS model...")
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
config_path = "GPT_SoVITS/configs/tts_infer.yaml"
tts_config = TTS_Config(config_path)
sovits_model = TTS(tts_config)
print(">>> GPT-SoVITS model loaded!")

app = FastAPI()

def generate_tts_sovits(tts_text: str, ref_wav_bytes: bytes, prompt_text: str) -> bytes:
    import time
    start = time.time()
    # 将参考音频保存为临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
        tmp_wav.write(ref_wav_bytes)
        ref_audio_path = tmp_wav.name

    req = {
        "text": tts_text,
        "text_lang": 'en',
        "ref_audio_path": ref_audio_path,
        "aux_ref_audio_paths": [],
        "prompt_text": prompt_text,
        "prompt_lang": 'en',
        "top_k": 5,
        "top_p": 1.0,
        "temperature": 1.0,
        "text_split_method": "cut1",
        "batch_size": 1,
        "batch_threshold": 0.75,
        "split_bucket": True,
        "speed_factor": 1.0,
        "fragment_interval": 0.3,
        "seed": -1,
        "media_type": "wav",
        "streaming_mode": False,
        "parallel_infer": True,
        "repetition_penalty": 1.35,
        "sample_steps": 32,
        "super_sampling": False,
    }

    try:
        generator = sovits_model.run(req)
        sr, audio = next(generator)

        if audio.dtype != np.float32:
            audio = audio.astype(np.float32) / 32768.0  # 归一化

        audio_tensor = torch.from_numpy(audio).unsqueeze(0) if audio.ndim == 1 else torch.from_numpy(audio.T)

        # 采样率转换为 24000
        if sr != 24000:
            resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=24000)
            audio_tensor = resampler(audio_tensor)
            sr = 24000

        out_buf = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        torchaudio.save(out_buf.name, audio_tensor, sr)

        with open(out_buf.name, "rb") as f:
            result = f.read()

        duration = sf_info(out_buf.name).frames / sr
        end = time.time()
        print(f">>> RTF: {(end - start)/duration:.4f}")

        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"TTS 推理失败: {e}")
    finally:
        os.remove(ref_audio_path)

@app.post("/generate")
async def tts_zero_shot(
    tts_text: str = Form(...),
    prompt_text: str = Form(...),
    prompt_wav: UploadFile = File(...)
):
    try:
        ref_wav_bytes = await prompt_wav.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"读取参考音频失败: {e}")

    try:
        out_wav = generate_tts_sovits(tts_text, ref_wav_bytes, prompt_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return Response(content=out_wav, media_type="audio/wav")

@app.get('/health')
def health():
    return {"status": "running"}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', required=False, default="gpt-sovits")
    parser.add_argument('--port', type=int, default=5044)
    parser.add_argument('--use_gpu', type=bool, default=True)
    args = parser.parse_args()

    # 模型预热逻辑
    try:
        print(">>> Running warmup...")
        sample_text = "Hello, this is a warmup test."
        prompt_text = "This is a warm up audio, and here is another warm up audio."
        warmup_wav_path = os.path.join(BASE_DIR, "warmup.wav")
        if os.path.exists(warmup_wav_path):
            with open(warmup_wav_path, "rb") as f:
                ref_wav_bytes = f.read()
            generate_tts_sovits(sample_text, ref_wav_bytes, prompt_text)
            print(">>> Warmup completed!")
        else:
            print(f">>> Skipping warmup. Reference wav not found at {warmup_wav_path}")
    except Exception as e:
        print(f">>> Warmup failed: {e}")

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=args.port)