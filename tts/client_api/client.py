import requests
from pydub import AudioSegment
import time


def get_response(text, voice="m0", output_path="./output.mp3"):
    """
    Get the TTS response from the server and save it to a file.

    :param text: The text to convert to speech.
    :param voice: The voice to use for the TTS (default is "m0").
    :param output_path: The path where the output audio file will be saved.
    """
    print(f"\n>>> Requesting TTS for voice [{voice}] with text: \n{text}")
    start = time.time()

    response = requests.post(
        "http://216.249.100.66:13645/v1/audio/speech",
        json={
            "input": text,  # Text
            "voice": voice,  # Select from [f0 - f4 (female), m0 - m4 (male)]
        }
    )
    if response.status_code != 200:
        print(f"请求失败，状态码：{response.status_code}")
        print(f"错误信息：{response.text}")
        return
    end = time.time()

    with open(output_path, "wb") as f:
        f.write(response.content)
    print(f"Response time: {(end - start):4f} seconds")

    audio = AudioSegment.from_file(output_path, format="mp3")
    duration = len(audio) / 1000  # 毫秒转秒
    print(f"RTF = {((end - start) / duration):.4f}")


if __name__ == "__main__":
    male_voices = ["m0", "m1"]
    female_voices = ["f0", "f1", "f2", "f3", "f4"]

    for voice in female_voices:
        text = "hello this is Tutornet speaking, what do you need? Do you want a cup of coffee?"
        output_path = f"./output_{voice}.mp3"
        get_response(text, voice=voice, output_path=output_path)

    for voice in male_voices:
        text = "hello this is Tutornet speaking, what do you need?"
        output_path = f"./output_{voice}.mp3"
        get_response(text, voice=voice, output_path=output_path)