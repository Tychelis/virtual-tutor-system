
git clone https://github.com/RVC-Boss/GPT-SoVITS.git

conda create -n sovits python=3.9
conda activate sovits

cd GPT-SoVITS
bash install.sh


python3 - <<EOF
from huggingface_hub import snapshot_download
snapshot_download('lj1995/GPT-SoVITS', local_dir='GPT_SoVITS/pretrained_models')
EOF


uvicorn server:app --host 0.0.0.0 --port 8102 --workers 1

curl -X GET "http://localhost:8102/inference_zero_shot" \
  -F "tts_text=hello this is Tutornet speaking, what do you need? Do you want a cup of coffee?" \
  -F "prompt_text=the course name comp9331 is simply compained with comp3331." \
  -F "prompt_wav=@./ref.wav" \
  --output output.wav