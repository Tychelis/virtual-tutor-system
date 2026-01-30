import torch
import time
import io
import torchaudio
from speechbrain.inference.TTS import Tacotron2
from speechbrain.inference.vocoders import HIFIGAN


def generate_tts(tts_text: str, sample_rate: int = 24000):
    mel_output, mel_length, alignment = tacotron2.encode_text(tts_text)
    waveforms = hifi_gan.decode_batch(mel_output)
    duration = waveforms.shape[-1] / sample_rate

    # Save to in-memory buffer
    buffer = io.BytesIO()
    torchaudio.save(buffer, waveforms.squeeze(1).cpu(), sample_rate, format="wav")
    return buffer.getvalue(), duration, waveforms


def main(tts_text):
    sample_rate = 24000

    # Generate speech
    print(">>> Starting speech synthesis...")
    start = time.time()
    wav_bytes, duration, waveform = generate_tts(tts_text, sample_rate)
    end = time.time()

    rtf = (end - start) / duration if duration > 0 else float("inf")
    print(f">>> Synthesis completed in {end - start:.2f} seconds.")
    print(f">>> Output duration: {duration:.2f} seconds, RTF: {rtf:.4f}")

    # Save to file
    output_path = "demo_output.wav"
    torchaudio.save(output_path, waveform.squeeze(1).cpu(), sample_rate)
    print(f">>> Audio saved to {output_path}")
    print(f"===================================================\n")


if __name__ == "__main__":
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    print(f">>> Device selected: {DEVICE}")

    # Load models
    print(">>> Loading models...")
    tacotron2 = Tacotron2.from_hparams(
        source="speechbrain/tts-tacotron2-ljspeech",
        savedir="tmpdir_tts",
        run_opts={"device": DEVICE}
    )
    hifi_gan = HIFIGAN.from_hparams(
        source="speechbrain/tts-hifigan-ljspeech",
        savedir="tmpdir_vocoder",
        run_opts={"device": DEVICE}
    )
    print(">>> Models loaded successfully.")
    tts_text = "Hello, this is TutorNet speaking. what do you need? do you want a cup of coffee?"

    for _ in range(10):
        main(tts_text)

