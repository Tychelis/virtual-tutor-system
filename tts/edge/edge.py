import io
import time
import asyncio
import edge_tts
from pydub import AudioSegment


async def generate_edge_tts(text: str, voice: str = "en-US-GuyNeural") -> bytes:
    communicate = edge_tts.Communicate(text, voice)
    out_buf = io.BytesIO()

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            out_buf.write(chunk["data"])

    return out_buf.getvalue()


async def main():
    tts_text = "Hello, this is TutorNet speaking. what do you need? do you want a cup of coffee?"
    character = "en-US-GuyNeural"

    print(f">>> Generating TTS for: [{tts_text}] with voice: {character}")
    start_time = time.time()
    audio_bytes = await generate_edge_tts(tts_text, character)
    end_time = time.time()

    # 计算音频持续时间（单位：秒）
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
    duration = len(audio) / 1000

    # 计算 RTF（实时系数）
    rtf = (end_time - start_time) / duration

    # 保存音频到文件
    output_path = "output/edge_tts.mp3"
    with open(output_path, "wb") as f:
        f.write(audio_bytes)
    print(f">>> Output saved to {output_path}")
    print(f">>> Audio duration: {duration:.4f} seconds")
    print(f">>> RTF: {rtf:.4f} (Real-Time Factor)")


# 启动主程序
asyncio.run(main())