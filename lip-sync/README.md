# Lip-Sync Module

## Introduction

The Lip-Sync module is a core component of the intelligent digital human mentor system, responsible for implementing real-time audio-video synchronization for digital human dialogues. This module combines synthesized audio with digital human models to generate lip-synchronized videos, enabling digital humans to "speak" naturally.

Main features include:
- Real-time lip synchronization generation
- Video background blur processing
- Support for multiple digital human models
- Audio and video streaming processing
- WebRTC output support

## Acknowledgment

This module heavily utilizes code from the [LiveTalking](https://github.com/lipku/LiveTalking) project. We acknowledge and appreciate the excellent work of the original authors that has made our implementation possible. The LiveTalking project provides the core functionalities for real-time digital human animation and lip synchronization that we have adapted and integrated into our intelligent mentor system.

## System Requirements

### Hardware Requirements
- **GPU**: NVIDIA GPU, CUDA 11.3 or higher, at least 24GB video memory
- **Network**: Stable internet connection with an upload bandwidth of at least 5Mbps

### Software Requirements
- Python 3.10
- CUDA 11.3+
- Conda package manager
- FFmpeg

## Installation Guide

### 1. Configure the LiveTalking Module

All lip-sync related code is located in the lip-sync folder. By default, the following operations are run in the lip-sync folder.

```bash
# Create conda environment
conda create -n nerfstream python=3.10
conda activate nerfstream

# Install PyTorch
# Choose the installation command according to your CUDA version: https://pytorch.org/get-started/previous-versions/
conda install pytorch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 pytorch-cuda=12.4 -c pytorch -c nvidia

# Install MuseTalk related modules
conda install ffmpeg
pip install --no-cache-dir -U openmim 
mim install mmengine 
mim install "mmcv==2.1.0" 
# Compilation process may use a lot of CPU resources, please monitor CPU usage
mim install "mmdet==3.2.0" 
mim install "mmpose>=1.1.0"

# Download model files
# Download model files from https://drive.google.com/file/d/18Cj9hTO5WcByMVQa2Q1OHKmK8JEsqISy/view?usp=sharing
# After downloading, extract the files to the models folder
```

After installation is complete, modify the `lip-sync.json` file:
- Set `conda_init` to the path of the conda activation script
- Set `conda_env` to the location of the nerfstream environment
- Set `working_directory` to the directory where the lip-sync module is located

### 2. Configure the Video Background Blur Module

This module is used to implement the background blur function when users upload video files. This module uses gRPC service calls and requires a gRPC server to be started. The related code is in the blur subfolder of the lip-sync folder.

```bash
# First download the human segmentation model from GitHub
# Download human_segmentation_pphumanseg_2023mar.onnx

# Then run the following commands in the terminal
conda activate nerfstream
cd blur
```

### 3. Configure the MuseTalk Module

This project uses the MuseTalk project to generate inference intermediate files. For specific configuration methods, please refer to the MuseTalk project: https://github.com/TMElyralab/MuseTalk

```bash
# Get MuseTalk
git clone https://github.com/TMElyralab/MuseTalk.git
cd MuseTalk

# Create a conda environment according to the MuseTalk guide
conda create -n MuseTalk python==3.10
conda activate MuseTalk

# Option 1: Using pip to install PyTorch
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118

# Option 2: Using conda to install PyTorch
conda install pytorch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 pytorch-cuda=11.8 -c pytorch -c nvidia

# Install required packages
pip install -r requirements.txt

pip install --no-cache-dir -U openmim
mim install mmengine
mim install "mmcv==2.0.1"
mim install "mmdet==3.1.0"
mim install "mmpose==1.1.0"

# Set FFMPEG
export FFMPEG_PATH=/path/to/ffmpeg
# Example:
export FFMPEG_PATH=/musetalk/ffmpeg-4.4-amd64-static

# Download weights
bash ./download_weights.sh
```

After installing MuseTalk, modify the following configurations in `lip-sync.json`:
- Set `muse_conda_env` to the path of the conda environment in MuseTalk
- Set `ffmpeg_path` to the path of the installed ffmpeg
- Set `muse_talk_base` to the path of the folder where MuseTalk is located

## Starting Services

For the lip-sync module, you need to start the GRPC server that provides background blur service and the server that provides the lip-sync backend service. The ports occupied by the two servers can be modified in `lip-sync.json`.

Default ports:
- Lip-sync backend service: 8205
- Background blur service: 23002

```bash
# Start the blur server, if port 23002 is already in use, use another port
cd blur
conda activate nerfstream
python blur_server.py

# Start the lip-sync backend server in another terminal window
cd lip-sync   # Return to the lip-sync root directory
conda activate nerfstream
python live_server.py
```

## Common Issues

If you encounter installation or running problems, please refer to the following suggestions:

1. Ensure NVIDIA drivers and CUDA versions are compatible
2. Check if there is enough video memory (at least 24GB required)
3. Ensure all dependency packages are correctly installed
4. Check if the `lip-sync.json` configuration is correct

## Testing

All test code for the lip-sync module is located in the `test/` folder. These tests verify the functionality of API. 

The test results are saved in the test report in the `../doc` folder


