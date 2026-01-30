#!/usr/bin/env python3
"""
TTS配置管理器
负责读取Avatar的TTS配置并确保正确的TTS服务在运行
"""

import os
import json
import time
import requests
import subprocess
from typing import Dict, Optional, Tuple
from logger import logger


class TTSConfigManager:
    """TTS配置管理器"""
    
    def __init__(self, working_directory: str = None):
        if working_directory is None:
            working_directory = os.path.dirname(os.path.abspath(__file__))
        self.working_directory = working_directory
        self.avatars_dir = os.path.join(working_directory, "data", "avatars")
        
        # TTS模型到启动命令的映射
        self.tts_commands = {
            "edgeTTS": {
                "env": "edge",
                "port": 8604,
                "server_path": "../tts/edge/server.py",
                "args": ["--model_name", "edgeTTS", "--port", "8604", "--use_gpu", "false"]
            },
            "sovits": {
                "env": "sovits",
                "port": 8604,
                "server_path": "../tts/sovits/GPT-SoVITS/so_server.py",
                "args": ["--model_name", "sovits", "--port", "8604"]
            },
            "cosyvoice": {
                "env": "cosyvoice2",
                "port": 8604,
                "server_path": "../tts/cosyvoice/CosyVoice/server.py",
                "args": ["--model_name", "cosyvoice", "--port", "8604"]
            },
            "tacotron": {
                "env": "edge",  # 使用edge环境
                "port": 8604,
                "server_path": "../tts/taco/taco_server.py",
                "args": ["--model_name", "tacotron", "--port", "8604"]
            }
        }
    
    def load_avatar_config(self, avatar_id: str) -> Optional[Dict]:
        """
        加载Avatar的配置文件
        
        Args:
            avatar_id: Avatar ID
            
        Returns:
            配置字典，如果不存在返回None
        """
        config_path = os.path.join(self.avatars_dir, avatar_id, "config.json")
        
        if not os.path.exists(config_path):
            logger.warning(f"Avatar config not found: {config_path}")
            return None
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"Loaded avatar config for {avatar_id}: {config}")
            return config
        except Exception as e:
            logger.error(f"Failed to load avatar config: {e}")
            return None
    
    def get_current_tts(self, port: int = 8604) -> Optional[str]:
        """
        获取当前运行的TTS模型
        
        Args:
            port: TTS服务端口
            
        Returns:
            当前TTS模型名称，如果无法确定返回None
        """
        try:
            # 尝试通过health endpoint获取
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            if response.status_code == 200:
                # 尝试从响应中获取模型信息
                try:
                    data = response.json()
                    if "model" in data:
                        return data["model"]
                except:
                    pass
                return "running"  # 有服务运行但无法确定模型
        except requests.RequestException:
            return None
    
    def stop_tts_service(self, port: int = 8604) -> bool:
        """
        停止TTS服务
        
        Args:
            port: TTS服务端口
            
        Returns:
            是否成功停止
        """
        try:
            # 查找占用端口的进程
            import psutil
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == psutil.CONN_LISTEN and conn.laddr.port == port:
                    pid = conn.pid
                    if pid:
                        logger.info(f"Stopping TTS service on port {port} (PID: {pid})")
                        os.kill(pid, 9)
                        time.sleep(1)
                        return True
            logger.info(f"No TTS service found on port {port}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop TTS service: {e}")
            return False
    
    def start_tts_service(self, model_name: str, port: int = 8604) -> bool:
        """
        启动指定的TTS服务
        
        Args:
            model_name: TTS模型名称
            port: TTS服务端口
            
        Returns:
            是否成功启动
        """
        if model_name not in self.tts_commands:
            logger.error(f"Unknown TTS model: {model_name}")
            return False
        
        config = self.tts_commands[model_name]
        
        # 构建启动命令
        conda_path = "/workspace/conda/etc/profile.d/conda.sh"
        env_name = config["env"]
        server_path = os.path.join(self.working_directory, config["server_path"])
        
        if not os.path.exists(server_path):
            logger.error(f"TTS server script not found: {server_path}")
            return False
        
        # 构建完整的启动命令
        command = f"""
source {conda_path} && \
conda activate {env_name} && \
cd {os.path.dirname(server_path)} && \
nohup python {os.path.basename(server_path)} {' '.join(config['args'])} > /tmp/tts_{model_name}.log 2>&1 &
"""
        
        try:
            logger.info(f"Starting TTS service: {model_name}")
            logger.debug(f"Command: {command}")
            
            # 执行启动命令
            process = subprocess.Popen(
                command,
                shell=True,
                executable='/bin/bash',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 等待服务启动
            max_wait = 30
            wait_interval = 1
            for i in range(max_wait):
                time.sleep(wait_interval)
                try:
                    response = requests.get(f"http://localhost:{port}/health", timeout=2)
                    if response.status_code == 200:
                        logger.info(f"TTS service {model_name} started successfully")
                        return True
                except:
                    pass
                
                if i % 5 == 0:
                    logger.info(f"Waiting for TTS service to start... ({i}/{max_wait}s)")
            
            logger.error(f"TTS service {model_name} failed to start within {max_wait}s")
            return False
            
        except Exception as e:
            logger.error(f"Failed to start TTS service: {e}")
            return False
    
    def ensure_correct_tts(self, avatar_id: str) -> Tuple[bool, str]:
        """
        确保正确的TTS服务在运行
        
        Args:
            avatar_id: Avatar ID
            
        Returns:
            (success, tts_server_url)
        """
        # 加载Avatar配置
        config = self.load_avatar_config(avatar_id)
        
        if config is None:
            logger.warning(f"No config found for avatar {avatar_id}, using default edgeTTS")
            required_tts = "edgeTTS"
        else:
            required_tts = config.get("tts_model", "edgeTTS")
        
        logger.info(f"Avatar {avatar_id} requires TTS model: {required_tts}")
        
        # 检查当前TTS
        current_tts = self.get_current_tts()
        
        if current_tts and current_tts != "running":
            if current_tts == required_tts:
                logger.info(f"TTS service {required_tts} is already running")
                return True, "http://127.0.0.1:8604"
        
        # 需要切换TTS
        logger.info(f"Switching TTS from {current_tts} to {required_tts}")
        
        # 停止当前TTS服务
        if current_tts:
            if not self.stop_tts_service():
                logger.warning("Failed to stop current TTS service, attempting to start new one anyway")
        
        # 启动新的TTS服务
        if self.start_tts_service(required_tts):
            return True, "http://127.0.0.1:8604"
        else:
            logger.error(f"Failed to start TTS service {required_tts}")
            
            # 尝试启动默认的edgeTTS作为fallback
            if required_tts != "edgeTTS":
                logger.info("Attempting to start edgeTTS as fallback")
                if self.start_tts_service("edgeTTS"):
                    return True, "http://127.0.0.1:8604"
            
            return False, ""
    
    def get_avatar_tts_info(self, avatar_id: str) -> Dict:
        """
        获取Avatar的TTS信息用于显示
        
        Args:
            avatar_id: Avatar ID
            
        Returns:
            TTS信息字典
        """
        config = self.load_avatar_config(avatar_id)
        
        if config is None:
            return {
                "tts_model": "edgeTTS",
                "timbre": "Default",
                "has_config": False
            }
        
        return {
            "tts_model": config.get("tts_model", "edgeTTS"),
            "timbre": config.get("timbre", ""),
            "ref_audio": config.get("ref_audio", ""),
            "has_config": True,
            "created_at": config.get("created_at", "")
        }


# 全局实例
_tts_manager = None

def get_tts_manager() -> TTSConfigManager:
    """获取TTS配置管理器单例"""
    global _tts_manager
    if _tts_manager is None:
        _tts_manager = TTSConfigManager()
    return _tts_manager


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python tts_config_manager.py <avatar_id>")
        sys.exit(1)
    
    avatar_id = sys.argv[1]
    manager = TTSConfigManager()
    
    print(f"\n=== Testing TTS Config Manager for Avatar: {avatar_id} ===\n")
    
    # 测试加载配置
    print("1. Loading avatar config...")
    config = manager.load_avatar_config(avatar_id)
    if config:
        print(f"   Config: {json.dumps(config, indent=2)}")
    else:
        print("   No config found")
    
    # 测试获取当前TTS
    print("\n2. Checking current TTS service...")
    current = manager.get_current_tts()
    print(f"   Current TTS: {current}")
    
    # 测试获取TTS信息
    print("\n3. Getting TTS info...")
    info = manager.get_avatar_tts_info(avatar_id)
    print(f"   TTS Info: {json.dumps(info, indent=2)}")
    
    # 测试确保正确TTS
    print("\n4. Ensuring correct TTS service...")
    success, url = manager.ensure_correct_tts(avatar_id)
    print(f"   Success: {success}, URL: {url}")






