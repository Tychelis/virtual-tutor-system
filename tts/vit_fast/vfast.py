from nemo.collections.tts.models import VitsModel
import soundfile as sf
import time
import numpy as np

# 加载预训练模型
audio_gen = VitsModel.from_pretrained("tts_en_lj_vits")
audio_gen.eval()

text = "Hello, this is TutorNet speaking. what do you need? do you want a cup of coffee?"
tokens = audio_gen.parse(text)

rts_list = []

for i in range(10):
    print(f"\n>>> Round {i+1}")
    start_time = time.time()

    # 合成语音
    audio = audio_gen.convert_text_to_waveform(tokens=tokens)

    end_time = time.time()

    # 保存音频
    filename = f"output_{i+1}.wav"
    sf.write(filename, audio.detach().cpu().numpy().T, 22050)
    print(f">>> Generated -> {filename}")

    # 计算持续时间和RTF
    audio_time = audio.shape[1] / 22050
    duration = end_time - start_time
    rtf = duration / audio_time
    rts_list.append(rtf)

    print(f"Audio duration: {audio_time:.4f} seconds.")
    print(f"Audio generation took {duration:.4f} seconds.")
    print(f">>> Audio RTF: {rtf:.4f}")

# 显示平均RTF
print(f"\nAverage RTF over 10 runs: {np.mean(rts_list):.4f}")