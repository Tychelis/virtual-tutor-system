"""Avatar Manager - 核心管理模块"""

import subprocess
import os
import signal
import time
import logging
import json
from typing import Dict, Optional, List
from datetime import datetime
import psutil
import threading

# Try to import pynvml for GPU memory management
try:
    import pynvml
    pynvml.nvmlInit()
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False
    print("Warning: pynvml not available, GPU memory checking disabled")
except Exception as e:
    NVML_AVAILABLE = False
    print(f"Warning: Failed to initialize pynvml: {e}")

from config import (
    MAX_AVATARS, PRIMARY_GPU, BACKUP_GPU, BASE_PORT,
    AVATAR_CONFIG, LIP_SYNC_PATH, AVATAR_DATA_PATH, STARTUP_TIMEOUT,
    LOG_FILE, LOG_LEVEL, CONDA_INIT, CONDA_ENV, TTS_PORT, TTS_TACOTRON_PORT, get_tts_port_for_model
)

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AvatarManager')


class AvatarInstance:
    """Avatar实例类"""
    
    def __init__(self, avatar_id: str, port: int, gpu_id: int, process: subprocess.Popen, real_avatar_name: str = None):
        self.avatar_id = avatar_id  # 实例ID (g_user_1)
        self.real_avatar_name = real_avatar_name or avatar_id  # 真实名称 (g)
        self.port = port
        self.gpu_id = gpu_id
        self.process = process
        self.pid = process.pid
        self.start_time = datetime.now()
        self.last_activity = datetime.now()
        self.connections = 0
    
    def is_running(self) -> bool:
        """检查进程是否运行"""
        return self.process.poll() is None
    
    def get_info(self) -> dict:
        """获取实例信息"""
        return {
            'avatar_id': self.avatar_id,
            'real_avatar_name': self.real_avatar_name,
            'port': self.port,
            'gpu': self.gpu_id,
            'pid': self.pid,
            'running': self.is_running(),
            'start_time': self.start_time.isoformat(),
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
            'webrtc_url': f'http://localhost:{self.port}/offer',
            'connections': self.connections
        }
    
    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity = datetime.now()
    
    def get_idle_seconds(self) -> float:
        """获取空闲时间（秒）"""
        return (datetime.now() - self.last_activity).total_seconds()


