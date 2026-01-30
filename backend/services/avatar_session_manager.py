"""Avatar Session Manager - 管理用户Avatar会话和端口映射（支持Redis持久化）"""

from threading import Lock
import time
import httpx
import logging
import json
import os
import sys

# 导入统一端口配置
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from scripts.ports_config import get_avatar_manager_url

logger = logging.getLogger(__name__)

class AvatarSessionManager:
    """管理用户和Avatar端口的映射关系（支持Redis持久化）"""
    
    REDIS_KEY = "avatar:user_mappings"  # Redis中存储映射表的key
    ENABLE_REDIS_PERSISTENCE = True  # 启用Redis持久化（多worker环境必需）
    
    def __init__(self):
        self.user_avatar_map = {}  # {user_id: {"avatar_id": str, "port": int, "instance_id": str, "timestamp": float}}
        self.port_user_map = {}    # {port: user_id} 反向映射
        self._lock = Lock()
        self._redis = None
        if self.ENABLE_REDIS_PERSISTENCE:
            self._load_from_redis()  # 初始化时从Redis恢复映射
        else:
            logger.info("Redis persistence is DISABLED for avatar sessions - starting with clean state")
    
    def _get_redis(self):
        """懒加载Redis客户端"""
        if self._redis is None:
            try:
                # 尝试多种导入方式以适配不同执行环境
                try:
                    from services.redis_client import redis_client
                    self._redis = redis_client
                except ImportError:
                    from backend.services.redis_client import redis_client
                    self._redis = redis_client
            except Exception as e:
                logger.warning(f" Redis not available: {e}")
        return self._redis
    
    def _save_to_redis(self):
        """保存映射表到Redis（保存整个表，用于兼容）"""
        if not self.ENABLE_REDIS_PERSISTENCE:
            return
        
        redis = self._get_redis()
        if redis:
            try:
                # 使用 Hash 结构原子性地保存每个用户
                for user_id, info in self.user_avatar_map.items():
                    redis.hset(self.REDIS_KEY, user_id, json.dumps(info))
                logger.debug(f" Saved {len(self.user_avatar_map)} avatar mappings to Redis Hash")
            except Exception as e:
                logger.warning(f" Failed to save to Redis: {e}")
    
    def _load_from_redis(self):
        """从Redis恢复映射表（使用Hash结构）"""
        redis = self._get_redis()
        if redis:
            try:
                # 从 Redis Hash 加载所有用户映射
                all_data = redis.hgetall(self.REDIS_KEY)
                if all_data:
                    self.user_avatar_map = {}
                    self.port_user_map = {}
                    for user_id_bytes, info_bytes in all_data.items():
                        user_id = user_id_bytes.decode('utf-8') if isinstance(user_id_bytes, bytes) else user_id_bytes
                        info_str = info_bytes.decode('utf-8') if isinstance(info_bytes, bytes) else info_bytes
                        info = json.loads(info_str)
                        self.user_avatar_map[user_id] = info
                        user_id_int = int(user_id)
                        self.port_user_map[info['port']] = user_id_int
                    logger.info(f" Restored {len(self.user_avatar_map)} avatar mappings from Redis Hash")
                    return True
            except Exception as e:
                logger.warning(f" Failed to load from Redis: {e}")
        return False
    
    def set_user_avatar(self, user_id: int, avatar_id: str, port: int, instance_id: str = None):
        """设置用户的Avatar端口（支持实例ID，原子性保存）"""
        with self._lock:
            user_id_str = str(user_id)
            
            # 清理旧的端口映射
            if user_id_str in self.user_avatar_map:
                old_port = self.user_avatar_map[user_id_str].get('port')
                if old_port and old_port in self.port_user_map:
                    del self.port_user_map[old_port]
            
            # 设置新映射
            user_info = {
                "avatar_id": avatar_id,
                "port": port,
                "instance_id": instance_id or avatar_id,
                "timestamp": time.time()
            }
            self.user_avatar_map[user_id_str] = user_info
            self.port_user_map[port] = user_id
            logger.info(f"💾 SET_USER_AVATAR: User {user_id} → Avatar {avatar_id} (instance: {instance_id}) on port {port}")
            
            # 原子性地保存单个用户到Redis Hash（不影响其他用户）
            if self.ENABLE_REDIS_PERSISTENCE:
                redis = self._get_redis()
                if redis:
                    try:
                        redis.hset(self.REDIS_KEY, user_id_str, json.dumps(user_info))
                        logger.info(f"✓ Redis Hash saved for user {user_id}")
                    except Exception as e:
                        logger.error(f"❌ Redis save failed for user {user_id}: {e}")
    
    def get_user_port(self, user_id: int) -> int:
        """获取用户的Avatar端口（多worker安全：优先从Redis读取）"""
        user_id_str = str(user_id)
        
        # 🔧 多worker环境：优先从Redis读取（避免worker间状态不一致）
        if self.ENABLE_REDIS_PERSISTENCE:
            redis = self._get_redis()
            if redis:
                try:
                    user_info_bytes = redis.hget(self.REDIS_KEY, user_id_str)
                    if user_info_bytes:
                        user_info_str = user_info_bytes.decode('utf-8') if isinstance(user_info_bytes, bytes) else user_info_bytes
                        user_info = json.loads(user_info_str)
                        port = user_info.get('port')
                        # 同时更新本地缓存
                        with self._lock:
                            if user_id_str not in self.user_avatar_map:
                                self.user_avatar_map[user_id_str] = user_info
                                self.port_user_map[port] = user_id
                        return port
                except Exception as e:
                    logger.warning(f"⚠️ Failed to read user {user_id} from Redis: {e}")
        
        # Fallback: 从内存读取
        with self._lock:
            session = self.user_avatar_map.get(user_id_str)
            if session:
                return session["port"]
            return None  # 返回None而不是默认端口，让调用者决定
    
    def get_user_avatar(self, user_id: int) -> dict:
        """获取用户的Avatar信息（多worker安全：优先从Redis读取）"""
        user_id_str = str(user_id)
        
        # 🔧 多worker环境：优先从Redis读取
        if self.ENABLE_REDIS_PERSISTENCE:
            redis = self._get_redis()
            if redis:
                try:
                    user_info_bytes = redis.hget(self.REDIS_KEY, user_id_str)
                    if user_info_bytes:
                        user_info_str = user_info_bytes.decode('utf-8') if isinstance(user_info_bytes, bytes) else user_info_bytes
                        user_info = json.loads(user_info_str)
                        # 同时更新本地缓存
                        with self._lock:
                            if user_id_str not in self.user_avatar_map:
                                self.user_avatar_map[user_id_str] = user_info
                                port = user_info.get('port')
                                if port:
                                    self.port_user_map[port] = user_id
                        return user_info
                except Exception as e:
                    logger.warning(f"⚠️ Failed to read user {user_id} avatar info from Redis: {e}")
        
        # Fallback: 从内存读取
        with self._lock:
            return self.user_avatar_map.get(user_id_str)
    
    def get_user_by_port(self, port: int) -> int:
        """根据端口获取用户ID"""
        with self._lock:
            return self.port_user_map.get(port)
    
    def remove_user(self, user_id: int):
        """移除用户会话（原子性删除）"""
        with self._lock:
            user_id_str = str(user_id)
            if user_id_str in self.user_avatar_map:
                port = self.user_avatar_map[user_id_str].get('port')
                if port and port in self.port_user_map:
                    del self.port_user_map[port]
                del self.user_avatar_map[user_id_str]
                logger.info(f"  Removed session for user {user_id}")
                
                # 原子性地从Redis Hash删除（不影响其他用户）
                if self.ENABLE_REDIS_PERSISTENCE:
                    redis = self._get_redis()
                    if redis:
                        try:
                            redis.hdel(self.REDIS_KEY, user_id_str)
                            logger.debug(f" Removed user {user_id} from Redis Hash")
                        except Exception as e:
                            logger.warning(f" Failed to remove from Redis: {e}")
    
    def clear_all(self):
        """清除所有会话"""
        with self._lock:
            self.user_avatar_map.clear()
            self.port_user_map.clear()
            logger.info("  Cleared all avatar sessions")
            
            # 清除Redis Hash（如果启用了持久化）
            if self.ENABLE_REDIS_PERSISTENCE:
                redis = self._get_redis()
                if redis:
                    try:
                        redis.delete(self.REDIS_KEY)
                        logger.debug("  Cleared avatar mappings from Redis Hash")
                    except Exception as e:
                        logger.warning(f" Failed to clear Redis: {e}")
    
    def get_all_mappings(self):
        """获取所有用户-Avatar映射"""
        with self._lock:
            return self.user_avatar_map.copy()
    
    def sync_from_avatar_manager(self, avatar_manager_url=None):
        """从Avatar Manager同步现有的实例映射（用于Backend重启后恢复映射）"""
        if avatar_manager_url is None:
            avatar_manager_url = get_avatar_manager_url()
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{avatar_manager_url}/avatar/list")
                data = response.json()
                
                if data.get("status") == "success":
                    avatars = data.get("data", [])
                    synced_count = 0
                    
                    for avatar in avatars:
                        avatar_id = avatar.get("avatar_id", "")
                        port = avatar.get("port")
                        
                        # 解析instance_id格式：{avatar_name}_user_{user_id}
                        if "_user_" in avatar_id:
                            parts = avatar_id.split("_user_")
                            if len(parts) == 2:
                                avatar_name = parts[0]
                                try:
                                    user_id = int(parts[1])
                                    self.set_user_avatar(user_id, avatar_name, port, avatar_id)
                                    synced_count += 1
                                    logger.info(f" Synced: User {user_id} → {avatar_name} (port {port})")
                                except ValueError:
                                    logger.warning(f" Invalid user_id in avatar_id: {avatar_id}")
                    
                    if synced_count > 0:
                        logger.info(f" Synced {synced_count} avatar mappings from Avatar Manager")
                    else:
                        logger.info(" No avatar instances to sync from Avatar Manager")
                    return synced_count
                else:
                    logger.warning(f" Failed to sync: {data.get('message', 'Unknown error')}")
                    return 0
                    
        except Exception as e:
            logger.error(f" Error syncing from Avatar Manager: {e}")
            return 0


# 全局实例
_manager = AvatarSessionManager()

def get_avatar_session_manager() -> AvatarSessionManager:
    """获取全局Avatar会话管理器"""
    return _manager

