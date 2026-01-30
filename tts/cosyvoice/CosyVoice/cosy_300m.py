from cosyvoice.cli.cosyvoice import CosyVoice
from cosyvoice.utils.file_utils import load_wav
import torchaudio
import time
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import Response
import torchaudio
import sys
import os
import time
import warnings

sys.path.append('/workspace/chengxin/tts/cosyvoice2/CosyVoice/third_party/Matcha-TTS')
from cosyvoice.utils.file_utils import load_wav

warnings.filterwarnings("ignore")
cosyvoice = CosyVoice('pretrained_models/CosyVoice-300M')

start = time.time()
prompt = load_wav('ref.wav', 16000)
for i, res in enumerate(
        cosyvoice.inference_zero_shot(
            "Hello, this is TutorNet speaking. what do you need? do you want a cup of coffee?",
            "",
            prompt,
            stream=False
        )
):
    torchaudio.save(f"../output/output_300.wav", res['tts_speech'], cosyvoice.sample_rate)

end = time.time()
# get generated audio duration
duration = torchaudio.info("../output/output_300.wav").num_frames / cosyvoice.sample_rate
rtf = (end - start) / duration

print(f">>> RTF of CosyVoice-300M: {rtf:.4f}")
print(f">>> Duration of the input audio: {duration:.4f} seconds")
print(f">>> Total time taken: {end - start:.4f} seconds")
