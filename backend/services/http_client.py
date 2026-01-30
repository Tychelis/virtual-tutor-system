"""
HTTP客户端管理器（同步版本）
使用httpx实现连接池，优化Backend到Avatar服务的转发性能
"""
import httpx
from typing import Optional
from threading import Lock

class SyncHTTPClient:
    """同步HTTP客户端单例，管理连接池"""
    
    _instance: Optional['SyncHTTPClient'] = None
    _lock = Lock()
    _client: Optional[httpx.Client] = None
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置，但不创建客户端（延迟到第一次使用）"""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            # 连接池配置
            self._limits = httpx.Limits(
                max_connections=100,        # 最大连接数
                max_keepalive_connections=20,  # 最大保持连接数
                keepalive_expiry=30.0       # 保持连接超时时间
            )
            # 超时配置
            self._timeout = httpx.Timeout(
                connect=10.0,   # 连接超时
                read=60.0,      # 读取超时
                write=10.0,     # 写入超时
                pool=5.0        # 连接池超时
            )
    
    def get_client(self) -> httpx.Client:
        """获取或创建同步客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(
                limits=self._limits,
                timeout=self._timeout,
                follow_redirects=True,
                http2=False  # 关闭HTTP/2（需要额外的h2包）
            )
        return self._client
    
    def close(self):
        """关闭客户端"""
        if self._client and not self._client.is_closed:
            self._client.close()
            self._client = None
    
    def post(self, url: str, **kwargs) -> httpx.Response:
        """
        同步POST请求
        
        Args:
            url: 目标URL
            **kwargs: httpx.Client.post的参数
        
        Returns:
            httpx.Response对象
        """
        client = self.get_client()
        return client.post(url, **kwargs)
    
    def get(self, url: str, **kwargs) -> httpx.Response:
        """
        同步GET请求
        
        Args:
            url: 目标URL
            **kwargs: httpx.Client.get的参数
        
        Returns:
            httpx.Response对象
        """
        client = self.get_client()
        return client.get(url, **kwargs)
    
    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """
        同步通用请求
        
        Args:
            method: HTTP方法
            url: 目标URL
            **kwargs: httpx.Client.request的参数
        
        Returns:
            httpx.Response对象
        """
        client = self.get_client()
        return client.request(method, url, **kwargs)


# 全局实例
http_client = SyncHTTPClient()


# 清理函数，在应用关闭时调用
def cleanup_http_client():
    """清理HTTP客户端连接"""
    http_client.close()
