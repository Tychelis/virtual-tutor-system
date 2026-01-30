"""GPU监控模块"""

import logging
from typing import Dict, List

try:
    import pynvml
    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False
    print(" 警告: pynvml未安装，GPU监控功能将不可用")
    print("   安装: pip install nvidia-ml-py3")

logger = logging.getLogger('Monitor')


class GPUMonitor:
    """GPU监控器"""
    
    def __init__(self):
        self.initialized = False
        
        if PYNVML_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self.initialized = True
                self.device_count = pynvml.nvmlDeviceGetCount()
                logger.info(f"GPU监控初始化成功，检测到 {self.device_count} 个GPU")
            except Exception as e:
                logger.error(f"GPU监控初始化失败: {e}")
        else:
            logger.warning("pynvml不可用，GPU监控功能已禁用")
    
    def get_gpu_stats(self) -> List[dict]:
        """获取所有GPU统计信息"""
        if not self.initialized:
            return []
        
        stats = []
        try:
            for i in range(self.device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                
                # GPU名称
                name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode('utf-8')
                
                # 显存信息
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                mem_total_gb = mem_info.total / 1024**3
                mem_used_gb = mem_info.used / 1024**3
                mem_free_gb = mem_info.free / 1024**3
                mem_usage_pct = (mem_info.used / mem_info.total) * 100
                
                # 温度
                try:
                    temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                except:
                    temp = None
                
                # GPU使用率
                try:
                    utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_util = utilization.gpu
                except:
                    gpu_util = None
                
                # 功耗
                try:
                    power_draw = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000  # mW to W
                    power_limit = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000
                except:
                    power_draw = None
                    power_limit = None
                
                stats.append({
                    'gpu_id': i,
                    'name': name,
                    'memory': {
                        'total_gb': round(mem_total_gb, 2),
                        'used_gb': round(mem_used_gb, 2),
                        'free_gb': round(mem_free_gb, 2),
                        'usage_percent': round(mem_usage_pct, 1)
                    },
                    'temperature_celsius': temp,
                    'gpu_utilization_percent': gpu_util,
                    'power_draw_watts': round(power_draw, 1) if power_draw else None,
                    'power_limit_watts': round(power_limit, 1) if power_limit else None
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"获取GPU统计信息失败: {e}")
            return []
    
    def check_alerts(self) -> List[str]:
        """检查GPU告警"""
        if not self.initialized:
            return []
        
        alerts = []
        stats = self.get_gpu_stats()
        
        for gpu in stats:
            gpu_id = gpu['gpu_id']
            
            # 显存告警
            mem_usage = gpu['memory']['usage_percent']
            if mem_usage > 95:
                alerts.append(f"GPU {gpu_id} 显存使用率过高: {mem_usage:.1f}%")
            
            # 温度告警
            temp = gpu['temperature_celsius']
            if temp and temp > 85:
                alerts.append(f"GPU {gpu_id} 温度过高: {temp}°C")
            
            # GPU使用率告警（如果很高可能需要扩容）
            gpu_util = gpu['gpu_utilization_percent']
            if gpu_util and gpu_util > 95:
                alerts.append(f"GPU {gpu_id} 使用率过高: {gpu_util}%")
        
        return alerts
    
    def __del__(self):
        """清理"""
        if self.initialized:
            try:
                pynvml.nvmlShutdown()
            except:
                pass


# 全局监控器实例
_monitor = None

def get_monitor() -> GPUMonitor:
    """获取全局监控器实例"""
    global _monitor
    if _monitor is None:
        _monitor = GPUMonitor()
    return _monitor





