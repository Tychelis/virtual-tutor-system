from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import Response
import torchaudio
import sys
import os
import time
import warnings

sys.path.append('/workspace/chengxin/tts/cosyvoice2/CosyVoice/third_party/Matcha-TTS')
from cosyvoice.cli.cosyvoice import CosyVoice2
from cosyvoice.utils.file_utils import load_wav

warnings.filterwarnings("ignore")
print(f">>> Python executable: {sys.executable}")

output_dir = '../output'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print(">>> Initializing CosyVoice2 model...")
model_dir = 'pretrained_models/CosyVoice2-0.5B'
model = CosyVoice2(
    model_dir=model_dir,
    load_jit=False,
    load_trt=False,
    load_vllm=False,
    fp16=False
)
print(f">>> Model loaded from {model_dir}!")

# 加载参考语音
prompt = load_wav('ref.wav', 16000)
tts_text = "Hello, this is TutorNet speaking. what do you need? do you want a cup of coffee?"

rtf_list = []

for i in range(10):
    print(f"\n>>> Round {i + 1}/10: Generating TTS output...")
    start = time.time()

    chunks = list(
        model.inference_instruct2(
            tts_text,
            "",
            prompt,
            stream=False
        )
    )
    waveform = chunks[0]["tts_speech"]
    output_path = f"../output/output_0.5b_round_{i+1}.wav"
    torchaudio.save(output_path, waveform, model.sample_rate)

    end = time.time()
    duration = torchaudio.info(output_path).num_frames / model.sample_rate
    rtf = (end - start) / duration
    rtf_list.append(rtf)

    print(f">>> Duration: {duration:.4f} s | Time taken: {end - start:.4f} s")
    print(f">>> RTF for round {i + 1}: {rtf:.4f}")

avg_rtf = sum(rtf_list) / len(rtf_list)

print("\n=============== Summary ===============\n")
print(f">>> RTF of round 1: {rtf_list[0]:.4f}")
print(f">>> RTF of round 2: {rtf_list[1]:.4f}")
print(f">>> RTF of round 3: {rtf_list[2]:.4f}")
print(f">>> RTF of round 4: {rtf_list[3]:.4f}")
print(f">>> RTF of round 5: {rtf_list[4]:.4f}")
print(f">>> RTF of round 6: {rtf_list[5]:.4f}")
print(f">>> RTF of round 7: {rtf_list[6]:.4f}")
print(f">>> RTF of round 8: {rtf_list[7]:.4f}")
print(f">>> RTF of round 9: {rtf_list[8]:.4f}")
print(f">>> RTF of round 10: {rtf_list[9]:.4f}")
print(f"\n>>> Average RTF over 10 rounds: {avg_rtf:.4f}")