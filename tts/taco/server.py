from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import Response
from speechbrain.inference.TTS import Tacotron2
from speechbrain.inference.vocoders import HIFIGAN
import torchaudio
import torch
import io
import tempfile
import subprocess
import time
import torchaudio.transforms as T
import librosa
import soundfile as sf
import numpy as np
import argparse
import os
import uvicorn


def scale(x):
    if 0 <= x < 50:
        return (x - 0) / (50 - 0) * (0.8 - 0.5) + 0.5
    elif 51 <= x <= 100:
        return (x - 51) / (100 - 51) * (2.0 - 0.8) + 0.8
    elif x == 51:
        return 0.8
    else:
        return 1.0


def resample(sample_rate, resample_rate, audio_bytes):
    if sample_rate == resample_rate:
        return audio_bytes

    # 读取音频
    audio_tensor, sr = torchaudio.load(io.BytesIO(audio_bytes))
    resampler = T.Resample(orig_freq=sample_rate, new_freq=resample_rate)
    audio_resampled = resampler(audio_tensor)

    # 保存为 bytes
    buffer = io.BytesIO()
    torchaudio.save(buffer, audio_resampled.cpu(), resample_rate, format="wav")
    return buffer.getvalue()


def generate_tts(tts_text: str, sample_rate: int):
    mel_output, mel_length, alignment = tacotron2.encode_text(tts_text)
    waveforms = hifi_gan.decode_batch(mel_output)
    duration = waveforms.shape[-1] / sample_rate
    buffer = io.BytesIO()
    torchaudio.save(buffer, waveforms.squeeze(1).cpu(), sample_rate, format="wav")
    return buffer.getvalue(), duration


app = FastAPI()


@app.post("/generate")
async def tts_zero_shot(
        tts_text: str = Form(...),
        prompt_text: str = Form(...),
        prompt_wav: UploadFile = File(...)
):
    try:
        # 读取参考音频（即使不使用也要处理）
        # ref_wav_bytes = await prompt_wav.read()

        # 处理 prompt_text 为整数，用于控制采样率
        prompt_int = int(prompt_text) if prompt_text.isdigit() else 45
        print(f">>> Using scale factor: {prompt_int}")
        scale_factor = scale(prompt_int)
        sample_rate = int(scale_factor * 24000)
        sample_rate = (sample_rate // 100) * 100

        # 生成音频
        start = time.time()
        out_wav, duration = generate_tts(tts_text, sample_rate)
        out_wav_resampled = resample(sample_rate, 24000, out_wav)
        end = time.time()

        rtf = (end - start) / duration if duration > 0 else float('inf')
        print(f">>> Generated audio duration: {duration:.2f}s, RTF: {rtf:.4f}")

        # 保存临时输出（可选）
        with open("temp_out.wav", "wb") as f:
            f.write(out_wav_resampled)

        torch.cuda.empty_cache()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {e}")

    return Response(content=out_wav_resampled, media_type="audio/wav")


@app.get("/health")
def health():
    return {"status": "running"}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', required=True)
    parser.add_argument('--port', type=int, default=5033)
    parser.add_argument('--use_gpu', type=bool, default=True)

    args = parser.parse_args()
    if args.model_name == 'tacotron':
        print(f">>> Using Tacotron2 model: {args.model_name}")
    else:
        raise ValueError(f"Unsupported model name: {args.model_name}, only 'tacotron' is supported.")

    if args.use_gpu:
        print(">>> Using GPU for inference.")
        DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
        if DEVICE == "cpu":
            print(">>> Warning: GPU not available, using CPU for inference, this may be slow.")
    else:
        print(">>> Using CPU for inference, this may be slow.")
        DEVICE = "cpu"
    print(f">>> Loading TTS and Vocoder models on {DEVICE}...")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    tts_dir = os.path.join(script_dir, "tmpdir_tts")
    vocoder_dir = os.path.join(script_dir, "tmpdir_vocoder")
    tacotron2 = Tacotron2.from_hparams(
        source="speechbrain/tts-tacotron2-ljspeech",
        savedir=tts_dir,
        run_opts={"device": DEVICE}
    )
    hifi_gan = HIFIGAN.from_hparams(
        source="speechbrain/tts-hifigan-ljspeech",
        savedir=vocoder_dir,
        run_opts={"device": DEVICE}
    )
    print(">>> TTS and Vocoder models loaded successfully.")

    uvicorn.run(app, host='0.0.0.0', port=args.port)