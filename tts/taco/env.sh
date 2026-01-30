conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
conda create -n taco2 python=3.10.12 -y
conda activate taco2

pip install speechbrain
pip install uvicorn
pip install torchaudio
pip install soundfile
pip install python-multipart
pip install fastapi
pip install librosa