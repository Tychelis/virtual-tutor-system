# 创建虚拟环境（以 conda 为例）
conda create -n vittts python=3.10 -y
conda activate vittts

# 安装 pytorch（根据你的系统和 CUDA）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

git clone https://github.com/jaywalnut310/vits.git
cd vits
pip install torch numpy scipy soundfile

sudo apt-get install espeak
cd monotonic_align
python setup.py build_ext --inplace
cd ..

pip install nemo_toolkit["tts"]