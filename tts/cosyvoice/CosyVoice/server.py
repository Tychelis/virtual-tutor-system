from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import Response
import io
import uvicorn
import torchaudio
import soundfile as sf
import numpy as np
import os
import sys
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAT_DIR = os.path.join(BASE_DIR, "third_party", "Matcha-TTS")
MODEL05B_DIR = os.path.join(BASE_DIR, "pretrained_models", "CosyVoice2-0.5B")
sys.path.append(MAT_DIR)  # 若有第三方子模块
from cosyvoice.cli.cosyvoice import CosyVoice2
import torchaudio
from IPython.display import Audio
from cosyvoice.utils.file_utils import load_wav
from soundfile import info
import soundfile as sf

import warnings

warnings.filterwarnings("ignore")

import sys

print(f">>> Python executable: {sys.executable}\n")

print(">>> Initializing CosyVoice2 model...")
model_dir = MODEL05B_DIR
model = CosyVoice2(
    model_dir=model_dir,
    load_jit=False,
    load_trt=False,
    load_vllm=False,
    fp16=False
)
print(f">>> Model loaded from {model_dir}!")

app = FastAPI()


def generate_tts(tts_text: str, ref_wav_bytes: bytes, prompt_text: str) -> bytes:
    ref_audio_buf = io.BytesIO(ref_wav_bytes)
    prompt_speech, sr = torchaudio.load(ref_audio_buf)
    print(f">>> Reference audio sample rate: {sr}")
    # 强制重采样为 16000Hz
    resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
    prompt_speech = resampler(prompt_speech)

    # 生成 TTS 音频
    print(">>> Generating TTS output...")
    print(f">>> TTS text: {tts_text}")
    chunks = list(
        model.inference_instruct2(
            tts_text,
            "",
            prompt_speech,
            stream=False
        )
    )
    waveform = chunks[0]["tts_speech"]

    # 将 waveform 写入内存中的 WAV 二进制流
    out_buf = io.BytesIO()
    torchaudio.save(out_buf, waveform, model.sample_rate, format="wav")
    out_wav_bytes = out_buf.getvalue()

    return out_wav_bytes


@app.post("/generate")
async def tts_zero_shot(
        tts_text: str = Form(...),
        prompt_text: str = Form(...),
        prompt_wav: UploadFile = File(...)
):
    # 1. 读取上传的参考音频
    try:
        ref_wav_bytes = await prompt_wav.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Load wav failed : {e}")

    # 2. 调用你的 TTS 生成函数
    try:
        import time
        start = time.time()
        out_wav: bytes = generate_tts(tts_text, ref_wav_bytes, prompt_text)
        end = time.time()

        info_out = sf.info(io.BytesIO(out_wav))
        sample_rate = info_out.samplerate
        duration_out = info_out.frames / sample_rate
        print(f">>> Generated wav sample rate: {sample_rate}")

        # calc rtf
        rtf = (end - start) / duration_out
        print(f">>> RTF: {rtf:.4f} (Real-Time Factor)")

        # save output in temp file
        with open("temp_out.wav", "wb") as f:
            f.write(out_wav)
        print(f">>> Output saved to temp_out.wav")

        import torch
        torch.cuda.empty_cache()
    except Exception as e:
        # 内部运算失败
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {e}")

    # 3. 返回整个 WAV 二进制流
    return Response(content=out_wav, media_type="audio/wav")


@app.get('/health')
def health():
    return {"status": "running"}


# Alias for /generate to support /inference_zero_shot endpoint
@app.get("/inference_zero_shot")
async def tts_zero_shot_get(
        tts_text: str = Form(...),
        prompt_text: str = Form(...),
        prompt_wav: UploadFile = File(...)
):
    return await tts_zero_shot(tts_text, prompt_text, prompt_wav)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', required=True)
    parser.add_argument('--port', type=int, default=5033)
    parser.add_argument('--use_gpu', type=bool, default=True)
    # 实际上 model_name & use_gpu 参数在 CosyVoice2 中未使用（必须用GPU运算），
    # 但保留以兼容原有接口
    args = parser.parse_args()

    uvicorn.run(app, host='0.0.0.0', port=args.port)