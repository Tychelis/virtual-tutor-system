# 下载安装 miniconda
#wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
#bash Miniconda3-latest-Linux-x86_64.sh
#source ~/.bashrc

conda create -n cosyvoice2 python=3.10.12
conda activate cosyvoice2

conda install pytorch==2.0.1 torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia
pip install tensorflow==2.13.0

# sudo apt install -y ffmpeg sox libsox-dev
ffmpeg -version
sox --version
dpkg -s libsox-dev

git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git
cd CosyVoice
pip install -r requirements.txt
pip install modelscope

# 下载预训练模型
mkdir -p pretrained_models
python3 - <<EOF
from modelscope import snapshot_download
snapshot_download('iic/CosyVoice2-0.5B', local_dir='pretrained_models/CosyVoice2-0.5B')
EOF

python3 - <<EOF
from modelscope import snapshot_download
snapshot_download('iic/CosyVoice-300M', local_dir='pretrained_models/CosyVoice-300M')
EOF

#uvicorn server:app --host 0.0.0.0 --port 8102 --workers 1
#
#curl -v -X GET http://127.0.0.1:8102/tts_zero_shot \
#  -F "tts_text=this is a test" \
#  -F "prompt_text=reftext" \
#  -F "prompt_wav=@ref.wav;type=audio/wav" \
#  --output out.wav