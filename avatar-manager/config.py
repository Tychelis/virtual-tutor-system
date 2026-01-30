"""Avatar Manager 配置文件"""

import sys
import os
# 添加项目根目录到路径，以便导入统一端口配置
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.ports_config import AVATAR_BASE_PORT, AVATAR_MANAGER_API_PORT, TTS_PORT, TTS_TACOTRON_PORT, get_tts_port_for_model

# Avatar管理配置
MAX_AVATARS = 5  # 最大Avatar数量
PRIMARY_GPU = 1  # 主要使用的GPU（0或1）- 改用GPU 1，因为GPU 0被LLM占用
BACKUP_GPU = 0   # 备用GPU

# 端口配置（从统一配置导入）
BASE_PORT = AVATAR_BASE_PORT  # Avatar起始端口
API_PORT = AVATAR_MANAGER_API_PORT   # Manager API端口

# Avatar启动配置
AVATAR_CONFIG = {
    'transport': 'webrtc',
    'model': 'musetalk',
    'max_session': 100,  # 每个Avatar支持100个并发连接（可根据服务器性能调整）
    'tts': 'edgetts',  # 改用edgetts（全小写，无需GPU，稳定可靠）
    'tts_server': f'http://127.0.0.1:{TTS_PORT}'  # 使用统一配置的TTS端口
}

# 路径配置
# 使用绝对路径以确保在不同工作目录下都能找到配置
LIP_SYNC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lip-sync'))
AVATAR_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lip-sync/data/avatars'))

# Conda环境配置
CONDA_INIT = '/workspace/conda/etc/profile.d/conda.sh'
CONDA_ENV = '/workspace/conda/envs/avatar'  # lip-sync使用的conda环境

# 超时配置（秒）
STARTUP_TIMEOUT = 30  # Avatar启动超时
IDLE_TIMEOUT = 1800   # 空闲30分钟自动关闭（0表示不自动关闭）
HEALTH_CHECK_INTERVAL = 60  # 健康检查间隔

# 日志配置
LOG_FILE = 'logs/avatar_manager.log'
LOG_LEVEL = 'INFO'

# 监控配置
ENABLE_MONITORING = True
MONITOR_INTERVAL = 10  # GPU监控间隔（秒）