class AvatarManager:
    """Avatar管理器"""
    
    def __init__(self, max_instances: int = MAX_AVATARS, primary_gpu: int = PRIMARY_GPU):
        self.max_instances = max_instances
        self.primary_gpu = primary_gpu
        self.backup_gpu = BACKUP_GPU
        self.instances: Dict[str, AvatarInstance] = {}  # key: instance_id (g_user_1)
        self.avatar_map: Dict[str, str] = {}  # 映射: real_avatar_name -> instance_id
        self.base_port = BASE_PORT
        self._lock = threading.Lock()  # 添加线程锁防止并发端口分配冲突
        self._allocating_ports: set = set()  # 正在分配中的端口集合（防止并发冲突）
        
        logger.info(f"Avatar Manager 初始化")
        logger.info(f"  最大实例数: {self.max_instances}")
        logger.info(f"  主GPU: {self.primary_gpu}")
        logger.info(f"  起始端口: {self.base_port}")
    
    def _allocate_port(self, exclude_port: Optional[int] = None) -> int:
        """分配端口（检查manager内部和系统层面的端口占用）
        
        Args:
            exclude_port: 要排除的端口（用于避免分配正在使用的端口）
        """
        # 获取已在manager中注册的端口（包括所有实例，无论是否运行）
        used_ports = {inst.port for inst in self.instances.values()}
        
        # 调试：打印所有已注册的实例信息
        if self.instances:
            instance_info = [(inst.avatar_id, inst.port, inst.is_running()) for inst in self.instances.values()]
            logger.info(f"已注册实例详情: {instance_info}")
        
        # 合并正在分配中的端口（防止并发冲突）
        used_ports.update(self._allocating_ports)
        
        # 如果有排除的端口，也加入已使用列表
        if exclude_port is not None:
            used_ports.add(exclude_port)
        
        # 添加详细日志
        logger.info(f"端口分配检查: 已注册端口={sorted(used_ports)}, 正在分配中={sorted(self._allocating_ports)}, instances数量={len(self.instances)}")
        
        for i in range(self.max_instances):
            port = self.base_port + i
            
            # 跳过已使用的端口（包括正在分配中的）
            if port in used_ports:
                logger.debug(f"端口 {port} 已在manager中注册或正在分配中，跳过")
                continue
            
            # 双重检查：先检查系统层面，再检查manager内部（防止并发）
            if not self._is_port_available(port):
                logger.warning(f"端口 {port} 在系统层面已被占用，跳过")
                continue
            
            # 再次检查manager内部（防止在检查期间有新实例注册）
            if port in {inst.port for inst in self.instances.values()} or port in self._allocating_ports:
                logger.warning(f"端口 {port} 在二次检查时发现已被占用，跳过")
                continue
            
            # 立即标记为正在分配中，防止并发时重复分配
            self._allocating_ports.add(port)
            logger.info(f"分配端口 {port} (系统检查通过，已标记为分配中)")
            return port
        
        raise Exception("无可用端口")
    
    def _is_port_available(self, port: int) -> bool:
        """检查端口在系统层面是否可用
        
        Args:
            port: 端口号
            
        Returns:
            True if port is available, False otherwise
        """
        try:
            # 使用psutil检查端口是否被占用
            connections = psutil.net_connections(kind='inet')
            for conn in connections:
                if conn.status == psutil.CONN_LISTEN:
                    if conn.laddr and conn.laddr.port == port:
                        logger.warning(f"端口 {port} 已被进程 PID {conn.pid} 占用 (状态: {conn.status})")
                        return False
            logger.debug(f"端口 {port} 在系统层面可用")
            return True
        except (psutil.AccessDenied, psutil.NoSuchProcess) as e:
            # 如果检查失败，保守地认为端口不可用
            logger.warning(f"无法检查端口 {port} 状态 (权限问题): {e}")
            return False
        except Exception as e:
            # 其他异常，记录详细信息但保守地认为端口不可用
            logger.error(f"检查端口 {port} 状态时发生异常: {e}", exc_info=True)
            return False

    def _wait_for_port_binding(self, port: int, timeout: int = 30) -> bool:
        """等待端口真正被subprocess bind（socket成功监听）

        通过主动轮询检查，验证subprocess是否已成功绑定到指定端口
        这替代了之前依赖time.sleep()的不可靠方式

        Args:
            port: 端口号
            timeout: 最大等待时间（秒）

        Returns:
            True if port successfully bound and listening, False if timeout
        """
        import socket
        start_time = time.time()
        poll_interval = 0.1  # 100ms轮询间隔

        while time.time() - start_time < timeout:
            try:
                # 尝试连接到该端口，如果成功说明socket已listening
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex(('127.0.0.1', port))
                sock.close()

                if result == 0:
                    elapsed = time.time() - start_time
                    logger.info(f"✓ 端口 {port} socket已成功bind (耗时: {elapsed:.2f}秒)")
                    return True
            except Exception as e:
                logger.debug(f"Socket验证异常 (端口{port}): {type(e).__name__}")

            time.sleep(poll_interval)

        elapsed = time.time() - start_time
        logger.error(f"✗ 端口 {port} socket验证超时 (等待{elapsed:.1f}秒,超时{timeout}秒)")
        return False

    def _get_gpu_memory_info(self, gpu_id: int) -> Optional[dict]:
        """获取GPU显存信息
        
        Returns:
            dict with 'total', 'used', 'free' in MB, or None if unavailable
        """
        if not NVML_AVAILABLE:
            return None
        
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_id)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            return {
                'total': info.total / (1024 ** 2),  # Convert to MB
                'used': info.used / (1024 ** 2),
                'free': info.free / (1024 ** 2)
            }
        except Exception as e:
            logger.warning(f"Failed to get GPU {gpu_id} memory info: {e}")
            return None
    
    def _allocate_gpu(self, required_mb: int = 11000) -> int:
        """自动分配GPU，选择显存最充足的GPU
        
        Args:
            required_mb: 需要的显存（MB），默认11GB（降低阈值以便更好分配）
        
        Returns:
            GPU ID
        """
        # 获取所有可用的GPU
        available_gpus = [self.primary_gpu, self.backup_gpu]
        
        if not NVML_AVAILABLE:
            # 如果无法获取GPU信息，使用简单的轮询策略
            logger.warning("NVML not available, using simple round-robin GPU allocation")
            gpu_usage = {}
            for inst in self.instances.values():
                gpu_id = inst.gpu_id
                gpu_usage[gpu_id] = gpu_usage.get(gpu_id, 0) + 1
            
            # 选择使用最少的GPU
            best_gpu = self.primary_gpu
            min_count = gpu_usage.get(self.primary_gpu, 0)
            
            for gpu_id in available_gpus:
                count = gpu_usage.get(gpu_id, 0)
                if count < min_count:
                    min_count = count
                    best_gpu = gpu_id
            
            logger.info(f"Allocated GPU {best_gpu} (round-robin, instances: {gpu_usage})")
            return best_gpu
        
        # 基于显存分配
        best_gpu = self.primary_gpu
        max_free_mb = -1
        candidates_with_enough_mem = []
        
        for gpu_id in available_gpus:
            mem_info = self._get_gpu_memory_info(gpu_id)
            if mem_info is None:
                continue
            
            free_mb = mem_info['free']
            used_mb = mem_info['used']
            total_mb = mem_info['total']
            
            logger.debug(f"GPU {gpu_id}: {free_mb:.0f} MB free / {total_mb:.0f} MB total ({used_mb:.0f} MB used)")
            
            # 检查是否有足够的显存
            if free_mb >= required_mb:
                candidates_with_enough_mem.append((gpu_id, free_mb))
                if free_mb > max_free_mb:
                    max_free_mb = free_mb
                    best_gpu = gpu_id
        
        if max_free_mb < 0:
            # 如果没有GPU有足够的显存，选择显存最多的
            logger.warning(f"No GPU has {required_mb} MB free, selecting GPU with most free memory")
            for gpu_id in available_gpus:
                mem_info = self._get_gpu_memory_info(gpu_id)
                if mem_info and mem_info['free'] > max_free_mb:
                    max_free_mb = mem_info['free']
                    best_gpu = gpu_id
        else:
            # 有足够的显存，从候选者中选择显存最多的
            logger.info(f"Found {len(candidates_with_enough_mem)} GPU(s) with enough memory: {candidates_with_enough_mem}")
        
        mem_info = self._get_gpu_memory_info(best_gpu)
        if mem_info:
            logger.info(f"Allocated GPU {best_gpu}: {mem_info['free']:.0f} MB free / {mem_info['total']:.0f} MB total")
        else:
            logger.info(f"Allocated GPU {best_gpu} (memory info unavailable)")
        
        return best_gpu
    
    def _normalize_tts_model(self, tts_model: str) -> str:
        """标准化TTS模型名称
        
        支持多种命名格式的统一化：
        - TacoTron2 -> tacotron
        - TacoTron -> tacotron
        - edgeTTS -> edgetts
        - EdgeTTS -> edgetts
        - cosyvoice -> cosyvoice
        - sovits -> sovits
        """
        if not tts_model:
            return 'edgetts'
        
        tts_lower = tts_model.lower()
        
        # 映射表
        tts_mapping = {
            'tacotron2': 'tacotron',
            'tacotrons': 'tacotron',
            'edgetts': 'edgetts',
            'cosyvoice': 'cosyvoice',
            'cosyvoice2': 'cosyvoice',
            'sovits': 'sovits',
            'gpt-sovits': 'sovits',
        }
        
        # 查找匹配
        for key, value in tts_mapping.items():
            if key in tts_lower:
                return value
        
        # 默认返回小写版本
        return tts_lower
    
    def _load_avatar_config(self, avatar_name: str) -> Dict:
        """读取Avatar配置文件
        
        Args:
            avatar_name: Avatar名称（如 test_yongen）
        
        Returns:
            配置字典，如果文件不存在则返回默认配置
        """
        config_path = os.path.join(AVATAR_DATA_PATH, avatar_name, 'config.json')
        default_config = {
            'tts_model': 'edgeTTS',
            'timbre': 'Default',
            'avatar_model': 'musetalk',
            'transport': 'webrtc',
            'max_session': 100  # 默认支持100个并发连接
        }
        
        if not os.path.exists(config_path):
            logger.warning(f"Avatar config file not found: {config_path}, using defaults")
            return default_config
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 合并默认配置
            result = default_config.copy()
            result.update(config)
            
            logger.info(f"Loaded avatar config for {avatar_name}: tts_model={result.get('tts_model')}, timbre={result.get('timbre')}")
            return result
        except Exception as e:
            logger.error(f"Failed to load avatar config from {config_path}: {e}")
            return default_config
    
    def _build_command(self, avatar_id: str, port: int, real_avatar_name: str = None) -> str:
        """构建启动命令（使用conda环境）
        
        Args:
            avatar_id: 实例ID（如 g_user_1）
            port: 端口号
            real_avatar_name: 真实Avatar名称（如 g），如果为None则使用avatar_id
        """
        # 使用真实Avatar名称，而不是实例ID
        actual_avatar_name = real_avatar_name if real_avatar_name else avatar_id
        
        # 读取Avatar配置文件
        avatar_config = self._load_avatar_config(actual_avatar_name)
        
        # 获取TTS模型并标准化
        tts_model = avatar_config.get('tts_model', 'edgeTTS')
        tts_normalized = self._normalize_tts_model(tts_model)
        
        # 根据TTS模型选择正确的端口（使用统一的端口映射函数）
        tts_port = get_tts_port_for_model(tts_normalized)
        
        # 构建Python命令参数
        python_args = [
            'app.py',
            '--transport', avatar_config.get('transport', AVATAR_CONFIG['transport']),
            '--model', avatar_config.get('avatar_model', AVATAR_CONFIG['model']).lower(),
            '--avatar_id', actual_avatar_name,  # 使用真实Avatar名称
            '--max_session', str(avatar_config.get('max_session', AVATAR_CONFIG['max_session'])),
            '--listenport', str(port),
            '--tts', tts_normalized,  # 使用从配置文件读取的TTS模型
            '--TTS_SERVER', f'http://127.0.0.1:{tts_port}'  # 根据TTS模型选择正确的端口
        ]
        
        # 如果配置了timbre，添加到参数中
        # 对于 EdgeTTS，timbre 必须是有效的语音名称（如 "en-US-BrianNeural"），不能是 "Default"
        if avatar_config.get('timbre'):
            timbre = avatar_config['timbre']
            
            # 如果是 EdgeTTS，需要将友好名称（MaleA, FemaleB等）转换为实际的语音名称
            if tts_normalized == 'edgetts':
                # EdgeTTS 音色映射表（与 tts/tts.py 保持一致）
                edge_timbre_map = {
                    "Default": "en-US-BrianNeural",
                    "MaleA": "en-US-GuyNeural",
                    "MaleB": "en-US-ChristopherNeural",
                    "MaleC": "en-US-DavisNeural",
                    "MaleD": "en-US-AndrewNeural",
                    "MaleE": "en-US-JacobNeural",
                    "MaleF": "en-US-SteffanNeural",
                    "FemaleA": "en-US-EmmaNeural",
                    "FemaleB": "en-US-JennyMultilingualNeural",
                    "FemaleC": "en-US-JennyNeural",
                    "FemaleD": "en-US-AriaNeural",
                    "FemaleE": "en-US-AnaNeural",
                    "FemaleF": "en-US-SaraNeural",
                    "ChineseMaleA": "zh-CN-YunjianNeural",
                    "ChineseMaleB": "zh-CN-YunxiNeural",
                    "ChineseMaleC": "zh-CN-YunxiNeural",  # 添加 MaleC 映射
                    "ChineseFemaleA": "zh-CN-XiaoxiaoNeural",
                    "ChineseFemaleB": "zh-CN-XiaoyiNeural",
                }
                
                # 如果timbre是友好名称，转换为实际的语音名称；否则直接使用（可能已经是语音名称）
                timbre = edge_timbre_map.get(timbre, edge_timbre_map["Default"])
                logger.info(f"Mapped EdgeTTS timbre: {avatar_config['timbre']} -> {timbre}")
            
            python_args.extend(['--REF_FILE', timbre])
        
        logger.info(f"Building command for avatar {avatar_id} (real: {actual_avatar_name}): TTS={tts_normalized}")
        
        # 构建完整的bash命令，激活conda环境后执行
        cmd = f"source {CONDA_INIT} && conda activate {CONDA_ENV} && python {' '.join(python_args)}"
        return cmd
    
    def _check_and_start_tts_service(self, tts_model: str) -> bool:
        """检查并启动TTS服务（如果未运行）
        
        Args:
            tts_model: TTS模型名称（标准化后，如 'edgetts', 'tacotron'等）
        
        Returns:
            是否成功（服务已运行或已启动）
        """
        # 获取TTS端口
        tts_port = get_tts_port_for_model(tts_model)
        
        # 检查端口是否已被占用（TTS服务是否在运行）
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == psutil.CONN_LISTEN and conn.laddr.port == tts_port:
                    logger.info(f"TTS service for {tts_model} is already running on port {tts_port}")
                    return True
        except Exception as e:
            logger.warning(f"Failed to check port {tts_port}: {e}")
        
        # TTS服务未运行，需要启动
        logger.info(f"Starting TTS service for {tts_model} on port {tts_port}")
        
        # 读取model_info.json获取TTS服务器配置
        model_info_path = os.path.join(LIP_SYNC_PATH, '..', 'tts', 'model_info.json')
        
        try:
            with open(model_info_path, 'r', encoding='utf-8') as f:
                model_infos = json.load(f)
            
            # 找到对应的模型配置（需要匹配标准化后的模型名）
            tts_model_key = None
            for key in model_infos.keys():
                if key.lower() == tts_model or key.lower() in tts_model or tts_model in key.lower():
                    tts_model_key = key
                    break
            
            if not tts_model_key:
                logger.error(f"No configuration found for TTS model: {tts_model}")
                return False
            
            model_info = model_infos[tts_model_key]
            
            # 检查状态
            if model_info.get('status') != 'active':
                logger.error(f"TTS model {tts_model_key} is not active")
                return False
            
            # 获取服务器路径和环境
            server_path = model_info.get('server_path')
            env_path = model_info.get('env_path', '/workspace/conda/envs/edge')
            
            if not server_path or not os.path.exists(server_path):
                logger.error(f"TTS server path not found: {server_path}")
                return False
            
            # 构建启动命令
            python_exec = os.path.join(env_path, 'bin', 'python')
            server_dir = os.path.dirname(server_path)
            server_file = os.path.basename(server_path)
            
            # 启动命令
            cmd = f"source {CONDA_INIT} && cd {server_dir} && nohup {python_exec} {server_file} --model_name {tts_model_key} --port {tts_port} --use_gpu false > /tmp/tts_{tts_model_key}.log 2>&1 &"
            
            logger.debug(f"Starting TTS command: {cmd}")
            
            # 启动进程
            process = subprocess.Popen(
                cmd,
                shell=True,
                executable='/bin/bash',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 等待服务启动
            logger.info(f"Waiting for TTS service {tts_model_key} to start on port {tts_port}...")
            max_wait = 30
            wait_interval = 1
            
            for i in range(max_wait):
                time.sleep(wait_interval)
                try:
                    for conn in psutil.net_connections(kind='inet'):
                        if conn.status == psutil.CONN_LISTEN and conn.laddr.port == tts_port:
                            logger.info(f"TTS service {tts_model_key} started successfully on port {tts_port}")
                            return True
                except Exception:
                    pass
            
            logger.error(f"TTS service {tts_model_key} failed to start within {max_wait} seconds")
            return False
            
        except Exception as e:
            logger.error(f"Failed to start TTS service for {tts_model}: {e}")
            return False
    
    def start(self, avatar_id: str, force_gpu: Optional[int] = None, real_avatar_name: str = None) -> dict:
        """启动Avatar实例（支持多用户共享同一个avatar）
        
        Args:
            avatar_id: 实例ID（如 g_user_1）
            force_gpu: 强制使用的GPU
            real_avatar_name: 真实Avatar名称（如 g）
        """
        actual_avatar_name = real_avatar_name if real_avatar_name else avatar_id
        logger.info(f"请求启动Avatar: {avatar_id} (真实名称: {actual_avatar_name})")
        
        # 使用锁保护整个端口分配和实例创建过程，防止并发冲突
        with self._lock:
            # 检查该真实avatar是否已有实例在运行（实现共享）
            if actual_avatar_name in self.avatar_map:
                existing_instance_id = self.avatar_map[actual_avatar_name]
                existing_instance = self.instances.get(existing_instance_id)
                
                if existing_instance and existing_instance.is_running():
                    # 复用现有实例
                    existing_instance.connections += 1
                    existing_instance.update_activity()
                    logger.info(f"复用现有Avatar实例: {existing_instance_id} (真实名称: {actual_avatar_name}, 连接数: {existing_instance.connections})")
                    return existing_instance.get_info()
                else:
                    # 实例已失效，清理映射
                    logger.warning(f"Avatar实例 {existing_instance_id} 已失效，将创建新实例")
                    del self.avatar_map[actual_avatar_name]
                    if existing_instance_id in self.instances:
                        del self.instances[existing_instance_id]
            
            # 再次检查（防止并发时两个请求都通过了第一次检查）
            if actual_avatar_name in self.avatar_map:
                existing_instance_id = self.avatar_map[actual_avatar_name]
                existing_instance = self.instances.get(existing_instance_id)
                if existing_instance and existing_instance.is_running():
                    # 在两次检查之间，另一个线程已经创建了实例
                    existing_instance.connections += 1
                    existing_instance.update_activity()
                    logger.info(f"复用现有Avatar实例（二次检查）: {existing_instance_id} (真实名称: {actual_avatar_name}, 连接数: {existing_instance.connections})")
                    return existing_instance.get_info()
            
            # 检查数量限制
            if len(self.instances) >= self.max_instances:
                raise Exception(f"已达到最大限制: {self.max_instances}个Avatar")
            
            # 获取Avatar配置以确定需要的TTS模型
            actual_avatar_name = real_avatar_name if real_avatar_name else avatar_id
            avatar_config = self._load_avatar_config(actual_avatar_name)
            tts_model = avatar_config.get('tts_model', 'edgeTTS')
            tts_normalized = self._normalize_tts_model(tts_model)
            
            # 检查并启动对应的TTS服务（按需启动）
            if not self._check_and_start_tts_service(tts_normalized):
                logger.warning(f"Failed to start TTS service for {tts_normalized}, proceeding anyway")
            
            # 分配资源（关键：必须在锁内分配端口）
            # 先预占avatar_map，防止并发时重复分配
            self.avatar_map[actual_avatar_name] = avatar_id  # 预占位置
            port = self._allocate_port()
            
            # GPU分配：如果指定了force_gpu则使用，否则自动选择最合适的GPU
            if force_gpu is not None:
                gpu_id = force_gpu
            else:
                gpu_id = self._allocate_gpu()
            
            # 构建启动命令（传递真实Avatar名称）
            cmd = self._build_command(avatar_id, port, real_avatar_name)
            
            # 设置环境变量
            env = os.environ.copy()
            env['CUDA_VISIBLE_DEVICES'] = str(gpu_id)
            
            logger.info(f"启动Avatar {avatar_id}")
            logger.info(f"  端口: {port}")
            logger.info(f"  GPU: {gpu_id}")
            logger.info(f"  Conda环境: {CONDA_ENV}")
            logger.debug(f"  命令: {cmd}")
            
            # 创建Avatar专属日志文件（使用绝对路径，因为进程在lip-sync目录运行）
            log_dir = os.path.abspath(os.path.dirname(LOG_FILE))
            log_file_path = os.path.join(log_dir, f'avatar_{avatar_id}_{port}.log')
            
            # 在命令中添加输出重定向（使用绝对路径）
            cmd_with_redirect = f"{cmd} >> {log_file_path} 2>&1"
            
            try:
                # 启动进程（使用bash执行conda命令），输出重定向到日志文件
                process = subprocess.Popen(
                    cmd_with_redirect,
                    cwd=LIP_SYNC_PATH,
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    shell=True,
                    executable='/bin/bash'
                )

                # 第一步：快速检查进程是否立即崩溃（缩短为1秒）
                time.sleep(1)

                if process.poll() is not None:
                    # 进程已退出，启动失败
                    # 读取日志文件的最后几行
                    try:
                        with open(log_file_path, 'r') as f:
                            lines = f.readlines()
                            error_msg = ''.join(lines[-10:])  # 最后10行
                    except:
                        error_msg = "无法读取日志"
                    # ✓ 立即释放端口
                    if actual_avatar_name in self.avatar_map and self.avatar_map[actual_avatar_name] == avatar_id:
                        del self.avatar_map[actual_avatar_name]
                    self._allocating_ports.discard(port)
                    raise Exception(f"Avatar启动失败（立即退出），查看日志: {log_file_path}\n{error_msg[:500]}")

                # 第二步：主动验证socket已真正bind ✓ 这替代了原来的2秒sleep，消除竞态条件
                # 给予最多29秒（加上第一步的1秒共30秒）用于socket绑定
                if not self._wait_for_port_binding(port, timeout=29):
                    # socket未能在规定时间内bind
                    logger.error(f"✗ 端口 {port} socket绑定验证失败，终止进程PID {process.pid}")
                    try:
                        parent = psutil.Process(process.pid)
                        children = parent.children(recursive=True)

                        # 先杀所有子进程
                        for child in children:
                            try:
                                logger.info(f"   杀死子进程 PID: {child.pid}")
                                os.kill(child.pid, signal.SIGKILL)
                            except:
                                pass

                        # 再杀父进程
                        os.kill(process.pid, signal.SIGKILL)
                    except Exception as kill_err:
                        logger.warning(f"杀死进程失败: {kill_err}")

                    # ✓ 立即释放端口
                    if actual_avatar_name in self.avatar_map and self.avatar_map[actual_avatar_name] == avatar_id:
                        del self.avatar_map[actual_avatar_name]
                    self._allocating_ports.discard(port)
                    raise Exception(f"Avatar socket绑定超时（{port}），进程已杀死")

                # 第三步：socket已验证成功，安全地创建实例对象
                instance = AvatarInstance(avatar_id, port, gpu_id, process, real_avatar_name)
                instance.connections = 1  # 初始连接数为1
                self.instances[avatar_id] = instance

                # 建立real_avatar_name到instance_id的映射（用于实例共享）
                self.avatar_map[actual_avatar_name] = avatar_id

                # ✓ 现在安全地从"正在分配中"移除端口（socket已confirmed绑定）
                self._allocating_ports.discard(port)

                logger.info(f"✓ Avatar {avatar_id} 启动成功 (PID: {process.pid}, 端口: {port}, 真实名称: {actual_avatar_name})")

                return instance.get_info()
                
            except Exception as e:
                logger.error(f" 启动Avatar {avatar_id} 失败: {e}")
                # 启动失败时，清理预占和正在分配的端口
                if actual_avatar_name in self.avatar_map and self.avatar_map[actual_avatar_name] == avatar_id:
                    del self.avatar_map[actual_avatar_name]
                self._allocating_ports.discard(port)
                raise
    
    def stop(self, avatar_id: str, force: bool = True):
        """停止Avatar实例并立即释放GPU显存（默认强制关闭）
        
        Args:
            avatar_id: 实例ID或真实avatar名称
            force: 是否强制关闭（忽略连接计数）
        """
        logger.info(f"请求停止Avatar: {avatar_id} (force={force})")
        
        # 支持通过real_avatar_name停止
        actual_instance_id = avatar_id
        if avatar_id in self.avatar_map:
            actual_instance_id = self.avatar_map[avatar_id]
            logger.info(f"通过真实名称 {avatar_id} 找到实例 {actual_instance_id}")
        
        if actual_instance_id not in self.instances:
            raise Exception(f"Avatar {avatar_id} 不存在")
        
        instance = self.instances[actual_instance_id]
        real_avatar_name = instance.real_avatar_name
        port = instance.port  # 保存端口号用于删除log文件
        
        # 如果不强制关闭，检查连接计数
        if not force:
            instance.connections = max(0, instance.connections - 1)
            if instance.connections > 0:
                logger.info(f"Avatar {actual_instance_id} 还有 {instance.connections} 个连接，不关闭")
                return
            logger.info(f"Avatar {actual_instance_id} 连接数为0，执行关闭")
        
        try:
            # 强制终止整个进程树（包括所有子进程）
            logger.info(f" 强制终止Avatar {avatar_id} (PID: {instance.pid}) 及其子进程")
            try:
                parent = psutil.Process(instance.pid)
                children = parent.children(recursive=True)
                
                # 先杀所有子进程
                for child in children:
                    try:
                        logger.info(f"   杀死子进程 PID: {child.pid}")
                        os.kill(child.pid, signal.SIGKILL)
                    except:
                        pass
                
                # 再杀父进程
                os.kill(instance.pid, signal.SIGKILL)
            except:
                # 如果psutil失败，直接用系统命令
                import subprocess
                subprocess.run(['pkill', '-9', '-f', f'app.py.*{port}'], check=False)
            
            # 等待GPU显存完全释放
            logger.info(f" 等待3秒让GPU显存完全释放...")
            time.sleep(3)
            
            # 清理log文件
            log_dir = os.path.abspath(os.path.dirname(LOG_FILE))
            log_file_path = os.path.join(log_dir, f'avatar_{avatar_id}_{port}.log')
            if os.path.exists(log_file_path):
                try:
                    os.remove(log_file_path)
                    logger.info(f" 已删除log文件: {log_file_path}")
                except Exception as log_err:
                    logger.warning(f" 删除log文件失败: {log_err}")
            else:
                logger.info(f" log文件不存在，无需删除: {log_file_path}")
            
            # 从列表中移除
            del self.instances[actual_instance_id]
            
            # 清理avatar_map映射
            if real_avatar_name in self.avatar_map and self.avatar_map[real_avatar_name] == actual_instance_id:
                del self.avatar_map[real_avatar_name]
                logger.info(f" 已清理映射: {real_avatar_name} -> {actual_instance_id}")
            
            logger.info(f" Avatar {actual_instance_id} 已停止，GPU显存已释放")
            
        except ProcessLookupError:
            # 进程已不存在
            #  暂时注释掉自动删除log（用于调试）
            # log_dir = os.path.abspath(os.path.dirname(LOG_FILE))
            # log_file_path = os.path.join(log_dir, f'avatar_{actual_instance_id}_{port}.log')
            # if os.path.exists(log_file_path):
            #     try:
            #         os.remove(log_file_path)
            #         logger.info(f" 已删除log文件: {log_file_path}")
            #     except:
            #         pass
            
            del self.instances[actual_instance_id]
            
            # 清理avatar_map映射
            if real_avatar_name in self.avatar_map and self.avatar_map[real_avatar_name] == actual_instance_id:
                del self.avatar_map[real_avatar_name]
            
            logger.info(f"Avatar {actual_instance_id} 进程已不存在")
        except Exception as e:
            logger.error(f" 停止Avatar {avatar_id} 失败: {e}")
            raise
    
    def stop_all(self):
        """停止所有Avatar"""
        logger.info("停止所有Avatar实例")
        avatar_ids = list(self.instances.keys())
        for avatar_id in avatar_ids:
            try:
                self.stop(avatar_id)
            except Exception as e:
                logger.error(f"停止 {avatar_id} 失败: {e}")
    
    def restart(self, avatar_id: str) -> dict:
        """重启Avatar"""
        logger.info(f"重启Avatar: {avatar_id}")
        
        if avatar_id not in self.instances:
            raise Exception(f"Avatar {avatar_id} 不存在")
        
        # 保存GPU配置和真实Avatar名称
        gpu_id = self.instances[avatar_id].gpu_id
        real_avatar_name = self.instances[avatar_id].real_avatar_name
        logger.info(f"  保留真实Avatar名称: {real_avatar_name}")
        
        # 停止
        self.stop(avatar_id)
        
        # 启动（使用真实Avatar名称）
        return self.start(avatar_id, force_gpu=gpu_id, real_avatar_name=real_avatar_name)
    
    def get_info(self, avatar_id: str) -> Optional[dict]:
        """获取Avatar信息"""
        if avatar_id not in self.instances:
            return None
        return self.instances[avatar_id].get_info()
    
    def list_all(self) -> list:
        """列出所有Avatar"""
        return [inst.get_info() for inst in self.instances.values()]
    
    def get_status(self) -> dict:
        """获取系统状态"""
        running_count = len(self.instances)
        available = self.max_instances - running_count
        
        # GPU使用情况
        gpu_usage = {}
        for inst in self.instances.values():
            gpu_id = inst.gpu_id
            gpu_usage[gpu_id] = gpu_usage.get(gpu_id, 0) + 1
        
        # Avatar共享情况统计
        total_connections = sum(inst.connections for inst in self.instances.values())
        shared_avatars = sum(1 for inst in self.instances.values() if inst.connections > 1)
        
        return {
            'running': running_count,
            'max': self.max_instances,
            'available': available,
            'utilization': f"{running_count}/{self.max_instances}",
            'gpu_distribution': gpu_usage,
            'total_connections': total_connections,
            'shared_avatars': shared_avatars,
            'avatar_map': self.avatar_map,
            'avatars': self.list_all()
        }
    
    def health_check(self):
        """健康检查"""
        logger.info("执行健康检查")
        
        for avatar_id, instance in list(self.instances.items()):
            if not instance.is_running():
                logger.warning(f" Avatar {avatar_id} 进程异常退出，尝试重启")
                try:
                    self.restart(avatar_id)
                except Exception as e:
                    logger.error(f"重启 {avatar_id} 失败: {e}")
    
    def cleanup_idle(self, idle_timeout: int):
        """清理空闲实例"""
        if idle_timeout <= 0:
            return
        
        logger.info(f"检查空闲实例 (超时: {idle_timeout}秒)")
        
        for avatar_id, instance in list(self.instances.items()):
            idle_seconds = instance.get_idle_seconds()
            if idle_seconds > idle_timeout:
                logger.info(f"清理空闲Avatar {avatar_id} (空闲: {idle_seconds:.0f}秒)")
                try:
                    self.stop(avatar_id)
                except Exception as e:
                    logger.error(f"清理 {avatar_id} 失败: {e}")


# 全局管理器实例
_manager = None

def get_manager() -> AvatarManager:
    """获取全局管理器实例"""
    global _manager
    if _manager is None:
        _manager = AvatarManager()
    return _manager


